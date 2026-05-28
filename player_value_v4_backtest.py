# -*- coding: utf-8 -*-
"""
V4 Backtest

Goal:
Test whether rookie-contract surplus candidates in season Y
perform better in season Y+1 than the broader rookie-contract baseline.

To note: 
- Season labels are NFL season-year labels. 
- The descriptive data window is 2021–2025. 
- Backtest candidate seasons are 2021–2024 
    because each candidate season requires a following-season outcome. 
- The 2025 season is used as the latest-season watchlist 
    because 2026 outcomes are not available yet.
"""

import os
import pandas as pd


## SETUP ##

INPUT_FILE = "outputs_v3/player_value_2021_2025_v3_contract_context.csv"
OUTPUT_DIR = "outputs_v4/backtests"

os.makedirs(OUTPUT_DIR, exist_ok=True)

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)
pd.set_option("display.max_rows", 100)

df = pd.read_csv(INPUT_FILE)

print("Raw rows:", df.shape)


## SIMPLIFY TO ONE ROW PER PLAYER-SEASON-POSITION ##

group_cols = ["season", "player_id", "position_final"]

agg_rules = {
    "player_name": "first",
    "team": lambda x: "/".join(sorted(x.dropna().astype(str).unique())),

    "passing_yards": "sum",
    "passing_tds": "sum",
    "passing_interceptions": "sum",
    "sacks_suffered": "sum",
    "rushing_yards": "sum",
    "rushing_tds": "sum",
    "receptions": "sum",
    "receiving_yards": "sum",
    "receiving_tds": "sum",
    "targets": "sum",
    "passing_epa": "sum",
    "rushing_epa": "sum",
    "receiving_epa": "sum",
    "total_epa": "sum",
    "production_score": "sum",

    "cap_number": "sum",
    "cash_paid": "sum",

    "has_contract_match": "max",
    "has_missing_contract": "max",
    "meets_sample_threshold": "max",
    "sample_confidence": "first",
    "contract_confidence": "first",
    "overall_confidence": "first",

    "draft_year": "first",
    "draft_round": "first",
    "draft_pick": "first",
    "years_since_drafted": "first",
    "draft_capital_bucket": "first",
    "estimated_contract_stage": "first",
    "is_likely_rookie_contract": "first",
}

agg_rules = {k: v for k, v in agg_rules.items() if k in df.columns}

df = (
    df
    .groupby(group_cols, as_index=False)
    .agg(agg_rules)
)

print("Rows after player-season aggregation:", df.shape)


## RECOMPUTE RANKS AND SURPLUS AFTER AGGREGATION ##

df["production_rank_position"] = (
    df
    .groupby(["season", "position_final"])["production_score"]
    .rank(method="min", ascending=False)
)

df["cost_rank_position"] = (
    df
    .groupby(["season", "position_final"])["cap_number"]
    .rank(method="min", ascending=False)
)

df["player_surplus_gap"] = (
    df["cost_rank_position"] - df["production_rank_position"]
)

df["player_surplus_rank"] = (
    df
    .groupby(["season", "position_final"])["player_surplus_gap"]
    .rank(method="min", ascending=False)
)


## CREATE CANDIDATES AND BASELINE ##

candidate_seasons = [2021, 2022, 2023, 2024]
surplus_threshold = 5

model_candidates = df[
    (df["season"].isin(candidate_seasons)) &
    (df["is_likely_rookie_contract"] == True) &
    (df["overall_confidence"] == "high") &
    (df["player_surplus_gap"] >= surplus_threshold)
].copy()

baseline = df[
    (df["season"].isin(candidate_seasons)) &
    (df["is_likely_rookie_contract"] == True) &
    (df["overall_confidence"] == "high")
].copy()

#print("\nModel candidates:", model_candidates.shape)
#print(model_candidates["position_final"].value_counts())

#print("\nBaseline:", baseline.shape)
#print(baseline["position_final"].value_counts())


## BUILD NEXT-YEAR TABLE ##

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


candidate_results = run_backtest(model_candidates, "model_candidates")
baseline_results = run_backtest(baseline, "rookie_contract_baseline")

combined = pd.concat(
    [candidate_results, baseline_results],
    ignore_index=True
)


## SUMMARIZE ##

summary = (
    combined
    .groupby(["group", "position_final"], as_index=False)
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

summary["appearance_rate"] = (
    summary["appeared_next_year"] / summary["players"]
)

summary["hit_rate"] = (
    summary["hits"] / summary["players"]
)

#print("\nSummary:")
#print(summary)


## LIFT SUMMARY ##

model_summary = summary[
    summary["group"] == "model_candidates"
].copy()

baseline_summary = summary[
    summary["group"] == "rookie_contract_baseline"
].copy()

lift = model_summary.merge(
    baseline_summary,
    on="position_final",
    suffixes=("_model", "_baseline")
)

lift["hit_rate_lift"] = (
    lift["hit_rate_model"] - lift["hit_rate_baseline"]
)

lift["appearance_rate_lift"] = (
    lift["appearance_rate_model"] - lift["appearance_rate_baseline"]
)

lift["next_surplus_gap_lift"] = (
    lift["avg_next_surplus_gap_model"] -
    lift["avg_next_surplus_gap_baseline"]
)

print("\nLift:")
print(
    lift[
        [
            "position_final",
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
    ]
)


## SAVE OUTPUTS ##

candidate_results.to_csv(
    f"{OUTPUT_DIR}/model_candidate_backtest_simple.csv",
    index=False
)

baseline_results.to_csv(
    f"{OUTPUT_DIR}/rookie_contract_baseline_backtest_simple.csv",
    index=False
)

summary.to_csv(
    f"{OUTPUT_DIR}/backtest_summary_simple.csv",
    index=False
)

lift.to_csv(
    f"{OUTPUT_DIR}/backtest_lift_simple.csv",
    index=False
)

print("\nSaved outputs to:", OUTPUT_DIR)
print("\nSaved V4 backtest outputs to:", OUTPUT_DIR)