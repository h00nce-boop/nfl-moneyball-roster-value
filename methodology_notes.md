# Methodology Notes

## Project Goal

This project uses public NFL data to evaluate roster value through a Moneyball-style lens: which teams and players generate the most production relative to contract cost?

The goal is not to create a perfect front-office valuation system. It is to build a transparent public-data model that can identify roster-building patterns, surplus-value players, and possible market inefficiencies.

The central question is:

> Can public data identify production before the market fully prices it?

## Season Labeling

This project uses NFL season-year labels, not calendar-year labels.

A season is labeled by the year in which the NFL season begins. For example, the 2025 season refers to the 2025 NFL season, even though that season concludes in early 2026.

The descriptive model covers the 2021-2025 NFL seasons.

V4 and V5 validation use 2021-2024 as candidate seasons because each candidate season requires a following-season outcome:

* 2021 candidates are evaluated using 2022 outcomes
* 2022 candidates are evaluated using 2023 outcomes
* 2023 candidates are evaluated using 2024 outcomes
* 2024 candidates are evaluated using 2025 outcomes

The 2025 season is treated as the latest candidate pool because 2026 outcomes are not available yet.

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

For V4, the model creates a cleaned player-season-position table. This collapses duplicate player-season-position rows before recomputing production rank, cost rank, and surplus gap. The goal is to evaluate whether a player's full-season surplus signal carries forward into the following season.

### Candidate Pool

The V4 backtest starts with high-confidence rookie-contract players from the 2021-2024 candidate seasons.

The default model-candidate threshold is:

```text
player_surplus_gap >= 5
```

The comparison group is made up of high-confidence rookie-contract players with:

```text
player_surplus_gap < 5
```

This comparison tests whether the surplus signal adds value beyond simply identifying rookie-contract players.

It is not a causal matched-control design. The model-flagged group already has stronger current surplus by construction. V5 addresses this by adding a matched rookie-contract baseline.

### Outcome Window

Each candidate season is evaluated using the following season:

* 2021 candidates -> 2022 outcomes
* 2022 candidates -> 2023 outcomes
* 2023 candidates -> 2024 outcomes
* 2024 candidates -> 2025 outcomes

The 2025 season is not used as a validation candidate season because 2026 outcomes are not available yet.

### First-pass Hit Definition

A player is counted as a first-pass V4 hit if he:

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

The most important V4 performance outputs are:

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

### Candidate-review Summaries

Candidate-review outputs are qualitative inspection tools, not the primary model-performance tables.

The review buckets are defined by outcome type:

* true positives
* model misses
* missed opportunities

Because those buckets are outcome-defined, their summary table should not be interpreted as a hit-rate table.

Model performance should be evaluated using the V4 lift, threshold-sensitivity, season-stability, and performance-reference files listed above.

## V5: Matched Validation and Opportunity Controls

V5 strengthens the validation layer by asking whether the rookie-contract surplus signal survives a fairer comparison group.

The main V5 question is:

> Among rookie-contract players with similar season, position, draft-capital profile, contract-stage profile, production percentile, and regular-season opportunity, did model-flagged surplus candidates perform better the next season than matched non-candidates?

### V5 Feature Table

V5 begins with the cleaned V4 player-season table and adds public snap-count and injury-report context.

Regular-season and playoff snaps are intentionally separated. Regular-season opportunity is used in the matching logic, while playoff data is preserved as additional context.

Important regular-season opportunity fields include:

* `reg_snap_games`
* `reg_offense_snaps`
* `reg_avg_offense_snap_pct`
* `reg_max_offense_snap_pct`
* `reg_games_off_snap_50_plus`
* `reg_games_off_snap_70_plus`
* `played_regular_season`

Important playoff context fields include:

* `playoff_snap_games`
* `playoff_offense_snaps`
* `playoff_avg_offense_snap_pct`
* `played_playoffs`

Important injury-report fields include:

* `injury_report_weeks`
* `out_weeks`
* `doubtful_weeks`
* `questionable_weeks`
* `practice_dnp_weeks`
* `limited_practice_weeks`
* `was_on_injury_report`
* `has_injury_source_for_season`
* `injury_merge_matched`

The injury fields improve auditability and future modeling options, but the main V5 matched specification should not be described as a complete injury-adjusted model.

### V5 Candidate Definition

The default V5 candidate definition is:

```text
is_likely_rookie_contract == True
AND player_surplus_gap >= 5
```

The default non-candidate pool is:

```text
is_likely_rookie_contract == True
AND player_surplus_gap < 5
```

