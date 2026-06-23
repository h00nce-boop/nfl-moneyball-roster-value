# -*- coding: utf-8 -*-
"""
NFL Moneyball decision-support dashboard.

This version is intentionally stripped back for a first-time football-ops or
analytics reader. It keeps the app organized around four practical questions:

1. What is the signal?
2. Which players should I review?
3. What does the team context look like?
4. How did the signal validate historically?

Run with:
streamlit run app.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd
import streamlit as st


# -----------------------------------------------------------------------------
# Page setup
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="NFL Moneyball Decision Support",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 3rem;
            max-width: 1320px;
        }
        h1, h2, h3 {
            letter-spacing: -0.02em;
        }
        div[data-testid="stMetric"] {
            border: 1px solid rgba(49, 51, 63, 0.13);
            border-radius: 0.8rem;
            padding: 0.85rem 1rem;
            background: rgba(250, 250, 250, 0.68);
        }
        .moneyball-kicker {
            color: #0d4f3c;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.11em;
            text-transform: uppercase;
            margin-top: 0.1rem;
            margin-bottom: 0.2rem;
        }
        .plain-card {
            border: 1px solid rgba(49, 51, 63, 0.12);
            border-radius: 0.9rem;
            padding: 0.9rem 1rem;
            background: rgba(250, 250, 250, 0.62);
            margin-bottom: 0.8rem;
        }
        .small-note {
            color: rgba(49, 51, 63, 0.72);
            font-size: 0.93rem;
            line-height: 1.35rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


APP_ROOT = Path(__file__).resolve().parent
SEARCH_ROOTS = []
for root in [Path.cwd(), APP_ROOT]:
    if root not in SEARCH_ROOTS:
        SEARCH_ROOTS.append(root)


# -----------------------------------------------------------------------------
# Data loading helpers
# -----------------------------------------------------------------------------

def candidate_paths(relative_paths: Iterable[str | Path]) -> list[Path]:
    paths: list[Path] = []
    for root in SEARCH_ROOTS:
        for relative_path in relative_paths:
            candidate = root / Path(relative_path)
            if candidate not in paths:
                paths.append(candidate)
    return paths


@st.cache_data(show_spinner=False)
def read_csv_cached(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def read_site_data_players(path: str) -> pd.DataFrame:
    """Read site-data.js as a fallback player table."""
    text = Path(path).read_text(encoding="utf-8")
    match = re.search(r"window\.NFL_MONEYBALL_DATA\s*=\s*(\{.*\})\s*;?\s*$", text, re.S)
    if match is None:
        return pd.DataFrame()

    payload = json.loads(match.group(1))
    players = pd.DataFrame(payload.get("players", []))
    if players.empty:
        return players

    if "position" in players.columns and "position_final" not in players.columns:
        players = players.rename(columns={"position": "position_final"})
    return players


def load_first_csv(label: str, relative_paths: Iterable[str | Path]) -> tuple[pd.DataFrame, Optional[Path]]:
    for path in candidate_paths(relative_paths):
        if path.exists():
            try:
                return read_csv_cached(str(path)), path
            except Exception as exc:
                st.warning(f"Could not read {label} at `{path}`: {exc}")
    return pd.DataFrame(), None


def normalize_boolish(series: pd.Series) -> pd.Series:
    return series.astype("string").str.lower().str.strip().isin(["true", "1", "yes", "y"])


def normalize_player_table(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    if "position" in out.columns and "position_final" not in out.columns:
        out = out.rename(columns={"position": "position_final"})

    numeric_cols = [
        "season",
        "production_score",
        "total_epa",
        "cap_number",
        "cash_paid",
        "production_rank_position",
        "cost_rank_position",
        "player_surplus_gap",
        "player_surplus_rank",
        "draft_year",
        "draft_round",
        "draft_pick",
        "years_since_drafted",
        "reg_snap_games",
        "reg_offense_snaps",
        "reg_avg_offense_snap_pct",
        "surplus_percentile_position",
    ]
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    if "season" in out.columns:
        out = out.dropna(subset=["season"]).copy()
        out["season"] = out["season"].astype(int)

    string_cols = [
        "player_id",
        "player_name",
        "team",
        "position_final",
        "player_value_tier",
        "draft_capital_bucket",
        "estimated_contract_stage",
        "surplus_context",
        "overall_confidence",
        "is_likely_rookie_contract",
    ]
    for col in string_cols:
        if col in out.columns:
            out[col] = out[col].astype("string").fillna("Unknown").replace({"": "Unknown"})

    if "is_likely_rookie_contract_bool" not in out.columns and "is_likely_rookie_contract" in out.columns:
        out["is_likely_rookie_contract_bool"] = normalize_boolish(out["is_likely_rookie_contract"])
    elif "is_likely_rookie_contract_bool" in out.columns:
        out["is_likely_rookie_contract_bool"] = normalize_boolish(out["is_likely_rookie_contract_bool"])

    if "is_v5_default_candidate" not in out.columns:
        if {"is_likely_rookie_contract_bool", "player_surplus_gap"}.issubset(out.columns):
            out["is_v5_default_candidate"] = (
                out["is_likely_rookie_contract_bool"].eq(True)
                & out["player_surplus_gap"].fillna(-999).ge(5)
            ).astype(int)

    return out


def load_player_table() -> tuple[pd.DataFrame, Optional[Path], str]:
    player_paths = [
        "outputs_v3/player_value_2021_2025_v3_contract_context.csv",
        "outputs_v4/player_value_2021_2025_player_season_clean.csv",
        "outputs_v5/outcomes/player_season_outcomes_v5.csv",
        "outputs_v5/outcomes/historical_validation_rows_v5.csv",
    ]
    df, path = load_first_csv("player table", player_paths)
    if not df.empty:
        return normalize_player_table(df), path, "csv"

    for path in candidate_paths(["site-data.js"]):
        if path.exists():
            try:
                fallback = read_site_data_players(str(path))
                if not fallback.empty:
                    return normalize_player_table(fallback), path, "site-data.js fallback"
            except Exception as exc:
                st.warning(f"Could not read player fallback from `{path}`: {exc}")

    return pd.DataFrame(), None, "missing"

def format_team(value) -> str:
    if value == "All":
        return "All"
    return str(value).upper()


def format_position(value) -> str:
    if value == "All":
        return "All"
    return str(value).upper()


def team_options_for(df: pd.DataFrame) -> list[str]:
    if "team" not in df.columns or df.empty:
        return ["All"]

    teams = (
        df["team"]
        .dropna()
        .astype(str)
        .str.upper()
        .sort_values()
        .unique()
        .tolist()
    )

    return ["All"] + teams


def position_options_for(df: pd.DataFrame) -> list[str]:
    if "position_final" not in df.columns or df.empty:
        return ["All"]

    positions = (
        df["position_final"]
        .dropna()
        .astype(str)
        .str.upper()
        .sort_values()
        .unique()
        .tolist()
    )

    return ["All"] + positions


def confidence_options_for(df: pd.DataFrame) -> list[str]:
    if "overall_confidence" not in df.columns or df.empty:
        return ["All"]

    has_high = df["overall_confidence"].astype(str).str.lower().eq("high").any()
    return ["All", "High"] if has_high else ["All"]


def apply_team_filter(df: pd.DataFrame, selected_team: str) -> pd.DataFrame:
    if selected_team == "All" or "team" not in df.columns:
        return df

    return df[df["team"].astype(str).str.upper().eq(selected_team)].copy()


def apply_position_filter(df: pd.DataFrame, selected_position: str) -> pd.DataFrame:
    if selected_position == "All" or "position_final" not in df.columns:
        return df

    return df[df["position_final"].astype(str).str.upper().eq(selected_position)].copy()


def apply_confidence_filter(df: pd.DataFrame, selected_confidence: str) -> pd.DataFrame:
    if selected_confidence == "All" or "overall_confidence" not in df.columns:
        return df

    # Since the public-facing options are only All and High, this means "High only."
    return df[df["overall_confidence"].astype(str).str.lower().eq("high")].copy()


def make_download_df(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    download_df = clean_display_df(df, columns)

    if "Team" in download_df.columns:
        download_df["Team"] = download_df["Team"].astype(str).str.upper()

    if "Position" in download_df.columns:
        download_df["Position"] = download_df["Position"].astype(str).str.upper()

    return download_df


def download_filtered_csv(
    df: pd.DataFrame,
    columns: Iterable[str],
    *,
    file_name: str,
    button_label: str,
) -> None:
    if df.empty:
        return

    download_df = make_download_df(df, columns)
    csv = download_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label=button_label,
        data=csv,
        file_name=file_name,
        mime="text/csv",
        use_container_width=True,
    )


TEAM_SURPLUS, TEAM_SURPLUS_PATH = load_first_csv(
    "team surplus",
    ["outputs/team_surplus_2021_2025.csv"],
)
FOCUS_TEAM_SURPLUS, FOCUS_TEAM_SURPLUS_PATH = load_first_csv(
    "focus team surplus",
    ["outputs/focus_team_surplus_2021_2025.csv", "outputs/team_surplus_2021_2025.csv"],
)
PLAYER_VALUE, PLAYER_VALUE_PATH, PLAYER_VALUE_SOURCE = load_player_table()
WATCHLIST, WATCHLIST_PATH = load_first_csv(
    "latest V5 watchlist",
    [
        "outputs_v5/watchlists/2026_candidate_pool_v5.csv",
        "2026_candidate_pool_v5.csv",
        "outputs_v4/backtests/candidate_review_2025_watchlist.csv",
    ],
)
if not WATCHLIST.empty:
    WATCHLIST = normalize_player_table(WATCHLIST)

K3_LIFT, K3_LIFT_PATH = load_first_csv(
    "K=3 matched validation summary",
    [
        "outputs_v5/backtests/k3/k3_matched_lift_summary_v5.csv",
        "outputs_v5/backtests/k3/matched_lift_summary_v5.csv",
        "k3_matched_lift_summary_v5.csv",
    ],
)
SENSITIVITY, SENSITIVITY_PATH = load_first_csv(
    "K sensitivity summary",
    [
        "outputs_v5/backtests/sensitivity_k_summary_main_outcomes_v5.csv",
        "outputs_v5/backtests/sensitivity_k_summary_v5.csv",
        "sensitivity_k_summary_main_outcomes_v5.csv",
        "sensitivity_k_summary_v5.csv",
    ],
)
BY_POSITION, BY_POSITION_PATH = load_first_csv(
    "K=3 matched lift by position",
    [
        "outputs_v5/backtests/k3/k3_matched_lift_by_position_v5.csv",
        "k3_matched_lift_by_position_v5.csv",
    ],
)
BY_SEASON, BY_SEASON_PATH = load_first_csv(
    "K=3 matched lift by season",
    [
        "outputs_v5/backtests/k3/k3_matched_lift_by_season_v5.csv",
        "k3_matched_lift_by_season_v5.csv",
    ],
)


# -----------------------------------------------------------------------------
# Human-readable labels
# -----------------------------------------------------------------------------
COLUMN_LABELS = {
    "season": "Season",
    "team": "Team",
    "player_name": "Player",
    "position_final": "Position",
    "production_score": "Production Score",
    "total_epa": "Total EPA",
    "cap_number": "Public Cap Cost ($M)",
    "cash_paid": "Cash Paid ($M)",
    "production_rank_position": "Production Rank Within Position",
    "cost_rank_position": "Cost Rank Within Position",
    "player_surplus_gap": "Value Gap",
    "player_surplus_rank": "Value Rank",
    "player_value_tier": "Value Tier",
    "draft_year": "Draft Year",
    "draft_round": "Draft Round",
    "draft_pick": "Draft Pick",
    "draft_capital_bucket": "Draft Capital",
    "years_since_drafted": "Years Since Drafted",
    "estimated_contract_stage": "Contract Stage",
    "surplus_context": "Surplus Context",
    "overall_confidence": "Confidence",
    "is_likely_rookie_contract": "Likely Rookie Contract",
    "overall_rank": "Performance Rank",
    "cap_cost_rank": "Cost Rank",
    "surplus_rank_gap": "Team Value Gap",
    "surplus_value_rank": "Team Value Rank",
    "surplus_tier": "Team Value Tier",
    "offensive_epa_per_play": "Offensive EPA / Play",
    "defensive_epa_allowed_per_play": "Defensive EPA Allowed / Play",
    "total_cap_number": "Public Cap Cost Proxy",
    "reg_snap_games": "Regular-Season Snap Games",
    "reg_offense_snaps": "Regular-Season Offensive Snaps",
    "reg_avg_offense_snap_pct": "Average Offensive Snap Share",
    "candidate_position_final": "Position",
    "candidate_season": "Candidate Season",
    "matched_candidates": "Matched Candidates",
    "candidate_rate": "Candidate Rate",
    "matched_control_rate": "Matched-Control Rate",
    "lift_pp": "Lift (Percentage Points)",
    "lift_ci_low_pp": "95% CI Low",
    "lift_ci_high_pp": "95% CI High",
}

VALUE_LABELS = {
    "All": "All",
    "Unknown": "Unknown",
    "unknown": "Unknown",
    "round_1": "Round 1",
    "round_2": "Round 2",
    "round_3": "Round 3",
    "rounds_4_5": "Rounds 4-5",
    "rounds_6_7": "Rounds 6-7",
    "undrafted_or_unmatched": "Undrafted / Unmatched",
    "rookie_contract": "Rookie Contract",
    "possible_fifth_year_option": "Possible Fifth-Year Option",
    "second_contract_or_later": "Second Contract or Later",
    "pre_extension_breakout": "Pre-Extension Breakout",
    "rookie_contract_surplus": "Rookie-Contract Surplus",
    "expensive_star": "Expensive Star",
    "negative_surplus": "Negative Surplus",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
    "elite_surplus": "Elite Surplus",
    "positive_surplus": "Positive Surplus",
    "neutral": "Neutral",
    "overpriced": "Overpriced",
}

HUMANIZE_COLUMNS = {
    "draft_capital_bucket",
    "estimated_contract_stage",
    "surplus_context",
    "overall_confidence",
    "player_value_tier",
    "surplus_tier",
    "is_likely_rookie_contract",
}

OUTCOME_LABELS = {
    "primary_v5_hit": "Top-half next-season production",
    "secondary_v5_hit": "Retained positive surplus",
    "retained_positive_surplus": "Retained positive surplus",
    "next_year_meaningful_regular_role": "Meaningful role next season",
    "appeared_next_year": "Appeared next season",
    "next_year_top_half_position": "Top-half next-season production",
    "improved_production_score": "Improved production score",
    "improved_production_percentile": "Improved production percentile",
}

OUTCOME_EXPLANATIONS = {
    "primary_v5_hit": "The player ranked in the top half of his position by next-season production.",
    "secondary_v5_hit": "The player still had positive value gap the following season.",
    "next_year_meaningful_regular_role": "The player had at least 8 regular-season snap games and at least 25% average offensive snap share.",
    "appeared_next_year": "The player appeared in the following-season dataset.",
}

MAIN_OUTCOMES = [
    "primary_v5_hit",
    "secondary_v5_hit",
    "next_year_meaningful_regular_role",
    "appeared_next_year",
]


def humanize_value(value) -> str:
    if pd.isna(value):
        return "Unknown"
    text = str(value).strip()
    if text in VALUE_LABELS:
        return VALUE_LABELS[text]
    lower = text.lower()
    if lower in VALUE_LABELS:
        return VALUE_LABELS[lower]
    return text.replace("_", " ").replace("/", " / ").title()


def format_boolish(value) -> str:
    text = str(value).lower().strip()
    if text in {"true", "1", "yes", "y"}:
        return "Yes"
    if text in {"false", "0", "no", "n"}:
        return "No"
    return humanize_value(value)

def clean_display_df(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    shown_cols = [col for col in columns if col in df.columns]
    display_df = df[shown_cols].copy()

    for col in shown_cols:
        if col in HUMANIZE_COLUMNS:
            if col == "is_likely_rookie_contract":
                display_df[col] = display_df[col].map(format_boolish)
            else:
                display_df[col] = display_df[col].map(humanize_value)

    rename_map = {col: COLUMN_LABELS.get(col, humanize_value(col)) for col in shown_cols}
    display_df = display_df.rename(columns=rename_map)
    return display_df


def display_table(df: pd.DataFrame, columns: Iterable[str], *, height: int = 420) -> None:
    st.dataframe(clean_display_df(df, columns), use_container_width=True, hide_index=True, height=height)


def option_values(df: pd.DataFrame, column: str, include_all: bool = True) -> list:
    if column not in df.columns or df.empty:
        return ["All"] if include_all else []

    values = df[column].dropna().tolist()

    if "season" in column.lower() or "year" in column.lower():
        values = pd.to_numeric(pd.Series(values), errors="coerce").dropna().astype(int).unique().tolist()
        values = sorted(values)
    else:
        values = sorted(
            pd.Series(values).astype(str).dropna().unique().tolist(),
            key=lambda x: humanize_value(x),
        )
    return (["All"] if include_all else []) + values

def season_options_for(df: pd.DataFrame, column: str = "season", include_all: bool = True) -> list:
    if column not in df.columns or df.empty:
        return ["All"] if include_all else []

    seasons = (
        pd.to_numeric(df[column], errors="coerce")
        .dropna()
        .astype(int)
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    return (["All"] if include_all else []) + seasons

def pct(value) -> str:
    number = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(number):
        return "n/a"
    return f"{number:.1%}"


def pp(value) -> str:
    number = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(number):
        return "n/a"
    return f"{number:+.1f} pp"


def fmt_number(value, decimals: int = 1, prefix: str = "", suffix: str = "") -> str:
    number = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(number):
        return "n/a"
    return f"{prefix}{number:.{decimals}f}{suffix}"


def fmt_gap(value) -> str:
    return fmt_number(value, decimals=1, prefix="") if pd.isna(pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]) else f"{pd.to_numeric(pd.Series([value]), errors='coerce').iloc[0]:+.1f}"


def format_rank(value) -> str:
    number = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(number):
        return "n/a"
    return str(int(round(float(number))))


def normalize_for_search(value) -> str:
    if pd.isna(value):
        return ""
    text = str(value).lower()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def filter_name_tokens(df: pd.DataFrame, query: str) -> pd.DataFrame:
    query_norm = normalize_for_search(query)
    if not query_norm or "player_name" not in df.columns:
        return df.iloc[0:0].copy()

    name_series = df["player_name"].map(normalize_for_search)
    token_mask = pd.Series(True, index=df.index)
    for token in query_norm.split():
        token_mask = token_mask & name_series.str.contains(token, regex=False, na=False)

    compact_query = query_norm.replace(" ", "")
    compact_names = name_series.str.replace(" ", "", regex=False)
    compact_mask = compact_names.str.contains(compact_query, regex=False, na=False)
    return df.loc[token_mask | compact_mask].copy()


def apply_optional_filter(df: pd.DataFrame, column: str, selected_value) -> pd.DataFrame:
    if selected_value == "All" or column not in df.columns:
        return df
    return df[df[column].eq(selected_value)].copy()


def get_v5_outcome(v5_lift: pd.DataFrame, outcome: str) -> Optional[pd.Series]:
    if v5_lift.empty or "outcome" not in v5_lift.columns:
        return None
    match = v5_lift[v5_lift["outcome"].eq(outcome)]
    if match.empty:
        return None
    return match.iloc[0]


def player_history_for(row: pd.Series, source_df: pd.DataFrame) -> pd.DataFrame:
    if source_df.empty:
        return source_df
    if "player_id" in source_df.columns and pd.notna(row.get("player_id")):
        player_id = str(row.get("player_id"))
        id_mask = source_df["player_id"].astype(str).eq(player_id)
        if id_mask.any():
            return source_df.loc[id_mask].copy()
    if "player_name" in source_df.columns and pd.notna(row.get("player_name")):
        return source_df[source_df["player_name"].astype(str).eq(str(row.get("player_name")))].copy()
    return source_df.iloc[0:0].copy()


def render_player_read(row: pd.Series, source_df: pd.DataFrame, *, context: str) -> None:
    player = row.get("player_name", "Selected player")
    season_value = row.get("season", "")
    team_value = row.get("team", "")
    pos = row.get("position_final", "")
    value_gap = row.get("player_surplus_gap")
    prod_rank = row.get("production_rank_position")
    cost_rank = row.get("cost_rank_position")
    cap_number = row.get("cap_number")
    production_score = row.get("production_score")
    contract_stage = humanize_value(row.get("estimated_contract_stage", "Unknown"))
    draft_bucket = humanize_value(row.get("draft_capital_bucket", "Unknown"))
    is_rookie = bool(row.get("is_likely_rookie_contract_bool", False))

    st.subheader(f"{player} | {season_value} {team_value} {pos}")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Value Gap", fmt_gap(value_gap), help="Cost rank within position minus production rank within position.")
    with col2:
        st.metric("Production Rank", format_rank(prod_rank), help="Lower rank is better within the position.")
    with col3:
        st.metric("Cost Rank", format_rank(cost_rank), help="Lower rank means more expensive within the position.")
    with col4:
        st.metric("Public Cap Cost", fmt_number(cap_number, decimals=2, prefix="$", suffix="M"))

    st.write(
        f"Model read: {player} ranked {format_rank(prod_rank)} in production within {pos} and "
        f"{format_rank(cost_rank)} in public cost within {pos}, producing a value gap of {fmt_gap(value_gap)}."
    )

    if context == "candidate":
        st.info(
            "This is a review queue row, not a signing recommendation. A team would still check film, "
            "medical history, scheme fit, depth-chart path, age curve, and internal cap accounting."
        )
    elif is_rookie and pd.to_numeric(pd.Series([value_gap]), errors="coerce").iloc[0] >= 5:
        st.success(
            "This row fits the default V5 candidate shape: likely rookie-contract timeline and value gap of at least +5."
        )
    else:
        st.info(
            "This row is still useful descriptively, but it is not necessarily part of the default V5 matched-validation candidate pool."
        )

    st.caption(
        f"Contract stage: {contract_stage}. Draft capital: {draft_bucket}. "
        f"Production score: {fmt_number(production_score, decimals=1)}."
    )

    history = player_history_for(row, source_df)
    if not history.empty and "season" in history.columns:
        history = history.sort_values("season")
        st.markdown("**Player history in this model**")
        display_table(
            history,
            [
                "season",
                "team",
                "position_final",
                "player_surplus_gap",
                "production_rank_position",
                "cost_rank_position",
                "production_score",
                "total_epa",
                "cap_number",
                "draft_capital_bucket",
                "estimated_contract_stage",
                "overall_confidence",
            ],
            height=250,
        )

        if {"season", "player_surplus_gap"}.issubset(history.columns):
            trend = history[["season", "player_surplus_gap"]].copy()
            trend["player_surplus_gap"] = pd.to_numeric(trend["player_surplus_gap"], errors="coerce")
            trend = trend.dropna(subset=["season", "player_surplus_gap"])
            if len(trend) > 1:
                chart_df = trend.rename(columns={"player_surplus_gap": "Value Gap"}).set_index("season")[["Value Gap"]]
                st.line_chart(chart_df)


def require_data() -> None:
    if PLAYER_VALUE.empty:
        st.error(
            "No player-value table was found. Expected `outputs_v3/player_value_2021_2025_v3_contract_context.csv` "
            "or another supported player output."
        )
        st.stop()


# -----------------------------------------------------------------------------
# Sidebar navigation
# -----------------------------------------------------------------------------
st.sidebar.title("Workflow")
page = st.sidebar.radio(
    "Choose what you want to do",
    [
        "Start Here",
        "Find Players",
        "Check Team Context",
        "Validate the Signal",
        "Methodology and Limits",
    ],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Value Gap = cost rank within position minus production rank within position. Positive values mean production outpaced the public cost proxy."
)
st.sidebar.caption(
    "The app is designed as a screening tool. It should point to players worth review, not replace scouting or internal cap data."
)


# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------
st.markdown('<div class="moneyball-kicker">Public Data Decision Support</div>', unsafe_allow_html=True)
st.title("NFL Moneyball: Roster Value Decision Tool")
st.markdown(
    "A public-data screen for finding offensive skill players who produced more than their public contract-cost profile suggested."
)

if not PLAYER_VALUE.empty:
    latest_season = int(pd.to_numeric(PLAYER_VALUE["season"], errors="coerce").dropna().max()) if "season" in PLAYER_VALUE.columns else None
else:
    latest_season = None


# -----------------------------------------------------------------------------
# Page: Start Here
# -----------------------------------------------------------------------------
if page == "Start Here":
    st.header("What this app is for")
    st.markdown(
        """
        This is a **decision-support screen**. The practical question is not simply who is good.
        The practical question is: **who produced more than his public cost rank would imply, and did that profile persist historically?**
        """
    )

    if not K3_LIFT.empty:
        primary = get_v5_outcome(K3_LIFT, "primary_v5_hit")
        secondary = get_v5_outcome(K3_LIFT, "secondary_v5_hit")
        role = get_v5_outcome(K3_LIFT, "next_year_meaningful_regular_role")
        appeared = get_v5_outcome(K3_LIFT, "appeared_next_year")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Top-half production lift", pp(primary["lift_pp"]) if primary is not None else "n/a")
        with col2:
            st.metric("Positive-surplus lift", pp(secondary["lift_pp"]) if secondary is not None else "n/a")
        with col3:
            st.metric("Meaningful-role lift", pp(role["lift_pp"]) if role is not None else "n/a")
        with col4:
            st.metric("Appearance lift", pp(appeared["lift_pp"]) if appeared is not None else "n/a")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown(
            """
            <div class="plain-card">
            <b>1. Find Players</b><br>
            Filter by season, team, position, contract stage, draft capital, and value gap. Leave Player as "All" to build a board.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            """
            <div class="plain-card">
            <b>2. Validate the Signal</b><br>
            Read the bars as percentage-point lift versus matched rookie-contract controls, not as raw hit rates.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_c:
        st.markdown(
            """
            <div class="plain-card">
            <b>3. Check Team Context</b><br>
            Use the team page for roster-efficiency context, not as the primary player-discovery workflow.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.subheader("Safe interpretation")
    st.write(
        "The strongest V5 claim is persistence: flagged rookie-contract surplus players were more likely than matched peers "
        "to stay relevant, retain positive surplus, and produce in the top half of their position the following season. "
        "This is not causal proof and not a guaranteed breakout model."
    )


