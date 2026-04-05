from datetime import date, timedelta
from collections import defaultdict

from scheduler.data import load_teams_from_csv
from scheduler.models import BreakWindow, LeagueConfig
from scheduler.optimizer import (
    build_matchups,
    optimize_schedule,
    _nfl_thanksgiving,
    _nfl_week_index,
)
from scheduler.nfl import (
    NFL_DIVISION_ORDER,
    nfl_conference_with_9_home_games,
    nfl_inter_conf_division_opponent,
    nfl_inter_conf_division_two_years_ago,
    nfl_intra_conf_pairings,
)
from scheduler.ticketmaster import _event_date, _is_basketball_event


def test_matchup_count_and_balance():
    teams = load_teams_from_csv("locations.csv")
    config = LeagueConfig(games_per_team=82)

    directed = build_matchups(teams, config)
    counts = {t.code: {"home": 0, "away": 0} for t in teams}
    for home, away in directed:
        counts[home]["home"] += 1
        counts[away]["away"] += 1

    for team, split in counts.items():
        assert split["home"] == 41
        assert split["away"] == 41


def test_optimizer_runs_small_schedule():
    teams = load_teams_from_csv("locations.csv")
    config = LeagueConfig(
        games_per_team=60,
        season_start=date(2026, 10, 20),
        season_end=date(2027, 4, 12),
        max_back_to_backs=14,
        max_three_in_four=16,
        all_star_break=BreakWindow(date(2027, 2, 13), date(2027, 2, 18)),
        seed=10,
    )

    result = optimize_schedule(teams, config)
    expected_games = len(teams) * config.games_per_team // 2
    assert len(result.schedule) == expected_games
    assert result.league_emissions_kg > 0


def test_ticketmaster_event_date_parsing():
    event = {
        "dates": {
            "start": {
                "localDate": "2026-11-14",
                "dateTime": "2026-11-15T03:00:00Z",
            }
        }
    }
    assert _event_date(event) == date(2026, 11, 14)


def test_ticketmaster_basketball_filter():
    event = {
        "name": "NBA Basketball: Lakers vs Celtics",
        "classifications": [
            {
                "segment": {"name": "Sports"},
                "genre": {"name": "Basketball"},
                "subGenre": {"name": "NBA"},
            }
        ],
    }
    assert _is_basketball_event(event) is True


def test_nba_82_matchup_matrix_and_blackout_dates():
    teams = load_teams_from_csv("locations.csv")
    team_map = {t.code: t for t in teams}
    config = LeagueConfig(
        name="NBA",
        games_per_team=82,
        season_start=date(2026, 10, 20),
        season_end=date(2027, 4, 20),
        all_star_break=BreakWindow(date(2027, 2, 13), date(2027, 2, 18)),
        league_blackout_dates={date(2026, 12, 24), date(2027, 2, 14), date(2027, 4, 5)},
    )

    directed = build_matchups(teams, config)
    pair_totals = defaultdict(int)
    home = defaultdict(int)
    away = defaultdict(int)
    for h, a in directed:
        pair_totals[tuple(sorted((h, a)))] += 1
        home[h] += 1
        away[a] += 1

    for t in teams:
        c = t.code
        assert home[c] == 41
        assert away[c] == 41

        div = 0
        conf4 = 0
        conf3 = 0
        inter = 0
        for o in team_map:
            if o == c:
                continue
            cnt = pair_totals[tuple(sorted((c, o)))]
            if team_map[o].conference != t.conference:
                inter += cnt
            elif team_map[o].division == t.division:
                div += cnt
            else:
                if cnt == 4:
                    conf4 += cnt
                elif cnt == 3:
                    conf3 += cnt
                else:
                    raise AssertionError(f"Unexpected same-conference count {c}-{o}: {cnt}")

        assert div == 16
        assert conf4 == 24
        assert conf3 == 12
        assert inter == 30

    result = optimize_schedule(teams, config)
    assert len(result.schedule) == 1230
    assert all(g.date not in config.league_blackout_dates for g in result.schedule)
    # Hard density rule: no team should have 3 consecutive game days.
    by_team_dates = defaultdict(list)
    for g in result.schedule:
        by_team_dates[g.home].append(g.date)
        by_team_dates[g.away].append(g.date)
    for dates in by_team_dates.values():
        ordered = sorted(set(dates))
        streak = 1
        max_streak = 1
        for i in range(1, len(ordered)):
            if (ordered[i] - ordered[i - 1]).days == 1:
                streak += 1
            else:
                streak = 1
            max_streak = max(max_streak, streak)
        assert max_streak < 3
    # B2B profile should stay close to target range.
    avg_b2b = sum(s.back_to_backs for s in result.team_states.values()) / len(result.team_states)
    assert 12 <= avg_b2b <= 16.5


