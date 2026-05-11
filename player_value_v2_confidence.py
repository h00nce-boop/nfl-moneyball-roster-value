# -*- coding: utf-8 -*-
"""
Player-level surplus value model for the NFL Moneyball roster-value project.

This script builds the player-level value model using regular-season public
NFL player stats and cleaned public contract data. It currently focuses on
offensive skill positions: QB, RB, WR, and TE.

The model creates a first-pass production score, merges player production with
contract cost data, ranks players within season-position groups, and calculates
player_surplus_gap as:

    cost_rank_position - production_rank_position

Positive values suggest a player produced better than his cost rank. Negative
values suggest the player was expensive relative to production.

This version also adds data-quality and confidence flags for missing contract
matches and low-sample players. Missing contract data should not be interpreted
as true zero cost.

Limitations: this model does not yet include defensive players, offensive
linemen, rookie-contract status, draft capital, injuries, or learned/statistical
production-score weights.

@author: hannah
"""

import os
import nflreadpy as nfl
import pandas as pd


## SETUP ##
seasons = [2021, 2022, 2023, 2024, 2025]
focus_teams = ["PHI", "NYG", "CLE", "BAL", "DET"]

os.makedirs("outputs_v2", exist_ok=True)


## LOAD DATA ##
player_stats = nfl.load_player_stats(seasons)
contracts_flat = pd.read_csv("outputs/contracts_flat_2021_2025.csv")


## CONVERT TO PANDAS ##
def to_pandas_safe(data):
    if hasattr(data, "to_pandas"):
        return data.to_pandas()
    return data


player_stats = to_pandas_safe(player_stats)


## CLEAN PLAYER STATS ##
if "season_type" in player_stats.columns:
    player_stats = player_stats[player_stats["season_type"] == "REG"].copy()


## STANDARDIZE KEY COLUMNS ##
# Your audit showed player_stats has team, not recent_team.
if "team" not in player_stats.columns:
    raise KeyError("player_stats is missing team column.")

if "player_id" not in player_stats.columns:
    raise KeyError("player_stats is missing player_id column.")

if "player_display_name" not in player_stats.columns:
    if "player_name" in player_stats.columns:
        player_stats["player_display_name"] = player_stats["player_name"]
    else:
        raise KeyError("player_stats is missing player_display_name/player_name column.")


## MAKE SURE PRODUCTION COLUMNS EXIST ##
production_cols = [
    "passing_yards",
    "passing_tds",
    "passing_interceptions",
    "sacks_suffered",
    "rushing_yards",
    "rushing_tds",
    "receptions",
    "receiving_yards",
    "receiving_tds",
    "targets",
    "passing_epa",
    "rushing_epa",
    "receiving_epa"
]

for col in production_cols:
    if col not in player_stats.columns:
        player_stats[col] = 0

for col in production_cols:
    player_stats[col] = pd.to_numeric(
        player_stats[col],
        errors="coerce"
    ).fillna(0)


## AGGREGATE PLAYER STATS TO PLAYER-SEASON ##
player_prod = (
    player_stats
    .groupby(
        [
            "season",
            "team",
            "player_id",
            "player_display_name",
            "position",
            "position_group"
        ],
        as_index=False
    )
    .agg(
        passing_yards=("passing_yards", "sum"),
        passing_tds=("passing_tds", "sum"),
        passing_interceptions=("passing_interceptions", "sum"),
        sacks_suffered=("sacks_suffered", "sum"),
        rushing_yards=("rushing_yards", "sum"),
        rushing_tds=("rushing_tds", "sum"),
        receptions=("receptions", "sum"),
        receiving_yards=("receiving_yards", "sum"),
        receiving_tds=("receiving_tds", "sum"),
        targets=("targets", "sum"),
        passing_epa=("passing_epa", "sum"),
        rushing_epa=("rushing_epa", "sum"),
        receiving_epa=("receiving_epa", "sum")
    )
    .rename(columns={"player_display_name": "player_name"})
)


## CREATE SIMPLE PRODUCTION SCORE ##
# This is a first-pass public-data production proxy.
# EPA is included because it is more meaningful than raw yards alone.
player_prod["total_epa"] = (
    player_prod["passing_epa"]
    + player_prod["rushing_epa"]
    + player_prod["receiving_epa"]
)

player_prod["production_score"] = (
    player_prod["total_epa"] * 1.0
    + player_prod["passing_yards"] * 0.01
    + player_prod["passing_tds"] * 2
    - player_prod["passing_interceptions"] * 2
    - player_prod["sacks_suffered"] * 0.25
    + player_prod["rushing_yards"] * 0.05
    + player_prod["rushing_tds"] * 3
    + player_prod["receptions"] * 0.25
    + player_prod["receiving_yards"] * 0.05
    + player_prod["receiving_tds"] * 3
)


## PREPARE CONTRACT COST ##
# Your audit showed contracts_flat has gsis_id, so use that instead of name matching.
contract_keep_cols = [
    "season",
    "team_abbr",
    "gsis_id",
    "player",
    "position",
    "cap_number",
    "cash_paid",
    "base_salary",
    "guaranteed_salary"
]

contract_keep_cols = [
    col for col in contract_keep_cols
    if col in contracts_flat.columns
]

contracts_player = contracts_flat[contract_keep_cols].copy()

contracts_player = contracts_player.rename(
    columns={
        "team_abbr": "team",
        "gsis_id": "player_id",
        "player": "contract_player_name",
        "position": "contract_position"
    }
)


