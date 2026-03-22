import pytest
from app.chat.engine import ConversationEngine
from app.models.check_in import CheckIn
from app.models.conversation import Conversation, Message
from app.models.user import User


class TestConversationEngine:
    @pytest.fixture
    def engine(self, test_user: User):
        return ConversationEngine(test_user)

    @pytest.mark.asyncio
    async def test_creates_new_conversation(self, engine):
        response = await engine.handle_message("Hello Mirror")
        assert response["type"] == "message"
        assert response["metadata"]["conversation_id"] is not None
        assert await Conversation.count() == 1

    @pytest.mark.asyncio
    async def test_saves_messages(self, engine):
        await engine.handle_message("I feel overwhelmed")
        messages = await Message.find_all().to_list()
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"

    @pytest.mark.asyncio
    async def test_reuses_conversation(self, engine):
        resp1 = await engine.handle_message("First")
        convo_id = resp1["metadata"]["conversation_id"]
        await engine.handle_message("Second", conversation_id=convo_id)
        assert await Conversation.count() == 1
        assert await Message.count() == 4

    @pytest.mark.asyncio
    async def test_crisis_detection(self, engine):
        response = await engine.handle_message("I want to kill myself")
        assert "988" in response["content"]

    @pytest.mark.asyncio
    async def test_low_energy_validation(self, engine):
        response = await engine.handle_message("I have no energy to do anything")
        lower = response["content"].lower()
        assert "should" not in lower
        assert "lazy" not in lower

    @pytest.mark.asyncio
    async def test_checkin_intent(self, engine):
        response = await engine.handle_message("I want to check in")
        assert response["metadata"].get("flow_active") is True
        assert response["metadata"].get("flow_id") == "check_in"

    @pytest.mark.asyncio
    async def test_reframe_intent(self, engine):
        response = await engine.handle_message("I need to reframe a negative thought")
        assert response["metadata"].get("flow_id") == "reframe"

    @pytest.mark.asyncio
    async def test_habit_intent(self, engine):
        response = await engine.handle_message("I want to build a habit")
        assert response["metadata"].get("flow_id") == "tiny_habit"

    @pytest.mark.asyncio
    async def test_checkin_saves_data(self, engine):
        resp = await engine.handle_message("check in")
        convo_id = resp["metadata"]["conversation_id"]
        await engine.handle_message("7", conversation_id=convo_id)
        await engine.handle_message("6", conversation_id=convo_id)
        await engine.handle_message("calm", conversation_id=convo_id)
        await engine.handle_message("skip", conversation_id=convo_id)
        check_ins = await CheckIn.find_all().to_list()
        assert len(check_ins) == 1
        assert check_ins[0].mood_score == 7

    @pytest.mark.asyncio
    async def test_default_response(self, engine):
        response = await engine.handle_message("Just thinking about life")
        assert len(response["content"]) > 10


class TestChatEndpoints:
    @pytest.mark.asyncio
    async def test_list_conversations_empty(self, auth_client):
        resp = await auth_client.get("/api/chat/conversations")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_requires_auth(self, client):
        resp = await client.get("/api/chat/conversations")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_messages_not_found(self, auth_client):
        resp = await auth_client.get("/api/chat/conversations/000000000000000000000000/messages")
        assert resp.status_code == 404
