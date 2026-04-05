from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Set, Tuple


@dataclass(frozen=True)
class Team:
    code: str
    latitude: float
    longitude: float
    timezone: str
    conference: str
    division: str
    aircraft_type: str | None = None
    flight_emissions_kg_per_mile: float | None = None


@dataclass(frozen=True)
class BreakWindow:
    start: date
    end: date


@dataclass
class LeagueConfig:
    name: str = "NBA"
    games_per_team: int = 82
    season_start: date = date(2026, 10, 20)
    season_end: date = date(2027, 4, 20)
    max_back_to_backs: int = 15
    max_three_in_four: int = 24
    close_range_miles: float = 120.0
    flight_emissions_kg_per_mile: float = 18.0
    ground_emissions_kg_per_mile: float = 1.2
    travel_weight: float = 0.9
    fairness_weight: float = 0.08
    density_weight: float = 0.02
    seed: int = 7
    all_star_break: BreakWindow = field(
        default_factory=lambda: BreakWindow(date(2027, 2, 13), date(2027, 2, 18))
    )
    league_blackout_dates: Set[date] = field(default_factory=set)
    team_blackout_dates: Dict[str, Set[date]] = field(default_factory=dict)
    venue_blocks: Dict[str, Set[date]] = field(default_factory=dict)
    preset_games: List["Game"] = field(default_factory=list)


@dataclass(frozen=True)
class Game:
    game_id: str
    date: date
    home: str
    away: str
    venue: str
    neutral_site: Optional[str] = None


@dataclass
class TeamState:
    games: List[Game] = field(default_factory=list)
    total_distance_miles: float = 0.0
    total_emissions_kg: float = 0.0
    back_to_backs: int = 0
    three_in_four: int = 0
    timezone_jumps: int = 0


@dataclass
class OptimizationResult:
    schedule: List[Game]
    team_states: Dict[str, TeamState]
    league_emissions_kg: float
    league_distance_miles: float
    fairness_score: float
    sustainability_score: float
    objective_value: float
    diagnostics: Dict[str, float]


DivisionMap = Dict[str, Tuple[str, str]]
