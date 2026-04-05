from __future__ import annotations

from pathlib import Path
from typing import Dict

NBA_TEAM_NAME_TO_CODE = {
    "Atlanta Hawks": "ATL",
    "Boston Celtics": "BOS",
    "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA",
    "Chicago Bulls": "CHI",
    "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL",
    "Denver Nuggets": "DEN",
    "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW",
    "Houston Rockets": "HOU",
    "Indiana Pacers": "IND",
    "Los Angeles Clippers": "LAC",
    "Los Angeles Lakers": "LAL",
    "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA",
    "Milwaukee Bucks": "MIL",
    "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP",
    "New York Knicks": "NYK",
    "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL",
    "Philadelphia 76ers": "PHI",
    "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR",
    "Sacramento Kings": "SAC",
    "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR",
    "Utah Jazz": "UTA",
    "Washington Wizards": "WAS",
}

NBA_FALLBACK_VENUES_BY_CODE = {
    "ATL": "State Farm Arena",
    "BOS": "TD Garden",
    "BKN": "Barclays Center",
    "CHA": "Spectrum Center",
    "CHI": "United Center",
    "CLE": "Rocket Arena",
    "DAL": "American Airlines Center",
    "DEN": "Ball Arena",
    "DET": "Little Caesars Arena",
    "GSW": "Chase Center",
    "HOU": "Toyota Center",
    "IND": "Gainbridge Fieldhouse",
    "LAC": "Intuit Dome",
    "LAL": "Crypto.com Arena",
    "MEM": "FedExForum",
    "MIA": "Kaseya Center",
    "MIL": "Fiserv Forum",
    "MIN": "Target Center",
    "NOP": "Smoothie King Center",
    "NYK": "Madison Square Garden",
    "OKC": "Paycom Center",
    "ORL": "Kia Center",
    "PHI": "Xfinity Mobile Arena",
    "PHX": "Mortgage Matchup Center",
    "POR": "Moda Center",
    "SAC": "Golden 1 Center",
    "SAS": "Frost Bank Center",
    "TOR": "Scotiabank Arena",
    "UTA": "Delta Center",
    "WAS": "Capital One Arena",
}

NBA_TEAM_FULL_NAME_BY_CODE = {
    code: full_name for full_name, code in NBA_TEAM_NAME_TO_CODE.items()
}


def _normalize_team_name(name: str) -> str:
    return (
        name.replace("\u00a0", " ")
        .replace("’", "'")
        .replace("  ", " ")
        .strip()
    )


def _parse_markdown_team_venues(md_path: Path) -> Dict[str, str]:
    venues: Dict[str, str] = {}
    if not md_path.exists():
        return venues

    for line in md_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 4:
            continue
        team = parts[1]
        venue = parts[2]
        if team in {"Team", "---"}:
            continue
        if not team or not venue or team.startswith("-"):
            continue
        venues[_normalize_team_name(team)] = _normalize_team_name(venue)

    return venues


def load_nba_venues_by_team_code(base_dir: str | Path) -> Dict[str, str]:
    base = Path(base_dir)
    md_path = base / "nba_arenas_2025_2026.md"
    parsed = _parse_markdown_team_venues(md_path)

    mapped: Dict[str, str] = {}
    normalized_map = {_normalize_team_name(k): v for k, v in NBA_TEAM_NAME_TO_CODE.items()}
    for team_name, venue in parsed.items():
        code = normalized_map.get(_normalize_team_name(team_name))
        if code:
            mapped[code] = venue

    if mapped:
        return mapped
    return dict(NBA_FALLBACK_VENUES_BY_CODE)


def load_all_league_venues(base_dir: str | Path) -> Dict[str, Dict[str, str]]:
    base = Path(base_dir)
    return {
        "NBA": _parse_markdown_team_venues(base / "nba_arenas_2025_2026.md"),
        "NHL": _parse_markdown_team_venues(base / "nhl_arenas_2025_2026.md"),
        "NFL": _parse_markdown_team_venues(base / "nfl_stadiums_2025_2026.md"),
    }
