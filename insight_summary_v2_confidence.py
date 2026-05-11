# -*- coding: utf-8 -*-
"""
Makes the summary tables using the v2 confidence player-value output.

Outputs are saved to:
- outputs_v2/summary/

@author: hannah
"""

import os
import pandas as pd

os.makedirs("outputs_v2/summary", exist_ok=True)

team_surplus = pd.read_csv("outputs/team_surplus_2021_2025.csv")
focus_team_surplus = pd.read_csv("outputs/focus_team_surplus_2021_2025.csv")
player_value = pd.read_csv("outputs_v2/player_value_2021_2025_v2_confidence.csv")
focus_player_value = pd.read_csv("outputs_v2/focus_player_value_2021_2025_v2_confidence.csv")
player_value_diagnostics = pd.read_csv("outputs_v2/player_value_diagnostics_2021_2025_v2_confidence.csv")


## 1. TEAM-LEVEL SUMMARY, 2021-2025 ##
focus_team_summary = (
    focus_team_surplus
    .groupby(["team", "team_role"], as_index=False)
    .agg(
        avg_overall_rank=("overall_rank", "mean"),
        avg_cap_cost_rank=("cap_cost_rank", "mean"),
        avg_surplus_gap=("surplus_rank_gap", "mean"),
        best_surplus_gap=("surplus_rank_gap", "max"),
        worst_surplus_gap=("surplus_rank_gap", "min")
    )
    .sort_values("avg_surplus_gap", ascending=False)
)

focus_team_summary.to_csv(
    "outputs_v2/summary/focus_team_summary_2021_2025.csv",
    index=False
)


## 2. 2025 TEAM SURPLUS SUMMARY ##
team_2025_summary = (
    team_surplus
    .query("season == 2025")
    [[
        "team",
        "overall_rank",
        "cap_cost_rank",
        "surplus_rank_gap",
        "surplus_value_rank",
        "surplus_tier",
        "offensive_epa_per_play",
        "defensive_epa_allowed_per_play",
        "total_cap_number"
    ]]
    .sort_values("surplus_value_rank")
)

team_2025_summary.to_csv(
    "outputs_v2/summary/team_surplus_summary_2025.csv",
    index=False
)


## 3. EAGLES PLAYER SUMMARY, 2025 ##
eagles_players_2025 = (
    focus_player_value
    .query("season == 2025 and team == 'PHI'")
    [[
        "player_name",
        "position_final",
        "production_score",
        "total_epa",
        "cap_number",
        "production_rank_position",
        "cost_rank_position",
        "player_surplus_gap",
        "player_value_tier",
        "has_contract_match",
        "has_missing_contract",
        "contract_confidence",
        "sample_confidence",
        "overall_confidence"
    ]]
    .sort_values("player_surplus_gap", ascending=False)
)

eagles_players_2025.to_csv(
    "outputs_v2/summary/eagles_skill_player_summary_2025.csv",
    index=False
)


## 4. LEAGUE-WIDE TOP PLAYER BARGAINS, 2025 ##
top_player_bargains_2025 = (
    player_value
    .query("season == 2025")
    [[
        "player_name",
        "team",
        "position_final",
        "production_score",
        "total_epa",
        "cap_number",
        "production_rank_position",
        "cost_rank_position",
        "player_surplus_gap",
        "player_value_tier",
        "has_contract_match",
        "has_missing_contract",
        "contract_confidence",
        "sample_confidence",
        "overall_confidence"
    ]]
    .sort_values("player_surplus_gap", ascending=False)
    .head(25)
)

top_player_bargains_2025.to_csv(
    "outputs_v2/summary/top_skill_player_bargains_2025.csv",
    index=False
)

print(player_value.shape)
print(focus_player_value.shape)
print(eagles_players_2025.shape)

print(
    focus_player_value
    .query("season == 2025 and team == 'PHI'")
    [[
        "player_name",
        "position_final",
        "passing_yards",
        "receptions",
        "receiving_yards",
        "targets",
        "meets_sample_threshold",
        "player_surplus_gap",
        "overall_confidence"
    ]]
)

print("\nSaved summary outputs:")
print("- outputs_v2/summary/focus_team_summary_2021_2025.csv")
print("- outputs_v2/summary/team_surplus_summary_2025.csv")
print("- outputs_v2/summary/eagles_skill_player_summary_2025.csv")
print("- outputs_v2/summary/top_skill_player_bargains_2025.csv")

print("\nFocus Team Summary:")
print(focus_team_summary)

print("\n2025 Eagles Skill Player Summary:")
print(eagles_players_2025)

###############################################################################

## 5. PLAYER DATA QUALITY SUMMARY ##

player_data_quality = (
    player_value
    .groupby(
        [
            "season",
            "overall_confidence",
            "contract_confidence",
            "sample_confidence"
        ],
        as_index=False
    )
    .size()
    .rename(columns={"size": "player_count"})
)

player_data_quality.to_csv(
    "outputs_v2/summary/player_data_quality_summary_2021_2025.csv",
    index=False
)

print("- outputs_v2/summary/player_data_quality_summary_2021_2025.csv")

print("\nPlayer Data Quality Summary:")
print(player_data_quality)

## 6. PLAYER DATA QUALITY DIAGNOSTICS ##
player_data_quality_diagnostics = (
    player_value_diagnostics
    .groupby(
        [
            "season",
            "overall_confidence",
            "contract_confidence",
            "sample_confidence",
            "meets_sample_threshold"
        ],
        as_index=False
    )
    .size()
    .rename(columns={"size": "player_count"})
)

player_data_quality_diagnostics.to_csv(
    "outputs_v2/summary/player_data_quality_diagnostics_2021_2025.csv",
    index=False
)

print("- outputs_v2/summary/player_data_quality_diagnostics_2021_2025.csv")

print("\nPlayer Data Quality Diagnostics:")
print(player_data_quality_diagnostics)
