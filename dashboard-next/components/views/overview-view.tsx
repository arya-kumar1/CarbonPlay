"use client";

import { KpiCard } from "@/components/kpi-card";
import { EmissionsChart } from "@/components/charts/emissions-chart";
import { NflShortWeeksChart } from "@/components/charts/nfl-short-weeks-chart";
import { TravelFairnessChart } from "@/components/charts/travel-fairness-chart";
import { OptimizeResponse } from "@/lib/types";
import { LeagueTheme } from "@/lib/league-theme";

export function OverviewView({
  data,
  highlightedTeam,
  theme
}: {
  data: OptimizeResponse;
  highlightedTeam?: string | null;
  theme: LeagueTheme;
}) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Total Emissions" value={`${Math.round(data.league_metrics.league_emissions_kg).toLocaleString()} kg`} theme={theme} />
        <KpiCard label="Total Distance" value={`${Math.round(data.league_metrics.league_distance_miles).toLocaleString()} mi`} theme={theme} />
        <KpiCard label="Fairness Score" value={data.scores.fairness.toFixed(1)} theme={theme} />
        <KpiCard
          label="Venue Conflicts"
          value={`${data.venue_block_diagnostics.effective_block_dates}`}
          subtext={`Improvement vs baseline: ${data.scores.emissions_improvement_vs_baseline_pct.toFixed(2)}%`}
          theme={theme}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <EmissionsChart data={data.team_metrics} highlightedTeam={highlightedTeam} theme={theme} />
        {data.meta.league === "NFL" ? (
          <NflShortWeeksChart schedule={data.schedule} highlightedTeam={highlightedTeam} theme={theme} />
        ) : (
          <TravelFairnessChart data={data.team_metrics} theme={theme} />
        )}
      </div>
    </div>
  );
}
