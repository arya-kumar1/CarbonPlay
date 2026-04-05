"use client";

import { ComparisonChart } from "@/components/charts/comparison-chart";
import { AdvancedInsights } from "@/components/charts/advanced-insights";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { OptimizeResponse } from "@/lib/types";
import { LeagueTheme } from "@/lib/league-theme";
import { getTeamColor } from "@/lib/team-colors";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, Cell } from "recharts";

export function ComparisonsView({ data, theme }: { data: OptimizeResponse; theme: LeagueTheme }) {
  if (!data.baseline) {
    return (
      <div className="space-y-4">
        <Card className={`${theme.cardClass} ${theme.borderClass}`}>
          <CardHeader>
            <CardTitle>No Baseline Loaded</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Turn on baseline comparison in the sidebar to compare optimized schedule emissions against a reference schedule.
          </CardContent>
        </Card>
        <AdvancedInsights data={data} theme={theme} />
      </div>
    );
  }

  const baselineByTeam = new Map(data.baseline.team_metrics.map((row) => [row.team, row]));
  const pctRows = data.team_metrics
    .map((optimized) => {
      const baseline = baselineByTeam.get(optimized.team);
      const baselineValue = baseline?.emissions_kg ?? optimized.emissions_kg;
      const pctDecrease = baselineValue > 0
        ? ((baselineValue - optimized.emissions_kg) / baselineValue) * 100
        : 0;
      return { team: optimized.team, pctDecrease };
    })
    .sort((a, b) => b.pctDecrease - a.pctDecrease);

  const minChartWidth = Math.max(900, pctRows.length * 56);

  return (
    <div className="min-w-0 space-y-4">
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card className={`${theme.cardClass} ${theme.borderClass}`}>
          <CardHeader>
            <CardTitle>League Emissions Reduction</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">
            {data.scores.emissions_improvement_vs_baseline_pct.toFixed(2)}%
          </CardContent>
        </Card>
      </div>

      <Card className={`${theme.cardClass} ${theme.borderClass} min-w-0 max-w-full overflow-hidden`}>
        <CardHeader>
          <CardTitle>Percent Decrease by Team</CardTitle>
        </CardHeader>
        <CardContent className="h-[340px] max-w-full overflow-x-auto overflow-y-hidden">
          <div className="h-full min-w-full" style={{ width: `${minChartWidth}px` }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={pctRows} margin={{ left: 8, right: 16, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis dataKey="team" tickLine={false} axisLine={false} interval={0} angle={-35} textAnchor="end" height={75} />
                <YAxis tickLine={false} axisLine={false} unit="%" />
                <Tooltip formatter={(v: number) => `${v.toFixed(2)}%`} />
                <Bar dataKey="pctDecrease" radius={[8, 8, 0, 0]}>
                  {pctRows.map((row) => (
                    <Cell key={row.team} fill={getTeamColor(row.team, data.meta.league)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <ComparisonChart optimized={data.team_metrics} baseline={data.baseline.team_metrics} theme={theme} />
      <AdvancedInsights data={data} theme={theme} />
    </div>
  );
}
