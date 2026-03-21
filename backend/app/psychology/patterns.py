"""Pattern detection engine - finds recurring behavioral patterns in user data.

Uses statistical methods (rolling averages, frequency analysis, correlations).
No ML required. Each rule has a minimum data threshold before it fires.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class DataPoint:
    """Generic data point for pattern analysis."""

    timestamp: datetime
    metric: str  # "mood", "energy", "checkin", "habit_completion", etc.
    value: float
    tags: dict = field(default_factory=dict)  # extra context


@dataclass
class DetectedPatternResult:
    """A pattern detected from user data."""

    pattern_type: str  # temporal | mood_trigger | behavior_chain | energy_cycle | strategy_effectiveness
    description: str  # Human-readable description
    evidence: dict  # Data supporting this pattern
    confidence: float  # 0.0 - 1.0
    actionable_insight: Optional[str] = None  # What to do about it


# Minimum data points before any pattern fires
MIN_DATA_POINTS = 5
MIN_CONFIDENCE = 0.6


def detect_all_patterns(data_points: list[DataPoint]) -> list[DetectedPatternResult]:
    """Run all pattern detection rules on the data."""
    if len(data_points) < MIN_DATA_POINTS:
        return []

    patterns: list[DetectedPatternResult] = []

    patterns.extend(detect_temporal_patterns(data_points))
    patterns.extend(detect_mood_energy_correlation(data_points))
    patterns.extend(detect_day_of_week_patterns(data_points))
    patterns.extend(detect_streak_patterns(data_points))
    patterns.extend(detect_time_of_day_patterns(data_points))

    # Filter by confidence threshold
    return [p for p in patterns if p.confidence >= MIN_CONFIDENCE]


def detect_temporal_patterns(data_points: list[DataPoint]) -> list[DetectedPatternResult]:
    """Detect patterns related to specific days of the week.

    Example: "Your mood dips every Sunday evening"
    """
    patterns = []

    # Group mood scores by day of week
    mood_by_day: dict[int, list[float]] = defaultdict(list)
    for dp in data_points:
        if dp.metric == "mood":
            mood_by_day[dp.timestamp.weekday()].append(dp.value)

    if not mood_by_day:
        return []

    # Calculate average mood per day
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_averages = {}
    for day, scores in mood_by_day.items():
        if len(scores) >= 3:  # Need at least 3 data points per day
            day_averages[day] = sum(scores) / len(scores)

    if len(day_averages) < 3:  # Need data for at least 3 different days
        return []

    overall_avg = sum(day_averages.values()) / len(day_averages)

    # Find days significantly below or above average
    for day, avg in day_averages.items():
        diff = avg - overall_avg
        n_points = len(mood_by_day[day])

        if diff <= -1.0 and n_points >= 3:  # 1+ point below average
            confidence = min(0.5 + (abs(diff) * 0.15) + (n_points * 0.03), 0.95)
            patterns.append(DetectedPatternResult(
                pattern_type="temporal",
                description=f"Your mood tends to dip on {day_names[day]}s (avg {avg:.1f} vs overall {overall_avg:.1f})",
                evidence={
                    "day": day_names[day],
                    "day_average": round(avg, 1),
                    "overall_average": round(overall_avg, 1),
                    "data_points": n_points,
                },
                confidence=round(confidence, 2),
                actionable_insight=f"Consider scheduling something uplifting on {day_names[day]}s, or plan lighter days.",
            ))
        elif diff >= 1.0 and n_points >= 3:  # 1+ point above average
            confidence = min(0.5 + (abs(diff) * 0.15) + (n_points * 0.03), 0.95)
            patterns.append(DetectedPatternResult(
                pattern_type="temporal",
                description=f"Your mood tends to be higher on {day_names[day]}s (avg {avg:.1f} vs overall {overall_avg:.1f})",
                evidence={
                    "day": day_names[day],
                    "day_average": round(avg, 1),
                    "overall_average": round(overall_avg, 1),
                    "data_points": n_points,
                },
                confidence=round(confidence, 2),
                actionable_insight=f"What's different about {day_names[day]}s? Try bringing that into other days.",
            ))

    return patterns


def detect_mood_energy_correlation(data_points: list[DataPoint]) -> list[DetectedPatternResult]:
    """Detect correlation between energy and mood.

    Example: "When your energy is above 7, your mood averages 8.2"
    """
    patterns = []

    # Pair mood and energy readings by date
    mood_by_date: dict[str, float] = {}
    energy_by_date: dict[str, float] = {}

    for dp in data_points:
        date_key = dp.timestamp.strftime("%Y-%m-%d")
        if dp.metric == "mood":
            mood_by_date[date_key] = dp.value
        elif dp.metric == "energy":
            energy_by_date[date_key] = dp.value

    # Find dates with both readings
    paired = []
    for date_key in mood_by_date:
        if date_key in energy_by_date:
            paired.append((energy_by_date[date_key], mood_by_date[date_key]))

    if len(paired) < MIN_DATA_POINTS:
        return []

    # Split into high energy vs low energy days
    high_energy = [mood for energy, mood in paired if energy >= 7]
    low_energy = [mood for energy, mood in paired if energy <= 3]

    if len(high_energy) >= 3 and len(low_energy) >= 3:
        high_avg = sum(high_energy) / len(high_energy)
        low_avg = sum(low_energy) / len(low_energy)
        diff = high_avg - low_avg

        if diff >= 1.5:
            confidence = min(0.5 + (diff * 0.1) + (min(len(high_energy), len(low_energy)) * 0.03), 0.95)
            patterns.append(DetectedPatternResult(
                pattern_type="behavior_chain",
                description=f"Your mood is {diff:.1f} points higher on high-energy days (≥7) vs low-energy days (≤3)",
                evidence={
                    "high_energy_mood_avg": round(high_avg, 1),
                    "low_energy_mood_avg": round(low_avg, 1),
                    "high_energy_days": len(high_energy),
                    "low_energy_days": len(low_energy),
                },
                confidence=round(confidence, 2),
                actionable_insight="Energy and mood are linked for you. Protecting your energy (sleep, movement) directly protects your mood.",
            ))

    return patterns


def detect_day_of_week_patterns(data_points: list[DataPoint]) -> list[DetectedPatternResult]:
    """Detect habit completion patterns by day of week.

    Example: "You skip workouts on Mondays 80% of the time"
    """
    patterns = []

    # Group habit completions by day of week
    completions_by_day: dict[int, list[bool]] = defaultdict(list)
    for dp in data_points:
        if dp.metric == "habit_completion":
            completions_by_day[dp.timestamp.weekday()].append(dp.value > 0)

    if not completions_by_day:
        return []

    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Calculate completion rate per day
    overall_completions = []
    day_rates = {}
    for day, completions in completions_by_day.items():
        if len(completions) >= 3:
            rate = sum(completions) / len(completions)
            day_rates[day] = rate
            overall_completions.extend(completions)

    if not day_rates or not overall_completions:
        return []

    overall_rate = sum(overall_completions) / len(overall_completions)

    # Find days with significantly lower completion rate
    for day, rate in day_rates.items():
        n_points = len(completions_by_day[day])
        if rate <= 0.3 and overall_rate >= 0.5 and n_points >= 3:
            skip_pct = (1 - rate) * 100
            confidence = min(0.5 + ((overall_rate - rate) * 0.3) + (n_points * 0.02), 0.95)
            habit_name = None
            for dp in data_points:
                if dp.metric == "habit_completion" and dp.timestamp.weekday() == day:
                    habit_name = dp.tags.get("habit_name")
                    break

            desc = f"You skip habits on {day_names[day]}s {skip_pct:.0f}% of the time"
            if habit_name:
                desc = f"You skip '{habit_name}' on {day_names[day]}s {skip_pct:.0f}% of the time"

            patterns.append(DetectedPatternResult(
                pattern_type="temporal",
                description=desc,
                evidence={
                    "day": day_names[day],
                    "completion_rate": round(rate, 2),
                    "overall_rate": round(overall_rate, 2),
                    "data_points": n_points,
                },
                confidence=round(confidence, 2),
                actionable_insight=f"What's different about {day_names[day]}s? Maybe swap to a tiny version on that day instead of skipping entirely.",
            ))

    return patterns


def detect_streak_patterns(data_points: list[DataPoint]) -> list[DetectedPatternResult]:
    """Detect patterns related to check-in streaks and absences.

    Example: "After 2+ days without check-ins, your next mood is usually low"
    """
    patterns = []

    # Get check-in dates sorted
    checkin_dates = sorted(set(
        dp.timestamp.date() for dp in data_points if dp.metric in ("mood", "checkin")
    ))

    if len(checkin_dates) < MIN_DATA_POINTS:
        return []

    # Find gaps and mood after gaps
    gap_return_moods = []
    regular_moods = []

    mood_by_date = {}
    for dp in data_points:
        if dp.metric == "mood":
            mood_by_date[dp.timestamp.date()] = dp.value

    for i in range(1, len(checkin_dates)):
        gap_days = (checkin_dates[i] - checkin_dates[i - 1]).days
        return_mood = mood_by_date.get(checkin_dates[i])

        if return_mood is not None:
            if gap_days >= 2:
                gap_return_moods.append(return_mood)
            else:
                regular_moods.append(return_mood)

    if len(gap_return_moods) >= 3 and len(regular_moods) >= 3:
        gap_avg = sum(gap_return_moods) / len(gap_return_moods)
        regular_avg = sum(regular_moods) / len(regular_moods)
        diff = regular_avg - gap_avg

        if diff >= 1.0:
            confidence = min(0.5 + (diff * 0.1) + (len(gap_return_moods) * 0.05), 0.95)
            patterns.append(DetectedPatternResult(
                pattern_type="behavior_chain",
                description=f"After 2+ days without checking in, your mood is {diff:.1f} points lower than usual",
                evidence={
                    "avg_mood_after_gap": round(gap_avg, 1),
                    "avg_mood_regular": round(regular_avg, 1),
                    "gap_instances": len(gap_return_moods),
                },
                confidence=round(confidence, 2),
                actionable_insight="Checking in regularly seems to help your mood. Even a 30-second quick check-in counts.",
            ))

    return patterns


def detect_time_of_day_patterns(data_points: list[DataPoint]) -> list[DetectedPatternResult]:
    """Detect energy patterns by time of day.

    Example: "Your energy peaks between 9-11am"
    """
    patterns = []

    # Group energy by time bucket
    time_buckets = {
        "morning (6-9am)": (6, 9),
        "mid-morning (9-12pm)": (9, 12),
        "afternoon (12-3pm)": (12, 15),
        "late afternoon (3-6pm)": (15, 18),
        "evening (6-9pm)": (18, 21),
        "night (9pm+)": (21, 24),
    }

    energy_by_bucket: dict[str, list[float]] = defaultdict(list)
    for dp in data_points:
        if dp.metric == "energy":
            hour = dp.timestamp.hour
            for bucket_name, (start, end) in time_buckets.items():
                if start <= hour < end:
                    energy_by_bucket[bucket_name].append(dp.value)
                    break

    if len(energy_by_bucket) < 2:
        return []

    # Find peak and trough
    bucket_avgs = {}
    for bucket, values in energy_by_bucket.items():
        if len(values) >= 3:
            bucket_avgs[bucket] = sum(values) / len(values)

    if len(bucket_avgs) < 2:
        return []

    peak_bucket = max(bucket_avgs, key=bucket_avgs.get)
    trough_bucket = min(bucket_avgs, key=bucket_avgs.get)
    diff = bucket_avgs[peak_bucket] - bucket_avgs[trough_bucket]

    if diff >= 1.5:
        confidence = min(0.5 + (diff * 0.1) + (len(energy_by_bucket[peak_bucket]) * 0.02), 0.95)
        patterns.append(DetectedPatternResult(
            pattern_type="energy_cycle",
            description=f"Your energy peaks in the {peak_bucket} (avg {bucket_avgs[peak_bucket]:.1f}) and dips in the {trough_bucket} (avg {bucket_avgs[trough_bucket]:.1f})",
            evidence={
                "peak_time": peak_bucket,
                "peak_avg": round(bucket_avgs[peak_bucket], 1),
                "trough_time": trough_bucket,
                "trough_avg": round(bucket_avgs[trough_bucket], 1),
                "all_averages": {k: round(v, 1) for k, v in bucket_avgs.items()},
            },
            confidence=round(confidence, 2),
            actionable_insight=f"Schedule your most important work for {peak_bucket}. Save easy tasks for {trough_bucket}.",
        ))

    return patterns


def detect_strategy_effectiveness(
    suggestions: list[dict],
) -> list[DetectedPatternResult]:
    """Detect which suggestion strategies work best for this user.

    Input: list of dicts with keys: strategy_type, status (accepted/rejected/completed), effectiveness_rating
    """
    patterns = []

    if len(suggestions) < MIN_DATA_POINTS:
        return []

    # Group by strategy type
    by_strategy: dict[str, list[dict]] = defaultdict(list)
    for s in suggestions:
        by_strategy[s["strategy_type"]].append(s)

    strategy_scores: dict[str, float] = {}
    for strategy, items in by_strategy.items():
        if len(items) < 3:
            continue

        completed = sum(1 for i in items if i.get("status") == "completed")
        rejected = sum(1 for i in items if i.get("status") == "rejected")
        total = len(items)

        completion_rate = completed / total
        rejection_rate = rejected / total
        strategy_scores[strategy] = completion_rate

        # Flag high rejection rate
        if rejection_rate >= 0.6 and total >= 5:
            confidence = min(0.5 + (rejection_rate * 0.3), 0.95)
            patterns.append(DetectedPatternResult(
                pattern_type="strategy_effectiveness",
                description=f"You reject '{strategy}' suggestions {rejection_rate*100:.0f}% of the time",
                evidence={
                    "strategy": strategy,
                    "rejection_rate": round(rejection_rate, 2),
                    "total_suggestions": total,
                },
                confidence=round(confidence, 2),
                actionable_insight=f"I'll suggest fewer '{strategy}' approaches and try alternatives that work better for you.",
            ))

    # Find best strategy
    if len(strategy_scores) >= 2:
        best = max(strategy_scores, key=strategy_scores.get)
        worst = min(strategy_scores, key=strategy_scores.get)
        diff = strategy_scores[best] - strategy_scores[worst]

        if diff >= 0.3:
            confidence = min(0.5 + (diff * 0.3), 0.9)
            patterns.append(DetectedPatternResult(
                pattern_type="strategy_effectiveness",
                description=f"'{best}' suggestions work best for you ({strategy_scores[best]*100:.0f}% completion) vs '{worst}' ({strategy_scores[worst]*100:.0f}%)",
                evidence={
                    "best_strategy": best,
                    "best_rate": round(strategy_scores[best], 2),
                    "worst_strategy": worst,
                    "worst_rate": round(strategy_scores[worst], 2),
                    "all_scores": {k: round(v, 2) for k, v in strategy_scores.items()},
                },
                confidence=round(confidence, 2),
                actionable_insight=f"I'll lean more into '{best}' approaches since they resonate with you.",
            ))

    return patterns
