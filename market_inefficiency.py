# -*- coding: utf-8 -*-
"""
Market Inefficiency Analysis - V3/V4 Context

Goal:
Summarize which offensive skill-player archetypes generate surplus value
using the V3 confidence + contract-context player table.

This version updates the original market inefficiency analysis by using:
- V2 confidence fields
- V3 draft-capital and contract-stage fields
- V4 validation context where available

Outputs are saved to:
- outputs_v3/summary/

@author: hannah
"""

import os
import pandas as pd


## SETUP ##

INPUT_FILE = "outputs_v3/player_value_2021_2025_v3_contract_context.csv"
OUTPUT_DIR = "outputs_v3/summary"

V4_LIFT_FILE = "outputs_v4/backtests/backtest_lift_model_vs_not_flagged_clean.csv"
V4_THRESHOLD_FILE = "outputs_v4/backtests/threshold_sensitivity_lift.csv"
V4_SEASON_FILE = "outputs_v4/backtests/season_stability_lift_by_season.csv"

os.makedirs(OUTPUT_DIR, exist_ok=True)

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)
pd.set_option("display.max_rows", 100)

player_value = pd.read_csv(INPUT_FILE)

print("Loaded V3 player value file:", player_value.shape)


## REQUIRED COLUMN CHECK ##

required_columns = [
    "season",
    "team",
    "player_id",
    "player_name",
    "position_final",
    "production_score",
    "total_epa",
    "cap_number",
    "player_surplus_gap",
    "player_value_tier",
    "overall_confidence",
    "estimated_contract_stage",
    "is_likely_rookie_contract",
    "draft_capital_bucket",
    "surplus_context",
]

missing_columns = [
    col for col in required_columns if col not in player_value.columns
]

if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")


## ANALYSIS UNIVERSE ##

# Public-facing market-inefficiency conclusions should only use rows
# with high confidence and a valid public contract-cost proxy.
# Missing, unmatched, or zero-cost rows are saved for auditability,
# but they are not treated as "cheap" players.
valid_market_mask = (
    (player_value["overall_confidence"] == "high")
    & (player_value["has_contract_match"] == True)
    & (player_value["has_missing_contract"] == False)
    & (player_value["cap_number"].notna())
    & (player_value["cap_number"] > 0)
)

market_universe = player_value.loc[valid_market_mask].copy()
excluded_market_rows = player_value.loc[~valid_market_mask].copy()

excluded_market_rows.to_csv(
    f"{OUTPUT_DIR}/market_inefficiency_excluded_rows_v3.csv",
    index=False,
)

print("Market analysis universe:", market_universe.shape)
print("Excluded from market analysis:", excluded_market_rows.shape)
print(market_universe["position_final"].value_counts())

if market_universe.empty:
    raise ValueError(
        "Market analysis universe is empty after applying confidence and valid-cost filters."
    )


## COST TIER FUNCTION ##

def assign_cost_tier(cap_number):
    """
    Cost tiers use cap_number as a public contract-cost proxy.
    Cap values are treated as millions of dollars.

    Missing, unmatched, or zero-cost rows are intentionally excluded
    before this function is called. They are saved in the excluded-row
    audit file instead of being treated as a public-facing cost tier.
    """
    if pd.isna(cap_number) or cap_number <= 0:
        return pd.NA
    if cap_number >= 20:
        return "Premium cost"
    if cap_number >= 10:
        return "High cost"
    if cap_number >= 4:
        return "Mid cost"
    return "Low cost"


def assign_surplus_bucket(gap):
    """
    Readable surplus bucket based on player_surplus_gap.
    """
    if pd.isna(gap):
        return "unknown"
    elif gap >= 20:
        return "elite_surplus"
    elif gap >= 10:
        return "strong_surplus"
    elif gap >= 5:
        return "positive_surplus"
    elif gap > -5:
        return "neutral"
    else:
        return "negative_surplus"


market_universe["cost_tier"] = market_universe["cap_number"].apply(
    assign_cost_tier
)

market_universe = market_universe.dropna(subset=["cost_tier"]).copy()

market_universe["surplus_bucket"] = market_universe["player_surplus_gap"].apply(
    assign_surplus_bucket
)


## HELPER SUMMARY FUNCTION ##

def summarize_group(df, group_cols):
    """
    Summarize surplus value for a group of players.
    """
    summary = (
        df
        .groupby(group_cols, as_index=False)
        .agg(
            players_evaluated=("player_id", "count"),
            avg_surplus_gap=("player_surplus_gap", "mean"),
            median_surplus_gap=("player_surplus_gap", "median"),
            pct_positive_surplus=(
                "player_surplus_gap",
                lambda x: (x > 0).mean()
            ),
            pct_strong_surplus=(
                "player_surplus_gap",
                lambda x: (x >= 10).mean()
            ),
            avg_cap_number=("cap_number", "mean"),
            avg_production_score=("production_score", "mean"),
            avg_total_epa=("total_epa", "mean"),
            rookie_contract_rate=(
                "is_likely_rookie_contract",
                lambda x: (x == True).mean()
            ),
        )
    )

    summary = summary.sort_values(
        "avg_surplus_gap",
        ascending=False
    )
    
    summary["meets_min_group_size"] = summary["players_evaluated"] >= 10

    return summary


