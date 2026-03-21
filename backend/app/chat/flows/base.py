"""Base class for structured therapeutic conversation flows."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class FlowPrompt:
    """A prompt to send to the user during a flow."""

    prompt: str
    input_type: str = "text"  # text | slider | choice | mood_picker
    options: Optional[list[str]] = None
    min_val: Optional[int] = None
    max_val: Optional[int] = None


@dataclass
class FlowResult:
    """Result of processing user input in a flow step."""

    next_step: Optional[str] = None  # None means flow is complete
    response_message: Optional[str] = None  # Message to send to user
    prompt: Optional[FlowPrompt] = None  # Next prompt if continuing
    data: dict = field(default_factory=dict)  # Extracted data from this step


@dataclass
class UserContext:
    """Context about the user passed to flows."""

    user_id: str
    user_name: str
    energy_level: Optional[int] = None
    mood_score: Optional[int] = None
    last_check_in_type: Optional[str] = None
    active_patterns: list = field(default_factory=list)
    life_area_scores: dict = field(default_factory=dict)


class BaseFlow(ABC):
    """Abstract base class for structured conversation flows.

    Each flow is a state machine with named steps.
    Steps produce prompts and consume user responses.
    """

    flow_id: str
    display_name: str

    def __init__(self):
        self.state: dict[str, Any] = {}
        self.current_step: Optional[str] = None
        self.collected_data: dict[str, Any] = {}
        self.is_complete: bool = False

    @abstractmethod
    def get_steps(self) -> list[str]:
        """Return ordered list of step names."""
        ...

    @abstractmethod
    async def get_initial_prompt(self, context: UserContext) -> FlowResult:
        """Generate the first prompt to start the flow."""
        ...

    @abstractmethod
    async def handle_input(
        self, step: str, value: Any, context: UserContext
    ) -> FlowResult:
        """Process user input for the current step."""
        ...

    @abstractmethod
    async def on_complete(self, context: UserContext) -> str:
        """Called when flow finishes. Returns summary message."""
        ...

    async def start(self, context: UserContext) -> FlowResult:
        """Start the flow."""
        result = await self.get_initial_prompt(context)
        self.current_step = result.next_step
        return result

    async def process(self, value: Any, context: UserContext) -> FlowResult:
        """Process input for the current step and advance."""
        if self.current_step is None:
            return FlowResult(response_message="Flow has not been started.")

        result = await self.handle_input(self.current_step, value, context)

        if result.next_step is None:
            self.is_complete = True
            summary = await self.on_complete(context)
            result.response_message = summary

        self.current_step = result.next_step
        return result
