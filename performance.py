#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May  7 18:05:12 2026

@author: hannah
"""
import nflreadpy as nfl
import pandas as pd

## DATA LOADING ##

seasons = [2021, 2022, 2023, 2024, 2025]

player_stats = nfl.load_player_stats(seasons)
pbp = nfl.load_pbp(seasons)
rosters = nfl.load_rosters(seasons)
snap_counts = nfl.load_snap_counts(seasons)
team_stats = nfl.load_team_stats(seasons)
players = nfl.load_players()
contracts = nfl.load_contracts()
draft_picks = nfl.load_draft_picks(seasons)


## CONVERTING TO PANDAS // CLEANING ##
def to_pandas_safe(data):
    if hasattr(data, "to_pandas"):
        return data.to_pandas()
    return data

player_stats = to_pandas_safe(player_stats)
pbp = to_pandas_safe(pbp)
rosters = to_pandas_safe(rosters)
snap_counts = to_pandas_safe(snap_counts)
team_stats = to_pandas_safe(team_stats)
players = to_pandas_safe(players)
contracts = to_pandas_safe(contracts)
draft_picks = to_pandas_safe(draft_picks)

## BUILD OFFENSIVE EPA ##
team_offense = (
    pbp
    .query("season_type == 'REG' and posteam.notna()")
    .groupby(["season", "posteam"], as_index=False)
    .agg(
        offensive_plays=("play_id", "count"),
        offensive_epa_total=("epa", "sum"),
        offensive_epa_per_play=("epa", "mean"),
        offensive_success_rate=("success", "mean")
    )
    .rename(columns={"posteam": "team"})
)

## BUILD DEFENSIVE EPA ##
team_defense = (
    pbp
    .query("season_type == 'REG' and defteam.notna()")
    .groupby(["season", "defteam"], as_index=False)
    .agg(
        defensive_plays=("play_id", "count"),
        defensive_epa_allowed_total=("epa", "sum"),
        defensive_epa_allowed_per_play=("epa", "mean")
    )
    .rename(columns={"defteam": "team"})
)

## JOINING OFFENSE + DEFENSE ##
team_value = team_offense.merge(
    team_defense,
    on=["season", "team"],
    how="left"
)


## SIMPLE RANKINGS ##
team_value["offense_rank"] = (
    team_value
    .groupby("season")["offensive_epa_per_play"]
    .rank(ascending=False)
)

team_value["defense_rank"] = (
    team_value
    .groupby("season")["defensive_epa_allowed_per_play"]
    .rank(ascending=True)
)

team_value["overall_efficiency_rank"] = (
    team_value["offense_rank"] + team_value["defense_rank"]
)

team_value["overall_rank"] = (
    team_value
    .groupby("season")["overall_efficiency_rank"]
    .rank(ascending=True)
)

## LOOKING AT 2025 ##
team_value_2025 = (
    team_value
    .query("season == 2025")
    .sort_values("overall_rank")
)

team_value_2025[[
    "team",
    "offensive_epa_per_play",
    "defensive_epa_allowed_per_play",
    "offense_rank",
    "defense_rank",
    "overall_rank"
]].head(10)

## EAGLES, GIANTS, BROWNS ##
focus_teams = ["PHI", "NYG", "CLE", "BAL", "DET"]

focus_team_labels = {
    "PHI": "Eagles - main case study",
    "NYG": "Giants - rebuild comparison",
    "CLE": "Browns - cap cautionary tale",
    "BAL": "Ravens - contender benchmark",
    "DET": "Lions - young-core benchmark"
}

focus_teams = list(focus_team_labels.keys())

focus_team_value = (
    team_value
    .loc[team_value["team"].isin(focus_teams)]
    .copy()
)

focus_team_value["team_role"] = focus_team_value["team"].map(focus_team_labels)

focus_team_value.sort_values(["season", "team"])

## FOCUS TEAM VIEW ##
focus_team_summary = (
    focus_team_value[[
        "season",
        "team",
        "team_role",
        "offensive_epa_per_play",
        "defensive_epa_allowed_per_play",
        "offense_rank",
        "defense_rank",
        "overall_rank"
    ]]
    .sort_values(["team", "season"])
)

print("\nFocus Team Performance Summary:")
print(focus_team_summary)

## SAVE TABLES ##
import os

os.makedirs("outputs", exist_ok=True)

team_value.to_csv("outputs/team_value_2021_2025.csv", index=False)
team_value_2025.to_csv("outputs/team_value_2025.csv", index=False)
focus_team_summary.to_csv("outputs/focus_team_performance_2021_2025.csv", index=False)

## 2025 RANKINGS ##
print("\nTop 10 Teams by 2025 Overall Efficiency:")
print(
    team_value_2025[[
        "team",
        "offensive_epa_per_play",
        "defensive_epa_allowed_per_play",
        "offense_rank",
        "defense_rank",
        "overall_rank"
    ]]
    .head(10)
)

## YEAR-OVER-YEAR TREND ##
focus_trend = (
    focus_team_summary
    .pivot(index="season", columns="team", values="overall_rank")
    .reset_index()
)

print("\nFocus Team Overall Rank Trend:")
print(focus_trend)

focus_trend.to_csv("outputs/focus_team_rank_trend_2021_2025.csv", index=False)

print("\nSaved performance outputs:")
print("- outputs/team_value_2021_2025.csv")
print("- outputs/team_value_2025.csv")
print("- outputs/focus_team_performance_2021_2025.csv")
print("- outputs/focus_team_rank_trend_2021_2025.csv")
