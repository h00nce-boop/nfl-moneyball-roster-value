# -*- coding: utf-8 -*-
"""
V4 Threshold Sensitivity

Goal:
Test whether the surplus-gap threshold is meaningful.

Instead of only using player_surplus_gap >= 5, this script tests several
thresholds and compares flagged rookie-contract players against the
rookie-contract players the model passed on.

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

INPUT_FILE = "outputs_v4/player_value_2021_2025_player_season_clean.csv"
OUTPUT_DIR = "outputs_v4/backtests"

os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv(INPUT_FILE)

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)
pd.set_option("display.max_rows", 100)

print("Loaded clean player-season file:", df.shape)


## BASELINE POOL ##

candidate_seasons = [2021, 2022, 2023, 2024]
thresholds = [0, 3, 5, 10, 15, 20]

baseline_pool = df[
    (df["season"].isin(candidate_seasons)) &
    (df["is_likely_rookie_contract"] == True) &
    (df["overall_confidence"] == "high")
].copy()

print("\nBaseline pool:", baseline_pool.shape)
print(baseline_pool["position_final"].value_counts())


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

def run_backtest(group, group_name, threshold):
    group = group.copy()
    group["candidate_season"] = group["season"]

    result = group.merge(
        next_year,
        on=["candidate_season", "player_id", "position_final"],
        how="left"
    )

    result["group"] = group_name
    result["threshold"] = threshold

    result["appeared_next_year"] = result["next_production_score"].notna()

    result["remained_positive_surplus"] = (
        result["next_player_surplus_gap"] > 0
    )

    result["remained_strong_surplus"] = (
        result["next_player_surplus_gap"] >= threshold
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


## OPTIONAL CHECKPOINT: TEST THRESHOLD 5 ONLY ##

# test_threshold = 5
#
# model_candidates = baseline_pool[
#     baseline_pool["player_surplus_gap"] >= test_threshold
# ].copy()
#
# not_flagged_baseline = baseline_pool[
#     baseline_pool["player_surplus_gap"] < test_threshold
# ].copy()
#
# print("\nTest threshold:", test_threshold)
# print("Model candidates:", model_candidates.shape)
# print("Not flagged:", not_flagged_baseline.shape)
#
# candidate_results = run_backtest(
#     model_candidates,
#     "model_candidates",
#     test_threshold
# )
#
# not_flagged_results = run_backtest(
#     not_flagged_baseline,
#     "not_flagged_baseline",
#     test_threshold
# )
#
# test_combined = pd.concat(
#     [candidate_results, not_flagged_results],
#     ignore_index=True
# )
#
# print("\nTest combined:", test_combined.shape)
# print(test_combined["group"].value_counts())
#
# test_summary = (
#     test_combined
#     .groupby(["threshold", "group", "position_final"], as_index=False)
#     .agg(
#         players=("player_id", "count"),
#         appeared_next_year=("appeared_next_year", "sum"),
#         hits=("hit", "sum"),
#         avg_surplus_gap=("player_surplus_gap", "mean"),
#         avg_next_surplus_gap=("next_player_surplus_gap", "mean"),
#         avg_production_score=("production_score", "mean"),
#         avg_next_production_score=("next_production_score", "mean"),
#     )
# )
#
# test_summary["appearance_rate"] = (
#     test_summary["appeared_next_year"] / test_summary["players"]
# )
#
# test_summary["hit_rate"] = (
#     test_summary["hits"] / test_summary["players"]
# )
#
# print("\nTest summary:")
# print(test_summary)


## RUN THRESHOLD LOOP ##

all_results = []
threshold_count_rows = []

for threshold in thresholds:
    model_candidates = baseline_pool[
        baseline_pool["player_surplus_gap"] >= threshold
    ].copy()

    not_flagged_baseline = baseline_pool[
        baseline_pool["player_surplus_gap"] < threshold
    ].copy()

    threshold_count_rows.append(
        {
            "threshold": threshold,
            "model_candidates": len(model_candidates),
            "not_flagged_baseline": len(not_flagged_baseline),
            "total_players": len(model_candidates) + len(not_flagged_baseline),
        }
    )

    candidate_results = run_backtest(
        model_candidates,
        "model_candidates",
        threshold
    )

    not_flagged_results = run_backtest(
        not_flagged_baseline,
        "not_flagged_baseline",
        threshold
    )

    threshold_results = pd.concat(
        [candidate_results, not_flagged_results],
        ignore_index=True
    )

    all_results.append(threshold_results)

combined = pd.concat(all_results, ignore_index=True)

threshold_counts = pd.DataFrame(threshold_count_rows)

print("\nThreshold candidate counts:")
print(threshold_counts.to_string(index=False))


## SUMMARY BY POSITION ##

summary_by_position = (
    combined
    .groupby(["threshold", "group", "position_final"], as_index=False)
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

summary_by_position["appearance_rate"] = (
    summary_by_position["appeared_next_year"] /
    summary_by_position["players"]
)

summary_by_position["hit_rate"] = (
    summary_by_position["hits"] /
    summary_by_position["players"]
)

# print("\nSummary by position:")
# print(summary_by_position)


## OVERALL SUMMARY ##

summary_overall = (
    combined
    .groupby(["threshold", "group"], as_index=False)
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

summary_overall["position_final"] = "ALL"

summary_overall["appearance_rate"] = (
    summary_overall["appeared_next_year"] /
    summary_overall["players"]
)

summary_overall["hit_rate"] = (
    summary_overall["hits"] /
    summary_overall["players"]
)

summary_all = pd.concat(
    [summary_by_position, summary_overall],
    ignore_index=True
)


## LIFT TABLE ##

model_summary = summary_all[
    summary_all["group"] == "model_candidates"
].copy()

baseline_summary = summary_all[
    summary_all["group"] == "not_flagged_baseline"
].copy()

lift = model_summary.merge(
    baseline_summary,
    on=["threshold", "position_final"],
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

lift["next_production_score_lift"] = (
    lift["avg_next_production_score_model"] -
    lift["avg_next_production_score_baseline"]
)


## USEFUL PRINTED VIEWS ##

overall_view = lift[
    lift["position_final"] == "ALL"
][
    [
        "threshold",
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

overall_view = overall_view.round(3)

print("\nThreshold sensitivity: overall")
print(overall_view.to_string(index=False))


position_view = lift[
    lift["position_final"] != "ALL"
][
    [
        "threshold",
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

position_view = position_view.round(3)

print("\nThreshold sensitivity: by position")
print(position_view.to_string(index=False))


## SAVE OUTPUTS ##

combined.to_csv(
    f"{OUTPUT_DIR}/threshold_sensitivity_combined_results.csv",
    index=False
)

summary_all.to_csv(
    f"{OUTPUT_DIR}/threshold_sensitivity_summary.csv",
    index=False
)

lift.to_csv(
    f"{OUTPUT_DIR}/threshold_sensitivity_lift.csv",
    index=False
)

threshold_counts.to_csv(
    f"{OUTPUT_DIR}/threshold_sensitivity_candidate_counts.csv",
    index=False
)

print("\nSaved threshold sensitivity outputs to:", OUTPUT_DIR)