def test_nhl_82_matchup_matrix_structure():
    from scheduler.data import load_teams_for_league

    teams = load_teams_for_league("NHL", ".")
    team_map = {t.code: t for t in teams}
    config = LeagueConfig(
        name="NHL",
        games_per_team=82,
        season_start=date(2026, 10, 7),
        season_end=date(2027, 4, 18),
    )
    directed = build_matchups(teams, config)
    pair_totals = defaultdict(int)
    home = defaultdict(int)
    away = defaultdict(int)
    for h, a in directed:
        pair_totals[tuple(sorted((h, a)))] += 1
        home[h] += 1
        away[a] += 1

    for t in teams:
        c = t.code
        assert home[c] == 41
        assert away[c] == 41
        division_games = 0
        conf_non_div_games = 0
        inter_games = 0
        division_three = 0
        division_four = 0
        for o in team_map:
            if o == c:
                continue
            cnt = pair_totals[tuple(sorted((c, o)))]
            if team_map[o].conference != t.conference:
                inter_games += cnt
                assert cnt == 2
            elif team_map[o].division != t.division:
                conf_non_div_games += cnt
                assert cnt == 3
            else:
                division_games += cnt
                if cnt == 3:
                    division_three += 1
                elif cnt == 4:
                    division_four += 1
                else:
                    raise AssertionError(f"Unexpected division count {c}-{o}: {cnt}")

        assert division_games == 26
        assert conf_non_div_games == 24
        assert inter_games == 32
        assert division_three == 2
        assert division_four == 5


def test_nfl_17_matchup_structure_and_home_split():
    from scheduler.data import load_teams_for_league

    teams = load_teams_for_league("NFL", ".")
    team_map = {t.code: t for t in teams}
    season_year = 2026
    config = LeagueConfig(
        name="NFL",
        games_per_team=17,
        season_start=date(2026, 9, 10),
        season_end=date(2027, 1, 10),
        max_back_to_backs=0,
        max_three_in_four=0,
    )
    directed = build_matchups(teams, config)
    pair_totals = defaultdict(int)
    home = defaultdict(int)
    away = defaultdict(int)
    for h, a in directed:
        pair_totals[tuple(sorted((h, a)))] += 1
        home[h] += 1
        away[a] += 1

    intra_pairs = nfl_intra_conf_pairings(season_year)
    paired = {k: v for a, b in intra_pairs for k, v in ((a, b), (b, a))}
    conf_with_9 = nfl_conference_with_9_home_games(season_year)

    for t in teams:
        c = t.code
        conf = t.conference
        div = t.division
        assert home[c] + away[c] == 17
        assert home[c] == (9 if conf == conf_with_9 else 8)

        divisional = 0
        intra_rot = 0
        inter_rot = 0
        same_place = 0
        extra17 = 0

        intra_target = paired[div]
        inter_target = nfl_inter_conf_division_opponent(div, season_year)
        extra_target = nfl_inter_conf_division_two_years_ago(div, season_year)
        for o, ot in team_map.items():
            if o == c:
                continue
            cnt = pair_totals[tuple(sorted((c, o)))]
            if cnt == 0:
                continue
            if ot.conference == conf and ot.division == div:
                assert cnt == 2
                divisional += cnt
            elif ot.conference == conf and ot.division == intra_target:
                assert cnt == 1
                intra_rot += cnt
            elif ot.conference != conf and ot.division == inter_target:
                assert cnt == 1
                inter_rot += cnt
            elif ot.conference == conf:
                assert cnt == 1
                same_place += cnt
            elif ot.conference != conf and ot.division == extra_target:
                assert cnt == 1
                extra17 += cnt
            else:
                assert cnt == 0

        assert divisional == 6
        assert intra_rot == 4
        assert inter_rot == 4
        assert same_place == 2
        assert extra17 == 1


def test_nfl_one_tnf_one_mnf_per_week_thanksgiving_three():
    from scheduler.data import load_teams_for_league

    teams = load_teams_for_league("NFL", ".")
    config = LeagueConfig(
        name="NFL",
        games_per_team=17,
        season_start=date(2026, 9, 10),
        season_end=date(2027, 1, 10),
        seed=11,
    )
    result = optimize_schedule(teams, config)
    assert len(result.schedule) == 272

    week_anchor = config.season_start - timedelta(days=(config.season_start.weekday() - 3) % 7)
    total_weeks = _nfl_week_index(config, config.season_end) + 1
    tg = _nfl_thanksgiving(config.season_start.year)
    thu_by_week = defaultdict(int)
    mon_by_week = defaultdict(int)
    for g in result.schedule:
        w = _nfl_week_index(config, g.date)
        if g.date.weekday() == 3:
            thu_by_week[w] += 1
        elif g.date.weekday() == 0:
            mon_by_week[w] += 1

    for w in range(total_weeks):
        d_thu = week_anchor + timedelta(days=w * 7)
        d_mon = week_anchor + timedelta(days=w * 7 + 4)
        if config.season_start <= d_thu <= config.season_end:
            if d_thu == tg:
                assert thu_by_week[w] == 3
            else:
                assert thu_by_week[w] == 1
        if config.season_start <= d_mon <= config.season_end:
            assert mon_by_week[w] == 1
