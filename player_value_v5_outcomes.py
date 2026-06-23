# -*- coding: utf-8 -*-
"""
V5 Player Value Outcomes

Goal:
Create next-season outcome labels for the V5 feature table.

This script answers:
For each player-season, did the player appear next year?
Did he remain productive?
Did he retain positive surplus value?
Did he improve?

This is the required input for the V5 matched backtest.

@author: hannah
"""

import os
import pandas as pd

## SETTING UP ##
INPUT_FILE = "outputs_v5/features/player_season_features_v5.csv"

OUTCOME_DIR = "outputs_v5/outcomes"
WATCHLIST_DIR = "outputs_v5/watchlists"

OUTCOME_FILE = f"{OUTCOME_DIR}/player_season_outcomes_v5.csv"
VALIDATION_FILE = f"{OUTCOME_DIR}/historical_validation_rows_v5.csv"
SUMMARY_BY_SEASON_FILE = f"{OUTCOME_DIR}/v5_candidate_summary_by_season.csv"
SUMMARY_BY_POSITION_FILE = f"{OUTCOME_DIR}/v5_candidate_summary_by_position.csv"
WATCHLIST_FILE = f"{WATCHLIST_DIR}/2026_candidate_pool_v5.csv"

SURPLUS_GAP_THRESHOLD = 5

os.makedirs(OUTCOME_DIR, exist_ok=True)
os.makedirs(WATCHLIST_DIR, exist_ok=True)

# Helper functions
def normalize_bool(series):
    if series.dtype == bool:
        return series

    return (
        series
        .astype("string")
        .str.lower()
        .str.strip()
        .isin(["true", "1", "yes", "y"])
    )

def make_nullable_flag(condition, eval_mask):
    condition = pd.Series(condition, index=eval_mask.index).fillna(False)

    out = pd.Series(pd.NA, index=eval_mask.index, dtype="Int64")
    out.loc[eval_mask] = condition.loc[eval_mask].astype(int)

    return out

def summarize_candidate_vs_noncandidate(df, group_cols):
    summary = (
        df
        .groupby(group_cols + ["is_v5_default_candidate"], dropna=False)
        .agg(
            rows=("player_id", "size"),
            appeared_next_year_rate=("appeared_next_year", "mean"),
            primary_v5_hit_rate=("primary_v5_hit", "mean"),
            secondary_v5_hit_rate=("secondary_v5_hit", "mean"),
            retained_positive_surplus_rate=("retained_positive_surplus", "mean"),
            improved_production_score_rate=("improved_production_score", "mean"),
            improved_production_percentile_rate=("improved_production_percentile", "mean"),
            next_year_top_half_position_rate=("next_year_top_half_position", "mean"),
            next_year_meaningful_regular_role_rate=("next_year_meaningful_regular_role", "mean"),
        ).reset_index())
    return summary

## FEATURES FILE ##
features = pd.read_csv(INPUT_FILE)

features["season"] = pd.to_numeric(features["season"], errors="coerce").astype("Int64")

print("Input V5 feature table:", features.shape)

duplicate_player_seasons = features.duplicated(["season", "player_id"]).sum()
duplicate_player_season_positions = features.duplicated(
    ["season", "player_id", "position_final"]
).sum()

print("Duplicate season-player rows:", duplicate_player_seasons)
print("Duplicate season-player-position rows:", duplicate_player_season_positions)

assert duplicate_player_seasons == 0, "Expected one row per season-player."

## CURRENT-YEAR PERCENTILES ##
features["production_score"] = pd.to_numeric(
    features["production_score"],
    errors="coerce"
)

features["player_surplus_gap"] = pd.to_numeric(
    features["player_surplus_gap"],
    errors="coerce"
)

features["production_percentile_position"] = (
    features
    .groupby(["season", "position_final"])["production_score"]
    .rank(pct=True, ascending=True)
)

features["surplus_percentile_position"] = (
    features
    .groupby(["season", "position_final"])["player_surplus_gap"]
    .rank(pct=True, ascending=True)
)


## V5 DEFAULT CANDIDATES ##
features["is_likely_rookie_contract_bool"] = normalize_bool(
    features["is_likely_rookie_contract"]
)

