from __future__ import annotations

from datetime import date

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .models import BreakWindow, LeagueConfig
from .service import run_optimization


app = FastAPI(title="Carbon-Aware League Scheduler", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://carbon-play-jxqaxmt7g-arya-kumar1s-projects.vercel.app",
        "https://carbon-play-bvr2kcxab-arya-kumar1s-projects.vercel.app",

    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OptimizeRequest(BaseModel):
    league: str = "NBA"
    games_per_team: int = Field(default=82, ge=10)
    season_start: date = date(2026, 10, 20)
    season_end: date = date(2027, 4, 20)
    max_back_to_backs: int = Field(default=15, ge=0)
    max_three_in_four: int = Field(default=24, ge=0)
    close_range_miles: float = 120.0
    flight_emissions_kg_per_mile: float = 18.0
    ground_emissions_kg_per_mile: float = 1.2
    sustainability_weight: float = 0.9
    fairness_weight: float = 0.08
    travel_burden_weight: float = 0.02
    all_star_break_start: date = date(2027, 2, 13)
    all_star_break_end: date = date(2027, 2, 18)
    all_star_game_date: date = date(2027, 2, 14)
    ncaa_championship_date: date = date(2027, 4, 5)
    seed: int = 7
    use_ticketmaster_blocks: bool = False
    ticketmaster_api_key: str | None = None
    include_baseline: bool = False


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/optimize")
def optimize(payload: OptimizeRequest) -> dict:
    season_christmas_eve = date(payload.season_start.year, 12, 24)
    blackout_dates = {
        season_christmas_eve,
        payload.all_star_game_date,
        payload.ncaa_championship_date,
    }
    config = LeagueConfig(
        name=payload.league,
        games_per_team=payload.games_per_team,
        season_start=payload.season_start,
        season_end=payload.season_end,
        max_back_to_backs=payload.max_back_to_backs,
        max_three_in_four=payload.max_three_in_four,
        close_range_miles=payload.close_range_miles,
        flight_emissions_kg_per_mile=payload.flight_emissions_kg_per_mile,
        ground_emissions_kg_per_mile=payload.ground_emissions_kg_per_mile,
        travel_weight=payload.sustainability_weight,
        fairness_weight=payload.fairness_weight,
        density_weight=payload.travel_burden_weight,
        all_star_break=BreakWindow(payload.all_star_break_start, payload.all_star_break_end),
        league_blackout_dates=blackout_dates,
        seed=payload.seed,
    )
    return run_optimization(
        config,
        use_ticketmaster_blocks=payload.use_ticketmaster_blocks,
        ticketmaster_api_key=payload.ticketmaster_api_key,
        include_baseline=payload.include_baseline,
    )
