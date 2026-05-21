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


## LOAD DATA ##
team_surplus = pd.read_csv("outputs/team_surplus_2021_2025.csv")
focus_team_surplus = pd.read_csv("outputs/focus_team_surplus_2021_2025.csv")

# Use v3 player outputs so the dashboard includes confidence,
# draft-capital, and contract-cycle context.
player_value = pd.read_csv("outputs_v3/player_value_2021_2025_v3_contract_context.csv")
focus_player_value = pd.read_csv("outputs_v3/focus_player_value_2021_2025_v3_contract_context.csv")


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
    "Player rankings use v2 confidence outputs. Low-sample players are excluded from the final ranked table, while missing public contract matches are flagged for interpretation."
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
    "League-wide bargains are shown from the v2 ranked player table. Confidence fields help distinguish stronger signals from results affected by missing contract data."
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