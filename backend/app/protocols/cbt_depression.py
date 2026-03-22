"""8-session CBT for Depression protocol."""

from app.protocols.base import BaseProtocol, HomeworkTier, SessionDefinition


class CBTDepressionProtocol(BaseProtocol):
    protocol_id = "cbt_depression"
    display_name = "CBT for Depression"
    instrument = "phq9"
    min_score = 5
    max_score = 19
    mid_screening_session = 4

    @property
    def sessions(self) -> list[SessionDefinition]:
        return [
            SessionDefinition(
                number=1,
                focus="Psychoeducation",
                goals=[
                    "Understand the CBT model (thoughts-feelings-behaviors)",
                    "Normalize the experience of depression",
                    "Set expectations for the program",
                ],
                homework=HomeworkTier(
                    structured="Read the CBT model handout and identify one example from your week where thoughts affected your mood",
                    gentle="Notice one moment this week where a thought changed how you felt",
                    minimal="Just notice how you're feeling once today — no need to analyze",
                ),
            ),
            SessionDefinition(
                number=2,
                focus="Behavioral Activation Introduction",
                goals=[
                    "Understand the activity-mood connection",
                    "Identify activities that used to bring pleasure or mastery",
                    "Begin simple activity monitoring",
                ],
                homework=HomeworkTier(
                    structured="Track your activities and mood rating (1-10) for 3 days using the activity log",
                    gentle="Pick one small enjoyable activity and do it this week",
                    minimal="Notice one moment when you felt slightly better than usual",
                ),
            ),
            SessionDefinition(
                number=3,
                focus="Activity Scheduling",
                goals=[
                    "Schedule pleasant and mastery activities",
                    "Use graded task assignment for overwhelming tasks",
                    "Build momentum with small wins",
                ],
                homework=HomeworkTier(
                    structured="Schedule 3 activities this week (mix of pleasure and mastery) and rate mood before/after",
                    gentle="Schedule 1 activity that feels manageable and follow through",
                    minimal="Do one tiny thing that's slightly more than you did yesterday",
                ),
            ),
            SessionDefinition(
                number=4,
                focus="Thought Catching",
                goals=[
                    "Identify automatic negative thoughts",
                    "Connect thoughts to emotions and situations",
                    "Begin using thought records",
                ],
                homework=HomeworkTier(
                    structured="Complete 3 thought records this week, identifying situation, thought, emotion, and intensity",
                    gentle="When you notice your mood shift, write down what thought was happening",
                    minimal="Just notice one thought that pops up when you feel down — no need to write it",
                ),
                uses_existing_flow="reframe",
            ),
            SessionDefinition(
                number=5,
                focus="Cognitive Restructuring",
                goals=[
                    "Evaluate evidence for and against automatic thoughts",
                    "Generate balanced alternative thoughts",
                    "Practice cognitive flexibility",
                ],
                homework=HomeworkTier(
                    structured="Complete 3 full thought records with evidence for/against and balanced thought columns",
                    gentle="Pick one negative thought and ask: what would I tell a friend who thought this?",
                    minimal="When a harsh thought appears, just whisper 'that's a thought, not a fact'",
                ),
            ),
            SessionDefinition(
                number=6,
                focus="Core Beliefs",
                goals=[
                    "Identify underlying core beliefs driving automatic thoughts",
                    "Understand how core beliefs formed",
                    "Begin to question rigid core beliefs",
                ],
                homework=HomeworkTier(
                    structured="Use the downward arrow technique on 2 automatic thoughts to identify core beliefs, then list 3 pieces of counter-evidence",
                    gentle="Notice if your self-critical thoughts share a theme (e.g., 'I'm not good enough')",
                    minimal="Just be aware that some thoughts are old stories, not current truths",
                ),
            ),
            SessionDefinition(
                number=7,
                focus="Behavioral Experiments",
                goals=[
                    "Design experiments to test negative predictions",
                    "Gather real-world evidence against distorted beliefs",
                    "Build confidence through action",
                ],
                homework=HomeworkTier(
                    structured="Design and carry out 2 behavioral experiments, recording predictions vs actual outcomes",
                    gentle="Test one small prediction this week — did what you feared actually happen?",
                    minimal="Notice one time something went better than you expected",
                ),
            ),
            SessionDefinition(
                number=8,
                focus="Relapse Prevention",
                goals=[
                    "Review skills learned throughout the program",
                    "Create a personal relapse prevention plan",
                    "Identify early warning signs and coping strategies",
                ],
                homework=HomeworkTier(
                    structured="Write a full relapse prevention plan: warning signs, coping strategies, support contacts, and when to seek help",
                    gentle="List your top 3 coping tools and when you'd use each one",
                    minimal="Remember: you've already proven you can do hard things by completing this program",
                ),
            ),
        ]
