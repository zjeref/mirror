"""Tests for protocol registry."""

from app.protocols.registry import get_protocol, get_eligible_protocols
from app.protocols.cbt_depression import CBTDepressionProtocol
from app.protocols.anxiety import AnxietyProtocol
from app.protocols.behavioral_activation import BehavioralActivationProtocol


class TestGetProtocol:
    def test_get_cbt_depression(self):
        p = get_protocol("cbt_depression")
        assert p is not None
        assert isinstance(p, CBTDepressionProtocol)

    def test_get_anxiety(self):
        p = get_protocol("anxiety")
        assert p is not None
        assert isinstance(p, AnxietyProtocol)

    def test_get_behavioral_activation(self):
        p = get_protocol("behavioral_activation")
        assert p is not None
        assert isinstance(p, BehavioralActivationProtocol)

    def test_get_unknown_returns_none(self):
        assert get_protocol("nonexistent") is None


class TestGetEligibleProtocols:
    def test_phq9_moderate_returns_cbt_and_ba(self):
        protocols = get_eligible_protocols("phq9", 12)
        ids = {p.protocol_id for p in protocols}
        assert "cbt_depression" in ids
        assert "behavioral_activation" in ids
        assert "anxiety" not in ids

    def test_gad7_moderate_returns_anxiety_only(self):
        protocols = get_eligible_protocols("gad7", 12)
        ids = {p.protocol_id for p in protocols}
        assert ids == {"anxiety"}

    def test_severe_score_returns_empty(self):
        protocols = get_eligible_protocols("phq9", 22)
        assert protocols == []

    def test_minimal_score_returns_empty(self):
        protocols = get_eligible_protocols("phq9", 3)
        assert protocols == []

    def test_unknown_instrument_returns_empty(self):
        protocols = get_eligible_protocols("unknown", 12)
        assert protocols == []
