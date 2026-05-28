# -*- coding: utf-8 -*-
"""
Streamlit dashboard for the NFL Moneyball project.

The dashboard allows users to explore team-level surplus value, focus-team
trends, player-level skill-position value, and league-wide player bargains.

Run with:
streamlit run app.py

@author: hannah
"""
import pandas as pd
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="NFL Moneyball Dashboard",
    layout="wide"
)

st.title("NFL Moneyball: Roster Surplus Value Dashboard")

st.markdown(
    """
    This dashboard explores NFL roster surplus value using public data.

    The core question: **which teams and players produced more than their contract-cost profile would suggest?**
    """
)

st.caption(
    "Seasons use NFL season-year labels. The project covers the 2021–2025 NFL seasons. V4 backtests use 2021–2024 candidate seasons, while 2025 is treated as the latest-season watchlist because 2026 outcomes are not available yet."
)


## LOAD DATA ##
team_surplus = pd.read_csv("outputs/team_surplus_2021_2025.csv")
focus_team_surplus = pd.read_csv("outputs/focus_team_surplus_2021_2025.csv")

# Use v3 player outputs so the dashboard includes confidence,
# draft-capital, and contract-cycle context.
player_value = pd.read_csv("outputs_v3/player_value_2021_2025_v3_contract_context.csv")
focus_player_value = pd.read_csv("outputs_v3/focus_player_value_2021_2025_v3_contract_context.csv")

## OPTIONAL V4 DATA ##
v4_threshold_path = Path("outputs_v4/backtests/threshold_sensitivity_lift.csv")
v4_season_path = Path("outputs_v4/backtests/season_stability_lift_by_season.csv")
v4_watchlist_path = Path("outputs_v4/backtests/candidate_review_2025_watchlist.csv")

v4_threshold = pd.read_csv(v4_threshold_path) if v4_threshold_path.exists() else None
v4_season = pd.read_csv(v4_season_path) if v4_season_path.exists() else None
v4_watchlist = pd.read_csv(v4_watchlist_path) if v4_watchlist_path.exists() else None

## SIDEBAR ##
st.sidebar.header("Filters")

seasons = sorted(team_surplus["season"].unique())

season = st.sidebar.selectbox(
    "Season",
    seasons,
    index=len(seasons) - 1
)

focus_teams = ["PHI", "NYG", "CLE", "BAL", "DET"]

team = st.sidebar.selectbox(
    "Focus Team",
    focus_teams,
    index=0
)

position_options = ["All"] + sorted(player_value["position_final"].dropna().unique().tolist())

position_filter = st.sidebar.selectbox(
    "Position",
    position_options,
    index=0
)

contract_stage_options = ["All"] + sorted(
    player_value["estimated_contract_stage"].dropna().unique().tolist()
)

contract_stage_filter = st.sidebar.selectbox(
    "Contract Stage",
    contract_stage_options,
    index=0
)

draft_bucket_options = ["All"] + sorted(
    player_value["draft_capital_bucket"].dropna().unique().tolist()
)

draft_bucket_filter = st.sidebar.selectbox(
    "Draft Capital",
    draft_bucket_options,
    index=0
)

surplus_context_options = ["All"] + sorted(
    player_value["surplus_context"].dropna().unique().tolist()
)

surplus_context_filter = st.sidebar.selectbox(
    "Surplus Context",
    surplus_context_options,
    index=0
)

def apply_player_filters(df):
    filtered = df.copy()

    if position_filter != "All":
        filtered = filtered[filtered["position_final"] == position_filter]

    if contract_stage_filter != "All":
        filtered = filtered[filtered["estimated_contract_stage"] == contract_stage_filter]

    if draft_bucket_filter != "All":
        filtered = filtered[filtered["draft_capital_bucket"] == draft_bucket_filter]

    if surplus_context_filter != "All":
        filtered = filtered[filtered["surplus_context"] == surplus_context_filter]

    return filtered

## EXPLANATION ##
with st.expander("Methodology"):
    st.markdown(
        """
        **Team surplus value** compares a team's performance rank against its contract-cost rank.

        `surplus_rank_gap = cap_cost_rank - overall_rank`

        Positive values indicate that a team performed better than its cost rank.

        **Player surplus value** compares a player's production rank against his cost rank within his position group.

        `player_surplus_gap = cost_rank_position - production_rank_position`

        Positive values indicate that a player produced better than his cost rank.

        Contract cost is treated as a public-data proxy, not audited official salary-cap accounting.

        **V2 confidence update:** the player-value model now includes data-quality flags for contract matching and sample size. Missing public contract data is no longer treated as true zero cost. Low-sample players are preserved in a diagnostic file but excluded from the final ranked player table.
        
        **V3 contract-context update:** the player-value model now adds draft-capital and estimated contract-stage context. This helps distinguish generally cheap production from production that may be structurally underpriced because the player is still on a rookie-contract or pre-extension timeline.
        
        **V4 backtest update:** the model now tests whether high-confidence rookie-contract surplus candidates outperform similar rookie-contract players the model did not flag. V4 uses 2021–2024 as candidate seasons and evaluates each candidate using the following season. The 2025 season is used as the latest-season watchlist because 2026 outcomes are not available yet.
        """
    )


