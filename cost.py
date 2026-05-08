# -*- coding: utf-8 -*-
"""
Builds team-level contract cost metrics for the NFL Moneyball project.

This script flattens yearly contract data, cleans team names, removes duplicate
player-team-season rows, and aggregates contract cost by team-season.

Outputs:
- outputs/contracts_flat_2021_2025.csv
- outputs/team_cost_2021_2025.csv
- outputs/focus_team_cost_2021_2025.csv

@author: hannah
"""

import nflreadpy as nfl
import pandas as pd
import os

## DATA CLEANING ##
seasons = [2021, 2022, 2023, 2024, 2025]

contracts = nfl.load_contracts()


def to_pandas_safe(data):
    if hasattr(data, "to_pandas"):
        return data.to_pandas()
    return data


contracts = to_pandas_safe(contracts)


## FLATTEN NESTED CONTRACT YEAR DATA ##
# Drop original team column so it does not conflict with the yearly team in cols
contracts_for_flattening = contracts.drop(columns=["team"], errors="ignore").copy()

contract_years = contracts_for_flattening.explode("cols").reset_index(drop=True)

contract_year_details = pd.json_normalize(contract_years["cols"])

contracts_flat = pd.concat(
    [
        contract_years.drop(columns=["cols"]).reset_index(drop=True),
        contract_year_details.reset_index(drop=True)
    ],
    axis=1
)


## CLEAN YEAR FIELD ##
contracts_flat["season"] = pd.to_numeric(
    contracts_flat["year"],
    errors="coerce"
)

contracts_flat = contracts_flat.dropna(subset=["season"]).copy()
contracts_flat["season"] = contracts_flat["season"].astype(int)

contracts_flat = contracts_flat[
    contracts_flat["season"].isin(seasons)
].copy()


## CLEAN / MAP TEAM FIELD ##
team_name_map = {
    "Cardinals": "ARI",
    "Falcons": "ATL",
    "Ravens": "BAL",
    "Bills": "BUF",
    "Panthers": "CAR",
    "Bears": "CHI",
    "Bengals": "CIN",
    "Browns": "CLE",
    "Cowboys": "DAL",
    "Broncos": "DEN",
    "Lions": "DET",
    "Packers": "GB",
    "Texans": "HOU",
    "Colts": "IND",
    "Jaguars": "JAX",
    "Chiefs": "KC",
    "Raiders": "LV",
    "Chargers": "LAC",
    "Rams": "LA",
    "Dolphins": "MIA",
    "Vikings": "MIN",
    "Patriots": "NE",
    "Saints": "NO",
    "Giants": "NYG",
    "Jets": "NYJ",
    "Eagles": "PHI",
    "Steelers": "PIT",
    "49ers": "SF",
    "Seahawks": "SEA",
    "Buccaneers": "TB",
    "Titans": "TEN",
    "Commanders": "WAS",
    "Redskins": "WAS",
    "Football Team": "WAS",
    "Washington": "WAS",
    "Washington Football Team": "WAS",

    # abbreviations
    "ARI": "ARI",
    "ATL": "ATL",
    "BAL": "BAL",
    "BUF": "BUF",
    "CAR": "CAR",
    "CHI": "CHI",
    "CIN": "CIN",
    "CLE": "CLE",
    "DAL": "DAL",
    "DEN": "DEN",
    "DET": "DET",
    "GB": "GB",
    "HOU": "HOU",
    "IND": "IND",
    "JAX": "JAX",
    "KC": "KC",
    "LV": "LV",
    "LAC": "LAC",
    "LA": "LA",
    "LAR": "LA",
    "MIA": "MIA",
    "MIN": "MIN",
    "NE": "NE",
    "NO": "NO",
    "NYG": "NYG",
    "NYJ": "NYJ",
    "PHI": "PHI",
    "PIT": "PIT",
    "SF": "SF",
    "SEA": "SEA",
    "TB": "TB",
    "TEN": "TEN",
    "WAS": "WAS",
    "WSH": "WAS"
}


def clean_team(team_value):
    if team_value is None:
        return None

    if pd.isna(team_value):
        return None

    team_value = str(team_value).strip()

    # If multiple teams are listed, use the last listed team
    if "/" in team_value:
        team_value = team_value.split("/")[-1].strip()

    return team_name_map.get(team_value, None)


