export type League = "NBA" | "NHL" | "NFL";

export interface TeamMetric {
  team: string;
  distance_miles: number;
  emissions_kg: number;
  back_to_backs: number;
  three_in_four: number;
  timezone_jumps: number;
}

export interface TeamLocation {
  team: string;
  latitude: number;
  longitude: number;
  timezone: string;
  conference: string;
  division: string;
  aircraft_type?: string | null;
}

export interface ScheduleRow {
  game_id: string;
  date: string;
  home: string;
  away: string;
  venue: string;
}

export interface OptimizeResponse {
  meta: {
    league: League;
    games: number;
    season_start: string;
    season_end: string;
    ticketmaster_blocks_enabled: boolean;
    baseline_included: boolean;
    schedule_fallback_used?: boolean;
  };
  scores: {
    sustainability: number;
    fairness: number;
    objective: number;
    emissions_improvement_vs_baseline_pct: number;
  };
  league_metrics: {
    league_distance_miles: number;
    league_emissions_kg: number;
    avg_emissions_per_game: number;
    avg_distance_per_team: number;
    avg_back_to_backs: number;
    avg_time_zone_jumps: number;
  };
  team_metrics: TeamMetric[];
  team_locations: TeamLocation[];
  schedule: ScheduleRow[];
  rest_distribution: Array<{
    team: string;
    avg_rest_days: number;
    min_rest_days: number;
    max_rest_days: number;
  }>;
  venue_block_diagnostics: {
    manual_block_dates: number;
    effective_block_dates: number;
    ticketmaster: Record<string, unknown>;
  };
  baseline: null | {
    league_emissions_kg: number;
    league_distance_miles: number;
    avg_emissions_per_game: number;
    team_metrics: TeamMetric[];
  };
}

export interface OptimizePayload {
  league: League;
  games_per_team: number;
  season_start: string;
  season_end: string;
  max_back_to_backs: number;
  max_three_in_four: number;
  close_range_miles: number;
  flight_emissions_kg_per_mile: number;
  ground_emissions_kg_per_mile: number;
  sustainability_weight: number;
  fairness_weight: number;
  travel_burden_weight: number;
  all_star_break_start: string;
  all_star_break_end: string;
  all_star_game_date: string;
  ncaa_championship_date: string;
  use_ticketmaster_blocks: boolean;
  ticketmaster_api_key?: string;
  include_baseline: boolean;
  seed: number;
}