The surplus gap remains the signal being tested.

### Validation Window

V5 uses historical rows where the following season exists in the dataset.

That means the historical validation window uses 2021-2024 candidate seasons and evaluates them using 2022-2025 outcomes.

The 2025 candidate pool is saved separately as a 2026 evaluation/watchlist file because 2026 outcomes are not available yet.

### Outcome Labels

V5 creates several next-season outcome labels.

Primary V5 hit:

```text
next_year_top_half_position == 1
```

This means the player appeared in the next season and ranked in the top half of his position by next-season production percentile.

Secondary V5 hit:

```text
retained_positive_surplus == 1
```

This means the player appeared in the next season and retained a positive next-season surplus gap.

Additional outcome labels include:

* `appeared_next_year`
* `next_year_same_position`
* `retained_positive_surplus`
* `improved_production_score`
* `improved_production_percentile`
* `next_year_top_half_position`
* `next_year_top_third_position`
* `next_year_meaningful_regular_role`

The meaningful-role outcome is defined as:

```text
next_year_reg_snap_games >= 8
AND next_year_reg_avg_offense_snap_pct >= 0.25
```

### Matching Design

The V5 matched backtest compares candidates to similar rookie-contract non-candidates.

Candidates:

```text
is_v5_default_candidate == 1
AND primary_v5_hit is not missing
```

Controls:

```text
rookie_contract_bool == True
AND is_v5_default_candidate == 0
AND primary_v5_hit is not missing
```

Controls can be reused. The main specification uses K=3 controls per candidate when available.

The exact-match tiers are tried in this order:

1. Same season, position, draft-capital bucket, and estimated contract stage
2. Same season, position, and draft-capital bucket
3. Same season, position, and estimated contract stage
4. Same season and position

Within each exact-match tier, nearest controls are selected using weighted distance across these variables:

| Match feature | Weight |
| --- | ---: |
| `match_production_pct` | 2.00 |
| `match_reg_avg_offense_snap_pct` | 1.25 |
| `match_reg_snap_games` | 1.00 |
| `match_reg_offense_snaps_pctile` | 1.00 |
| `match_years_since_drafted` | 0.75 |

The model intentionally does not match on `player_surplus_gap`. That variable is the surplus signal being tested.

### Lift Calculation

For each matched candidate, the model compares the candidate's outcome to the average outcome of his matched controls.

For each outcome:

```text
candidate_lift = candidate_outcome - matched_control_outcome_mean
```

The summary lift is the average candidate-level lift across matched candidates.

The script also reports standard errors and approximate 95 percent confidence intervals using the distribution of candidate-level differences.

### K-sensitivity

V5 repeats the matched validation for K=1, K=3, and K=5 matched controls.

The output convention is intentionally redundant: each run is stored in a K-specific folder and each file receives the same K prefix. For example, the default run writes `outputs_v5/backtests/k3/k3_matched_lift_summary_v5.csv`. The folder separates the sensitivity runs, while the filename remains self-describing if files are exported, attached, or compared outside the repository structure.

The goal is to test whether the conclusion depends on one arbitrary matched-control count.

The primary lift remained positive across K=1, K=3, and K=5.

### Main V5 Interpretation

In the main K=3 matched specification, V5 candidates produced a +14.3 percentage-point lift in next-season top-half positional production versus matched controls. The K=3 run matched 252 historical V5 candidates from the 2021-2024 candidate seasons.

Default K=3 matched-control results:

| Outcome | Candidate rate | Matched-control rate | Lift | Approx. 95% CI |
| --- | ---: | ---: | ---: | ---: |
| `primary_v5_hit` / top-half next-season production | 56.3% | 42.1% | +14.3 pp | +7.5 to +21.1 pp |
| `secondary_v5_hit` / retained positive surplus | 56.3% | 32.0% | +24.3 pp | +17.3 to +31.3 pp |
| `next_year_meaningful_regular_role` | 82.5% | 65.6% | +16.9 pp | +11.5 to +22.3 pp |
| `appeared_next_year` | 85.3% | 65.6% | +19.7 pp | +14.6 to +24.8 pp |

The signal was positive for the main persistence-oriented outcomes: appearing again, remaining positive-surplus, maintaining a meaningful role, and producing in the top half of the position the following season.

The output also includes improvement-based labels. Those are not the headline result. In the K=3 run, `improved_production_score` and `improved_production_percentile` were negative versus matched controls. That does not invalidate the persistence finding, but it does affect how the result should be described. V5 should be framed as a surplus-persistence and role-retention signal, not as proof that candidates are more likely to improve raw production from the current season.

