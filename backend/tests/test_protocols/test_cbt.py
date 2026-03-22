"""Tests for CBT Depression, Anxiety, and Behavioral Activation protocols."""

from app.protocols.cbt_depression import CBTDepressionProtocol
from app.protocols.anxiety import AnxietyProtocol
from app.protocols.behavioral_activation import BehavioralActivationProtocol


class TestCBTDepressionProtocol:
    def setup_method(self):
        self.protocol = CBTDepressionProtocol()

    def test_has_8_sessions(self):
        assert self.protocol.total_sessions == 8

    def test_sessions_are_sequential(self):
        numbers = [s.number for s in self.protocol.sessions]
        assert numbers == [1, 2, 3, 4, 5, 6, 7, 8]

    def test_all_sessions_have_homework_tiers(self):
        for session in self.protocol.sessions:
            assert session.homework.structured
            assert session.homework.gentle
            assert session.homework.minimal

    def test_protocol_metadata(self):
        assert self.protocol.protocol_id == "cbt_depression"
        assert self.protocol.instrument == "phq9"
        assert self.protocol.min_score == 5
        assert self.protocol.max_score == 19
        assert self.protocol.mid_screening_session == 4

    def test_eligible_for_moderate_phq9(self):
        assert self.protocol.is_eligible(12, "phq9") is True

    def test_not_eligible_for_severe_phq9(self):
        assert self.protocol.is_eligible(22, "phq9") is False

    def test_not_eligible_for_gad7(self):
        assert self.protocol.is_eligible(12, "gad7") is False

    def test_get_session_by_number(self):
        session = self.protocol.get_session(1)
        assert session is not None
        assert session.number == 1
        assert "psychoeducation" in session.focus.lower()

    def test_get_session_invalid_number(self):
        assert self.protocol.get_session(99) is None

    def test_thought_catching_uses_reframe_flow(self):
        session = self.protocol.get_session(4)
        assert session is not None
        assert session.uses_existing_flow == "reframe"

    def test_get_homework_structured(self):
        hw = self.protocol.get_homework(1, "structured")
        assert hw is not None
        assert isinstance(hw, str)
        assert len(hw) > 0

    def test_get_homework_gentle(self):
        hw = self.protocol.get_homework(1, "gentle")
        assert hw is not None

    def test_get_homework_minimal(self):
        hw = self.protocol.get_homework(1, "minimal")
        assert hw is not None

    def test_get_homework_invalid_session(self):
        hw = self.protocol.get_homework(99, "structured")
        assert hw is None


class TestAnxietyProtocol:
    def setup_method(self):
        self.protocol = AnxietyProtocol()

    def test_has_7_sessions(self):
        assert self.protocol.total_sessions == 7

    def test_sessions_are_sequential(self):
        numbers = [s.number for s in self.protocol.sessions]
        assert numbers == [1, 2, 3, 4, 5, 6, 7]

    def test_protocol_metadata(self):
        assert self.protocol.protocol_id == "anxiety"
        assert self.protocol.instrument == "gad7"
        assert self.protocol.min_score == 5
        assert self.protocol.max_score == 19
        assert self.protocol.mid_screening_session == 4

    def test_eligible_for_moderate_gad7(self):
        assert self.protocol.is_eligible(12, "gad7") is True

    def test_not_eligible_for_phq9(self):
        assert self.protocol.is_eligible(12, "phq9") is False

    def test_all_sessions_have_homework(self):
        for session in self.protocol.sessions:
            assert session.homework.structured
            assert session.homework.gentle
            assert session.homework.minimal


class TestBehavioralActivationProtocol:
    def setup_method(self):
        self.protocol = BehavioralActivationProtocol()

    def test_has_6_sessions(self):
        assert self.protocol.total_sessions == 6

    def test_sessions_are_sequential(self):
        numbers = [s.number for s in self.protocol.sessions]
        assert numbers == [1, 2, 3, 4, 5, 6]

    def test_protocol_metadata(self):
        assert self.protocol.protocol_id == "behavioral_activation"
        assert self.protocol.instrument == "phq9"
        assert self.protocol.min_score == 5
        assert self.protocol.max_score == 19
        assert self.protocol.mid_screening_session == 3

    def test_skip_sessions_on_switch(self):
        assert self.protocol.skip_sessions_on_switch == [1, 2]

    def test_values_session_uses_values_flow(self):
        session = self.protocol.get_session(2)
        assert session is not None
        assert session.uses_existing_flow == "values"

    def test_eligible_for_moderate_phq9(self):
        assert self.protocol.is_eligible(8, "phq9") is True

    def test_all_sessions_have_homework(self):
        for session in self.protocol.sessions:
            assert session.homework.structured
            assert session.homework.gentle
            assert session.homework.minimal