# -----------------------------------------------------------------------------
# Page: Find Players
# -----------------------------------------------------------------------------
elif page == "Find Players":
    require_data()

    st.header("Find players")
    st.markdown(
        "Use this page two ways: leave **Player** as `All matching players` to build a board, "
        "or choose a specific player from the searchable dropdown for an exact lookup."
    )

    source_tab, shortlist_tab = st.tabs(["All model players", "V5 surplus shortlist"])

    with source_tab:
        st.subheader("All model players")
        st.caption("Every filter is optional. The table updates as you narrow the board.")

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            season_options = season_options_for(PLAYER_VALUE)
            selected_season = st.selectbox(
                "Season",
                season_options,
                index=0,
                key="finder_season",
                format_func=humanize_value,
            )

        with c2:
            selected_team = st.selectbox(
                "Team",
                team_options_for(PLAYER_VALUE),
                index=0,
                key="finder_team",
                format_func=format_team,
            )

        with c3:
            selected_position = st.selectbox(
                "Position",
                position_options_for(PLAYER_VALUE),
                index=0,
                key="finder_position",
                format_func=format_position,
            )

        with c4:
            selected_confidence = st.selectbox(
                "Confidence",
                confidence_options_for(PLAYER_VALUE),
                index=0,
                key="finder_conf",
                help="Use High for the cleanest public-cost and sample-size interpretation.",
            )

        c5, c6, c7 = st.columns([1.2, 1.2, 1])

        with c5:
            contract_options = option_values(PLAYER_VALUE, "estimated_contract_stage")
            selected_contract = st.selectbox(
                "Contract Stage",
                contract_options,
                index=0,
                key="finder_contract",
                format_func=humanize_value,
            )

        with c6:
            draft_options = option_values(PLAYER_VALUE, "draft_capital_bucket")
            selected_draft = st.selectbox(
                "Draft Capital",
                draft_options,
                index=0,
                key="finder_draft",
                format_func=humanize_value,
            )

        with c7:
            min_gap = st.slider(
                "Minimum Value Gap",
                min_value=-80,
                max_value=80,
                value=-80,
                step=1,
                key="finder_gap",
            )

        filtered = PLAYER_VALUE.copy()

        filtered = apply_optional_filter(filtered, "season", selected_season)
        filtered = apply_team_filter(filtered, selected_team)
        filtered = apply_position_filter(filtered, selected_position)
        filtered = apply_confidence_filter(filtered, selected_confidence)
        filtered = apply_optional_filter(filtered, "estimated_contract_stage", selected_contract)
        filtered = apply_optional_filter(filtered, "draft_capital_bucket", selected_draft)

        if "player_surplus_gap" in filtered.columns:
            filtered = filtered[
                pd.to_numeric(filtered["player_surplus_gap"], errors="coerce")
                .fillna(-999)
                .ge(min_gap)
            ]

        player_options = ["All matching players"]

        if "player_name" in filtered.columns and not filtered.empty:
            player_options += sorted(
                filtered["player_name"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

        selected_player = st.selectbox(
            "Player search",
            player_options,
            index=0,
            key="finder_player",
            help=(
                "This is a searchable dropdown. Click into it and type any part of a player name. "
                "The options shown here already respect the filters above. Leave it on All matching players "
                "to show everyone who matches the filters."
            ),
        )

        if selected_player != "All matching players":
            filtered = filtered[
                filtered["player_name"].astype(str).eq(selected_player)
            ].copy()

        sort_cols = [
            col for col in ["player_surplus_gap", "production_score"]
            if col in filtered.columns
        ]

        if sort_cols:
            filtered = filtered.sort_values(
                sort_cols,
                ascending=[False] * len(sort_cols),
            )

        finder_display_cols = [
            "player_name",
            "season",
            "team",
            "position_final",
            "player_surplus_gap",
            "production_rank_position",
            "cost_rank_position",
            "production_score",
            "total_epa",
            "cap_number",
            "draft_year",
            "draft_round",
            "draft_pick",
            "draft_capital_bucket",
            "estimated_contract_stage",
            "is_likely_rookie_contract",
            "overall_confidence",
        ]

        st.write(f"Showing {len(filtered):,} matching player-season row(s).")

        display_table(
            filtered.head(150),
            finder_display_cols,
            height=390,
        )

        download_filtered_csv(
            filtered,
            finder_display_cols,
            file_name="nfl_moneyball_filtered_players.csv",
            button_label="Download filtered player data",
        )

        if not filtered.empty:
            explain_df = filtered.reset_index(drop=True).head(150)

            selected_idx = st.selectbox(
                "Explain one row",
                explain_df.index.tolist(),
                format_func=lambda i: (
                    f"{explain_df.loc[i, 'player_name']} | "
                    f"{explain_df.loc[i, 'season']} | "
                    f"{str(explain_df.loc[i].get('team', '')).upper()} | "
                    f"{str(explain_df.loc[i].get('position_final', '')).upper()} | "
                    f"gap {fmt_gap(explain_df.loc[i].get('player_surplus_gap'))}"
                ),
                key="finder_explain_row",
            )

            render_player_read(
                explain_df.loc[selected_idx],
                PLAYER_VALUE,
                context="all",
            )

    with shortlist_tab:
        st.subheader("V5 surplus shortlist")
        st.caption(
            "This is the narrower decision-support board: it defaults to rookie-contract players "
            "with a positive value gap."
        )

        if not WATCHLIST.empty:
            base_board = WATCHLIST.copy()
            st.caption("Using the latest V5 watchlist file when available.")
        else:
            base_board = PLAYER_VALUE.copy()
            st.caption(
                "No separate V5 watchlist file was found, so this board is built from the player-value table."
            )

        s1, s2, s3, s4 = st.columns(4)

        with s1:
            shortlist_season_options = season_options_for(base_board)
            default_latest_index = 0

            if latest_season in shortlist_season_options:
                default_latest_index = shortlist_season_options.index(latest_season)

            shortlist_season = st.selectbox(
                "Season",
                shortlist_season_options,
                index=default_latest_index,
                key="short_season",
                format_func=humanize_value,
            )

        with s2:
            shortlist_team = st.selectbox(
                "Team",
                team_options_for(base_board),
                index=0,
                key="short_team",
                format_func=format_team,
            )

        with s3:
            shortlist_position = st.selectbox(
                "Position",
                position_options_for(base_board),
                index=0,
                key="short_pos",
                format_func=format_position,
            )

        with s4:
            shortlist_confidence = st.selectbox(
                "Confidence",
                confidence_options_for(base_board),
                index=0,
                key="short_conf",
                help="Use High for the cleanest public-cost and sample-size interpretation.",
            )

        s5, s6, s7 = st.columns([1.2, 1.2, 1])

        with s5:
            shortlist_contract = st.selectbox(
                "Contract Stage",
                option_values(base_board, "estimated_contract_stage"),
                index=0,
                key="short_contract",
                format_func=humanize_value,
            )

        with s6:
            shortlist_draft = st.selectbox(
                "Draft Capital",
                option_values(base_board, "draft_capital_bucket"),
                index=0,
                key="short_draft",
                format_func=humanize_value,
            )

        with s7:
            shortlist_min_gap = st.slider(
                "Minimum Value Gap",
                min_value=-20,
                max_value=80,
                value=5,
                step=1,
                key="short_gap",
            )

        rookie_only = st.checkbox(
            "Rookie-contract only",
            value=True,
            key="short_rookie",
        )

        board = base_board.copy()

        board = apply_optional_filter(board, "season", shortlist_season)
        board = apply_team_filter(board, shortlist_team)
        board = apply_position_filter(board, shortlist_position)
        board = apply_confidence_filter(board, shortlist_confidence)
        board = apply_optional_filter(board, "estimated_contract_stage", shortlist_contract)
        board = apply_optional_filter(board, "draft_capital_bucket", shortlist_draft)

        if "player_surplus_gap" in board.columns:
            board = board[
                pd.to_numeric(board["player_surplus_gap"], errors="coerce")
                .fillna(-999)
                .ge(shortlist_min_gap)
            ]

        if rookie_only:
            if "is_likely_rookie_contract_bool" in board.columns:
                board = board[board["is_likely_rookie_contract_bool"].eq(True)]
            elif "is_likely_rookie_contract" in board.columns:
                board = board[
                    board["is_likely_rookie_contract"]
                    .astype(str)
                    .str.lower()
                    .isin(["true", "1", "yes", "y"])
                ]
            elif "estimated_contract_stage" in board.columns:
                board = board[
                    board["estimated_contract_stage"].isin(
                        ["rookie_contract", "possible_fifth_year_option"]
                    )
                ]

        shortlist_player_options = ["All matching players"]

        if "player_name" in board.columns and not board.empty:
            shortlist_player_options += sorted(
                board["player_name"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

        shortlist_player = st.selectbox(
            "Player search",
            shortlist_player_options,
            index=0,
            key="short_player",
            help=(
                "This is a searchable dropdown. Click into it and type any part of a player name. "
                "The options shown here already respect the shortlist filters above. Leave it on "
                "All matching players to show everyone who matches the filters."
            ),
        )

        if shortlist_player != "All matching players":
            board = board[
                board["player_name"].astype(str).eq(shortlist_player)
            ].copy()

        sort_cols = [
            col for col in ["player_surplus_gap", "production_score"]
            if col in board.columns
        ]

        if sort_cols:
            board = board.sort_values(
                sort_cols,
                ascending=[False] * len(sort_cols),
            )

        shortlist_display_cols = [
            "player_name",
            "season",
            "team",
            "position_final",
            "player_surplus_gap",
            "production_rank_position",
            "cost_rank_position",
            "production_score",
            "total_epa",
            "cap_number",
            "draft_year",
            "draft_round",
            "draft_pick",
            "draft_capital_bucket",
            "estimated_contract_stage",
            "reg_snap_games",
            "reg_avg_offense_snap_pct",
            "overall_confidence",
        ]

        st.write(f"Showing {len(board):,} shortlist row(s).")

        display_table(
            board.head(100),
            shortlist_display_cols,
            height=390,
        )

        download_filtered_csv(
            board,
            shortlist_display_cols,
            file_name="nfl_moneyball_v5_surplus_shortlist.csv",
            button_label="Download filtered shortlist",
        )

        if not board.empty:
            explain_board = board.reset_index(drop=True).head(100)

            board_idx = st.selectbox(
                "Explain one shortlist row",
                explain_board.index.tolist(),
                format_func=lambda i: (
                    f"{explain_board.loc[i, 'player_name']} | "
                    f"{str(explain_board.loc[i].get('team', '')).upper()} | "
                    f"{str(explain_board.loc[i].get('position_final', '')).upper()} | "
                    f"gap {fmt_gap(explain_board.loc[i].get('player_surplus_gap'))}"
                ),
                key="short_explain_row",
            )

            render_player_read(
                explain_board.loc[board_idx],
                PLAYER_VALUE,
                context="candidate",
            )

# -----------------------------------------------------------------------------
# Page: Check Team Context
# -----------------------------------------------------------------------------
elif page == "Check Team Context":
    st.header("Check team context")
    if TEAM_SURPLUS.empty:
        st.info("Team surplus files were not found in this app environment.")
    else:
        t1, t2 = st.columns(2)
        with t1:
            team_seasons = season_options_for(TEAM_SURPLUS, include_all=False)
            selected_team_season = st.selectbox(
                "Season",
                team_seasons,
                index=len(team_seasons) - 1 if team_seasons else 0,
                format_func=humanize_value,
            )
        with t2:
            team_list = option_values(TEAM_SURPLUS, "team", include_all=False)
            default_team_index = team_list.index("PHI") if "PHI" in team_list else 0
            selected_team_context = st.selectbox("Team", team_list, index=default_team_index, format_func=humanize_value)

        season_table = TEAM_SURPLUS[TEAM_SURPLUS["season"].astype(int).eq(int(selected_team_season))].copy()
        season_table = season_table.sort_values("surplus_value_rank") if "surplus_value_rank" in season_table.columns else season_table

        c1, c2 = st.columns([1.15, 1])
        with c1:
            st.subheader(f"{selected_team_season} team ranking")
            display_table(
                season_table,
                ["team", "overall_rank", "cap_cost_rank", "surplus_rank_gap", "surplus_value_rank", "surplus_tier"],
                height=500,
            )
        with c2:
            st.subheader(f"{selected_team_context} trend")
            trend = TEAM_SURPLUS[TEAM_SURPLUS["team"].eq(selected_team_context)].copy().sort_values("season")
            if not trend.empty and {"season", "surplus_rank_gap"}.issubset(trend.columns):
                chart_df = trend.rename(columns={"surplus_rank_gap": "Team Value Gap"}).set_index("season")[["Team Value Gap"]]
                st.line_chart(chart_df)
            display_table(
                trend,
                [
                    "season",
                    "overall_rank",
                    "cap_cost_rank",
                    "surplus_rank_gap",
                    "surplus_value_rank",
                    "offensive_epa_per_play",
                    "defensive_epa_allowed_per_play",
                    "total_cap_number",
                ],
                height=260,
            )


# -----------------------------------------------------------------------------
# Page: Validate the Signal
# -----------------------------------------------------------------------------
elif page == "Validate the Signal":
    st.header("Validate the signal")
    st.markdown(
        "V5 asks whether the surplus-value signal survives a fairer comparison: flagged rookie-contract players versus similar rookie-contract non-candidates."
    )

    if not K3_LIFT.empty and "outcome" in K3_LIFT.columns:
        summary = K3_LIFT[K3_LIFT["outcome"].isin(MAIN_OUTCOMES)].copy()
        summary["Outcome"] = summary["outcome"].map(OUTCOME_LABELS)
        summary["What the outcome means"] = summary["outcome"].map(OUTCOME_EXPLANATIONS)
        summary["lift_pp"] = pd.to_numeric(summary["lift_pp"], errors="coerce")

        st.subheader("What the bars represent")
        st.info(
            "Each bar is lift in percentage points: candidate rate minus matched-control rate. "
            "For example, +14.3 pp means the flagged players were 14.3 percentage points more likely than matched peers to meet that outcome."
        )

        chart_df = summary[["Outcome", "lift_pp"]].rename(columns={"lift_pp": "Lift vs matched controls (percentage points)"})
        chart_df = chart_df.set_index("Outcome")
        st.bar_chart(chart_df)
        st.caption("Bars above zero favor V5 candidates. Bars below zero favor the matched controls.")

        table = summary.copy()
        table["Candidate Rate"] = table["candidate_rate"].map(pct) if "candidate_rate" in table.columns else "n/a"
        table["Matched-Control Rate"] = table["matched_control_rate"].map(pct) if "matched_control_rate" in table.columns else "n/a"
        table["Lift"] = table["lift_pp"].map(pp)
        if {"lift_ci_low_pp", "lift_ci_high_pp"}.issubset(table.columns):
            table["Approx. 95% CI"] = table.apply(lambda row: f"{pp(row['lift_ci_low_pp'])} to {pp(row['lift_ci_high_pp'])}", axis=1)
        else:
            table["Approx. 95% CI"] = "n/a"

        st.subheader("Main V5 matched outcomes")
        st.dataframe(
            table[["Outcome", "What the outcome means", "matched_candidates", "Candidate Rate", "Matched-Control Rate", "Lift", "Approx. 95% CI"]]
            .rename(columns={"matched_candidates": "Matched Candidates"}),
            use_container_width=True,
            hide_index=True,
        )

        if not SENSITIVITY.empty and {"k_matches", "outcome", "lift_pp"}.issubset(SENSITIVITY.columns):
            st.subheader("Sensitivity to number of matched controls")
            st.caption(
                "This checks whether the primary result depends on using exactly three controls per candidate."
            )
            sensitivity_primary = SENSITIVITY[SENSITIVITY["outcome"].eq("primary_v5_hit")].copy()
            if not sensitivity_primary.empty:
                sensitivity_primary["k_matches"] = pd.to_numeric(sensitivity_primary["k_matches"], errors="coerce")
                sensitivity_primary = sensitivity_primary.sort_values("k_matches")
                sensitivity_chart = sensitivity_primary.rename(
                    columns={"k_matches": "Matched Controls", "lift_pp": "Primary Lift (pp)"}
                ).set_index("Matched Controls")[["Primary Lift (pp)"]]
                st.line_chart(sensitivity_chart)
                display_table(
                    sensitivity_primary,
                    ["k_matches", "matched_candidates", "candidate_rate", "matched_control_rate", "lift_pp", "lift_ci_low_pp", "lift_ci_high_pp"],
                    height=180,
                )

        with st.expander("Diagnostic splits by position and season"):
            if not BY_POSITION.empty and "outcome" in BY_POSITION.columns:
                st.markdown("**Primary lift by position**")
                pos = BY_POSITION[BY_POSITION["outcome"].eq("primary_v5_hit")].copy()
                display_table(
                    pos.sort_values("lift_pp", ascending=False),
                    ["candidate_position_final", "matched_candidates", "candidate_rate", "matched_control_rate", "lift_pp", "lift_ci_low_pp", "lift_ci_high_pp"],
                    height=240,
                )
            if not BY_SEASON.empty and "outcome" in BY_SEASON.columns:
                st.markdown("**Primary lift by validation season**")
                seas = BY_SEASON[BY_SEASON["outcome"].eq("primary_v5_hit")].copy()
                display_table(
                    seas.sort_values("candidate_season"),
                    ["candidate_season", "matched_candidates", "candidate_rate", "matched_control_rate", "lift_pp", "lift_ci_low_pp", "lift_ci_high_pp"],
                    height=240,
                )

        st.warning(
            "Do not overclaim this. V5 is strongest as a persistence and role-retention screen. It does not prove causality and does not guarantee breakouts."
        )
    else:
        st.info(
            "No V5 matched-validation summary file was found. Expected `outputs_v5/backtests/k3/k3_matched_lift_summary_v5.csv`."
        )


# -----------------------------------------------------------------------------
# Page: Methodology and Limits
# -----------------------------------------------------------------------------
elif page == "Methodology and Limits":
    st.header("Methodology and limits")
    st.subheader("How value is measured")
    st.markdown(
        """
        The player model ranks players within position by production and by public contract-cost proxy.

        ```text
        player_value_gap = cost_rank_within_position - production_rank_within_position
        ```

        A positive gap means the player produced better than his public cost rank. A negative gap means the player was expensive relative to his production rank.
        """
    )

    st.subheader("What V5 adds")
    st.markdown(
        """
        V5 tests whether the rookie-contract surplus profile persists historically. The default candidate definition is:

        ```text
        likely rookie contract == True
        and player value gap >= 5
        ```

        Candidates are compared with similar rookie-contract non-candidates by season, position, draft-capital bucket, contract stage, production percentile, and regular-season opportunity.
        """
    )

    st.subheader("EPA limitations")
    st.markdown(
        """
        EPA is useful because it connects production to down, distance, field position, and game context. It is limited for individual valuation because it can blend player quality with scheme, quarterback environment, offensive line, teammates, coaching, opponent strength, and role. That is why this app frames EPA-based production as a screening input, not a full player grade.
        """
    )

    st.subheader("What the model can and cannot claim")
    left, right = st.columns(2)
    with left:
        st.markdown(
            """
            **Supported claims**

            - This player produced more than his public cost rank suggested.
            - This profile showed positive next-season lift versus matched peers.
            - This row is worth deeper scouting and cap review.
            """
        )
    with right:
        st.markdown(
            """
            **Unsupported claims**

            - This proves the player is objectively underpaid.
            - This guarantees a future breakout.
            - This replaces team scouting, medical, scheme, or internal cap data.
            """
        )
