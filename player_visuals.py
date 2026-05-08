# -*- coding: utf-8 -*-
"""
Creates player-level visuals for the NFL Moneyball project.

Outputs include Eagles skill-player value charts, league-wide bargain charts,
and focus-team skill-player summaries.

@author: hannah
"""

import os
import pandas as pd
import matplotlib.pyplot as plt

os.makedirs("outputs/figures", exist_ok=True)

player_value = pd.read_csv("outputs/player_value_skill_2021_2025.csv")
focus_player_value = pd.read_csv("outputs/focus_player_value_skill_2021_2025.csv")


## 2025 EAGLES SKILL PLAYER VALUE ##
eagles_2025 = (
    focus_player_value
    .query("season == 2025 and team == 'PHI'")
    .sort_values("player_surplus_gap", ascending=True)
)

plt.figure(figsize=(10, 6))

plt.barh(
    eagles_2025["player_name"],
    eagles_2025["player_surplus_gap"]
)

plt.axvline(0, linestyle="--", linewidth=1)

plt.xlabel("Player Surplus Gap, positive is better")
plt.ylabel("Player")
plt.title("2025 Eagles Skill Player Surplus Value")

plt.tight_layout()
plt.savefig("outputs/figures/2025_eagles_skill_player_surplus.png", dpi=300)
plt.show()


## 2025 EAGLES PRODUCTION VS COST ##
plt.figure(figsize=(10, 6))

plt.scatter(
    eagles_2025["cap_number"],
    eagles_2025["production_score"]
)

for _, row in eagles_2025.iterrows():
    plt.text(
        row["cap_number"] + 0.2,
        row["production_score"] + 0.2,
        row["player_name"],
        fontsize=9
    )

plt.xlabel("Cap Number, $ millions")
plt.ylabel("Production Score")
plt.title("2025 Eagles Skill Players: Cost vs Production")

plt.tight_layout()
plt.savefig("outputs/figures/2025_eagles_skill_cost_vs_production.png", dpi=300)
plt.show()


## 2025 TOP LEAGUE-WIDE SKILL PLAYER BARGAINS ##
top_bargains_2025 = (
    player_value
    .query("season == 2025")
    .sort_values("player_surplus_gap", ascending=False)
    .head(15)
    .sort_values("player_surplus_gap", ascending=True)
)

plt.figure(figsize=(10, 7))

plt.barh(
    top_bargains_2025["player_name"] + " (" + top_bargains_2025["team"] + ")",
    top_bargains_2025["player_surplus_gap"]
)

plt.xlabel("Player Surplus Gap")
plt.ylabel("Player")
plt.title("Top 15 Skill Player Bargains, 2025")

plt.tight_layout()
plt.savefig("outputs/figures/2025_top_skill_player_bargains.png", dpi=300)
plt.show()


## 2025 FOCUS TEAM PLAYER VALUE AVERAGES ##
focus_2025 = focus_player_value.query("season == 2025").copy()

focus_team_player_summary = (
    focus_2025
    .groupby("team", as_index=False)
    .agg(
        avg_player_surplus_gap=("player_surplus_gap", "mean"),
        median_player_surplus_gap=("player_surplus_gap", "median"),
        skill_players_evaluated=("player_name", "count")
    )
    .sort_values("avg_player_surplus_gap", ascending=False)
)

plt.figure(figsize=(10, 6))

plt.bar(
    focus_team_player_summary["team"],
    focus_team_player_summary["avg_player_surplus_gap"]
)

plt.axhline(0, linestyle="--", linewidth=1)

plt.xlabel("Team")
plt.ylabel("Average Skill Player Surplus Gap")
plt.title("2025 Focus Teams: Average Skill Player Surplus Value")

plt.tight_layout()
plt.savefig("outputs/figures/2025_focus_team_avg_skill_player_surplus.png", dpi=300)
plt.show()


## SAVE SUMMARY TABLES ##
eagles_2025.to_csv("outputs/2025_eagles_skill_player_value.csv", index=False)
top_bargains_2025.to_csv("outputs/2025_top_skill_player_bargains.csv", index=False)
focus_team_player_summary.to_csv("outputs/2025_focus_team_skill_player_summary.csv", index=False)

print("\nSaved player visual outputs:")
print("- outputs/figures/2025_eagles_skill_player_surplus.png")
print("- outputs/figures/2025_eagles_skill_cost_vs_production.png")
print("- outputs/figures/2025_top_skill_player_bargains.png")
print("- outputs/figures/2025_focus_team_avg_skill_player_surplus.png")
print("- outputs/2025_eagles_skill_player_value.csv")
print("- outputs/2025_top_skill_player_bargains.csv")
print("- outputs/2025_focus_team_skill_player_summary.csv")

print("\n2025 Eagles Skill Player Value:")
print(
    eagles_2025[[
        "player_name",
        "position_final",
        "production_score",
        "cap_number",
        "production_rank_position",
        "cost_rank_position",
        "player_surplus_gap",
        "player_value_tier"
    ]]
)

print("\n2025 Focus Team Skill Player Summary:")
print(focus_team_player_summary)