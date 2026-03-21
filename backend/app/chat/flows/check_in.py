"""Daily check-in flow - the primary structured interaction."""

from datetime import datetime, timezone
from typing import Any, Optional

from app.chat.flows.base import BaseFlow, FlowPrompt, FlowResult, UserContext
from app.chat.flows.registry import register_flow


@register_flow
class CheckInFlow(BaseFlow):
    flow_id = "check_in"
    display_name = "Daily Check-in"

    MOOD_TAGS = [
        "calm", "anxious", "hopeful", "sad", "frustrated",
        "grateful", "overwhelmed", "motivated", "numb", "content",
    ]

    def get_steps(self) -> list[str]:
        return ["greeting", "mood", "energy", "mood_tags", "intention", "summary"]

    async def get_initial_prompt(self, context: UserContext) -> FlowResult:
        hour = datetime.now().hour
        if hour < 12:
            greeting = f"Good morning, {context.user_name}."
        elif hour < 17:
            greeting = f"Hey, {context.user_name}."
        else:
            greeting = f"Good evening, {context.user_name}."

        return FlowResult(
            next_step="mood",
            response_message=greeting,
            prompt=FlowPrompt(
                prompt="On a scale of 1-10, how are you feeling right now?",
                input_type="slider",
                min_val=1,
                max_val=10,
            ),
        )

    async def handle_input(
        self, step: str, value: Any, context: UserContext
    ) -> FlowResult:
        if step == "mood":
            score = self._parse_score(value)
            self.collected_data["mood_score"] = score

            # Validate low mood
            if score <= 3:
                msg = "I hear you. Low days are real, and you showing up here matters."
            elif score <= 6:
                msg = "Got it. Middle-of-the-road days can be tricky."
            else:
                msg = "That's good to hear."

            return FlowResult(
                next_step="energy",
                response_message=msg,
                prompt=FlowPrompt(
                    prompt="What's your energy level right now?",
                    input_type="slider",
                    min_val=1,
                    max_val=10,
                ),
            )

        elif step == "energy":
            score = self._parse_score(value)
            self.collected_data["energy_score"] = score
            context.energy_level = score

            if score <= 2:
                msg = "Very low energy. That's okay — we'll keep things tiny today."
            elif score <= 5:
                msg = "Noted."
            else:
                msg = "Nice, you've got some fuel to work with."

            return FlowResult(
                next_step="mood_tags",
                response_message=msg,
                prompt=FlowPrompt(
                    prompt="Which words describe how you feel? Pick any that fit.",
                    input_type="choice",
                    options=self.MOOD_TAGS,
                ),
            )

        elif step == "mood_tags":
            tags = self._parse_tags(value)
            self.collected_data["mood_tags"] = tags

            return FlowResult(
                next_step="intention",
                response_message="Thanks for sharing that.",
                prompt=FlowPrompt(
                    prompt="What's one thing on your mind today? (or type 'skip')",
                    input_type="text",
                ),
            )

        elif step == "intention":
            intention = str(value).strip() if value else None
            if intention and intention.lower() != "skip":
                self.collected_data["top_intention"] = intention

            # Flow complete
            return FlowResult(next_step=None)

        return FlowResult(
            next_step=None,
            response_message="Something went wrong. Let's wrap up.",
        )

    async def on_complete(self, context: UserContext) -> str:
        """Generate summary and return closing message."""
        mood = self.collected_data.get("mood_score", 5)
        energy = self.collected_data.get("energy_score", 5)
        tags = self.collected_data.get("mood_tags", [])
        intention = self.collected_data.get("top_intention")

        # Determine check-in type
        hour = datetime.now().hour
        self.collected_data["check_in_type"] = "morning" if hour < 14 else "evening"

        # Build personalized closing
        parts = []

        if energy <= 2:
            parts.append(
                "Your energy is really low right now. The only goal today is to be gentle with yourself. "
                "Even just breathing counts."
            )
        elif energy <= 4:
            parts.append(
                "Energy's on the lower side. Let's aim for just one tiny thing today — "
                "something that takes less than 2 minutes."
            )
        elif mood <= 3:
            parts.append(
                "It's a tough day. That's valid. You don't need to be productive to be worthwhile."
            )
        else:
            parts.append("Check-in complete.")

        if intention:
            if energy <= 3:
                parts.append(
                    f"You mentioned '{intention}' — what's the absolute smallest step toward that?"
                )
            else:
                parts.append(f"You're thinking about: {intention}. I'll check back on that.")

        parts.append("I'm here whenever you need me.")

        return " ".join(parts)

    def _parse_score(self, value: Any) -> int:
        try:
            score = int(value)
            return max(1, min(10, score))
        except (TypeError, ValueError):
            return 5  # Default middle ground

    def _parse_tags(self, value: Any) -> list[str]:
        if isinstance(value, list):
            return [t for t in value if t in self.MOOD_TAGS]
        if isinstance(value, str):
            return [t.strip() for t in value.split(",") if t.strip() in self.MOOD_TAGS]
        return []
