# -*- coding: utf-8 -*-
"""
V4 Backtest Visuals

Creates static validation visuals for the V4 NFL Moneyball backtest.

Outputs:
- threshold sensitivity hit-rate lift
- threshold sensitivity next-surplus-gap lift
- threshold sensitivity by position
- season stability hit-rate lift
- season stability next-surplus-gap lift

@author: hannah
"""

import os
import pandas as pd
import matplotlib.pyplot as plt


## SETUP ##

OUTPUT_DIR = "outputs_v4/figures"
os.makedirs(OUTPUT_DIR, exist_ok=True)

THRESHOLD_FILE = "outputs_v4/backtests/threshold_sensitivity_lift.csv"
SEASON_FILE = "outputs_v4/backtests/season_stability_lift_by_season.csv"
SEASON_POSITION_FILE = "outputs_v4/backtests/season_stability_lift_by_season_position.csv"

threshold_lift = pd.read_csv(THRESHOLD_FILE)
season_lift = pd.read_csv(SEASON_FILE)
season_position_lift = pd.read_csv(SEASON_POSITION_FILE)

print("Loaded threshold lift:", threshold_lift.shape)
print("Loaded season lift:", season_lift.shape)
print("Loaded season-position lift:", season_position_lift.shape)


## HELPER ##

def save_current_figure(filename):
    path = f"{OUTPUT_DIR}/{filename}"
    plt.tight_layout()
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    print("Saved:", path)


## 1. OVERALL THRESHOLD HIT-RATE LIFT ##

overall_threshold = (
    threshold_lift
    .loc[threshold_lift["position_final"] == "ALL"]
    .sort_values("threshold")
    .copy()
)

plt.figure(figsize=(9, 5))
plt.plot(
    overall_threshold["threshold"],
    overall_threshold["hit_rate_lift"],
    marker="o"
)
plt.axhline(0, linewidth=1)
plt.title("V4 Threshold Sensitivity: Overall Hit-Rate Lift")
plt.xlabel("Player Surplus Gap Threshold")
plt.ylabel("Hit-Rate Lift vs Not-Flagged Baseline")
plt.grid(True, alpha=0.3)

save_current_figure("v4_threshold_sensitivity_overall_hit_rate_lift.png")


## 2. OVERALL THRESHOLD NEXT-SURPLUS-GAP LIFT ##

plt.figure(figsize=(9, 5))
plt.plot(
    overall_threshold["threshold"],
    overall_threshold["next_surplus_gap_lift"],
    marker="o"
)
plt.axhline(0, linewidth=1)
plt.title("V4 Threshold Sensitivity: Overall Next-Season Surplus-Gap Lift")
plt.xlabel("Player Surplus Gap Threshold")
plt.ylabel("Next-Season Surplus-Gap Lift")
plt.grid(True, alpha=0.3)

save_current_figure("v4_threshold_sensitivity_overall_next_surplus_gap_lift.png")


## 3. THRESHOLD HIT-RATE LIFT BY POSITION ##

threshold_by_position = (
    threshold_lift
    .loc[threshold_lift["position_final"] != "ALL"]
    .sort_values(["position_final", "threshold"])
    .copy()
)

plt.figure(figsize=(9, 5))

for position, group in threshold_by_position.groupby("position_final"):
    plt.plot(
        group["threshold"],
        group["hit_rate_lift"],
        marker="o",
        label=position
    )

plt.axhline(0, linewidth=1)
plt.title("V4 Threshold Sensitivity: Hit-Rate Lift by Position")
plt.xlabel("Player Surplus Gap Threshold")
plt.ylabel("Hit-Rate Lift vs Not-Flagged Baseline")
plt.legend(title="Position")
plt.grid(True, alpha=0.3)

save_current_figure("v4_threshold_sensitivity_hit_rate_lift_by_position.png")


## 4. THRESHOLD NEXT-SURPLUS-GAP LIFT BY POSITION ##

plt.figure(figsize=(9, 5))

for position, group in threshold_by_position.groupby("position_final"):
    plt.plot(
        group["threshold"],
        group["next_surplus_gap_lift"],
        marker="o",
        label=position
    )

plt.axhline(0, linewidth=1)
plt.title("V4 Threshold Sensitivity: Next-Season Surplus-Gap Lift by Position")
plt.xlabel("Player Surplus Gap Threshold")
plt.ylabel("Next-Season Surplus-Gap Lift")
plt.legend(title="Position")
plt.grid(True, alpha=0.3)

save_current_figure("v4_threshold_sensitivity_next_surplus_gap_lift_by_position.png")


## 5. SEASON STABILITY HIT-RATE LIFT ##

season_lift = season_lift.sort_values("season").copy()

plt.figure(figsize=(9, 5))
plt.plot(
    season_lift["season"],
    season_lift["hit_rate_lift"],
    marker="o"
)
plt.axhline(0, linewidth=1)
plt.title("V4 Season Stability: Hit-Rate Lift by Candidate Season")
plt.xlabel("Candidate Season")
plt.ylabel("Hit-Rate Lift vs Not-Flagged Baseline")
plt.xticks(season_lift["season"])
plt.grid(True, alpha=0.3)

save_current_figure("v4_season_stability_hit_rate_lift.png")


## 6. SEASON STABILITY NEXT-SURPLUS-GAP LIFT ##

plt.figure(figsize=(9, 5))
plt.plot(
    season_lift["season"],
    season_lift["next_surplus_gap_lift"],
    marker="o"
)
plt.axhline(0, linewidth=1)
plt.title("V4 Season Stability: Next-Season Surplus-Gap Lift")
plt.xlabel("Candidate Season")
plt.ylabel("Next-Season Surplus-Gap Lift")
plt.xticks(season_lift["season"])
plt.grid(True, alpha=0.3)

save_current_figure("v4_season_stability_next_surplus_gap_lift.png")


## 7. SEASON STABILITY HIT-RATE LIFT BY POSITION ##

season_position_lift = season_position_lift.sort_values(
    ["position_final", "season"]
).copy()

plt.figure(figsize=(9, 5))

for position, group in season_position_lift.groupby("position_final"):
    plt.plot(
        group["season"],
        group["hit_rate_lift"],
        marker="o",
        label=position
    )

plt.axhline(0, linewidth=1)
plt.title("V4 Season Stability: Hit-Rate Lift by Position")
plt.xlabel("Candidate Season")
plt.ylabel("Hit-Rate Lift vs Not-Flagged Baseline")
plt.legend(title="Position")
plt.grid(True, alpha=0.3)

save_current_figure("v4_season_stability_hit_rate_lift_by_position.png")


print("\nSaved V4 visuals to:", OUTPUT_DIR)