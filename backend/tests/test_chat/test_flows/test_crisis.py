"""Tests for crisis flow - safety critical, must be thorough."""

import pytest

from app.chat.flows.base import UserContext
from app.chat.flows.crisis import CrisisFlow, contains_crisis_keywords


class TestCrisisDetection:
    """Crisis detection must NEVER miss a true positive."""

    @pytest.mark.parametrize("text", [
        "I want to kill myself",
        "I'm thinking about suicide",
        "I want to end it all",
        "I don't want to live anymore",
        "I want to hurt myself",
        "thinking about self harm",
        "I'd be better off dead",
        "there's no reason to live",
        "I want to take my life",
    ])
    def test_detects_crisis_keywords(self, text):
        assert contains_crisis_keywords(text), f"Failed to detect crisis in: '{text}'"

    @pytest.mark.parametrize("text", [
        "I had a great day",
        "I'm feeling tired",
        "Work was stressful",
        "I'm sad today",
        "I don't want to go to work",
    ])
    def test_no_false_positives_on_normal_text(self, text):
        assert not contains_crisis_keywords(text), f"False positive on: '{text}'"


class TestCrisisFlow:
    @pytest.fixture
    def flow(self):
        return CrisisFlow()

    @pytest.fixture
    def context(self):
        return UserContext(user_id="test-user", user_name="Test")

    @pytest.mark.asyncio
    async def test_provides_crisis_resources(self, flow, context):
        result = await flow.start(context)
        content = result.response_message
        assert "988" in content  # Suicide hotline
        assert "741741" in content  # Crisis text line

    @pytest.mark.asyncio
    async def test_never_dismissive(self, flow, context):
        result = await flow.start(context)
        content = result.response_message.lower()
        assert "just" not in content or "just talk" in content  # "just cheer up" type language
        assert "overreacting" not in content

    @pytest.mark.asyncio
    async def test_validates_feelings(self, flow, context):
        result = await flow.start(context)
        content = result.response_message.lower()
        assert any(word in content for word in ["hear", "valid", "real", "glad"])
