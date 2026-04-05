from __future__ import annotations

from datetime import date
from typing import Dict, List

from .models import Game, OptimizationResult, Team, TeamState


def games_to_rows(schedule: List[Game]) -> List[Dict[str, str]]:
    return [
        {
            "game_id": g.game_id,
            "date": g.date.isoformat(),
            "home": g.home,
            "away": g.away,
            "venue": g.venue,
        }
        for g in schedule
    ]


def team_metrics(team_states: Dict[str, TeamState]) -> List[Dict[str, float]]:
    rows: List[Dict[str, float]] = []
    for code, state in sorted(team_states.items()):
        rows.append(
            {
                "team": code,
                "distance_miles": state.total_distance_miles,
                "emissions_kg": state.total_emissions_kg,
                "back_to_backs": state.back_to_backs,
                "three_in_four": state.three_in_four,
                "timezone_jumps": state.timezone_jumps,
            }
        )
    return rows


def rest_distribution(result: OptimizationResult) -> List[Dict[str, float]]:
    rows: List[Dict[str, float]] = []
    for code, state in result.team_states.items():
        dates = sorted(g.date for g in state.games)
        if len(dates) < 2:
            continue
        rests = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
        rows.append(
            {
                "team": code,
                "avg_rest_days": sum(rests) / len(rests),
                "min_rest_days": min(rests),
                "max_rest_days": max(rests),
            }
        )
    return sorted(rows, key=lambda x: x["team"])
