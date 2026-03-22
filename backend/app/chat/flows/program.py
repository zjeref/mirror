"""Structured program flow (QuitSure-inspired).

Time-boxed multi-day programs that dismantle beliefs before asking for behavior change.
"""

from datetime import datetime, timezone
from typing import Any

from app.chat.flows.base import BaseFlow, FlowPrompt, FlowResult, UserContext
from app.chat.flows.registry import register_flow
from app.models.program import ProgramEnrollment, PROGRAMS


@register_flow
class ProgramFlow(BaseFlow):
    flow_id = "program"
    display_name = "Structured Program"

    def get_steps(self) -> list[str]:
        return ["choose_program", "daily_prompt", "daily_response", "reflection"]

    async def get_initial_prompt(self, context: UserContext) -> FlowResult:
        # Check if user has an active enrollment
        active = await ProgramEnrollment.find_one(
            ProgramEnrollment.user_id == context.user_id,
            ProgramEnrollment.is_active == True,
        )

        if active:
            program = PROGRAMS.get(active.program_id)
            if program and active.current_day < active.total_days:
                next_day = active.current_day + 1
                day_content = program["days"].get(next_day, {})
                self.collected_data["enrollment_id"] = str(active.id)
                self.collected_data["program_id"] = active.program_id
                self.collected_data["day"] = next_day

                return FlowResult(
                    next_step="daily_response",
                    response_message=(
                        f"**Day {next_day} of {active.total_days}: {day_content.get('title', '')}**\n\n"
                        f"{day_content.get('prompt', '')}"
                    ),
                    prompt=FlowPrompt(prompt="Take your time with this..."),
                )

        # No active program — show options
        program_list = []
        for pid, p in PROGRAMS.items():
            program_list.append(f"**{p['name']}** — {p['description']}")

        return FlowResult(
            next_step="choose_program",
            response_message=(
                "I have a structured journey that might help. "
                "Unlike generic advice, this is a day-by-day experience designed "
                "to shift how you think — not just what you do.\n\n"
                + "\n\n".join(program_list) + "\n\n"
                "The key: **you don't need to change anything yet.** "
                "Just show up each day and be honest."
            ),
            prompt=FlowPrompt(
                prompt="Want to start?",
                input_type="choice",
                options=["Start The Belief Reset", "Not right now"],
            ),
        )

    async def handle_input(self, step: str, value: Any, context: UserContext) -> FlowResult:
        if step == "choose_program":
            if "not" in str(value).lower() or "no" in str(value).lower():
                return FlowResult(next_step=None)

            # Enroll in belief_reset_7d
            program_id = "belief_reset_7d"
            program = PROGRAMS[program_id]

            enrollment = ProgramEnrollment(
                user_id=context.user_id,
                program_id=program_id,
                current_day=1,
                total_days=program["total_days"],
                started_at=datetime.now(timezone.utc),
            )
            await enrollment.insert()

            day_content = program["days"][1]
            self.collected_data["enrollment_id"] = str(enrollment.id)
            self.collected_data["program_id"] = program_id
            self.collected_data["day"] = 1

            return FlowResult(
                next_step="daily_response",
                response_message=(
                    f"You're in. No pressure to change anything — just show up.\n\n"
                    f"**Day 1 of {program['total_days']}: {day_content['title']}**\n\n"
                    f"{day_content['prompt']}"
                ),
                prompt=FlowPrompt(prompt="Take your time..."),
            )

        elif step == "daily_response":
            day = self.collected_data.get("day", 1)
            user_response = str(value)

            # Save the insight
            enrollment = await ProgramEnrollment.get(self.collected_data["enrollment_id"])
            if enrollment:
                enrollment.collected_insights.append({
                    "day": day,
                    "response": user_response,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                enrollment.days_completed.append(day)
                enrollment.current_day = day

                if day >= enrollment.total_days:
                    enrollment.is_active = False
                    enrollment.completed_at = datetime.now(timezone.utc)

                await enrollment.save()

            if day >= self.collected_data.get("total_days", 7):
                # Program complete
                return FlowResult(next_step=None)

            # Acknowledge and close today's session
            program = PROGRAMS.get(self.collected_data.get("program_id", ""))
            day_content = program["days"].get(day, {}) if program else {}

            acknowledgments = {
                "belief_identification": "Thank you for being honest about that. Most people never examine these beliefs — they just live inside them. You just took them out and looked at them. That takes courage.",
                "origin_tracing": "So this belief has been with you for a while. It makes sense — you learned it from somewhere. But learning something doesn't make it true. Tomorrow we'll look at what it's cost you.",
                "develop_discrepancy": "That gap between where you are and where you could be — that's not a failure. That's information. It means part of you knows there's something more.",
                "testing": "Interesting. So there ARE exceptions. The belief isn't absolute — it just FEELS absolute. That's a really important distinction.",
                "identity_exploration": "That person you just described? They're not a fantasy. They're you without one belief in the way. Let that sink in.",
                "belief_reconstruction": "That's your truth — not a motivational quote, not someone else's words. Yours. We'll build on this tomorrow.",
                "implementation_intention": "You've done something most people never do — you examined an old story, tested it, and chose a truer one. Now you have one action to prove it's real. I'll check in with you about it.",
            }

            technique = day_content.get("technique", "")
            ack = acknowledgments.get(technique, "Thank you for sharing that. I'll hold onto it.")

            return FlowResult(
                next_step=None,
                response_message=ack + f"\n\n**Day {day} complete.** Come back tomorrow for Day {day + 1}.",
            )

        return FlowResult(next_step=None)

    async def on_complete(self, context: UserContext) -> str:
        day = self.collected_data.get("day", 0)
        total = self.collected_data.get("total_days", 7)

        if day >= total:
            return (
                "You've completed The Belief Reset. Over 7 days, you identified a belief "
                "that was holding you back, traced where it came from, tested it against "
                "evidence, and built a truer story.\n\n"
                "This isn't the end — it's a foundation. The new story only becomes real "
                "through action. I'll help with that.\n\n"
                "How are you feeling right now?"
            )

        return f"Day {day} complete. See you tomorrow."
