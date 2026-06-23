# -*- coding: utf-8 -*-
"""
V5 Matched Backtest

Goal:
Test whether the V5 surplus-value candidate signal still shows next-season lift
after comparing candidates to similar rookie-contract peers.

Candidates:
    is_v5_default_candidate == 1

Controls:
    rookie-contract players who were not V5 candidates

Important:
    Do NOT match on player_surplus_gap.
    player_surplus_gap is the signal being tested.
    
@author: hannah
"""

import pandas as pd
import os
import numpy as np

seasons = [2021, 2022, 2023, 2024, 2025]

## SETTING UP ##

INPUT_FILE = "outputs_v5/outcomes/historical_validation_rows_v5.csv"
OUTPUT_DIR = "outputs_v5/backtests/k3"

MATCHED_PAIRS_FILE = f"{OUTPUT_DIR}/matched_pairs_v5.csv"
MATCHED_CANDIDATE_LEVEL_FILE = f"{OUTPUT_DIR}/matched_candidate_level_v5.csv"
MATCHED_LIFT_SUMMARY_FILE = f"{OUTPUT_DIR}/matched_lift_summary_v5.csv"
MATCHED_LIFT_BY_POSITION_FILE = f"{OUTPUT_DIR}/matched_lift_by_position_v5.csv"
MATCHED_LIFT_BY_SEASON_FILE = f"{OUTPUT_DIR}/matched_lift_by_season_v5.csv"
MATCHED_TIER_SUMMARY_FILE = f"{OUTPUT_DIR}/matched_tier_summary_v5.csv"
MATCHED_CONTROL_REUSE_FILE = f"{OUTPUT_DIR}/matched_control_reuse_v5.csv"
UNMATCHED_CANDIDATES_FILE = f"{OUTPUT_DIR}/unmatched_candidates_v5.csv"


os.makedirs(OUTPUT_DIR, exist_ok=True)

# use 3 nearest controls per candidate when available, controls can be reused
K_MATCHES = 3

# exact-match tiers tried in every order 
## season + position kept in tiers to avoid comparing across eras/positions
EXACT_TIERS = [
    (
        "tier_1_same_season_position_draft_bucket_contract_stage",
        ["season", "position_final", "draft_capital_bucket", "estimated_contract_stage"],
    ),
    (
        "tier_2_same_season_position_draft_bucket",
        ["season", "position_final", "draft_capital_bucket"],
    ),
    (
        "tier_3_same_season_position_contract_stage",
        ["season", "position_final", "estimated_contract_stage"],
    ),
    (
        "tier_4_same_season_position",
        ["season", "position_final"],
    ),
]

# compared outcomes
OUTCOME_COLS = [
    "appeared_next_year",
    "primary_v5_hit",
    "secondary_v5_hit",
    "retained_positive_surplus",
    "improved_production_score",
    "improved_production_percentile",
    "next_year_top_half_position",
    "next_year_meaningful_regular_role",
]

# metadata to preserve in matched-pairs file
META_COLS = [
    "season",
    "player_id",
    "player_name",
    "team",
    "position_final",
    "draft_year",
    "draft_round",
    "draft_pick",
    "draft_capital_bucket",
    "years_since_drafted",
    "estimated_contract_stage",
    "production_score",
    "production_percentile_position",
    "cap_number",
    "cash_paid",
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
]

## HELPER FUNCTIONS ##
def normalize_bool(series):
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)

    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce").fillna(0).astype(int).eq(1)

    return (
        series
        .astype("string")
        .str.lower()
        .str.strip()
        .isin(["true", "1", "yes", "y"])
    )


