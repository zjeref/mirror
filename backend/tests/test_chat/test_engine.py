"""Tests for the ConversationEngine - routing, intent detection, responses."""

import pytest
from sqlalchemy.orm import Session

from app.chat.engine import ConversationEngine
from app.models.check_in import CheckIn
from app.models.conversation import Conversation, Message
from app.models.user import User


class TestConversationEngine:
    @pytest.fixture
    def engine(self, db: Session, test_user: User):
        return ConversationEngine(db, test_user)

    @pytest.mark.asyncio
    async def test_creates_new_conversation(self, engine, db):
        response = await engine.handle_message("Hello Mirror")
        assert response["type"] == "message"
        assert response["sender"] == "mirror"
        assert response["metadata"]["conversation_id"] is not None

        convos = db.query(Conversation).all()
        assert len(convos) == 1

    @pytest.mark.asyncio
    async def test_saves_user_and_assistant_messages(self, engine, db):
        await engine.handle_message("I feel overwhelmed")

        messages = db.query(Message).order_by(Message.created_at).all()
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"

    @pytest.mark.asyncio
    async def test_reuses_existing_conversation(self, engine, db):
        resp1 = await engine.handle_message("First message")
        convo_id = resp1["metadata"]["conversation_id"]

        resp2 = await engine.handle_message("Second message", conversation_id=convo_id)
        assert resp2["metadata"]["conversation_id"] == convo_id
        assert db.query(Conversation).count() == 1
        assert db.query(Message).count() == 4

    @pytest.mark.asyncio
    async def test_crisis_detection_triggers_flow(self, engine, db):
        response = await engine.handle_message("I want to kill myself")
        assert "988" in response["content"]
        assert "Crisis Text Line" in response["content"] or "741741" in response["content"]

    @pytest.mark.asyncio
    async def test_low_energy_validation(self, engine, db):
        response = await engine.handle_message("I have no energy to do anything")
        lower = response["content"].lower()
        assert "valid" in lower or "real" in lower or "protecting" in lower
        assert "should" not in lower
        assert "lazy" not in lower

    @pytest.mark.asyncio
    async def test_checkin_intent_starts_flow(self, engine, db):
        response = await engine.handle_message("I want to check in")
        assert response["metadata"].get("flow_active") is True
        assert response["metadata"].get("flow_id") == "check_in"

    @pytest.mark.asyncio
    async def test_reframe_intent_detected(self, engine, db):
        response = await engine.handle_message("I need to reframe a negative thought")
        assert response["metadata"].get("flow_active") is True
        assert response["metadata"].get("flow_id") == "reframe"

    @pytest.mark.asyncio
    async def test_habit_intent_detected(self, engine, db):
        response = await engine.handle_message("I want to build a habit")
        assert response["metadata"].get("flow_active") is True
        assert response["metadata"].get("flow_id") == "tiny_habit"

    @pytest.mark.asyncio
    async def test_cognitive_distortion_flagged(self, engine, db):
        response = await engine.handle_message("I always fail at everything I try")
        lower = response["content"].lower()
        # Should either start reframe flow or mention the distortion
        has_distortion_mention = "all-or-nothing" in lower or "reframe" in lower
        has_flow = response["metadata"].get("flow_id") == "reframe"
        assert has_distortion_mention or has_flow

    @pytest.mark.asyncio
    async def test_overwhelm_gets_focused_response(self, engine, db):
        response = await engine.handle_message("I'm overwhelmed, there's too much to do")
        lower = response["content"].lower()
        assert "one" in lower  # Should focus on one thing

    @pytest.mark.asyncio
    async def test_checkin_flow_saves_data(self, engine, db):
        """Full check-in flow should save a CheckIn record."""
        # Start check-in
        resp = await engine.handle_message("check in")
        convo_id = resp["metadata"]["conversation_id"]

        # Process through the flow
        await engine.handle_message("7", conversation_id=convo_id)  # mood
        await engine.handle_message("6", conversation_id=convo_id)  # energy
        await engine.handle_message("calm", conversation_id=convo_id)  # tags
        await engine.handle_message("skip", conversation_id=convo_id)  # intention

        # Check that CheckIn was saved
        check_ins = db.query(CheckIn).all()
        assert len(check_ins) == 1
        assert check_ins[0].mood_score == 7
        assert check_ins[0].energy_score == 6

    @pytest.mark.asyncio
    async def test_default_response_is_welcoming(self, engine, db):
        response = await engine.handle_message("Just thinking about life")
        assert "hear you" in response["content"].lower()


class TestChatEndpoints:
    def test_list_conversations_empty(self, auth_client):
        response = auth_client.get("/api/chat/conversations")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_conversations_requires_auth(self, client):
        response = client.get("/api/chat/conversations")
        assert response.status_code in (401, 403)

    def test_get_messages_not_found(self, auth_client):
        response = auth_client.get("/api/chat/conversations/nonexistent/messages")
        assert response.status_code == 404
