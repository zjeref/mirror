"""Tests for conversational screening flow delivery."""

import pytest
from app.screening.delivery import ScreeningFlow
from app.chat.flows.base import UserContext, FlowPrompt


@pytest.fixture
def user_context():
    return UserContext(user_id="test-user-123", user_name="Test User")


@pytest.fixture
def phq9_flow():
    return ScreeningFlow("phq9")


@pytest.fixture
def gad7_flow():
    return ScreeningFlow("gad7")


class TestScreeningFlowSetup:
    def test_flow_id(self, phq9_flow):
        assert phq9_flow.flow_id == "screening_phq9"

    def test_get_steps_phq9_returns_9(self, phq9_flow):
        steps = phq9_flow.get_steps()
        assert len(steps) == 9
        assert steps[0] == "item_0"
        assert steps[8] == "item_8"

    def test_get_steps_gad7_returns_7(self, gad7_flow):
        steps = gad7_flow.get_steps()
        assert len(steps) == 7

    def test_unknown_instrument_raises(self):
        with pytest.raises(ValueError):
            ScreeningFlow("unknown_instrument")


class TestScreeningFlowStart:
    @pytest.mark.asyncio
    async def test_phq9_starts_with_intro_and_choice(self, phq9_flow, user_context):
        result = await phq9_flow.start(user_context)
        assert result.response_message is not None
        assert result.prompt is not None
        assert result.prompt.input_type == "choice"
        assert result.prompt.options == [
            "Not at all",
            "Several days",
            "More than half the days",
            "Nearly every day",
        ]
        assert result.next_step == "item_0"


class TestScreeningFlowCompletion:
    @pytest.mark.asyncio
    async def test_phq9_full_several_days(self, phq9_flow, user_context):
        """9 'Several days' answers → total_score=9, severity_tier='mild'."""
        await phq9_flow.start(user_context)

        for i in range(9):
            result = await phq9_flow.process("Several days", user_context)

        assert phq9_flow.is_complete
        assert phq9_flow.collected_data["instrument"] == "phq9"
        assert phq9_flow.collected_data["item_scores"] == [1] * 9
        assert phq9_flow.collected_data["total_score"] == 9
        assert phq9_flow.collected_data["severity_tier"] == "mild"

    @pytest.mark.asyncio
    async def test_gad7_full_not_at_all(self, gad7_flow, user_context):
        """7 'Not at all' answers → total_score=0."""
        await gad7_flow.start(user_context)

        for i in range(7):
            result = await gad7_flow.process("Not at all", user_context)

        assert gad7_flow.is_complete
        assert gad7_flow.collected_data["total_score"] == 0

    @pytest.mark.asyncio
    async def test_nearly_every_day_maps_to_3(self, phq9_flow, user_context):
        """'Nearly every day' should map to score 3."""
        await phq9_flow.start(user_context)

        # Answer first question with "Nearly every day"
        result = await phq9_flow.process("Nearly every day", user_context)

        assert phq9_flow.collected_data["item_scores"][0] == 3


class TestResponseParsing:
    @pytest.mark.asyncio
    async def test_int_fallback(self, phq9_flow, user_context):
        """Numeric input falls back to int parsing."""
        await phq9_flow.start(user_context)
        await phq9_flow.process("2", user_context)
        assert phq9_flow.collected_data["item_scores"][0] == 2

    @pytest.mark.asyncio
    async def test_garbage_fallback_to_zero(self, phq9_flow, user_context):
        """Unrecognized input falls back to 0."""
        await phq9_flow.start(user_context)
        await phq9_flow.process("banana", user_context)
        assert phq9_flow.collected_data["item_scores"][0] == 0


class TestWarmTransitions:
    @pytest.mark.asyncio
    async def test_transition_messages_present(self, phq9_flow, user_context):
        """Each intermediate response includes a warm transition."""
        await phq9_flow.start(user_context)

        result = await phq9_flow.process("Not at all", user_context)
        # Should have a response message with transition + next question
        assert result.response_message is not None
        assert result.prompt is not None
        assert result.prompt.input_type == "choice"
