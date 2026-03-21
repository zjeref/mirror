"""CBT Reframing flow - guides user through challenging a negative thought."""

from typing import Any

from app.chat.flows.base import BaseFlow, FlowPrompt, FlowResult, UserContext
from app.chat.flows.registry import register_flow
from app.psychology.cbt import detect_distortions, generate_reframe


@register_flow
class ReframeFlow(BaseFlow):
    flow_id = "reframe"
    display_name = "Thought Reframing"

    def get_steps(self) -> list[str]:
        return ["capture_thought", "identify_emotion", "emotion_intensity", "reframe", "rate"]

    async def get_initial_prompt(self, context: UserContext) -> FlowResult:
        return FlowResult(
            next_step="capture_thought",
            response_message=(
                "Let's work through this thought together. "
                "Sometimes just looking at it from a different angle can shift something."
            ),
            prompt=FlowPrompt(
                prompt="What's the thought that's bothering you? Write it exactly as it sounds in your head.",
                input_type="text",
            ),
        )

    async def handle_input(
        self, step: str, value: Any, context: UserContext
    ) -> FlowResult:
        if step == "capture_thought":
            thought = str(value).strip()
            self.collected_data["automatic_thought"] = thought

            # Detect distortions immediately
            distortions = detect_distortions(thought)
            self.collected_data["distortions"] = [
                {"name": d.name, "display_name": d.display_name, "confidence": d.confidence}
                for d in distortions
            ]

            return FlowResult(
                next_step="identify_emotion",
                response_message="Thank you for sharing that.",
                prompt=FlowPrompt(
                    prompt="What emotion comes up when you think this thought?",
                    input_type="choice",
                    options=[
                        "anxious", "sad", "angry", "frustrated",
                        "ashamed", "hopeless", "overwhelmed", "other",
                    ],
                ),
            )

        elif step == "identify_emotion":
            emotion = str(value).strip()
            self.collected_data["emotion"] = emotion

            return FlowResult(
                next_step="emotion_intensity",
                response_message=f"Feeling {emotion}. That's valid.",
                prompt=FlowPrompt(
                    prompt=f"How intense is this {emotion} feeling right now? (1 = barely there, 10 = overwhelming)",
                    input_type="slider",
                    min_val=1,
                    max_val=10,
                ),
            )

        elif step == "emotion_intensity":
            try:
                intensity = max(1, min(10, int(value)))
            except (TypeError, ValueError):
                intensity = 5
            self.collected_data["emotion_intensity"] = intensity

            # Generate reframe based on detected distortions
            thought = self.collected_data["automatic_thought"]
            distortions = detect_distortions(thought)

            if distortions:
                top = distortions[0]
                reframe = generate_reframe(thought, top)
                self.collected_data["reframe"] = reframe.reframed_thought
                self.collected_data["distortion_name"] = top.display_name

                response = (
                    f"I notice something in what you said — it looks like **{top.display_name}**.\n\n"
                    f"_{top.explanation}_\n\n"
                    f"Here's another way to look at it:\n\n"
                    f"> {reframe.reframed_thought}"
                )
            else:
                # No clear distortion, offer a general reframe
                self.collected_data["reframe"] = (
                    f"What would you say to a close friend who told you: '{thought}'?"
                )
                response = (
                    "I hear the weight in what you're saying.\n\n"
                    f"Try this: What would you say to a close friend who told you: \"{thought}\"?\n\n"
                    "We're often kinder to others than to ourselves."
                )

            return FlowResult(
                next_step="rate",
                response_message=response,
                prompt=FlowPrompt(
                    prompt="How believable does this alternative perspective feel? (1 = not at all, 10 = very)",
                    input_type="slider",
                    min_val=1,
                    max_val=10,
                ),
            )

        elif step == "rate":
            try:
                rating = max(1, min(10, int(value)))
            except (TypeError, ValueError):
                rating = 5
            self.collected_data["reframe_believability"] = rating

            return FlowResult(next_step=None)

        return FlowResult(next_step=None)

    async def on_complete(self, context: UserContext) -> str:
        believability = self.collected_data.get("reframe_believability", 5)

        if believability >= 7:
            return (
                "That's great — the alternative perspective resonates. "
                "Try coming back to it next time this thought pops up. "
                "The more you practice, the more natural it becomes."
            )
        elif believability >= 4:
            return (
                "It doesn't need to feel 100% true right now. "
                "Even a small crack in the old thought pattern is progress. "
                "We can revisit this anytime."
            )
        else:
            return (
                "That's okay — reframes don't always land right away, and that's normal. "
                "The important thing is you looked at the thought instead of just believing it. "
                "That takes courage."
            )
