"use client";

import { useDashboardStore } from "@/store/dashboard-store";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmissionsChart } from "@/components/charts/emissions-chart";
import { OptimizeResponse } from "@/lib/types";
import { LeagueTheme } from "@/lib/league-theme";

export function EmissionsView({ data, theme }: { data: OptimizeResponse; theme: LeagueTheme }) {
  const { setHoveredTeam } = useDashboardStore();

  return (
    <div className="min-w-0 space-y-4">
      <div className="min-w-0 max-w-full">
        <EmissionsChart data={data.team_metrics} theme={theme} />
      </div>
      <Card className={`${theme.cardClass} ${theme.borderClass} min-w-0 max-w-full`}>
        <CardHeader>
          <CardTitle>Team Emissions Table</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="max-h-[420px] overflow-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-card/95">
                <tr>
                  <th className="px-2 py-2 text-left text-xs uppercase tracking-wide text-muted-foreground">Team</th>
                  <th className="px-2 py-2 text-right text-xs uppercase tracking-wide text-muted-foreground">Emissions</th>
                </tr>
              </thead>
              <tbody>
                {[...data.team_metrics]
                  .sort((a, b) => b.emissions_kg - a.emissions_kg)
                  .map((row) => (
                    <tr
                      key={row.team}
                      onMouseEnter={() => setHoveredTeam(row.team)}
                      onMouseLeave={() => setHoveredTeam(null)}
                      className="border-t border-border/50"
                    >
                      <td className="px-2 py-2 font-medium">{row.team}</td>
                      <td className="px-2 py-2 text-right">{Math.round(row.emissions_kg).toLocaleString()} kg</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
