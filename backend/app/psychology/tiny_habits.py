"""Tiny Habits module - BJ Fogg's behavior design framework.

Core formula: After I [ANCHOR], I will [TINY BEHAVIOR], and celebrate by [CELEBRATION].
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TinyHabitRecipe:
    """A complete tiny habit recipe following BJ Fogg's framework."""

    anchor: str  # Existing routine: "After I pour my morning coffee"
    tiny_behavior: str  # 2-second version: "I will do 2 pushups"
    full_behavior: str  # Aspirational: "30-minute workout"
    celebration: str  # Immediate reward: "I'll say 'I'm getting stronger!'"
    life_area: str
    scale_levels: list[str]  # Progressive versions from tiny to full


# Common anchors people already have
COMMON_ANCHORS = [
    "After I wake up and put my feet on the floor",
    "After I pour my morning coffee/tea",
    "After I brush my teeth (morning)",
    "After I sit down at my desk",
    "After I eat lunch",
    "After I finish work for the day",
    "After I eat dinner",
    "After I brush my teeth (evening)",
    "After I get into bed",
]

# Tiny habit templates by life area
HABIT_TEMPLATES: dict[str, list[dict]] = {
    "physical": [
        {
            "name": "Move more",
            "tiny": "Do 2 pushups",
            "scales": [
                "Do 2 pushups",
                "Do 5 pushups",
                "Do a 5-minute bodyweight circuit",
                "Do a 15-minute workout",
                "Complete a full workout",
            ],
            "full": "Daily exercise routine",
            "suggested_anchor": "After I pour my morning coffee/tea",
            "celebration": "Say 'I'm getting stronger!'",
        },
        {
            "name": "Drink water",
            "tiny": "Take one sip of water",
            "scales": [
                "Take one sip of water",
                "Drink half a glass",
                "Drink a full glass",
                "Track water intake for the day",
            ],
            "full": "Stay hydrated all day",
            "suggested_anchor": "After I wake up and put my feet on the floor",
            "celebration": "Feel the cool water and smile",
        },
        {
            "name": "Stretch",
            "tiny": "Do one shoulder roll",
            "scales": [
                "Do one shoulder roll",
                "Stretch for 1 minute",
                "Do a 5-minute morning stretch",
                "Complete a 15-minute yoga flow",
            ],
            "full": "Daily stretching routine",
            "suggested_anchor": "After I wake up and put my feet on the floor",
            "celebration": "Take a deep breath and say 'ahh'",
        },
        {
            "name": "Walk",
            "tiny": "Put on your shoes",
            "scales": [
                "Put on your shoes",
                "Walk to the door and back",
                "Walk around the block",
                "Walk for 15 minutes",
                "Walk for 30+ minutes",
            ],
            "full": "Daily walk",
            "suggested_anchor": "After I finish work for the day",
            "celebration": "Notice how the air feels on your face",
        },
    ],
    "mental": [
        {
            "name": "Journal",
            "tiny": "Write one sentence about your day",
            "scales": [
                "Write one sentence",
                "Write 3 sentences",
                "Free-write for 5 minutes",
                "Deep journal session for 15 minutes",
            ],
            "full": "Daily journaling practice",
            "suggested_anchor": "After I get into bed",
            "celebration": "Say 'I showed up for myself'",
        },
        {
            "name": "Breathe",
            "tiny": "Take one deep breath",
            "scales": [
                "Take one deep breath",
                "Take 3 deep breaths",
                "Do box breathing for 1 minute",
                "Meditate for 5 minutes",
                "Meditate for 15 minutes",
            ],
            "full": "Daily meditation",
            "suggested_anchor": "After I sit down at my desk",
            "celebration": "Notice how your body feels right now",
        },
        {
            "name": "Gratitude",
            "tiny": "Think of one thing you're not annoyed about",
            "scales": [
                "Think of one thing you're not annoyed about",
                "Name one thing you're grateful for",
                "Write down 3 things you're grateful for",
                "Write a gratitude letter to someone",
            ],
            "full": "Daily gratitude practice",
            "suggested_anchor": "After I get into bed",
            "celebration": "Smile and let the feeling sit for a moment",
        },
    ],
    "career": [
        {
            "name": "Learn",
            "tiny": "Read one paragraph of something in your field",
            "scales": [
                "Read one paragraph",
                "Read for 5 minutes",
                "Read for 15 minutes",
                "Complete a lesson or tutorial",
            ],
            "full": "Daily learning habit",
            "suggested_anchor": "After I eat lunch",
            "celebration": "Say 'I'm growing'",
        },
        {
            "name": "Code",
            "tiny": "Open your editor and read one line of code",
            "scales": [
                "Open your editor",
                "Write or modify one line",
                "Work on code for 10 minutes",
                "Complete a focused coding session",
            ],
            "full": "Daily coding practice",
            "suggested_anchor": "After I pour my morning coffee/tea",
            "celebration": "Fist pump and say 'shipped it'",
        },
        {
            "name": "Plan",
            "tiny": "Write tomorrow's #1 priority on a sticky note",
            "scales": [
                "Write your #1 priority",
                "List top 3 tasks for tomorrow",
                "Plan your full day with time blocks",
            ],
            "full": "Daily planning",
            "suggested_anchor": "After I finish work for the day",
            "celebration": "Close your notebook with satisfaction",
        },
    ],
    "habits": [
        {
            "name": "Track",
            "tiny": "Open Mirror and look at your streaks",
            "scales": [
                "Open Mirror",
                "Log one habit completion",
                "Do a quick check-in",
                "Do a full check-in and reflect",
            ],
            "full": "Daily tracking and reflection",
            "suggested_anchor": "After I brush my teeth (evening)",
            "celebration": "Say 'I'm paying attention to my life'",
        },
    ],
}


