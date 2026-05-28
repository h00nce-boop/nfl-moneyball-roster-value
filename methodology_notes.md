# Methodology Notes

## Project Goal

This project uses public NFL data to evaluate roster value through a Moneyball-style lens: which teams and players generate the most production relative to contract cost?

The goal is not to create a perfect front-office valuation system. It is to build a transparent public-data model that can identify roster-building patterns, surplus-value players, and possible market inefficiencies.

## Season labeling

This project uses NFL season-year labels, not calendar-year labels. A season is labeled by the year in which the NFL season begins. For example, the 2025 season refers to the 2025 NFL season, even though that season concludes in early 2026.

The descriptive model covers the 2021–2025 NFL seasons.

V4 backtesting uses 2021–2024 as candidate seasons because each candidate season requires a following-season outcome:

- 2021 candidates are evaluated using 2022 outcomes
- 2022 candidates are evaluated using 2023 outcomes
- 2023 candidates are evaluated using 2024 outcomes
- 2024 candidates are evaluated using 2025 outcomes

The 2025 season is treated as the latest-season watchlist because 2026 outcomes are not available yet.

## V1: Baseline Surplus Value

The original model compares production rank to cost rank.

For teams:

```text
surplus_rank_gap = cap_cost_rank - overall_performance_rank
```

For players:

```text
player_surplus_gap = cost_rank_position - production_rank_position
```

A positive gap means the team or player produced better than their cost rank. A negative gap means the team or player was expensive relative to their production rank.

The player model focuses on offensive skill-position players:

- QB
- RB
- WR
- TE

## V2: Confidence Workflow

V2 adds confidence and data-quality flags.

The goal is to avoid over-interpreting players with missing contract data or very small samples.

Important fields:

- `has_contract_match`
- `has_missing_contract`
- `contract_confidence`
- `meets_sample_threshold`
- `sample_confidence`
- `overall_confidence`

The diagnostic file preserves flagged and excluded players for auditability.

This update prevents missing public contract data from being treated as a meaningful zero-dollar cost and separates stronger player-value signals from lower-confidence results.

## V3: Contract Context

V3 adds draft-capital and estimated contract-stage context.

This helps separate general cheapness from structurally underpriced production, especially rookie-contract and pre-extension players.

Important fields:

- `draft_year`
- `draft_round`
- `draft_pick`
- `draft_capital_bucket`
- `years_since_drafted`
- `estimated_contract_stage`
- `is_likely_rookie_contract`
- `surplus_context`

This moves the model closer to the central Moneyball question: can production be identified before the market fully prices it?

## V4: Backtesting and Decision Support

V4 tests whether high-confidence rookie-contract surplus candidates outperform similar rookie-contract players the model did not flag.

The backtest uses the same player-season surplus framework but evaluates next-season outcomes.

### Candidate pool

The V4 backtest starts with high-confidence rookie-contract players from the 2021–2024 candidate seasons.

The default model-candidate threshold is:

```text
player_surplus_gap >= 5
```

The comparison group is made up of similar high-confidence rookie-contract players with:

```text
player_surplus_gap < 5
```

### Outcome window

Each candidate season is evaluated using the following season:

- 2021 candidates -> 2022 outcomes
- 2022 candidates -> 2023 outcomes
- 2023 candidates -> 2024 outcomes
- 2024 candidates -> 2025 outcomes

The 2025 season is not used as a backtest candidate season because 2026 outcomes are not available yet.

### First-pass hit definition

A player is counted as a first-pass hit if he:

```text
appeared in the following season
AND
(remained positive-surplus OR improved production score)
```

This is intentionally simple and should be interpreted as a first validation layer, not a final prediction model.

### Baseline comparison

The preferred V4 comparison is:

```text
model candidates vs. not-flagged rookie-contract baseline
```

This tests whether the surplus signal adds value beyond simply identifying rookie-contract players.

### Threshold sensitivity

V4 tests multiple surplus thresholds:

```text
0, 3, 5, 10, 15, 20
```

This checks whether the model depends too heavily on one arbitrary cutoff.

### Season stability

V4 also evaluates whether the signal is stable across candidate seasons. This helps identify whether the overall result is broad-based or driven by one season.

### Candidate review

V4 creates human-readable review tables:

- true positives
- model misses
- missed opportunities
- 2025 latest-season watchlist

The 2025 watchlist is not a backtest result. It identifies latest-season players who match the historically tested candidate profile and should be evaluated when 2026 data becomes available.

## Current Limitations

- Public contract data may be incomplete.
- Contract cost is a public-data proxy, not audited official salary-cap accounting.
- Draft matching depends on player IDs in public datasets.
- Contract stage is estimated, not a full cap-accounting model.
- Offensive skill-position production is easier to measure than offensive line or defensive value.
- Production-score weights are hand-built rather than statistically learned.
- Rank gaps are intuitive but coarse and do not show the magnitude between players.
- The model does not yet include injuries, snap counts, scheme, teammates, coaching context, or opponent strength.
- The V4 hit definition is a first-pass validation rule, not a final predictive target.