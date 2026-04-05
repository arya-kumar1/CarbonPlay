from __future__ import annotations

import argparse
import json
from datetime import date

from .models import BreakWindow, LeagueConfig
from .service import run_optimization


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Carbon-aware sports scheduler")
    parser.add_argument("--games-per-team", type=int, default=82)
    parser.add_argument("--season-start", type=str, default="2026-10-20")
    parser.add_argument("--season-end", type=str, default="2027-04-20")
    parser.add_argument("--max-back-to-backs", type=int, default=22)
    parser.add_argument("--max-three-in-four", type=int, default=24)
    parser.add_argument("--sustainability-weight", type=float, default=0.7)
    parser.add_argument("--fairness-weight", type=float, default=0.2)
    parser.add_argument("--travel-burden-weight", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = LeagueConfig(
        games_per_team=args.games_per_team,
        season_start=date.fromisoformat(args.season_start),
        season_end=date.fromisoformat(args.season_end),
        max_back_to_backs=args.max_back_to_backs,
        max_three_in_four=args.max_three_in_four,
        travel_weight=args.sustainability_weight,
        fairness_weight=args.fairness_weight,
        density_weight=args.travel_burden_weight,
        all_star_break=BreakWindow(date(2027, 2, 13), date(2027, 2, 18)),
        seed=args.seed,
    )
    result = run_optimization(config)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
