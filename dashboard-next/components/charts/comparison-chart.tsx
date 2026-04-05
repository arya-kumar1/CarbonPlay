"use client";

import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { TeamMetric } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LeagueTheme } from "@/lib/league-theme";
import { Cell } from "recharts";
import { getTeamColor, hexToRgba } from "@/lib/team-colors";

export function ComparisonChart({
  optimized,
  baseline,
  theme
}: {
  optimized: TeamMetric[];
  baseline: TeamMetric[];
  theme: LeagueTheme;
}) {
  const baselineByTeam = new Map(baseline.map((b) => [b.team, b]));
  const rows = optimized
    .map((o) => ({
      team: o.team,
      optimized: o.emissions_kg,
      baseline: baselineByTeam.get(o.team)?.emissions_kg ?? o.emissions_kg
    }))
    .sort((a, b) => b.optimized - a.optimized);
  const minChartWidth = Math.max(900, rows.length * 64);

  return (
    <Card className={`${theme.cardClass} min-w-0 max-w-full overflow-hidden`}>
      <CardHeader>
        <CardTitle>Optimized vs Baseline Emissions</CardTitle>
      </CardHeader>
      <CardContent className="h-[340px] max-w-full overflow-x-auto overflow-y-hidden">
        <div className="h-full min-w-full" style={{ width: `${minChartWidth}px` }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={rows} margin={{ left: 8, right: 16, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis dataKey="team" tickLine={false} axisLine={false} interval={0} angle={-35} textAnchor="end" height={75} />
              <YAxis tickLine={false} axisLine={false} />
              <Tooltip formatter={(v: number) => `${v.toLocaleString()} kg`} />
              <Legend />
              <Bar dataKey="optimized" radius={[8, 8, 0, 0]}>
                {rows.map((row) => (
                  <Cell key={`opt-${row.team}`} fill={getTeamColor(row.team, theme.league)} />
                ))}
              </Bar>
              <Bar dataKey="baseline" radius={[8, 8, 0, 0]}>
                {rows.map((row) => (
                  <Cell key={`base-${row.team}`} fill={hexToRgba(getTeamColor(row.team, theme.league), 0.42)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
