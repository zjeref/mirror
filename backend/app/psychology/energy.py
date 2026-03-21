"""Energy module - maps energy levels to appropriate action difficulty.

The core principle: never suggest more than the user can handle.
At energy 1, even standing up is an achievement.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MinimumViableAction:
    """The smallest possible action that still counts as progress."""

    validation: str  # Empathetic acknowledgment first
    action: str  # The suggested action
    fallback: str  # Even easier alternative
    scale_up: Optional[str] = None  # If they feel like doing more
    energy_required: int = 1
    life_area: str = "general"
    time_estimate: str = "< 1 min"


# Energy ladders per life area
# Each level maps to a list of possible MVAs at that energy
ENERGY_LADDERS: dict[str, dict[int, list[dict]]] = {
    "physical": {
        1: [
            {"action": "Take 3 deep breaths right where you are.", "time": "30 sec"},
            {"action": "Stretch your arms above your head once.", "time": "10 sec"},
            {"action": "Stand up for 10 seconds, then sit back down.", "time": "15 sec"},
        ],
        2: [
            {"action": "Walk to the nearest window and look outside for 30 seconds.", "time": "1 min"},
            {"action": "Fill a glass of water and drink it.", "time": "1 min"},
            {"action": "Do 2 shoulder rolls.", "time": "20 sec"},
        ],
        3: [
            {"action": "Put on your shoes. That's it. You can take them off.", "time": "1 min"},
            {"action": "Walk to your front door and back.", "time": "2 min"},
            {"action": "Do 3 pushups (wall pushups count).", "time": "1 min"},
        ],
        4: [
            {"action": "Walk around the block. No pace requirement.", "time": "5 min"},
            {"action": "Do a 3-minute stretch routine.", "time": "3 min"},
            {"action": "Dance to one song. Any movement counts.", "time": "3 min"},
        ],
        5: [
            {"action": "10 minutes of any movement. Walking, stretching, anything.", "time": "10 min"},
            {"action": "Take a short walk outside.", "time": "10 min"},
        ],
        6: [
            {"action": "15-minute walk at whatever pace feels right.", "time": "15 min"},
            {"action": "A quick bodyweight circuit: 10 squats, 10 pushups, 30-sec plank.", "time": "10 min"},
        ],
        7: [
            {"action": "20-30 minute workout or walk.", "time": "25 min"},
            {"action": "Go to the gym. Even 20 minutes counts.", "time": "30 min"},
        ],
        8: [
            {"action": "Full planned workout.", "time": "45 min"},
            {"action": "Run, bike, or do a full routine.", "time": "45 min"},
        ],
    },
    "mental": {
        1: [
            {"action": "Close your eyes for 30 seconds. That's it.", "time": "30 sec"},
            {"action": "Name 3 things you can see right now.", "time": "30 sec"},
            {"action": "Put your hand on your chest and feel your heartbeat.", "time": "20 sec"},
        ],
        2: [
            {"action": "Write one sentence about how you feel. Just one.", "time": "1 min"},
            {"action": "Text someone you care about, even just an emoji.", "time": "30 sec"},
        ],
        3: [
            {"action": "Open your journal and write 3 sentences. Stream of consciousness.", "time": "3 min"},
            {"action": "Name one thing that went okay today, even tiny.", "time": "1 min"},
        ],
        4: [
            {"action": "Do a 5-minute free-write. Don't filter, just write.", "time": "5 min"},
            {"action": "Listen to one song that matches how you feel.", "time": "4 min"},
        ],
        5: [
            {"action": "Journal for 10 minutes about whatever's on your mind.", "time": "10 min"},
            {"action": "Try a 5-minute guided breathing exercise.", "time": "5 min"},
        ],
        6: [
            {"action": "Reflect on one thing you're grateful for and why.", "time": "5 min"},
            {"action": "Call or message a friend you haven't talked to recently.", "time": "10 min"},
        ],
        7: [
            {"action": "Do a proper journaling session. Dig into what you're feeling and why.", "time": "20 min"},
        ],
        8: [
            {"action": "Work through a thought record for something that's been bothering you.", "time": "30 min"},
        ],
    },
    "career": {
        1: [
            {"action": "Open your work app. Just open it. You can close it.", "time": "10 sec"},
            {"action": "Read one unread message or notification.", "time": "30 sec"},
        ],
        2: [
            {"action": "Write down tomorrow's single most important task.", "time": "1 min"},
            {"action": "Clear one notification or email.", "time": "2 min"},
        ],
        3: [
            {"action": "Spend 5 minutes on the easiest task on your list.", "time": "5 min"},
            {"action": "Organize your workspace for 3 minutes.", "time": "3 min"},
        ],
        4: [
            {"action": "Do one small task from your list. Anything counts.", "time": "10 min"},
            {"action": "Read one article related to your field.", "time": "10 min"},
        ],
        5: [
            {"action": "25-minute focused work session on your top priority.", "time": "25 min"},
        ],
        6: [
            {"action": "One pomodoro (25 min) on your most important task.", "time": "25 min"},
            {"action": "Spend 20 minutes learning something new for your career.", "time": "20 min"},
        ],
        7: [
            {"action": "Two pomodoros on deep work.", "time": "55 min"},
        ],
        8: [
            {"action": "Full deep work session. Block distractions, go all in.", "time": "90 min"},
        ],
    },
    "habits": {
        1: [
            {"action": "Just acknowledge: 'I'm thinking about my habits.' That counts.", "time": "5 sec"},
        ],
        2: [
            {"action": "Look at your habit list. Just look at it.", "time": "30 sec"},
            {"action": "Do the tiniest version of one habit.", "time": "1 min"},
        ],
        3: [
            {"action": "Complete one tiny habit from your list.", "time": "2 min"},
        ],
        4: [
            {"action": "Complete 2 habits from your list.", "time": "10 min"},
        ],
        5: [
            {"action": "Complete all your tiny habits today.", "time": "15 min"},
        ],
        6: [
            {"action": "Do the full version of your most important habit.", "time": "20 min"},
        ],
        7: [
            {"action": "Crush your habits today. Full versions.", "time": "30 min"},
        ],
        8: [
            {"action": "All habits, full versions, plus reflect on what's working.", "time": "45 min"},
        ],
    },
}

# Validation messages by energy level
VALIDATIONS = {
    1: [
        "Having almost no energy is real, not laziness. Your body is protecting you.",
        "Right now, existing is enough. Seriously.",
        "You showed up here. That already took energy you barely have. That counts.",
    ],
    2: [
        "Very low energy today. That's valid. We'll keep it tiny.",
        "You don't need to be productive to be worthwhile. Let's find one micro-step.",
    ],
    3: [
        "Energy is low but you're here. Let's find something that takes almost nothing.",
        "Some fuel in the tank, but not much. Let's be strategic about it.",
    ],
    4: [
        "You've got a little energy. Let's use it wisely on one thing that matters.",
    ],
    5: [
        "Middle ground. Enough to do something meaningful if we pick the right thing.",
    ],
}


def get_validation(energy: int) -> str:
    """Get an empathetic validation message for the user's energy level."""
    if energy >= 6:
        return "You've got energy to work with. Let's make it count."

    messages = VALIDATIONS.get(energy, VALIDATIONS[5])
    # In production, rotate through messages and avoid repeats
    return messages[0]


