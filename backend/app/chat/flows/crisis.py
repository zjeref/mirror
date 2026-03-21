"""Crisis safety flow - highest priority, always activates first.

This flow does NOT attempt therapy. It provides empathetic acknowledgment
and connects users to professional crisis resources.
"""

from typing import Any

from app.chat.flows.base import BaseFlow, FlowPrompt, FlowResult, UserContext
from app.chat.flows.registry import register_flow

CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end it all", "want to die", "self harm",
    "self-harm", "don't want to live", "no reason to live",
    "better off dead", "ending my life", "hurt myself",
    "not worth living", "take my life", "jump off", "overdose",
    "cut myself", "cutting myself",
]

CRISIS_RESPONSE = (
    "I hear you, and I'm really glad you're talking about this. "
    "What you're feeling is real and valid.\n\n"
    "Please reach out to people who can help right now:\n\n"
    "**988 Suicide & Crisis Lifeline** — Call or text **988** (US)\n"
    "**Crisis Text Line** — Text **HOME** to **741741**\n"
    "**International Association for Suicide Prevention** — https://www.iasp.info/resources/Crisis_Centres/\n\n"
    "You don't have to go through this alone. "
    "I'm here to talk, but these professionals are trained to help in ways I can't.\n\n"
    "Would you like to keep talking? I'm listening."
)


def contains_crisis_keywords(text: str) -> bool:
    """Check if text contains crisis-related keywords."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in CRISIS_KEYWORDS)


@register_flow
class CrisisFlow(BaseFlow):
    flow_id = "crisis"
    display_name = "Crisis Support"

    def get_steps(self) -> list[str]:
        return ["respond", "follow_up"]

    async def get_initial_prompt(self, context: UserContext) -> FlowResult:
        return FlowResult(
            next_step="follow_up",
            response_message=CRISIS_RESPONSE,
            prompt=FlowPrompt(
                prompt="",
                input_type="text",
            ),
        )

    async def handle_input(
        self, step: str, value: Any, context: UserContext
    ) -> FlowResult:
        # Stay in conversation, keep being supportive
        return FlowResult(
            next_step=None,
            response_message=(
                "I'm here. Take all the time you need. "
                "There's no pressure to say anything specific. "
                "If you want to talk about something else, that's okay too."
            ),
        )

    async def on_complete(self, context: UserContext) -> str:
        return (
            "Remember: 988 is always there, 24/7. "
            "And I'm here whenever you want to talk."
        )
