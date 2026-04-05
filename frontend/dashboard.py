from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure local package imports work when Streamlit is launched from any cwd.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scheduler.models import BreakWindow, LeagueConfig
from scheduler.service import run_optimization


st.set_page_config(page_title="Carbon-Aware League Scheduler", layout="wide")
st.title("Carbon-Aware League Scheduler")
st.caption("Optimize season schedules to reduce emissions while preserving fairness and feasibility.")

with st.sidebar:
    st.header("Controls")
    league = st.selectbox("League", ["NBA", "NHL"], index=0)
    if league == "NBA":
        default_start = date(2026, 10, 20)
        default_end = date(2027, 4, 20)
        default_games = 82
        default_all_star_game = date(2027, 2, 14)
        default_special_break = date(2027, 4, 5)
    else:
        default_start = date(2026, 10, 7)
        default_end = date(2027, 4, 18)
        default_games = 82
        default_all_star_game = date(2027, 2, 6)
        default_special_break = date(2027, 2, 7)  # Super Bowl day handling for NHL

    games_per_team = st.slider("Games per team", 58, 90, default_games, step=2)
    season_start = st.date_input("Season start", default_start)
    season_end = st.date_input("Season end", default_end)
    all_star_game_date = st.date_input("All-Star game date (no games)", default_all_star_game)
    ncaa_championship_date = st.date_input(
        "Special no-game date", default_special_break, help="NCAA title day for NBA, Super Bowl window for NHL."
    )

    st.subheader("Constraint Limits")
    max_b2b = st.slider("Max back-to-backs", 0, 28, 15)
    max_3in4 = st.slider("Max 3 in 4 windows", 0, 30, 24)

    st.subheader("Objective Weights")
    sustainability = st.slider("Sustainability", 0.0, 1.0, 0.9, step=0.05)
    fairness = st.slider("Fairness", 0.0, 1.0, 0.08, step=0.01)
    travel_burden = st.slider("Travel burden", 0.0, 1.0, 0.02, step=0.01)

    st.subheader("Travel Model")
    close_range = st.slider("Ground threshold (miles)", 50, 300, 120)
    flight_factor = st.number_input("Flight kg CO2e / mile", min_value=1.0, value=18.0)
    ground_factor = st.number_input("Ground kg CO2e / mile", min_value=0.1, value=1.2)
    use_ticketmaster_blocks = st.checkbox("Use Ticketmaster event blackout dates", value=False)
    ticketmaster_api_key = st.text_input(
        "Ticketmaster API key (optional, falls back to TICKETMASTER_API_KEY env var)",
        type="password",
    )
    include_baseline = st.checkbox("Compute baseline comparison (slower)", value=False)

    run = st.button("Generate Optimized Schedule", type="primary")

