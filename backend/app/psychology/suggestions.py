"""Suggestion engine - picks the right action for the right moment.

Core principle: match suggestion difficulty to user's actual energy level.
Track what works and what doesn't to self-calibrate over time.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.psychology.cbt import detect_distortions, generate_reframe
from app.psychology.energy import get_mva, get_validation


@dataclass
class SuggestionResult:
    """A suggestion to present to the user."""

    content: str
    strategy_type: str  # mva | cbt_reframe | tiny_habit | general
    life_area: str
    energy_required: int
    rationale: str
    validation: Optional[str] = None  # Empathetic prefix for low energy


@dataclass
class UserState:
    """Current state of the user for suggestion selection."""

    energy: int  # 1-10
    mood: int  # 1-10
    mood_tags: list[str] = field(default_factory=list)
    recent_thought: Optional[str] = None  # For CBT detection
    life_area_scores: dict[str, float] = field(default_factory=dict)
    days_since_last_checkin: int = 0
    strategy_effectiveness: dict[str, float] = field(default_factory=dict)
    recent_rejections: list[str] = field(default_factory=list)


# Life areas sorted by priority (lowest scoring first)
LIFE_AREAS = ["physical", "mental", "career", "habits"]


def suggest(state: UserState) -> SuggestionResult:
    """Generate a contextual suggestion based on current user state.

    Selection logic:
    1. If energy <= 2: only MVAs (minimum viable actions)
    2. If cognitive distortions detected: CBT reframe
    3. If returning after absence: gentle welcome
    4. Otherwise: energy-matched action for weakest life area
    """

    # Rule 1: Returning after absence
    if state.days_since_last_checkin >= 3:
        return SuggestionResult(
            content=(
                "Welcome back. No judgment, no guilt. "
                "You're here now, and that's what matters. "
                "How are you doing?"
            ),
            strategy_type="validation",
            life_area="general",
            energy_required=0,
            rationale="User returning after 3+ day absence",
            validation="We missed you, but life happens.",
        )

    # Rule 2: Very low energy - only MVAs
    if state.energy <= 2:
        target_area = _get_weakest_area(state)
        mva = get_mva(target_area, state.energy)
        return SuggestionResult(
            content=mva.action,
            strategy_type="mva",
            life_area=target_area,
            energy_required=mva.energy_required,
            rationale=f"Energy at {state.energy}/10 - only micro-actions suggested",
            validation=mva.validation,
        )

    # Rule 3: Check for cognitive distortions in recent thought
    if state.recent_thought:
        distortions = detect_distortions(state.recent_thought)
        if distortions and distortions[0].confidence >= 0.5:
            top_distortion = distortions[0]
            reframe = generate_reframe(state.recent_thought, top_distortion)
            return SuggestionResult(
                content=reframe.reframed_thought,
                strategy_type="cbt_reframe",
                life_area="mental",
                energy_required=2,
                rationale=f"Detected {top_distortion.display_name} in user's thought",
                validation=reframe.explanation,
            )

    # Rule 4: Low mood (3 or below) - validation first, gentle suggestion
    if state.mood <= 3:
        mva = get_mva("mental", min(state.energy, 4))
        return SuggestionResult(
            content=mva.action,
            strategy_type="mva",
            life_area="mental",
            energy_required=mva.energy_required,
            rationale="Low mood - prioritizing mental health with gentle suggestion",
            validation=get_validation(state.energy),
        )

    # Rule 5: Energy-matched suggestion for weakest life area
    target_area = _get_weakest_area(state)
    mva = get_mva(target_area, state.energy)

    # Avoid strategies that have been recently rejected
    strategy_type = "mva"
    if state.energy >= 5 and "mva" in state.recent_rejections:
        strategy_type = "general"

    return SuggestionResult(
        content=mva.action,
        strategy_type=strategy_type,
        life_area=target_area,
        energy_required=mva.energy_required,
        rationale=f"Energy at {state.energy}/10, targeting weakest area: {target_area}",
        validation=get_validation(state.energy) if state.energy <= 4 else None,
    )


def _get_weakest_area(state: UserState) -> str:
    """Get the life area with the lowest score."""
    if not state.life_area_scores:
        return "physical"  # Default

    return min(state.life_area_scores, key=lambda a: state.life_area_scores.get(a, 5.0))


def score_strategy(
    strategy_type: str,
    state: UserState,
) -> float:
    """Score a strategy type for the current user state.

    Higher score = better fit. Used for ranking when multiple strategies apply.
    """
    score = 1.0

    # Effectiveness history
    effectiveness = state.strategy_effectiveness.get(strategy_type, 0.5)
    score *= effectiveness

    # Energy match
    energy_costs = {"mva": 1, "cbt_reframe": 2, "tiny_habit": 3, "general": 4}
    cost = energy_costs.get(strategy_type, 3)
    if cost > state.energy:
        score *= 0.1  # Heavily penalize suggestions above energy level

    # Novelty - penalize recently rejected
    if strategy_type in state.recent_rejections:
        score *= 0.3

    return score
