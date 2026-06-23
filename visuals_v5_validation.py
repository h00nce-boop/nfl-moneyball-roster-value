# -*- coding: utf-8 -*-
"""
V5 Validation Visuals

Creating portfolio-ready visuals for the V5 matched validation section.

@author: hannah
"""

import os
import pandas as pd
import matplotlib.pyplot as plt

## SET UP ##
BACKTEST_DIR = "outputs_v5/backtests"
K3_DIR = "outputs_v5/backtests/k3"
FIGURE_DIR = "outputs_v5/figures"

os.makedirs(FIGURE_DIR, exist_ok=True)

SUMMARY_FILE = f"{K3_DIR}/k3_matched_lift_summary_v5.csv"
BY_POSITION_FILE = f"{K3_DIR}/k3_matched_lift_by_position_v5.csv"
BY_SEASON_FILE = f"{K3_DIR}/k3_matched_lift_by_season_v5.csv"
SENSITIVITY_FILE = f"{BACKTEST_DIR}/sensitivity_k_summary_main_outcomes_v5.csv"

## HELP FUNCTIONS ##
def save_horizontal_lift_chart(
    df,
    label_col,
    value_col,
    title,
    subtitle,
    xlabel,
    output_file,
    ci_low_col=None,
    ci_high_col=None,
    value_suffix=" pp",
):
    plot_df = df.copy()
    plot_df[value_col] = pd.to_numeric(plot_df[value_col], errors="coerce")

    # Reverse so highest value appears at top after barh plotting
    plot_df = plot_df.iloc[::-1].copy()

    labels = plot_df[label_col].astype(str)
    values = plot_df[value_col]

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.barh(labels, values)

    # Optional confidence interval error bars
    if ci_low_col and ci_high_col and ci_low_col in plot_df.columns and ci_high_col in plot_df.columns:
        ci_low = pd.to_numeric(plot_df[ci_low_col], errors="coerce")
        ci_high = pd.to_numeric(plot_df[ci_high_col], errors="coerce")

        lower_err = values - ci_low
        upper_err = ci_high - values

        ax.errorbar(
            values,
            labels,
            xerr=[lower_err, upper_err],
            fmt="none",
            capsize=4,
            linewidth=1,
        )

    ax.axvline(0, linewidth=1)

    # Value labels
    x_range = values.max() - values.min()
    if pd.isna(x_range) or x_range == 0:
        x_range = 1

    label_offset = x_range * 0.03

    for y, value in enumerate(values):
        if pd.isna(value):
            continue

        if value >= 0:
            x = value + label_offset
            ha = "left"
        else:
            x = value - label_offset
            ha = "right"

        ax.text(
            x,
            y,
            f"{value:.1f}{value_suffix}",
            va="center",
            ha=ha,
            fontsize=10,
        )

    ax.set_title(title, fontsize=16, pad=18)

    if subtitle:
        ax.text(
            0,
            1.02,
            subtitle,
            transform=ax.transAxes,
            fontsize=10,
            va="bottom",
        )

    ax.set_xlabel(xlabel)
    ax.set_ylabel("")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.grid(axis="x", alpha=0.25)

    plt.tight_layout()
    plt.savefig(output_file, dpi=250, bbox_inches="tight")
    plt.close()

    print(f"Saved: {output_file}")


def clean_outcome_label(outcome):
    labels = {
        "appeared_next_year": "Appeared\nNext Year",
        "primary_v5_hit": "Top-Half\nProduction",
        "secondary_v5_hit": "Positive\nSurplus",
        "next_year_meaningful_regular_role": "Meaningful\nRole",
        "retained_positive_surplus": "Positive\nSurplus",
        "next_year_top_half_position": "Top-Half\nProduction",
    }

    return labels.get(outcome, outcome)

## READ IN DATA ##
summary = pd.read_csv(SUMMARY_FILE)
by_position = pd.read_csv(BY_POSITION_FILE)
by_season = pd.read_csv(BY_SEASON_FILE)
sensitivity = pd.read_csv(SENSITIVITY_FILE)

## MATCHED LIFT BY OUTCOME ##
main_outcomes = [
    "appeared_next_year",
    "primary_v5_hit",
    "secondary_v5_hit",
    "next_year_meaningful_regular_role",
]

summary_main = summary[
    summary["outcome"].isin(main_outcomes)
].copy()

summary_main["outcome_label"] = summary_main["outcome"].map(clean_outcome_label)

outcome_order = [
    "Top-Half\nProduction",
    "Positive\nSurplus",
    "Meaningful\nRole",
    "Appeared\nNext Year",
]

summary_main["outcome_label"] = pd.Categorical(
    summary_main["outcome_label"],
    categories=outcome_order,
    ordered=True,
)

summary_main = summary_main.sort_values("outcome_label")

