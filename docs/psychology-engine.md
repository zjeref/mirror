# Psychology Engine

## Core Principles

1. **Never guilt the user.** Validation first, suggestions second.
2. **Energy-calibrated actions.** Never suggest more than the user can handle.
3. **Track outcomes.** Every suggestion eventually gets a worked/didn't signal.
4. **Minimum data thresholds.** No patterns surfaced until ≥ 5 data points.
5. **Adapt over time.** Deprioritize strategies that get rejected.

## Strategy Selection

```python
score = base_relevance × user_effectiveness × energy_match × novelty_bonus
```

### Energy Rules
- Energy ≤ 2: ONLY MVA (minimum viable actions) or validation
- Energy 3-4: MVA + tiny habits eligible
- Energy 5-6: Add CBT reframes
- Energy 7+: All strategies including aspirational
- 3+ days declining: Validation-first mode

## CBT Module (`cbt.py`)

### Detected Distortions
| Distortion | Example Pattern |
|-----------|----------------|
| All-or-nothing | "always", "never", "completely" |
| Catastrophizing | "worst", "disaster", "ruined" |
| Mind reading | "they think", "everyone knows" |
| Should statements | "I should", "I must", "supposed to" |
| Overgeneralization | "nothing works", "always fail" |
| Labeling | "I'm a failure", "I'm worthless" |
| Emotional reasoning | "I feel like a failure" |
| Disqualifying positive | "doesn't count", "was just luck" |
| Fortune telling | "I know it will fail", "no point" |

### Adding a New Distortion
1. Add regex pattern to `DISTORTION_PATTERNS` list in `cbt.py`
2. Add reframe templates to `REFRAME_TEMPLATES` dict
3. Add test in `tests/test_psychology/test_cbt.py`

## Energy Ladders (`energy.py`)

### Life Areas
Each area has actions for energy levels 1-8:

**Physical**: breathe → stretch → shoes on → walk block → 10min movement → 15min walk → 30min workout → full workout

**Mental**: close eyes → write 1 sentence → journal 3 sentences → 5min free-write → 10min journal → gratitude → deep journal → thought record

**Career**: open app → clear 1 notification → 5min easy task → 1 small task → pomodoro → deep pomodoro → 2 pomodoros → full deep work

**Habits**: acknowledge → look at list → 1 tiny habit → 2 habits → all tiny → full version → all full → all full + reflect

### Adding a New Life Area
1. Add ladder dict to `ENERGY_LADDERS` in `energy.py`
2. Add to `LifeArea` enum in `life_areas.py`
3. Add templates in `tiny_habits.py`
4. Update tests

## Pattern Detection (`patterns.py`)

### Pattern Types
| Type | What It Detects | Min Data |
|------|----------------|----------|
| temporal | Day-of-week mood variations | 3 per day, 3+ days |
| behavior_chain | Mood-energy correlation | 5 paired readings |
| temporal (habits) | Day-of-week habit skip rates | 3 per day |
| behavior_chain (streaks) | Mood drop after absence | 3 gap instances |
| energy_cycle | Time-of-day energy peaks/troughs | 3 per time bucket |
| strategy_effectiveness | Which strategies get rejected/completed | 3 per strategy |

### Adding a New Pattern Rule
1. Create detection function in `patterns.py`
2. Set minimum data threshold (never < 5)
3. Calculate confidence score (0.0-1.0)
4. Include `actionable_insight` in result
5. Add to `detect_all_patterns()` function
6. Add test with synthetic data in `test_patterns.py`

## Suggestion Engine (`suggestions.py`)

### Selection Priority
1. **Returning after 3+ day absence** → Welcome back (validation only)
2. **Energy ≤ 2** → MVA for weakest life area
3. **Cognitive distortion detected** → CBT reframe
4. **Low mood (≤ 3)** → Mental health MVA
5. **Default** → Energy-matched action for weakest life area

### Self-Calibration
The engine tracks:
- `strategy_effectiveness`: completion rate per strategy type
- `recent_rejections`: strategies rejected in last N suggestions
- Rejected strategies get 0.3× score multiplier
- High-energy-cost strategies get 0.1× when above user's energy