def require_columns(df, cols, label):
    missing = [c for c in cols if c not in df.columns]

    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def add_match_features(df):
    out = df.copy()

    out["match_production_pct"] = pd.to_numeric(
        out["production_percentile_position"],
        errors="coerce"
    ).clip(0, 1)
    
    out["match_reg_avg_offense_snap_pct"] = pd.to_numeric(
        out["reg_avg_offense_snap_pct"],
        errors="coerce"
    ).clip(0, 1)

    out["match_reg_snap_games"] = (
        pd.to_numeric(out["reg_snap_games"], errors="coerce") / 17
    ).clip(0, 1)

    out["reg_offense_snaps"] = pd.to_numeric(
        out["reg_offense_snaps"],
        errors="coerce"
    )

    out["match_reg_offense_snaps_pctile"] = (
        out
        .groupby(["season", "position_final"])["reg_offense_snaps"]
        .rank(pct=True, ascending=True)
    )

    out["years_since_drafted"] = pd.to_numeric(
        out["years_since_drafted"],
        errors="coerce"
    )

    max_years = out["years_since_drafted"].quantile(0.95)

    if pd.isna(max_years) or max_years <= 0:
        max_years = 5

    out["match_years_since_drafted"] = (
        out["years_since_drafted"] / max_years
    ).clip(0, 1)

    match_cols = [
        "match_production_pct",
        "match_reg_avg_offense_snap_pct",
        "match_reg_snap_games",
        "match_reg_offense_snaps_pctile",
        "match_years_since_drafted",
    ]

    for col in match_cols:
        median_value = out[col].median()

        if pd.isna(median_value):
            median_value = 0.5

        out[col] = out[col].fillna(median_value)

    return out


MATCH_WEIGHTS = {

    "match_production_pct": 2.00,

    "match_reg_avg_offense_snap_pct": 1.25,
    "match_reg_snap_games": 1.00,
    "match_reg_offense_snaps_pctile": 1.00,

    "match_years_since_drafted": 0.75,
}


def weighted_distance(candidate_row, control_pool):
    total = np.zeros(len(control_pool), dtype=float)

    for col, weight in MATCH_WEIGHTS.items():
        candidate_value = float(candidate_row[col])
        control_values = control_pool[col].astype(float).to_numpy()

        total += weight * np.square(control_values - candidate_value)

    return np.sqrt(total)


def filter_exact_pool(candidate_row, controls, exact_cols):
    mask = np.ones(len(controls), dtype=bool)

    for col in exact_cols:
        mask = mask & controls[col].eq(candidate_row[col]).to_numpy()

    return controls.loc[mask].copy()


def safe_get(row, col):
    if col in row.index:
        return row[col]

    return np.nan


def summarize_lift(candidate_level, outcome_cols, group_cols=None):

    rows = []

    if group_cols is None:
        grouped = [((), candidate_level)]
        group_cols = []
    else:
        grouped = candidate_level.groupby(group_cols, dropna=False)

    for group_key, group in grouped:
        if not isinstance(group_key, tuple):
            group_key = (group_key,)

        group_info = {
            col: value
            for col, value in zip(group_cols, group_key)
        }

        for outcome in outcome_cols:
            candidate_col = f"candidate_{outcome}"
            control_col = f"matched_control_{outcome}_mean"

            if candidate_col not in group.columns or control_col not in group.columns:
                continue

            candidate_values = pd.to_numeric(group[candidate_col], errors="coerce")
            control_values = pd.to_numeric(group[control_col], errors="coerce")

            valid = candidate_values.notna() & control_values.notna()

            n = int(valid.sum())

            if n == 0:
                candidate_rate = np.nan
                control_rate = np.nan
                lift = np.nan
                se = np.nan
                ci_low = np.nan
                ci_high = np.nan
            else:
                candidate_rate = candidate_values.loc[valid].mean()
                control_rate = control_values.loc[valid].mean()
                diff = candidate_values.loc[valid] - control_values.loc[valid]

                lift = diff.mean()

                if n > 1:
                    se = diff.std(ddof=1) / np.sqrt(n)
                    ci_low = lift - 1.96 * se
                    ci_high = lift + 1.96 * se
                else:
                    se = np.nan
                    ci_low = np.nan
                    ci_high = np.nan

            row = {
                **group_info,
                "outcome": outcome,
                "matched_candidates": n,
                "candidate_rate": candidate_rate,
                "matched_control_rate": control_rate,
                "lift": lift,
                "lift_pp": lift * 100 if pd.notna(lift) else np.nan,
                "lift_se": se,
                "lift_ci_low_pp": ci_low * 100 if pd.notna(ci_low) else np.nan,
                "lift_ci_high_pp": ci_high * 100 if pd.notna(ci_high) else np.nan,
                "relative_lift_pct": (
                    (lift / control_rate) * 100
                    if pd.notna(lift) and pd.notna(control_rate) and control_rate != 0
                    else np.nan
                ),
            }

            rows.append(row)

    return pd.DataFrame(rows)