save_horizontal_lift_chart(
    df=summary_main,
    label_col="outcome_label",
    value_col="lift_pp",
    title="V5 Matched Lift by Outcome",
    subtitle="Lift vs. matched rookie-contract controls, K=3",
    xlabel="Lift in percentage points",
    output_file=f"{FIGURE_DIR}/v5_matched_lift_by_outcome.png",
    ci_low_col=None,
    ci_high_col=None,
)

## PRIMARY LIFT BY POSITION ##
position_primary = by_position[
    by_position["outcome"].eq("primary_v5_hit")
].copy()

position_primary = position_primary.sort_values("lift_pp", ascending=True)

save_horizontal_lift_chart(
    df=position_primary,
    label_col="candidate_position_final",
    value_col="lift_pp",
    title="V5 Primary Hit Lift by Position",
    subtitle="Primary hit = next-season top-half production within position, K=3",
    xlabel="Lift in percentage points",
    output_file=f"{FIGURE_DIR}/v5_primary_lift_by_position.png",
    ci_low_col="lift_ci_low_pp",
    ci_high_col="lift_ci_high_pp",
)

## PRIMARY LIFT BY SZN ##
season_primary = by_season[
    by_season["outcome"].eq("primary_v5_hit")
].copy()

season_primary["candidate_season"] = season_primary["candidate_season"].astype(int).astype(str)
season_primary = season_primary.sort_values("candidate_season", ascending=False)

save_horizontal_lift_chart(
    df=season_primary,
    label_col="candidate_season",
    value_col="lift_pp",
    title="V5 Primary Hit Lift by Validation Season",
    subtitle="Positive in three of four validation seasons; 2024 was the weak cohort",
    xlabel="Lift in percentage points",
    output_file=f"{FIGURE_DIR}/v5_primary_lift_by_season.png",
    ci_low_col="lift_ci_low_pp",
    ci_high_col="lift_ci_high_pp",
)

## PRIMARY LIFT SENSITIVITY FOR K = 1,3,5 ##
sensitivity_primary = sensitivity[
    sensitivity["outcome"].eq("primary_v5_hit")
].copy()

sensitivity_primary = sensitivity_primary.sort_values("k_matches")

fig, ax = plt.subplots(figsize=(9, 5.5))

ax.plot(
    sensitivity_primary["k_matches"],
    sensitivity_primary["lift_pp"],
    marker="o",
    linewidth=2,
)

ax.errorbar(
    sensitivity_primary["k_matches"],
    sensitivity_primary["lift_pp"],
    yerr=[
        sensitivity_primary["lift_pp"] - sensitivity_primary["lift_ci_low_pp"],
        sensitivity_primary["lift_ci_high_pp"] - sensitivity_primary["lift_pp"],
    ],
    fmt="none",
    capsize=4,
    linewidth=1,
)

for _, row in sensitivity_primary.iterrows():
    ax.text(
        row["k_matches"],
        row["lift_pp"] + 0.8,
        f"{row['lift_pp']:.1f} pp",
        ha="center",
        va="bottom",
        fontsize=10,
    )

ax.axhline(0, linewidth=1)

ax.set_title("V5 Primary Hit Lift Sensitivity", fontsize=16, pad=18)
ax.text(
    0,
    1.02,
    "Primary lift remains positive across alternate matched-control counts",
    transform=ax.transAxes,
    fontsize=10,
    va="bottom",
)

ax.set_xlabel("Matched controls per candidate")
ax.set_ylabel("Lift in percentage points")

ax.set_xticks(sensitivity_primary["k_matches"])

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.grid(axis="y", alpha=0.25)

plt.tight_layout()
plt.savefig(f"{FIGURE_DIR}/v5_primary_lift_sensitivity_k.png", dpi=250, bbox_inches="tight")
plt.close()

print(f"Saved: {FIGURE_DIR}/v5_primary_lift_sensitivity_k.png")

## PRINTING SUMMARY FOR REPORT ##
print("\nMain V5 matched outcome lifts:")
print(
    summary_main[
        [
            "outcome",
            "matched_candidates",
            "candidate_rate",
            "matched_control_rate",
            "lift_pp",
            "lift_ci_low_pp",
            "lift_ci_high_pp",
        ]
    ].sort_values("outcome")
)

print("\nPrimary lift by position:")
print(
    position_primary[
        [
            "candidate_position_final",
            "matched_candidates",
            "candidate_rate",
            "matched_control_rate",
            "lift_pp",
            "lift_ci_low_pp",
            "lift_ci_high_pp",
        ]
    ]
)

print("\nPrimary lift by season:")
print(
    season_primary[
        [
            "candidate_season",
            "matched_candidates",
            "candidate_rate",
            "matched_control_rate",
            "lift_pp",
            "lift_ci_low_pp",
            "lift_ci_high_pp",
        ]
    ]
)

print("\nSensitivity by K:")
print(
    sensitivity_primary[
        [
            "k_matches",
            "matched_candidates",
            "candidate_rate",
            "matched_control_rate",
            "lift_pp",
            "lift_ci_low_pp",
            "lift_ci_high_pp",
        ]
    ]
)
