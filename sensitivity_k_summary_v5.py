# -*- coding: utf-8 -*-
"""
Combine V5 K-sensitivity matched lift summaries.

@author: hannah
"""

import os
import pandas as pd

OUTPUT_FILE = "outputs_v5/backtests/sensitivity_k_summary_v5.csv"

files = {
    1: "outputs_v5/backtests/k1/k1_matched_lift_summary_v5.csv",
    3: "outputs_v5/backtests/k3/k3_matched_lift_summary_v5.csv",
    5: "outputs_v5/backtests/k5/k5_matched_lift_summary_v5.csv",
}

frames = []

for k, path in files.items():
    df = pd.read_csv(path)
    df.insert(0, "k_matches", k)
    frames.append(df)

sensitivity = pd.concat(frames, ignore_index=True)

main_outcomes = [
    "appeared_next_year",
    "primary_v5_hit",
    "secondary_v5_hit",
    "next_year_meaningful_regular_role",
]

sensitivity_main = sensitivity[
    sensitivity["outcome"].isin(main_outcomes)
].copy()

os.makedirs("outputs_v5/backtests", exist_ok=True)

sensitivity.to_csv(OUTPUT_FILE, index=False)

sensitivity_main.to_csv(
    "outputs_v5/backtests/sensitivity_k_summary_main_outcomes_v5.csv",
    index=False
)

print(sensitivity_main[
    [
        "k_matches",
        "outcome",
        "matched_candidates",
        "candidate_rate",
        "matched_control_rate",
        "lift_pp",
        "lift_ci_low_pp",
        "lift_ci_high_pp",
    ]
])