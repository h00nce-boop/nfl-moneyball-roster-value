# Methodology Notes

## Project Goal

This project uses public NFL data to evaluate roster value through a Moneyball-style lens: which teams and players generate the most production relative to contract cost?

The goal is not to create a perfect front-office valuation system. It is to build a transparent public-data model that can identify roster-building patterns, surplus-value players, and possible market inefficiencies.

The central question is:

> Can public data identify production before the market fully prices it?

## Season Labeling

This project uses NFL season-year labels, not calendar-year labels.

A season is labeled by the year in which the NFL season begins. For example, the 2025 season refers to the 2025 NFL season, even though that season concludes in early 2026.

The descriptive model covers the 2021–2025 NFL seasons.

V4 backtesting uses 2021–2024 as candidate seasons because each candidate season requires a following-season outcome:

* 2021 candidates are evaluated using 2022 outcomes
* 2022 candidates are evaluated using 2023 outcomes
* 2023 candidates are evaluated using 2024 outcomes
* 2024 candidates are evaluated using 2025 outcomes

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

A positive gap means the team or player produced better than their cost rank.

A negative gap means the team or player was expensive relative to their production rank.

The player model focuses on offensive skill-position players:

* QB
* RB
* WR
* TE

The base descriptive player model is built at the player-team-season level. If a player appears for multiple teams in one season, each team stint may appear separately in descriptive outputs so production and cost can be attributed to the team context available in the public data.

## V2: Confidence Workflow

V2 adds confidence and data-quality flags.

The goal is to avoid over-interpreting players with missing contract data or very small samples.

Important fields:

* `has_contract_match`
* `has_missing_contract`
* `contract_confidence`
* `meets_sample_threshold`
* `sample_confidence`
* `overall_confidence`

The diagnostic file preserves flagged and excluded players for auditability.

This update prevents missing public contract data from being treated as meaningful zero-dollar cost and separates stronger player-value signals from lower-confidence results.

## V3: Contract Context

V3 adds draft-capital and estimated contract-stage context.

This helps separate general cheapness from structurally underpriced production, especially rookie-contract and pre-extension players.

Important fields:

* `draft_year`
* `draft_round`
* `draft_pick`
* `draft_capital_bucket`
* `years_since_drafted`
* `estimated_contract_stage`
* `is_likely_rookie_contract`
* `surplus_context`

This moves the model closer to the central Moneyball question: can production be identified before the market fully prices it?

## V4: Backtesting and Decision Support

V4 tests whether high-confidence rookie-contract surplus candidates outperform high-confidence rookie-contract players the model did not flag.

The backtest uses the same player-season surplus framework but evaluates next-season outcomes.

For V4, the model creates a cleaned player-season-position table. This collapses duplicate player-season-position rows before recomputing production rank, cost rank, and surplus gap. The goal is to evaluate whether a player’s full-season surplus signal carries forward into the following season.

### Candidate Pool

The V4 backtest starts with high-confidence rookie-contract players from the 2021–2024 candidate seasons.

The default model-candidate threshold is:

```text
player_surplus_gap >= 5
```

The comparison group is made up of high-confidence rookie-contract players with:

```text
player_surplus_gap < 5
```

This comparison tests whether the surplus signal adds value beyond simply identifying rookie-contract players.

It is not a causal matched-control design. The model-flagged group already has stronger current surplus by construction. Future versions should add matched baselines by position, draft capital, production tier, opportunity, age/experience, and season.

### Outcome Window

Each candidate season is evaluated using the following season:

* 2021 candidates -> 2022 outcomes
* 2022 candidates -> 2023 outcomes
* 2023 candidates -> 2024 outcomes
* 2024 candidates -> 2025 outcomes

The 2025 season is not used as a backtest candidate season because 2026 outcomes are not available yet.

### First-Pass Hit Definition

A player is counted as a first-pass hit if he:

```text
appeared in the following season
AND
(remained positive-surplus OR improved production score)
```

This is intentionally simple and should be interpreted as a first validation layer, not a final prediction model.

The broad hit definition captures whether a player remained relevant in the following season through either surplus retention or production improvement. It should not be interpreted as proof that the model predicts future breakouts.

### Baseline Comparison

The preferred V4 comparison is:

```text
model candidates vs. not-flagged rookie-contract baseline
```

This tests whether the surplus signal adds value beyond simply identifying rookie-contract players.

The most important performance outputs are:

* `backtest_lift_model_vs_not_flagged_clean.csv`
* `threshold_sensitivity_lift.csv`
* `season_stability_lift_by_season.csv`
* `candidate_review_performance_lift_reference.csv`

### Threshold Sensitivity

V4 tests multiple surplus thresholds:

```text
0, 3, 5, 10, 15, 20
```

This checks whether the model depends too heavily on one arbitrary cutoff.

### Season Stability

V4 also evaluates whether the signal is stable across candidate seasons.

This helps identify whether the overall result is broad-based or driven by one season.

### Candidate Review

V4 creates human-readable review tables:

* true positives
* model misses
* missed opportunities
* 2025 latest-season watchlist

The 2025 watchlist is not a backtest result. It identifies latest-season players who match the historically tested candidate profile and should be evaluated when 2026 data becomes available.

### Candidate Review Summaries

Candidate-review outputs are qualitative inspection tools, not the primary model-performance tables.

The review buckets are defined by outcome type:

* true positives
* model misses
* missed opportunities

Because those buckets are outcome-defined, their summary table should not be interpreted as a hit-rate table.

Model performance should be evaluated using the V4 lift, threshold-sensitivity, season-stability, and performance-reference files listed above.

## Market Inefficiency Analysis

The updated market-inefficiency workflow uses the V3 player-value output rather than the original V1 player table.

The public-facing market analysis is limited to rows with:

* high overall confidence
* non-missing public cap-number proxy
* cap number greater than zero

When available, the workflow also requires:

* a matched public contract record
* no missing-contract flag

Rows that fail those checks are preserved in an excluded-row audit file, but they are not used to draw public-facing cost-tier conclusions.

This prevents missing, unmatched, or invalid public contract data from being interpreted as a true low-cost player signal.

The analysis summarizes surplus value by:

* position
* cost tier
* estimated contract stage
* draft-capital bucket
* surplus context
* position by contract stage
* position by draft capital

This connects the original market-efficiency question to the V3 contract-cycle model and the V4 validation layer.

## Interpretation Rules

The model supports claims like:

* “This player or team generated more production than their public cost rank suggested.”
* “This profile showed surplus value in the valid-cost, high-confidence universe.”
* “The V4 candidate profile showed first-pass next-season persistence against a rookie-contract baseline.”
* “The 2025 watchlist identifies players who match the historically tested candidate profile.”

The model does not support claims like:

* “This is a complete front-office valuation system.”
* “This proves a player is objectively underpaid.”
* “The V4 model predicts future breakouts.”
* “The 2025 watchlist players are guaranteed hits.”
* “The backtest proves causality.”

## Current Limitations

* Public contract data may be incomplete.
* Contract cost is a public-data proxy, not audited official salary-cap accounting.
* Draft matching depends on player IDs in public datasets.
* Contract stage is estimated, not a full cap-accounting model.
* Offensive skill-position production is easier to measure than offensive line or defensive value.
* The player model currently excludes defense and offensive line.
* Production-score weights are hand-built rather than statistically learned.
* Rank gaps are intuitive but coarse and do not show the magnitude between players.
* The model does not yet include injuries, snap counts, scheme, teammates, coaching context, or opponent strength.
* The V4 hit definition is a first-pass validation rule, not a final predictive target.
* The V4 baseline is useful for comparison but is not a causal matched-control group.