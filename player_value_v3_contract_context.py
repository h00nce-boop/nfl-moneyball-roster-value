# -*- coding: utf-8 -*-
"""
Adds contract-cycle and draft-capital context to the existing
player-level v2 confidence output.

This is intentionally a light-touch v3 script:
- starts from the existing v2 player value file
- adds draft year / draft round / draft pick
- estimates rookie-contract status
- labels player surplus context
- saves v3 outputs


@author: hannah
"""

import os
import pandas as pd
import nflreadpy as nfl


## SETUP ##
seasons = [2021, 2022, 2023, 2024, 2025]
focus_teams = ["PHI", "NYG", "CLE", "BAL", "DET"]

os.makedirs("outputs_v3", exist_ok=True)
os.makedirs("outputs_v3/summary", exist_ok=True)

## LOAD DATA ##
player_value = pd.read_csv(
    "outputs_v2/player_value_2021_2025_v2_confidence.csv"
)

player_diagnostics = pd.read_csv(
    "outputs_v2/player_value_diagnostics_2021_2025_v2_confidence.csv"
)

## LOAD DRAFT DATA ##
draft_picks = nfl.load_draft_picks()

if hasattr(draft_picks, "to_pandas"):
    draft_picks = draft_picks.to_pandas()


## CLEAN DRAFT DATA ##
if "season" in draft_picks.columns:
    draft_picks = draft_picks.rename(columns={"season": "draft_year"})

if "team" in draft_picks.columns:
    draft_picks = draft_picks.rename(columns={"team": "draft_team"})

if "round" in draft_picks.columns:
    draft_picks = draft_picks.rename(columns={"round": "draft_round"})

if "pick" in draft_picks.columns:
    draft_picks = draft_picks.rename(columns={"pick": "draft_pick"})

if "gsis_id" in draft_picks.columns:
    draft_picks = draft_picks.rename(columns={"gsis_id": "player_id"})

draft_keep_cols = [
    "player_id",
    "draft_year",
    "draft_team",
    "draft_round",
    "draft_pick",
]

draft_keep_cols = [
    col for col in draft_keep_cols
    if col in draft_picks.columns
]

draft_clean = draft_picks[draft_keep_cols].copy()

draft_clean = draft_clean.drop_duplicates(subset=["player_id"])


## MERGE DRAFT DATA ONTO V2 PLAYER VALUE ##
player_value = player_value.merge(
    draft_clean,
    on="player_id",
    how="left"
)

player_diagnostics = player_diagnostics.merge(
    draft_clean,
    on="player_id",
    how="left"
)

## DE-TRUNCATE ##
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 120)


## ADD CONTRACT-CYCLE FIELDS ##
def draft_capital_bucket(row):
    if pd.isna(row["draft_round"]):
        return "undrafted_or_unmatched"
    elif row["draft_round"] == 1:
        return "round_1"
    elif row["draft_round"] == 2:
        return "round_2"
    elif row["draft_round"] == 3:
        return "round_3"
    elif row["draft_round"] in [4, 5]:
        return "rounds_4_5"
    elif row["draft_round"] in [6, 7]:
        return "rounds_6_7"
    else:
        return "undrafted_or_unmatched"


def contract_stage(row):
    if pd.isna(row["draft_year"]):
        return "undrafted_or_unmatched"

    years_since_drafted = row["season"] - row["draft_year"]

    if years_since_drafted < 0:
        return "data_issue"

    if row["draft_round"] == 1:
        if years_since_drafted <= 3:
            return "rookie_contract"
        elif years_since_drafted == 4:
            return "possible_fifth_year_option"
        else:
            return "second_contract_or_later"

    if row["draft_round"] in [2, 3, 4, 5, 6, 7]:
        if years_since_drafted <= 3:
            return "rookie_contract"
        else:
            return "second_contract_or_later"

    return "undrafted_or_unmatched"


def surplus_context(row):
    if row["overall_confidence"] == "low":
        return "low_confidence"

    if pd.isna(row["player_surplus_gap"]):
        return "unranked"

    if row["player_surplus_gap"] >= 10 and row["estimated_contract_stage"] in [
        "rookie_contract",
        "possible_fifth_year_option"
    ]:
        return "rookie_contract_surplus"

    if row["player_surplus_gap"] >= 5 and row["estimated_contract_stage"] in [
        "rookie_contract",
        "possible_fifth_year_option"
    ]:
        return "pre_extension_breakout"

    if row["player_surplus_gap"] >= 10:
        return "veteran_positive_value"

    if row["player_surplus_gap"] <= -10:
        return "expensive_negative_value"

    if row["player_surplus_gap"] > 0:
        return "positive_value"

    if row["player_surplus_gap"] == 0:
        return "market_rate"

    return "negative_value"


for df in [player_value, player_diagnostics]:
    df["years_since_drafted"] = df["season"] - df["draft_year"]

    df["draft_capital_bucket"] = df.apply(
        draft_capital_bucket,
        axis=1
    )

    df["estimated_contract_stage"] = df.apply(
        contract_stage,
        axis=1
    )

    df["is_likely_rookie_contract"] = df["estimated_contract_stage"].isin(
        ["rookie_contract", "possible_fifth_year_option"]
    )