def get_mva(
    life_area: str,
    energy: int,
    user_calibration: Optional[dict] = None,
) -> MinimumViableAction:
    """Get the minimum viable action for a life area at a given energy level.

    Args:
        life_area: One of physical, mental, career, habits
        energy: 1-10 energy level
        user_calibration: Optional dict of {area: {energy_level: adjusted_level}}
            to personalize based on what the user actually does.
    """
    energy = max(1, min(10, energy))
    area_ladder = ENERGY_LADDERS.get(life_area, ENERGY_LADDERS["physical"])

    # Apply user calibration if available
    effective_energy = energy
    if user_calibration and life_area in user_calibration:
        calibration = user_calibration[life_area]
        effective_energy = calibration.get(str(energy), energy)

    # Find the closest energy level in the ladder
    available_levels = sorted(area_ladder.keys())
    target_level = min(available_levels, key=lambda l: abs(l - effective_energy))

    # Ensure we don't suggest above their actual energy
    if target_level > energy:
        lower_levels = [l for l in available_levels if l <= energy]
        target_level = max(lower_levels) if lower_levels else min(available_levels)

    actions = area_ladder[target_level]
    action = actions[0]  # In production, rotate

    # Get fallback (one level lower)
    fallback_level = max(min(available_levels), target_level - 1)
    fallback_actions = area_ladder.get(fallback_level, actions)
    fallback = fallback_actions[0]

    # Get scale-up (one level higher)
    scale_up_level = min(max(available_levels), target_level + 1)
    scale_up_actions = area_ladder.get(scale_up_level, actions)

    return MinimumViableAction(
        validation=get_validation(energy),
        action=action["action"],
        fallback=fallback["action"],
        scale_up=scale_up_actions[0]["action"] if scale_up_level != target_level else None,
        energy_required=target_level,
        life_area=life_area,
        time_estimate=action.get("time", "< 5 min"),
    )
