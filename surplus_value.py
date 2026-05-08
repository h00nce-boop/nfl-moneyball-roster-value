#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May  7 20:04:42 2026

@author: hannah
"""

import pandas as pd
import os

## LOAD OUTPUTS ##
performance = pd.read_csv("outputs/team_value_2021_2025.csv")
cost = pd.read_csv("outputs/team_cost_2021_2025.csv")

## MERGE PERFORMANCE + COST ##
team_surplus = performance.merge(
    cost,
    on=["season", "team"],
    how="inner"
)

print("\nMerged team_surplus shape:")
print(team_surplus.shape)

print("\nColumns:")
print(list(team_surplus.columns))

## PERFORMANCE SCORE ##
team_surplus["performance_score"] = (
    33 - team_surplus["overall_rank"]
)

## COST SCORE ##
team_surplus["cost_score"] = (
    33 - team_surplus["cap_cost_rank"]
)

## SURPLUS VALUE SCORE ##
team_surplus["surplus_rank_gap"] = (
    team_surplus["cap_cost_rank"] - team_surplus["overall_rank"]
)

## TIER LABELS ##
def label_surplus_tier(gap):
    if gap >= 10:
        return "Strong surplus value"
    elif gap >= 4:
        return "Positive value"
    elif gap > -4:
        return "Fair value"
    elif gap > -10:
        return "Negative value"
    else:
        return "Major underperformance"

team_surplus["surplus_tier"] = team_surplus["surplus_rank_gap"].apply(label_surplus_tier)


## RANKING BY SURPLUS VALUE ##
team_surplus["surplus_value_rank"] = (
    team_surplus
    .groupby("season")["surplus_rank_gap"]
    .rank(ascending=False)
)

team_surplus = team_surplus.sort_values(["season", "surplus_value_rank"])

## 2025 TEAM SURPLUS ##
team_surplus_2025 = (
    team_surplus
    .query("season == 2025")
    .sort_values("surplus_value_rank")
)

print("\nTop 10 Surplus Value Teams in 2025:")
print(
    team_surplus_2025[[
        "team",
        "overall_rank",
        "cap_cost_rank",
        "surplus_rank_gap",
        "surplus_value_rank",
        "surplus_tier"
    ]]
    .head(10)
)

print("\nBottom 10 Surplus Value Teams in 2025:")
print(
    team_surplus_2025[[
        "team",
        "overall_rank",
        "cap_cost_rank",
        "surplus_rank_gap",
        "surplus_value_rank",
        "surplus_tier"
    ]]
    .tail(10)
)

## FOCUS TEAM VIEW ##
focus_team_labels = {
    "PHI": "Eagles - main case study",
    "NYG": "Giants - rebuild comparison",
    "CLE": "Browns - cap cautionary tale",
    "BAL": "Ravens - contender benchmark",
    "DET": "Lions - young-core benchmark"
}

focus_teams = list(focus_team_labels.keys())

focus_team_surplus = (
    team_surplus
    .loc[team_surplus["team"].isin(focus_teams)]
    .copy()
)

focus_team_surplus["team_role"] = focus_team_surplus["team"].map(focus_team_labels)

focus_team_surplus = focus_team_surplus.sort_values(["season", "team"])

print("\nFocus Team Surplus Value:")
print(
    focus_team_surplus[[
        "season",
        "team",
        "team_role",
        "overall_rank",
        "cap_cost_rank",
        "surplus_rank_gap",
        "surplus_value_rank",
        "surplus_tier"
    ]]
)

## SAVE OUTPUTS ##
os.makedirs("outputs", exist_ok=True)

team_surplus.to_csv("outputs/team_surplus_2021_2025.csv", index=False)
team_surplus_2025.to_csv("outputs/team_surplus_2025.csv", index=False)
focus_team_surplus.to_csv("outputs/focus_team_surplus_2021_2025.csv", index=False)

print("\nSaved surplus value outputs:")
print("- outputs/team_surplus_2021_2025.csv")
print("- outputs/team_surplus_2025.csv")
print("- outputs/focus_team_surplus_2021_2025.csv")