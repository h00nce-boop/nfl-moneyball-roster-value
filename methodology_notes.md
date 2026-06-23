# Methodology Notes: NFL Moneyball V5

## 1. Project goal

This project uses public NFL data to evaluate roster value through a Moneyball-style lens:

> Which offensive skill-position players produce more than their public contract-cost profile suggests?

The goal is not to create a complete front-office valuation system. The goal is to create a transparent decision-support workflow that can help identify players and player archetypes worth deeper review.

The current version is **V5**. V5 focuses on making the value definition clearer, adding opportunity controls, and validating the rookie-contract surplus signal against matched rookie-contract peers.

## 2. Data scope

### Seasons

The descriptive model covers the 2021-2025 NFL seasons.

V4 and V5 validation use 2021-2024 as candidate seasons because each candidate season requires a following-season outcome:

- 2021 candidates -> 2022 outcomes
- 2022 candidates -> 2023 outcomes
- 2023 candidates -> 2024 outcomes
- 2024 candidates -> 2025 outcomes

The 2025 season is saved as a 2026 evaluation/watchlist pool because 2026 outcomes are not available yet.

### Positions

The player model currently covers offensive skill-position players:

- QB
- RB
- WR
- TE

Defense and offensive line are not yet included.

### Data sources

The project uses public NFL data through `nflreadpy`, including player stats, EPA fields, team stats, rosters, contracts, draft data, snap counts, and injury reports.

Public contract cost is treated as a proxy. It is not official audited team cap accounting.

## 3. Value definition

### 3.1 Production score

The player production score is an EPA-based public-data production proxy.

EPA is the anchor because it values plays in context rather than treating all yards as equal. However, the production score is not pure EPA. It also adds lightweight traditional production terms so that volume and scoring output are represented.

```text
total_epa = passing_epa + rushing_epa + receiving_epa

production_score =
    total_epa
    + 0.01 * passing_yards
    + 2.00 * passing_tds
    - 2.00 * passing_interceptions
    - 0.25 * sacks_suffered
    + 0.05 * rushing_yards
    + 3.00 * rushing_tds
    + 0.25 * receptions
    + 0.05 * receiving_yards
    + 3.00 * receiving_tds
```

This score is designed for transparency and ranking, not as a final player grade.

### 3.2 Cost score

The cost side uses public contract data, primarily public cap number.

Rows with missing public contract matches are flagged. They should not be treated as true zero-cost players. High-confidence player-value claims require a usable contract match and sufficient player sample.

### 3.3 Rank-based value gap

Players are ranked within season and position by production and by cost.

```text
player_surplus_gap = cost_rank_within_position - production_rank_within_position
```

Interpretation:

- Positive value gap: the player produced better than his public cost rank.
- Negative value gap: the player was expensive relative to his production rank.
- Larger positive gaps identify stronger public-data surplus profiles.

Example:

```text
production_rank_within_position = 12
cost_rank_within_position = 31
player_surplus_gap = 31 - 12 = +19
```

The rank-gap approach is intuitive, but coarse. It does not measure how far apart two adjacent players are in actual production or dollars.

## 4. V1-V4 context

### V1: baseline surplus value

V1 created the initial team and player rank-gap framework.

For teams:

```text
surplus_rank_gap = cap_cost_rank - overall_performance_rank
```

For players:

```text
player_surplus_gap = cost_rank_within_position - production_rank_within_position
```

### V2: confidence workflow

V2 added data-quality and confidence flags to avoid over-interpreting missing contract data and low-sample rows.

Important fields:

- `has_contract_match`
- `has_missing_contract`
- `contract_confidence`
- `meets_sample_threshold`
- `sample_confidence`
- `overall_confidence`

High-confidence player rows require both a usable contract match and enough role/usage to support a ranking.

### V3: contract context

V3 added draft-capital and estimated contract-stage context.

Important fields:

- `draft_year`
- `draft_round`
- `draft_pick`
- `draft_capital_bucket`
- `years_since_drafted`
- `estimated_contract_stage`
- `is_likely_rookie_contract`
- `surplus_context`

This separates general cheapness from structurally underpriced production, especially rookie-contract and pre-extension players.

### V4: first-pass validation

V4 tested whether high-confidence rookie-contract surplus candidates outperformed high-confidence rookie-contract players the model did not flag.

Default V4 candidate definition:

```text
is_likely_rookie_contract == True
AND player_surplus_gap >= 5
```

V4's hit definition was intentionally broad:

```text
appeared in the following season
AND
(remained positive-surplus OR improved production score)
```