## READING DATA ##
df = pd.read_csv(INPUT_FILE)

print(df.shape)

require_columns(
    df,
    [
        "season",
        "player_id",
        "player_name",
        "position_final",
        "is_v5_default_candidate",
        "production_percentile_position",
        "reg_snap_games",
        "reg_offense_snaps",
        "reg_avg_offense_snap_pct",
        "years_since_drafted",
    ],
    "historical_validation_rows_v5.csv",
)

require_columns(df, OUTCOME_COLS, "historical_validation_rows_v5.csv")

df = df.reset_index(drop=True)
df["row_id"] = np.arange(len(df))

df["season"] = pd.to_numeric(df["season"], errors="coerce").astype("Int64")

for col in ["position_final", "draft_capital_bucket", "estimated_contract_stage"]:
    if col not in df.columns:
        df[col] = "unknown"

    df[col] = (
        df[col]
        .astype("string")
        .str.strip()
        .fillna("unknown")
        .replace({"": "unknown", "<NA>": "unknown", "nan": "unknown"})
    )

df["is_v5_default_candidate_bool"] = normalize_bool(df["is_v5_default_candidate"])

if "is_likely_rookie_contract_bool" in df.columns:
    df["rookie_contract_bool"] = normalize_bool(df["is_likely_rookie_contract_bool"])
elif "is_likely_rookie_contract" in df.columns:
    df["rookie_contract_bool"] = normalize_bool(df["is_likely_rookie_contract"])
else:
    raise ValueError(
        "Could not find is_likely_rookie_contract_bool or is_likely_rookie_contract."
    )

for col in OUTCOME_COLS:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = add_match_features(df)

## DEFINE CANDIDATES AND CONTROLS ##
candidate_mask = (
    df["is_v5_default_candidate_bool"].eq(True)
    & df["primary_v5_hit"].notna()
)

control_mask = (
    df["rookie_contract_bool"].eq(True)
    & df["is_v5_default_candidate_bool"].eq(False)
    & df["primary_v5_hit"].notna()
)

candidates = df.loc[candidate_mask].copy()
controls = df.loc[control_mask].copy()

print("\nCandidate rows:", len(candidates))
print("Rookie-contract control rows:", len(controls))

print("\nCandidates by season-position:")
print(
    candidates
    .groupby(["season", "position_final"])
    .size()
    .reset_index(name="candidates")
    .sort_values(["season", "position_final"])
)

print("\nControls by season-position:")
print(
    controls
    .groupby(["season", "position_final"])
    .size()
    .reset_index(name="controls")
    .sort_values(["season", "position_final"])
)

if len(candidates) == 0:
    raise ValueError("No V5 candidates found.")

if len(controls) == 0:
    raise ValueError("No rookie-contract non-candidate controls found.")
    
## MATCHING CANDIDATES TO CONTROLS ##
pairs = []
unmatched_candidates = []