if run:
    league_blackouts = {
        date(season_start.year, 12, 24),
        all_star_game_date,
        ncaa_championship_date,
    }
    if league == "NHL":
        league_blackouts |= {
            date(season_start.year, 12, 25),
            date(season_start.year, 12, 26),
        }

    config = LeagueConfig(
        name=league,
        games_per_team=games_per_team,
        season_start=season_start,
        season_end=season_end,
        max_back_to_backs=max_b2b,
        max_three_in_four=max_3in4,
        close_range_miles=float(close_range),
        flight_emissions_kg_per_mile=float(flight_factor),
        ground_emissions_kg_per_mile=float(ground_factor),
        travel_weight=sustainability,
        fairness_weight=fairness,
        density_weight=travel_burden,
        all_star_break=(
            BreakWindow(date(2027, 2, 13), date(2027, 2, 18))
            if league == "NBA"
            else BreakWindow(date(2027, 2, 1), date(2027, 2, 10))
        ),
        league_blackout_dates=league_blackouts,
    )

    data = run_optimization(
        config,
        use_ticketmaster_blocks=use_ticketmaster_blocks,
        ticketmaster_api_key=ticketmaster_api_key or None,
        include_baseline=include_baseline,
    )

    league_metrics = data["league_metrics"]
    scores = data["scores"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("League emissions", f"{league_metrics['league_emissions_kg']:,.0f} kg")
    c2.metric("Avg emissions / game", f"{league_metrics['avg_emissions_per_game']:,.0f} kg")
    c3.metric("Sustainability score", f"{scores['sustainability']:.1f}")
    c4.metric(
        "Vs baseline",
        f"{scores['emissions_improvement_vs_baseline_pct']:.2f}%",
        help="Positive means lower emissions than baseline schedule.",
    )

    team_df = pd.DataFrame(data["team_metrics"])
    schedule_df = pd.DataFrame(data["schedule"])
    baseline_df = (
        pd.DataFrame(data["baseline"]["team_metrics"])
        if data.get("baseline") and data["baseline"].get("team_metrics")
        else pd.DataFrame()
    )
    location_df = pd.DataFrame(data["team_locations"])
    rest_df = pd.DataFrame(data["rest_distribution"])

    tab1, tab2, tab3, tab4 = st.tabs([
        "Team Analytics",
        "Schedule",
        "Comparisons",
        "Maps",
    ])

    with tab1:
        left, right = st.columns(2)
        with left:
            st.plotly_chart(
                px.bar(
                    team_df,
                    x="team",
                    y="emissions_kg",
                    color="emissions_kg",
                    title="Carbon Emissions by Team",
                    labels={"emissions_kg": "kg CO2e"},
                ),
                use_container_width=True,
            )
            st.plotly_chart(
                px.bar(
                    team_df,
                    x="team",
                    y="distance_miles",
                    color="distance_miles",
                    title="Distance Traveled by Team",
                    labels={"distance_miles": "Miles"},
                ),
                use_container_width=True,
            )
        with right:
            st.plotly_chart(
                px.bar(
                    team_df,
                    x="team",
                    y="back_to_backs",
                    color="back_to_backs",
                    title="Back-to-Back Frequency",
                ),
                use_container_width=True,
            )
            if not rest_df.empty:
                st.plotly_chart(
                    px.bar(
                        rest_df,
                        x="team",
                        y="avg_rest_days",
                        title="Rest Days Distribution",
                    ),
                    use_container_width=True,
                )

    with tab2:
        team_filter = st.selectbox("Filter by team", ["All"] + sorted(team_df["team"].tolist()))
        view = schedule_df.copy()
        if team_filter != "All":
            view = view[(view["home"] == team_filter) | (view["away"] == team_filter)]
        st.dataframe(view.sort_values("date"), use_container_width=True)

    with tab3:
        if not baseline_df.empty:
            compare = team_df[["team", "emissions_kg", "distance_miles"]].merge(
                baseline_df[["team", "emissions_kg", "distance_miles"]],
                on="team",
                suffixes=("_optimized", "_baseline"),
            )
            compare["emissions_delta_kg"] = (
                compare["emissions_kg_baseline"] - compare["emissions_kg_optimized"]
            )

            st.plotly_chart(
                px.bar(
                    compare,
                    x="team",
                    y="emissions_delta_kg",
                    color="emissions_delta_kg",
                    title="Optimized vs Baseline Emissions Delta by Team",
                    labels={"emissions_delta_kg": "kg CO2e reduction"},
                ),
                use_container_width=True,
            )
        else:
            st.info("Baseline comparison was skipped for faster schedule generation.")

        summary = {
            "Fairness score": scores["fairness"],
            "Sustainability score": scores["sustainability"],
            "Objective": scores["objective"],
            "League distance miles": league_metrics["league_distance_miles"],
            "Avg distance per team": league_metrics["avg_distance_per_team"],
            "Avg time-zone jumps": league_metrics["avg_time_zone_jumps"],
        }
        st.json(summary)
        st.json(data.get("venue_block_diagnostics", {}))

    with tab4:
        merged = location_df.merge(team_df, left_on="team", right_on="team")

        st.plotly_chart(
            px.scatter_geo(
                merged,
                lat="latitude",
                lon="longitude",
                color="emissions_kg",
                size="distance_miles",
                hover_name="team",
                scope="north america",
                title="League-wide Team Travel & Emissions Map",
            ),
            use_container_width=True,
        )

        selected_team = st.selectbox("Team route map", sorted(team_df["team"].tolist()))
        team_games = schedule_df[(schedule_df["home"] == selected_team) | (schedule_df["away"] == selected_team)]
        if not team_games.empty:
            loc = location_df.set_index("team")
            lats = []
            lons = []
            labels = []
            for _, g in team_games.sort_values("date").iterrows():
                opponent = g["home"] if g["away"] == selected_team else g["away"]
                lats.append(loc.loc[opponent, "latitude"])
                lons.append(loc.loc[opponent, "longitude"])
                labels.append(f"{g['date']} vs {opponent}")

            fig = go.Figure()
            fig.add_trace(
                go.Scattergeo(
                    lon=lons,
                    lat=lats,
                    mode="lines+markers",
                    marker={"size": 7},
                    text=labels,
                )
            )
            fig.update_layout(title=f"{selected_team} Travel Route", geo_scope="north america")
            st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Set your controls and click 'Generate Optimized Schedule'.")
