"""ConversationEngine - Routes messages to structured flows or generates responses.

Safety-first routing:
1. Keyword crisis check (instant, <1ms)
2. LLM risk assessment check (from previous message's state)
3. Slow escalation detection (mood trending down)
4. Active flow routing
5. Intent detection → start flow
6. LLM freeform response + state assessment
"""

from datetime import datetime, timezone
from typing import Any, Optional

from app.chat.flows.base import BaseFlow, FlowResult, UserContext
from app.chat.flows.crisis import (
    contains_crisis_keywords,
    check_llm_risk,
    check_slow_escalation,
    log_crisis_event,
)
from app.chat.flows.registry import get_flow_class
from app.sessions.engine import SessionEngine

import app.chat.flows.check_in  # noqa: F401
import app.chat.flows.crisis  # noqa: F401
import app.chat.flows.reframe  # noqa: F401
import app.chat.flows.tiny_habit  # noqa: F401
import app.chat.flows.values  # noqa: F401
import app.chat.flows.program  # noqa: F401

from app.models.check_in import CheckIn
from app.models.conversation import Conversation, Message
from app.models.user import User


INTENT_PATTERNS: dict[str, list[str]] = {
    "check_in": [
        "check in", "checkin", "check-in", "how am i doing",
        "daily check", "morning check", "evening check",
    ],
    "reframe": [
        "i keep thinking", "i can't stop thinking", "negative thought",
        "reframe", "thought record", "challenge this thought",
    ],
    "tiny_habit": [
        "build a habit", "new habit", "start a habit", "tiny habit",
        "create a habit",
    ],
    "values": [
        "what matters", "my values", "values exploration", "explore values",
        "what do i care about", "life purpose", "find my purpose",
    ],
    "program": [
        "start a program", "belief reset", "structured program",
        "7 day", "7-day", "daily program", "start the journey",
    ],
}


