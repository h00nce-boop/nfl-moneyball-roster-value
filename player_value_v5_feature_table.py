# -*- coding: utf-8 -*-
"""
V5 Player Value Feature Builder

Goal:
Tests whether NFL Moneyball's rookie-contract surplus signal survives
after controlling for variables such as:
    
- position
- season
- draft capital
- contract stage
- opportunity
- injury/availability

This script builds the V5 player-season feature table.

Key design choice:
Regular-season snap context and playoff snap context are kept separate.

@author: hannah
"""

import pandas as pd
import os
import nflreadpy as nfl

seasons = [2021, 2022, 2023, 2024, 2025]

## READING EXISTING DATA ##

INPUT_FILE = "outputs_v4/player_value_2021_2025_player_season_clean.csv"
OUTPUT_DIR = "outputs_v5/features"
OUTPUT_FILE = f"{OUTPUT_DIR}/player_season_features_v5.csv"

os.makedirs(OUTPUT_DIR, exist_ok=True)

data = pd.read_csv(INPUT_FILE)

# Helper functions
def to_pandas(data):
    if hasattr(data, "to_pandas"):
        return data.to_pandas()
    return data

def clean_id(series):
    return(series.astype("string")
           .str.strip()
           .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA, "<NA>": pd.NA}))

def pct_to_decimal(series):
    s = (series.astype("string")
         .str.replace("%", "", regex=False)
         .str.strip())
    s = pd.to_numeric(s, errors="coerce")
    return s.where(s <= 1, s/100)

def classify_snap_season_type(df):
    out = df.copy()

    source_col = None

    if "season_type" in out.columns:
        source_col = "season_type"
    elif "game_type" in out.columns:
        source_col = "game_type"

    if source_col is not None:
        raw = out[source_col].astype("string").str.upper().str.strip()

        regular_values = {
            "REG",
            "REGULAR",
            "REGULAR_SEASON",
        }

        playoff_values = {
            "POST",
            "POSTSEASON",
            "PLAYOFF",
            "PLAYOFFS",
            "WC",
            "WILD_CARD",
            "WILDCARD",
            "DIV",
            "DIVISIONAL",
            "CON",
            "CONF",
            "CONFERENCE",
            "SB",
            "SUPER_BOWL",
            "SUPERBOWL",
        }

        out["snap_season_type"] = "unknown"
        out.loc[raw.isin(regular_values), "snap_season_type"] = "regular"
        out.loc[raw.isin(playoff_values), "snap_season_type"] = "playoff"

    else:
        out["snap_season_type"] = "unknown"

    if "week" in out.columns:
        unknown_mask = out["snap_season_type"].eq("unknown")

        out.loc[
            unknown_mask & out["week"].between(1, 18),
            "snap_season_type"
        ] = "regular"

        out.loc[
            unknown_mask & out["week"].gt(18),
            "snap_season_type"
        ] = "playoff"

    return out

