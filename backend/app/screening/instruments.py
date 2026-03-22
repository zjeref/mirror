"""
Validated screening instruments: PHQ-9, GAD-7, PCL-5.

Each instrument has clinical wording (from validated measures) and
conversational rephrasing for use in chat-based administration.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class InstrumentItem:
    index: int
    clinical: str
    conversational: str


@dataclass
class ScoringThreshold:
    """Maps a score range [min, max] to a severity tier label."""
    min_score: int
    max_score: int
    tier: str


@dataclass
class Instrument:
    name: str
    display_name: str
    items: List[InstrumentItem]
    thresholds: List[ScoringThreshold]
    response_options: List[str]

    def score(self, item_scores: List[int]) -> Dict:
        total = sum(item_scores)
        tier = "unknown"
        for threshold in self.thresholds:
            if threshold.min_score <= total <= threshold.max_score:
                tier = threshold.tier
                break
        return {
            "instrument": self.name,
            "total_score": total,
            "item_scores": item_scores,
            "severity_tier": tier,
        }


# ---------------------------------------------------------------------------
# PHQ-9 — Patient Health Questionnaire (Depression)
# Thresholds: 0-4 minimal, 5-9 mild, 10-14 moderate, 15-19 moderately severe,
#             20-27 severe
# ---------------------------------------------------------------------------

PHQ9 = Instrument(
    name="phq9",
    display_name="PHQ-9 (Depression)",
    response_options=["Not at all", "Several days", "More than half the days", "Nearly every day"],
    thresholds=[
        ScoringThreshold(0, 4, "minimal"),
        ScoringThreshold(5, 9, "mild"),
        ScoringThreshold(10, 14, "moderate"),
        ScoringThreshold(15, 19, "moderately_severe"),
        ScoringThreshold(20, 27, "severe"),
    ],
    items=[
        InstrumentItem(
            index=0,
            clinical="Little interest or pleasure in doing things",
            conversational=(
                "Over the past two weeks, how often have you found yourself "
                "losing interest or pleasure in things you usually enjoy?"
            ),
        ),
        InstrumentItem(
            index=1,
            clinical="Feeling down, depressed, or hopeless",
            conversational=(
                "How often have you been feeling down, depressed, or like "
                "things aren't going to get better?"
            ),
        ),
        InstrumentItem(
            index=2,
            clinical="Trouble falling or staying asleep, or sleeping too much",
            conversational=(
                "Have you been having trouble falling asleep, staying asleep, "
                "or found yourself sleeping much more than usual?"
            ),
        ),
        InstrumentItem(
            index=3,
            clinical="Feeling tired or having little energy",
            conversational=(
                "How often have you been feeling tired or like you have very "
                "little energy, even for small tasks?"
            ),
        ),
        InstrumentItem(
            index=4,
            clinical="Poor appetite or overeating",
            conversational=(
                "Have you noticed changes in your appetite — eating much less "
                "or much more than usual?"
            ),
        ),
        InstrumentItem(
            index=5,
            clinical=(
                "Feeling bad about yourself — or that you are a failure or "
                "have let yourself or your family down"
            ),
            conversational=(
                "How often have you been feeling bad about yourself, like "
                "you've let people down or that you're not good enough?"
            ),
        ),
        InstrumentItem(
            index=6,
            clinical=(
                "Trouble concentrating on things, such as reading the newspaper "
                "or watching television"
            ),
            conversational=(
                "Have you been having a hard time concentrating — like reading, "
                "watching something, or getting through tasks at work?"
            ),
        ),
        InstrumentItem(
            index=7,
            clinical=(
                "Moving or speaking so slowly that other people could have "
                "noticed? Or the opposite — being so fidgety or restless that "
                "you have been moving around a lot more than usual"
            ),
            conversational=(
                "Have you noticed your body slowing down — moving or speaking "
                "more slowly — or the opposite, feeling so restless you can't "
                "sit still?"
            ),
        ),
        InstrumentItem(
            index=8,
            clinical=(
                "Thoughts that you would be better off dead, or of hurting yourself"
            ),
            conversational=(
                "This one is important and I want to ask it with care — "
                "have you had any thoughts that you'd be better off dead, "
                "or thoughts of hurting yourself in any way?"
            ),
        ),
    ],
)


# ---------------------------------------------------------------------------
# GAD-7 — Generalised Anxiety Disorder (Anxiety)
# Thresholds: 0-4 minimal, 5-9 mild, 10-14 moderate, 15-21 severe
# (Note: GAD-7 max = 21; plan specifies moderately_severe 15-18, severe 19-21)
# ---------------------------------------------------------------------------

GAD7 = Instrument(
    name="gad7",
    display_name="GAD-7 (Anxiety)",
    response_options=["Not at all", "Several days", "More than half the days", "Nearly every day"],
    thresholds=[
        ScoringThreshold(0, 4, "minimal"),
        ScoringThreshold(5, 9, "mild"),
        ScoringThreshold(10, 14, "moderate"),
        ScoringThreshold(15, 18, "moderately_severe"),
        ScoringThreshold(19, 21, "severe"),
    ],
    items=[
        InstrumentItem(
            index=0,
            clinical="Feeling nervous, anxious, or on edge",
            conversational=(
                "Over the past two weeks, how often have you been feeling "
                "nervous, anxious, or on edge?"
            ),
        ),
        InstrumentItem(
            index=1,
            clinical="Not being able to stop or control worrying",
            conversational=(
                "How often have you found it hard to stop worrying, even "
                "when you want to?"
            ),
        ),
        InstrumentItem(
            index=2,
            clinical="Worrying too much about different things",
            conversational=(
                "Have you been worrying a lot about many different things — "
                "more than feels normal for you?"
            ),
        ),
        InstrumentItem(
            index=3,
            clinical="Trouble relaxing",
            conversational=(
                "How often have you had trouble relaxing, even when you have "
                "the time and space to do so?"
            ),
        ),
        InstrumentItem(
            index=4,
            clinical="Being so restless that it's hard to sit still",
            conversational=(
                "Have you felt so restless or wound up that it was hard to "
                "just sit still?"
            ),
        ),
        InstrumentItem(
            index=5,
            clinical="Becoming easily annoyed or irritable",
            conversational=(
                "How often have you been getting irritated or annoyed more "
                "easily than usual?"
            ),
        ),
        InstrumentItem(
            index=6,
            clinical="Feeling afraid as if something awful might happen",
            conversational=(
                "Have you been feeling afraid, like something bad is about "
                "to happen, even if you can't explain why?"
            ),
        ),
    ],
)


# ---------------------------------------------------------------------------
# PCL-5 — PTSD Checklist (abbreviated, 8-item version for screening)
# 5-point Likert: 0=Not at all, 1=A little bit, 2=Moderately, 3=Quite a bit,
#                 4=Extremely
# Thresholds: 0-7 minimal, 8-15 mild, 16-32 severe
# ---------------------------------------------------------------------------

PCL5 = Instrument(
    name="pcl5",
    display_name="PCL-5 (PTSD Screening, abbreviated)",
    response_options=["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"],
    thresholds=[
        ScoringThreshold(0, 7, "minimal"),
        ScoringThreshold(8, 15, "mild"),
        ScoringThreshold(16, 32, "severe"),
    ],
    items=[
        InstrumentItem(
            index=0,
            clinical="Repeated, disturbing, and unwanted memories of the stressful experience",
            conversational=(
                "Have you had unwanted memories of a distressing experience "
                "come back to you, even when you weren't trying to think about it?"
            ),
        ),
        InstrumentItem(
            index=1,
            clinical="Avoiding memories, thoughts, or feelings related to the stressful experience",
            conversational=(
                "Have you been avoiding thoughts or feelings connected to "
                "something painful that happened?"
            ),
        ),
        InstrumentItem(
            index=2,
            clinical="Avoiding external reminders of the stressful experience",
            conversational=(
                "Have you been staying away from people, places, or situations "
                "that remind you of a difficult experience?"
            ),
        ),
        InstrumentItem(
            index=3,
            clinical="Feeling distant or cut off from other people",
            conversational=(
                "How often have you felt distant or cut off from the people "
                "around you?"
            ),
        ),
        InstrumentItem(
            index=4,
            clinical="Feeling irritable or having angry outbursts",
            conversational=(
                "Have you been feeling irritable or finding yourself getting "
                "angry in ways that feel hard to control?"
            ),
        ),
        InstrumentItem(
            index=5,
            clinical="Being 'super-alert' or watchful or on guard",
            conversational=(
                "Have you been feeling hyper-alert — like you need to watch "
                "your surroundings or stay on guard, even when you're safe?"
            ),
        ),
        InstrumentItem(
            index=6,
            clinical="Feeling jumpy or easily startled",
            conversational=(
                "Have you been startling more easily than usual, or feeling "
                "jumpy when something unexpected happens?"
            ),
        ),
        InstrumentItem(
            index=7,
            clinical="Trouble experiencing positive feelings",
            conversational=(
                "Have you had difficulty feeling positive emotions — like "
                "happiness, love, or joy — even in moments that used to feel good?"
            ),
        ),
    ],
)


# ---------------------------------------------------------------------------
# Registry + public API
# ---------------------------------------------------------------------------

_REGISTRY: Dict[str, Instrument] = {
    "phq9": PHQ9,
    "gad7": GAD7,
    "pcl5": PCL5,
}


def get_instrument(name: str) -> Optional[Instrument]:
    """Return the named instrument, or None if unknown."""
    return _REGISTRY.get(name.lower())


def score_instrument(name: str, item_scores: List[int]) -> Dict:
    """Score the named instrument against the provided item responses."""
    instrument = get_instrument(name)
    if instrument is None:
        raise ValueError(f"Unknown instrument: {name!r}")
    return instrument.score(item_scores)
