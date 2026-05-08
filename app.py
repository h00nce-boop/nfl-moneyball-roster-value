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
player_value = pd.read_csv("outputs/player_value_skill_2021_2025.csv")
focus_player_value = pd.read_csv("outputs/focus_player_value_skill_2021_2025.csv")


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

team_players = (
    focus_player_value
    .query("season == @season and team == @team")
    .sort_values("player_surplus_gap", ascending=False)
)

st.subheader(f"{team} Skill Player Value, {season}")

st.dataframe(
    team_players[[
        "player_name",
        "position_final",
        "production_score",
        "total_epa",
        "cap_number",
        "production_rank_position",
        "cost_rank_position",
        "player_surplus_gap",
        "player_value_tier"
    ]],
    use_container_width=True
)


## LEAGUE-WIDE PLAYER BARGAINS ##
st.header("League-Wide Skill Player Bargains")

top_players = (
    player_value
    .query("season == @season")
    .sort_values("player_surplus_gap", ascending=False)
    .head(25)
)

st.dataframe(
    top_players[[
        "player_name",
        "team",
        "position_final",
        "production_score",
        "total_epa",
        "cap_number",
        "production_rank_position",
        "cost_rank_position",
        "player_surplus_gap",
        "player_value_tier"
    ]],
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