def aggregate_snaps_by_type(snaps_df, snap_type, prefix):
    df = snaps_df[snaps_df["snap_season_type"].eq(snap_type)].copy()

    if df.empty:
        return pd.DataFrame(columns=["season", "player_id"])

    if "offense_pct" in df.columns:
        df["game_off_snap_50_plus"] = (df["offense_pct"] >= 0.50).astype(int)
        df["game_off_snap_70_plus"] = (df["offense_pct"] >= 0.70).astype(int)

    if "defense_pct" in df.columns:
        df["game_def_snap_50_plus"] = (df["defense_pct"] >= 0.50).astype(int)

    snap_aggs = {}

    if "game_id" in df.columns:
        snap_aggs[f"{prefix}_snap_games"] = ("game_id", "nunique")
    elif "week" in df.columns:
        snap_aggs[f"{prefix}_snap_games"] = ("week", "nunique")

    if "team" in df.columns:
        snap_aggs[f"{prefix}_teams_with_snaps"] = ("team", "nunique")

    if "offense_snaps" in df.columns:
        snap_aggs[f"{prefix}_offense_snaps"] = ("offense_snaps", "sum")

    if "defense_snaps" in df.columns:
        snap_aggs[f"{prefix}_defense_snaps"] = ("defense_snaps", "sum")

    if "st_snaps" in df.columns:
        snap_aggs[f"{prefix}_special_teams_snaps"] = ("st_snaps", "sum")

    if "offense_pct" in df.columns:
        snap_aggs[f"{prefix}_avg_offense_snap_pct"] = ("offense_pct", "mean")
        snap_aggs[f"{prefix}_max_offense_snap_pct"] = ("offense_pct", "max")
        snap_aggs[f"{prefix}_games_off_snap_50_plus"] = ("game_off_snap_50_plus", "sum")
        snap_aggs[f"{prefix}_games_off_snap_70_plus"] = ("game_off_snap_70_plus", "sum")

    if "defense_pct" in df.columns:
        snap_aggs[f"{prefix}_avg_defense_snap_pct"] = ("defense_pct", "mean")
        snap_aggs[f"{prefix}_max_defense_snap_pct"] = ("defense_pct", "max")
        snap_aggs[f"{prefix}_games_def_snap_50_plus"] = ("game_def_snap_50_plus", "sum")

    if "st_pct" in df.columns:
        snap_aggs[f"{prefix}_avg_st_snap_pct"] = ("st_pct", "mean")
        snap_aggs[f"{prefix}_max_st_snap_pct"] = ("st_pct", "max")

    out = (
        df
        .dropna(subset=["season", "player_id"])
        .groupby(["season", "player_id"], as_index=False)
        .agg(**snap_aggs)
    )

    return out

## RAW DATA ##
snaps = to_pandas(nfl.load_snap_counts(seasons))
injuries = to_pandas(nfl.load_injuries(seasons))
players = to_pandas(nfl.load_players())

data["player_id"] = clean_id(data["player_id"])
data["season"] = pd.to_numeric(data["season"], errors="coerce").astype("Int64")


## ID MAP BEFORE JOIN ##
### gsis_id and pfr_id

id_map = (players[["gsis_id", "pfr_id"]].copy()
          .rename(columns={
              "gsis_id": "player_id",
              "pfr_id": "pfr_player_id",}))


id_map["player_id"] = clean_id(id_map["player_id"])
id_map["pfr_player_id"] = clean_id(id_map["pfr_player_id"])

id_map = (id_map.dropna(subset=["player_id", "pfr_player_id"])
          .drop_duplicates(subset=["pfr_player_id"]))

print(id_map.shape)


## AGGREGATING SNAPS ##
snaps_clean = snaps.copy()

snaps_clean["season"] = pd.to_numeric(snaps_clean["season"], errors="coerce").astype("Int64")
snaps_clean["pfr_player_id"] = clean_id(snaps_clean["pfr_player_id"])

if "week" in snaps_clean.columns:
    snaps_clean["week"] = pd.to_numeric(snaps_clean["week"], errors="coerce")

for col in ["offense_snaps", "defense_snaps", "st_snaps"]:
    if col in snaps_clean.columns:
        snaps_clean[col] = pd.to_numeric(snaps_clean[col], errors="coerce").fillna(0)

for col in ["offense_pct", "defense_pct", "st_pct"]:
    if col in snaps_clean.columns:
        snaps_clean[col] = pct_to_decimal(snaps_clean[col])

snaps_clean = snaps_clean.merge(
    id_map,
    on="pfr_player_id",
    how="left",
    validate="many_to_one",
)

## UNMAPPED SNAPS ##
unmapped_snaps = (snaps_clean[snaps_clean["player_id"].isna()]
                  [["season", "player", "pfr_player_id"]]
                  .drop_duplicates().sort_values(["season", "player"]))

print(len(unmapped_snaps))

unmapped_snaps.to_csv(
    f"{OUTPUT_DIR}/debug_unmapped_snaps.csv",
    index=False
)