V4 was useful as a first validation layer, but the comparison group was still broad. V5 addresses that by adding matched rookie-contract controls.

## 5. V5 feature table

V5 starts from the cleaned player-season-position table and adds opportunity and availability context.

Regular-season and playoff snaps are separated. Regular-season opportunity is used in matching; playoff data is preserved as additional context.

Important regular-season fields include:

- `reg_snap_games`
- `reg_offense_snaps`
- `reg_avg_offense_snap_pct`
- `reg_max_offense_snap_pct`
- `reg_games_off_snap_50_plus`
- `reg_games_off_snap_70_plus`
- `played_regular_season`

Important playoff fields include:

- `playoff_snap_games`
- `playoff_offense_snaps`
- `playoff_avg_offense_snap_pct`
- `played_playoffs`

Important injury-report fields include:

- `injury_report_weeks`
- `out_weeks`
- `doubtful_weeks`
- `questionable_weeks`
- `practice_dnp_weeks`
- `limited_practice_weeks`
- `was_on_injury_report`
- `has_injury_source_for_season`
- `injury_merge_matched`

The injury fields improve auditability and future modeling options. The current V5 matched specification should not be described as fully injury-adjusted.

## 6. V5 candidate definition

Default V5 candidates:

```text
is_likely_rookie_contract == True
AND player_surplus_gap >= 5
```

Default V5 controls:

```text
is_likely_rookie_contract == True
AND player_surplus_gap < 5
```

The surplus gap is the signal being tested.

## 7. V5 outcome labels

V5 creates next-season labels by joining each candidate season to the following season.

### Primary outcome

```text
primary_v5_hit = next_year_top_half_position == 1
```

This means the player appeared in the next season and ranked in the top half of his position by next-season production percentile.

### Secondary outcome

```text
secondary_v5_hit = retained_positive_surplus == 1
```

This means the player appeared in the next season and retained a positive next-season value gap.

### Other main outcomes

- `appeared_next_year`
- `next_year_meaningful_regular_role`
- `retained_positive_surplus`
- `improved_production_score`
- `improved_production_percentile`
- `next_year_top_half_position`
- `next_year_top_third_position`

Meaningful role is defined as:

```text
next_year_reg_snap_games >= 8
AND next_year_reg_avg_offense_snap_pct >= 0.25
```

## 8. Matching design

V5 compares candidates to similar rookie-contract non-candidates.

Candidate pool:

```text
is_v5_default_candidate == 1
AND primary_v5_hit is not missing
```

Control pool:

```text
rookie_contract_bool == True
AND is_v5_default_candidate == 0
AND primary_v5_hit is not missing
```

Controls can be reused. The main specification uses K=3 controls per candidate when available.

### Exact-match tiers

The matcher tries exact tiers in this order:

1. Same season, position, draft-capital bucket, and estimated contract stage
2. Same season, position, and draft-capital bucket
3. Same season, position, and estimated contract stage
4. Same season and position

### Nearest-control distance

Within each exact tier, nearest controls are selected using weighted distance across:

| Match feature | Weight |
| --- | ---: |
| `match_production_pct` | 2.00 |
| `match_reg_avg_offense_snap_pct` | 1.25 |
| `match_reg_snap_games` | 1.00 |
| `match_reg_offense_snaps_pctile` | 1.00 |
| `match_years_since_drafted` | 0.75 |

The model intentionally does **not** match on `player_surplus_gap`, because that is the signal being tested.

## 9. Lift calculation

For each matched candidate, the model compares the candidate outcome to the average outcome of his matched controls.

```text
candidate_lift = candidate_outcome - matched_control_outcome_mean
```

The summary lift is the average candidate-level lift across matched candidates.

The script also reports standard errors and approximate 95 percent confidence intervals using the distribution of candidate-level differences.

## 10. Main V5 results

Default K=3 matched-control results:

| Outcome | Matched candidates | Candidate rate | Matched-control rate | Lift | Approx. 95% CI |
| --- | ---: | ---: | ---: | ---: | ---: |
| Top-half next-season production | 252 | 56.3% | 42.1% | +14.3 pp | +7.5 pp to +21.1 pp |
| Retained positive surplus | 252 | 56.3% | 32.0% | +24.3 pp | +17.3 pp to +31.3 pp |
| Meaningful regular-season role | 252 | 82.5% | 65.6% | +16.9 pp | +11.5 pp to +22.3 pp |
| Appeared the next year | 252 | 85.3% | 65.6% | +19.7 pp | +14.6 pp to +24.8 pp |

Interpretation:

