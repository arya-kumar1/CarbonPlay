from __future__ import annotations

import os
import time
from datetime import date, datetime
from typing import Dict, List, Optional, Set, Tuple

from .venue_catalog import NBA_TEAM_FULL_NAME_BY_CODE

DISCOVERY_BASE = "https://app.ticketmaster.com/discovery/v2"


def _clean_token(text: str) -> str:
    return text.lower().replace(".", " ").replace("-", " ").strip()


def _team_keywords(team_full_name: str) -> Set[str]:
    parts = team_full_name.split()
    keywords: Set[str] = {_clean_token(team_full_name)}
    if len(parts) >= 2:
        nickname = " ".join(parts[1:])
        keywords.add(_clean_token(nickname))
        keywords.add(_clean_token(parts[-1]))
    return {k for k in keywords if k}


def _event_date(event: Dict) -> Optional[date]:
    start = event.get("dates", {}).get("start", {})
    local_date = start.get("localDate")
    if local_date:
        try:
            return date.fromisoformat(local_date)
        except ValueError:
            pass

    dt = start.get("dateTime")
    if not dt:
        return None
    try:
        return datetime.fromisoformat(dt.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _is_cancelled(event: Dict) -> bool:
    status = event.get("dates", {}).get("status", {}).get("code", "")
    return status.lower() in {"cancelled"}


def _looks_like_home_game(event_name: str, team_keywords: Set[str]) -> bool:
    name = _clean_token(event_name)
    return any(keyword in name for keyword in team_keywords)


def _is_basketball_event(event: Dict) -> bool:
    name = _clean_token(event.get("name", "") or "")
    basketball_tokens = ("basketball", "nba", "wnba", "g league", "gleague")
    if any(tok in name for tok in basketball_tokens):
        return True

    for c in event.get("classifications", []) or []:
        segment = _clean_token(c.get("segment", {}).get("name", "") or "")
        genre = _clean_token(c.get("genre", {}).get("name", "") or "")
        sub_genre = _clean_token(c.get("subGenre", {}).get("name", "") or "")
        if "basketball" in segment or "basketball" in genre or "basketball" in sub_genre:
            return True
    return False


class TicketmasterDiscoveryClient:
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        try:
            import requests  # type: ignore
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Ticketmaster integration requires 'requests'. Install dependencies from requirements.txt."
            ) from exc

        self.api_key = api_key or os.getenv("TICKETMASTER_API_KEY")
        self.timeout = timeout
        self.session = requests.Session()
        self._venue_cache: Dict[str, Optional[str]] = {}

    def enabled(self) -> bool:
        return bool(self.api_key)

    def get_venue_id(self, venue_name: str, country_code: str = "US") -> Optional[str]:
        if venue_name in self._venue_cache:
            return self._venue_cache[venue_name]

        url = f"{DISCOVERY_BASE}/venues.json"
        params = {
            "apikey": self.api_key,
            "keyword": venue_name,
            "countryCode": country_code,
            "size": 10,
            "sort": "relevance,desc",
        }
        resp = self.session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()

        data = resp.json()
        venues = data.get("_embedded", {}).get("venues", [])
        if not venues:
            self._venue_cache[venue_name] = None
            return None

        target = _clean_token(venue_name)
        for venue in venues:
            if _clean_token(venue.get("name", "")) == target:
                venue_id = venue.get("id")
                self._venue_cache[venue_name] = venue_id
                return venue_id

        venue_id = venues[0].get("id")
        self._venue_cache[venue_name] = venue_id
        return venue_id

    def get_events_for_venue(
        self,
        venue_id: str,
        start_date: date,
        end_date: date,
        pause_seconds: float = 0.12,
    ) -> List[Dict]:
        all_events: List[Dict] = []
        page = 0
        page_size = 200

        while True:
            if page * page_size >= 1000:
                break

            url = f"{DISCOVERY_BASE}/events.json"
            params = {
                "apikey": self.api_key,
                "venueId": venue_id,
                "startDateTime": f"{start_date.isoformat()}T00:00:00Z",
                "endDateTime": f"{end_date.isoformat()}T23:59:59Z",
                "size": page_size,
                "page": page,
                "sort": "date,asc",
            }
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()

            events = data.get("_embedded", {}).get("events", [])
            all_events.extend(events)

            page_info = data.get("page", {})
            total_pages = page_info.get("totalPages", 0)
            number = page_info.get("number", 0)
            if total_pages == 0 or number >= total_pages - 1:
                break

            page += 1
            time.sleep(pause_seconds)

        return all_events


def build_nba_venue_blocks_from_ticketmaster(
    venues_by_team_code: Dict[str, str],
    season_start: date,
    season_end: date,
    api_key: Optional[str] = None,
) -> Tuple[Dict[str, Set[date]], Dict[str, int]]:
    client = TicketmasterDiscoveryClient(api_key=api_key)
    if not client.enabled():
        return {}, {
            "venues_processed": 0,
            "events_considered": 0,
            "basketball_events_skipped": 0,
            "blocked_dates": 0,
        }

    blocks: Dict[str, Set[date]] = {}
    events_considered = 0
    basketball_events_skipped = 0

    for team_code, venue_name in venues_by_team_code.items():
        venue_id = client.get_venue_id(venue_name)
        if not venue_id:
            continue

        team_name = NBA_TEAM_FULL_NAME_BY_CODE.get(team_code, team_code)
        keywords = _team_keywords(team_name)
        events = client.get_events_for_venue(venue_id, season_start, season_end)

        team_blocked: Set[date] = set()
        for event in events:
            events_considered += 1
            if _is_cancelled(event):
                continue
            if _is_basketball_event(event):
                basketball_events_skipped += 1
                continue

            name = event.get("name", "") or ""
            if _looks_like_home_game(name, keywords):
                continue

            d = _event_date(event)
            if d is None:
                continue
            if season_start <= d <= season_end:
                team_blocked.add(d)

        if team_blocked:
            blocks[team_code] = team_blocked

    blocked_dates = sum(len(dates) for dates in blocks.values())
    diagnostics = {
        "venues_processed": len(venues_by_team_code),
        "events_considered": events_considered,
        "basketball_events_skipped": basketball_events_skipped,
        "blocked_dates": blocked_dates,
    }
    return blocks, diagnostics
