"""6-session Behavioral Activation protocol."""

from app.protocols.base import BaseProtocol, HomeworkTier, SessionDefinition


class BehavioralActivationProtocol(BaseProtocol):
    protocol_id = "behavioral_activation"
    display_name = "Behavioral Activation"
    instrument = "phq9"
    min_score = 5
    max_score = 19
    mid_screening_session = 3

    # When switching from CBT to BA, sessions 1-2 overlap with CBT sessions 2-3,
    # so they can be skipped.
    skip_sessions_on_switch: list[int] = [1, 2]

    @property
    def sessions(self) -> list[SessionDefinition]:
        return [
            SessionDefinition(
                number=1,
                focus="Activity Monitoring",
                goals=[
                    "Understand the link between activity and mood",
                    "Begin tracking daily activities and mood ratings",
                    "Identify patterns of withdrawal and avoidance",
                ],
                homework=HomeworkTier(
                    structured="Complete a full activity log for 3 days, rating mood (1-10) and sense of accomplishment (1-10) for each activity",
                    gentle="Track your main activities and mood for 1 day",
                    minimal="Just notice what you did today and how you felt — no writing needed",
                ),
            ),
            SessionDefinition(
                number=2,
                focus="Values Connection",
                goals=[
                    "Identify personal values across life domains",
                    "Connect desired activities to core values",
                    "Set value-aligned activity goals",
                ],
                homework=HomeworkTier(
                    structured="Complete a values assessment across 5 life domains and identify 2 value-aligned activities to try this week",
                    gentle="Pick one value that matters to you and do one small thing that honors it",
                    minimal="Think about what matters to you — even vaguely is fine",
                ),
                uses_existing_flow="values",
            ),
            SessionDefinition(
                number=3,
                focus="Activity Scheduling",
                goals=[
                    "Schedule pleasant and mastery activities intentionally",
                    "Use graded task assignment for difficult activities",
                    "Balance routine, necessary, and pleasant activities",
                ],
                homework=HomeworkTier(
                    structured="Schedule 5 activities this week (mix of pleasant, mastery, and routine) and rate mood before/after each",
                    gentle="Schedule 2 activities — one pleasant, one necessary — and follow through",
                    minimal="Do one small thing tomorrow that you wouldn't have done otherwise",
                ),
            ),
            SessionDefinition(
                number=4,
                focus="Barriers and Avoidance",
                goals=[
                    "Identify common barriers to activation",
                    "Recognize avoidance patterns and their short-term relief",
                    "Develop strategies for working through barriers",
                ],
                homework=HomeworkTier(
                    structured="Log each time you avoid an activity: what was it, what barrier arose, what happened instead, and how you felt after",
                    gentle="Notice one moment of avoidance this week and gently ask: what was I protecting myself from?",
                    minimal="Just notice if you avoid something — no judgment, just awareness",
                ),
            ),
            SessionDefinition(
                number=5,
                focus="Expanding Activity Repertoire",
                goals=[
                    "Broaden the range of meaningful activities",
                    "Re-engage with previously abandoned activities",
                    "Build social activation where appropriate",
                ],
                homework=HomeworkTier(
                    structured="Try 2 new or previously abandoned activities this week, rating mood and meaning (1-10) for each",
                    gentle="Revisit one activity you used to enjoy — even briefly",
                    minimal="Think of one thing you used to like doing — hold that memory gently",
                ),
            ),
            SessionDefinition(
                number=6,
                focus="Review and Maintenance",
                goals=[
                    "Review progress and what worked best",
                    "Create a sustainable activity maintenance plan",
                    "Prepare for setbacks and low-energy days",
                ],
                homework=HomeworkTier(
                    structured="Write a maintenance plan: your top 5 activation strategies, a low-energy backup plan, and weekly activity goals",
                    gentle="List your top 3 activities that helped most and commit to keeping one",
                    minimal="Remember: even tiny actions count — you've already proven that",
                ),
            ),
        ]
