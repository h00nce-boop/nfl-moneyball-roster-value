# NFL Moneyball: Finding Roster Surplus Value Under the Salary Cap

## Project Overview

This project builds a public-data NFL roster value model inspired by *Moneyball*. The goal is to identify which teams and players generate the most production relative to contract cost, then use the Philadelphia Eagles as a case study in sustainable roster construction.

The main idea is not simply to ask, “Who is good?” The project asks a more front-office-style question:

> Which teams and players create more value than their cost suggests?

The project evaluates all 32 NFL teams from 2021–2025, then focuses more closely on five teams:

- Philadelphia Eagles — main case study
- New York Giants — division/rebuild comparison
- Cleveland Browns — cap-efficiency comparison
- Baltimore Ravens — contender benchmark
- Detroit Lions — young-core benchmark

## Project Status

This is an ongoing portfolio project. The current version includes:

- a team-level surplus value model
- a player-level offensive skill-position value model
- V2 confidence and data-quality flags
- V3 draft-capital and contract-cycle context
- V4 backtesting and latest-season candidate review
- an interactive Streamlit dashboard
- updated market-inefficiency analysis using confidence, draft-capital, contract-stage, and V4 validation context

The newest V4 layer moves the project from descriptive rankings toward decision support by testing whether model-flagged rookie-contract surplus candidates outperform similar rookie-contract players the model did not flag.

Future iterations will expand the model to include defensive players, offensive linemen, injury adjustments, opportunity-adjusted production, age curves, and draft-prospect analysis.

## Core Question

Can we identify roster-building inefficiencies using public NFL data?

More specifically:

- Which teams outperform their contract-cost profile?
- Which skill players generate the most surplus value?
- What player archetypes appear undervalued?
- How do the Eagles compare with the Giants, Browns, Ravens, and Lions?
- Can public data reveal a repeatable roster-building edge?

## Moneyball Thesis

The “Moneyball” idea in this project is that NFL teams should not only chase raw talent or name recognition. They should look for production before it becomes expensive.

In baseball, the Oakland A’s found value in traits the market underpriced. In this NFL version, the potential inefficiency is:

> The market pays heavily for already-proven production, but surplus value comes from identifying production one contract cycle earlier.

For the Eagles, the early finding is:

> The Eagles’ roster-building edge is not that every star is cheap. It is that they combine expensive stars with enough surplus-value contributors to keep the overall roster efficient.