features["is_v5_default_candidate"] = (
    features["is_likely_rookie_contract_bool"]
    & (features["player_surplus_gap"] >= SURPLUS_GAP_THRESHOLD)
).astype(int)

features["is_wr_case_study_candidate"] = (
    features["position_final"].eq("WR")
    & features["is_v5_default_candidate"].eq(1)
).astype(int)

print("\nV5 default candidates:")
print(features["is_v5_default_candidate"].value_counts(dropna=False))

print("\nWR case-study candidates:")
print(features["is_wr_case_study_candidate"].value_counts(dropna=False))

## NEXT YEAR LOOK UP TABLE ##
next_year_cols = [
    "season",
    "player_id",
    "position_final",
    "team",
    "production_score",
    "production_percentile_position",
    "player_surplus_gap",
    "surplus_percentile_position",
    "production_rank_position",
    "cost_rank_position",
    "player_surplus_rank",
    "reg_snap_games",
    "reg_offense_snaps",
    "reg_avg_offense_snap_pct",
    "reg_games_off_snap_50_plus",
    "reg_games_off_snap_70_plus",
    "playoff_snap_games",
    "playoff_offense_snaps",
    "playoff_avg_offense_snap_pct",
    "played_regular_season",
    "played_playoffs",
]

next_year_cols = [c for c in next_year_cols if c in features.columns]

next_year = features[next_year_cols].copy()

# Note: shifting next year rows back 1 year so 2022 data joins to 2021 rows, etc.
next_year["season"] = (next_year["season"].astype(int) - 1).astype("Int64")

rename_next_year_cols = {
    c: f"next_year_{c}"
    for c in next_year_cols
    if c not in ["season", "player_id"]
}

next_year = next_year.rename(columns=rename_next_year_cols)

## NEXT YEAR OUTCOMES MERGING ##
outcomes = features.merge(
    next_year,
    on=["season", "player_id"],
    how="left",
    validate="one_to_one",
)

max_season = int(features["season"].max())

outcomes["has_next_season_in_dataset"] = (
    outcomes["season"].astype(int) < max_season
).astype(int)

eval_mask = outcomes["has_next_season_in_dataset"].eq(1)

## OUTCOME LABELS ##
outcomes["appeared_next_year"] = make_nullable_flag(
    outcomes["next_year_production_score"].notna(),
    eval_mask
)

outcomes["next_year_same_position"] = make_nullable_flag(
    outcomes["position_final"].eq(outcomes["next_year_position_final"]),
    eval_mask
)

outcomes["retained_positive_surplus"] = make_nullable_flag(
    outcomes["next_year_player_surplus_gap"] > 0,
    eval_mask
)

outcomes["improved_production_score"] = make_nullable_flag(
    outcomes["next_year_production_score"] > outcomes["production_score"],
    eval_mask
)

outcomes["improved_production_percentile"] = make_nullable_flag(
    outcomes["next_year_production_percentile_position"]
    > outcomes["production_percentile_position"],
    eval_mask
)

outcomes["next_year_top_half_position"] = make_nullable_flag(
    outcomes["next_year_production_percentile_position"] >= 0.50,
    eval_mask
)

outcomes["next_year_top_third_position"] = make_nullable_flag(
    outcomes["next_year_production_percentile_position"] >= 0.67,
    eval_mask
)

if {
    "next_year_reg_snap_games",
    "next_year_reg_avg_offense_snap_pct",
}.issubset(outcomes.columns):

    outcomes["next_year_meaningful_regular_role"] = make_nullable_flag(
        (outcomes["next_year_reg_snap_games"].fillna(0) >= 8)
        & (outcomes["next_year_reg_avg_offense_snap_pct"].fillna(0) >= 0.25),
        eval_mask
    )

else:
    outcomes["next_year_meaningful_regular_role"] = pd.Series(
        pd.NA,
        index=outcomes.index,
        dtype="Int64"
    )
    
# Primary = next year top-half production w/in position
# Secondary = next year retained positive surplus
outcomes["primary_v5_hit"] = outcomes["next_year_top_half_position"]
outcomes["secondary_v5_hit"] = outcomes["retained_positive_surplus"]

