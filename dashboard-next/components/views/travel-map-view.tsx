"use client";

import { TravelMap } from "@/components/map/travel-map";
import { OptimizeResponse } from "@/lib/types";
import { useDashboardStore } from "@/store/dashboard-store";
import { LeagueTheme } from "@/lib/league-theme";

export function TravelMapView({ data, theme }: { data: OptimizeResponse; theme: LeagueTheme }) {
  const hoveredTeam = useDashboardStore((s) => s.hoveredTeam);
  const selectedTeam = useDashboardStore((s) => s.selectedTeam);
  return <TravelMap data={data} highlightedTeam={hoveredTeam ?? selectedTeam} theme={theme} />;
}