player_value["surplus_context"] = player_value.apply(
    surplus_context,
    axis=1
)

## CLEAN YEAR / DRAFT NUMBER FORMATTING ##
for df in [player_value, player_diagnostics]:
    for col in ["draft_year", "draft_round", "draft_pick", "years_since_drafted"]:
        if col in df.columns:
            df[col] = df[col].astype("Int64")

## REMOVE MISSING CONTRACTS FROM FINAL RANKED TABLE ##
player_value_ranked = player_value[
    (player_value["has_contract_match"] == True)
    & (player_value["cap_number"].notna())
    & (player_value["meets_sample_threshold"] == True)
].copy()

## CREATE FOCUS TEAM OUTPUT ##
focus_player_value = (
    player_value_ranked
    .loc[player_value_ranked["team"].isin(focus_teams)]
    .copy()
    .sort_values(
        [
            "season",
            "team",
            "position_final",
            "player_surplus_rank"
        ]
    )
)


## CREATE SIMPLE SUMMARY FILES ##
contract_stage_summary = (
    player_value_ranked
    .groupby(
        [
            "season",
            "position_final",
            "estimated_contract_stage"
        ],
        as_index=False
    )
    .agg(
        players=("player_id", "nunique"),
        avg_surplus_gap=("player_surplus_gap", "mean"),
        avg_cap_number=("cap_number", "mean"),
        avg_production_score=("production_score", "mean")
    )
    .sort_values(
        ["season", "position_final", "avg_surplus_gap"],
        ascending=[True, True, False]
    )
)

draft_capital_summary = (
    player_value_ranked
    .groupby(
        [
            "season",
            "position_final",
            "draft_capital_bucket"
        ],
        as_index=False
    )
    .agg(
        players=("player_id", "nunique"),
        avg_surplus_gap=("player_surplus_gap", "mean"),
        avg_cap_number=("cap_number", "mean"),
        avg_production_score=("production_score", "mean")
    )
    .sort_values(
        ["season", "position_final", "avg_surplus_gap"],
        ascending=[True, True, False]
    )
)

pre_extension_candidates = (
    player_value_ranked
    .loc[
        (player_value_ranked["season"] == 2025)
        & (player_value_ranked["is_likely_rookie_contract"] == True)
        & (player_value_ranked["player_surplus_gap"] >= 5)
    ]
    .copy()
    .sort_values(
        ["player_surplus_gap", "production_score"],
        ascending=[False, False]
    )
)


## SAVE OUTPUTS ##
player_value_ranked.to_csv(
    "outputs_v3/player_value_2021_2025_v3_contract_context.csv",
    index=False
)

focus_player_value.to_csv(
    "outputs_v3/focus_player_value_2021_2025_v3_contract_context.csv",
    index=False
)

player_diagnostics.to_csv(
    "outputs_v3/player_value_diagnostics_2021_2025_v3_contract_context.csv",
    index=False
)

contract_stage_summary.to_csv(
    "outputs_v3/summary/contract_stage_summary_2021_2025.csv",
    index=False
)

draft_capital_summary.to_csv(
    "outputs_v3/summary/draft_capital_summary_2021_2025.csv",
    index=False
)

pre_extension_candidates.to_csv(
    "outputs_v3/summary/pre_extension_candidates_2025.csv",
    index=False
)


print("\nSaved v3 contract-context outputs:")
print("- outputs_v3/player_value_2021_2025_v3_contract_context.csv")
print("- outputs_v3/focus_player_value_2021_2025_v3_contract_context.csv")
print("- outputs_v3/player_value_diagnostics_2021_2025_v3_contract_context.csv")
print("- outputs_v3/summary/contract_stage_summary_2021_2025.csv")
print("- outputs_v3/summary/draft_capital_summary_2021_2025.csv")
print("- outputs_v3/summary/pre_extension_candidates_2025.csv")

## VALIDATION ##
print("\nV3 validation checks:")
print("Ranked rows:", len(player_value_ranked))
print("Draft match rate:", round(player_value_ranked["draft_year"].notna().mean(), 3))
print("Rookie-contract rows:", player_value_ranked["is_likely_rookie_contract"].sum())

print("\nContract stage counts:")
print(player_value_ranked["estimated_contract_stage"].value_counts(dropna=False))

print("\nDraft capital counts:")
print(player_value_ranked["draft_capital_bucket"].value_counts(dropna=False))

print("\nTop 10 pre-extension candidates:")
print(
    pre_extension_candidates[
        [
            "season",
            "team",
            "player_name",
            "position_final",
            "player_surplus_gap",
            "draft_year",
            "draft_round",
            "estimated_contract_stage"
        ]
    ].head(10)
)

print("\nDraft year range:")
print(player_value_ranked["draft_year"].min())
print(player_value_ranked["draft_year"].max())

print("\nDraft year counts:")
print(player_value_ranked["draft_year"].value_counts(dropna=False).sort_index())