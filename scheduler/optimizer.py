from __future__ import annotations

import random
from collections import defaultdict
from datetime import date, timedelta
from itertools import combinations
from typing import Dict, List, Set, Tuple

from .geo import haversine_miles, timezone_jump_hours
from .models import Game, LeagueConfig, OptimizationResult, Team, TeamState
from .nfl import (
    NFL_DIVISION_ORDER,
    NFL_PREV_RANK,
    nfl_conference_with_9_home_games,
    nfl_inter_conf_division_opponent,
    nfl_inter_conf_division_two_years_ago,
    nfl_intra_conf_pairings,
)
from .nhl import NHL_CANADIAN_FORCE_FOUR


def _regular_pair_expansion(codes: List[str], degree: int) -> List[Tuple[str, str]]:
    n = len(codes)
    if degree < 0 or degree > n - 1:
        raise ValueError(f"Invalid regular degree {degree} for {n} teams")
    if (n * degree) % 2 != 0:
        raise ValueError(f"Cannot build {degree}-regular pairing on {n} teams")

    edges: set[Tuple[str, str]] = set()
    half = degree // 2

    for i in range(n):
        for step in range(1, half + 1):
            j = (i + step) % n
            a, b = sorted((codes[i], codes[j]))
            edges.add((a, b))

    if degree % 2 == 1:
        if n % 2 != 0:
            raise ValueError(f"Odd degree {degree} requires an even number of teams, got {n}")
        for i in range(n // 2):
            j = i + (n // 2)
            a, b = sorted((codes[i], codes[j]))
            edges.add((a, b))

    return sorted(edges)


def _build_degree_k_graph(
    nodes: List[str], degree: int, forbidden_edges: Set[Tuple[str, str]], seed: int
) -> Set[Tuple[str, str]]:
    rng = random.Random(seed)
    nodes = sorted(nodes)
    forbidden = {tuple(sorted(e)) for e in forbidden_edges}

    for _ in range(180):
        rem = {n: degree for n in nodes}
        edges: Set[Tuple[str, str]] = set()

        def recurse() -> bool:
            pending = [n for n in nodes if rem[n] > 0]
            if not pending:
                return True

            pending.sort(key=lambda n: (-rem[n], n))
            u = pending[0]
            cands = [
                v
                for v in nodes
                if v != u
                and rem[v] > 0
                and tuple(sorted((u, v))) not in forbidden
                and tuple(sorted((u, v))) not in edges
            ]
            if len(cands) < rem[u]:
                return False
            rng.shuffle(cands)

            from itertools import combinations as _comb

            for chosen in _comb(cands, rem[u]):
                new_edges = [tuple(sorted((u, v))) for v in chosen]
                if any(e in edges for e in new_edges):
                    continue
                for e in new_edges:
                    edges.add(e)
                prev_u = rem[u]
                rem[u] = 0
                for v in chosen:
                    rem[v] -= 1

                feasible = True
                for n in nodes:
                    if rem[n] <= 0:
                        continue
                    avail = [
                        m
                        for m in nodes
                        if m != n
                        and rem[m] > 0
                        and tuple(sorted((n, m))) not in forbidden
                        and tuple(sorted((n, m))) not in edges
                    ]
                    if len(avail) < rem[n]:
                        feasible = False
                        break

                if feasible and recurse():
                    return True

                rem[u] = prev_u
                for v in chosen:
                    rem[v] += 1
                for e in new_edges:
                    edges.remove(e)
            return False

        if recurse():
            return edges

    raise RuntimeError(f"Could not build {degree}-regular graph for nodes={nodes}")


def build_dates(config: LeagueConfig) -> List[date]:
    current = config.season_start
    dates: List[date] = []
    nfl_bf = _nfl_black_friday(config.season_start.year) if config.name.upper() == "NFL" else None
    nfl_xmas = _nfl_christmas(config.season_start.year) if config.name.upper() == "NFL" else None
    nfl_tg = _nfl_thanksgiving(config.season_start.year) if config.name.upper() == "NFL" else None
    while current <= config.season_end:
        if config.name.upper() == "NFL":
            # NFL regular scheduling uses Sunday as the default slot.
            # Keep holiday specials available as explicit non-Sunday slots.
            if current.weekday() != 6 and current not in {nfl_tg, nfl_bf, nfl_xmas}:
                current += timedelta(days=1)
                continue
        if not (config.all_star_break.start <= current <= config.all_star_break.end) and current not in config.league_blackout_dates:
            dates.append(current)
        current += timedelta(days=1)
    return dates


def _nfl_thanksgiving(year: int) -> date:
    d = date(year, 11, 1)
    while d.weekday() != 3:
        d += timedelta(days=1)
    return d + timedelta(days=21)


def _nfl_black_friday(year: int) -> date:
    return _nfl_thanksgiving(year) + timedelta(days=1)


def _nfl_christmas(year: int) -> date:
    return date(year, 12, 25)


def _nfl_date_capacity(config: LeagueConfig, d: date) -> int | None:
    if config.name.upper() != "NFL":
        return None
    tg = _nfl_thanksgiving(config.season_start.year)
    bf = _nfl_black_friday(config.season_start.year)
    xmas = _nfl_christmas(config.season_start.year)
    if d == tg:
        return 3
    if d == bf:
        return 1
    if d == xmas:
        return 3
    if d.weekday() == 3:
        return 1
    if d.weekday() == 0:
        return 1
    if d.weekday() == 6:
        return None  # Sunday unrestricted
    return 0


def _nfl_week_index(config: LeagueConfig, d: date) -> int:
    # NFL week is anchored on Thursday (Thu..Wed).
    week_anchor = config.season_start - timedelta(days=(config.season_start.weekday() - 3) % 7)
    return (d - week_anchor).days // 7


def _violates_nfl_short_week(d: date, existing_dates: List[date], config: LeagueConfig) -> bool:
    dw = _nfl_week_index(config, d)
    dwd = d.weekday()
    for g in existing_dates:
        gw = _nfl_week_index(config, g)
        # One game per team per week.
        if gw == dw:
            return True
        # Monday (week w) -> Thursday (week w+1) not allowed.
        if g.weekday() == 0 and dwd == 3 and dw == gw + 1:
            return True
        if dwd == 0 and g.weekday() == 3 and gw == dw + 1:
            return True
    return False


def _connected_components(edges: Set[Tuple[str, str]], nodes: List[str]) -> List[List[str]]:
    adj = {n: set() for n in nodes}
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    seen = set()
    comps: List[List[str]] = []
    for n in nodes:
        if n in seen:
            continue
        stack = [n]
        comp: List[str] = []
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            comp.append(cur)
            stack.extend(v for v in adj[cur] if v not in seen)
        comps.append(comp)
    return comps


def _euler_orient_component(
    comp_nodes: List[str], edges: Set[Tuple[str, str]]
) -> Dict[Tuple[str, str], str]:
    local_adj: Dict[str, List[Tuple[str, str]]] = {n: [] for n in comp_nodes}
    for a, b in edges:
        if a in local_adj and b in local_adj:
            local_adj[a].append((a, b))
            local_adj[b].append((a, b))

    # Hierholzer traversal on undirected edges.
    edge_used: Set[Tuple[str, str]] = set()
    start = comp_nodes[0]
    stack = [start]
    edge_stack: List[Tuple[str, str]] = []
    circuit_edges: List[Tuple[str, str]] = []

    while stack:
        v = stack[-1]
        while local_adj[v] and local_adj[v][-1] in edge_used:
            local_adj[v].pop()
        if local_adj[v]:
            e = local_adj[v].pop()
            if e in edge_used:
                continue
            edge_used.add(e)
            a, b = e
            nxt = b if v == a else a
            stack.append(nxt)
            edge_stack.append((v, nxt))
        else:
            stack.pop()
            if edge_stack:
                circuit_edges.append(edge_stack.pop())

    oriented: Dict[Tuple[str, str], str] = {}
    for src, dst in circuit_edges:
        key = tuple(sorted((src, dst)))
        if key in oriented:
            continue
        oriented[key] = src  # src is the home-heavy side for 3-game pair
    return oriented


def _build_three_game_pairs(conference_teams: List[Team], seed: int) -> Set[Tuple[str, str]]:
    rng = random.Random(seed)
    codes = [t.code for t in conference_teams]
    division = {t.code: t.division for t in conference_teams}
    target_degree = 4

    allowed: Dict[str, Set[str]] = {c: set() for c in codes}
    for a, b in combinations(codes, 2):
        if division[a] != division[b]:
            allowed[a].add(b)
            allowed[b].add(a)

    for _ in range(250):
        rem = {c: target_degree for c in codes}
        edges: Set[Tuple[str, str]] = set()

        def recurse() -> bool:
            open_nodes = [c for c in codes if rem[c] > 0]
            if not open_nodes:
                return True

            open_nodes.sort(key=lambda c: (rem[c], len([n for n in allowed[c] if rem[n] > 0])))
            u = open_nodes[0]
            candidates = [n for n in allowed[u] if rem[n] > 0 and tuple(sorted((u, n))) not in edges]
            if len(candidates) < rem[u]:
                return False

            rng.shuffle(candidates)

            from itertools import combinations as _comb

            for chosen in _comb(candidates, rem[u]):
                trial_edges = [tuple(sorted((u, v))) for v in chosen]
                if any(e in edges for e in trial_edges):
                    continue
                if any(rem[v] <= 0 for v in chosen):
                    continue

                for e in trial_edges:
                    edges.add(e)
                prev_u = rem[u]
                rem[u] = 0
                for v in chosen:
                    rem[v] -= 1

                feasible = True
                for c in codes:
                    avail = [n for n in allowed[c] if rem[n] > 0 and tuple(sorted((c, n))) not in edges]
                    if rem[c] > len(avail):
                        feasible = False
                        break
                if feasible and recurse():
                    return True

                rem[u] = prev_u
                for v in chosen:
                    rem[v] += 1
                for e in trial_edges:
                    edges.remove(e)
            return False

        if recurse():
            return edges

    raise RuntimeError("Could not construct 3-game rotation pairs for conference.")


def _build_nba_pair_matrix(teams: List[Team], seed: int) -> Tuple[Dict[Tuple[str, str], int], Dict[Tuple[str, str], str]]:
    pair_counts: Dict[Tuple[str, str], int] = {}
    home_heavy: Dict[Tuple[str, str], str] = {}
    team_map = {t.code: t for t in teams}
    codes = sorted(team_map.keys())

    conferences: Dict[str, List[Team]] = defaultdict(list)
    for t in teams:
        conferences[t.conference].append(t)

    three_game_pairs: Set[Tuple[str, str]] = set()
    for i, conf in enumerate(sorted(conferences.keys())):
        conf_teams = sorted(conferences[conf], key=lambda t: t.code)
        three_game_pairs |= _build_three_game_pairs(conf_teams, seed + i * 997)

    for a, b in combinations(codes, 2):
        ta, tb = team_map[a], team_map[b]
        key = (a, b)
        if ta.conference != tb.conference:
            pair_counts[key] = 2
        elif ta.division == tb.division:
            pair_counts[key] = 4
        else:
            pair_counts[key] = 3 if key in three_game_pairs else 4

    # Orient odd pairs so each team has balanced home/away (2 home-heavy, 2 away-heavy among 3-game pairs).
    odd_pairs = {k for k, v in pair_counts.items() if v % 2 == 1}
    for conf in sorted(conferences.keys()):
        conf_codes = [t.code for t in conferences[conf]]
        conf_odd = {p for p in odd_pairs if p[0] in conf_codes and p[1] in conf_codes}
        comps = _connected_components(conf_odd, conf_codes)
        for comp in comps:
            comp_edges = {e for e in conf_odd if e[0] in comp and e[1] in comp}
            oriented = _euler_orient_component(comp, comp_edges)
            home_heavy.update(oriented)

    return pair_counts, home_heavy


def _build_nhl_pair_matrix(
    teams: List[Team], seed: int
) -> Tuple[Dict[Tuple[str, str], int], Dict[Tuple[str, str], str]]:
    team_map = {t.code: t for t in teams}
    codes = sorted(team_map.keys())
    pair_counts: Dict[Tuple[str, str], int] = {}

    conferences: Dict[str, List[Team]] = defaultdict(list)
    divisions: Dict[str, List[Team]] = defaultdict(list)
    for t in teams:
        conferences[t.conference].append(t)
        divisions[f"{t.conference}:{t.division}"].append(t)

    # Baseline: non-division in-conference = 3, inter-conference = 2
    for a, b in combinations(codes, 2):
        ta, tb = team_map[a], team_map[b]
        key = (a, b)
        if ta.conference != tb.conference:
            pair_counts[key] = 2
        elif ta.division != tb.division:
            pair_counts[key] = 3

    # Within each division: 4 games x 5 opponents + 3 games x 2 opponents.
    three_game_division_pairs: Set[Tuple[str, str]] = set()
    for i, div_key in enumerate(sorted(divisions.keys())):
        div_codes = sorted(t.code for t in divisions[div_key])
        forbidden = {
            tuple(sorted(e))
            for e in NHL_CANADIAN_FORCE_FOUR
            if e[0] in div_codes and e[1] in div_codes
        }
        # Each team has exactly two 3-game division opponents -> degree 2 graph.
        degree2_edges = _build_degree_k_graph(div_codes, degree=2, forbidden_edges=forbidden, seed=seed + i * 811)
        three_game_division_pairs |= degree2_edges

    for a, b in combinations(codes, 2):
        ta, tb = team_map[a], team_map[b]
        if ta.conference == tb.conference and ta.division == tb.division:
            key = (a, b)
            pair_counts[key] = 3 if key in three_game_division_pairs else 4

    odd_pairs = {k for k, v in pair_counts.items() if v % 2 == 1}
    home_heavy: Dict[Tuple[str, str], str] = {}
    for conf in sorted(conferences.keys()):
        conf_codes = [t.code for t in conferences[conf]]
        conf_odd = {p for p in odd_pairs if p[0] in conf_codes and p[1] in conf_codes}
        comps = _connected_components(conf_odd, conf_codes)
        for comp in comps:
            comp_edges = {e for e in conf_odd if e[0] in comp and e[1] in comp}
            if comp_edges:
                home_heavy.update(_euler_orient_component(comp, comp_edges))

    return pair_counts, home_heavy


def _ordered_by_rank(codes: List[str]) -> List[str]:
    return sorted(codes, key=lambda c: (NFL_PREV_RANK.get(c, 99), c))


def _cycle_oriented_edges(nodes: List[str], undirected_edges: Set[Tuple[str, str]], reverse: bool = False) -> List[Tuple[str, str]]:
    adj: Dict[str, List[str]] = {n: [] for n in nodes}
    for a, b in undirected_edges:
        adj[a].append(b)
        adj[b].append(a)
    start = sorted(nodes)[0]
    order = [start]
    prev = None
    cur = start
    while True:
        nxt_candidates = [n for n in adj[cur] if n != prev]
        if not nxt_candidates:
            break
        nxt = sorted(nxt_candidates)[0]
        if nxt == start:
            break
        order.append(nxt)
        prev, cur = cur, nxt
        if len(order) > len(nodes):
            break
    if reverse:
        order = list(reversed(order))
    oriented: List[Tuple[str, str]] = []
    for i in range(len(order)):
        oriented.append((order[i], order[(i + 1) % len(order)]))
    return oriented


def _build_nfl_matchups(teams: List[Team], season_year: int, seed: int) -> List[Tuple[str, str]]:
    by_conf_div: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
    for t in teams:
        by_conf_div[t.conference][t.division].append(t.code)
    for conf in by_conf_div:
        for div in by_conf_div[conf]:
            by_conf_div[conf][div] = _ordered_by_rank(by_conf_div[conf][div])

    directed: List[Tuple[str, str]] = []

    # 1) Six divisional games (home/away split).
    for conf in ["AFC", "NFC"]:
        for div in NFL_DIVISION_ORDER:
            codes = by_conf_div[conf][div]
            for a, b in combinations(codes, 2):
                directed.append((a, b))
                directed.append((b, a))

    # 2) Intra-conference division rotation (4 games, 2H/2A).
    for conf in ["AFC", "NFC"]:
        for div_a, div_b in nfl_intra_conf_pairings(season_year):
            a_codes = by_conf_div[conf][div_a]
            b_codes = by_conf_div[conf][div_b]
            for i, a in enumerate(a_codes):
                for j, b in enumerate(b_codes):
                    if (i + j + season_year) % 2 == 0:
                        directed.append((a, b))
                    else:
                        directed.append((b, a))

    # 3) Inter-conference division rotation (4 games, 2H/2A).
    for afc_div in NFL_DIVISION_ORDER:
        nfc_div = nfl_inter_conf_division_opponent(afc_div, season_year)
        a_codes = by_conf_div["AFC"][afc_div]
        n_codes = by_conf_div["NFC"][nfc_div]
        for i, a in enumerate(a_codes):
            for j, n in enumerate(n_codes):
                if (i + j + season_year + 1) % 2 == 0:
                    directed.append((a, n))
                else:
                    directed.append((n, a))

    # 4) Same-place games vs remaining two divisions in conference (1H/1A per team).
    intra_pairs = nfl_intra_conf_pairings(season_year)
    paired = {k: v for a, b in intra_pairs for k, v in ((a, b), (b, a))}
    for conf in ["AFC", "NFC"]:
        # Build the remaining-division cycle graph after removing paired edges.
        rem_edges: Set[Tuple[str, str]] = set()
        for a, b in combinations(NFL_DIVISION_ORDER, 2):
            if paired.get(a) == b:
                continue
            rem_edges.add(tuple(sorted((a, b))))
        oriented = _cycle_oriented_edges(NFL_DIVISION_ORDER, rem_edges, reverse=(season_year % 2 == 0))
        for home_div, away_div in oriented:
            home_codes = by_conf_div[conf][home_div]
            away_codes = by_conf_div[conf][away_div]
            for rank in range(4):
                directed.append((home_codes[rank], away_codes[rank]))

    # 5) The 17th game: non-conference same-rank from division played 2 years ago.
    extra_home_conf = nfl_conference_with_9_home_games(season_year)
    for afc_div in NFL_DIVISION_ORDER:
        nfc_div = nfl_inter_conf_division_two_years_ago(afc_div, season_year)
        a_codes = by_conf_div["AFC"][afc_div]
        n_codes = by_conf_div["NFC"][nfc_div]
        for rank in range(4):
            a = a_codes[rank]
            n = n_codes[rank]
            if extra_home_conf == "AFC":
                directed.append((a, n))
            else:
                directed.append((n, a))

    # Sanity checks.
    home = defaultdict(int)
    away = defaultdict(int)
    for h, a in directed:
        home[h] += 1
        away[a] += 1

    target_home_afc = 9 if nfl_conference_with_9_home_games(season_year) == "AFC" else 8
    target_home_nfc = 9 if nfl_conference_with_9_home_games(season_year) == "NFC" else 8
    team_map = {t.code: t for t in teams}
    for t in teams:
        if home[t.code] != (target_home_afc if team_map[t.code].conference == "AFC" else target_home_nfc):
            raise RuntimeError(f"NFL home split mismatch for {t.code}: {home[t.code]}")
        if home[t.code] + away[t.code] != 17:
            raise RuntimeError(f"NFL game count mismatch for {t.code}: {home[t.code] + away[t.code]}")

    rng = random.Random(seed)
    rng.shuffle(directed)
    return directed


def build_matchups(teams: List[Team], config: LeagueConfig) -> List[Tuple[str, str]]:
    if config.name.upper() == "NFL" and len(teams) == 32 and config.games_per_team == 17:
        return _build_nfl_matchups(teams, config.season_start.year, config.seed)
    if config.name.upper() == "NBA" and len(teams) == 30 and config.games_per_team == 82:
        pair_counts, home_heavy = _build_nba_pair_matrix(teams, config.seed)
    elif config.name.upper() == "NHL" and len(teams) == 32 and config.games_per_team == 82:
        pair_counts, home_heavy = _build_nhl_pair_matrix(teams, config.seed)
    else:
        n = len(teams)
        if config.games_per_team % 2 != 0:
            raise ValueError("games_per_team must be even to keep home/away balanced.")
        baseline = 2 * (n - 1)
        if config.games_per_team < baseline:
            raise ValueError(f"games_per_team must be >= {baseline} for {n} teams.")
        extra_per_team = config.games_per_team - baseline
        if extra_per_team % 2 != 0:
            raise ValueError("games_per_team must produce an even extra match count per team.")
        extra_pair_degree = extra_per_team // 2
        pair_counts = defaultdict(int)
        for a, b in combinations(sorted(t.code for t in teams), 2):
            pair_counts[(a, b)] = 2
        if extra_pair_degree > 0:
            expansion_pairs = _regular_pair_expansion(sorted(t.code for t in teams), extra_pair_degree)
            for a, b in expansion_pairs:
                pair_counts[(a, b)] += 2
        home_heavy = {}

    directed: List[Tuple[str, str]] = []
    home_counts = defaultdict(int)
    away_counts = defaultdict(int)

    for (a, b), total in pair_counts.items():
        if total % 2 == 0:
            home_each = total // 2
            directed.extend([(a, b)] * home_each)
            directed.extend([(b, a)] * home_each)
            home_counts[a] += home_each
            home_counts[b] += home_each
            away_counts[a] += home_each
            away_counts[b] += home_each
        else:
            heavy = home_heavy.get((a, b), a)
            light = b if heavy == a else a
            directed.extend([(heavy, light)] * ((total + 1) // 2))
            directed.extend([(light, heavy)] * ((total - 1) // 2))
            home_counts[heavy] += (total + 1) // 2
            away_counts[heavy] += (total - 1) // 2
            home_counts[light] += (total - 1) // 2
            away_counts[light] += (total + 1) // 2

    for t in teams:
        if home_counts[t.code] != away_counts[t.code]:
            raise RuntimeError(f"Home/away imbalance for {t.code}: {home_counts[t.code]} vs {away_counts[t.code]}")

    rng = random.Random(config.seed)
    rng.shuffle(directed)
    return directed


def _window_3_in_4(game_dates: List[date], new_date: date) -> int:
    merged = sorted(game_dates + [new_date])
    count = 0
    for i in range(len(merged)):
        j = i
        while j < len(merged) and (merged[j] - merged[i]).days <= 3:
            j += 1
        if j - i >= 3:
            count += 1
    return count


def _count_back_to_backs(game_dates: List[date]) -> int:
    if len(game_dates) < 2:
        return 0
    dates = sorted(game_dates)
    return sum(1 for i in range(1, len(dates)) if (dates[i] - dates[i - 1]).days == 1)


def _max_consecutive_game_days(game_dates: List[date]) -> int:
    if not game_dates:
        return 0
    ordered = sorted(set(game_dates))
    best = 1
    run = 1
    for i in range(1, len(ordered)):
        if (ordered[i] - ordered[i - 1]).days == 1:
            run += 1
        else:
            run = 1
        best = max(best, run)
    return best


def _target_back_to_backs(config: LeagueConfig) -> float:
    if config.name.upper() == "NFL":
        return 0.0
    # Anchor to ~15 B2B for an 82-game season and scale proportionally.
    return 15.0 * (config.games_per_team / 82.0)


def _feasible(team_games: List[Game], d: date, max_b2b: int, max_3in4: int) -> bool:
    if any(g.date == d for g in team_games):
        return False

    dates = sorted(g.date for g in team_games)
    b2b = _count_back_to_backs(dates + [d])
    if b2b > max_b2b:
        return False

    three_in_four = _window_3_in_4(dates, d)
    if three_in_four > max_3in4:
        return False

    if _max_consecutive_game_days(dates + [d]) >= 3:
        return False

    return True


def _constraint_overflows(
    team_games: List[Game], d: date, max_b2b: int, max_3in4: int
) -> Tuple[int, int]:
    dates = sorted(g.date for g in team_games)
    b2b_over = max(0, _count_back_to_backs(dates + [d]) - max_b2b)
    three_over = max(0, _window_3_in_4(dates, d) - max_3in4)
    return b2b_over, three_over


def _emissions_for_distance(
    dist: float, config: LeagueConfig, flight_factor_override: float | None = None
) -> float:
    flight_factor = flight_factor_override or config.flight_emissions_kg_per_mile
    factor = (
        config.ground_emissions_kg_per_mile
        if dist <= config.close_range_miles
        else flight_factor
    )
    return dist * factor


def _previous_context(
    team_code: str,
    d: date,
    team_games: List[Game],
    team_map: Dict[str, Team],
    season_start: date,
) -> Tuple[Tuple[float, float, str], int]:
    prior = [g for g in team_games if g.date < d]
    if not prior:
        t = team_map[team_code]
        anchor_date = season_start - timedelta(days=4)
        return (t.latitude, t.longitude, t.timezone), (d - anchor_date).days

    prev = max(prior, key=lambda g: g.date)
    venue_team = team_map[prev.home]
    return (
        (venue_team.latitude, venue_team.longitude, venue_team.timezone),
        (d - prev.date).days,
    )


def _count_three_in_four_windows(dates: List[date]) -> int:
    if len(dates) < 3:
        return 0
    ordered = sorted(dates)
    count = 0
    for i in range(len(ordered)):
        j = i
        while j < len(ordered) and (ordered[j] - ordered[i]).days <= 3:
            j += 1
        if j - i >= 3:
            count += 1
    return count


def _recompute_team_states(
    schedule: List[Game], teams: List[Team], config: LeagueConfig
) -> Dict[str, TeamState]:
    team_map = {t.code: t for t in teams}
    team_states: Dict[str, TeamState] = {t.code: TeamState() for t in teams}

    for g in sorted(schedule, key=lambda x: x.date):
        team_states[g.home].games.append(g)
        team_states[g.away].games.append(g)

    for team_code, state in team_states.items():
        state.games.sort(key=lambda g: g.date)
        home = team_map[team_code]
        last_loc = (home.latitude, home.longitude, home.timezone)
        last_date = config.season_start - timedelta(days=4)

        for g in state.games:
            dest_team = team_map[g.home]
            dist = haversine_miles(last_loc[0], last_loc[1], dest_team.latitude, dest_team.longitude)
            state.total_distance_miles += dist
            state.total_emissions_kg += _emissions_for_distance(
                dist,
                config,
                flight_factor_override=home.flight_emissions_kg_per_mile,
            )
            state.timezone_jumps += timezone_jump_hours(last_loc[2], dest_team.timezone)

            if (g.date - last_date).days == 1:
                state.back_to_backs += 1

            last_loc = (dest_team.latitude, dest_team.longitude, dest_team.timezone)
            last_date = g.date

        state.three_in_four = _count_three_in_four_windows([g.date for g in state.games])

    return team_states


def _finalize_result_from_schedule(
    schedule: List[Game], teams: List[Team], config: LeagueConfig
) -> OptimizationResult:
    schedule.sort(key=lambda g: g.date)
    schedule = [
        Game(
            game_id=f"G{i:04d}",
            date=g.date,
            home=g.home,
            away=g.away,
            venue=g.venue,
            neutral_site=g.neutral_site,
        )
        for i, g in enumerate(schedule, start=1)
    ]
    team_states = _recompute_team_states(schedule, teams, config)

    league_distance = sum(state.total_distance_miles for state in team_states.values())
    league_emissions = sum(state.total_emissions_kg for state in team_states.values())

    travel_values = [s.total_distance_miles for s in team_states.values()]
    target_b2b = _target_back_to_backs(config)
    rest_imbalance = [abs(s.back_to_backs - target_b2b) for s in team_states.values()]

    avg_travel = sum(travel_values) / len(travel_values)
    travel_var = sum((x - avg_travel) ** 2 for x in travel_values) / len(travel_values)
    avg_rest_imbalance = sum(rest_imbalance) / len(rest_imbalance)

    fairness_raw = 1.0 / (1.0 + (travel_var / 150_000_000.0) + (avg_rest_imbalance / 10.0))
    fairness_score = max(0.0, min(100.0, fairness_raw * 100.0))

    emissions_per_game = league_emissions / max(1, len(schedule))
    sustainability_raw = 1.0 / (1.0 + (emissions_per_game / 30_000.0))
    sustainability_score = max(0.0, min(100.0, sustainability_raw * 100.0))

    objective_value = (
        config.travel_weight * league_emissions
        + config.fairness_weight * (100.0 - fairness_score) * 10_000
        + config.density_weight * sum(abs(s.back_to_backs - target_b2b) for s in team_states.values()) * 850
    )

    diagnostics = {
        "total_games": float(len(schedule)),
        "avg_emissions_per_game": emissions_per_game,
        "avg_distance_per_team": avg_travel,
        "max_team_distance": max(travel_values),
        "min_team_distance": min(travel_values),
        "avg_back_to_backs": sum(s.back_to_backs for s in team_states.values()) / len(team_states),
        "target_back_to_backs": float(target_b2b),
        "avg_time_zone_jumps": sum(s.timezone_jumps for s in team_states.values()) / len(team_states),
    }

    return OptimizationResult(
        schedule=schedule,
        team_states=team_states,
        league_emissions_kg=league_emissions,
        league_distance_miles=league_distance,
        fairness_score=fairness_score,
        sustainability_score=sustainability_score,
        objective_value=objective_value,
        diagnostics=diagnostics,
    )


def _optimize_nfl_weekly(teams: List[Team], config: LeagueConfig) -> OptimizationResult:
    team_codes = [t.code for t in teams]
    week_anchor = config.season_start - timedelta(days=(config.season_start.weekday() - 3) % 7)
    total_weeks = _nfl_week_index(config, config.season_end) + 1
    sunday_by_week: Dict[int, date] = {
        w: week_anchor + timedelta(days=w * 7 + 3) for w in range(total_weeks)
    }
    tg = _nfl_thanksgiving(config.season_start.year)
    bf = _nfl_black_friday(config.season_start.year)
    xmas = _nfl_christmas(config.season_start.year)

    base_matchups = build_matchups(teams, config)
    max_attempts = 80
    for enforce_holidays in (True, False):
        for attempt in range(max_attempts):
            rng = random.Random(config.seed + attempt * 17 + (0 if enforce_holidays else 10_000))
            unscheduled = list(base_matchups)
            occupied: Dict[int, Set[str]] = {w: set() for w in range(total_weeks)}
            team_game_count: Dict[str, int] = {t: 0 for t in team_codes}
            schedule: List[Game] = []

            def _add_game(d: date, home: str, away: str, venue: str | None = None, neutral: str | None = None) -> bool:
                w = _nfl_week_index(config, d)
                if w < 0 or w >= total_weeks:
                    return False
                if home in occupied[w] or away in occupied[w]:
                    return False
                if _violates_nfl_short_week(d, [g.date for g in schedule if g.home == home or g.away == home], config):
                    return False
                if _violates_nfl_short_week(d, [g.date for g in schedule if g.home == away or g.away == away], config):
                    return False
                if team_game_count[home] >= config.games_per_team or team_game_count[away] >= config.games_per_team:
                    return False
                schedule.append(
                    Game(
                        game_id="TMP",
                        date=d,
                        home=home,
                        away=away,
                        venue=venue or home,
                        neutral_site=neutral,
                    )
                )
                occupied[w].add(home)
                occupied[w].add(away)
                team_game_count[home] += 1
                team_game_count[away] += 1
                if (home, away) in unscheduled:
                    unscheduled.remove((home, away))
                return True

            def _pick(d: date, must_home: str | None = None, avoid_away: Set[str] | None = None) -> Tuple[str, str] | None:
                avoid_away = avoid_away or set()
                cands = list(unscheduled)
                rng.shuffle(cands)
                for h, a in cands:
                    if must_home and h != must_home:
                        continue
                    if a in avoid_away:
                        continue
                    if _add_game(d, h, a):
                        return (h, a)
                return None

            # Presets first.
            ok = True
            for preset in config.preset_games:
                if not _add_game(preset.date, preset.home, preset.away, preset.venue, preset.neutral_site):
                    ok = False
                    break
            if not ok:
                continue

            if enforce_holidays:
                if _pick(tg, must_home="DET", avoid_away={"DAL"}) is None:
                    continue
                if _pick(tg, must_home="DAL", avoid_away={"DET"}) is None:
                    continue
                if _pick(tg) is None:
                    continue
                if _pick(bf) is None:
                    continue
                if _pick(xmas) is None or _pick(xmas) is None or _pick(xmas) is None:
                    continue

            # Weekly fill: one TNF (Thu) and one MNF (Mon) per NFL week, then Sundays.
            # Thanksgiving Thursday already has three games when enforce_holidays is True.
            failed = False
            week_order = list(range(total_weeks))
            for week_pos, w in enumerate(week_order):
                d_thu = week_anchor + timedelta(days=w * 7)
                d_mon = week_anchor + timedelta(days=w * 7 + 4)
                d = sunday_by_week[w]

                if enforce_holidays and d_thu == tg:
                    pass
                elif config.season_start <= d_thu <= config.season_end:
                    if _pick(d_thu) is None:
                        failed = True
                        break

                if config.season_start <= d_mon <= config.season_end:
                    if _pick(d_mon) is None:
                        failed = True
                        break

                if not (config.season_start <= d <= config.season_end):
                    for t in team_codes:
                        remaining_games = config.games_per_team - team_game_count[t]
                        remaining_weeks = sum(
                            1 for ww in week_order[week_pos + 1 :] if t not in occupied[ww]
                        )
                        if remaining_games > remaining_weeks:
                            failed = True
                            break
                    if failed:
                        break
                    continue

                free = set(t for t in team_codes if t not in occupied[w] and team_game_count[t] < config.games_per_team)
                if len(free) < 2:
                    continue

                cands = [(h, a) for h, a in unscheduled if h in free and a in free]
                best_pick: List[Tuple[str, str]] = []
                # Try multiple randomized greedy matchings and keep the fullest week.
                for _ in range(24):
                    trial_free = set(free)
                    trial_cands = list(cands)
                    rng.shuffle(trial_cands)
                    picked: List[Tuple[str, str]] = []
                    for h, a in trial_cands:
                        if h in trial_free and a in trial_free:
                            picked.append((h, a))
                            trial_free.remove(h)
                            trial_free.remove(a)
                    if len(picked) > len(best_pick):
                        best_pick = picked
                    if len(best_pick) == len(free) // 2:
                        break

                for h, a in best_pick:
                    _add_game(d, h, a)

                # Forward feasibility check.
                for t in team_codes:
                    remaining_games = config.games_per_team - team_game_count[t]
                    remaining_weeks = sum(
                        1 for ww in week_order[week_pos + 1 :] if t not in occupied[ww]
                    )
                    if remaining_games > remaining_weeks:
                        failed = True
                        break
                if failed:
                    break
            if failed:
                continue

            if unscheduled:
                continue
            if any(team_game_count[t] != config.games_per_team for t in team_codes):
                continue

            return _finalize_result_from_schedule(schedule, teams, config)

    raise RuntimeError("Unable to build a feasible NFL weekly schedule with hard weekly constraints.")


def optimize_schedule(teams: List[Team], config: LeagueConfig) -> OptimizationResult:
    if config.name.upper() == "NFL":
        return _optimize_nfl_weekly(teams, config)

    rng = random.Random(config.seed)
    dates = build_dates(config)
    matchups = build_matchups(teams, config)
    team_map = {t.code: t for t in teams}

    schedule: List[Game] = []
    team_states: Dict[str, TeamState] = {t.code: TeamState() for t in teams}

    venue_usage = defaultdict(set)
    date_usage = defaultdict(int)
    nfl_monday_games = defaultdict(int)
    nfl_thursday_games = defaultdict(int)
    nfl_team_weeks: Dict[str, Set[int]] = defaultdict(set)

    game_counter = 1
    unscheduled = list(matchups)

    # Seed fixed-date games (e.g., international games) before greedy fill.
    for preset in config.preset_games:
        if (preset.home, preset.away) in unscheduled:
            unscheduled.remove((preset.home, preset.away))
        schedule.append(preset)
        date_usage[preset.date] += 1
        venue_usage[preset.home].add(preset.date)
        team_states[preset.home].games.append(preset)
        team_states[preset.away].games.append(preset)
        if config.name.upper() == "NFL":
            w = _nfl_week_index(config, preset.date)
            nfl_team_weeks[preset.home].add(w)
            nfl_team_weeks[preset.away].add(w)
            if preset.date.weekday() == 0:
                nfl_monday_games[preset.home] += 1
                nfl_monday_games[preset.away] += 1
            if preset.date.weekday() == 3:
                nfl_thursday_games[preset.home] += 1
                nfl_thursday_games[preset.away] += 1
        game_counter = max(game_counter, int(preset.game_id[1:]) + 1 if preset.game_id.startswith("G") else game_counter)

    if config.name.upper() == "NFL":
        tg = _nfl_thanksgiving(config.season_start.year)
        bf = _nfl_black_friday(config.season_start.year)
        xmas = _nfl_christmas(config.season_start.year)

        def _pick_seeded_matchup(
            target_date: date,
            must_home: str | None = None,
            avoid_away: set[str] | None = None,
        ) -> Tuple[str, str] | None:
            avoid_away = avoid_away or set()
            for h, a in list(unscheduled):
                if must_home and h != must_home:
                    continue
                if a in avoid_away:
                    continue
                if date_usage[target_date] >= (_nfl_date_capacity(config, target_date) or 0):
                    break
                if any(g.date == target_date for g in team_states[h].games) or any(g.date == target_date for g in team_states[a].games):
                    continue
                if _violates_nfl_short_week(
                    target_date, [g.date for g in team_states[h].games], config
                ):
                    continue
                if _violates_nfl_short_week(
                    target_date, [g.date for g in team_states[a].games], config
                ):
                    continue
                return (h, a)
            return None

        # Mandatory holiday slots.
        mandatory_slots: List[Tuple[date, str | None, set[str]]] = []
        mandatory_slots.extend([(tg, "DET", {"DAL"}), (tg, "DAL", {"DET"}), (tg, None, set())])
        if bf in dates:
            mandatory_slots.append((bf, None, set()))
        if xmas in dates:
            mandatory_slots.extend([(xmas, None, set()), (xmas, None, set()), (xmas, None, set())])

        for slot_date, must_home, avoid_away in mandatory_slots:
            cap = _nfl_date_capacity(config, slot_date)
            if cap is not None and date_usage[slot_date] >= cap:
                continue
            picked = _pick_seeded_matchup(slot_date, must_home=must_home, avoid_away=avoid_away)
            if not picked:
                continue
            home, away = picked
            game = Game(
                game_id=f"G{game_counter:04d}",
                date=slot_date,
                home=home,
                away=away,
                venue=home,
            )
            game_counter += 1
            schedule.append(game)
            unscheduled.remove((home, away))
            date_usage[slot_date] += 1
            venue_usage[home].add(slot_date)
            team_states[home].games.append(game)
            team_states[away].games.append(game)
            w = _nfl_week_index(config, slot_date)
            nfl_team_weeks[home].add(w)
            nfl_team_weeks[away].add(w)
            if slot_date.weekday() == 0:
                nfl_monday_games[home] += 1
                nfl_monday_games[away] += 1
            if slot_date.weekday() == 3:
                nfl_thursday_games[home] += 1
                nfl_thursday_games[away] += 1

    for home, away in unscheduled:
        strict_candidates: List[Tuple[float, date]] = []
        relaxed_candidates: List[Tuple[float, date]] = []
        home_state = team_states[home]
        away_state = team_states[away]

        valid_dates = dates[:]
        rng.shuffle(valid_dates)

        for d in valid_dates:
            if config.name.upper() == "NFL":
                cap = _nfl_date_capacity(config, d)
                if cap == 0:
                    continue
                if cap is not None and date_usage[d] >= cap:
                    continue
                week_idx = _nfl_week_index(config, d)
                if week_idx in nfl_team_weeks[home] or week_idx in nfl_team_weeks[away]:
                    continue
            if d in venue_usage[home]:
                continue
            if d in config.venue_blocks.get(home, set()):
                continue

            if any(g.date == d for g in home_state.games) or any(g.date == d for g in away_state.games):
                continue
            if d in config.team_blackout_dates.get(home, set()):
                continue
            if d in config.team_blackout_dates.get(away, set()):
                continue

            home_dates = [g.date for g in home_state.games]
            away_dates = [g.date for g in away_state.games]
            if config.name.upper() == "NFL":
                if _violates_nfl_short_week(d, home_dates, config):
                    continue
                if _violates_nfl_short_week(d, away_dates, config):
                    continue

            # Hard rule: never allow 3 straight game-days for any team.
            if _max_consecutive_game_days(home_dates + [d]) >= 3:
                continue
            if _max_consecutive_game_days(away_dates + [d]) >= 3:
                continue

            h_team = team_map[home]
            venue_coords = (h_team.latitude, h_team.longitude, h_team.timezone)
            away_prev_loc, away_rest = _previous_context(
                away, d, away_state.games, team_map, config.season_start
            )
            home_prev_loc, home_rest = _previous_context(
                home, d, home_state.games, team_map, config.season_start
            )

            away_dist = haversine_miles(
                away_prev_loc[0],
                away_prev_loc[1],
                venue_coords[0],
                venue_coords[1],
            )
            home_dist = haversine_miles(
                home_prev_loc[0],
                home_prev_loc[1],
                venue_coords[0],
                venue_coords[1],
            )

            home_emissions = _emissions_for_distance(
                home_dist, config, flight_factor_override=h_team.flight_emissions_kg_per_mile
            )
            away_emissions = _emissions_for_distance(
                away_dist, config, flight_factor_override=team_map[away].flight_emissions_kg_per_mile
            )
            travel_component = away_emissions + home_emissions

            fairness_component = abs(home_rest - away_rest)

            target_b2b = _target_back_to_backs(config)
            home_b2b_after = _count_back_to_backs(home_dates + [d])
            away_b2b_after = _count_back_to_backs(away_dates + [d])
            home_games_after = len(home_dates) + 1
            away_games_after = len(away_dates) + 1
            home_expected_b2b = target_b2b * (home_games_after / max(1.0, float(config.games_per_team)))
            away_expected_b2b = target_b2b * (away_games_after / max(1.0, float(config.games_per_team)))
            density_component = abs(home_b2b_after - home_expected_b2b) + abs(
                away_b2b_after - away_expected_b2b
            )

            objective = (
                config.travel_weight * travel_component
                + config.fairness_weight * fairness_component * 100.0
                + config.density_weight * density_component * 260.0
            )
            if config.name.upper() == "NFL":
                short_week_penalty = 0.0
                if d.weekday() == 0 and (
                    nfl_monday_games[home] >= 2 or nfl_monday_games[away] >= 2
                ):
                    short_week_penalty += 120_000.0
                if d.weekday() == 3 and (
                    nfl_thursday_games[home] >= 2 or nfl_thursday_games[away] >= 2
                ):
                    short_week_penalty += 120_000.0
                objective += short_week_penalty
                strict_candidates.append((objective, d))
            else:
                home_b2b_over, home_3in4_over = _constraint_overflows(
                    home_state.games, d, config.max_back_to_backs, config.max_three_in_four
                )
                away_b2b_over, away_3in4_over = _constraint_overflows(
                    away_state.games, d, config.max_back_to_backs, config.max_three_in_four
                )
                total_b2b_over = home_b2b_over + away_b2b_over
                total_3in4_over = home_3in4_over + away_3in4_over
                total_over = total_b2b_over + total_3in4_over

                if total_over == 0:
                    strict_candidates.append((objective, d))
                else:
                    # Keep feasibility by allowing only small overflow when needed.
                    overflow_penalty = (total_b2b_over * 200_000.0) + (total_3in4_over * 120_000.0)
                    relaxed_candidates.append((objective + overflow_penalty, d))

        if strict_candidates:
            strict_candidates.sort(key=lambda x: x[0])
            chosen_date = strict_candidates[0][1]
        elif relaxed_candidates:
            relaxed_candidates.sort(key=lambda x: x[0])
            chosen_date = relaxed_candidates[0][1]
        else:
            if config.name.upper() == "NFL":
                nfl_fallback: List[Tuple[float, date]] = []
                tg = _nfl_thanksgiving(config.season_start.year)
                bf = _nfl_black_friday(config.season_start.year)
                xmas = _nfl_christmas(config.season_start.year)
                for d in valid_dates:
                    cap = _nfl_date_capacity(config, d)
                    if cap == 0:
                        continue
                    # Keep special-day quotas strict.
                    if d in {tg, bf, xmas} and cap is not None and date_usage[d] >= cap:
                        continue
                    week_idx = _nfl_week_index(config, d)
                    if week_idx in nfl_team_weeks[home] or week_idx in nfl_team_weeks[away]:
                        continue
                    if d in venue_usage[home]:
                        continue
                    if d in config.venue_blocks.get(home, set()):
                        continue
                    if any(g.date == d for g in home_state.games) or any(g.date == d for g in away_state.games):
                        continue
                    if d in config.team_blackout_dates.get(home, set()) or d in config.team_blackout_dates.get(away, set()):
                        continue
                    home_dates = [g.date for g in home_state.games]
                    away_dates = [g.date for g in away_state.games]
                    if _violates_nfl_short_week(d, home_dates, config):
                        continue
                    if _violates_nfl_short_week(d, away_dates, config):
                        continue
                    h_team = team_map[home]
                    venue_coords = (h_team.latitude, h_team.longitude, h_team.timezone)
                    away_prev_loc, away_rest = _previous_context(away, d, away_state.games, team_map, config.season_start)
                    home_prev_loc, home_rest = _previous_context(home, d, home_state.games, team_map, config.season_start)
                    away_dist = haversine_miles(away_prev_loc[0], away_prev_loc[1], venue_coords[0], venue_coords[1])
                    home_dist = haversine_miles(home_prev_loc[0], home_prev_loc[1], venue_coords[0], venue_coords[1])
                    travel_component = _emissions_for_distance(home_dist, config, h_team.flight_emissions_kg_per_mile) + _emissions_for_distance(
                        away_dist, config, team_map[away].flight_emissions_kg_per_mile
                    )
                    fairness_component = abs(home_rest - away_rest)
                    objective = config.travel_weight * travel_component + config.fairness_weight * fairness_component * 100.0
                    if cap is not None and date_usage[d] >= cap:
                        overflow_factor = 200_000.0
                        if d.weekday() == 0:
                            overflow_factor = 2_000_000.0
                        elif d.weekday() == 3 and d != tg:
                            overflow_factor = 2_000_000.0
                        objective += (date_usage[d] - cap + 1) * overflow_factor
                    if d.weekday() == 0 and (
                        nfl_monday_games[home] >= 2 or nfl_monday_games[away] >= 2
                    ):
                        objective += 120_000.0
                    if d.weekday() == 3 and (
                        nfl_thursday_games[home] >= 2 or nfl_thursday_games[away] >= 2
                    ):
                        objective += 120_000.0
                    nfl_fallback.append((objective, d))
                if nfl_fallback:
                    nfl_fallback.sort(key=lambda x: x[0])
                    chosen_date = nfl_fallback[0][1]
                else:
                    raise RuntimeError(f"No feasible date found for matchup {away}@{home}")
            else:
                raise RuntimeError(f"No feasible date found for matchup {away}@{home}")

        game = Game(
            game_id=f"G{game_counter:04d}",
            date=chosen_date,
            home=home,
            away=away,
            venue=home,
        )
        game_counter += 1
        schedule.append(game)

        date_usage[chosen_date] += 1
        venue_usage[home].add(chosen_date)
        team_states[home].games.append(game)
        team_states[away].games.append(game)
        if config.name.upper() == "NFL":
            w = _nfl_week_index(config, chosen_date)
            nfl_team_weeks[home].add(w)
            nfl_team_weeks[away].add(w)
            if chosen_date.weekday() == 0:
                nfl_monday_games[home] += 1
                nfl_monday_games[away] += 1
            if chosen_date.weekday() == 3:
                nfl_thursday_games[home] += 1
                nfl_thursday_games[away] += 1

    schedule.sort(key=lambda g: g.date)
    team_states = _recompute_team_states(schedule, teams, config)

    league_distance = sum(state.total_distance_miles for state in team_states.values())
    league_emissions = sum(state.total_emissions_kg for state in team_states.values())

    travel_values = [s.total_distance_miles for s in team_states.values()]
    target_b2b = _target_back_to_backs(config)
    rest_imbalance = [abs(s.back_to_backs - target_b2b) for s in team_states.values()]

    avg_travel = sum(travel_values) / len(travel_values)
    travel_var = sum((x - avg_travel) ** 2 for x in travel_values) / len(travel_values)
    avg_rest_imbalance = sum(rest_imbalance) / len(rest_imbalance)

    fairness_raw = 1.0 / (1.0 + (travel_var / 150_000_000.0) + (avg_rest_imbalance / 10.0))
    fairness_score = max(0.0, min(100.0, fairness_raw * 100.0))

    emissions_per_game = league_emissions / max(1, len(schedule))
    sustainability_raw = 1.0 / (1.0 + (emissions_per_game / 30_000.0))
    sustainability_score = max(0.0, min(100.0, sustainability_raw * 100.0))

    objective_value = (
        config.travel_weight * league_emissions
        + config.fairness_weight * (100.0 - fairness_score) * 10_000
        + config.density_weight * sum(abs(s.back_to_backs - target_b2b) for s in team_states.values()) * 850
    )

    diagnostics = {
        "total_games": float(len(schedule)),
        "avg_emissions_per_game": emissions_per_game,
        "avg_distance_per_team": avg_travel,
        "max_team_distance": max(travel_values),
        "min_team_distance": min(travel_values),
        "avg_back_to_backs": sum(s.back_to_backs for s in team_states.values()) / len(team_states),
        "target_back_to_backs": float(target_b2b),
        "avg_time_zone_jumps": sum(s.timezone_jumps for s in team_states.values()) / len(team_states),
    }

    return OptimizationResult(
        schedule=schedule,
        team_states=team_states,
        league_emissions_kg=league_emissions,
        league_distance_miles=league_distance,
        fairness_score=fairness_score,
        sustainability_score=sustainability_score,
        objective_value=objective_value,
        diagnostics=diagnostics,
    )
