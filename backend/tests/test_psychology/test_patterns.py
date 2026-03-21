"""Tests for pattern detection engine."""

import pytest
from datetime import datetime, timedelta

from app.psychology.patterns import (
    DataPoint,
    detect_all_patterns,
    detect_temporal_patterns,
    detect_mood_energy_correlation,
    detect_day_of_week_patterns,
    detect_streak_patterns,
    detect_strategy_effectiveness,
)


def _make_date(days_ago: int, hour: int = 12) -> datetime:
    return datetime.now() - timedelta(days=days_ago, hours=hour)


def _generate_checkins_with_monday_dip(weeks: int = 6) -> list[DataPoint]:
    """Generate mood data where Mondays are consistently lower."""
    points = []
    for week in range(weeks):
        for day in range(7):
            date = _make_date(week * 7 + day)
            # Force to specific weekday
            while date.weekday() != day:
                date += timedelta(days=1)

            mood = 7.0 if day != 0 else 4.0  # Monday (0) = low
            points.append(DataPoint(timestamp=date, metric="mood", value=mood))
    return points


class TestTemporalPatterns:
    def test_detects_monday_mood_dip(self):
        data = _generate_checkins_with_monday_dip(weeks=6)
        patterns = detect_temporal_patterns(data)
        assert len(patterns) >= 1
        monday_patterns = [p for p in patterns if "Monday" in p.description]
        assert len(monday_patterns) >= 1
        assert "dip" in monday_patterns[0].description.lower()

    def test_no_pattern_with_insufficient_data(self):
        data = [
            DataPoint(timestamp=_make_date(1), metric="mood", value=7),
            DataPoint(timestamp=_make_date(2), metric="mood", value=6),
        ]
        patterns = detect_temporal_patterns(data)
        assert len(patterns) == 0

    def test_detects_high_mood_days(self):
        points = []
        for week in range(6):
            for day in range(7):
                date = _make_date(week * 7 + day)
                while date.weekday() != day:
                    date += timedelta(days=1)
                mood = 5.0 if day != 5 else 9.0  # Saturday (5) = high
                points.append(DataPoint(timestamp=date, metric="mood", value=mood))

        patterns = detect_temporal_patterns(points)
        saturday_patterns = [p for p in patterns if "Saturday" in p.description]
        assert len(saturday_patterns) >= 1
        assert "higher" in saturday_patterns[0].description.lower()


class TestMoodEnergyCorrelation:
    def test_detects_energy_mood_link(self):
        points = []
        for i in range(20):
            date = _make_date(i)
            if i % 2 == 0:  # High energy days
                points.append(DataPoint(timestamp=date, metric="energy", value=8))
                points.append(DataPoint(timestamp=date, metric="mood", value=8))
            else:  # Low energy days
                points.append(DataPoint(timestamp=date, metric="energy", value=2))
                points.append(DataPoint(timestamp=date, metric="mood", value=3))

        patterns = detect_mood_energy_correlation(points)
        assert len(patterns) >= 1
        assert "high-energy" in patterns[0].description.lower() or "higher" in patterns[0].description.lower()

    def test_no_correlation_when_random(self):
        import random
        random.seed(42)
        points = []
        for i in range(20):
            date = _make_date(i)
            points.append(DataPoint(timestamp=date, metric="energy", value=random.randint(4, 6)))
            points.append(DataPoint(timestamp=date, metric="mood", value=random.randint(4, 6)))

        patterns = detect_mood_energy_correlation(points)
        # With random data in narrow range, shouldn't find strong correlation
        assert all(p.confidence < 0.8 for p in patterns)


class TestDayOfWeekPatterns:
    def test_detects_monday_habit_skip(self):
        points = []
        for week in range(6):
            for day in range(7):
                date = _make_date(week * 7 + day)
                while date.weekday() != day:
                    date += timedelta(days=1)
                # Skip on Mondays, complete other days
                completed = 0.0 if day == 0 else 1.0
                points.append(DataPoint(
                    timestamp=date,
                    metric="habit_completion",
                    value=completed,
                    tags={"habit_name": "Exercise"},
                ))

        patterns = detect_day_of_week_patterns(points)
        monday_patterns = [p for p in patterns if "Monday" in p.description]
        assert len(monday_patterns) >= 1


class TestStreakPatterns:
    def test_detects_mood_drop_after_gap(self):
        points = []
        # Regular check-ins with good mood
        for i in range(10):
            date = _make_date(30 - i)
            points.append(DataPoint(timestamp=date, metric="mood", value=7))

        # Gap of 3 days, then low mood
        points.append(DataPoint(timestamp=_make_date(16), metric="mood", value=7))
        points.append(DataPoint(timestamp=_make_date(13), metric="mood", value=3))  # After gap

        # Another gap
        points.append(DataPoint(timestamp=_make_date(10), metric="mood", value=7))
        points.append(DataPoint(timestamp=_make_date(7), metric="mood", value=3))  # After gap

        # Another gap
        points.append(DataPoint(timestamp=_make_date(4), metric="mood", value=7))
        points.append(DataPoint(timestamp=_make_date(1), metric="mood", value=3))  # After gap

        patterns = detect_streak_patterns(points)
        # Should detect that mood drops after gaps
        gap_patterns = [p for p in patterns if "gap" in p.description.lower() or "checking in" in p.description.lower()]
        assert len(gap_patterns) >= 1


class TestStrategyEffectiveness:
    def test_detects_high_rejection_rate(self):
        suggestions = []
        for i in range(8):
            suggestions.append({
                "strategy_type": "cbt_reframe",
                "status": "rejected" if i < 6 else "completed",
            })
        for i in range(8):
            suggestions.append({
                "strategy_type": "mva",
                "status": "completed",
            })

        patterns = detect_strategy_effectiveness(suggestions)
        rejection_patterns = [p for p in patterns if "reject" in p.description.lower()]
        assert len(rejection_patterns) >= 1

    def test_detects_best_strategy(self):
        suggestions = []
        # MVA works well
        for _ in range(6):
            suggestions.append({"strategy_type": "mva", "status": "completed"})
        # CBT doesn't
        for _ in range(6):
            suggestions.append({"strategy_type": "cbt_reframe", "status": "rejected"})

        patterns = detect_strategy_effectiveness(suggestions)
        best_patterns = [p for p in patterns if "best" in p.description.lower() or "work" in p.description.lower()]
        assert len(best_patterns) >= 1

    def test_no_pattern_with_insufficient_data(self):
        suggestions = [{"strategy_type": "mva", "status": "completed"}]
        patterns = detect_strategy_effectiveness(suggestions)
        assert len(patterns) == 0


class TestDetectAll:
    def test_filters_low_confidence_patterns(self):
        """Only patterns above 0.6 confidence should be returned."""
        data = _generate_checkins_with_monday_dip(weeks=6)
        patterns = detect_all_patterns(data)
        for p in patterns:
            assert p.confidence >= 0.6

    def test_returns_empty_with_no_data(self):
        assert detect_all_patterns([]) == []

    def test_returns_empty_with_minimal_data(self):
        data = [DataPoint(timestamp=_make_date(1), metric="mood", value=5)]
        assert detect_all_patterns(data) == []

    def test_all_patterns_have_required_fields(self):
        data = _generate_checkins_with_monday_dip(weeks=6)
        patterns = detect_all_patterns(data)
        for p in patterns:
            assert p.pattern_type
            assert p.description
            assert 0.0 <= p.confidence <= 1.0
            assert p.evidence is not None
