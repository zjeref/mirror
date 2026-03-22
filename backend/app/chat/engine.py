"""ConversationEngine - Routes messages to structured flows or generates responses."""

from datetime import datetime, timezone
from typing import Any, Optional

from app.chat.flows.base import BaseFlow, FlowResult, UserContext
from app.chat.flows.crisis import contains_crisis_keywords
from app.chat.flows.registry import get_flow_class

# Import flows to trigger registration
import app.chat.flows.check_in  # noqa: F401
import app.chat.flows.crisis  # noqa: F401
import app.chat.flows.reframe  # noqa: F401
import app.chat.flows.tiny_habit  # noqa: F401

from app.models.check_in import CheckIn
from app.models.conversation import Conversation, Message
from app.models.user import User


# Intent detection patterns
INTENT_PATTERNS: dict[str, list[str]] = {
    "check_in": [
        "check in", "checkin", "check-in", "how am i doing",
        "daily check", "morning check", "evening check",
    ],
    "reframe": [
        "i keep thinking", "i can't stop thinking", "negative thought",
        "reframe", "thought record", "challenge this thought",
        "i always fail", "i'm a failure", "i'm worthless", "nothing works",
        "i'm stupid", "i'm broken",
    ],
    "tiny_habit": [
        "build a habit", "new habit", "start a habit", "tiny habit",
        "create a habit", "habit", "routine",
    ],
}


class ConversationEngine:
    """Orchestrates chat: routes to flows, detects intent, generates responses."""

    def __init__(self, user: User):
        self.user = user
        self.active_flows: dict[str, BaseFlow] = {}

    def _build_user_context(self) -> UserContext:
        return UserContext(user_id=str(self.user.id), user_name=self.user.name)

    async def handle_message(
        self, content: str, conversation_id: Optional[str] = None,
    ) -> dict:
        conversation = await self._get_or_create_conversation(conversation_id)
        context = self._build_user_context()

        user_msg = Message(conversation_id=str(conversation.id), role="user", content=content)
        await user_msg.insert()

        response = await self._route_message(content, conversation, context)

        assistant_msg = Message(
            conversation_id=str(conversation.id),
            role="assistant",
            content=response["content"],
            metadata_=response.get("metadata"),
        )
        await assistant_msg.insert()

        response["metadata"] = response.get("metadata", {})
        response["metadata"]["conversation_id"] = str(conversation.id)
        return response

    async def _route_message(
        self, content: str, conversation: Conversation, context: UserContext
    ) -> dict:
        if contains_crisis_keywords(content):
            return await self._start_flow("crisis", conversation, context)

        flow = self.active_flows.get(str(conversation.id))
        if flow and not flow.is_complete:
            result = await flow.process(content, context)
            if flow.is_complete:
                await self._on_flow_complete(flow, conversation)
                del self.active_flows[str(conversation.id)]
            return self._flow_result_to_response(result, flow, str(conversation.id))

        detected_intent = self._detect_intent(content)
        if detected_intent:
            return await self._start_flow(detected_intent, conversation, context)

        return await self._generate_smart_response(content, conversation, context)

    def _detect_intent(self, content: str) -> Optional[str]:
        content_lower = content.lower()
        for intent, patterns in INTENT_PATTERNS.items():
            for pattern in patterns:
                if pattern in content_lower:
                    return intent
        return None

    async def _start_flow(
        self, flow_id: str, conversation: Conversation, context: UserContext
    ) -> dict:
        flow_class = get_flow_class(flow_id)
        if not flow_class:
            return self._make_response("I don't recognize that flow.")

        flow = flow_class()
        result = await flow.start(context)
        if not flow.is_complete:
            self.active_flows[str(conversation.id)] = flow
        return self._flow_result_to_response(result, flow, str(conversation.id))

    async def _generate_smart_response(
        self, content: str, conversation: Conversation, context: UserContext
    ) -> dict:
        from app.chat.llm.client import generate_response

        recent_messages = await Message.find(
            Message.conversation_id == str(conversation.id)
        ).sort("-created_at").limit(20).to_list()
        recent_messages.reverse()

        history = [
            {"role": msg.role, "content": msg.content}
            for msg in recent_messages
            if msg.role in ("user", "assistant")
        ]

        user_context_parts = [f"User's name: {context.user_name}"]
        latest_checkin = await CheckIn.find(
            CheckIn.user_id == str(self.user.id)
        ).sort("-created_at").first_or_none()

        if latest_checkin:
            user_context_parts.append(
                f"Last check-in: mood {latest_checkin.mood_score}/10, "
                f"energy {latest_checkin.energy_score}/10"
            )
            if latest_checkin.mood_tags:
                user_context_parts.append(f"Recent mood tags: {', '.join(latest_checkin.mood_tags)}")

        response_text = await generate_response(
            user_message=content,
            conversation_history=history,
            user_context="\n".join(user_context_parts),
        )
        return self._make_response(response_text)

    def _flow_result_to_response(
        self, result: FlowResult, flow: BaseFlow, conversation_id: str
    ) -> dict:
        response = {
            "type": "message",
            "content": result.response_message or "",
            "sender": "mirror",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "conversation_id": conversation_id,
                "flow_active": not flow.is_complete,
                "flow_id": flow.flow_id,
            },
        }
        if result.prompt and not flow.is_complete:
            response["flow_prompt"] = {
                "type": "flow_prompt",
                "flow_id": flow.flow_id,
                "step": result.next_step,
                "prompt": result.prompt.prompt,
                "input_type": result.prompt.input_type,
                "options": result.prompt.options,
                "min_val": result.prompt.min_val,
                "max_val": result.prompt.max_val,
            }
        return response

    async def _on_flow_complete(self, flow: BaseFlow, conversation: Conversation):
        if flow.flow_id == "check_in":
            await self._save_check_in(flow, conversation)

    async def _save_check_in(self, flow: BaseFlow, conversation: Conversation):
        data = flow.collected_data
        check_in = CheckIn(
            user_id=str(self.user.id),
            check_in_type=data.get("check_in_type", "ad_hoc"),
            mood_score=data.get("mood_score", 5),
            energy_score=data.get("energy_score", 5),
            mood_tags=data.get("mood_tags"),
            top_intention=data.get("top_intention"),
            conversation_id=str(conversation.id),
        )
        await check_in.insert()

    async def _get_or_create_conversation(self, conversation_id: Optional[str]) -> Conversation:
        if conversation_id:
            conversation = await Conversation.get(conversation_id)
            if conversation and conversation.user_id == str(self.user.id):
                return conversation

        conversation = Conversation(user_id=str(self.user.id), conversation_type="freeform")
        await conversation.insert()
        return conversation

    def _make_response(self, content: str) -> dict:
        return {
            "type": "message",
            "content": content,
            "sender": "mirror",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {"flow_active": False},
        }