def get_templates_for_area(life_area: str) -> list[dict]:
    """Get available habit templates for a life area."""
    return HABIT_TEMPLATES.get(life_area, [])


def create_recipe(
    template: dict,
    anchor: Optional[str] = None,
    celebration: Optional[str] = None,
) -> TinyHabitRecipe:
    """Create a tiny habit recipe from a template."""
    return TinyHabitRecipe(
        anchor=anchor or template["suggested_anchor"],
        tiny_behavior=template["tiny"],
        full_behavior=template["full"],
        celebration=celebration or template["celebration"],
        life_area=template.get("life_area", "general"),
        scale_levels=template["scales"],
    )


def scale_to_energy(recipe: TinyHabitRecipe, energy: int) -> str:
    """Return the version of the habit appropriate for the current energy level.

    At low energy, always falls back to the tiniest version.
    """
    energy = max(1, min(10, energy))
    num_levels = len(recipe.scale_levels)

    if energy <= 2:
        return recipe.scale_levels[0]  # Always tiny
    elif energy <= 4:
        idx = min(1, num_levels - 1)
    elif energy <= 6:
        idx = min(2, num_levels - 1)
    elif energy <= 8:
        idx = min(3, num_levels - 1)
    else:
        idx = num_levels - 1  # Full version

    return recipe.scale_levels[idx]


def suggest_anchor(life_area: str, time_of_day: Optional[str] = None) -> list[str]:
    """Suggest anchors based on life area and time of day."""
    morning_anchors = [
        "After I wake up and put my feet on the floor",
        "After I pour my morning coffee/tea",
        "After I brush my teeth (morning)",
    ]
    workday_anchors = [
        "After I sit down at my desk",
        "After I eat lunch",
    ]
    evening_anchors = [
        "After I finish work for the day",
        "After I eat dinner",
        "After I brush my teeth (evening)",
        "After I get into bed",
    ]

    if time_of_day == "morning":
        return morning_anchors
    elif time_of_day == "evening":
        return evening_anchors
    elif time_of_day == "work":
        return workday_anchors

    return COMMON_ANCHORS
