"""Protocol registry for looking up and filtering clinical protocols."""

from app.protocols.base import BaseProtocol
from app.protocols.cbt_depression import CBTDepressionProtocol
from app.protocols.anxiety import AnxietyProtocol
from app.protocols.behavioral_activation import BehavioralActivationProtocol

_PROTOCOLS: dict[str, BaseProtocol] = {
    "cbt_depression": CBTDepressionProtocol(),
    "anxiety": AnxietyProtocol(),
    "behavioral_activation": BehavioralActivationProtocol(),
}


def get_protocol(protocol_id: str) -> BaseProtocol | None:
    """Get a protocol by its ID."""
    return _PROTOCOLS.get(protocol_id)


def get_eligible_protocols(instrument: str, score: int) -> list[BaseProtocol]:
    """Return all protocols eligible for the given instrument and score."""
    return [p for p in _PROTOCOLS.values() if p.is_eligible(score, instrument)]
