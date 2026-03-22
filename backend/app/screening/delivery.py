"""Conversational delivery of screening instruments via chat flows."""

import random
from typing import Any, Optional

from app.chat.flows.base import BaseFlow, FlowPrompt, FlowResult, UserContext
from app.screening.instruments import get_instrument, Instrument


_TRANSITIONS = [
    "Got it.",
    "Thank you.",
    "Noted.",
    "Thanks for sharing that.",
    "Understood.",
    "Okay, thank you.",
]


class ScreeningFlow(BaseFlow):
    """Delivers a screening instrument one question at a time through chat."""

    display_name: str = "Screening"

    def __init__(self, instrument_name: str):
        super().__init__()
        instrument = get_instrument(instrument_name)
        if instrument is None:
            raise ValueError(f"Unknown instrument: {instrument_name!r}")
        self.instrument: Instrument = instrument
        self.flow_id = f"screening_{instrument_name}"
        self.display_name = instrument.display_name
        self.collected_data["item_scores"] = []

    def get_steps(self) -> list[str]:
        return [f"item_{i}" for i in range(len(self.instrument.items))]

    async def get_initial_prompt(self, context: UserContext) -> FlowResult:
        item = self.instrument.items[0]
        intro = (
            f"I'd like to walk through a short check-in with you — "
            f"the {self.instrument.display_name}. "
            f"I'll ask you a few questions about how you've been feeling "
            f"over the past two weeks. There are no right or wrong answers.\n\n"
            f"{item.conversational}"
        )
        return FlowResult(
            next_step="item_0",
            response_message=intro,
            prompt=FlowPrompt(
                prompt=item.conversational,
                input_type="choice",
                options=list(self.instrument.response_options),
            ),
        )

    def _parse_response(self, value: Any) -> int:
        """Parse user response to a numeric score.

        Strategy: match label string -> int parse -> fallback 0.
        """
        if isinstance(value, str):
            # Try exact label match
            for idx, label in enumerate(self.instrument.response_options):
                if value.strip().lower() == label.lower():
                    return idx
            # Try int parse
            try:
                return int(value.strip())
            except (ValueError, TypeError):
                pass
        elif isinstance(value, (int, float)):
            return int(value)
        return 0

    async def handle_input(
        self, step: str, value: Any, context: UserContext
    ) -> FlowResult:
        score = self._parse_response(value)
        self.collected_data["item_scores"].append(score)

        step_idx = int(step.split("_")[1])
        next_idx = step_idx + 1
        steps = self.get_steps()

        if next_idx >= len(steps):
            # Flow complete — score it
            result = self.instrument.score(self.collected_data["item_scores"])
            self.collected_data.update(result)
            return FlowResult(next_step=None)

        # Build next question with warm transition
        next_item = self.instrument.items[next_idx]
        transition = random.choice(_TRANSITIONS)
        message = f"{transition} {next_item.conversational}"

        return FlowResult(
            next_step=steps[next_idx],
            response_message=message,
            prompt=FlowPrompt(
                prompt=next_item.conversational,
                input_type="choice",
                options=list(self.instrument.response_options),
            ),
        )

    async def on_complete(self, context: UserContext) -> str:
        total = self.collected_data.get("total_score", 0)
        return (
            f"Thank you for completing the {self.instrument.display_name}. "
            f"Your responses have been recorded. "
            f"I appreciate you taking the time to share how you've been feeling."
        )
