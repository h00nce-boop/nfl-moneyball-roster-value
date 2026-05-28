# -*- coding: utf-8 -*-
"""
V4 Candidate Review

Goal:
Create human-readable review tables from the V4 backtest.

This script identifies:
1. Top true positives:
   Players the model flagged who validated the next season.

2. Model misses:
   Players the model flagged who did not validate the next season.

3. Missed opportunities:
   Players the model did not flag who later validated.

4. 2025 watchlist:
   Current/future-facing players who match the validated candidate profile,
   but do not yet have next-year outcomes.
   
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


## SETUP ##

BACKTEST_FILE = "outputs_v4/backtests/season_stability_combined_results.csv"
CLEAN_PLAYER_FILE = "outputs_v4/player_value_2021_2025_player_season_clean.csv"
OUTPUT_DIR = "outputs_v4/backtests"

os.makedirs(OUTPUT_DIR, exist_ok=True)

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)
pd.set_option("display.max_rows", 100)

backtest = pd.read_csv(BACKTEST_FILE)
players = pd.read_csv(CLEAN_PLAYER_FILE)

print("Loaded backtest results:", backtest.shape)
print("Loaded clean player-season file:", players.shape)

surplus_threshold = 5
watchlist_season = 2025


## FUNCTION ##

def keep_existing_columns(df, columns):
    return [col for col in columns if col in df.columns]


def print_preview(title, df, columns, n=10):
   
    print(f"\n{title}")
    print("Rows:", len(df))

    if len(df) == 0:
        print("No rows found.")
        return

    preview_columns = keep_existing_columns(df, columns)

    print(
        df[preview_columns]
        .head(n)
        .to_string(index=False)
    )


## REVIEW COLUMNS ##

review_columns = [
    "season",
    "player_name",
    "team",
    "position_final",
    "production_score",
    "player_surplus_gap",
    "cap_number",
    "next_team",
    "next_production_score",
    "next_player_surplus_gap",
    "next_cap_number",
    "appeared_next_year",
    "remained_positive_surplus",
    "improved_production",
    "hit",
]

compact_review_columns = [
    "season",
    "player_name",
    "team",
    "position_final",
    "player_surplus_gap",
    "next_player_surplus_gap",
    "appeared_next_year",
    "hit",
]

watchlist_columns = [
    "season",
    "player_name",
    "team",
    "position_final",
    "production_score",
    "player_surplus_gap",
    "player_surplus_rank",
    "cap_number",
    "draft_year",
    "draft_round",
    "draft_pick",
    "years_since_drafted",
    "draft_capital_bucket",
    "estimated_contract_stage",
    "is_likely_rookie_contract",
    "overall_confidence",
]

compact_watchlist_columns = [
    "player_name",
    "team",
    "position_final",
    "production_score",
    "player_surplus_gap",
    "cap_number",
    "estimated_contract_stage",
]


## TOP TRUE POSITIVES ##

top_true_positives = backtest[
    (backtest["group"] == "model_candidates") &
    (backtest["hit"] == True)
].copy()

top_true_positives = top_true_positives.sort_values(
    ["next_player_surplus_gap", "next_production_score"],
    ascending=[False, False],
    na_position="last"
)

top_true_positives["review_group"] = "true_positives"


## MODEL MISSES ##

model_misses = backtest[
    (backtest["group"] == "model_candidates") &
    (backtest["hit"] == False)
].copy()

model_misses = model_misses.sort_values(
    ["player_surplus_gap", "production_score"],
    ascending=[False, False],
    na_position="last"
)

model_misses["review_group"] = "model_misses"


## MISSED OPPORTUNITIES / FALSE NEGATIVES ##

missed_opportunities = backtest[
    (backtest["group"] == "not_flagged_baseline") &
    (backtest["hit"] == True)
].copy()

missed_opportunities = missed_opportunities.sort_values(
    ["next_player_surplus_gap", "next_production_score"],
    ascending=[False, False],
    na_position="last"
)

missed_opportunities["review_group"] = "missed_opportunities"


## 2025 WATCHLIST ##

watchlist_2025 = players[
    (players["season"] == watchlist_season) &
    (players["is_likely_rookie_contract"] == True) &
    (players["overall_confidence"] == "high") &
    (players["player_surplus_gap"] >= surplus_threshold)
].copy()

watchlist_2025 = watchlist_2025.sort_values(
    ["player_surplus_gap", "production_score"],
    ascending=[False, False],
    na_position="last"
)

watchlist_2025["review_group"] = "2025_watchlist"
watchlist_2025["watchlist_note"] = (
    "Matches historical candidate profile; no next-year outcome yet."
)


## REVIEW BUCKET SUMMARY ##
# These review groups are defined by outcome type, so this summary should
# not be interpreted as a model-performance table.
#
# Performance should be evaluated using:
# - backtest_lift_model_vs_not_flagged_clean.csv
# - threshold_sensitivity_lift.csv
# - season_stability_lift_by_season.csv

review_frames = [
    top_true_positives,
    model_misses,
    missed_opportunities,
]

review_combined = pd.concat(
    review_frames,
    ignore_index=True
)

candidate_review_bucket_summary = (
    review_combined
    .groupby("review_group", as_index=False)
    .agg(
        players=("player_id", "count"),
        appeared_next_year=("appeared_next_year", "sum"),
        avg_candidate_surplus_gap=("player_surplus_gap", "mean"),
        avg_next_surplus_gap=("next_player_surplus_gap", "mean"),
        avg_candidate_production_score=("production_score", "mean"),
        avg_next_production_score=("next_production_score", "mean"),
    )
)

candidate_review_bucket_summary["appearance_rate"] = (
    candidate_review_bucket_summary["appeared_next_year"] /
    candidate_review_bucket_summary["players"]
)

candidate_review_bucket_summary["summary_type"] = "qualitative_review_bucket"

candidate_review_bucket_summary["interpretation_note"] = (
    "Review buckets are outcome-defined, so this table should not be used "
    "as a model-performance table. Use V4 backtest lift, threshold sensitivity, "
    "and season stability outputs for performance evaluation."
)

candidate_review_bucket_summary = candidate_review_bucket_summary.sort_values(
    "review_group"
)


## PERFORMANCE REFERENCE SUMMARY ##
# This table uses the actual backtest groups as denominators, so these rates
# are interpretable as performance reference metrics.

performance_reference = (
    backtest
    .loc[backtest["group"].isin(["model_candidates", "not_flagged_baseline"])]
    .groupby("group", as_index=False)
    .agg(
        players=("player_id", "count"),
        appeared_next_year=("appeared_next_year", "sum"),
        hits=("hit", "sum"),
        avg_candidate_surplus_gap=("player_surplus_gap", "mean"),
        avg_next_surplus_gap=("next_player_surplus_gap", "mean"),
        avg_candidate_production_score=("production_score", "mean"),
        avg_next_production_score=("next_production_score", "mean"),
    )
)

performance_reference["appearance_rate"] = (
    performance_reference["appeared_next_year"] /
    performance_reference["players"]
)

performance_reference["hit_rate"] = (
    performance_reference["hits"] /
    performance_reference["players"]
)

model_row = performance_reference[
    performance_reference["group"] == "model_candidates"
].iloc[0]

baseline_row = performance_reference[
    performance_reference["group"] == "not_flagged_baseline"
].iloc[0]

performance_lift_reference = pd.DataFrame(
    [
        {
            "comparison": "model_candidates_vs_not_flagged_baseline",
            "players_model": model_row["players"],
            "players_baseline": baseline_row["players"],
            "hit_rate_model": model_row["hit_rate"],
            "hit_rate_baseline": baseline_row["hit_rate"],
            "hit_rate_lift": model_row["hit_rate"] - baseline_row["hit_rate"],
            "appearance_rate_model": model_row["appearance_rate"],
            "appearance_rate_baseline": baseline_row["appearance_rate"],
            "appearance_rate_lift": (
                model_row["appearance_rate"] - baseline_row["appearance_rate"]
            ),
            "avg_next_surplus_gap_model": model_row["avg_next_surplus_gap"],
            "avg_next_surplus_gap_baseline": baseline_row["avg_next_surplus_gap"],
            "next_surplus_gap_lift": (
                model_row["avg_next_surplus_gap"] -
                baseline_row["avg_next_surplus_gap"]
            ),
        }
    ]
)


## PRINT USEFUL VIEWS ##

bucket_summary_view = candidate_review_bucket_summary.copy()
bucket_summary_view = bucket_summary_view.round(3)

print("\nCandidate review bucket summary:")
print(bucket_summary_view.to_string(index=False))

performance_reference_view = performance_lift_reference.copy()
performance_reference_view = performance_reference_view.round(3)

print("\nCandidate review performance reference:")
print(performance_reference_view.to_string(index=False))

print_preview(
    "Top true positives",
    top_true_positives,
    compact_review_columns,
    n=10
)

print_preview(
    "Model misses",
    model_misses,
    compact_review_columns,
    n=10
)

print_preview(
    "Missed opportunities",
    missed_opportunities,
    compact_review_columns,
    n=10
)

print_preview(
    "2025 watchlist",
    watchlist_2025,
    compact_watchlist_columns,
    n=15
)


## SAVE OUTPUTS ##

top_true_positives[
    keep_existing_columns(top_true_positives, review_columns + ["review_group"])
].to_csv(
    f"{OUTPUT_DIR}/candidate_review_top_true_positives.csv",
    index=False
)

model_misses[
    keep_existing_columns(model_misses, review_columns + ["review_group"])
].to_csv(
    f"{OUTPUT_DIR}/candidate_review_model_misses.csv",
    index=False
)

missed_opportunities[
    keep_existing_columns(missed_opportunities, review_columns + ["review_group"])
].to_csv(
    f"{OUTPUT_DIR}/candidate_review_missed_opportunities.csv",
    index=False
)

watchlist_2025[
    keep_existing_columns(
        watchlist_2025,
        watchlist_columns + ["review_group", "watchlist_note"]
    )
].to_csv(
    f"{OUTPUT_DIR}/candidate_review_2025_watchlist.csv",
    index=False
)

candidate_review_bucket_summary.to_csv(
    f"{OUTPUT_DIR}/candidate_review_bucket_summary.csv",
    index=False
)

# Backward-compatible filename, but now without misleading hit-rate columns.
candidate_review_bucket_summary.to_csv(
    f"{OUTPUT_DIR}/candidate_review_summary.csv",
    index=False
)

performance_reference.to_csv(
    f"{OUTPUT_DIR}/candidate_review_performance_reference_by_group.csv",
    index=False
)

performance_lift_reference.to_csv(
    f"{OUTPUT_DIR}/candidate_review_performance_lift_reference.csv",
    index=False
)

review_combined.to_csv(
    f"{OUTPUT_DIR}/candidate_review_combined_historical.csv",
    index=False
)

print("\nSaved candidate review outputs to:", OUTPUT_DIR)