for _, candidate in candidates.iterrows():
    found_match = False

    for tier_name, exact_cols in EXACT_TIERS:
        control_pool = filter_exact_pool(candidate, controls, exact_cols)

        if control_pool.empty:
            continue

        control_pool = control_pool.copy()
        control_pool["match_distance"] = weighted_distance(candidate, control_pool)

        control_pool = (
            control_pool
            .sort_values(
                ["match_distance", "player_id", "player_name"],
                ascending=[True, True, True]
            )
            .head(K_MATCHES)
        )

        for match_rank, (_, control) in enumerate(control_pool.iterrows(), start=1):
            pair_row = {
                "candidate_row_id": candidate["row_id"],
                "control_row_id": control["row_id"],
                "match_rank": match_rank,
                "match_tier": tier_name,
                "match_distance": control["match_distance"],
                "k_requested": K_MATCHES,
                "controls_reused": True,
            }

            for col in META_COLS:
                pair_row[f"candidate_{col}"] = safe_get(candidate, col)
                pair_row[f"control_{col}"] = safe_get(control, col)

            for col in MATCH_WEIGHTS.keys():
                pair_row[f"candidate_{col}"] = safe_get(candidate, col)
                pair_row[f"control_{col}"] = safe_get(control, col)

            for outcome in OUTCOME_COLS:
                cand_value = safe_get(candidate, outcome)
                ctrl_value = safe_get(control, outcome)

                pair_row[f"candidate_{outcome}"] = cand_value
                pair_row[f"control_{outcome}"] = ctrl_value

                if pd.notna(cand_value) and pd.notna(ctrl_value):
                    pair_row[f"diff_{outcome}"] = cand_value - ctrl_value
                else:
                    pair_row[f"diff_{outcome}"] = np.nan

            pairs.append(pair_row)

        found_match = True
        break

    if not found_match:
        unmatched_row = {
            "candidate_row_id": candidate["row_id"],
        }

        for col in META_COLS:
            unmatched_row[col] = safe_get(candidate, col)

        unmatched_candidates.append(unmatched_row)


pairs = pd.DataFrame(pairs)

unmatched_cols = ["candidate_row_id"] + META_COLS

unmatched_candidates = pd.DataFrame(
    unmatched_candidates,
    columns=unmatched_cols
)

if pairs.empty:
    raise ValueError("No matched pairs created. Check exact-match tiers and control pool.")

pairs.to_csv(MATCHED_PAIRS_FILE, index=False)
unmatched_candidates.to_csv(UNMATCHED_CANDIDATES_FILE, index=False)

print(MATCHED_PAIRS_FILE)
print(pairs.shape)

print(UNMATCHED_CANDIDATES_FILE)
print(unmatched_candidates.shape)

## CANDIDATE-LEVEL MATCHED RESULTS ##
candidate_agg = {
    "control_row_id": ("control_row_id", "size"),
    "match_distance_avg": ("match_distance", "mean"),
    "match_distance_min": ("match_distance", "min"),
    "match_distance_max": ("match_distance", "max"),
    "match_tier": ("match_tier", "first"),
}

for col in META_COLS:
    pair_col = f"candidate_{col}"
    if pair_col in pairs.columns:
        candidate_agg[pair_col] = (pair_col, "first")

for outcome in OUTCOME_COLS:
    candidate_col = f"candidate_{outcome}"
    control_col = f"control_{outcome}"

    if candidate_col in pairs.columns:
        candidate_agg[candidate_col] = (candidate_col, "first")

    if control_col in pairs.columns:
        candidate_agg[f"matched_control_{outcome}_mean"] = (control_col, "mean")

candidate_level = (
    pairs
    .groupby("candidate_row_id", as_index=False)
    .agg(**candidate_agg)
    .rename(columns={"control_row_id": "n_matched_controls"})
)

for outcome in OUTCOME_COLS:
    candidate_col = f"candidate_{outcome}"
    control_mean_col = f"matched_control_{outcome}_mean"

    if candidate_col in candidate_level.columns and control_mean_col in candidate_level.columns:
        candidate_level[f"lift_{outcome}"] = (
            candidate_level[candidate_col] - candidate_level[control_mean_col]
        )