## OUTCOME TABLE ##
outcomes.to_csv(OUTCOME_FILE, index=False)

print(OUTCOME_FILE)
print(outcomes.shape)

historical_validation = outcomes[
    outcomes["has_next_season_in_dataset"].eq(1)
].copy()

## PRINTING SUMMARIES ##
summary_by_season = summarize_candidate_vs_noncandidate(
    historical_validation,
    group_cols=["season"]
)

summary_by_position = summarize_candidate_vs_noncandidate(
    historical_validation,
    group_cols=["position_final"]
)

summary_by_season.to_csv(SUMMARY_BY_SEASON_FILE, index=False)
summary_by_position.to_csv(SUMMARY_BY_POSITION_FILE, index=False)

print(SUMMARY_BY_SEASON_FILE)

print(SUMMARY_BY_POSITION_FILE)

print(summary_by_season)

print(summary_by_position)

## SAVING 2026 WATCHLIST INPUT ##
watchlist_season = max_season

watchlist_cols = [
    "season",
    "player_id",
    "player_name",
    "team",
    "position_final",
    "production_score",
    "production_percentile_position",
    "cap_number",
    "cash_paid",
    "draft_year",
    "draft_round",
    "draft_pick",
    "draft_capital_bucket",
    "years_since_drafted",
    "estimated_contract_stage",
    "is_likely_rookie_contract",
    "production_rank_position",
    "cost_rank_position",
    "player_surplus_gap",
    "surplus_percentile_position",
    "player_surplus_rank",
    "reg_snap_games",
    "reg_offense_snaps",
    "reg_avg_offense_snap_pct",
    "reg_games_off_snap_50_plus",
    "reg_games_off_snap_70_plus",
    "playoff_snap_games",
    "playoff_offense_snaps",
    "playoff_avg_offense_snap_pct",
    "played_playoffs",
    "injury_report_weeks",
    "out_weeks",
    "practice_dnp_weeks",
    "limited_practice_weeks",
    "was_on_injury_report",
    "is_v5_default_candidate",
    "is_wr_case_study_candidate",
]

watchlist_cols = [c for c in watchlist_cols if c in outcomes.columns]

watchlist = (
    outcomes[
        outcomes["season"].astype(int).eq(watchlist_season)
        & outcomes["is_v5_default_candidate"].eq(1)
    ][watchlist_cols]
    .copy()
    .sort_values(
        ["position_final", "player_surplus_gap", "production_score"],
        ascending=[True, False, False]
    )
)

watchlist.to_csv(WATCHLIST_FILE, index=False)

print("\nSaved 2026 candidate pool:")
print(WATCHLIST_FILE)
print(watchlist.shape)

print("\nTop 20 2026 candidate pool rows:")
print(
    watchlist[
        [
            "season",
            "player_name",
            "team",
            "position_final",
            "player_surplus_gap",
            "production_score",
            "reg_snap_games",
            "reg_avg_offense_snap_pct",
        ]
    ].head(20)
)

ROOKIE_ONLY_SUMMARY_FILE = f"{OUTCOME_DIR}/v5_candidate_summary_rookie_contract_only.csv"

rookie_validation = historical_validation[
    historical_validation["is_likely_rookie_contract_bool"].eq(True)
].copy()

rookie_only_summary = (
    rookie_validation
    .groupby("is_v5_default_candidate")
    .agg(
        rows=("player_id", "size"),
        appeared_next_year_rate=("appeared_next_year", "mean"),
        primary_v5_hit_rate=("primary_v5_hit", "mean"),
        secondary_v5_hit_rate=("secondary_v5_hit", "mean"),
        retained_positive_surplus_rate=("retained_positive_surplus", "mean"),
        improved_production_score_rate=("improved_production_score", "mean"),
        improved_production_percentile_rate=("improved_production_percentile", "mean"),
        next_year_top_half_position_rate=("next_year_top_half_position", "mean"),
        next_year_meaningful_regular_role_rate=("next_year_meaningful_regular_role", "mean"),
    )
    .reset_index()
)

rookie_only_summary.to_csv(ROOKIE_ONLY_SUMMARY_FILE, index=False)
