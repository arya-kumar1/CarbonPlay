from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Dict, List, Tuple

NFL_DIVISION_ORDER = ["East", "North", "South", "West"]

NFL_DIVISION_TEAMS: Dict[Tuple[str, str], List[str]] = {
    ("AFC", "East"): ["BUF", "MIA", "NYJ", "NE"],
    ("AFC", "North"): ["BAL", "PIT", "CIN", "CLE"],
    ("AFC", "South"): ["HOU", "IND", "JAX", "TEN"],
    ("AFC", "West"): ["KC", "LAC", "DEN", "LV"],
    ("NFC", "East"): ["PHI", "WAS", "DAL", "NYG"],
    ("NFC", "North"): ["DET", "GB", "MIN", "CHI"],
    ("NFC", "South"): ["TB", "ATL", "NO", "CAR"],
    ("NFC", "West"): ["SF", "LAR", "SEA", "ARI"],
}

NFL_DIVISIONS: Dict[str, Tuple[str, str]] = {
    team: (conference, division)
    for (conference, division), teams in NFL_DIVISION_TEAMS.items()
    for team in teams
}

# Previous-season division ranks used for same-place scheduling.
NFL_PREV_RANK: Dict[str, int] = {
    "BUF": 1, "MIA": 2, "NYJ": 3, "NE": 4,
    "BAL": 1, "PIT": 2, "CIN": 3, "CLE": 4,
    "HOU": 1, "IND": 2, "JAX": 3, "TEN": 4,
    "KC": 1, "LAC": 2, "DEN": 3, "LV": 4,
    "PHI": 1, "WAS": 2, "DAL": 3, "NYG": 4,
    "DET": 1, "GB": 2, "MIN": 3, "CHI": 4,
    "TB": 1, "ATL": 2, "NO": 3, "CAR": 4,
    "SF": 1, "LAR": 2, "SEA": 3, "ARI": 4,
}


def nfl_intra_conf_pairings(season_year: int) -> List[Tuple[str, str]]:
    # 3-year cycle of division-vs-division pairings within conference.
    cycle = [
        [("East", "North"), ("South", "West")],
        [("East", "South"), ("North", "West")],
        [("East", "West"), ("North", "South")],
    ]
    idx = season_year % 3
    return cycle[idx]


def nfl_inter_conf_division_opponent(afc_division: str, season_year: int) -> str:
    # 4-year AFC->NFC rotation.
    i = NFL_DIVISION_ORDER.index(afc_division)
    offset = season_year % 4
    return NFL_DIVISION_ORDER[(i + offset) % 4]


def nfl_inter_conf_division_two_years_ago(afc_division: str, season_year: int) -> str:
    i = NFL_DIVISION_ORDER.index(afc_division)
    offset = (season_year % 4 - 2) % 4
    return NFL_DIVISION_ORDER[(i + offset) % 4]


def nfl_conference_with_9_home_games(season_year: int) -> str:
    # User requirement: NFC has 8 homes in 2025 -> AFC has 9 in 2025.
    # Alternate yearly.
    return "AFC" if season_year % 2 == 1 else "NFC"


def teams_by_conference_and_division() -> Dict[str, Dict[str, List[str]]]:
    out: Dict[str, Dict[str, List[str]]] = defaultdict(dict)
    for (conf, div), teams in NFL_DIVISION_TEAMS.items():
        out[conf][div] = list(teams)
    return out


def nfl_international_fixed_games_2026() -> List[Tuple[date, str, str, str]]:
    # Fully-specified confirmed matchups in the provided prompt.
    return [
        (date(2026, 9, 10), "SF", "LAR", "Melbourne Cricket Ground"),
        (date(2026, 9, 18), "DAL", "BAL", "Maracana"),
    ]
