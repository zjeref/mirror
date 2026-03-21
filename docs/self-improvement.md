# Self-Improvement Guide for Claude Code

This document explains how Claude Code can read, understand, and improve the Mirror codebase.

## How to Analyze Mirror's Effectiveness

### Step 1: Read the data
```python
# Query suggestion effectiveness
SELECT strategy_type,
       COUNT(*) as total,
       SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
       SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected,
       AVG(effectiveness_rating) as avg_rating
FROM suggestions
GROUP BY strategy_type;

# Query pattern confidence
SELECT pattern_type, description, confidence, times_confirmed
FROM detected_patterns
WHERE is_active = 1
ORDER BY confidence DESC;
```

### Step 2: Identify weak spots
- Which strategies have high rejection rates? → Consider new approaches
- Which life areas get least engagement? → Improve those energy ladders
- Which flow steps cause drop-off? → Simplify or improve UX
- Are pattern detections accurate? → Tune thresholds

### Step 3: Make improvements

## Improvement Categories

### 1. New Psychology Strategies
**When**: A strategy type has < 30% completion rate, or users frequently express needs the system can't address.

**How**:
1. Create `backend/app/psychology/new_strategy.py`
2. Add detection logic in `engine.py`
3. Add to suggestion scoring in `suggestions.py`
4. Add energy constraints
5. Write tests
6. Document in `docs/psychology-engine.md`

### 2. New Pattern Detection Rules
**When**: Users show behaviors the system doesn't detect yet.

**How**:
1. Add detection function in `patterns.py`
2. Set `minimum_data_points` (≥ 5)
3. Calculate confidence (only surface ≥ 0.6)
4. Include actionable_insight
5. Write test with synthetic data

### 3. New Chat Flows
**When**: Users need guided exercises the system doesn't offer.

**How**:
1. Create `backend/app/chat/flows/new_flow.py`
2. Inherit from BaseFlow, define steps as state machine
3. Register via `@register_flow` decorator
4. Add intent keywords in `engine.py` INTENT_PATTERNS
5. Write flow tests

### 4. Energy Ladder Tuning
**When**: Users at certain energy levels consistently reject suggestions or do harder things than suggested.

**How**:
1. Analyze `suggestions` table: energy_required vs user energy at time of suggestion
2. Adjust action difficulty in `ENERGY_LADDERS` dict
3. Add new actions to fill gaps
4. Ensure monotonicity: higher energy → harder suggestions

### 5. CBT Distortion Patterns
**When**: Users express cognitive distortions the system doesn't catch.

**How**:
1. Add regex to `DISTORTION_PATTERNS` in `cbt.py`
2. Add reframe templates to `REFRAME_TEMPLATES`
3. Test with real examples

### 6. Frontend UX
**When**: User engagement drops or specific components get low interaction.

**How**:
1. Check dashboard component usage
2. Simplify underused features
3. Add missing visualization types
4. Improve flow widget UX

## Improvement Backlog

### Open Ideas
- [ ] Seasonal mood detection (needs 3+ months of data)
- [ ] Social accountability (share streaks with a buddy)
- [ ] Energy forecasting from sleep + previous day data
- [ ] Guided breathing exercise flow
- [ ] Weekly/monthly recap emails
- [ ] Export data as PDF report
- [ ] Gratitude journaling flow
- [ ] Habit chaining suggestions (link habits together)
- [ ] Integration with wearable health data

### Rejected Ideas (with reasons)
- **Gamification (points/badges)**: Extrinsic motivation undermines intrinsic growth for target users
- **Social feed**: Comparing yourself to others contradicts validation-first philosophy
- **Streak shaming**: "You broke your streak!" is guilt-tripping. Never.

## Code Quality Checks

When improving Mirror, verify:
1. `cd backend && python -m pytest tests/ -v` → all tests pass
2. `cd frontend && npm run build` → builds clean
3. No guilt language in any user-facing text
4. Crisis detection still works (test_crisis.py)
5. Energy ≤ 2 only produces MVAs (test_suggestions.py)
6. New code has tests