## MAKE CONTRACT COST COLUMNS NUMERIC ##
# Do not treat missing costs as true zero costs.
for col in ["cap_number", "cash_paid", "base_salary", "guaranteed_salary"]:
    if col not in contracts_player.columns:
        contracts_player[col] = pd.NA

    contracts_player[col] = pd.to_numeric(
        contracts_player[col],
        errors="coerce"
    )


## JOIN PRODUCTION + CONTRACTS BY ID ##
player_value = player_prod.merge(
    contracts_player,
    on=["season", "team", "player_id"],
    how="left"
)


## DATA QUALITY FLAGS ##
# A contract match means the player successfully joined to a contract row.
player_value["has_contract_match"] = player_value["contract_player_name"].notna()

# Missing contract data should not be treated as true zero cost.
player_value["has_missing_contract"] = ~player_value["has_contract_match"]


## CLEAN COST FIELDS AFTER JOIN ##
# Keep missing contract values as missing.
for col in ["cap_number", "cash_paid", "base_salary", "guaranteed_salary"]:
    if col not in player_value.columns:
        player_value[col] = pd.NA

    player_value[col] = pd.to_numeric(
        player_value[col],
        errors="coerce"
    )


## FINAL POSITION FIELD ##
player_value["position_final"] = player_value["position"]

if "contract_position" in player_value.columns:
    player_value["position_final"] = player_value["position_final"].fillna(
        player_value["contract_position"]
    )


## FOCUS ON OFFENSIVE SKILL PLAYERS ##
skill_positions = ["QB", "RB", "WR", "TE"]

player_value = player_value[
    player_value["position_final"].isin(skill_positions)
].copy()


## SAMPLE SIZE FLAGS ##
# These flags identify whether a player had enough usage to make a value
# ranking meaningful.
player_value["meets_sample_threshold"] = (
    (
        (player_value["position_final"] == "QB")
        & (
            (player_value["passing_yards"] >= 1000)
            | (player_value["passing_tds"] >= 8)
        )
    )
    |
    (
        (player_value["position_final"] == "RB")
        & (
            (player_value["rushing_yards"] >= 300)
            | (player_value["receptions"] >= 25)
        )
    )
    |
    (
        (player_value["position_final"].isin(["WR", "TE"]))
        & (
            (player_value["targets"] >= 40)
            | (player_value["receiving_yards"] >= 400)
        )
    )
)

player_value["sample_confidence"] = player_value["meets_sample_threshold"].map(
    {
        True: "normal_sample",
        False: "low_sample"
    }
)

player_value["contract_confidence"] = player_value["has_contract_match"].map(
    {
        True: "contract_matched",
        False: "missing_contract"
    }
)

player_value["overall_confidence"] = "high"

player_value.loc[
    player_value["has_missing_contract"]
    | ~player_value["meets_sample_threshold"],
    "overall_confidence"
] = "low"


## SAVE DIAGNOSTIC VERSION BEFORE FILTERING ##
# This keeps low-sample players available for review, even though they are not
# included in the final ranking.
player_value_diagnostics = player_value.copy()
player_value_diagnostics["meets_sample_threshold"].value_counts()


## FILTER LOW-SAMPLE PLAYERS ##
# Only players who meet the usage threshold are included in the value ranking.
player_value = player_value[
    player_value["meets_sample_threshold"]
].copy()


## CREATE PLAYER VALUE RANKS ##
# Rank production and cost within position-season.
player_value["production_rank_position"] = (
    player_value
    .groupby(["season", "position_final"])["production_score"]
    .rank(ascending=False)
)

player_value["cost_rank_position"] = (
    player_value
    .groupby(["season", "position_final"])["cap_number"]
    .rank(
        ascending=False,
        na_option="bottom"
    )
)

# Positive = production rank is better than cost rank.
player_value["player_surplus_gap"] = (
    player_value["cost_rank_position"]
    - player_value["production_rank_position"]
)

player_value["player_surplus_rank"] = (
    player_value
    .groupby(["season", "position_final"])["player_surplus_gap"]
    .rank(ascending=False)
)


## ADD VALUE TIERS ##
def label_player_value(gap):
    if gap >= 20:
        return "Major bargain"
    elif gap >= 10:
        return "Strong bargain"
    elif gap >= 3:
        return "Positive value"
    elif gap > -3:
        return "Fair value"
    elif gap > -10:
        return "Negative value"
    else:
        return "Major overpay"


player_value["player_value_tier"] = player_value["player_surplus_gap"].apply(
    label_player_value
)


## CREATE FOCUS TEAM TABLE ##
focus_player_value = (
    player_value
    .loc[player_value["team"].isin(focus_teams)]
    .copy()
)

focus_player_value = focus_player_value.sort_values(
    [
        "season",
        "team",
        "position_final",
        "player_surplus_rank"
    ]
)

## SAVE OUTPUTS ##
player_value.to_csv(
    "outputs_v2/player_value_2021_2025_v2_confidence.csv",
    index=False
)

focus_player_value.to_csv(
    "outputs_v2/focus_player_value_2021_2025_v2_confidence.csv",
    index=False
)

player_value_diagnostics.to_csv(
    "outputs_v2/player_value_diagnostics_2021_2025_v2_confidence.csv",
    index=False
)

print("\nSaved player value outputs:")
print("- outputs_v2/player_value_2021_2025_v2_confidence.csv")
print("- outputs_v2/focus_player_value_2021_2025_v2_confidence.csv")
print("- outputs_v2/player_value_diagnostics_2021_2025_v2_confidence.csv")