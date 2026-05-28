# NFL Moneyball: Finding Roster Surplus Value Under the Salary Cap

## Project Overview

This project builds a public-data NFL roster value model inspired by *Moneyball*.

The goal is to evaluate which NFL teams and offensive skill-position players generate the most production relative to contract cost, then use the Philadelphia Eagles as the main case study in sustainable roster construction.

The core question is not simply:

> Who is good?

It is:

> Which teams and players create more value than their cost suggests?

The project evaluates all 32 NFL teams from the 2021–2025 NFL seasons, with a deeper focus on:

* Philadelphia Eagles — main case study
* New York Giants — division/rebuild comparison
* Cleveland Browns — cap-efficiency comparison
* Baltimore Ravens — contender benchmark
* Detroit Lions — young-core benchmark

## Project Status

This is an ongoing portfolio project.

The current version includes:

* team-level surplus value model
* player-level offensive skill-position value model
* V2 confidence and data-quality flags
* V3 draft-capital and contract-cycle context
* V4 backtesting and latest-season candidate review
* market-inefficiency analysis by position, cost tier, draft capital, and contract stage
* interactive Streamlit dashboard

The project has moved from descriptive rankings toward early decision support.

V3 adds contract-cycle context to distinguish general cheapness from structurally underpriced production.

V4 adds a first-pass backtest to test whether model-flagged rookie-contract surplus candidates outperform similar rookie-contract players the model did not flag.

Important caveat: V4 is not a finished prediction model. It is a first validation layer for testing whether the surplus-value signal has next-season persistence.

## Live Dashboard

