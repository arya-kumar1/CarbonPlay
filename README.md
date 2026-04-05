# Carbon-Aware Sports Scheduling Optimizer

A full-stack prototype that generates season schedules minimizing travel emissions while preserving competitive fairness, venue feasibility, and league density constraints.

## What this includes

- Constraint-aware backend scheduler
- Carbon emissions + travel burden objective weighting
- Fairness metrics (rest parity, travel variance)
- Venue feasibility (blocked dates, no double-booking)
- League breaks (All-Star window)
- Baseline-vs-optimized comparison outputs
- Optional Ticketmaster Discovery API venue blackout ingestion
- Supports **NBA**, **NHL**, and **NFL** schedule generation
- FastAPI endpoint for optimization
- Streamlit dashboard with interactive controls and visual analytics

## Core constraints supported

- Number of teams and games per team
- Equal home and away games
- Home/away assignment by matchup pair
- Conference/division-aware matchup weighting
- Max back-to-backs
- Max 3-games-in-4-nights windows
- Season start/end boundaries
- Break windows
- Preplanned venue blocks
- Venue no-overlap per date
- Travel distance + timezone jumps
- Fairness penalties for rest imbalance and uneven burden

## League-specific schedule rules

- NBA (82 games):
  - 4 games vs each division opponent (16)
  - 4 games vs 6 non-division conference opponents (24)
  - 3 games vs remaining 4 conference opponents (12)
  - 2 games vs each opposite-conference team (30)
- NHL (82 games):
  - Within division: 26 games (4 vs 5 opponents, 3 vs 2 opponents)
  - Same conference non-division: 3 vs 8 opponents (24)
  - Inter-conference: 2 vs 16 opponents (32)
  - Canadian rivalry guarantees in Atlantic/Pacific are enforced for 4-game pairings
  - Team-level midseason bye-week blackouts are applied
- NFL (17 games, 32 teams):
  - Matchup matrix aligned with regular-season structure: 6 divisional (home/away), 4 intra-conference division rotation, 4 inter-conference division rotation, 2 same-place vs other in-conference divisions, 1 inter-conference “17th game” vs the division faced two years prior
  - Yearly home/away split: one conference gets 9 home games, the other 8 (alternates by season year)
  - **Weekly calendar**: one **Thursday Night** and one **Monday Night** game per NFL week; **Thanksgiving** has three Thursday games (including traditional Detroit and Dallas home slots when holiday seeding is enabled)
  - Anchored holiday windows: Black Friday and Christmas multi-game days (when in season range and holiday mode is on)
  - One bye week per team (weeks 5–13 window) with Thu/Sun/Mon blocked for that team
  - Short-week rules: blocks impossible Mon→Thu turnarounds; one game per team per NFL week (Thu–Wed)
  - Emissions objective uses the same travel model as other leagues (no NBA-style back-to-back density targets)
  - Team data: `locations_nfl.csv`; logic: `scheduler/nfl.py`, dedicated weekly optimizer path in `scheduler/optimizer.py`

## Transportation model

- Close-range threshold routes use ground emissions factor
- Longer routes use flight emissions factor (default tuned for chartered narrow-body travel model)

## Project structure

- `scheduler/optimizer.py`: matchup generation + schedule optimization loop
- `scheduler/service.py`: orchestration + baseline comparison
- `scheduler/api.py`: FastAPI service
- `scheduler/ticketmaster.py`: Ticketmaster Discovery API client and blackout builder
- `scheduler/venue_catalog.py`: league venue parsing from markdown catalogs
- `frontend/dashboard.py`: Streamlit dashboard and visualizations
- `locations.csv`: team stadium coordinates + timezone
- `locations_nhl.csv`: NHL arena coordinates + timezone
- `locations_nfl.csv`: NFL stadium coordinates + timezone
- `scheduler/nhl.py`: NHL divisions and team aircraft mappings
- `scheduler/nfl.py`: NFL divisions, rotation helpers, and optional fixed international games metadata

## Run locally

1. Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure environment variables:

```bash
cp .env.example .env
# then edit .env and set TICKETMASTER_API_KEY=...
```

3. Run API:

```bash
uvicorn scheduler.api:app --reload
```

4. Run dashboard:

```bash
streamlit run frontend/dashboard.py
```

5. Optional CLI run:

```bash
python -m scheduler.cli --games-per-team 82
```

## Next.js dashboard (premium UI)

An additional frontend is available in `dashboard-next/` using Next.js + shadcn-style components + Recharts + Mapbox. It supports all three leagues from the sidebar; for **NFL**, the overview includes a **short-week chart** (Monday / Thursday / Friday game counts per team) alongside emissions by team.

```bash
cd dashboard-next
cp .env.example .env.local
npm install
npm run dev
```

## API usage

`POST /optimize`

Payload fields include:
- `league` (`"NBA"`, `"NHL"`, or `"NFL"`)
- `games_per_team`
- `season_start`, `season_end`
- `max_back_to_backs`, `max_three_in_four`
- `sustainability_weight`, `fairness_weight`, `travel_burden_weight`
- `close_range_miles`
- `flight_emissions_kg_per_mile`, `ground_emissions_kg_per_mile`
- `use_ticketmaster_blocks`
- `ticketmaster_api_key` (optional, otherwise uses `TICKETMASTER_API_KEY`)

Response includes:
- full generated schedule
- team-by-team travel/emissions metrics
- league totals
- sustainability + fairness scores
- comparison against a baseline schedule

## Notes

- This prototype uses a greedy multi-objective heuristic with restart attempts.
- Restart search now selects the lowest-emissions feasible schedule by default.
- Ticketmaster integration uses Discovery API `venues` and `events` endpoints and converts non-home-team events into blocked venue dates.
- Ticketmaster blackout ingestion skips basketball/NBA events so league games are not treated as venue conflicts.
- Default settings are tuned for feasible 82-game NBA season generation (`2026-10-20` to `2027-04-20`, `max_back_to_backs=22`, `max_three_in_four=24`).
- NFL defaults in the Next.js app use a shorter season window (e.g. `2026-09-10`–`2027-01-10`), `games_per_team=17`, and zero back-to-back / three-in-four targets, matching the weekly NFL model.
- NHL emissions use team-specific charter aircraft factors from configured mappings (with Utah Mammoth assumed Boeing 757).
- For production-grade exact optimization, you can swap in OR-Tools CP-SAT or MILP while reusing this data model and UI.