## TEAM-LEVEL VIEW ##
st.header("Team-Level Surplus Value")

team_season = (
    team_surplus
    .query("season == @season")
    .sort_values("surplus_value_rank")
)

col1, col2 = st.columns(2)

with col1:
    st.subheader(f"{season} Team Surplus Rankings")
    st.dataframe(
        team_season[[
            "team",
            "overall_rank",
            "cap_cost_rank",
            "surplus_rank_gap",
            "surplus_value_rank",
            "surplus_tier"
        ]],
        use_container_width=True
    )

with col2:
    st.subheader(f"{season} Cost Proxy vs Performance")
    st.scatter_chart(
        team_season,
        x="total_cap_number",
        y="performance_score",
        color="team"
    )


## FOCUS TEAM TREND ##
st.header("Focus Team Trend")

focus_trend = (
    focus_team_surplus
    .loc[focus_team_surplus["team"].isin(focus_teams)]
    .copy()
)

st.line_chart(
    focus_trend,
    x="season",
    y="surplus_rank_gap",
    color="team"
)


## SELECTED TEAM VIEW ##
st.header(f"{team} Team Detail")

selected_team = (
    team_surplus
    .query("team == @team")
    .sort_values("season")
)

st.dataframe(
    selected_team[[
        "season",
        "overall_rank",
        "cap_cost_rank",
        "surplus_rank_gap",
        "surplus_value_rank",
        "surplus_tier",
        "offensive_epa_per_play",
        "defensive_epa_allowed_per_play",
        "total_cap_number"
    ]],
    use_container_width=True
)


## PLAYER-LEVEL VIEW ##
st.header("Player-Level Skill Position Value")

st.caption(
    "Cap number is shown in millions of dollars based on the public contract-cost proxy."
)

team_players = (
    focus_player_value
    .query("season == @season and team == @team")
    .copy()
)

team_players = apply_player_filters(team_players)

team_players = team_players.sort_values(
    "player_surplus_gap",
    ascending=False
)

st.subheader(f"{team} Skill Player Value, {season}")

st.caption(
    "Player rankings use V3 contract-context outputs with V2 confidence fields. Low-sample players are excluded from the final ranked table, while missing public contract matches are flagged for interpretation."
)

st.dataframe(
    team_players[
        [
            "player_name",
            "position_final",
            "production_score",
            "total_epa",
            "cap_number",
            "player_surplus_gap",
            "player_value_tier",
            "draft_year",
            "draft_round",
            "draft_pick",
            "draft_capital_bucket",
            "years_since_drafted",
            "estimated_contract_stage",
            "surplus_context",
            "overall_confidence"
        ]
    ],
    use_container_width=True
)

## LEAGUE-WIDE PLAYER BARGAINS ##
st.header("League-Wide Skill Player Bargains")

top_players = (
    player_value
    .query("season == @season")
    .copy()
)

top_players = apply_player_filters(top_players)

top_players = (
    top_players
    .sort_values("player_surplus_gap", ascending=False)
    .head(25)
)

st.caption(
    "League-wide bargains are shown from the V3 ranked player table, including confidence, draft-capital, and contract-stage context."
)

st.dataframe(
    top_players[
        [
            "player_name",
            "team",
            "position_final",
            "production_score",
            "total_epa",
            "cap_number",
            "player_surplus_gap",
            "player_value_tier",
            "draft_year",
            "draft_round",
            "draft_pick",
            "draft_capital_bucket",
            "years_since_drafted",
            "estimated_contract_stage",
            "surplus_context",
            "overall_confidence"
        ]
    ],
    use_container_width=True
)

## PRE-EXTENSION CANDIDATES ##
st.header("Pre-Extension Breakout Candidates")

pre_extension = (
    player_value
    .query("season == @season")
    .copy()
)

pre_extension = apply_player_filters(pre_extension)

pre_extension = pre_extension[
    pre_extension["surplus_context"].isin(
        ["pre_extension_breakout", "rookie_contract_surplus"]
    )
]

pre_extension = pre_extension.sort_values(
    "player_surplus_gap",
    ascending=False
).head(25)

st.caption(
    "This table highlights players with positive surplus value who are still "
    "estimated to be on rookie-contract or fifth-year-option timelines."
)

if season == 2025:
    st.caption(
        "The selected 2025 season is the latest season in the dataset. These players are watchlist candidates, not backtested hits, because 2026 outcomes are not available yet."
    )

st.dataframe(
    pre_extension[
        [
            "player_name",
            "team",
            "position_final",
            "player_surplus_gap",
            "production_score",
            "cap_number",
            "draft_year",
            "draft_round",
            "draft_pick",
            "draft_capital_bucket",
            "years_since_drafted",
            "estimated_contract_stage",
            "surplus_context",
            "overall_confidence"
        ]
    ],
    use_container_width=True
)

## V4 BACKTEST AND DECISION SUPPORT ##
st.header("V4 Backtest & Decision Support")

