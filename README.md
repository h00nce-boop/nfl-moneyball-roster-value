# NFL Moneyball: Roster Value Decision Support

**Interactive Portfolio Website:** https://nfl-moneyball.vercel.app  
**Live Streamlit Dashboard:** https://nfl-moneyball-roster-value.streamlit.app  
**Source Code:** https://github.com/h00nce-boop/nfl-moneyball-roster-value

## One-sentence summary

This project is a public-data decision-support tool for identifying offensive skill-position players who produced more than their public contract-cost profile suggested, then testing whether that surplus profile persisted the following season.

## What changed in V5

The project has moved from a descriptive portfolio project toward a more practical review workflow for a team analyst or football-operations staffer.

V5 adds:

- a clearer value definition
- a cleaned player-season validation table
- regular-season opportunity controls
- snap-count and injury-report context for auditability
- matched rookie-contract controls
- K-sensitivity testing across 1, 3, and 5 matched controls
- a 2026 evaluation candidate pool based on the 2025 season
- a simplified Streamlit dashboard organized around practical football questions

The strongest V5 claim is **persistence**, not guaranteed breakout prediction. V5 asks whether rookie-contract surplus players were more likely than matched peers to remain relevant, keep positive surplus, and produce in the top half of their position the following season.

## Who this is for

The dashboard is meant to behave like a public-data screening board. A team user should be able to answer:

1. What is the value signal?
2. Which players should I review?
3. What is the team context?
4. Did the signal validate historically?
5. What are the limits of the signal?

It should not be interpreted as a replacement for scouting, medical information, scheme evaluation, internal cap accounting, or club-specific player grades.

## Core question

The model does not start with:

> Who is good?

It starts with:

> Who produced more than his public contract-cost rank would imply, and did that profile persist historically?

## Data sources

