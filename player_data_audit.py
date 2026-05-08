# -*- coding: utf-8 -*-
"""
Builds the player-level skill-position surplus value model.

The first version focuses on QB, RB, WR, and TE. Player value is calculated by
comparing production rank against contract cost rank within each position group.

Outputs:
- outputs/player_value_skill_2021_2025.csv
- outputs/focus_player_value_skill_2021_2025.csv

@author: hannah
"""

import os
import nflreadpy as nfl
import pandas as pd

## SETUP ##
seasons = [2021, 2022, 2023, 2024, 2025]

os.makedirs("outputs/audits", exist_ok=True)


## LOAD DATA ##
player_stats = nfl.load_player_stats(seasons)
snap_counts = nfl.load_snap_counts(seasons)
rosters = nfl.load_rosters(seasons)
contracts_flat = pd.read_csv("outputs/contracts_flat_2021_2025.csv")


## CONVERT TO PANDAS ##
def to_pandas_safe(data):
    if hasattr(data, "to_pandas"):
        return data.to_pandas()
    return data


player_stats = to_pandas_safe(player_stats)
snap_counts = to_pandas_safe(snap_counts)
rosters = to_pandas_safe(rosters)


## STORE DATASETS ##
datasets = {
    "player_stats": player_stats,
    "snap_counts": snap_counts,
    "rosters": rosters,
    "contracts_flat": contracts_flat
}


## BASIC SHAPE + COLUMN AUDIT ##
print("\n" + "=" * 80)
print("BASIC DATASET AUDIT")
print("=" * 80)

summary_rows = []

for name, df in datasets.items():
    print("\n" + "-" * 80)
    print(name)
    print("-" * 80)
    print("type:", type(df))
    print("shape:", df.shape)
    print("columns:")
    print(list(df.columns))

    summary_rows.append({
        "dataset": name,
        "rows": df.shape[0],
        "columns": df.shape[1],
        "type": type(df).__name__
    })

dataset_summary = pd.DataFrame(summary_rows)
dataset_summary.to_csv("outputs/audits/player_dataset_summary.csv", index=False)


## KEY COLUMN SEARCH ##
keywords = [
    "season",
    "week",
    "team",
    "recent_team",
    "posteam",
    "player",
    "player_id",
    "gsis",
    "name",
    "position",
    "depth",
    "snap",
    "offense",
    "defense",
    "passing",
    "rushing",
    "receiving",
    "target",
    "reception",
    "yards",
    "td",
    "touchdown",
    "interception",
    "sack",
    "cap",
    "cash",
    "salary",
    "guaranteed"
]

print("\n" + "=" * 80)
print("KEY COLUMN SEARCH")
print("=" * 80)

column_search_rows = []

for name, df in datasets.items():
    print("\n" + "-" * 80)
    print(name)
    print("-" * 80)

    matched_cols = []

    for col in df.columns:
        if any(keyword in col.lower() for keyword in keywords):
            matched_cols.append(col)

    print(matched_cols)

    for col in matched_cols:
        column_search_rows.append({
            "dataset": name,
            "column": col
        })

column_search = pd.DataFrame(column_search_rows)
column_search.to_csv("outputs/audits/player_key_columns.csv", index=False)


## SAMPLE ROWS ##
print("\n" + "=" * 80)
print("SAMPLE ROWS")
print("=" * 80)

for name, df in datasets.items():
    print("\n" + "-" * 80)
    print(name)
    print("-" * 80)
    print(df.head(10))

    df.head(50).to_csv(f"outputs/audits/{name}_sample_rows.csv", index=False)


## PLAYER STATS AUDIT ##
print("\n" + "=" * 80)
print("PLAYER STATS AUDIT")
print("=" * 80)

print("\nplayer_stats seasons:")
if "season" in player_stats.columns:
    print(sorted(player_stats["season"].dropna().unique()))