st.markdown(
    """
    V4 tests whether model-flagged rookie-contract surplus candidates performed better the following season than similar rookie-contract players the model did not flag.
    """
)

if v4_threshold is None or v4_season is None or v4_watchlist is None:
    st.info(
        "V4 outputs were not found. Run the V4 backtest, threshold sensitivity, season stability, and candidate review scripts to populate this section."
    )
else:
    tab1, tab2, tab3 = st.tabs(
        [
            "Threshold Sensitivity",
            "Season Stability",
            "2025 Watchlist",
        ]
    )

    with tab1:
        st.subheader("Threshold Sensitivity")

        st.caption(
            "This view tests whether the model signal stays positive across different surplus-gap thresholds."
        )

        metric_label = st.selectbox(
            "Threshold sensitivity metric",
            [
                "Hit-rate lift",
                "Appearance-rate lift",
                "Next-surplus-gap lift",
                "Next-production-score lift",
            ],
            index=0
        )

        metric_map = {
            "Hit-rate lift": "hit_rate_lift",
            "Appearance-rate lift": "appearance_rate_lift",
            "Next-surplus-gap lift": "next_surplus_gap_lift",
            "Next-production-score lift": "next_production_score_lift",
        }

        metric_col = metric_map[metric_label]

        threshold_overall = (
            v4_threshold
            .loc[v4_threshold["position_final"] == "ALL"]
            .sort_values("threshold")
            .copy()
        )

        threshold_position = (
            v4_threshold
            .loc[v4_threshold["position_final"] != "ALL"]
            .sort_values(["threshold", "position_final"])
            .copy()
        )

        st.markdown("**Overall threshold results**")
        st.dataframe(
            threshold_overall[
                [
                    "threshold",
                    "players_model",
                    "players_baseline",
                    "hit_rate_model",
                    "hit_rate_baseline",
                    "hit_rate_lift",
                    "appearance_rate_lift",
                    "next_surplus_gap_lift",
                ]
            ],
            use_container_width=True
        )

        st.markdown(f"**{metric_label} by threshold and position**")

        threshold_chart = threshold_position.pivot(
            index="threshold",
            columns="position_final",
            values=metric_col
        )

        st.line_chart(threshold_chart)

    with tab2:
        st.subheader("Season Stability")

        st.caption(
            "This view checks whether the V4 signal is stable across candidate seasons."
        )

        season_metric_label = st.selectbox(
            "Season stability metric",
            [
                "Hit-rate lift",
                "Appearance-rate lift",
                "Next-surplus-gap lift",
                "Next-production-score lift",
            ],
            index=0
        )

        season_metric_col = metric_map[season_metric_label]

        season_results = v4_season.sort_values("season").copy()

        st.dataframe(
            season_results[
                [
                    "season",
                    "players_model",
                    "players_baseline",
                    "hit_rate_model",
                    "hit_rate_baseline",
                    "hit_rate_lift",
                    "appearance_rate_lift",
                    "next_surplus_gap_lift",
                ]
            ],
            use_container_width=True
        )

        season_chart = season_results.set_index("season")[[season_metric_col]]

        st.line_chart(season_chart)

    with tab3:
        st.subheader("2025 Latest-Season Watchlist")

        st.caption(
            "The 2025 watchlist identifies players who match the historically tested surplus profile. These are not backtested hits yet because 2026 outcomes are not available."
        )

        watchlist = v4_watchlist.copy()

        watchlist_position_options = ["All"] + sorted(
            watchlist["position_final"].dropna().unique().tolist()
        )

        watchlist_position = st.selectbox(
            "Watchlist position",
            watchlist_position_options,
            index=0
        )

        if watchlist_position != "All":
            watchlist = watchlist[
                watchlist["position_final"] == watchlist_position
            ]

        min_surplus_gap = st.slider(
            "Minimum player surplus gap",
            min_value=0,
            max_value=int(max(0, watchlist["player_surplus_gap"].max())),
            value=5,
            step=1
        )

        watchlist = watchlist[
            watchlist["player_surplus_gap"] >= min_surplus_gap
        ]

        watchlist = watchlist.sort_values(
            ["player_surplus_gap", "production_score"],
            ascending=[False, False]
        )

        display_columns = [
            "player_name",
            "team",
            "position_final",
            "production_score",
            "player_surplus_gap",
            "cap_number",
            "draft_year",
            "draft_round",
            "draft_pick",
            "draft_capital_bucket",
            "years_since_drafted",
            "estimated_contract_stage",
            "overall_confidence",
        ]

        display_columns = [
            col for col in display_columns if col in watchlist.columns
        ]

        st.dataframe(
            watchlist[display_columns],
            use_container_width=True
        )


## MONEYBALL INSIGHT ##
st.header("Moneyball Insight")

st.markdown(
    """
    The Billy Beane-style insight is not **avoid expensive players**.

    It is:

    > **Find production before the market prices it as proven production.**

    In this model, low-cost offensive skill players tend to generate positive surplus value, while mid/high/premium-cost players face a much steeper value hurdle.
    """
)