This project uses public NFL data through [`nflreadpy`](https://nflreadpy.nflverse.com/), including:

- player statistics, including public `passing_epa`, `rushing_epa`, and `receiving_epa` fields
- play-by-play-derived EPA context
- team statistics
- roster data
- public contract data
- draft data
- snap-count data
- injury-report data

EPA is not privately sourced from a club or league-office system; it comes from the public NFL data ecosystem loaded through `nflreadpy`.

The model covers the 2021, 2022, 2023, 2024, and 2025 NFL seasons.

Contract cost is treated as a **public-data proxy**, not audited official salary-cap accounting.

## How value is measured

### Production

Player production is an EPA-based public-data production score. It uses `total_epa` as the anchor and adds lightweight traditional production terms so that yards, touchdowns, interceptions, sacks, receptions, and receiving/rushing volume are still represented.

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

The goal is not to claim this is a perfect player grade. The goal is to create a transparent public-data production proxy that is good enough to support a first-pass roster-value screen.

### Cost

The cost side uses public contract data, primarily public cap number. Missing public contract matches are not treated as true zero-dollar cost. They are flagged and excluded from high-confidence public-facing rankings.

### Player surplus gap

Players are ranked within season and position by production and by public cost.

```text
player_surplus_gap = cost_rank_within_position - production_rank_within_position
```

A positive gap means production ranked better than cost. For example:

```text
production rank within WR = 12
public cost rank within WR = 31
player surplus gap = 31 - 12 = +19
```

That does **not** prove the player is objectively underpaid. It means the player produced ahead of his public cost rank and should be reviewed in context.

Rank direction matters:

- `production_rank_position`: lower is better. Rank 1 is the highest production score within that season and position.
- `cost_rank_position`: lower is more expensive. Rank 1 is the highest public cap number within that season and position.
- `player_surplus_gap`: higher is better for this screen. A positive gap means the player produced ahead of his public cost rank.

## V5 candidate definition

The default V5 candidate is:

```text
is_likely_rookie_contract == True
AND player_surplus_gap >= 5
```

The default control pool is:

```text
rookie-contract player
AND player_surplus_gap < 5
```

The 2025 candidate pool is saved as a 2026 evaluation/watchlist file because 2026 outcomes are not available yet.

## V5 matched validation

V5 compares candidates with similar rookie-contract non-candidates. The main K=3 run matched **252 historical V5 candidates** from the 2021-2024 candidate seasons.

Matching uses exact tiers in this order:

1. Same season, position, draft-capital bucket, and contract stage
2. Same season, position, and draft-capital bucket
3. Same season, position, and contract stage
4. Same season and position

Within an exact tier, controls are selected by nearest weighted distance across:

| Match feature | Weight |
| --- | ---: |
| production percentile within season-position | 2.00 |
| regular-season average offensive snap share | 1.25 |
| regular-season snap games | 1.00 |
| regular-season offensive-snap percentile | 1.00 |
| years since drafted | 0.75 |

The model intentionally does **not** match on `player_surplus_gap`, because that is the signal being tested.

## Main V5 results

Default K=3 matched-control results:

| Outcome | Matched candidates | Candidate rate | Matched-control rate | Lift | Approx. 95% CI |
| --- | ---: | ---: | ---: | ---: | ---: |
| Top-half next-season production | 252 | 56.3% | 42.1% | +14.3 pp | +7.5 pp to +21.1 pp |
| Retained positive surplus | 252 | 56.3% | 32.0% | +24.3 pp | +17.3 pp to +31.3 pp |
| Meaningful regular-season role | 252 | 82.5% | 65.6% | +16.9 pp | +11.5 pp to +22.3 pp |
| Appeared the next year | 252 | 85.3% | 65.6% | +19.7 pp | +14.6 pp to +24.8 pp |

The most important interpretation is that the V5 surplus profile showed positive next-season lift for persistence-oriented outcomes.

A nuance worth stating clearly: improvement outcomes were negative in the K=3 run:

- improved production score lift: -10.1 pp
- improved production percentile lift: -12.2 pp

That means V5 should be framed as a **surplus-persistence and role-retention signal**, not as proof that candidates are more likely to improve raw production from the current season.

## K-sensitivity

The primary lift remained positive across all three tested matched-control counts.

| Matched controls per candidate | Matched candidates | Candidate rate | Matched-control rate | Primary lift | Approx. 95% CI |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 252 | 56.3% | 46.0% | +10.3 pp | +2.1 pp to +18.5 pp |
| 3 | 252 | 56.3% | 42.1% | +14.3 pp | +7.5 pp to +21.1 pp |
| 5 | 252 | 56.3% | 36.1% | +20.3 pp | +13.6 pp to +27.0 pp |

This sensitivity check supports the claim that the primary result is not dependent on one arbitrary K value. The increase from K=1 to K=5 should not be over-interpreted as a law; it may reflect the available control pool and control averaging.

## What I would tell a team

This model should be used as a review queue, not a signing recommendation.

A practical interpretation would be:

> Here are offensive skill players whose production outran their public cost profile. Historically, similar V5 candidates were more likely than matched rookie-contract peers to appear the next season, retain positive surplus, maintain a meaningful role, and finish in the top half of their position by next-season production. These players deserve deeper film, medical, scheme, depth-chart, and cap review.

The best use case is narrowing the first-pass board before a human analyst or scout applies team-specific context.

## EPA limitations

EPA is useful because it incorporates down, distance, field position, and game context. But it has limitations when used for player valuation:

- EPA can blend player quality with quarterback environment, offensive line play, play-calling, scheme, and teammate quality.
- Receiving production depends heavily on target quality and route role.
- Running back EPA can be shaped by offensive line and box count context that is not fully modeled here.
- Quarterback and receiver credit can be hard to separate with public data.
- EPA can be sensitive to role, garbage time, turnovers, and small samples.
- Snap opportunity helps but does not fully adjust for injuries, development curve, or depth-chart constraints.
- Public cap number is not the same as a team's internal cap valuation or cash-flow view.

Because of those limitations, the model should be described as a screen for reviewable surplus profiles, not a complete player valuation model.

## Season labeling

This project uses NFL season-year labels, not calendar-year labels.

For example, the 2025 season refers to the 2025 NFL season, even though that season concludes in early 2026.

The descriptive model covers 2021-2025.

V4 and V5 validation use 2021-2024 as candidate seasons because each candidate season requires a following-season outcome:

- 2021 candidates are evaluated using 2022 outcomes
- 2022 candidates are evaluated using 2023 outcomes
- 2023 candidates are evaluated using 2024 outcomes
- 2024 candidates are evaluated using 2025 outcomes

The 2025 season is treated as the latest candidate pool because 2026 outcomes are not available yet.

## Dashboard workflow

The Streamlit app is organized around five pages:

1. **Start Here** - define the signal and show the headline V5 validation.
2. **Find Players** - filter all model players or the V5 surplus shortlist.
3. **Check Team Context** - review team-level surplus-value context.
4. **Validate the Signal** - inspect V5 matched validation and K-sensitivity.
5. **Methodology and Limits** - explain formulas, EPA limitations, and safe interpretation.

Public-facing column labels are intentionally readable. For example:

| Raw column | Public label |
| --- | --- |
| `player_surplus_gap` | Value Gap |
| `production_rank_position` | Production Rank Within Position |
| `cost_rank_position` | Public Cost Rank Within Position |
| `cap_number` | Public Cap Cost ($M) |
| `candidate_rate` | Candidate Rate |
| `matched_control_rate` | Matched-Control Rate |
| `lift_pp` | Lift (Percentage Points) |

## Key outputs

### Team-level outputs

```text
outputs/team_value_2021_2025.csv
outputs/team_cost_2021_2025.csv
outputs/team_surplus_2021_2025.csv
outputs/focus_team_surplus_2021_2025.csv
```

### V3 contract-context outputs

```text
outputs_v3/player_value_2021_2025_v3_contract_context.csv
outputs_v3/focus_player_value_2021_2025_v3_contract_context.csv
outputs_v3/summary/pre_extension_candidates_2025.csv
```

### V4 backtest and candidate-review outputs

```text
outputs_v4/player_value_2021_2025_player_season_clean.csv
outputs_v4/backtests/backtest_lift_model_vs_not_flagged_clean.csv
outputs_v4/backtests/threshold_sensitivity_lift.csv
outputs_v4/backtests/season_stability_lift_by_season.csv
outputs_v4/backtests/candidate_review_2025_watchlist.csv
```

### V5 matched-validation outputs

```text
outputs_v5/features/player_season_features_v5.csv
outputs_v5/outcomes/player_season_outcomes_v5.csv
outputs_v5/outcomes/historical_validation_rows_v5.csv
outputs_v5/watchlists/2026_candidate_pool_v5.csv

outputs_v5/backtests/k1/k1_matched_lift_summary_v5.csv
outputs_v5/backtests/k3/k3_matched_lift_summary_v5.csv
outputs_v5/backtests/k5/k5_matched_lift_summary_v5.csv
outputs_v5/backtests/sensitivity_k_summary_v5.csv
outputs_v5/backtests/sensitivity_k_summary_main_outcomes_v5.csv

outputs_v5/figures/v5_matched_lift_by_outcome.png
outputs_v5/figures/v5_primary_lift_sensitivity_k.png
outputs_v5/figures/v5_primary_lift_by_position.png
outputs_v5/figures/v5_primary_lift_by_season.png
```

The K label is intentionally repeated in both the folder name and filename, for example `k3/k3_matched_lift_summary_v5.csv`. The folder organizes each sensitivity run, while the filename remains self-describing if exported or compared outside the repository.

## How to run locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the core workflow:

```bash
python performance.py
python cost.py
python surplus_value.py
python player_value_v2_confidence.py
python player_value_v3_contract_context.py
python player_value_v4_backtest_clean.py
python player_value_v4_threshold_sensitivity.py
python player_value_v4_season_stability.py
python player_value_v4_candidate_review.py
python market_inefficiency.py
python visuals_v4_backtest.py
python player_value_v5_feature_table.py
python player_value_v5_outcomes.py
K_MATCHES=1 python player_value_v5_matched_backtest.py
K_MATCHES=3 python player_value_v5_matched_backtest.py
K_MATCHES=5 python player_value_v5_matched_backtest.py
python sensitivity_k_summary_v5.py
python visuals_v5_validation.py
streamlit run app.py
```

## Limitations

This is a public-data approximation and should be interpreted as decision support, not a full front-office valuation system.

Important limitations:

- Public contract data is approximate and can be incomplete.
- Contract stage and rookie-contract status are estimated from public draft data.
- The model currently covers only QB, RB, WR, and TE.
- Defense and offensive line are not yet modeled.
- Production-score weights are hand-built, not statistically learned.
- Rank gaps are intuitive but coarse and do not measure the magnitude between adjacent players.
- V5 improves comparability with matched controls, but it is still observational.
- Controls can be reused.
- The model does not fully adjust for scheme, coaching, teammate quality, opponent strength, medical history, or internal club valuation.

## Future improvements

Future versions could add:

- learned production-score weights
- non-reused matched controls
- stronger injury and availability adjustment
- age curves by position
- defensive player surplus value
- offensive line value proxies
- free-agent target recommendations
- draft-prospect analysis
- player-level report cards with film-review prompts

## Final takeaway

The Billy Beane-style insight is not:

> Avoid expensive players.

It is:

> Find production before the market prices it as proven production.

In NFL roster-building terms, the edge comes from identifying value one contract cycle early while being honest about the limits of public data.

## Rights and usage

This project is source-available for portfolio review only. All code, analysis, documentation, and original visualizations are copyright (c) 2026 Hannah Levy. All rights reserved.

Please do not copy, redistribute, modify, or use this work without written permission.