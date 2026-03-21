"""Tests for the check-in flow."""

import pytest

from app.chat.flows.base import UserContext
from app.chat.flows.check_in import CheckInFlow


@pytest.fixture
def flow():
    return CheckInFlow()


@pytest.fixture
def context():
    return UserContext(user_id="test-user", user_name="Test")


class TestCheckInFlow:
    @pytest.mark.asyncio
    async def test_starts_with_greeting(self, flow, context):
        result = await flow.start(context)
        assert result.response_message  # Has greeting
        assert result.prompt is not None
        assert result.prompt.input_type == "slider"
        assert result.next_step == "mood"

    @pytest.mark.asyncio
    async def test_mood_then_energy(self, flow, context):
        await flow.start(context)
        result = await flow.process(7, context)  # mood = 7
        assert flow.collected_data["mood_score"] == 7
        assert result.next_step == "energy"
        assert result.prompt.input_type == "slider"

    @pytest.mark.asyncio
    async def test_low_mood_gets_validation(self, flow, context):
        await flow.start(context)
        result = await flow.process(2, context)  # mood = 2
        assert "low" in result.response_message.lower() or "hear" in result.response_message.lower()

    @pytest.mark.asyncio
    async def test_full_flow_completes(self, flow, context):
        await flow.start(context)
        await flow.process(5, context)  # mood
        await flow.process(6, context)  # energy
        await flow.process("calm,hopeful", context)  # mood tags
        result = await flow.process("Finish my project", context)  # intention

        assert flow.is_complete
        assert flow.collected_data["mood_score"] == 5
        assert flow.collected_data["energy_score"] == 6
        assert flow.collected_data.get("top_intention") == "Finish my project"

    @pytest.mark.asyncio
    async def test_low_energy_closing_is_gentle(self, flow, context):
        await flow.start(context)
        await flow.process(3, context)  # mood
        await flow.process(1, context)  # energy = 1
        await flow.process("numb", context)  # mood tags
        result = await flow.process("skip", context)  # skip intention

        assert flow.is_complete
        assert result.response_message is not None
        lower = result.response_message.lower()
        assert "gentle" in lower or "breathe" in lower or "counts" in lower

    @pytest.mark.asyncio
    async def test_skip_intention_works(self, flow, context):
        await flow.start(context)
        await flow.process(5, context)
        await flow.process(5, context)
        await flow.process("calm", context)
        await flow.process("skip", context)

        assert "top_intention" not in flow.collected_data

    @pytest.mark.asyncio
    async def test_clamps_scores_to_valid_range(self, flow, context):
        await flow.start(context)
        await flow.process(15, context)  # Over max
        assert flow.collected_data["mood_score"] == 10

        await flow.process(-3, context)  # Under min
        assert flow.collected_data["energy_score"] == 1
