#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V4 Season Stability

Goal:
Test whether the V4 backtest signal is stable across candidate seasons.

This script compares model-flagged rookie-contract surplus candidates
against rookie-contract players the model passed on, using the default
surplus threshold of player_surplus_gap >= 5.

To note: 
- Season labels are NFL season-year labels. 
- The descriptive data window is 2021–2025. 
- Backtest candidate seasons are 2021–2024 
    because each candidate season requires a following-season outcome. 
- The 2025 season is used as the latest-season watchlist 
    because 2026 outcomes are not available yet.

@author: hannah
"""

import os
import pandas as pd

##SETUP ##

INPUT_FILE = "outputs_v4/player_value_2021_2025_player_season_clean.csv"
OUTPUT_DIR = "outputs_v4/backtests"

os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv(INPUT_FILE)

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)
pd.set_option("display.max_rows", 100)

print("Loaded clean player-season file:", df.shape)

candidate_seasons = [2021, 2022, 2023, 2024]
surplus_threshold = 5


## BASELINE POOL ##

baseline_pool = df[
    (df["season"].isin(candidate_seasons)) &
    (df["is_likely_rookie_contract"] == True) &
    (df["overall_confidence"] == "high")
].copy()

model_candidates = baseline_pool[
    baseline_pool["player_surplus_gap"] >= surplus_threshold
].copy()

not_flagged_baseline = baseline_pool[
    baseline_pool["player_surplus_gap"] < surplus_threshold
].copy()

##CANDIDATE COUNT BY SEASON ##
model_counts = (
    model_candidates
    .groupby("season")
    .size()
    .reindex(candidate_seasons, fill_value=0)
    .rename("model_candidates")
)

baseline_counts = (
    not_flagged_baseline
    .groupby("season")
    .size()
    .reindex(candidate_seasons, fill_value=0)
    .rename("not_flagged_baseline")
)

season_counts = pd.concat(
    [model_counts, baseline_counts],
    axis=1
).reset_index()

season_counts["total_players"] = (
    season_counts["model_candidates"] +
    season_counts["not_flagged_baseline"]
)

print("\nCandidate counts by season:")
print(season_counts.to_string(index=False))


## NEXT YEAR TABLE ##
next_year = df.copy()
next_year["candidate_season"] = next_year["season"] - 1

next_year = next_year[
    [
        "candidate_season",
        "player_id",
        "position_final",
        "team",
        "production_score",
        "total_epa",
        "cap_number",
        "player_surplus_gap",
        "production_rank_position",
        "cost_rank_position",
    ]
].copy()

next_year = next_year.rename(
    columns={
        "team": "next_team",
        "production_score": "next_production_score",
        "total_epa": "next_total_epa",
        "cap_number": "next_cap_number",
        "player_surplus_gap": "next_player_surplus_gap",
        "production_rank_position": "next_production_rank_position",
        "cost_rank_position": "next_cost_rank_position",
    }
)

## BACKTEST FUNCTION ##
def run_backtest(group, group_name):
    group = group.copy()
    group["candidate_season"] = group["season"]

    result = group.merge(
        next_year,
        on=["candidate_season", "player_id", "position_final"],
        how="left"
    )

    result["group"] = group_name

    result["appeared_next_year"] = result["next_production_score"].notna()

    result["remained_positive_surplus"] = (
        result["next_player_surplus_gap"] > 0
    )

    result["remained_strong_surplus"] = (
        result["next_player_surplus_gap"] >= surplus_threshold
    )

    result["improved_production"] = (
        result["next_production_score"] > result["production_score"]
    )

    result["hit"] = (
        result["appeared_next_year"] &
        (
            result["remained_positive_surplus"] |
            result["improved_production"]
        )
    )

    return result

## RUN ##
candidate_results = run_backtest(
    model_candidates,
    "model_candidates"
)

not_flagged_results = run_backtest(
    not_flagged_baseline,
    "not_flagged_baseline"
)

combined = pd.concat(
    [candidate_results, not_flagged_results],
    ignore_index=True
)

## SUMMARY BY SEASON##
summary_by_season = (
    combined
    .groupby(["season", "group"], as_index=False)
    .agg(
        players=("player_id", "count"),
        appeared_next_year=("appeared_next_year", "sum"),
        hits=("hit", "sum"),
        avg_surplus_gap=("player_surplus_gap", "mean"),
        avg_next_surplus_gap=("next_player_surplus_gap", "mean"),
        avg_production_score=("production_score", "mean"),
        avg_next_production_score=("next_production_score", "mean"),
    )
)

summary_by_season["appearance_rate"] = (
    summary_by_season["appeared_next_year"] /
    summary_by_season["players"]
)

summary_by_season["hit_rate"] = (
    summary_by_season["hits"] /
    summary_by_season["players"]
)

## LIFT BY SEASON ##

model_summary_season = summary_by_season[
    summary_by_season["group"] == "model_candidates"
].copy()

baseline_summary_season = summary_by_season[
    summary_by_season["group"] == "not_flagged_baseline"
].copy()

lift_by_season = model_summary_season.merge(
    baseline_summary_season,
    on="season",
    suffixes=("_model", "_baseline")
)

lift_by_season["hit_rate_lift"] = (
    lift_by_season["hit_rate_model"] -
    lift_by_season["hit_rate_baseline"]
)

lift_by_season["appearance_rate_lift"] = (
    lift_by_season["appearance_rate_model"] -
    lift_by_season["appearance_rate_baseline"]
)

lift_by_season["next_surplus_gap_lift"] = (
    lift_by_season["avg_next_surplus_gap_model"] -
    lift_by_season["avg_next_surplus_gap_baseline"]
)

lift_by_season["next_production_score_lift"] = (
    lift_by_season["avg_next_production_score_model"] -
    lift_by_season["avg_next_production_score_baseline"]
)


## SUMMARY BY SEASON & POSITION ##
summary_by_season_position = (
    combined
    .groupby(["season", "position_final", "group"], as_index=False)
    .agg(
        players=("player_id", "count"),
        appeared_next_year=("appeared_next_year", "sum"),
        hits=("hit", "sum"),
        avg_surplus_gap=("player_surplus_gap", "mean"),
        avg_next_surplus_gap=("next_player_surplus_gap", "mean"),
        avg_production_score=("production_score", "mean"),
        avg_next_production_score=("next_production_score", "mean"),
    )
)

summary_by_season_position["appearance_rate"] = (
    summary_by_season_position["appeared_next_year"] /
    summary_by_season_position["players"]
)

summary_by_season_position["hit_rate"] = (
    summary_by_season_position["hits"] /
    summary_by_season_position["players"]
)

## LIFT BY SEASON & POSITION ##
model_summary_season_position = summary_by_season_position[
    summary_by_season_position["group"] == "model_candidates"
].copy()

baseline_summary_season_position = summary_by_season_position[
    summary_by_season_position["group"] == "not_flagged_baseline"
].copy()

lift_by_season_position = model_summary_season_position.merge(
    baseline_summary_season_position,
    on=["season", "position_final"],
    suffixes=("_model", "_baseline")
)

lift_by_season_position["hit_rate_lift"] = (
    lift_by_season_position["hit_rate_model"] -
    lift_by_season_position["hit_rate_baseline"]
)

lift_by_season_position["appearance_rate_lift"] = (
    lift_by_season_position["appearance_rate_model"] -
    lift_by_season_position["appearance_rate_baseline"]
)

lift_by_season_position["next_surplus_gap_lift"] = (
    lift_by_season_position["avg_next_surplus_gap_model"] -
    lift_by_season_position["avg_next_surplus_gap_baseline"]
)

lift_by_season_position["next_production_score_lift"] = (
    lift_by_season_position["avg_next_production_score_model"] -
    lift_by_season_position["avg_next_production_score_baseline"]
)


##USEFUL PRINTED##
season_view = lift_by_season[
    [
        "season",
        "players_model",
        "players_baseline",
        "hit_rate_model",
        "hit_rate_baseline",
        "hit_rate_lift",
        "appearance_rate_model",
        "appearance_rate_baseline",
        "appearance_rate_lift",
        "avg_next_surplus_gap_model",
        "avg_next_surplus_gap_baseline",
        "next_surplus_gap_lift",
    ]
].copy()

season_view = season_view.round(3)

print("\nSeason stability: overall by candidate season")
print(season_view.to_string(index=False))


season_position_view = lift_by_season_position[
    [
        "season",
        "position_final",
        "players_model",
        "players_baseline",
        "hit_rate_model",
        "hit_rate_baseline",
        "hit_rate_lift",
        "appearance_rate_lift",
        "next_surplus_gap_lift",
    ]
].copy()

season_position_view = season_position_view.round(3)

print("\nSeason stability: by season and position")
print(season_position_view.to_string(index=False))

# print("\nSummary by season:")
# print(summary_by_season)

# print("\nSummary by season and position:")
# print(summary_by_season_position)


## SAVE  ##

combined.to_csv(
    f"{OUTPUT_DIR}/season_stability_combined_results.csv",
    index=False
)

season_counts.to_csv(
    f"{OUTPUT_DIR}/season_stability_candidate_counts.csv",
    index=False
)

summary_by_season.to_csv(
    f"{OUTPUT_DIR}/season_stability_summary_by_season.csv",
    index=False
)

lift_by_season.to_csv(
    f"{OUTPUT_DIR}/season_stability_lift_by_season.csv",
    index=False
)

summary_by_season_position.to_csv(
    f"{OUTPUT_DIR}/season_stability_summary_by_season_position.csv",
    index=False
)

lift_by_season_position.to_csv(
    f"{OUTPUT_DIR}/season_stability_lift_by_season_position.csv",
    index=False
)

print("\nSaved season stability outputs to:", OUTPUT_DIR)