print("\nplayer_stats teams:")
team_col_candidates = ["recent_team", "team", "posteam"]

for col in team_col_candidates:
    if col in player_stats.columns:
        print(f"\nTeam column candidate: {col}")
        print(sorted(player_stats[col].dropna().unique())[:40])

print("\nplayer_stats player/name columns:")
print([c for c in player_stats.columns if "player" in c.lower() or "name" in c.lower()])

print("\nplayer_stats possible production columns:")
production_keywords = [
    "passing",
    "rushing",
    "receiving",
    "reception",
    "target",
    "yards",
    "td",
    "touchdown",
    "interception",
    "sack"
]

print([
    c for c in player_stats.columns
    if any(k in c.lower() for k in production_keywords)
])


## SNAP COUNTS AUDIT ##
print("\n" + "=" * 80)
print("SNAP COUNTS AUDIT")
print("=" * 80)

print("\nsnap_counts seasons:")
if "season" in snap_counts.columns:
    print(sorted(snap_counts["season"].dropna().unique()))

print("\nsnap_counts team columns:")
for col in ["team", "recent_team", "posteam"]:
    if col in snap_counts.columns:
        print(f"\nTeam column candidate: {col}")
        print(sorted(snap_counts[col].dropna().unique())[:40])

print("\nsnap_counts player/name columns:")
print([c for c in snap_counts.columns if "player" in c.lower() or "name" in c.lower() or "gsis" in c.lower()])

print("\nsnap_counts snap columns:")
print([c for c in snap_counts.columns if "snap" in c.lower() or "pct" in c.lower() or "offense" in c.lower() or "defense" in c.lower()])


## ROSTERS AUDIT ##
print("\n" + "=" * 80)
print("ROSTERS AUDIT")
print("=" * 80)

print("\nrosters seasons:")
if "season" in rosters.columns:
    print(sorted(rosters["season"].dropna().unique()))

print("\nrosters team columns:")
for col in ["team", "recent_team", "posteam"]:
    if col in rosters.columns:
        print(f"\nTeam column candidate: {col}")
        print(sorted(rosters[col].dropna().unique())[:40])

print("\nrosters player/name columns:")
print([c for c in rosters.columns if "player" in c.lower() or "name" in c.lower() or "gsis" in c.lower()])

print("\nrosters position/age/draft columns:")
print([
    c for c in rosters.columns
    if any(k in c.lower() for k in ["position", "depth", "birth", "age", "rookie", "draft", "college", "exp"])
])


## CONTRACTS AUDIT ##
print("\n" + "=" * 80)
print("CONTRACTS FLAT AUDIT")
print("=" * 80)

print("\ncontracts_flat seasons:")
if "season" in contracts_flat.columns:
    print(sorted(contracts_flat["season"].dropna().unique()))

print("\ncontracts_flat teams:")
if "team_abbr" in contracts_flat.columns:
    print(sorted(contracts_flat["team_abbr"].dropna().unique()))

print("\ncontracts_flat player/name columns:")
print([c for c in contracts_flat.columns if "player" in c.lower() or "name" in c.lower()])

print("\ncontracts_flat position/cost columns:")
print([
    c for c in contracts_flat.columns
    if any(k in c.lower() for k in ["position", "cap", "cash", "salary", "guaranteed", "bonus"])
])

print("\ncontracts_flat duplicate player-team-season check:")

if all(c in contracts_flat.columns for c in ["season", "team_abbr", "player"]):
    duplicate_contracts = (
        contracts_flat
        .groupby(["season", "team_abbr", "player"])
        .size()
        .reset_index(name="row_count")
        .query("row_count > 1")
        .sort_values("row_count", ascending=False)
    )

    print(duplicate_contracts.head(30))
    duplicate_contracts.to_csv("outputs/audits/contracts_duplicate_check.csv", index=False)
else:
    print("Could not run duplicate check because season/team_abbr/player columns were not all present.")