candidate_level.to_csv(MATCHED_CANDIDATE_LEVEL_FILE, index=False)

print(MATCHED_CANDIDATE_LEVEL_FILE)
print(candidate_level.shape)

## LIFT SUMMARIES ##
summary = summarize_lift(
    candidate_level,
    OUTCOME_COLS,
    group_cols=None,
)

by_position = summarize_lift(
    candidate_level,
    OUTCOME_COLS,
    group_cols=["candidate_position_final"],
)

by_season = summarize_lift(
    candidate_level,
    OUTCOME_COLS,
    group_cols=["candidate_season"],
)

summary.to_csv(MATCHED_LIFT_SUMMARY_FILE, index=False)
by_position.to_csv(MATCHED_LIFT_BY_POSITION_FILE, index=False)
by_season.to_csv(MATCHED_LIFT_BY_SEASON_FILE, index=False)

print(MATCHED_LIFT_SUMMARY_FILE)

print(MATCHED_LIFT_BY_POSITION_FILE)

print(MATCHED_LIFT_BY_SEASON_FILE)

## MATCH QUALITY/TIER SUMMARY ##
tier_summary = (
    candidate_level
    .groupby("match_tier", dropna=False)
    .agg(
        matched_candidates=("candidate_row_id", "size"),
        avg_matched_controls=("n_matched_controls", "mean"),
        avg_match_distance=("match_distance_avg", "mean"),
        median_match_distance=("match_distance_avg", "median"),
        primary_v5_candidate_rate=("candidate_primary_v5_hit", "mean"),
        primary_v5_matched_control_rate=("matched_control_primary_v5_hit_mean", "mean"),
    )
    .reset_index()
)

tier_summary["primary_v5_lift"] = (
    tier_summary["primary_v5_candidate_rate"]
    - tier_summary["primary_v5_matched_control_rate"]
)

tier_summary["primary_v5_lift_pp"] = tier_summary["primary_v5_lift"] * 100

tier_summary.to_csv(MATCHED_TIER_SUMMARY_FILE, index=False)

print(MATCHED_TIER_SUMMARY_FILE)
print(tier_summary)

## CONTROL REUSE SUMMARY ##
control_reuse = (
    pairs
    .groupby(
        [
            "control_row_id",
            "control_season",
            "control_player_id",
            "control_player_name",
            "control_team",
            "control_position_final",
        ],
        dropna=False
    )
    .agg(
        times_used=("candidate_row_id", "size"),
        avg_match_distance=("match_distance", "mean"),
    )
    .reset_index()
    .sort_values("times_used", ascending=False)
)

control_reuse.to_csv(MATCHED_CONTROL_REUSE_FILE, index=False)

print(MATCHED_CONTROL_REUSE_FILE)
print(control_reuse.head(20))

## FINAL PRINTS ##
total_candidates = len(candidates)
matched_candidates = candidate_level["candidate_row_id"].nunique()
unmatched_count = len(unmatched_candidates)

print("\nMatched candidate coverage:")
print(f"Total candidates:   {total_candidates}")
print(f"Matched candidates: {matched_candidates}")
print(f"Unmatched:          {unmatched_count}")
print(f"Match rate:         {matched_candidates / total_candidates:.1%}")

print("\nMain matched lift summary:")
main_outcomes = [
    "primary_v5_hit",
    "secondary_v5_hit",
    "appeared_next_year",
    "next_year_meaningful_regular_role",
]

print(
    summary[summary["outcome"].isin(main_outcomes)]
    .sort_values("outcome")
    .to_string(index=False)
)

print("\nPrimary V5 hit lift by position:")
print(
    by_position[by_position["outcome"].eq("primary_v5_hit")]
    .sort_values("lift_pp", ascending=False)
    .to_string(index=False)
)

print("\nPrimary V5 hit lift by season:")
print(
    by_season[by_season["outcome"].eq("primary_v5_hit")]
    .sort_values("candidate_season")
    .to_string(index=False)
)