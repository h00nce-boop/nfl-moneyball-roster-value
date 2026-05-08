# -*- coding: utf-8 -*-
"""
Creates team-level visuals for the NFL Moneyball project.

Outputs are saved to:
- outputs/figures/

@author: hannah
"""

import pandas as pd
import matplotlib.pyplot as plt
import os

## SETUP ##
os.makedirs("outputs/figures", exist_ok=True)

team_surplus = pd.read_csv("outputs/team_surplus_2021_2025.csv")
focus_team_surplus = pd.read_csv("outputs/focus_team_surplus_2021_2025.csv")

focus_teams = ["PHI", "NYG", "CLE", "BAL", "DET"]


## CHART 1: 2025 CONTRACT COST PROXY VS PERFORMANCE ##
team_2025 = team_surplus.query("season == 2025").copy()

plt.figure(figsize=(11, 7))

plt.scatter(
    team_2025["total_cap_number"],
    team_2025["performance_score"]
)

for _, row in team_2025.iterrows():
    if row["team"] in focus_teams:
        plt.text(
            row["total_cap_number"] + 2,
            row["performance_score"] + 0.2,
            row["team"],
            fontsize=10,
            fontweight="bold"
        )

plt.xlabel("Public Contract Cost Proxy, $ millions")
plt.ylabel("Performance Score, higher is better")
plt.title("2025 NFL Contract Cost Proxy vs Performance")

plt.tight_layout()
plt.savefig("outputs/figures/2025_contract_cost_proxy_vs_performance.png", dpi=300)
plt.show()


## CHART 2: SURPLUS VALUE GAP OVER TIME ##
plt.figure(figsize=(11, 7))

for team in focus_teams:
    team_data = (
        focus_team_surplus
        .loc[focus_team_surplus["team"] == team]
        .sort_values("season")
    )

    plt.plot(
        team_data["season"],
        team_data["surplus_rank_gap"],
        marker="o",
        label=team
    )

plt.axhline(0, linestyle="--", linewidth=1)

plt.xlabel("Season")
plt.ylabel("Surplus Rank Gap, positive is better")
plt.title("Roster Surplus Value Over Time: Focus Teams")
plt.legend()

plt.tight_layout()
plt.savefig("outputs/figures/focus_team_surplus_gap_trend.png", dpi=300)
plt.show()


## CHART 3: AVERAGE SURPLUS VALUE BY FOCUS TEAM ##
focus_avg = (
    focus_team_surplus
    .groupby(["team", "team_role"], as_index=False)
    .agg(
        avg_surplus_gap=("surplus_rank_gap", "mean"),
        avg_surplus_rank=("surplus_value_rank", "mean"),
        avg_performance_rank=("overall_rank", "mean"),
        avg_cap_cost_rank=("cap_cost_rank", "mean"),
        avg_contract_cost_proxy=("total_cap_number", "mean")
    )
    .sort_values("avg_surplus_gap", ascending=False)
)

plt.figure(figsize=(11, 7))

plt.bar(
    focus_avg["team"],
    focus_avg["avg_surplus_gap"]
)

plt.axhline(0, linestyle="--", linewidth=1)

plt.xlabel("Team")
plt.ylabel("Average Surplus Rank Gap")
plt.title("Average Roster Surplus Value, 2021–2025")

plt.tight_layout()
plt.savefig("outputs/figures/focus_team_avg_surplus_gap.png", dpi=300)
plt.show()


## CHART 4: AVERAGE COST VS PERFORMANCE FOR FOCUS TEAMS ##
plt.figure(figsize=(11, 7))

plt.scatter(
    focus_avg["avg_contract_cost_proxy"],
    focus_avg["avg_performance_rank"]
)

for _, row in focus_avg.iterrows():
    plt.text(
        row["avg_contract_cost_proxy"] + 2,
        row["avg_performance_rank"] + 0.2,
        row["team"],
        fontsize=10,
        fontweight="bold"
    )

plt.gca().invert_yaxis()

plt.xlabel("Average Public Contract Cost Proxy, $ millions")
plt.ylabel("Average Performance Rank, lower is better")
plt.title("Average Contract Cost Proxy vs Performance, 2021–2025")

plt.tight_layout()
plt.savefig("outputs/figures/focus_team_avg_cost_proxy_vs_performance.png", dpi=300)
plt.show()


## SAVE SUMMARY TABLE ##
focus_avg.to_csv("outputs/focus_team_average_surplus_summary.csv", index=False)

print("\nSaved visual outputs:")
print("- outputs/figures/2025_contract_cost_proxy_vs_performance.png")
print("- outputs/figures/focus_team_surplus_gap_trend.png")
print("- outputs/figures/focus_team_avg_surplus_gap.png")
print("- outputs/figures/focus_team_avg_cost_proxy_vs_performance.png")
print("- outputs/focus_team_average_surplus_summary.csv")

print("\nFocus Team Average Surplus Summary:")
print(focus_avg)