Live dashboard: [View the Streamlit app](https://nfl-moneyball-roster-value.streamlit.app/)

To run locally:

```bash
streamlit run app.py
```

Example dashboard views:

![Methodology and Filters Dashboard](outputs/figures/dashboard1.png)
![Team Level Surplus Value Dashboard](outputs/figures/dashboard2.png)
![Focus Team Trend + Eagles Team Detail Dashboard](outputs/figures/dashboard3.png)
![Player-Level Skill Position Value Dashboard](outputs_v2/figures/updated_dashboard4.png)
![Moneyball Insight Dashboard](outputs/figures/dashboard5.png)

## Moneyball Thesis

The central idea is that roster value is not about being cheap for its own sake.

It is about identifying production before the market fully prices it as proven production.

In this NFL version of *Moneyball*, the potential inefficiency is:

> The market pays heavily for already-proven production, but surplus value comes from identifying production one contract cycle earlier.

For the Eagles, the early finding is:

> The Eagles’ roster-building edge is not that every star is cheap. It is that they combine expensive stars with enough surplus-value contributors to keep the overall roster efficient.

## Data Sources

This project uses public NFL data through `nflreadpy`, including:

* play-by-play data
* player statistics
* team statistics
* roster data
* contract data
* draft data

The model covers the 2021, 2022, 2023, 2024, and 2025 NFL seasons.

Contract cost is treated as a public-data proxy, not audited official salary-cap accounting.

## Season Labeling

This project uses NFL season-year labels, not calendar-year labels.

For example, the 2025 season refers to the 2025 NFL season, even though that season concludes in early 2026.

The descriptive model covers 2021–2025.

V4 backtesting uses 2021–2024 as candidate seasons because each candidate season requires a following-season outcome:

* 2021 candidates are evaluated using 2022 outcomes
* 2022 candidates are evaluated using 2023 outcomes
* 2023 candidates are evaluated using 2024 outcomes
* 2024 candidates are evaluated using 2025 outcomes

The 2025 season is treated as the latest-season watchlist because 2026 outcomes are not available yet.

## Methodology Summary

### Team Surplus Value

Team surplus value compares team performance rank against team contract-cost rank.

```text
surplus_rank_gap = cap_cost_rank - overall_performance_rank
```

A positive surplus rank gap means a team performed better than its cost rank.

Example:

```text
cap_cost_rank = 25
overall_performance_rank = 5
surplus_rank_gap = 20
```

This would indicate strong surplus value because the team performed like a top-five team while ranking much lower in contract cost.

### Player Surplus Value

The player model focuses on offensive skill-position players:

* QB
* RB
* WR
* TE

Players are ranked within position by production and by contract cost.

```text
player_surplus_gap = cost_rank_position - production_rank_position
```

A positive player surplus gap means the player produced better than his cost rank.

A negative player surplus gap means the player was expensive relative to his production rank.

The base player model is built at the player-team-season level. If a player appears for multiple teams in one season, each team stint may appear separately in the descriptive player-value outputs.

For V4 backtesting, the model creates a cleaned player-season-position table. This collapses duplicate player-season-position rows before recomputing production rank, cost rank, and surplus gap.

## Version History

### V1: Baseline Surplus Value

The first version created the core team and player surplus-value framework.

It compared performance or production rank against contract-cost rank.

### V2: Confidence and Data Quality

V2 added data-quality and confidence flags to make the player model more defensible.

The updated workflow:

* keeps missing public contract values as missing
* flags whether a player matched to a contract record
* separates low-sample players from final ranked tables
* preserves diagnostic files for auditability
* adds confidence labels to player outputs and the dashboard

This prevents missing public contract data from being treated as meaningful zero-dollar cost.

### V3: Draft Capital and Contract-Cycle Context

V3 adds draft and contract-stage context, including:

* draft year
* draft round
* draft pick
* draft-capital bucket
* years since drafted
* estimated contract stage
* likely rookie-contract status
* surplus context

This helps separate cheap production from structurally underpriced production.

A productive rookie-contract player is not just cheap. He is cheap because the market has not fully repriced his production yet.

### V4: Backtesting and Candidate Review

V4 tests whether the player surplus signal has next-season value.

The main backtest compares:

* model candidates: high-confidence rookie-contract players with `player_surplus_gap >= 5`
* not-flagged baseline: high-confidence rookie-contract players with `player_surplus_gap < 5`

The first-pass hit definition is:

```text
appeared in the next season
AND
(remained positive-surplus OR improved production score)
```

This hit definition is intentionally broad. It should be interpreted as first-pass evidence of next-season persistence, not as a finished predictive target.

V4 also includes:

* threshold sensitivity testing
* season stability testing
* true-positive review
* model-miss review
* missed-opportunity review
* 2025 latest-season watchlist

The 2025 watchlist is not a backtest result because 2026 outcomes are not available yet.

## Key Findings

### 1. The Eagles stand out as a team-level surplus-value case

From 2021–2025, the Eagles show strong average roster surplus value among the focus teams.

This supports using Philadelphia as the main case study.

### 2. The Eagles’ edge is portfolio construction, not just cheap stars

The player-level model shows that not every Eagles star grades as a surplus bargain.

Expensive stars can still be excellent players while grading lower in surplus-value terms because they cost more.

The takeaway is not:

> The Eagles only win because their stars are cheap.

The better takeaway is:

> The Eagles can afford expensive stars because they generate enough surplus value elsewhere.

### 3. Surplus value changes across the contract cycle

At quarterback, Philadelphia’s surplus value was highest when Jalen Hurts was inexpensive.

The Eagles’ QB surplus gap was +33.0 in 2022, then narrowed to +3.0 in 2025 as the average cap number for the position increased.

This does not mean Hurts stopped being valuable. It means the cost hurdle became much higher once his contract reflected his proven production.

A similar pattern appears at wide receiver. The Eagles’ WR group produced strong average surplus value in 2022 and 2023, then remained positive but less extreme as average cost increased.

This supports the project’s central thesis:

> Surplus value is largest before the market fully prices the production.

### 4. Low-cost skill players are the clearest surplus-value archetype in the valid-cost universe

The market-inefficiency analysis shows a consistent pattern across offensive skill positions: low-cost players generate positive average surplus value, while mid/high/premium-cost players often generate negative surplus value relative to their cost rank.

This finding uses the valid-cost, high-confidence V3 market universe.

Missing, unmatched, and non-positive public contract-cost rows are excluded from public-facing cost-tier conclusions. Those rows are preserved in an audit file but are not treated as a real low-cost player signal.

The clearest example is wide receiver. From 2021–2025, low-cost wide receivers produced positive average surplus value, while high-cost and premium-cost wide receivers faced a much steeper value hurdle.

This does not mean expensive wide receivers are bad players. It means the cost hurdle is much higher. Once a player is paid like a proven star, he has to produce at an elite level just to remain a surplus-value asset.

### 5. V4 backtesting suggests the surplus signal has next-season value

The V4 backtest tests whether high-confidence rookie-contract surplus candidates outperform similar rookie-contract players the model did not flag.

At the default surplus threshold of:

```text
player_surplus_gap >= 5
```

model candidates outperformed not-flagged rookie-contract players across the full 2021–2024 candidate window.

Across all offensive skill positions:

* model candidates had a 57.9% next-season hit rate
* not-flagged rookie-contract players had a 47.6% next-season hit rate
* hit-rate lift was +10.3 percentage points
* next-season surplus-gap lift was +10.38

Threshold sensitivity showed that the model signal stayed positive across all tested surplus thresholds from 0 to 20.

The signal was strongest and most stable among wide receivers, while RB/TE/QB results were more sample-sensitive.

This does not mean the model predicts breakout players. It means the surplus profile is worth further development because it showed positive lift against a reasonable rookie-contract baseline.

## Key Outputs

### Team-Level Outputs

```text
outputs/team_value_2021_2025.csv
outputs/team_cost_2021_2025.csv
outputs/team_surplus_2021_2025.csv
outputs/focus_team_surplus_2021_2025.csv
```

### V2 Confidence Outputs

```text
outputs_v2/player_value_2021_2025_v2_confidence.csv
outputs_v2/focus_player_value_2021_2025_v2_confidence.csv
outputs_v2/player_value_diagnostics_2021_2025_v2_confidence.csv
```

### V3 Contract-Context Outputs

```text
outputs_v3/player_value_2021_2025_v3_contract_context.csv
outputs_v3/focus_player_value_2021_2025_v3_contract_context.csv
outputs_v3/summary/pre_extension_candidates_2025.csv
```

### V4 Backtest and Candidate Review Outputs

```text
outputs_v4/player_value_2021_2025_player_season_clean.csv
outputs_v4/backtests/backtest_lift_model_vs_not_flagged_clean.csv
outputs_v4/backtests/backtest_summary_clean.csv
outputs_v4/backtests/threshold_sensitivity_lift.csv
outputs_v4/backtests/threshold_sensitivity_summary.csv
outputs_v4/backtests/season_stability_lift_by_season.csv
outputs_v4/backtests/season_stability_lift_by_season_position.csv
outputs_v4/backtests/candidate_review_top_true_positives.csv
outputs_v4/backtests/candidate_review_model_misses.csv
outputs_v4/backtests/candidate_review_missed_opportunities.csv
outputs_v4/backtests/candidate_review_2025_watchlist.csv
outputs_v4/backtests/candidate_review_performance_lift_reference.csv
```

Candidate-review bucket files are useful for qualitative inspection, but they should not be interpreted as model-performance tables because the buckets are outcome-defined.

### Market Inefficiency Outputs

```text
outputs_v3/summary/market_inefficiency_position_summary_v3.csv
outputs_v3/summary/market_inefficiency_cost_tier_summary_v3.csv
outputs_v3/summary/market_inefficiency_contract_stage_summary_v3.csv
outputs_v3/summary/market_inefficiency_position_contract_stage_summary_v3.csv
outputs_v3/summary/market_inefficiency_draft_capital_summary_v3.csv
outputs_v3/summary/market_inefficiency_position_draft_capital_summary_v3.csv
outputs_v3/summary/market_inefficiency_surplus_context_summary_v3.csv
outputs_v3/summary/market_inefficiency_top_bargains_by_position_v3.csv
outputs_v3/summary/market_inefficiency_2025_watchlist_v3.csv
outputs_v3/summary/market_inefficiency_v4_position_validation_context.csv
outputs_v3/summary/market_inefficiency_takeaways_v3.csv
outputs_v3/summary/market_inefficiency_excluded_rows_v3.csv
```

## How to Run the Project

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the main workflow:

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
streamlit run app.py
```

The dashboard uses V3 player outputs for player-level sections. If V4 output files are available, the dashboard also shows default backtest results, threshold sensitivity, season stability, and the 2025 latest-season watchlist.

## Project Files

Core pipeline files:

```text
performance.py
cost.py
surplus_value.py
player_value_v2_confidence.py
player_value_v3_contract_context.py
player_value_v4_backtest_clean.py
player_value_v4_threshold_sensitivity.py
player_value_v4_season_stability.py
player_value_v4_candidate_review.py
market_inefficiency.py
visuals_v4_backtest.py
app.py
```

Supporting and earlier-version files:

```text
player_data_audit.py
player_value.py
player_visuals.py
visuals.py
visuals_v2_confidence.py
insight_summary.py
insight_summary_v2_confidence.py
```

For deeper methodology details, see:

```text
methodology_notes.md
```

## Limitations

This model is a public-data approximation and should be interpreted as a decision-support project, not a perfect front-office valuation system.

Key limitations:

* Public contract data is an approximation, not official audited salary-cap accounting.
* Missing contract data can reduce confidence in some player rankings.
* The player model currently covers only QB, RB, WR, and TE.
* Defensive players and offensive linemen are not yet modeled.
* Production-score weights are hand-built rather than statistically learned.
* Rank gaps are intuitive but coarse and do not show the magnitude between players.
* Rookie-contract status and draft capital are estimated using public draft data.
* Contract stage is estimated, not a full cap-accounting model.
* The model does not yet adjust for injuries, snap counts, scheme, teammates, coaching context, or strength of schedule.
* V4 backtesting shows first-pass persistence, not causal proof or a finished prediction model.

## Future Improvements

Future versions could add:

* defensive player surplus value
* offensive line value proxies
* snap-count and opportunity adjustments
* injury-adjusted value
* age curves by position
* more precise rookie-contract and extension-status modeling
* stronger draft-value and draft-capital modeling
* matched baselines by position, draft capital, and production tier
* free-agent target recommendations
* draft-prospect analysis
* comparison between surplus value and playoff success

## Final Takeaway

NFL roster efficiency is not about being cheap.

It is about knowing when to pay for premium talent and when to search for underpriced production.

The strongest market-efficiency pattern in the model is that low-cost offensive skill players, especially wide receivers, running backs, and tight ends, generate positive surplus value on average in the valid-cost player universe, while mid/high/premium-cost players face a much steeper value hurdle.

For the Eagles, the early evidence suggests:

> Philadelphia’s advantage comes from portfolio construction: combining premium stars with enough low-cost surplus contributors to keep the full roster efficient.

The Billy Beane-style insight is not:

> Avoid expensive players.

It is:

> Find production before the market prices it as proven production.

In NFL roster-building terms, the edge comes from identifying value one contract cycle early while being honest about the limits of public data.
