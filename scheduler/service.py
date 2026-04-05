from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
import random
from typing import Dict

from .data import load_teams_for_league
from .metrics import games_to_rows, rest_distribution, team_metrics
from .models import BreakWindow, LeagueConfig, OptimizationResult
from .models import Game
from .nfl import nfl_international_fixed_games_2026
from .optimizer import optimize_schedule
from .ticketmaster import build_nba_venue_blocks_from_ticketmaster
from .venue_catalog import load_nba_venues_by_team_code


DEFAULT_CSV = Path(__file__).resolve().parent.parent / "locations.csv"
DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _result_key(result: OptimizationResult, prioritize_emissions: bool) -> tuple:
    avg_b2b = sum(s.back_to_backs for s in result.team_states.values()) / max(1, len(result.team_states))
    b2b_target_gap = abs(avg_b2b - 15.0)
    if prioritize_emissions:
        return (result.league_emissions_kg, b2b_target_gap, result.objective_value)
    return (result.objective_value, b2b_target_gap, result.league_emissions_kg)


def _solve_with_restarts(
    config: LeagueConfig,
    teams,
    retries: int = 12,
    prioritize_emissions: bool = True,
):
    best_result: OptimizationResult | None = None
    last_error = None
    for i in range(retries):
        try:
            trial = replace(config, seed=config.seed + i)
            result = optimize_schedule(teams, trial)
            if best_result is None or _result_key(result, prioritize_emissions) < _result_key(
                best_result, prioritize_emissions
            ):
                best_result = result
        except RuntimeError as exc:
            last_error = exc
    if best_result is not None:
        return best_result
    raise RuntimeError(f"Unable to build a feasible schedule after {retries} attempts: {last_error}")


def _merge_venue_blocks(primary: Dict, extra: Dict) -> Dict:
    merged = {team: set(dates) for team, dates in (primary or {}).items()}
    for team, dates in (extra or {}).items():
        merged.setdefault(team, set()).update(dates)
    return merged


def _merge_team_blocks(primary: Dict[str, set], extra: Dict[str, set]) -> Dict[str, set]:
    merged = {team: set(dates) for team, dates in (primary or {}).items()}
    for team, dates in (extra or {}).items():
        merged.setdefault(team, set()).update(dates)
    return merged


def _fourth_thursday_of_november(year: int) -> date:
    d = date(year, 11, 1)
    while d.weekday() != 3:
        d += timedelta(days=1)
    return d + timedelta(days=21)


def _second_sunday_of_february(year: int) -> date:
    d = date(year, 2, 1)
    while d.weekday() != 6:
        d += timedelta(days=1)
    return d + timedelta(days=7)


def _build_nhl_blackouts(config: LeagueConfig) -> set[date]:
    # Christmas break and US Thanksgiving / Super Bowl day.
    return {
        _fourth_thursday_of_november(config.season_start.year),
        date(config.season_start.year, 12, 24),
        date(config.season_start.year, 12, 25),
        date(config.season_start.year, 12, 26),
        _second_sunday_of_february(config.season_end.year),
    }


def _build_nhl_team_bye_weeks(config: LeagueConfig, team_codes: list[str]) -> Dict[str, set[date]]:
    rng = random.Random(config.seed + 2026)
    midpoint = config.season_start + (config.season_end - config.season_start) / 2
    midpoint_date = date(midpoint.year, midpoint.month, midpoint.day)
    window_start = midpoint_date - timedelta(days=28)
    window_end = midpoint_date + timedelta(days=28)
    days = []
    d = window_start
    while d <= window_end:
        if not (config.all_star_break.start <= d <= config.all_star_break.end):
            days.append(d)
        d += timedelta(days=1)

    byes: Dict[str, set[date]] = {}
    if len(days) < 7:
        return byes

    starts = list(range(0, max(1, len(days) - 6), 3))
    rng.shuffle(starts)
    for i, team in enumerate(sorted(team_codes)):
        s_idx = starts[i % len(starts)]
        week = set(days[s_idx : s_idx + 7])
        byes[team] = week
    return byes


def _build_nfl_team_byes(config: LeagueConfig, team_codes: list[str]) -> Dict[str, set[date]]:
    # Single bye week per team between weeks 5-13.
    rng = random.Random(config.seed + 3030)
    season_start = config.season_start
    weekly_slots = []
    for w in range(5, 14):
        sun = season_start + timedelta(days=w * 7 + (6 - season_start.weekday()) % 7)
        weekly_slots.append(sun)
    rng.shuffle(weekly_slots)
    byes: Dict[str, set[date]] = {}
    for i, team in enumerate(sorted(team_codes)):
        sun = weekly_slots[i % len(weekly_slots)]
        week_dates = {sun - timedelta(days=3), sun, sun + timedelta(days=1)}  # Thu/Sun/Mon
        byes[team] = week_dates
    return byes


def _build_nfl_preset_games(config: LeagueConfig) -> list[Game]:
    presets: list[Game] = []
    if config.season_start.year == 2026:
        thanksgiving = _fourth_thursday_of_november(config.season_start.year)
        black_friday = thanksgiving + timedelta(days=1)
        christmas = date(config.season_start.year, 12, 25)
        for i, (d, home, away, venue) in enumerate(nfl_international_fixed_games_2026(), start=1):
            # Keep non-holiday Fridays clear for NFL (except Black Friday / Christmas).
            if d.weekday() == 4 and d not in {black_friday, christmas}:
                d = d + timedelta(days=2)
            presets.append(
                Game(
                    game_id=f"G{i:04d}",
                    date=d,
                    home=home,
                    away=away,
                    venue=venue,
                    neutral_site=venue,
                )
            )
    return presets


