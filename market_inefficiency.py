# -*- coding: utf-8 -*-
"""
Analyzes potential market inefficiencies by position and contract cost tier.

This script summarizes which offensive skill-player archetypes generate the
most surplus value across the 2021-2025 sample.

Outputs are saved to:
- outputs/summary/

@author: hannah
"""

import os
import pandas as pd

os.makedirs("outputs/summary", exist_ok=True)

player_value = pd.read_csv("outputs/player_value_skill_2021_2025.csv")
team_surplus = pd.read_csv("outputs/team_surplus_2021_2025.csv")


## POSITION-LEVEL SURPLUS SUMMARY ##
position_summary = (
    player_value
    .groupby("position_final", as_index=False)
    .agg(
        players_evaluated=("player_name", "count"),
        avg_surplus_gap=("player_surplus_gap", "mean"),
        median_surplus_gap=("player_surplus_gap", "median"),
        avg_cap_number=("cap_number", "mean"),
        avg_production_score=("production_score", "mean"),
        major_bargains=("player_value_tier", lambda x: (x == "Major bargain").sum()),
        strong_bargains=("player_value_tier", lambda x: (x == "Strong bargain").sum()),
        major_overpays=("player_value_tier", lambda x: (x == "Major overpay").sum())
    )
    .sort_values("avg_surplus_gap", ascending=False)
)

position_summary.to_csv(
    "outputs/summary/position_surplus_summary_2021_2025.csv",
    index=False
)


## COST TIER ANALYSIS ##
def assign_cost_tier(cap_number):
    if cap_number >= 20:
        return "Premium cost"
    elif cap_number >= 10:
        return "High cost"
    elif cap_number >= 4:
        return "Mid cost"
    elif cap_number > 0:
        return "Low cost"
    else:
        return "No/missing cost"


player_value["cost_tier"] = player_value["cap_number"].apply(assign_cost_tier)

cost_tier_summary = (
    player_value
    .groupby(["position_final", "cost_tier"], as_index=False)
    .agg(
        players_evaluated=("player_name", "count"),
        avg_surplus_gap=("player_surplus_gap", "mean"),
        median_surplus_gap=("player_surplus_gap", "median"),
        avg_production_score=("production_score", "mean"),
        avg_cap_number=("cap_number", "mean")
    )
    .sort_values(["position_final", "avg_surplus_gap"], ascending=[True, False])
)

cost_tier_summary.to_csv(
    "outputs/summary/cost_tier_surplus_summary_2021_2025.csv",
    index=False
)


## TOP PLAYER BARGAINS BY POSITION ##
top_by_position = (
    player_value
    .sort_values("player_surplus_gap", ascending=False)
    .groupby(["season", "position_final"])
    .head(10)
    [[
        "season",
        "player_name",
        "team",
        "position_final",
        "cap_number",
        "production_score",
        "total_epa",
        "production_rank_position",
        "cost_rank_position",
        "player_surplus_gap",
        "player_value_tier"
    ]]
)

top_by_position.to_csv(
    "outputs/summary/top_player_bargains_by_position_2021_2025.csv",
    index=False
)


## EAGLES PLAYER ARCHETYPE SUMMARY ##
eagles_summary = (
    player_value
    .query("team == 'PHI'")
    .groupby(["season", "position_final"], as_index=False)
    .agg(
        players_evaluated=("player_name", "count"),
        avg_surplus_gap=("player_surplus_gap", "mean"),
        best_player_surplus=("player_surplus_gap", "max"),
        worst_player_surplus=("player_surplus_gap", "min"),
        avg_cap_number=("cap_number", "mean")
    )
)

eagles_summary.to_csv(
    "outputs/summary/eagles_position_surplus_summary_2021_2025.csv",
    index=False
)


## PRINT KEY TAKEAWAYS ##
print("\nPosition Surplus Summary:")
print(position_summary)

print("\nCost Tier Surplus Summary:")
print(cost_tier_summary)

print("\nEagles Position Surplus Summary:")
print(eagles_summary)

print("\nSaved market inefficiency outputs:")
print("- outputs/summary/position_surplus_summary_2021_2025.csv")
print("- outputs/summary/cost_tier_surplus_summary_2021_2025.csv")
print("- outputs/summary/top_player_bargains_by_position_2021_2025.csv")
print("- outputs/summary/eagles_position_surplus_summary_2021_2025.csv")