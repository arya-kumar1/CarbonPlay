from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List

from .league import NBA_DIVISIONS
from .nfl import NFL_DIVISIONS
from .nhl import NHL_AIRCRAFT, NHL_DIVISIONS
from .models import Team


def load_teams_from_csv(csv_path: str | Path) -> List[Team]:
    teams: List[Team] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row["team"]
            conference, division = NBA_DIVISIONS.get(code, ("Unknown", "Unknown"))
            teams.append(
                Team(
                    code=code,
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    timezone=row["timezone"],
                    conference=conference,
                    division=division,
                )
            )
    return teams


def load_nhl_teams_from_csv(csv_path: str | Path) -> List[Team]:
    teams: List[Team] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row["team"]
            conference, division = NHL_DIVISIONS.get(code, ("Unknown", "Unknown"))
            aircraft_type, factor = NHL_AIRCRAFT.get(code, ("Unknown", 18.4))
            teams.append(
                Team(
                    code=code,
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    timezone=row["timezone"],
                    conference=conference,
                    division=division,
                    aircraft_type=aircraft_type,
                    flight_emissions_kg_per_mile=factor,
                )
            )
    return teams


def load_nfl_teams_from_csv(csv_path: str | Path) -> List[Team]:
    teams: List[Team] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row["team"]
            conference, division = NFL_DIVISIONS.get(code, ("Unknown", "Unknown"))
            teams.append(
                Team(
                    code=code,
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    timezone=row["timezone"],
                    conference=conference,
                    division=division,
                )
            )
    return teams


def load_teams_for_league(league: str, base_dir: str | Path) -> List[Team]:
    base = Path(base_dir)
    if league.upper() == "NHL":
        return load_nhl_teams_from_csv(base / "locations_nhl.csv")
    if league.upper() == "NFL":
        return load_nfl_teams_from_csv(base / "locations_nfl.csv")
    return load_teams_from_csv(base / "locations.csv")


def team_lookup(teams: Iterable[Team]) -> Dict[str, Team]:
    return {t.code: t for t in teams}
