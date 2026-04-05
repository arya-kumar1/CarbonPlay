"""
Ticketmaster Discovery API Helper
--------------------------------

This script demonstrates how to retrieve event listings for each team’s home venue
in the NBA, NHL and NFL during the 2025–26 seasons.  It uses the Ticketmaster
Discovery API to look up a venue’s identifier and then query for events
scheduled during a specified date range.  Replace the `{API_KEY}` token with
your own Ticketmaster API key before running.

Requirements:
    pip install requests

Example usage:

    python ticketmaster_events.py

This will loop through the hard‑coded lists of venue names for each league,
obtain the Ticketmaster venue ID for each and fetch events between
1 July 2025 and 30 June 2026.  Results are printed to the console but could
easily be saved to a file or database.

Note:
    - The Ticketmaster API imposes rate limits; you may need to throttle
      requests or add caching if processing many venues.
    - Not all events at a venue may be available via Ticketmaster (some
      venues use alternative ticketing partners).
"""

import datetime
import json
import time
from typing import Dict, List, Optional

import requests


API_KEY = "{API_KEY}"  # Replace with your actual Ticketmaster API key

# Date range for the 2025–26 season (ISO 8601 timestamps)
START_DATE = "2025-07-01T00:00:00Z"
END_DATE = "2026-06-30T23:59:59Z"