- V5 candidates were more likely than matched peers to appear the following season.
- V5 candidates were more likely to maintain a meaningful regular-season role.
- V5 candidates were more likely to retain positive surplus.
- V5 candidates were more likely to rank in the top half of their position the next season.

Important nuance:

- `improved_production_score` lift was -10.1 pp.
- `improved_production_percentile` lift was -12.2 pp.

That means V5 is strongest as a persistence and role-retention screen, not as evidence that candidates generally improve from their current production level.

## 11. K-sensitivity

V5 repeats the matched validation for K=1, K=3, and K=5 matched controls.

| K | Matched candidates | Candidate rate | Matched-control rate | Primary lift | Approx. 95% CI |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 252 | 56.3% | 46.0% | +10.3 pp | +2.1 pp to +18.5 pp |
| 3 | 252 | 56.3% | 42.1% | +14.3 pp | +7.5 pp to +21.1 pp |
| 5 | 252 | 56.3% | 36.1% | +20.3 pp | +13.6 pp to +27.0 pp |

The safe interpretation is that the primary lift stayed positive under all tested K values. The magnitude should not be treated as a law.

## 12. How to explain the prediction

The model does not produce a signing recommendation or guaranteed breakout label.

A team-facing explanation should sound like this:

> This player belongs in the review queue because he fits a historically persistent public-data profile: likely rookie-contract timeline, production ahead of public cost rank, and comparable matched peers who were less likely to maintain the same next-season relevance.

The next step should always include:

- film review
- medical/availability review
- role and scheme fit
- quarterback and offensive line context
- depth-chart path
- age and development context
- internal cap/cash accounting
- club-specific grades and character information

## 13. EPA limitations and impact on findings

EPA is useful because it values plays in context. A 6-yard gain on third-and-5 is not the same as a 6-yard gain on third-and-15.

However, EPA is limited for individual valuation.

### Main limitations

- EPA can blend player ability with scheme, play-calling, quarterback quality, offensive line quality, and teammate quality.
- Receiver EPA depends on target quality, route role, and quarterback decision-making.
- Running back production depends on blocking, box count, game script, and short-yardage role.
- Quarterback and receiver credit can be difficult to separate with public data.
- EPA can be affected by turnovers, garbage time, end-of-half situations, and small samples.
- Public player EPA does not fully account for assignment, route depth, defensive attention, or play design.
- Opportunity controls help but do not fully model injuries, player development, or depth-chart changes.

### How those limitations affect interpretation

The model may identify:

- genuinely underpriced player ability
- a player benefiting from a favorable offensive environment
- a player with a role that is valuable in EPA terms
- a player whose public cost has not yet updated to his current role
- a player whose production is more fragile than the surface signal suggests

That is why the output should be treated as a review prompt, not an answer.

## 14. What the model supports

Supported claims:

- This player produced more than his public cost rank suggested.
- This profile showed positive next-season lift against matched rookie-contract peers.
- The V5 candidate pool is worth deeper review.
- The 2025 candidate pool can be evaluated when 2026 outcomes are available.

Unsupported claims:

- This proves the player is objectively underpaid.
- This proves causality.
- This guarantees a breakout.
- This replaces scouting, medical, scheme, or internal cap information.
- The matched controls remove all bias.

## 15. Public-facing column labels

The app and website should avoid raw variable names when possible.

| Raw column | Public label |
| --- | --- |
| `player_surplus_gap` | Value Gap |
| `production_rank_position` | Production Rank Within Position |
| `cost_rank_position` | Cost Rank Within Position |
| `cap_number` | Public Cap Cost ($M) |
| `cash_paid` | Cash Paid ($M) |
| `candidate_rate` | Candidate Rate |
| `matched_control_rate` | Matched-Control Rate |
| `lift_pp` | Lift (Percentage Points) |
| `k_matches` | Matched Controls |
| `overall_confidence` | Confidence |

## 16. Current limitations

- Public contract data may be incomplete.
- Public cap number is not official team cap accounting.
- Contract stage is estimated.
- Draft matching depends on public IDs.
- The player model covers only QB, RB, WR, and TE.
- Production weights are hand-built.
- Rank gaps are coarse.
- V5 is observational, not causal.
- Controls can be reused.
- Snap opportunity controls do not fully model scheme, teammate quality, opponent strength, or development curve.
- Injury fields are included, but the main model is not fully injury-adjusted.

## 17. Future improvements

- learned production weights
- non-reused matched controls
- richer matching diagnostics
- stronger injury/availability adjustment
- age curves by position
- defensive and offensive-line value proxies
- free-agent target workflow
- player report cards with film prompts
- comparison with playoff/team success