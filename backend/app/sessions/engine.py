"""SessionEngine — orchestration layer for protocols, screenings, and homework.

Manages the lifecycle of therapeutic sessions: proactive greetings,
screening delivery, protocol enrollment, and homework follow-up.
"""

from datetime import datetime, timezone
from typing import Optional

from beanie.operators import In

from app.chat.flows.base import FlowResult, UserContext
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

    async def try_handle(self, content: str, context: UserContext) -> Optional[dict]:
        """Try to handle user input through active flows.

        Returns a response dict if handled, None to fall through to existing routing.
        """
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

        # 4. Nothing pending
        return None

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
