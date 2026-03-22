"""Tests for base protocol structures."""

from app.protocols.base import HomeworkTier, SessionDefinition


class TestHomeworkTier:
    def test_has_all_tiers(self):
        hw = HomeworkTier(
            structured="Do a full worksheet",
            gentle="Try noticing one thought",
            minimal="Just breathe today",
        )
        assert hw.structured == "Do a full worksheet"
        assert hw.gentle == "Try noticing one thought"
        assert hw.minimal == "Just breathe today"


class TestSessionDefinition:
    def test_basic_session(self):
        hw = HomeworkTier(
            structured="Write 3 thoughts",
            gentle="Notice 1 thought",
            minimal="Rest",
        )
        session = SessionDefinition(
            number=1,
            focus="Psychoeducation",
            goals=["Understand CBT model", "Normalize experience"],
            homework=hw,
            uses_existing_flow=None,
        )
        assert session.number == 1
        assert session.focus == "Psychoeducation"
        assert len(session.goals) == 2
        assert session.uses_existing_flow is None

    def test_session_with_existing_flow(self):
        hw = HomeworkTier(
            structured="s", gentle="g", minimal="m"
        )
        session = SessionDefinition(
            number=4,
            focus="Thought Catching",
            goals=["Identify automatic thoughts"],
            homework=hw,
            uses_existing_flow="reframe",
        )
        assert session.uses_existing_flow == "reframe"