class ConversationEngine:
    def __init__(self, user: User):
        self.user = user
        self.active_flows: dict[str, BaseFlow] = {}
        self._message_count: int = 0  # Track for conversation length management
        self.session_engine = SessionEngine(user)

    def _build_user_context(self) -> UserContext:
        return UserContext(user_id=str(self.user.id), user_name=self.user.name)

    async def handle_message(
        self, content: str, conversation_id: Optional[str] = None,
    ) -> dict:
        conversation = await self._get_or_create_conversation(conversation_id)
        context = self._build_user_context()
        self._message_count += 1

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
        user_id = str(self.user.id)

        # Safety Priority 1: Keyword crisis check (instant)
        if contains_crisis_keywords(content):
            await log_crisis_event(user_id, content, "keyword")
            return await self._start_flow("crisis", conversation, context)

        # Safety Priority 2: LLM risk assessment from previous message
        if await check_llm_risk(user_id):
            await log_crisis_event(user_id, content, "llm_risk")
            return await self._start_flow("crisis", conversation, context)

        # Safety Priority 3: Slow escalation detection
        if await check_slow_escalation(user_id):
            return self._make_response(
                "I've noticed you've been going through a really tough stretch. "
                "I want to check in — are you feeling safe right now?\n\n"
                "If you're in crisis, please reach out to **988** (call or text) "
                "or text **HOME** to **741741**."
            )

        # Priority 4: SessionEngine — protocols, screenings, homework
        session_response = await self.session_engine.try_handle(content, context)
        if session_response:
            return session_response

        # Priority 5: Active flow
        flow = self.active_flows.get(str(conversation.id))
        if flow and not flow.is_complete:
            result = await flow.process(content, context)
            if flow.is_complete:
                await self._on_flow_complete(flow, conversation)
                del self.active_flows[str(conversation.id)]
                # Offer next steps after flow completion
                if result.response_message:
                    result.response_message += (
                        "\n\nWould you like a suggestion for today, or just chat freely?"
                    )
            return self._flow_result_to_response(result, flow, str(conversation.id))

        # Priority 6: Intent detection
        detected_intent = self._detect_intent(content)
        if detected_intent:
            return await self._start_flow(detected_intent, conversation, context)

        # Priority 7: LLM response + state assessment
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
        from app.models.inferred_state import InferredStateRecord

        # Get history EXCLUDING the current message (already inserted above)
        recent_messages = await Message.find(
            Message.conversation_id == str(conversation.id)
        ).sort("-created_at").limit(21).to_list()
        recent_messages.reverse()

        # Remove the last one (current message) to avoid duplication
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in recent_messages[:-1]
            if msg.role in ("user", "assistant")
        ]

        # Build user context from values, activities, and inferred states
        user_context_parts = [f"User's name: {context.user_name}"]

        # Include user's values if they've done the values flow
        from app.models.activity import UserValues, Activity

        user_values = await UserValues.find_one(UserValues.user_id == str(self.user.id))
        if user_values and user_values.values:
            values_str = "; ".join(
                f"{area}: {val}" for area, val in user_values.values.items()
            )
            user_context_parts.append(f"User's core values: {values_str}")

        # Include recent activity patterns
        recent_activities = await Activity.find(
            Activity.user_id == str(self.user.id),
            Activity.completed == True,
        ).sort("-created_at").limit(5).to_list()
        if recent_activities:
            act_strs = []
            for a in recent_activities:
                mood_delta = ""
                if a.mood_before and a.mood_after:
                    delta = a.mood_after - a.mood_before
                    mood_delta = f" (mood {'+'if delta > 0 else ''}{delta:.0f})"
                act_strs.append(f"{a.name}{mood_delta}")
            user_context_parts.append(f"Recent activities: {', '.join(act_strs)}")

        # Check for active program
        from app.models.program import ProgramEnrollment
        active_program = await ProgramEnrollment.find_one(
            ProgramEnrollment.user_id == str(self.user.id),
            ProgramEnrollment.is_active == True,
        )
        if active_program:
            user_context_parts.append(
                f"Active program: day {active_program.current_day}/{active_program.total_days} "
                f"of {active_program.program_id}"
            )

        # Check for re-engagement (first message after absence)
        last_msg = await Message.find(
            Message.conversation_id == str(conversation.id),
        ).sort("-created_at").limit(2).to_list()
        if len(last_msg) <= 2:
            # This might be a new conversation — check last activity across all conversations
            from app.models.inferred_state import InferredStateRecord as ISR_check
            last_state = await ISR_check.find(
                ISR_check.user_id == str(self.user.id)
            ).sort("-created_at").limit(1).to_list()
            if last_state:
                from datetime import timedelta
                gap = datetime.now(timezone.utc) - last_state[0].created_at
                if gap > timedelta(days=2):
                    user_context_parts.append(
                        f"RETURNING USER after {gap.days} days away. "
                        "Welcome them warmly. NO guilt about absence. "
                        "Reference something from their past conversations if possible."
                    )

        recent_states = await InferredStateRecord.find(
            InferredStateRecord.user_id == str(self.user.id),
            InferredStateRecord.confidence >= 0.3,
        ).sort("-created_at").limit(10).to_list()

        if recent_states:
            moods = [s.mood_valence for s in recent_states if s.mood_valence]
            energies = [s.energy_level for s in recent_states if s.energy_level]
            motivations = [s.motivation_level for s in recent_states if s.motivation_level]

            if moods:
                user_context_parts.append(f"Recent mood trend: {sum(moods)/len(moods):.1f}/10")
            if energies:
                user_context_parts.append(f"Recent energy trend: {sum(energies)/len(energies):.1f}/10")
            if motivations:
                user_context_parts.append(f"Recent motivation: {sum(motivations)/len(motivations):.1f}/10")

            all_themes = {}
            for s in recent_states:
                for t in s.themes:
                    all_themes[t] = all_themes.get(t, 0) + 1
            if all_themes:
                top = sorted(all_themes, key=all_themes.get, reverse=True)[:3]
                user_context_parts.append(f"Recurring themes: {', '.join(top)}")

            stages = [s.stage_signals.get("stage") for s in recent_states if s.stage_signals.get("stage")]
            if stages:
                stage = stages[0]
                user_context_parts.append(f"Stage of change: {stage}")
                # Stage-specific instruction for the LLM
                stage_instructions = {
                    "precontemplation": "User is NOT ready for change. DO NOT suggest actions. Just listen and explore values.",
                    "contemplation": "User is ambivalent. Explore both sides. DO NOT rush to action plans.",
                    "preparation": "User is getting ready. Help plan tiny concrete steps.",
                    "action": "User is actively changing. Support, reinforce, troubleshoot obstacles.",
                    "maintenance": "User is sustaining change. Reinforce identity: 'You're someone who...'",
                    "relapse": "User had a setback. Normalize it. 'This is part of the process.' NO guilt.",
                }
                if stage in stage_instructions:
                    user_context_parts.append(f"STAGE INSTRUCTION: {stage_instructions[stage]}")

        # Conversation length management
        if self._message_count >= 20:
            user_context_parts.append(
                "This conversation has been going for a while. Consider gently suggesting "
                "the user take a break and check in tomorrow."
            )

        llm_response = await generate_response(
            user_message=content,
            conversation_history=history,
            user_context="\n".join(user_context_parts),
        )

        # Save LLM-inferred state
        if llm_response.state:
            await self._save_llm_state(llm_response.state, content, conversation)

        return self._make_response(llm_response.text)

    async def _save_llm_state(self, state: dict, content: str, conversation: Conversation):
        """Save the structured state assessment from Claude's response."""
        from app.models.inferred_state import InferredStateRecord

        record = InferredStateRecord(
            user_id=str(self.user.id),
            conversation_id=str(conversation.id),
            message_content="",  # Don't store raw content for privacy
            mood_valence=state.get("mood"),
            energy_level=state.get("energy"),
            motivation_level=state.get("motivation"),
            absolutist_count=0,
            first_person_ratio=0,
            word_count=len(content.split()),
            change_talk_score=state.get("change_talk", 0),
            sustain_talk_score=state.get("sustain_talk", 0),
            stage_signals={
                "stage": state.get("stage", ""),
                "risk": state.get("risk", "none"),
            },
            themes=state.get("themes", []),
            emotions=state.get("emotions", []),
            confidence=state.get("confidence", 0.5),
        )
        await record.insert()

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