## POSITION SUMMARY ##

position_summary = summarize_group(
    market_universe,
    ["position_final"]
)

position_summary.to_csv(
    f"{OUTPUT_DIR}/market_inefficiency_position_summary_v3.csv",
    index=False
)


## COST TIER SUMMARY ##

cost_tier_summary = summarize_group(
    market_universe,
    ["position_final", "cost_tier"]
)

cost_tier_summary.to_csv(
    f"{OUTPUT_DIR}/market_inefficiency_cost_tier_summary_v3.csv",
    index=False
)


## CONTRACT STAGE SUMMARY ##

contract_stage_summary = summarize_group(
    market_universe,
    ["estimated_contract_stage"]
)

contract_stage_summary.to_csv(
    f"{OUTPUT_DIR}/market_inefficiency_contract_stage_summary_v3.csv",
    index=False
)


## POSITION x CONTRACT STAGE SUMMARY ##

position_contract_stage_summary = summarize_group(
    market_universe,
    ["position_final", "estimated_contract_stage"]
)

position_contract_stage_summary.to_csv(
    f"{OUTPUT_DIR}/market_inefficiency_position_contract_stage_summary_v3.csv",
    index=False
)


## DRAFT CAPITAL SUMMARY ##

draft_capital_summary = summarize_group(
    market_universe,
    ["draft_capital_bucket"]
)

draft_capital_summary.to_csv(
    f"{OUTPUT_DIR}/market_inefficiency_draft_capital_summary_v3.csv",
    index=False
)


## POSITION x DRAFT CAPITAL SUMMARY ##

position_draft_capital_summary = summarize_group(
    market_universe,
    ["position_final", "draft_capital_bucket"]
)

position_draft_capital_summary.to_csv(
    f"{OUTPUT_DIR}/market_inefficiency_position_draft_capital_summary_v3.csv",
    index=False
)


## SURPLUS CONTEXT SUMMARY ##

surplus_context_summary = summarize_group(
    market_universe,
    ["surplus_context"]
)

surplus_context_summary.to_csv(
    f"{OUTPUT_DIR}/market_inefficiency_surplus_context_summary_v3.csv",
    index=False
)


## POSITION x COST TIER x CONTRACT STAGE SUMMARY ##

position_cost_stage_summary = summarize_group(
    market_universe,
    ["position_final", "cost_tier", "estimated_contract_stage"]
)

position_cost_stage_summary.to_csv(
    f"{OUTPUT_DIR}/market_inefficiency_position_cost_stage_summary_v3.csv",
    index=False
)


## TOP BARGAINS BY POSITION AND SEASON ##

top_bargain_columns = [
    "season",
    "player_name",
    "team",
    "position_final",
    "production_score",
    "total_epa",
    "cap_number",
    "cost_tier",
    "player_surplus_gap",
    "surplus_bucket",
    "draft_year",
    "draft_round",
    "draft_pick",
    "draft_capital_bucket",
    "years_since_drafted",
    "estimated_contract_stage",
    "is_likely_rookie_contract",
    "surplus_context",
    "overall_confidence",
]

top_bargain_columns = [
    col for col in top_bargain_columns if col in market_universe.columns
]

top_bargains_by_position = (
    market_universe
    .sort_values(
        ["season", "position_final", "player_surplus_gap"],
        ascending=[True, True, False]
    )
    .groupby(["season", "position_final"])
    .head(10)
    [top_bargain_columns]
)

top_bargains_by_position.to_csv(
    f"{OUTPUT_DIR}/market_inefficiency_top_bargains_by_position_v3.csv",
    index=False
)


## LATEST-SEASON MARKET WATCHLIST ##

latest_season = int(market_universe["season"].max())

latest_market_watchlist = market_universe[
    (market_universe["season"] == latest_season) &
    (market_universe["is_likely_rookie_contract"] == True) &
    (market_universe["player_surplus_gap"] >= 5)
].copy()

latest_market_watchlist = latest_market_watchlist.sort_values(
    ["player_surplus_gap", "production_score"],
    ascending=[False, False]
)

latest_market_watchlist[top_bargain_columns].to_csv(
    f"{OUTPUT_DIR}/market_inefficiency_{latest_season}_watchlist_v3.csv",
    index=False
)


## OPTIONAL V4 VALIDATION CONTEXT ##

if os.path.exists(V4_LIFT_FILE):
    v4_lift = pd.read_csv(V4_LIFT_FILE)

    preferred_v4_columns = [
        "position_final",
        "players_model",
        "players_baseline",
        "hit_rate_model",
        "hit_rate_baseline",
        "hit_rate_lift",
        "appearance_rate_lift",
        "next_surplus_gap_lift",
        "next_production_score_lift",
    ]

    v4_validation_columns = [
        col for col in preferred_v4_columns if col in v4_lift.columns
    ]

    v4_validation_context = v4_lift[v4_validation_columns].copy()

    v4_validation_context.to_csv(
        f"{OUTPUT_DIR}/market_inefficiency_v4_position_validation_context.csv",
        index=False
    )