def get_venue_id(name: str) -> Optional[str]:
    """Look up a venue ID in Ticketmaster by venue name.

    Args:
        name: The official name of the venue (e.g. "State Farm Arena").

    Returns:
        The venue ID string if found, otherwise None.
    """
    url = "https://app.ticketmaster.com/discovery/v2/venues.json"
    params = {
        "keyword": name,
        "apikey": API_KEY,
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    if "_embedded" not in data or "venues" not in data["_embedded"]:
        return None
    # In many cases the first venue is the correct one; refine if necessary
    for venue in data["_embedded"]["venues"]:
        if venue.get("name", "").lower() == name.lower():
            return venue.get("id")
    # fallback: return the first venue ID
    return data["_embedded"]["venues"][0].get("id")


def get_events_for_venue(venue_id: str, start_date: str, end_date: str) -> List[Dict[str, str]]:
    """Fetch events for a given venue within a specified date range.

    Args:
        venue_id: Ticketmaster venue identifier.
        start_date: ISO 8601 start date/time (inclusive).
        end_date: ISO 8601 end date/time (inclusive).

    Returns:
        A list of dictionaries representing events.  Each dictionary contains
        basic information such as event name, date, and classification.
    """
    events: List[Dict[str, str]] = []
    page = 0
    while True:
        url = "https://app.ticketmaster.com/discovery/v2/events.json"
        params = {
            "venueId": venue_id,
            "startDateTime": start_date,
            "endDateTime": end_date,
            "apikey": API_KEY,
            "size": 200,
            "page": page,
        }
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if "_embedded" in data and "events" in data["_embedded"]:
            for event in data["_embedded"]["events"]:
                info = {
                    "name": event.get("name"),
                    "date": event.get("dates", {}).get("start", {}).get("dateTime"),
                    "status": event.get("dates", {}).get("status", {}).get("code"),
                    "classifications": "/".join(
                        [c.get("segment", {}).get("name", "") for c in event.get("classifications", [])]
                    ),
                    "url": event.get("url"),
                }
                events.append(info)
        # Determine if there is another page
        page_info = data.get("page", {})
        if page_info.get("number", 0) >= page_info.get("totalPages", 0) - 1:
            break
        page += 1
        time.sleep(0.1)  # brief pause to respect rate limits
    return events


def fetch_league_events(venues: Dict[str, str]) -> Dict[str, List[Dict[str, str]]]:
    """Retrieve event listings for a dictionary of venue names.

    Args:
        venues: A mapping from team or franchise name to its official venue name.

    Returns:
        A mapping from venue name to a list of events.
    """
    results: Dict[str, List[Dict[str, str]]] = {}
    for team, venue_name in venues.items():
        print(f"Fetching venue ID for {team} – {venue_name}…")
        venue_id = get_venue_id(venue_name)
        if not venue_id:
            print(f"Warning: No venue ID found for {venue_name}")
            continue
        print(f"Venue ID for {venue_name}: {venue_id}")
        events = get_events_for_venue(venue_id, START_DATE, END_DATE)
        print(f"Found {len(events)} events at {venue_name}")
        results[venue_name] = events
    return results


def main() -> None:
    """Main entry point for script execution."""
    # Define dictionaries of team-to-venue mappings.  These should align with
    # the data in the markdown documents.
    nba_venues = {
        "Atlanta Hawks": "State Farm Arena",
        "Boston Celtics": "TD Garden",
        "Brooklyn Nets": "Barclays Center",
        "Charlotte Hornets": "Spectrum Center",
        "Chicago Bulls": "United Center",
        "Cleveland Cavaliers": "Rocket Arena",
        "Dallas Mavericks": "American Airlines Center",
        "Denver Nuggets": "Ball Arena",
        "Detroit Pistons": "Little Caesars Arena",
        "Golden State Warriors": "Chase Center",
        "Houston Rockets": "Toyota Center",
        "Indiana Pacers": "Gainbridge Fieldhouse",
        "LA Clippers": "Intuit Dome",
        "LA Lakers": "Crypto.com Arena",
        "Memphis Grizzlies": "FedExForum",
        "Miami Heat": "Kaseya Center",
        "Milwaukee Bucks": "Fiserv Forum",
        "Minnesota Timberwolves": "Target Center",
        "New Orleans Pelicans": "Smoothie King Center",
        "New York Knicks": "Madison Square Garden",
        "Oklahoma City Thunder": "Paycom Center",
        "Orlando Magic": "Kia Center",
        "Philadelphia 76ers": "Xfinity Mobile Arena",
        "Phoenix Suns": "Mortgage Matchup Center",
        "Portland Trail Blazers": "Moda Center",
        "Sacramento Kings": "Golden 1 Center",
        "San Antonio Spurs": "Frost Bank Center",
        "Toronto Raptors": "Scotiabank Arena",
        "Utah Jazz": "Delta Center",
        "Washington Wizards": "Capital One Arena",
    }

    nhl_venues = {
        "Anaheim Ducks": "Honda Center",
        "Boston Bruins": "TD Garden",
        "Buffalo Sabres": "KeyBank Center",
        "Carolina Hurricanes": "Lenovo Center",
        "Columbus Blue Jackets": "Nationwide Arena",
        "Detroit Red Wings": "Little Caesars Arena",
        "Florida Panthers": "Amerant Bank Arena",
        "Montreal Canadiens": "Bell Centre",
        "New Jersey Devils": "Prudential Center",
        "New York Islanders": "UBS Arena",
        "New York Rangers": "Madison Square Garden",
        "Ottawa Senators": "Canadian Tire Centre",
        "Philadelphia Flyers": "Xfinity Mobile Arena",
        "Pittsburgh Penguins": "PPG Paints Arena",
        "Tampa Bay Lightning": "Benchmark International Arena",
        "Toronto Maple Leafs": "Scotiabank Arena",
        "Washington Capitals": "Capital One Arena",
        "Calgary Flames": "Scotiabank Saddledome",
        "Chicago Blackhawks": "United Center",
        "Colorado Avalanche": "Ball Arena",
        "Dallas Stars": "American Airlines Center",
        "Edmonton Oilers": "Rogers Place",
        "Los Angeles Kings": "Crypto.com Arena",
        "Minnesota Wild": "Xcel Energy Center",
        "Nashville Predators": "Bridgestone Arena",
        "San Jose Sharks": "SAP Center at San Jose",
        "Seattle Kraken": "Climate Pledge Arena",
        "St. Louis Blues": "Enterprise Center",
        "Vancouver Canucks": "Rogers Arena",
        "Vegas Golden Knights": "T-Mobile Arena",
        "Winnipeg Jets": "Canada Life Centre",
        "Utah Mammoth": "Delta Center",
    }

    nfl_venues = {
        "Arizona Cardinals": "State Farm Stadium",
        "Atlanta Falcons": "Mercedes-Benz Stadium",
        "Carolina Panthers": "Bank of America Stadium",
        "Chicago Bears": "Soldier Field",
        "Dallas Cowboys": "AT&T Stadium",
        "Detroit Lions": "Ford Field",
        "Green Bay Packers": "Lambeau Field",
        "Los Angeles Rams": "SoFi Stadium",
        "Minnesota Vikings": "U.S. Bank Stadium",
        "New Orleans Saints": "Caesars Superdome",
        "New York Giants": "MetLife Stadium",
        "Philadelphia Eagles": "Lincoln Financial Field",
        "San Francisco 49ers": "Levi’s Stadium",
        "Seattle Seahawks": "Lumen Field",
        "Tampa Bay Buccaneers": "Raymond James Stadium",
        "Washington Commanders": "Northwest Stadium",
        "Baltimore Ravens": "M&T Bank Stadium",
        "Buffalo Bills": "Highmark Stadium",
        "Cincinnati Bengals": "Paycor Stadium",
        "Cleveland Browns": "Huntington Bank Field",
        "Pittsburgh Steelers": "Acrisure Stadium",
        "Houston Texans": "NRG Stadium",
        "Indianapolis Colts": "Lucas Oil Stadium",
        "Jacksonville Jaguars": "EverBank Stadium",
        "Tennessee Titans": "Nissan Stadium",
        "Denver Broncos": "Empower Field at Mile High",
        "Kansas City Chiefs": "GEHA Field at Arrowhead Stadium",
        "Las Vegas Raiders": "Allegiant Stadium",
        "Los Angeles Chargers": "SoFi Stadium",
        "Miami Dolphins": "Hard Rock Stadium",
        "New England Patriots": "Gillette Stadium",
        "New York Jets": "MetLife Stadium",
    }

    # Fetch events for each league; results could be stored or processed further
    print("\nFetching NBA venue events…")
    nba_events = fetch_league_events(nba_venues)
    print("\nFetching NHL venue events…")
    nhl_events = fetch_league_events(nhl_venues)
    print("\nFetching NFL venue events…")
    nfl_events = fetch_league_events(nfl_venues)

    # Example: print a summary of results
    for league_name, league_events in [
        ("NBA", nba_events),
        ("NHL", nhl_events),
        ("NFL", nfl_events),
    ]:
        print(f"\n=== {league_name} Events Summary ===")
        for venue_name, events in league_events.items():
            print(f"{venue_name}: {len(events)} events")


if __name__ == "__main__":
    main()