def run_optimization(
    config: LeagueConfig,
    csv_path: str | Path = DEFAULT_CSV,
    use_ticketmaster_blocks: bool = False,
    ticketmaster_api_key: str | None = None,
    project_root: str | Path = DEFAULT_PROJECT_ROOT,
    include_baseline: bool = True,
) -> Dict:
    teams = load_teams_for_league(config.name, Path(project_root))
    ticketmaster_diagnostics = {}

    effective_config = config
    if use_ticketmaster_blocks and config.name.upper() == "NBA":
        venue_map = load_nba_venues_by_team_code(project_root)
        try:
            tm_blocks, ticketmaster_diagnostics = build_nba_venue_blocks_from_ticketmaster(
                venues_by_team_code=venue_map,
                season_start=config.season_start,
                season_end=config.season_end,
                api_key=ticketmaster_api_key,
            )
            merged_blocks = _merge_venue_blocks(config.venue_blocks, tm_blocks)
            effective_config = replace(config, venue_blocks=merged_blocks)
        except Exception as exc:  # pragma: no cover - external dependency/runtime path
            ticketmaster_diagnostics = {"error": str(exc)}

    if config.name.upper() == "NHL":
        nhl_blackouts = _build_nhl_blackouts(config)
        team_byes = _build_nhl_team_bye_weeks(config, [t.code for t in teams])
        effective_config = replace(
            effective_config,
            league_blackout_dates=set(effective_config.league_blackout_dates).union(nhl_blackouts),
            team_blackout_dates=_merge_team_blocks(effective_config.team_blackout_dates, team_byes),
            all_star_break=BreakWindow(
                effective_config.all_star_break.start,
                effective_config.all_star_break.end,
            ),
        )

    if config.name.upper() == "NFL":
        effective_config = replace(
            effective_config,
            preset_games=[],
        )

    schedule_fallback_used = False
    retries = 8 if config.name.upper() == "NFL" else 1
    try:
        optimized = _solve_with_restarts(effective_config, teams, retries=retries, prioritize_emissions=True)
    except RuntimeError:
        if use_ticketmaster_blocks:
            effective_config = replace(config, venue_blocks=config.venue_blocks)
            ticketmaster_diagnostics = {
                **ticketmaster_diagnostics,
                "fallback": "ticketmaster_blocks_disabled_due_to_infeasibility",
            }
            optimized = _solve_with_restarts(effective_config, teams, retries=retries, prioritize_emissions=True)
            schedule_fallback_used = True
        else:
            raise
    baseline = None
    if include_baseline:
        baseline_config = replace(
            effective_config,
            travel_weight=0.0,
            fairness_weight=0.35,
            density_weight=0.65,
            seed=effective_config.seed + 500,
        )
        baseline = _solve_with_restarts(
            baseline_config,
            teams,
            retries=1,
            prioritize_emissions=False,
        )

    emissions_delta_pct = 0.0
    if baseline and baseline.league_emissions_kg > 0:
        emissions_delta_pct = (
            (baseline.league_emissions_kg - optimized.league_emissions_kg)
            / baseline.league_emissions_kg
        ) * 100.0

    return {
        "meta": {
            "league": config.name,
            "games": len(optimized.schedule),
            "season_start": config.season_start.isoformat(),
            "season_end": config.season_end.isoformat(),
            "ticketmaster_blocks_enabled": use_ticketmaster_blocks,
            "baseline_included": include_baseline,
            "schedule_fallback_used": schedule_fallback_used,
        },
        "scores": {
            "sustainability": optimized.sustainability_score,
            "fairness": optimized.fairness_score,
            "objective": optimized.objective_value,
            "emissions_improvement_vs_baseline_pct": emissions_delta_pct,
        },
        "league_metrics": {
            "league_distance_miles": optimized.league_distance_miles,
            "league_emissions_kg": optimized.league_emissions_kg,
            "avg_emissions_per_game": optimized.diagnostics["avg_emissions_per_game"],
            "avg_distance_per_team": optimized.diagnostics["avg_distance_per_team"],
            "avg_back_to_backs": optimized.diagnostics["avg_back_to_backs"],
            "avg_time_zone_jumps": optimized.diagnostics["avg_time_zone_jumps"],
        },
        "team_metrics": team_metrics(optimized.team_states),
        "team_locations": [
            {
                "team": t.code,
                "latitude": t.latitude,
                "longitude": t.longitude,
                "timezone": t.timezone,
                "conference": t.conference,
                "division": t.division,
                "aircraft_type": t.aircraft_type,
            }
            for t in teams
        ],
        "rest_distribution": rest_distribution(optimized),
        "schedule": games_to_rows(optimized.schedule),
        "venue_block_diagnostics": {
            "manual_block_dates": sum(len(v) for v in config.venue_blocks.values()),
            "effective_block_dates": sum(len(v) for v in effective_config.venue_blocks.values()),
            "ticketmaster": ticketmaster_diagnostics,
        },
        "baseline": (
            {
                "league_emissions_kg": baseline.league_emissions_kg,
                "league_distance_miles": baseline.league_distance_miles,
                "avg_emissions_per_game": baseline.diagnostics["avg_emissions_per_game"],
                "team_metrics": team_metrics(baseline.team_states),
            }
            if baseline
            else None
        ),
    }