## Dashboard Preview
Live dashboard: [View the Streamlit app](https://nfl-moneyball-roster-value.streamlit.app/)

This project includes a Streamlit dashboard for exploring team-level and player-level surplus value.

To run it locally:

```bash
streamlit run app.py
```
Example dashboard views:

![Methodology and Filters Dashboard](outputs/figures/dashboard1.png)
![Team Level Surplus Value Dashboard](outputs/figures/dashboard2.png)
![Focus Team Trend + Eagles Team Detail Dashboard](outputs/figures/dashboard3.png)
![Player-Level Skill Position Value Dashboard](outputs_v2/figures/updated_dashboard4.png)
![Moneyball Insight Dashboard](outputs/figures/dashboard5.png)


## Data Sources

This project uses public NFL data through `nflreadpy`, including:

- play-by-play data
- player statistics
- team statistics
- roster data
- contract data
- draft data
- snap count data for future expansion

The project uses data from the 2021, 2022, 2023, 2024, and 2025 NFL seasons.

## Why 2021–2025?

The model uses a five-season window to balance sample size and relevance.

A one-season sample can be too noisy because injuries, schedule strength, and small-sample performance can distort results. A much longer window can become less relevant because NFL rosters turn over quickly, coaching staffs change, and rookie contracts expire.

A 2021–2025 NFL-season window gives enough data to observe roster-building trends while staying close to the current NFL environment.

### Season labeling note

This project uses NFL season-year labels, not calendar-year labels. A season is labeled by the year in which the NFL season begins. For example, the 2025 season refers to the 2025 NFL season, even though that season concludes in early 2026.

The model covers the 2021–2025 NFL seasons. V4 backtesting uses 2021–2024 as candidate seasons because each candidate season requires a following-season outcome:

- 2021 candidates are evaluated using 2022 outcomes
- 2022 candidates are evaluated using 2023 outcomes
- 2023 candidates are evaluated using 2024 outcomes
- 2024 candidates are evaluated using 2025 outcomes

The 2025 season is treated as the latest-season watchlist because 2026 outcomes are not available yet.

## Methodology

### Team Performance

Team performance is measured using offensive and defensive EPA per play.

For each team-season, the model calculates:

- offensive EPA per play
- offensive success rate
- defensive EPA allowed per play
- offense rank
- defense rank
- overall performance rank

Lower overall rank means better performance.

### Contract Cost

Contract cost is measured using a cleaned public contract-cost proxy built from yearly contract data.

The raw contract data includes nested year-by-year contract rows, so the project flattens the contract data into one row per player-contract-season. The model then removes duplicate player-team-season rows before aggregating team cost.

The main cost fields are:

- cap number
- cash paid
- base salary
- guaranteed salary

Because this is public contract data, the model treats cost as a proxy rather than audited official salary-cap accounting.

In dashboard tables, contract cost fields such as `cap_number` are displayed in millions of dollars based on the cleaned public contract data.

### Team Surplus Value

Team surplus value compares how well a team performed against how expensive its roster was.

```text
surplus_rank_gap = cap_cost_rank - overall_performance_rank
```

A positive surplus rank gap means a team performed better than its cost rank.

For example:

```text
cap_cost_rank = 25
overall_performance_rank = 5
surplus_rank_gap = 20
```

This would indicate strong surplus value because the team performed like a top-five team while ranking much lower in contract cost.

A negative surplus rank gap means a team was expensive relative to its performance.

### Player Surplus Value

The player-level model focuses on offensive skill players:

- QB
- RB
- WR
- TE

For each player-season, the model calculates a public-data production score using:

- passing EPA
- rushing EPA
- receiving EPA
- passing yards
- passing touchdowns
- interceptions
- sacks suffered
- rushing yards
- rushing touchdowns
- receptions
- receiving yards
- receiving touchdowns

Players are ranked within their position group by production and by contract cost.

```text
player_surplus_gap = cost_rank_position - production_rank_position
```

A positive player surplus gap means the player produced better than his cost rank.

A negative player surplus gap means the player was expensive relative to his production rank.

The base player model is built at the player-team-season level. If a player appears for multiple teams in one season, each team stint may appear separately in the descriptive player-value outputs. This is useful for team roster analysis because it attributes production and contract cost to the team context in the public data.

For V4 backtesting, the model creates a cleaned player-season-position table. This collapses any duplicate player-season-position rows before recomputing production rank, cost rank, and surplus gap. The backtest therefore evaluates whether a player’s full-season surplus signal carried forward into the following season.

## Key Outputs

The project creates both team-level and player-level outputs.

### Team-Level Outputs

- `team_value_2021_2025.csv`
- `team_cost_2021_2025.csv`
- `team_surplus_2021_2025.csv`
- `focus_team_surplus_2021_2025.csv`

### Player-Level Outputs

- `player_value_skill_2021_2025.csv`
- `focus_player_value_skill_2021_2025.csv`
- `2025_eagles_skill_player_value.csv`
- `2025_top_skill_player_bargains.csv`

### Summary Outputs

- `focus_team_summary_2021_2025.csv`
- `team_surplus_summary_2025.csv`
- `eagles_skill_player_summary_2025.csv`
- `top_skill_player_bargains_2025.csv`
- `position_surplus_summary_2021_2025.csv`
- `cost_tier_surplus_summary_2021_2025.csv`

### Updated V2 Outputs

The v2 confidence workflow saves improved player-value files in `outputs_v2/`:

- `player_value_2021_2025_v2_confidence.csv`
- `focus_player_value_2021_2025_v2_confidence.csv`
- `player_value_diagnostics_2021_2025_v2_confidence.csv`

Summary outputs are saved in `outputs_v2/summary/`, including:

- `eagles_skill_player_summary_2025.csv`
- `top_skill_player_bargains_2025.csv`
- `player_data_quality_summary_2021_2025.csv`
- `player_data_quality_diagnostics_2021_2025.csv`

### Updated V3 Outputs

The V3 contract-context workflow saves player-value files in `outputs_v3/`:

- `player_value_2021_2025_v3_contract_context.csv`
- `focus_player_value_2021_2025_v3_contract_context.csv`

Summary outputs are saved in `outputs_v3/summary/`, including:

- `pre_extension_candidates_2025.csv`

The 2025 pre-extension candidate table is a latest-season watchlist, not a backtested result, because 2026 outcomes are not available yet.

### V4 Backtest and Candidate Review Outputs

The V4 workflow saves backtest and decision-support files in `outputs_v4/` and `outputs_v4/backtests/`.

Main V4 outputs include:

- `player_value_2021_2025_player_season_clean.csv`
- `backtest_lift_model_vs_not_flagged_clean.csv`
- `backtest_summary_clean.csv`
- `threshold_sensitivity_lift.csv`
- `threshold_sensitivity_summary.csv`
- `threshold_sensitivity_candidate_counts.csv`
- `season_stability_lift_by_season.csv`
- `season_stability_lift_by_season_position.csv`
- `candidate_review_summary.csv`
- `candidate_review_top_true_positives.csv`
- `candidate_review_model_misses.csv`
- `candidate_review_missed_opportunities.csv`
- `candidate_review_2025_watchlist.csv`
- `candidate_review_bucket_summary.csv`
- `candidate_review_performance_reference_by_group.csv`
- `candidate_review_performance_lift_reference.csv`

The V4 backtest compares model-flagged rookie-contract surplus candidates against high-confidence rookie-contract players the model did not flag.

### Updated Market Inefficiency Outputs

The updated market-inefficiency workflow uses the V3 confidence and contract-context player table.

Main outputs are saved in `outputs_v3/summary/`, including:

- `market_inefficiency_position_summary_v3.csv`
- `market_inefficiency_cost_tier_summary_v3.csv`
- `market_inefficiency_contract_stage_summary_v3.csv`
- `market_inefficiency_position_contract_stage_summary_v3.csv`
- `market_inefficiency_draft_capital_summary_v3.csv`
- `market_inefficiency_position_draft_capital_summary_v3.csv`
- `market_inefficiency_surplus_context_summary_v3.csv`
- `market_inefficiency_top_bargains_by_position_v3.csv`
- `market_inefficiency_2025_watchlist_v3.csv`
- `market_inefficiency_v4_position_validation_context.csv`
- `market_inefficiency_takeaways_v3.csv`

## Visualizations

The project creates several charts, including:

- 2025 contract cost proxy vs performance
- roster surplus value over time for focus teams
- average roster surplus value by focus team
- Eagles skill player surplus value
- Eagles skill player cost vs production
- top skill player bargains across the league
- V2 confidence and diagnostic visuals
- V4 backtest validation visuals

Team and player visuals are saved in:

```text
outputs/figures/
outputs_v2/figures/
```
V4 validation visuals are saved in:
```text
outputs_v4/figures/
```

## Early Findings

### 1. The Eagles stand out as a team-level surplus-value case

From 2021–2025, the Eagles show strong average roster surplus value among the focus teams. The model suggests that Philadelphia performed well relative to its public contract-cost profile.

This supports using the Eagles as the main case study.

### 2. The Eagles’ edge is portfolio construction, not just cheap stars

The player-level model shows that not every Eagles star grades as a surplus bargain. Expensive stars can still be excellent players while grading lower in surplus-value terms because they cost more.

This is important. The takeaway is not:

> The Eagles only win because their stars are cheap.

The better takeaway is:

> The Eagles can afford expensive stars because they generate enough surplus value elsewhere.

### 3. DeVonta Smith, Dallas Goedert, and Jalen Hurts grade positively in the 2025 skill-player model

In the 2025 Eagles skill-player model, DeVonta Smith, Dallas Goedert, and Jalen Hurts show positive surplus value.

This suggests that some of Philadelphia’s offensive value comes from players whose production rank compares favorably with their cost rank.

### 4. Expensive players are not automatically bad values, but the bar is higher

Players like A.J. Brown and Saquon Barkley can be excellent football players while still grading lower in a surplus-value model. The reason is simple: when a player is expensive, he must produce at an elite level to outperform his cost rank.

This distinction is important for interpreting the model.

### 5. The Giants are a useful contrast case

The Giants serve as a useful comparison because the model separates cheap production from overall team quality. A team can have some individual player bargains while still performing poorly overall.

This reinforces why both team-level and player-level analysis are needed.

### 6. Low-cost skill players are the clearest surplus-value archetype

The market inefficiency analysis shows a consistent pattern across offensive skill positions: low-cost players generate positive average surplus value, while mid/high/premium-cost players often generate negative surplus value relative to their cost rank.

The clearest example is wide receiver. From 2021–2025, low-cost wide receivers produced an average surplus gap of +12.2, while high-cost and premium-cost wide receivers produced negative average surplus gaps.

This does not mean expensive wide receivers are bad players. It means the cost hurdle is much higher. Once a player is paid like a proven star, he has to produce at an elite level just to remain a surplus-value asset.

The broader Moneyball takeaway is:

> The market pays heavily for proven production. The edge comes from identifying production before it becomes expensive.

### 7. V4 backtesting suggests the surplus signal has next-season value

The V4 backtest tests whether high-confidence rookie-contract surplus candidates outperform similar rookie-contract players the model did not flag.

At the default surplus threshold of `player_surplus_gap >= 5`, model candidates outperformed not-flagged rookie-contract players across the full 2021–2024 candidate window.

Across all offensive skill positions:

- model candidates had a 57.9% next-season hit rate
- not-flagged rookie-contract players had a 47.6% next-season hit rate
- hit-rate lift was +10.3 percentage points
- next-season surplus-gap lift was +10.38

Threshold sensitivity showed that the model signal stayed positive across all tested surplus thresholds from 0 to 20. The signal was strongest and most stable among wide receivers, while RB/TE/QB results were more sample-sensitive.

This does not mean the model is a finished front-office tool. It means the surplus signal is worth further development because it showed positive lift against a reasonable baseline.


## Eagles Case Study: Surplus Value Across the Contract Cycle

The Eagles case study shows how surplus value changes as players move through the contract cycle.

At quarterback, Philadelphia’s surplus value was highest when Jalen Hurts was inexpensive. The Eagles’ QB surplus gap was +33.0 in 2022, then narrowed to +3.0 in 2025 as the average cap number for the position increased.

This does not mean Hurts stopped being valuable. It means the cost hurdle became much higher once his contract reflected his proven production.

A similar pattern appears at wide receiver. The Eagles’ WR group produced strong average surplus value in 2022 and 2023, then remained positive but less extreme as the average cap number increased.

This supports the project’s central thesis:

> Surplus value is largest before the market fully prices the production.

The Eagles’ challenge going forward is not simply finding stars. It is continuously replacing lost surplus value as previously underpriced players become expensive.


## V2 Update: Data Quality and Confidence Flags

The second version of the player-value model adds data-quality and confidence flags to make the results more defensible.

In the original version, missing public contract data could distort player rankings because missing cost information risked being treated like a true zero-dollar cost. In the updated version, missing contract values are kept as missing, and players are flagged based on whether they successfully matched to a public contract row.

The updated player model now includes:

- `has_contract_match`: whether the player matched to a contract record
- `has_missing_contract`: whether the player is missing public contract data
- `contract_confidence`: readable label for contract match quality
- `meets_sample_threshold`: whether the player had enough usage to be ranked
- `sample_confidence`: readable label for sample-size quality
- `overall_confidence`: overall confidence label based on contract and sample-size flags

Low-sample players are preserved in a diagnostic output file but excluded from the final ranked player-value table. This keeps the final rankings focused on players with meaningful usage while still making it possible to audit which players were excluded and why.

The updated workflow creates two types of player outputs:

1. Final ranked player-value outputs for qualifying QB/RB/WR/TE players.
2. Diagnostic outputs that include all skill-position players before the sample-size filter.

This improves interpretation because a player is no longer simply labeled as a bargain or overpay. The model can now distinguish between high-confidence results and results that may be affected by missing contract data or small samples.

For example, a player with a positive surplus gap and high confidence can be interpreted as a stronger bargain candidate than a player with a similar gap but missing contract data.

This update does not fully solve all limitations. The model still uses public contract data as a proxy, focuses only on QB/RB/WR/TE, and uses hand-built production-score weights. However, the confidence flags make those limitations more visible and prevent missing data from being treated as meaningful cost information.


## Project Files

```text
performance.py
cost.py
surplus_value.py
visuals.py
player_data_audit.py
player_value.py
player_value_v2_confidence.py
player_visuals.py
insight_summary.py
insight_summary_v2_confidence.py
visuals_v2_confidence.py
market_inefficiency.py
app.py
player_value_v3_contract_context.py
player_value_v4_backtest.py
player_value_v4_backtest_clean.py
player_value_v4_threshold_sensitivity.py
player_value_v4_season_stability.py
player_value_v4_candidate_review.py
visuals_v4_backtest.py
```

## File Descriptions

### `performance.py`

Builds the team performance table using play-by-play data.

Main outputs:

- offensive EPA per play
- defensive EPA allowed per play
- offense rank
- defense rank
- overall rank

### `cost.py`

Builds the team cost table using public contract data.

Main steps:

- loads contract data
- flattens nested yearly contract data
- maps team names to abbreviations
- removes duplicate player-team-season rows
- aggregates contract cost by team-season

### `surplus_value.py`

Merges team performance and team cost.

Main outputs:

- surplus rank gap
- surplus value rank
- surplus value tier

### `visuals.py`

Creates team-level charts.

### `player_data_audit.py`

Audits the player-level datasets before modeling.

This file checks:

- dataframe shapes
- column names
- join keys
- contract match rates
- duplicate contract rows

### `player_value.py`

Builds the player-level skill-position surplus value model.

The first version focuses on:

- QB
- RB
- WR
- TE

### `player_value_v2_confidence.py`

Builds the updated player-level skill-position surplus value model with confidence and data-quality flags.

This version preserves missing contract values as missing, flags contract match quality, identifies low-sample players, saves a diagnostic file before filtering, and creates final ranked player-value outputs for qualifying QB/RB/WR/TE players.

### `player_value_v3_contract_context.py`

Builds on the V2 confidence player-value output by adding draft-capital and estimated contract-cycle context.

This file adds fields such as draft year, draft round, draft pick, draft-capital bucket, years since drafted, estimated contract stage, likely rookie-contract status, and surplus context.

### `player_value_v4_backtest_clean.py`

Creates the preferred V4 backtest comparing model-flagged rookie-contract surplus candidates against similar rookie-contract players the model did not flag.

This file also creates the cleaned player-season-position table used by later V4 scripts.

### `player_value_v4_threshold_sensitivity.py`

Tests whether the surplus signal depends too heavily on one threshold by evaluating multiple `player_surplus_gap` cutoffs.

### `player_value_v4_season_stability.py`

Tests whether the V4 backtest signal is stable across candidate seasons.

### `player_value_v4_candidate_review.py`

Creates human-readable review tables, including true positives, model misses, missed opportunities, and the 2025 latest-season watchlist.

### `visuals_v4_backtest.py`

Creates V4 static validation visuals, including threshold sensitivity and season stability charts.

### `player_visuals.py`

Creates player-level charts, including Eagles-specific player value charts.

### `insight_summary.py`

Creates clean summary tables for the final writeup and dashboard.

### `insight_summary_v2_confidence.py`

Creates updated summary tables using the v2 confidence player-value outputs.

This file carries confidence labels into the Eagles player summary, top league-wide bargain summary, and data-quality summary files.

### `visuals_v2_confidence.py`

Creates v2 confidence visuals showing sample-confidence, contract-confidence, overall-confidence, and diagnostic-vs-ranked player pool counts by season.

### `market_inefficiency.py`

Summarizes market inefficiency using the V3 player-value table, including confidence, draft-capital, contract-stage, cost-tier, and surplus-context fields.

This file updates the original cost-tier analysis by connecting descriptive market inefficiency to V4 validation context where available.

### `app.py`

Optional Streamlit dashboard for exploring the results interactively.

## How to Run the Project

### Original Workflow

```text
performance.py
cost.py
surplus_value.py
visuals.py
player_data_audit.py
player_value.py
player_visuals.py
insight_summary.py
market_inefficiency.py
```

Optional dashboard:

```bash
streamlit run app.py
```
Note: the Streamlit dashboard uses V3 player outputs for player-level sections, including V2 confidence fields and V3 contract-context fields. If V4 output files are available, the dashboard also shows threshold sensitivity, season stability, and the 2025 latest-season watchlist.

### V2 Confidence Workflow

The v2 confidence workflow uses the existing team and contract outputs, then creates updated player-value and summary files with confidence flags.

```text
performance.py
cost.py
surplus_value.py
player_value_v2_confidence.py
insight_summary_v2_confidence.py
visuals_v2_confidence.py
```
The v2 workflow saves updated player-value files in `outputs_v2/`, updated summary files in `outputs_v2/summary/`, and diagnostic visuals in `outputs_v2/figures/`.

### V2 Confidence Visuals

The v2 workflow also creates diagnostic visuals in `outputs_v2/figures/`.

![Diagnostic Player Pool vs Final Ranked Player Pool](outputs_v2/figures/player_pool_comparison_by_season.png)

![Skill-Player Sample Confidence by Season](outputs_v2/figures/player_sample_confidence_by_season.png)

These charts show why the final ranked player-value table is smaller than the diagnostic player pool: many skill-position players appear in the raw data but do not meet the usage threshold for meaningful ranking.

## V3 Contract Context Workflow

The v3 workflow builds on the v2 confidence output by adding draft-capital and estimated contract-cycle context to the player-value model.

The purpose of this step is to distinguish cheap production from structurally underpriced production. A player may look valuable because he is inexpensive, but v3 asks whether that value is connected to where the player is in the contract cycle.

New fields include:

- draft_year
- draft_round
- draft_pick
- draft_capital_bucket
- years_since_drafted
- estimated_contract_stage
- is_likely_rookie_contract
- surplus_context

The v3 workflow includes:
```text
player_value_v3_contract_context.py
market_inefficiency.py
```

The main v3 output is:

`outputs_v3/player_value_2021_2025_v3_contract_context.csv`

The main decision-support table is:

`outputs_v3/summary/pre_extension_candidates_2025.csv`

This moves the project closer to identifying players whose production may be appearing before the market has fully priced it.

## V4 Backtesting and Candidate Review Workflow

The V4 workflow tests whether the player surplus signal has next-season value.

The main backtest compares:

- model candidates: high-confidence rookie-contract players with positive surplus signals
- not-flagged baseline: high-confidence rookie-contract players the model did not flag

The V4 workflow uses:

- descriptive seasons: 2021–2025 NFL seasons
- candidate seasons: 2021–2024
- outcome seasons: 2022–2025
- latest watchlist season: 2025

The default candidate threshold is:

```text
player_surplus_gap >= 5
```

The first-pass hit definition is:

```text
appeared in the next season
AND
(remained positive-surplus OR improved production score)
```

The V4 workflow includes:

```text
market_inefficiency.py
player_value_v4_backtest_clean.py
player_value_v4_threshold_sensitivity.py
player_value_v4_season_stability.py
player_value_v4_candidate_review.py
visuals_v4_backtest.py
```

V4 outputs are saved in:

```text
outputs_v4/
outputs_v4/backtests/
outputs_v4/figures/
```
### V4 Backtest Visuals

![V4 Threshold Sensitivity: Overall Hit-Rate Lift](outputs_v4/figures/v4_threshold_sensitivity_overall_hit_rate_lift.png)

![V4 Threshold Sensitivity: Hit-Rate Lift by Position](outputs_v4/figures/v4_threshold_sensitivity_hit_rate_lift_by_position.png)

![V4 Season Stability: Hit-Rate Lift](outputs_v4/figures/v4_season_stability_hit_rate_lift.png)

## Limitations

This model is a public-data approximation and should be interpreted as a decision-support tool, not a perfect front-office valuation system.

Key limitations:

- Public contract data is an approximation, not official audited salary-cap accounting.
- Missing contract data can reduce confidence in some player rankings.
- The player model currently covers only QB, RB, WR, and TE.
- Defensive players and offensive linemen are not yet modeled.
- Production-score weights are hand-built rather than statistically learned.
- Rank gaps are intuitive but coarse and do not show the magnitude between players.
- Rookie-contract status and draft capital are estimated using public draft data; they are not a full contract-accounting or player-development model.
- The model does not yet adjust for injuries, snap counts, scheme, teammates, coaching context, or strength of schedule.

## Future Improvements

Future versions of this project could add:

- defensive player surplus value
- offensive line value proxies
- more precise rookie-contract and extension-status modeling
- more robust draft-value and draft-capital modeling
- injury-adjusted value
- age curves by position
- free-agent target recommendations
- trade-down scenario modeling
- a more polished Streamlit dashboard
- comparison between surplus value and playoff success

## Final Takeaway

The project’s core finding is that NFL roster efficiency is not about being cheap. It is about knowing when to pay for premium talent and when to search for underpriced production.

The strongest market-efficiency pattern in the model is that low-cost offensive skill players, especially wide receivers, running backs, and tight ends, generate positive surplus value on average, while mid/high/premium-cost players face a much steeper value hurdle.

For the Eagles, the early evidence suggests:

> Philadelphia’s advantage comes from portfolio construction: combining premium stars with enough low-cost surplus contributors to keep the full roster efficient.

The Billy Beane-style insight is not “avoid expensive players.” It is:

> Find production before the market prices it as proven production.

The v2 confidence update makes this conclusion more defensible by separating high-confidence player rankings from results that may be affected by missing public contract data or small samples.

It is also an important step toward turning the project from a descriptive ranking model into a decision-support tool, because it separates stronger signals from results that may be distorted by missing contract data or small samples.

In NFL roster-building terms, the edge comes from identifying value one contract cycle early while being honest about the limits of the available public data.