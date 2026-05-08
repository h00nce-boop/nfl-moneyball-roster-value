#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May  7 21:07:25 2026

@author: hannah
"""

import os
import pandas as pd

os.makedirs("outputs/summary", exist_ok=True)

team_surplus = pd.read_csv("outputs/team_surplus_2021_2025.csv")
focus_team_surplus = pd.read_csv("outputs/focus_team_surplus_2021_2025.csv")
player_value = pd.read_csv("outputs/player_value_skill_2021_2025.csv")
focus_player_value = pd.read_csv("outputs/focus_player_value_skill_2021_2025.csv")


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
    "outputs/summary/focus_team_summary_2021_2025.csv",
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
    "outputs/summary/team_surplus_summary_2025.csv",
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
        "player_value_tier"
    ]]
    .sort_values("player_surplus_gap", ascending=False)
)

eagles_players_2025.to_csv(
    "outputs/summary/eagles_skill_player_summary_2025.csv",
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
        "player_value_tier"
    ]]
    .sort_values("player_surplus_gap", ascending=False)
    .head(25)
)

top_player_bargains_2025.to_csv(
    "outputs/summary/top_skill_player_bargains_2025.csv",
    index=False
)


print("\nSaved summary outputs:")
print("- outputs/summary/focus_team_summary_2021_2025.csv")
print("- outputs/summary/team_surplus_summary_2025.csv")
print("- outputs/summary/eagles_skill_player_summary_2025.csv")
print("- outputs/summary/top_skill_player_bargains_2025.csv")

print("\nFocus Team Summary:")
print(focus_team_summary)

print("\n2025 Eagles Skill Player Summary:")
print(eagles_players_2025)