# Checkpoint - manual review
data_name_check = data[["season", "player_name", "position_final"]].copy()
data_name_check["player_name_clean"] = (
    data_name_check["player_name"]
    .astype("string")
    .str.lower()
    .str.replace(r"[^a-z\s]", "", regex=True)
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

unmapped_name_check = unmapped_snaps.copy()
unmapped_name_check["player_name_clean"] = (
    unmapped_name_check["player"]
    .astype("string")
    .str.lower()
    .str.replace(r"[^a-z\s]", "", regex=True)
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

possible_unmapped_overlap = unmapped_name_check.merge(
    data_name_check,
    on=["season", "player_name_clean"],
    how="inner"
)

print("\nPossible unmapped snap players that appear in base data by name:")
print(possible_unmapped_overlap.head(30))
print("Possible overlap rows:", len(possible_unmapped_overlap))

possible_unmapped_overlap.to_csv(
    f"{OUTPUT_DIR}/debug_possible_unmapped_snap_overlap.csv",
    index=False
)


## SPLITTING AND AGGREGATING SNAPS - REG SZN AND PLAYOFF SZN ##
snaps_clean = classify_snap_season_type(snaps_clean)

print("\nSnap season type counts:")
print(snaps_clean["snap_season_type"].value_counts(dropna=False))

reg_snaps_season = aggregate_snaps_by_type(
    snaps_clean,
    snap_type="regular",
    prefix="reg",
)

playoff_snaps_season = aggregate_snaps_by_type(
    snaps_clean,
    snap_type="playoff",
    prefix="playoff",
)

print(reg_snaps_season.shape)
print(reg_snaps_season.head())

print(playoff_snaps_season.shape)
print(playoff_snaps_season.head())

# Checkpoint - checking regular snap coverage
if "reg_snap_games" in reg_snaps_season.columns:
    reg_snap_coverage_check = data[
        ["season", "player_id", "player_name", "position_final"]
    ].merge(
        reg_snaps_season[["season", "player_id", "reg_snap_games"]],
        on=["season", "player_id"],
        how="left"
    )

    missing_reg_snap_coverage = reg_snap_coverage_check[
        reg_snap_coverage_check["reg_snap_games"].isna()
    ].copy()

    print(len(missing_reg_snap_coverage))

    if len(missing_reg_snap_coverage) > 0:
        print(
            missing_reg_snap_coverage
            .groupby(["season", "position_final"])
            .size()
            .reset_index(name="missing_rows")
            .sort_values(["season", "missing_rows"], ascending=[True, False])
        )

    missing_reg_snap_coverage.to_csv(
        f"{OUTPUT_DIR}/debug_base_rows_missing_reg_snap_data.csv",
        index=False
    )

## AGGREGATING INJURIES ##
injuries_clean = injuries.copy()

injuries_clean["season"] = pd.to_numeric(injuries_clean["season"], errors="coerce").astype("Int64")
injuries_clean["player_id"] = clean_id(injuries_clean["gsis_id"])

if "week" in injuries_clean.columns:
    injuries_clean["week"] = pd.to_numeric(injuries_clean["week"], errors="coerce")

if "season_type" in injuries_clean.columns:
    injuries_clean = injuries_clean[
        injuries_clean["season_type"].astype("string").str.upper().eq("REG")
    ].copy()

print("\nRaw injuries by season after REG filter:")
print(injuries_clean["season"].value_counts(dropna=False).sort_index())

print("\nNon-null injury gsis_id by season after REG filter:")
print(
    injuries_clean
    .assign(has_gsis_id=injuries_clean["player_id"].notna())
    .groupby("season")["has_gsis_id"]
    .sum()
)

if "report_status" in injuries_clean.columns:
    status = injuries_clean["report_status"].astype("string").str.lower()
else:
    status = pd.Series("", index=injuries_clean.index, dtype="string")

if "practice_status" in injuries_clean.columns:
    practice = injuries_clean["practice_status"].astype("string").str.lower()
else:
    practice = pd.Series("", index=injuries_clean.index, dtype="string")

injuries_clean["injury_out_flag"] = status.str.contains(r"\bout\b", na=False).astype(int)
injuries_clean["injury_doubtful_flag"] = status.str.contains("doubtful", na=False).astype(int)
injuries_clean["injury_questionable_flag"] = status.str.contains("questionable", na=False).astype(int)

injuries_clean["practice_dnp_flag"] = practice.str.contains("did not|dnp", na=False).astype(int)
injuries_clean["practice_limited_flag"] = practice.str.contains("limited", na=False).astype(int)

weekly_injury_aggs = {
    "injury_out_flag": ("injury_out_flag", "max"),
    "injury_doubtful_flag": ("injury_doubtful_flag", "max"),
    "injury_questionable_flag": ("injury_questionable_flag", "max"),
    "practice_dnp_flag": ("practice_dnp_flag", "max"),
    "practice_limited_flag": ("practice_limited_flag", "max"),
}

if "report_primary_injury" in injuries_clean.columns:
    weekly_injury_aggs["primary_injury_count"] = (
        "report_primary_injury",
        lambda x: x.dropna().nunique()
    )

injuries_weekly = (
    injuries_clean
    .dropna(subset=["season", "player_id", "week"])
    .groupby(["season", "player_id", "week"], as_index=False)
    .agg(**weekly_injury_aggs)
)

injury_season_aggs = {
    "injury_report_weeks": ("week", "nunique"),
    "out_weeks": ("injury_out_flag", "sum"),
    "doubtful_weeks": ("injury_doubtful_flag", "sum"),
    "questionable_weeks": ("injury_questionable_flag", "sum"),
    "practice_dnp_weeks": ("practice_dnp_flag", "sum"),
    "limited_practice_weeks": ("practice_limited_flag", "sum"),
}

if "primary_injury_count" in injuries_weekly.columns:
    injury_season_aggs["unique_primary_injury_weeks"] = ("primary_injury_count", "sum")

injuries_season = (
    injuries_weekly
    .groupby(["season", "player_id"], as_index=False)
    .agg(**injury_season_aggs)
)

print(injuries_season.shape)
print(injuries_season.head())


## MERGING EVERYTHING ##
features = data.merge(
    reg_snaps_season,
    on=["season", "player_id"],
    how="left",
    validate="one_to_one",
)

features = features.merge(
    playoff_snaps_season,
    on=["season", "player_id"],
    how="left",
    validate="one_to_one",
)

injury_source_seasons = set(
    injuries_season["season"]
    .dropna()
    .astype(int)
    .unique()
)

features = features.merge(
    injuries_season,
    on=["season", "player_id"],
    how="left",
    validate="one_to_one",
)

## MANUALLY FILLING IN MISSING SNAP VALUES ##
snap_fill_cols = [
    c for c in features.columns
    if c.startswith("reg_") or c.startswith("playoff_")
]

features[snap_fill_cols] = features[snap_fill_cols].fillna(0)

features["has_reg_snap_data"] = (
    features["reg_snap_games"] > 0
).astype(int) if "reg_snap_games" in features.columns else 0

features["has_playoff_snap_data"] = (
    features["playoff_snap_games"] > 0
).astype(int) if "playoff_snap_games" in features.columns else 0

## MANUALLY FILLING IN MISSING INJURIES VALUES ##
features["has_injury_source_for_season"] = (
    features["season"].astype(int).isin(injury_source_seasons)
).astype(int)

if "injury_report_weeks" in features.columns:
    features["injury_merge_matched"] = (
        features["injury_report_weeks"].notna()
    ).astype(int)
else:
    features["injury_merge_matched"] = 0

injury_fill_cols = [
    "injury_report_weeks",
    "out_weeks",
    "doubtful_weeks",
    "questionable_weeks",
    "practice_dnp_weeks",
    "limited_practice_weeks",
    "unique_primary_injury_weeks",
]

injury_fill_cols = [c for c in injury_fill_cols if c in features.columns]

mask_source_season = features["has_injury_source_for_season"].eq(1)

features.loc[mask_source_season, injury_fill_cols] = (
    features.loc[mask_source_season, injury_fill_cols].fillna(0)
)

## CLEANING OUTPUTTED FLAGS ##
features["played_regular_season"] = (
    features["reg_snap_games"] > 0
).astype(int) if "reg_snap_games" in features.columns else 0

features["played_playoffs"] = (
    features["playoff_snap_games"] > 0
).astype(int) if "playoff_snap_games" in features.columns else 0

features["was_on_injury_report"] = pd.Series(pd.NA, index=features.index, dtype="Int64")

if "injury_report_weeks" in features.columns:
    features.loc[mask_source_season, "was_on_injury_report"] = (
        features.loc[mask_source_season, "injury_report_weeks"] > 0
    ).astype(int)

## OUTPUT FILE ##
features.to_csv(OUTPUT_FILE, index=False)
print(f"\nSaved: {OUTPUT_FILE}")