### K-sensitivity Results

The primary hit-rate lift remained positive across alternate matched-control counts:

| K | Matched candidates | Candidate rate | Matched-control rate | Primary lift | Approx. 95% CI |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 252 | 56.3% | 46.0% | +10.3 pp | +2.1 to +18.5 pp |
| 3 | 252 | 56.3% | 42.1% | +14.3 pp | +7.5 to +21.1 pp |
| 5 | 252 | 56.3% | 36.1% | +20.3 pp | +13.6 to +27.0 pp |

This sensitivity check supports the conclusion that the primary result is not dependent on one arbitrary matched-control count. The increase from K=1 to K=5 should not be over-interpreted as a monotonic law; it may reflect the available matched-control pool and control averaging. The safe claim is that the primary lift remained positive under all three tested K values.

### Matching-quality Diagnostics

The K=3 tier summary shows that most candidates were matched using the strictest exact-match tier:

| Match tier | Matched candidates | Share of matched candidates | Avg. matched controls | Primary lift |
| --- | ---: | ---: | ---: | ---: |
| Same season, position, draft-capital bucket, and contract stage | 228 | 90.5% | 2.53 | +13.5 pp |
| Same season, position, and draft-capital bucket | 1 | 0.4% | 3.00 | +33.3 pp |
| Same season, position, and contract stage | 23 | 9.1% | 3.00 | +21.7 pp |

This is useful context for the public methodology because the matched comparison is not mostly falling back to loose same-season/same-position matches. Most candidates receive controls from the strictest tier.

### Position and Season Diagnostics

The validation visuals also break out primary lift by position and candidate season. These splits should be treated as diagnostics because the sample sizes are smaller and the uncertainty intervals are wider.

Current figure-level position lifts:

| Position | Primary lift |
| --- | ---: |
| RB | +28.1 pp |
| QB | +25.9 pp |
| TE | +9.6 pp |
| WR | +5.8 pp |

Current figure-level validation-season lifts:

| Candidate season | Primary lift |
| ---: | ---: |
| 2021 | +21.6 pp |
| 2022 | +25.6 pp |
| 2023 | +15.8 pp |
| 2024 | -4.2 pp |

The season split is important for interpretation: the primary lift was positive in three of four validation seasons, while the 2024 candidate cohort was the weak cohort. The README and dashboard should mention that nuance rather than presenting the aggregate result as uniformly positive every season.

It should not be interpreted as causal proof, a guaranteed breakout model, or a complete front-office valuation system.

## Market-inefficiency Analysis

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

This connects the original market-efficiency question to the V3 contract-cycle model and the V4/V5 validation layers.

## Interpretation Rules

The model supports claims like:

* "This player or team generated more production than their public cost rank suggested."
* "This profile showed surplus value in the valid-cost, high-confidence universe."
* "The V4 candidate profile showed first-pass next-season persistence against a rookie-contract baseline."
* "The V5 candidate profile showed positive next-season lift against a matched rookie-contract baseline."
* "The 2025 candidate pool identifies players who match the historically tested V5 profile and can be evaluated when 2026 data becomes available."

The model does not support claims like:

* "This is a complete front-office valuation system."
* "This proves a player is objectively underpaid."
* "The V5 model proves causality."
* "The V5 model guarantees future breakouts."
* "The 2025 candidate pool players are guaranteed hits."
* "The matched controls remove all bias."

## Current Limitations

* Public contract data may be incomplete.
* Contract cost is a public-data proxy, not audited official salary-cap accounting.
* Draft matching depends on player IDs in public datasets.
* Contract stage is estimated, not a full cap-accounting model.
* Offensive skill-position production is easier to measure than offensive line or defensive value.
* The player model currently excludes defense and offensive line.
* Production-score weights are hand-built rather than statistically learned.
* Rank gaps are intuitive but coarse and do not show the magnitude between players.
* V5 adds snap-based opportunity controls, but it does not fully model scheme, teammate quality, coaching context, opponent strength, depth-chart changes, or player development.
* V5 includes injury-report features, but the main matched specification should not be described as fully injury-adjusted.
* The V4 hit definition is a first-pass validation rule, not a final predictive target.
* The V4 baseline is useful for comparison but is not a causal matched-control group.
* The V5 matched baseline improves comparability, but it is still observational and controls can be reused.
* K-sensitivity tests robustness to matched-control count, but it does not replace a full causal identification strategy.