else:
    v4_validation_context = pd.DataFrame()
    print("V4 lift file not found. Skipping V4 validation context.")


if os.path.exists(V4_THRESHOLD_FILE):
    v4_threshold = pd.read_csv(V4_THRESHOLD_FILE)

    v4_threshold_overall = (
        v4_threshold
        .loc[v4_threshold["position_final"] == "ALL"]
        .copy()
    )

    v4_threshold_overall.to_csv(
        f"{OUTPUT_DIR}/market_inefficiency_v4_threshold_context.csv",
        index=False
    )


if os.path.exists(V4_SEASON_FILE):
    v4_season = pd.read_csv(V4_SEASON_FILE)

    v4_season.to_csv(
        f"{OUTPUT_DIR}/market_inefficiency_v4_season_context.csv",
        index=False
    )


## AUTO-GENERATED MARKET TAKEAWAYS ##

takeaway_rows = []

if len(position_summary) > 0:
    best_position = position_summary.iloc[0]

    takeaway_rows.append(
        {
            "finding": "Highest average surplus position",
            "evidence": (
                f"{best_position['position_final']} had the highest average "
                f"surplus gap in the high-confidence V3 market universe "
                f"({best_position['avg_surplus_gap']:.2f})."
            ),
            "interpretation": (
                "This position profile may be where public-data surplus value "
                "is easiest to identify."
            ),
        }
    )


headline_cost_tier_summary = cost_tier_summary[
    cost_tier_summary["meets_min_group_size"] == True
].copy()

if len(headline_cost_tier_summary) == 0:
    headline_cost_tier_summary = cost_tier_summary.copy()

if len(cost_tier_summary) > 0:
    best_cost_tier = cost_tier_summary.iloc[0]

  takeaway_rows.append(
        {
            "finding": "Best position-cost archetype",
            "evidence": (
                f"{best_cost_tier['position_final']} / "
                f"{best_cost_tier['cost_tier']} had the highest average "
                f"surplus gap among valid-cost groups "
                f"({best_cost_tier['avg_surplus_gap']:.2f})."
            ),
            "interpretation": (
                "The model is strongest when cost tier and position context "
                "are evaluated together rather than treating all cheap players "
                "as the same."
            ),
        }
    )


if (
    "estimated_contract_stage" in contract_stage_summary.columns
    and len(contract_stage_summary) > 0
):
    best_contract_stage = contract_stage_summary.iloc[0]

    takeaway_rows.append(
        {
            "finding": "Best contract-stage archetype",
            "evidence": (
                f"{best_contract_stage['estimated_contract_stage']} players "
                f"had the highest average surplus gap "
                f"({best_contract_stage['avg_surplus_gap']:.2f})."
            ),
            "interpretation": (
                "This connects the market-inefficiency analysis to the core "
                "contract-cycle thesis."
            ),
        }
    )


if len(v4_validation_context) > 0:
    preferred_v4_metric = "hit_rate_lift"

    if preferred_v4_metric in v4_validation_context.columns:
        best_v4_position = (
            v4_validation_context
            .sort_values(preferred_v4_metric, ascending=False)
            .iloc[0]
        )

        takeaway_rows.append(
            {
                "finding": "Strongest validated V4 position signal",
                "evidence": (
                    f"{best_v4_position['position_final']} had the largest "
                    f"V4 hit-rate lift "
                    f"({best_v4_position[preferred_v4_metric]:.3f}) versus the "
                    f"not-flagged rookie-contract baseline."
                ),
                "interpretation": (
                    "This is the cleanest bridge between descriptive market "
                    "inefficiency and next-season validation. It should be "
                    "interpreted as first-pass validation, not as a final "
                    "prediction model."
                ),
            }
        )


market_takeaways = pd.DataFrame(takeaway_rows)

market_takeaways.to_csv(
    f"{OUTPUT_DIR}/market_inefficiency_takeaways_v3.csv",
    index=False
)



## PRINT USEFUL VIEWS ##

print("\nPosition Summary:")
print(position_summary.round(3).to_string(index=False))

print("\nCost Tier Summary:")
print(cost_tier_summary.round(3).to_string(index=False))

print("\nContract Stage Summary:")
print(contract_stage_summary.round(3).to_string(index=False))

print("\nSurplus Context Summary:")
print(surplus_context_summary.round(3).to_string(index=False))

if len(v4_validation_context) > 0:
    print("\nV4 Position Validation Context:")
    print(v4_validation_context.round(3).to_string(index=False))

print("\nMarket Inefficiency Takeaways:")
print(market_takeaways.to_string(index=False))

print("\nSaved updated market inefficiency outputs to:", OUTPUT_DIR)