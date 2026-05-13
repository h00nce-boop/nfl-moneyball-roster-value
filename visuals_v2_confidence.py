# -*- coding: utf-8 -*-
"""
Creates v2 confidence visuals for the NFL Moneyball project.

These charts summarize the confidence and data-quality flags added in
player_value_v2_confidence.py. They show how the diagnostic player pool compares
with the final ranked player pool and how sample/contract confidence varies by
season.

@author: hannah
"""

import os
import pandas as pd
import matplotlib.pyplot as plt

os.makedirs("outputs_v2/figures", exist_ok=True)

player_quality = pd.read_csv(
    "outputs_v2/summary/player_data_quality_summary_2021_2025.csv")
player_quality_diagnostics = pd.read_csv(
    "outputs_v2/summary/player_data_quality_diagnostics_2021_2025.csv")


## 1. SAMPLE CONFIDENCE BY SEASON ##
sample_confidence_by_season = (
    player_quality_diagnostics
    .groupby(["season", "sample_confidence"], as_index=False)
    ["player_count"]
    .sum()
)

sample_pivot = sample_confidence_by_season.pivot(
    index="season",
    columns="sample_confidence",
    values="player_count"
).fillna(0)

sample_pivot.plot(kind="bar")

plt.title("Skill-Player Sample Confidence by Season")
plt.xlabel("Season")
plt.ylabel("Player Count")
plt.xticks(rotation=0)
plt.legend(title="Sample Confidence")
plt.tight_layout()
plt.savefig(
    "outputs_v2/figures/player_sample_confidence_by_season.png",
    dpi=300
)
plt.close()

## 2. CONTRACT CONFIDENCE BY SEASON ##
contract_confidence_by_season = (
    player_quality_diagnostics
    .groupby(["season", "contract_confidence"], as_index=False)
    ["player_count"]
    .sum())

contract_pivot = contract_confidence_by_season.pivot(
    index="season",
    columns="contract_confidence",
    values="player_count"
    ).fillna(0)

contract_pivot.plot(kind="bar")

plt.title("Player Contract Match Confidence by Season")
plt.xlabel("Season")
plt.ylabel("Player Count")
plt.xticks(rotation=0)
plt.legend(title="Contract Confidence")
plt.tight_layout()
plt.savefig(
    "outputs_v2/figures/player_contract_confidence_by_season.png",
    dpi=300
)
plt.close()

## 3. OVERALL CONFIDENCE BY SEASON ##   
overall_confidence_by_season = (
    player_quality_diagnostics
    .groupby(["season", "overall_confidence"], as_index=False)
    ["player_count"]
    .sum()
)

overall_pivot = overall_confidence_by_season.pivot(
    index="season",
    columns="overall_confidence",
    values="player_count"
).fillna(0)

overall_pivot.plot(kind="bar")

plt.title("Overall Confidence in Diagnostic Player Pool by Season")
plt.xlabel("Season")
plt.ylabel("Player Count")
plt.xticks(rotation=0)
plt.legend(title="Overall Confidence")
plt.tight_layout()
plt.savefig(
    "outputs_v2/figures/player_overall_confidence_by_season.png",
    dpi=300
)
plt.close()

## 4. FINAL RANKED VS DIAGNOSTIC PLAYER POOL ##
diagnostic_pool = (
    player_quality_diagnostics
    .groupby("season", as_index=False)["player_count"]
    .sum()
    .rename(columns={"player_count": "diagnostic_player_count"})
)

ranked_pool = (
    player_quality
    .groupby("season", as_index=False)["player_count"]
    .sum()
    .rename(columns={"player_count": "ranked_player_count"})
)

player_pool_comparison = diagnostic_pool.merge(
    ranked_pool,
    on="season",
    how="left"
)

player_pool_comparison = player_pool_comparison.rename(columns={
    'diagnostic_player_count': 'Diagnostic player pool', 
    'ranked_player_count': 'Final ranked player pool'})
player_pool_comparison = player_pool_comparison.set_index("season")

player_pool_comparison.plot(kind="bar")

plt.title("Diagnostic Player Pool vs Final Ranked Player Pool")
plt.xlabel("Season")
plt.ylabel("Player Count")
plt.xticks(rotation=0)
plt.legend(title="Player Pool")
plt.tight_layout()
plt.savefig(
    "outputs_v2/figures/player_pool_comparison_by_season.png",
    dpi=300
)
plt.close()

## PRINT CHECKS ##
print("\nSaved v2 confidence visuals:")
print("- outputs_v2/figures/player_sample_confidence_by_season.png")
print("- outputs_v2/figures/player_contract_confidence_by_season.png")
print("- outputs_v2/figures/player_overall_confidence_by_season.png")
print("- outputs_v2/figures/player_pool_comparison_by_season.png")

print("\nPlayer pool comparison:")
print(player_pool_comparison)