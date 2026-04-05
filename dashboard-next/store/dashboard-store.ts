import { create } from "zustand";
import { League, OptimizePayload } from "@/lib/types";

interface DashboardState {
  filters: OptimizePayload;
  selectedTeam: string | null;
  hoveredTeam: string | null;
  setLeague: (league: League) => void;
  setFilter: <K extends keyof OptimizePayload>(key: K, value: OptimizePayload[K]) => void;
  setSelectedTeam: (team: string | null) => void;
  setHoveredTeam: (team: string | null) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  filters: {
    league: "NBA",
    games_per_team: 82,
    season_start: "2026-10-20",
    season_end: "2027-04-20",
    max_back_to_backs: 15,
    max_three_in_four: 24,
    close_range_miles: 120,
    flight_emissions_kg_per_mile: 18,
    ground_emissions_kg_per_mile: 1.2,
    sustainability_weight: 0.9,
    fairness_weight: 0.08,
    travel_burden_weight: 0.02,
    all_star_break_start: "2027-02-13",
    all_star_break_end: "2027-02-18",
    all_star_game_date: "2027-02-14",
    ncaa_championship_date: "2027-04-05",
    use_ticketmaster_blocks: false,
    include_baseline: false,
    seed: 7
  },
  selectedTeam: null,
  hoveredTeam: null,
  setLeague: (league) =>
    set((state) => ({
      filters: {
        ...state.filters,
        league,
        games_per_team: league === "NFL" ? 17 : 82,
        season_start: league === "NHL" ? "2026-10-07" : league === "NFL" ? "2026-09-10" : "2026-10-20",
        season_end: league === "NHL" ? "2027-04-18" : league === "NFL" ? "2027-01-10" : "2027-04-20",
        max_back_to_backs: league === "NFL" ? 0 : 15,
        max_three_in_four: league === "NFL" ? 0 : 24,
        sustainability_weight: league === "NFL" ? 0.72 : 0.9,
        fairness_weight: league === "NFL" ? 0.18 : 0.08,
        travel_burden_weight: league === "NFL" ? 0.1 : 0.02,
        all_star_break_start: league === "NHL" ? "2027-02-01" : league === "NFL" ? "2027-02-03" : "2027-02-13",
        all_star_break_end: league === "NHL" ? "2027-02-10" : league === "NFL" ? "2027-02-08" : "2027-02-18",
        all_star_game_date: league === "NHL" ? "2027-02-06" : league === "NFL" ? "2027-02-07" : "2027-02-14",
        ncaa_championship_date: league === "NHL" ? "2027-02-07" : league === "NFL" ? "2027-01-01" : "2027-04-05"
      }
    })),
  setFilter: (key, value) => set((state) => ({ filters: { ...state.filters, [key]: value } })),
  setSelectedTeam: (team) => set({ selectedTeam: team }),
  setHoveredTeam: (team) => set({ hoveredTeam: team })
}));
