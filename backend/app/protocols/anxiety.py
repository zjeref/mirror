"""7-session Anxiety Management protocol."""

from app.protocols.base import BaseProtocol, HomeworkTier, SessionDefinition


class AnxietyProtocol(BaseProtocol):
    protocol_id = "anxiety"
    display_name = "Anxiety Management"
    instrument = "gad7"
    min_score = 5
    max_score = 19
    mid_screening_session = 4

    @property
    def sessions(self) -> list[SessionDefinition]:
        return [
            SessionDefinition(
                number=1,
                focus="Psychoeducation — The Anxiety Cycle",
                goals=[
                    "Understand the anxiety cycle (trigger-thought-sensation-behavior)",
                    "Normalize anxiety as a protective mechanism gone overboard",
                    "Distinguish between helpful and unhelpful anxiety",
                ],
                homework=HomeworkTier(
                    structured="Map out one anxiety episode using the anxiety cycle diagram: trigger, thoughts, body sensations, and behavior",
                    gentle="Notice one moment of anxiety this week and name the trigger",
                    minimal="Just notice where in your body anxiety shows up — no need to fix it",
                ),
            ),
            SessionDefinition(
                number=2,
                focus="Worry Awareness",
                goals=[
                    "Distinguish productive worry from unproductive worry",
                    "Identify worry patterns and themes",
                    "Begin scheduled worry time practice",
                ],
                homework=HomeworkTier(
                    structured="Keep a worry log for 3 days: write each worry, label it productive or unproductive, and practice postponing unproductive worries to a 15-min worry window",
                    gentle="When you notice worrying, ask: can I do something about this right now?",
                    minimal="Just notice when you're worrying — that awareness alone is progress",
                ),
            ),
            SessionDefinition(
                number=3,
                focus="Cognitive Restructuring for Anxiety",
                goals=[
                    "Identify anxious predictions and catastrophic thinking",
                    "Evaluate the probability and severity of feared outcomes",
                    "Generate more realistic alternative perspectives",
                ],
                homework=HomeworkTier(
                    structured="Complete 3 anxiety thought records: anxious prediction, probability estimate, worst/best/most likely outcome, and balanced thought",
                    gentle="Pick one worry and ask: what's the most likely outcome (not worst case)?",
                    minimal="When a scary thought appears, gently remind yourself: thoughts aren't predictions",
                ),
            ),
            SessionDefinition(
                number=4,
                focus="Relaxation and Grounding",
                goals=[
                    "Learn progressive muscle relaxation",
                    "Practice grounding techniques (5-4-3-2-1 senses)",
                    "Build a personal calming toolkit",
                ],
                homework=HomeworkTier(
                    structured="Practice progressive muscle relaxation daily (10 min) and the 5-4-3-2-1 grounding technique when anxious, logging your anxiety level before/after",
                    gentle="Try one grounding exercise when you feel anxious this week",
                    minimal="Take 3 slow breaths when you notice tension — that's enough",
                ),
            ),
            SessionDefinition(
                number=5,
                focus="Exposure Hierarchy",
                goals=[
                    "Understand the principle of gradual exposure",
                    "Build a personal fear/avoidance hierarchy",
                    "Rate anxiety levels for each item (SUDS 0-100)",
                ],
                homework=HomeworkTier(
                    structured="Create a full exposure hierarchy with 8-10 items rated by SUDS, and attempt the lowest item on the list",
                    gentle="List 3 things you avoid because of anxiety, from easiest to hardest",
                    minimal="Just think about one thing you avoid — no need to face it yet",
                ),
            ),
            SessionDefinition(
                number=6,
                focus="Exposure Practice",
                goals=[
                    "Begin working through the exposure hierarchy",
                    "Practice staying with anxiety until it naturally decreases",
                    "Build tolerance and self-efficacy",
                ],
                homework=HomeworkTier(
                    structured="Complete 2-3 exposure exercises from your hierarchy, recording SUDS before, peak, and after for each",
                    gentle="Try one small exposure from your list and notice that anxiety rises then falls",
                    minimal="Approach one slightly uncomfortable situation — even for 30 seconds counts",
                ),
            ),
            SessionDefinition(
                number=7,
                focus="Relapse Prevention",
                goals=[
                    "Review all skills learned throughout the program",
                    "Create a personal anxiety management plan",
                    "Identify early warning signs and maintenance strategies",
                ],
                homework=HomeworkTier(
                    structured="Write a full anxiety management plan: early warning signs, go-to coping skills, continued exposure goals, and when to seek additional help",
                    gentle="List your top 3 anxiety management tools and commit to using one daily",
                    minimal="Remember: anxiety is manageable, and you now have tools — even small ones count",
                ),
            ),
        ]
