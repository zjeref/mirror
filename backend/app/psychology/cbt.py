"""CBT (Cognitive Behavioral Therapy) module.

Detects cognitive distortions in user text and generates reframes.
Uses rule-based pattern matching (no LLM required for detection).
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ScoredDistortion:
    name: str
    display_name: str
    confidence: float  # 0.0 - 1.0
    matched_text: str
    explanation: str


@dataclass
class Reframe:
    distortion: str
    original_thought: str
    reframed_thought: str
    explanation: str


# Distortion patterns: (regex_pattern, distortion_name, display_name, explanation_template)
DISTORTION_PATTERNS = [
    # All-or-nothing thinking
    (
        r"\b(always|never|every\s*time|completely|totally|100%|nothing\s+ever|everything\s+is)\b",
        "all_or_nothing",
        "All-or-Nothing Thinking",
        "You're seeing things in black and white. Reality usually lives in the gray area.",
    ),
    # Catastrophizing
    (
        r"\b(worst|terrible|disaster|catastrophe|ruined|destroyed|end\s+of|horrible|can't\s+handle|falling\s+apart)\b",
        "catastrophizing",
        "Catastrophizing",
        "You might be imagining the worst possible outcome. What's the most likely outcome instead?",
    ),
    # Mind reading
    (
        r"\b(they\s+think|everyone\s+knows|people\s+must|they\s+probably|they\s+all|no\s+one\s+cares)\b",
        "mind_reading",
        "Mind Reading",
        "You're assuming you know what others think. But do you actually have evidence for that?",
    ),
    # Should statements
    (
        r"\b(i\s+should|i\s+must|i\s+have\s+to|i\s+need\s+to|i\s+ought\s+to|supposed\s+to)\b",
        "should_statements",
        "Should Statements",
        "You're placing rigid rules on yourself. What if 'should' became 'could' or 'want to'?",
    ),
    # Overgeneralization
    (
        r"\b(nothing\s+works|everything\s+goes\s+wrong|this\s+always|i\s+always\s+fail|never\s+going\s+to)\b",
        "overgeneralization",
        "Overgeneralization",
        "One experience doesn't define a pattern. What are some times this went differently?",
    ),
    # Labeling
    (
        r"\b(i('m|\s+am)\s+(such\s+)?(a\s+)?(failure|loser|idiot|stupid|worthless|useless|broken|lazy))\b",
        "labeling",
        "Labeling",
        "You're defining yourself by one label. You're a complex person having a hard moment.",
    ),
    # Emotional reasoning
    (
        r"\b(i\s+feel\s+(like\s+)?(a\s+)?(failure|worthless|stupid|incompetent|hopeless))\b",
        "emotional_reasoning",
        "Emotional Reasoning",
        "Feeling something doesn't make it true. Your emotions are valid, but they're not facts.",
    ),
    # Disqualifying the positive
    (
        r"\b(doesn't\s+count|that\s+was\s+(just\s+)?luck|anyone\s+could|it\s+was\s+nothing|but\s+that's\s+not)\b",
        "disqualifying_positive",
        "Disqualifying the Positive",
        "You're dismissing something positive. What if you let yourself take credit for it?",
    ),
    # Fortune telling
    (
        r"\b(i\s+know\s+(it|this)\s+will|going\s+to\s+fail|won't\s+work|no\s+point|what's\s+the\s+use)\b",
        "fortune_telling",
        "Fortune Telling",
        "You're predicting the future negatively. But you don't have a crystal ball — what if it goes okay?",
    ),
]


def detect_distortions(text: str) -> list[ScoredDistortion]:
    """Detect cognitive distortions in text using pattern matching.

    Returns distortions sorted by confidence (highest first).
    """
    text_lower = text.lower()
    found: list[ScoredDistortion] = []
    seen_types: set[str] = set()

    for pattern, name, display_name, explanation in DISTORTION_PATTERNS:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches and name not in seen_types:
            # Confidence based on how many pattern matches found
            confidence = min(0.5 + (len(matches) * 0.15), 0.95)

            # Get the actual matched text
            match_obj = re.search(pattern, text_lower, re.IGNORECASE)
            matched_text = match_obj.group(0) if match_obj else ""

            found.append(
                ScoredDistortion(
                    name=name,
                    display_name=display_name,
                    confidence=confidence,
                    matched_text=matched_text,
                    explanation=explanation,
                )
            )
            seen_types.add(name)

    return sorted(found, key=lambda d: d.confidence, reverse=True)


# Reframe templates keyed by distortion type
REFRAME_TEMPLATES = {
    "all_or_nothing": [
        "You said '{thought}'. What if you looked at what you DID do, even if it wasn't everything?",
        "Between 'never' and 'always', where did you actually land? Partial credit counts.",
        "What's one small exception to '{thought}'? Even a tiny one?",
    ],
    "catastrophizing": [
        "That sounds really heavy. What's the most LIKELY outcome here, not the worst possible one?",
        "On a scale of 1-10, how likely is the worst case? What about a 'just okay' outcome?",
        "If a friend told you '{thought}', what would you gently say back?",
    ],
    "mind_reading": [
        "You might be right, but have you checked? What evidence do you actually have?",
        "What if they're thinking something completely different — or not thinking about it at all?",
        "Is there another explanation for their behavior that doesn't involve you?",
    ],
    "should_statements": [
        "What if you replaced 'should' with 'could'? '{thought}' becomes a choice, not a command.",
        "Who made this rule? Is it actually yours, or did you absorb it from somewhere?",
        "What would you tell a friend who said '{thought}' to themselves?",
    ],
    "overgeneralization": [
        "This feels like a pattern, but is it really? Can you think of one time it went differently?",
        "What if this is one data point, not the whole dataset?",
        "'{thought}' — is that actually true every time, or does it feel that way right now?",
    ],
    "labeling": [
        "You're not a '{label}'. You're a person who had a tough moment. There's a big difference.",
        "If you described this situation to someone else, would they use the word '{label}'?",
        "You've done things that don't fit that label. What's one of them?",
    ],
    "emotional_reasoning": [
        "Your feelings are real and valid. But feeling like a failure doesn't mean you are one.",
        "Emotions are messengers, not facts. What's the feeling actually trying to tell you?",
        "What would you think about this situation on a day when you felt better?",
    ],
    "disqualifying_positive": [
        "You just dismissed something good. What if you let it count, even a little?",
        "If it was 'nothing', why did you bring it up? Part of you knows it matters.",
        "What if your bar for 'counts' is set too high?",
    ],
    "fortune_telling": [
        "You're predicting the future, but your track record of predictions includes surprises too.",
        "What if it doesn't go perfectly but still goes okay? What would 'okay' look like?",
        "'{thought}' — what evidence supports this? What evidence contradicts it?",
    ],
}


def generate_reframe(thought: str, distortion: ScoredDistortion) -> Reframe:
    """Generate a reframe for a detected cognitive distortion."""
    templates = REFRAME_TEMPLATES.get(distortion.name, REFRAME_TEMPLATES["all_or_nothing"])
    # Pick the first template (in production, rotate or pick based on user preferences)
    template = templates[0]

    # Extract label if it's a labeling distortion
    label = distortion.matched_text.split()[-1] if distortion.name == "labeling" else ""

    reframed = template.format(thought=thought, label=label)

    return Reframe(
        distortion=distortion.display_name,
        original_thought=thought,
        reframed_thought=reframed,
        explanation=distortion.explanation,
    )