contracts_flat["team_abbr"] = contracts_flat["team"].apply(clean_team)

unmapped_teams = (
    contracts_flat
    .loc[contracts_flat["team_abbr"].isna(), "team"]
    .drop_duplicates()
    .sort_values()
)

print("\nUnmapped teams:")
print(unmapped_teams)


## DEDUPLICATE PLAYER-TEAM-SEASON CONTRACT ROWS ##
player_col = "player"

print("\nRows before deduplication:")
print(len(contracts_flat))

duplicate_check = (
    contracts_flat
    .groupby(["season", "team_abbr", player_col])
    .size()
    .reset_index(name="row_count")
    .query("row_count > 1")
    .sort_values("row_count", ascending=False)
)

print("\nDuplicate player-team-season rows before deduplication:")
print(duplicate_check.head(20))

contracts_flat = (
    contracts_flat
    .sort_values(
        ["season", "team_abbr", player_col, "cap_number"],
        ascending=[True, True, True, False]
    )
    .drop_duplicates(
        subset=["season", "team_abbr", player_col],
        keep="first"
    )
    .copy()
)

print("\nRows after deduplication:")
print(len(contracts_flat))

duplicate_check_after = (
    contracts_flat
    .groupby(["season", "team_abbr", player_col])
    .size()
    .reset_index(name="row_count")
    .query("row_count > 1")
    .sort_values("row_count", ascending=False)
)

print("\nDuplicate player-team-season rows after deduplication:")
print(duplicate_check_after.head(20))


## BUILD TEAM COST TABLE ##
team_cost = (
    contracts_flat
    .groupby(["season", "team_abbr"], as_index=False)
    .agg(
        total_cap_number=("cap_number", "sum"),
        total_cash_paid=("cash_paid", "sum"),
        total_base_salary=("base_salary", "sum"),
        total_guaranteed_salary=("guaranteed_salary", "sum"),
        player_contract_count=("cap_number", "count")
    )
    .rename(columns={"team_abbr": "team"})
)

team_cost["cap_cost_rank"] = (
    team_cost
    .groupby("season")["total_cap_number"]
    .rank(ascending=False)
)

team_cost["cash_paid_rank"] = (
    team_cost
    .groupby("season")["total_cash_paid"]
    .rank(ascending=False)
)

team_cost = team_cost.sort_values(["season", "cap_cost_rank"])

print("\nTeam Cost Preview:")
print(team_cost.head(10))


## FOCUS TEAM COST VIEW ##
focus_teams = ["PHI", "NYG", "CLE", "BAL", "DET"]

focus_team_cost = (
    team_cost
    .loc[team_cost["team"].isin(focus_teams)]
    .sort_values(["season", "team"])
    .copy()
)

print("\nFocus Team Cost:")
print(focus_team_cost)


## VALIDATION CHECKS ##
print("\n--- VALIDATION CHECKS ---")

print("\nteam_cost shape:")
print(team_cost.shape)

print("\nfocus_team_cost shape:")
print(focus_team_cost.shape)

print("\nNumber of teams per season:")
print(
    team_cost
    .groupby("season")["team"]
    .nunique()
)

print("\nFocus teams per season:")
print(
    focus_team_cost
    .groupby("season")["team"]
    .nunique()
)

print("\nCap number summary:")
print(team_cost["total_cap_number"].describe())

print("\nRank ranges by season:")
print(
    team_cost
    .groupby("season")
    .agg(
        min_cap_rank=("cap_cost_rank", "min"),
        max_cap_rank=("cap_cost_rank", "max"),
        teams=("team", "nunique")
    )
)


## SAVE OUTPUTS ##
os.makedirs("outputs", exist_ok=True)

contracts_flat.to_csv("outputs/contracts_flat_2021_2025.csv", index=False)
team_cost.to_csv("outputs/team_cost_2021_2025.csv", index=False)
focus_team_cost.to_csv("outputs/focus_team_cost_2021_2025.csv", index=False)

print("\nSaved cost outputs:")
print("- outputs/contracts_flat_2021_2025.csv")
print("- outputs/team_cost_2021_2025.csv")
print("- outputs/focus_team_cost_2021_2025.csv")