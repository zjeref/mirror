"""SessionEngine — orchestration layer for protocols, screenings, and homework.

Manages the lifecycle of therapeutic sessions: proactive greetings,
screening delivery, protocol enrollment, and homework follow-up.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from beanie.operators import In

from app.chat.flows.base import FlowResult, UserContext
from app.models.activity import UserValues
from app.models.conversation import Conversation, Message
from app.models.inferred_state import InferredStateRecord
from app.models.notification import PendingAction
from app.models.program import ProgramEnrollment
from app.models.protocol import ProtocolEnrollment
from app.models.screening import ScreeningResult
from app.models.user import User
from app.protocols.registry import get_protocol
from app.psychology.severity import SeverityRouter
from app.screening.delivery import ScreeningFlow
from app.sessions.homework import HomeworkManager


class SessionEngine:
    """Orchestrates protocols, screenings, and homework for a user session."""

    def __init__(self, user: User):
        self.user = user
        self.user_id = str(user.id)
        self._active_screening_flow: Optional[ScreeningFlow] = None
        self._onboarding_pending: bool = False

    async def try_handle(self, content: str, context: UserContext) -> Optional[dict]:
        """Try to handle user input through active flows.

        Returns a response dict if handled, None to fall through to existing routing.
        """
        # Onboarding: any reply after welcome triggers PHQ-9 screening
        if self._onboarding_pending:
            self._onboarding_pending = False
            self._active_screening_flow = ScreeningFlow(instrument_name="phq9")
            result = await self._active_screening_flow.start(context)
            return self._flow_result_to_response(result)

        # Active screening flow takes priority
        if self._active_screening_flow and not self._active_screening_flow.is_complete:
            result = await self._active_screening_flow.process(content, context)

            if self._active_screening_flow.is_complete:
                return await self._on_screening_complete(context)

            return self._flow_result_to_response(result)

        # Active protocol enrollment — LLM handles therapeutic content for now
        return None

    async def handle_session_start(self, context: UserContext) -> Optional[dict]:
        """Generate a proactive greeting based on user state.

        Priority order:
        1. Pending homework → homework review prompt
        2. Active protocol with next session → session start prompt
        3. Pending screening action → start screening flow
        4. Nothing pending → return None
        """
        # 1. Pending homework?
        pending_hw = await HomeworkManager.get_pending(self.user_id)
        if pending_hw is not None:
            return self._make_response(
                f"Welcome back. Last time I asked: '{pending_hw.description}'. "
                f"How did that go?"
            )

        # 2. Active protocol with next session ready?
        enrollment = await self._get_active_enrollment()
        if enrollment is not None:
            protocol = get_protocol(enrollment.protocol_id)
            if protocol is not None:
                next_session_num = enrollment.current_session_number + 1
                session_def = protocol.get_session(next_session_num)
                if session_def is not None:
                    return self._make_response(
                        f"Ready for Session {next_session_num}? "
                        f"Today: {session_def.focus}"
                    )

        # 3. Pending screening action?
        action = await PendingAction.find_one(
            PendingAction.user_id == self.user_id,
            PendingAction.action_type == "screening_due",
            PendingAction.dismissed == False,  # noqa: E712
        )
        if action is not None:
            instrument = action.data.get("instrument", "phq9")
            self._active_screening_flow = ScreeningFlow(instrument)
            result = await self._active_screening_flow.start(context)

            # Dismiss the action
            action.dismissed = True
            await action.save()

            return self._flow_result_to_response(result)

        # 4. Pattern-based alert
        alert = await self._detect_pattern_alert()
        if alert:
            return alert

        # 5/6. Check if user has any conversations — if not, they're new (priority 6)
        has_conversations = await Conversation.find_one(
            Conversation.user_id == self.user_id
        )
        if not has_conversations:
            return await self._build_onboarding_greeting(context)

        # 5. Returning user contextual greeting
        return await self._build_contextual_greeting(context)

    async def _detect_pattern_alert(self) -> Optional[dict]:
        """Detect soft patterns in recent InferredStateRecords for conversation openers."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        records = await InferredStateRecord.find(
            InferredStateRecord.user_id == self.user_id,
            InferredStateRecord.confidence >= 0.3,
            InferredStateRecord.created_at >= cutoff,
        ).sort("-created_at").to_list()

        if not records:
            return None

        # Group by day — keep only the most recent record per day
        daily: dict[date, InferredStateRecord] = {}
        for r in records:
            day = r.created_at.date()
            if day not in daily:
                daily[day] = r

        day_records = sorted(daily.values(), key=lambda r: r.created_at)

        # Check mood dropping: 3+ days with mood_valence <= 4
        low_mood_days = [
            r for r in day_records
            if r.mood_valence is not None and r.mood_valence <= 4
        ]
        if len(low_mood_days) >= 3:
            avg_mood = sum(r.mood_valence for r in low_mood_days) / len(low_mood_days)
            if avg_mood <= 3:
                return self._make_response(
                    "I've noticed your mood has been lower the last few days. "
                    "That's something I want to check in on. How are you feeling right now?"
                )
            else:
                return self._make_response(
                    "I've been noticing some shifts in how you've been feeling lately. "
                    "Want to explore that together?"
                )

        # Check energy low: 3+ days with energy_level <= 3
        low_energy_days = [
            r for r in day_records
            if r.energy_level is not None and r.energy_level <= 3
        ]
        if len(low_energy_days) >= 3:
            avg_energy = sum(r.energy_level for r in low_energy_days) / len(low_energy_days)
            if avg_energy <= 2:
                return self._make_response(
                    "Your energy has been really low lately. "
                    "That's worth paying attention to. What's going on?"
                )
            else:
                return self._make_response(
                    "I noticed your energy has been on the lower side. "
                    "How are you holding up?"
                )

        # Check anxiety emerging: 2+ days with "anxiety" in themes
        anxiety_days = [
            r for r in day_records
            if "anxiety" in r.themes
        ]
        if len(anxiety_days) >= 2:
            return self._make_response(
                "I've been picking up on some worry patterns in our recent conversations. "
                "Want to dig into that?"
            )

        # Check positive trend: 3+ days with mood improving (each higher than previous)
        mood_days = [
            r for r in day_records
            if r.mood_valence is not None
        ]
        if len(mood_days) >= 3:
            # Check for longest improving streak from the end
            for start in range(len(mood_days) - 3, -1, -1):
                streak = mood_days[start:]
                improving = all(
                    streak[i + 1].mood_valence > streak[i].mood_valence
                    for i in range(len(streak) - 1)
                )
                if improving and len(streak) >= 3:
                    return self._make_response(
                        "Things seem to be moving in a good direction lately. "
                        "I'd love to hear what's been different."
                    )

        return None

    async def _build_contextual_greeting(self, context: UserContext) -> dict:
        """Build a greeting based on recency and user data."""
        name = self.user.name

        # Find most recent message for this user (across all conversations)
        # First get user's conversation IDs
        conversations = await Conversation.find(
            Conversation.user_id == self.user_id
        ).to_list()
        conv_ids = [str(c.id) for c in conversations]

        days_since = 0
        if conv_ids:
            last_message = await Message.find(
                In(Message.conversation_id, conv_ids),
            ).sort("-created_at").first_or_none()

            if last_message:
                msg_time = last_message.created_at
                if msg_time.tzinfo is None:
                    msg_time = msg_time.replace(tzinfo=timezone.utc)
                delta = datetime.now(timezone.utc) - msg_time
                days_since = delta.days

        # Occasionally reference a value (deterministic per day)
        should_ref_value = hash(self.user_id + str(date.today())) % 10 < 3
        value_ref = ""
        if should_ref_value:
            user_values = await UserValues.find_one(
                UserValues.user_id == self.user_id
            )
            if user_values and user_values.values:
                # Pick the first area with values
                for area, vals in user_values.values.items():
                    if vals:
                        value_ref = (
                            f" You mentioned {area} matters to you — "
                            f"how's that going?"
                        )
                        break

        if days_since == 0:
            greeting = "Hey again. What's on your mind?"
        elif days_since <= 2:
            greeting = f"Hey {name}. How's today going?"
        elif days_since <= 6:
            greeting = (
                f"Good to see you, {name}. "
                f"It's been a few days — how are things?"
            )
        else:
            greeting = (
                f"Hey {name}. It's been a while. "
                f"No pressure — I'm glad you're here. How are you doing?"
            )

        if value_ref and days_since > 0:
            greeting += value_ref

        return self._make_response(greeting)

    async def _build_onboarding_greeting(self, context: UserContext) -> dict:
        """Welcome new users and prepare for guided screening."""
        name = self.user.name
        self._onboarding_pending = True
        return self._make_response(
            f"Hey {name}. Welcome to Mirror. I'm here to help you understand "
            f"yourself better — not to fix you, just to walk alongside you.\n\n"
            f"I work best when I understand where you are. Mind if I ask you "
            f"a few questions? It'll take about 5 minutes."
        )

    async def enroll(
        self, protocol_id: str, screening_id: str
    ) -> Optional[ProtocolEnrollment]:
        """Enroll user in a protocol if no conflicting enrollment exists.

        Blocks if:
        - An active ProgramEnrollment exists (is_active=True)
        - An active ProtocolEnrollment exists (status in enrolled/active/paused)

        Returns the new enrollment or None if blocked.
        """
        # Block if active program enrollment exists
        active_program = await ProgramEnrollment.find_one(
            ProgramEnrollment.user_id == self.user_id,
            ProgramEnrollment.is_active == True,  # noqa: E712
        )
        if active_program is not None:
            return None

        # Block if active protocol enrollment exists
        active_protocol = await self._get_active_enrollment()
        if active_protocol is not None:
            return None

        # Create enrollment
        enrollment = ProtocolEnrollment(
            user_id=self.user_id,
            protocol_id=protocol_id,
            entry_screening_id=screening_id,
            status="enrolled",
        )
        await enrollment.insert()
        return enrollment

    async def check_mid_protocol_screening(
        self, enrollment: ProtocolEnrollment
    ) -> bool:
        """Check if current session number matches protocol's mid-screening point."""
        protocol = get_protocol(enrollment.protocol_id)
        if not protocol:
            return False
        return enrollment.current_session_number == protocol.mid_screening_session

    async def switch_protocol(
        self,
        current_enrollment: ProtocolEnrollment,
        new_protocol_id: str,
    ) -> Optional[ProtocolEnrollment]:
        """Switch from current protocol to a new one (e.g., CBT -> BA)."""
        new_protocol = get_protocol(new_protocol_id)
        if not new_protocol:
            return None

        # Determine starting session (skip overlap sessions)
        start_session = 1
        if hasattr(new_protocol, "skip_sessions_on_switch"):
            skippable = new_protocol.skip_sessions_on_switch
            start_session = max(skippable) + 1 if skippable else 1

        # Create new enrollment
        new_enrollment = ProtocolEnrollment(
            user_id=current_enrollment.user_id,
            protocol_id=new_protocol_id,
            current_session_number=start_session,
            status="enrolled",
            entry_screening_id=current_enrollment.entry_screening_id,
            screening_scores=current_enrollment.screening_scores,
        )
        await new_enrollment.insert()

        # Mark old as switched
        current_enrollment.status = "switched"
        current_enrollment.switched_to_enrollment_id = str(new_enrollment.id)
        current_enrollment.end_date = datetime.now(timezone.utc)
        await current_enrollment.save()

        return new_enrollment

    async def _get_active_enrollment(self) -> Optional[ProtocolEnrollment]:
        """Find enrollment with status in enrolled/active/paused."""
        return await ProtocolEnrollment.find_one(
            ProtocolEnrollment.user_id == self.user_id,
            In(ProtocolEnrollment.status, ["enrolled", "active", "paused"]),
        )

    async def _on_screening_complete(self, context: UserContext) -> dict:
        """Save screening result and route through severity router."""
        flow = self._active_screening_flow
        collected = flow.collected_data

        instrument_name = flow.instrument.name
        total_score = collected.get("total_score", 0)
        item_scores = collected.get("item_scores", [])
        severity_tier = collected.get("severity_tier", "")

        # Save ScreeningResult
        screening_result = ScreeningResult(
            user_id=self.user_id,
            instrument=instrument_name,
            item_scores=item_scores,
            total_score=total_score,
            severity_tier=severity_tier,
            status="completed",
            completed_at=datetime.now(timezone.utc),
        )
        await screening_result.insert()

        # Route through SeverityRouter
        decision = SeverityRouter.route(instrument_name, total_score)

        # Build completion message
        completion_msg = await flow.on_complete(context)
        routing_msg = self._build_routing_message(decision)

        self._active_screening_flow = None

        return self._make_response(f"{completion_msg}\n\n{routing_msg}")

    def _build_routing_message(self, decision) -> str:
        """Build a user-facing message from a routing decision."""
        parts = []

        if decision.action == "monitor":
            parts.append(
                "Based on your responses, things seem manageable right now. "
                "I'll check in with you again in a couple of weeks."
            )
        elif decision.action == "offer_protocol":
            protocols = ", ".join(decision.eligible_protocols)
            parts.append(
                f"I have some structured support that might help: {protocols}. "
                f"Would you like to explore that?"
            )
        elif decision.action == "recommend_protocol":
            protocols = ", ".join(decision.eligible_protocols)
            parts.append(
                f"I'd recommend starting a structured program. "
                f"Options available: {protocols}."
            )
        elif decision.action == "protocol_plus_referral":
            parts.append(
                "I'd like to support you with a structured program, and I also "
                "want to share some professional resources."
            )
        elif decision.action == "referral_only":
            parts.append(
                "Based on what you've shared, I want to make sure you have "
                "access to professional support."
            )

        if decision.message:
            parts.append(decision.message)

        return "\n\n".join(parts)

    def _make_response(self, content: str) -> dict:
        """Create a standard response dict."""
        return {"message": content, "source": "session_engine"}

    def _flow_result_to_response(self, result: FlowResult) -> dict:
        """Convert a FlowResult to a response dict."""
        response = {
            "message": result.response_message or "",
            "source": "session_engine",
        }
        if result.prompt is not None:
            response["prompt"] = {
                "text": result.prompt.prompt,
                "input_type": result.prompt.input_type,
                "options": result.prompt.options,
            }
        return response
