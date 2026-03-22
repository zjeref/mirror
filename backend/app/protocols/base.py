"""Base protocol definitions for structured therapeutic programs."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class HomeworkTier:
    """Three tiers of homework intensity, chosen based on user energy/engagement."""

    structured: str
    gentle: str
    minimal: str


@dataclass
class SessionDefinition:
    """A single session within a therapeutic protocol."""

    number: int
    focus: str
    goals: list[str]
    homework: HomeworkTier
    uses_existing_flow: str | None = None


class BaseProtocol(ABC):
    """Abstract base for all clinical protocols."""

    protocol_id: str
    display_name: str
    instrument: str
    min_score: int
    max_score: int
    mid_screening_session: int

    @property
    @abstractmethod
    def sessions(self) -> list[SessionDefinition]:
        """Return all session definitions for this protocol."""
        ...

    @property
    def total_sessions(self) -> int:
        return len(self.sessions)

    def get_session(self, number: int) -> SessionDefinition | None:
        for s in self.sessions:
            if s.number == number:
                return s
        return None

    def is_eligible(self, score: int, instrument: str) -> bool:
        if instrument != self.instrument:
            return False
        return self.min_score <= score <= self.max_score

    def get_homework(self, session_number: int, tier: str) -> str | None:
        session = self.get_session(session_number)
        if session is None:
            return None
        return getattr(session.homework, tier, None)
