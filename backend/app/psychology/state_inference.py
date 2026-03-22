"""Passive state inference engine.

Extracts mood, energy, motivation, and psychological state from natural
conversation without explicit check-ins. Uses linguistic markers backed
by research (Pennebaker LIWC, Al-Mosaiwi & Johnstone absolutist language,
Motivational Interviewing change/sustain talk classification).

Every user message is analyzed. Results accumulate over time to build
a rich user profile that powers the dashboard and personalizes responses.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class InferredState:
    """State inferred from a single message."""

    # Core dimensions (1-10, None if not enough signal)
    mood_valence: Optional[float] = None  # 1=very negative, 10=very positive
    energy_level: Optional[float] = None  # 1=very low, 10=very high
    motivation_level: Optional[float] = None  # 1=no motivation, 10=highly motivated

    # Linguistic markers
    absolutist_count: int = 0
    first_person_ratio: float = 0.0
    word_count: int = 0
    avg_word_length: float = 0.0

    # MI classification
    change_talk_score: float = 0.0  # 0-1, how much change talk
    sustain_talk_score: float = 0.0  # 0-1, how much sustain talk

    # Stage of change (transtheoretical model)
    stage_signals: dict = field(default_factory=dict)

    # Detected themes
    themes: list[str] = field(default_factory=list)

    # Confidence (how much signal was in this message)
    confidence: float = 0.0


# ── Sentiment / Mood Lexicons ──

POSITIVE_WORDS = {
    "good", "great", "happy", "amazing", "wonderful", "love", "enjoy",
    "excited", "grateful", "proud", "calm", "peaceful", "hopeful",
    "better", "improved", "progress", "accomplished", "beautiful",
    "fun", "glad", "pleased", "satisfied", "confident", "strong",
    "awesome", "fantastic", "brilliant", "thrilled", "blessed",
}

NEGATIVE_WORDS = {
    "bad", "terrible", "awful", "hate", "angry", "sad", "depressed",
    "anxious", "worried", "stressed", "frustrated", "hopeless",
    "worthless", "useless", "tired", "exhausted", "overwhelmed",
    "scared", "lonely", "miserable", "ugly", "stupid", "broken",
    "failed", "failing", "worse", "painful", "suffering", "numb",
    "empty", "drained", "burned", "burnout", "sucks", "horrible",
}

# ── Energy Indicators ──

HIGH_ENERGY_WORDS = {
    "excited", "pumped", "energized", "motivated", "fired up",
    "ready", "lets go", "can't wait", "hyped", "productive",
    "active", "alive", "buzzing", "charged",
}

LOW_ENERGY_WORDS = {
    "tired", "exhausted", "drained", "no energy", "can't move",
    "sleepy", "lethargic", "sluggish", "wiped", "burned out",
    "burnout", "fatigue", "heavy", "slow", "barely", "can't get up",
    "don't want to", "too tired", "no motivation",
}

# ── Absolutist Language (Al-Mosaiwi & Johnstone, 2018) ──

ABSOLUTIST_WORDS = {
    "always", "never", "nothing", "everything", "completely",
    "totally", "absolutely", "entire", "constant", "impossible",
    "everyone", "no one", "nobody", "all", "none",
}

# ── Change Talk vs Sustain Talk (MI Framework) ──

CHANGE_TALK_PATTERNS = [
    r"\bi\s+want\s+to\b",
    r"\bi\s+could\b",
    r"\bi\s+will\b",
    r"\bi('m|\s+am)\s+going\s+to\b",
    r"\bi\s+need\s+to\b",
    r"\bi('m|\s+am)\s+ready\b",
    r"\bi\s+started\b",
    r"\bi('ve|\s+have)\s+been\b.*(?:trying|working|doing)",
    r"\bmaybe\s+i\s+(?:can|could|should)\b",
    r"\bi\s+think\s+i\s+can\b",
    r"\bit('s|\s+is)\s+time\s+to\b",
    r"\bi('m|\s+am)\s+determined\b",
]

SUSTAIN_TALK_PATTERNS = [
    r"\bi\s+can('t|not)\b",
    r"\bthere('s|\s+is)\s+no\s+point\b",
    r"\bwhat('s|\s+is)\s+the\s+use\b",
    r"\bit\s+won('t|not)\s+work\b",
    r"\bi('ll|\s+will)\s+never\b",
    r"\bi\s+don('t|not)\s+(?:want|care|see)\b",
    r"\bwhy\s+bother\b",
    r"\btoo\s+(?:hard|difficult|late|much)\b",
    r"\bi\s+give\s+up\b",
    r"\bno\s+(?:way|chance|hope)\b",
]

# ── Stage of Change Signals ──

STAGE_PATTERNS = {
    "precontemplation": [
        r"\bi\s+don('t|not)\s+(?:see|have)\s+a\s+problem\b",
        r"\beveryone\s+(?:else|thinks)\b",
        r"\bi('m|\s+am)\s+fine\b",
        r"\bleave\s+me\s+alone\b",
    ],
    "contemplation": [
        r"\bpart\s+of\s+me\b",
        r"\bi\s+know\s+i\s+should\b",
        r"\bmaybe\s+i\b",
        r"\bi('m|\s+am)\s+thinking\s+about\b",
        r"\bon\s+one\s+hand\b",
        r"\bi\s+want\s+to\s+but\b",
    ],
    "preparation": [
        r"\bi('m|\s+am)\s+going\s+to\b",
        r"\bhow\s+(?:do|can|should)\s+i\b",
        r"\bi('ve|\s+have)\s+(?:decided|planned)\b",
        r"\bstarting\s+(?:next|tomorrow|this)\b",
    ],
    "action": [
        r"\bi\s+(?:started|began|did)\b",
        r"\bi('ve|\s+have)\s+been\s+(?:doing|trying|working)\b",
        r"\btoday\s+i\b",
        r"\byesterday\s+i\b",
    ],
    "maintenance": [
        r"\bi('ve|\s+have)\s+(?:kept|maintained|continued)\b",
        r"\bfor\s+(?:\d+|several|a\s+few)\s+(?:days|weeks|months)\b",
        r"\bit('s|\s+is)\s+(?:become|becoming)\s+(?:a\s+)?habit\b",
    ],
}

# ── Theme Detection ──

THEME_KEYWORDS = {
    "work": ["work", "job", "career", "boss", "office", "meeting", "deadline", "project", "colleague"],
    "health": ["gym", "exercise", "workout", "run", "walk", "sleep", "eat", "diet", "weight", "body"],
    "relationships": ["friend", "family", "partner", "girlfriend", "boyfriend", "wife", "husband", "mom", "dad", "lonely"],
    "money": ["money", "bills", "rent", "debt", "salary", "afford", "expensive", "broke", "financial"],
    "self_worth": ["worthless", "useless", "failure", "stupid", "ugly", "hate myself", "not good enough", "loser"],
    "anxiety": ["anxious", "worried", "panic", "nervous", "scared", "fear", "overthinking", "what if"],
    "depression": ["depressed", "numb", "empty", "hopeless", "pointless", "don't care", "no interest"],
    "motivation": ["lazy", "procrastinate", "can't start", "no motivation", "avoiding", "putting off"],
    "sleep": ["sleep", "insomnia", "can't sleep", "woke up", "nightmare", "tired", "rest"],
    "growth": ["learn", "improve", "goal", "progress", "better", "growth", "skill", "habit"],
}


def infer_state(text: str) -> InferredState:
    """Analyze a message and extract psychological state indicators.

    This runs on EVERY user message. It's lightweight (no API calls)
    and builds up a picture over time.
    """
    state = InferredState()
    text_lower = text.lower()
    words = text_lower.split()
    state.word_count = len(words)

    if state.word_count == 0:
        return state

    # ── Basic linguistic features ──
    state.avg_word_length = sum(len(w) for w in words) / len(words)

    # First-person pronoun ratio (elevated in depression)
    first_person = sum(1 for w in words if w in ("i", "me", "my", "mine", "myself", "i'm", "i've", "i'll", "i'd"))
    state.first_person_ratio = first_person / len(words)

    # Absolutist language count
    state.absolutist_count = sum(1 for w in words if w in ABSOLUTIST_WORDS)

    # ── Mood Valence ──
    pos_count = sum(1 for w in words if w in POSITIVE_WORDS)
    neg_count = sum(1 for w in words if w in NEGATIVE_WORDS)
    total_sentiment = pos_count + neg_count

    if total_sentiment > 0:
        # Scale to 1-10: pure negative = 1, pure positive = 10
        pos_ratio = pos_count / total_sentiment
        state.mood_valence = round(1 + pos_ratio * 9, 1)
        state.confidence += 0.3
    elif state.word_count >= 5:
        # No strong sentiment words — assume neutral
        state.mood_valence = 5.5
        state.confidence += 0.1

    # ── Energy Level ──
    high_e = sum(1 for phrase in HIGH_ENERGY_WORDS if phrase in text_lower)
    low_e = sum(1 for phrase in LOW_ENERGY_WORDS if phrase in text_lower)

    if high_e > 0 or low_e > 0:
        total_e = high_e + low_e
        high_ratio = high_e / total_e
        state.energy_level = round(1 + high_ratio * 9, 1)
        state.confidence += 0.3
    elif state.word_count >= 10:
        # Infer from message length + complexity (longer, richer = more energy)
        length_signal = min(state.word_count / 50, 1.0)  # Normalize
        state.energy_level = round(4 + length_signal * 4, 1)
        state.confidence += 0.1

    # ── Change Talk vs Sustain Talk (MI) ──
    change_matches = sum(1 for p in CHANGE_TALK_PATTERNS if re.search(p, text_lower))
    sustain_matches = sum(1 for p in SUSTAIN_TALK_PATTERNS if re.search(p, text_lower))
    total_mi = change_matches + sustain_matches

    if total_mi > 0:
        state.change_talk_score = round(change_matches / total_mi, 2)
        state.sustain_talk_score = round(sustain_matches / total_mi, 2)
        state.confidence += 0.2

        # Motivation from change talk ratio
        state.motivation_level = round(1 + state.change_talk_score * 9, 1)

    # ── Stage of Change ──
    for stage, patterns in STAGE_PATTERNS.items():
        matches = sum(1 for p in patterns if re.search(p, text_lower))
        if matches > 0:
            state.stage_signals[stage] = matches

    # ── Theme Detection ──
    for theme, keywords in THEME_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            state.themes.append(theme)

    # Clamp confidence
    state.confidence = min(state.confidence, 1.0)

    return state


def aggregate_states(states: list[InferredState]) -> dict:
    """Aggregate multiple inferred states into summary metrics.

    Used for dashboard population — averages mood/energy/motivation
    across recent messages.
    """
    if not states:
        return {"mood": None, "energy": None, "motivation": None, "themes": [], "stage": None}

    # Average mood across messages that had signal
    moods = [s.mood_valence for s in states if s.mood_valence is not None]
    energies = [s.energy_level for s in states if s.energy_level is not None]
    motivations = [s.motivation_level for s in states if s.motivation_level is not None]

    # Weighted by confidence
    def weighted_avg(values, weights):
        if not values:
            return None
        total_w = sum(weights)
        if total_w == 0:
            return sum(values) / len(values)
        return round(sum(v * w for v, w in zip(values, weights)) / total_w, 1)

    mood_weights = [s.confidence for s in states if s.mood_valence is not None]
    energy_weights = [s.confidence for s in states if s.energy_level is not None]
    motivation_weights = [s.confidence for s in states if s.motivation_level is not None]

    # Theme frequency
    all_themes = {}
    for s in states:
        for t in s.themes:
            all_themes[t] = all_themes.get(t, 0) + 1
    top_themes = sorted(all_themes, key=all_themes.get, reverse=True)[:5]

    # Dominant stage
    stage_votes = {}
    for s in states:
        for stage, count in s.stage_signals.items():
            stage_votes[stage] = stage_votes.get(stage, 0) + count
    dominant_stage = max(stage_votes, key=stage_votes.get) if stage_votes else None

    # Change talk ratio
    total_change = sum(s.change_talk_score for s in states)
    total_sustain = sum(s.sustain_talk_score for s in states)
    change_ratio = None
    if total_change + total_sustain > 0:
        change_ratio = round(total_change / (total_change + total_sustain), 2)

    return {
        "mood": weighted_avg(moods, mood_weights),
        "energy": weighted_avg(energies, energy_weights),
        "motivation": weighted_avg(motivations, motivation_weights),
        "themes": top_themes,
        "stage": dominant_stage,
        "change_talk_ratio": change_ratio,
        "absolutist_avg": round(sum(s.absolutist_count for s in states) / len(states), 2),
        "message_count": len(states),
    }
