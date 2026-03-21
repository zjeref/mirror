"""ConversationEngine - Routes messages to structured flows or generates responses."""

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

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
from app.psychology.cbt import detect_distortions
from app.psychology.energy import get_mva, get_validation
from app.psychology.suggestions import UserState, suggest


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

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.active_flows: dict[str, BaseFlow] = {}  # conversation_id -> active flow

    def _build_user_context(self) -> UserContext:
        return UserContext(
            user_id=self.user.id,
            user_name=self.user.name,
        )

    async def handle_message(
        self,
        content: str,
        conversation_id: Optional[str] = None,
    ) -> dict:
        """Process an incoming user message and generate a response."""
        conversation = self._get_or_create_conversation(conversation_id)
        context = self._build_user_context()

        # Save user message
        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            content=content,
        )
        self.db.add(user_msg)
        self.db.commit()

        # Route to active flow or detect intent
        response = await self._route_message(content, conversation, context)

        # Save assistant message
        assistant_msg = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=response["content"],
            metadata_=response.get("metadata"),
        )
        self.db.add(assistant_msg)
        self.db.commit()

        response["metadata"] = response.get("metadata", {})
        response["metadata"]["conversation_id"] = conversation.id
        return response

    async def handle_flow_response(
        self,
        conversation_id: str,
        flow_id: str,
        step: str,
        value: Any,
    ) -> dict:
        """Handle a structured flow response."""
        conversation = self._get_or_create_conversation(conversation_id)
        context = self._build_user_context()

        flow = self.active_flows.get(conversation_id)
        if not flow or flow.flow_id != flow_id:
            return self._make_response("That flow isn't active. Let's start fresh.")

        result = await flow.process(value, context)

        if flow.is_complete:
            self._on_flow_complete(flow, conversation)
            del self.active_flows[conversation_id]

        return self._flow_result_to_response(result, flow, conversation.id)

    async def _route_message(
        self, content: str, conversation: Conversation, context: UserContext
    ) -> dict:
        """Route message to the appropriate handler."""

        # Priority 1: Crisis detection (ALWAYS first)
        if contains_crisis_keywords(content):
            return await self._start_flow("crisis", conversation, context)

        # Priority 2: Active flow
        flow = self.active_flows.get(conversation.id)
        if flow and not flow.is_complete:
            result = await flow.process(content, context)
            if flow.is_complete:
                self._on_flow_complete(flow, conversation)
                del self.active_flows[conversation.id]
            return self._flow_result_to_response(result, flow, conversation.id)

        # Priority 3: Intent detection
        detected_intent = self._detect_intent(content)
        if detected_intent:
            return await self._start_flow(detected_intent, conversation, context)

        # Priority 4: Psychology-informed response
        return self._generate_smart_response(content, context)

    def _detect_intent(self, content: str) -> Optional[str]:
        """Detect user intent from message content."""
        content_lower = content.lower()

        for intent, patterns in INTENT_PATTERNS.items():
            for pattern in patterns:
                if pattern in content_lower:
                    return intent

        return None

    async def _start_flow(
        self, flow_id: str, conversation: Conversation, context: UserContext
    ) -> dict:
        """Start a new structured flow."""
        flow_class = get_flow_class(flow_id)
        if not flow_class:
            return self._make_response("I don't recognize that flow.")

        flow = flow_class()
        result = await flow.start(context)

        if not flow.is_complete:
            self.active_flows[conversation.id] = flow

        return self._flow_result_to_response(result, flow, conversation.id)

    def _generate_smart_response(self, content: str, context: UserContext) -> dict:
        """Generate a psychology-informed response for freeform messages."""
        content_lower = content.lower()

        # Check for low energy signals
        low_energy_phrases = [
            "no energy", "exhausted", "can't do anything", "too tired",
            "burned out", "burnout", "can't get up", "so tired",
            "don't have the energy", "drained",
        ]
        if any(phrase in content_lower for phrase in low_energy_phrases):
            mva = get_mva("physical", 2)
            return self._make_response(
                f"{mva.validation}\n\n"
                f"If you want to do one tiny thing: {mva.action}\n\n"
                f"But honestly, just resting is valid too."
            )

        # Check for cognitive distortions
        distortions = detect_distortions(content)
        if distortions and distortions[0].confidence >= 0.6:
            top = distortions[0]
            return self._make_response(
                f"I notice something in what you said — it sounds like it might be "
                f"**{top.display_name}**: {top.explanation}\n\n"
                f"Want to work through this with a thought reframing exercise? "
                f"Just say 'reframe' and we'll do it together."
            )

        # Check for overwhelm
        overwhelm_phrases = [
            "overwhelmed", "too much", "can't handle", "don't know where to start",
            "everything is", "falling apart",
        ]
        if any(phrase in content_lower for phrase in overwhelm_phrases):
            return self._make_response(
                "When everything feels like too much, the answer isn't to do more — "
                "it's to do less, but deliberately.\n\n"
                "What's the ONE thing that, if you did it today, would make you feel "
                "even slightly better? Just one. We start there."
            )

        # Default: empathetic, curious response
        return self._make_response(
            "I hear you. Tell me more about what's on your mind. "
            "I'm here to listen and help you figure out the smallest next step."
        )

    def _flow_result_to_response(
        self, result: FlowResult, flow: BaseFlow, conversation_id: str
    ) -> dict:
        """Convert a FlowResult to a WebSocket response dict."""
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

        # If there's a prompt, send it as a separate flow_prompt
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

    def _on_flow_complete(self, flow: BaseFlow, conversation: Conversation):
        """Handle flow completion - save structured data to DB."""
        if flow.flow_id == "check_in":
            self._save_check_in(flow, conversation)

    def _save_check_in(self, flow: BaseFlow, conversation: Conversation):
        """Save check-in data from completed flow."""
        data = flow.collected_data
        check_in = CheckIn(
            user_id=self.user.id,
            check_in_type=data.get("check_in_type", "ad_hoc"),
            mood_score=data.get("mood_score", 5),
            energy_score=data.get("energy_score", 5),
            mood_tags=data.get("mood_tags"),
            top_intention=data.get("top_intention"),
            conversation_id=conversation.id,
        )
        self.db.add(check_in)
        self.db.commit()

    def _get_or_create_conversation(self, conversation_id: Optional[str]) -> Conversation:
        if conversation_id:
            conversation = (
                self.db.query(Conversation)
                .filter(
                    Conversation.id == conversation_id,
                    Conversation.user_id == self.user.id,
                )
                .first()
            )
            if conversation:
                return conversation

        conversation = Conversation(
            user_id=self.user.id,
            conversation_type="freeform",
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def _make_response(self, content: str) -> dict:
        return {
            "type": "message",
            "content": content,
            "sender": "mirror",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {"flow_active": False},
        }