## JOIN KEY DIAGNOSTICS ##
print("\n" + "=" * 80)
print("JOIN KEY DIAGNOSTICS")
print("=" * 80)

print("\nRecommended join direction:")
print("1. player_stats to rosters: season + team + player_id")
print("2. player_stats to snap_counts: season + team + player_id or gsis_id")
print("3. player_stats to contracts_flat: season + team + player_name/player")

print("\nChecking likely keys:")

checks = {
    "player_stats_has_player_id": "player_id" in player_stats.columns,
    "player_stats_has_player_name": "player_name" in player_stats.columns,
    "player_stats_has_recent_team": "recent_team" in player_stats.columns,
    "player_stats_has_team": "team" in player_stats.columns,
    "snap_counts_has_player_id": "player_id" in snap_counts.columns,
    "snap_counts_has_gsis_id": "gsis_id" in snap_counts.columns,
    "snap_counts_has_team": "team" in snap_counts.columns,
    "rosters_has_player_id": "player_id" in rosters.columns,
    "rosters_has_team": "team" in rosters.columns,
    "contracts_has_player": "player" in contracts_flat.columns,
    "contracts_has_team_abbr": "team_abbr" in contracts_flat.columns,
    "contracts_has_cap_number": "cap_number" in contracts_flat.columns
}

for check, result in checks.items():
    print(f"{check}: {result}")

pd.DataFrame(
    [{"check": k, "result": v} for k, v in checks.items()]
).to_csv("outputs/audits/player_join_key_checks.csv", index=False)


## OPTIONAL: TEST PLAYER NAME MATCH RATE TO CONTRACTS ##
print("\n" + "=" * 80)
print("PLAYER NAME MATCH RATE TO CONTRACTS")
print("=" * 80)

# Standardize a team column for player_stats just for this audit
player_stats_audit = player_stats.copy()

if "recent_team" in player_stats_audit.columns:
    player_stats_audit["team_for_join"] = player_stats_audit["recent_team"]
elif "team" in player_stats_audit.columns:
    player_stats_audit["team_for_join"] = player_stats_audit["team"]
elif "posteam" in player_stats_audit.columns:
    player_stats_audit["team_for_join"] = player_stats_audit["posteam"]
else:
    player_stats_audit["team_for_join"] = None

if "player_name" not in player_stats_audit.columns:
    if "player_display_name" in player_stats_audit.columns:
        player_stats_audit["player_name"] = player_stats_audit["player_display_name"]
    elif "name" in player_stats_audit.columns:
        player_stats_audit["player_name"] = player_stats_audit["name"]

if all(c in player_stats_audit.columns for c in ["season", "team_for_join", "player_name"]) and all(c in contracts_flat.columns for c in ["season", "team_abbr", "player"]):
    player_keys = (
        player_stats_audit[["season", "team_for_join", "player_name"]]
        .drop_duplicates()
        .rename(columns={"team_for_join": "team", "player_name": "player"})
    )

    contract_keys = (
        contracts_flat[["season", "team_abbr", "player"]]
        .drop_duplicates()
        .rename(columns={"team_abbr": "team"})
    )

    name_match = player_keys.merge(
        contract_keys,
        on=["season", "team", "player"],
        how="left",
        indicator=True
    )

    match_summary = (
        name_match["_merge"]
        .value_counts()
        .reset_index()
    )

    match_summary.columns = ["merge_status", "count"]

    print(match_summary)

    match_summary.to_csv("outputs/audits/player_contract_name_match_summary.csv", index=False)

    unmatched_sample = (
        name_match
        .query("_merge == 'left_only'")
        .head(50)
    )

    print("\nSample unmatched player stat names:")
    print(unmatched_sample)

    unmatched_sample.to_csv("outputs/audits/player_contract_unmatched_sample.csv", index=False)
else:
    print("Could not test player-contract name match rate because required columns were missing.")


print("\nAudit complete. Files saved to outputs/audits/")
