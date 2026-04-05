"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { TeamMetric } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LeagueTheme } from "@/lib/league-theme";
import { Cell } from "recharts";
import { getTeamColor } from "@/lib/team-colors";

export function EmissionsChart({
  data,
  highlightedTeam,
  theme
}: {
  data: TeamMetric[];
  highlightedTeam?: string | null;
  theme: LeagueTheme;
}) {
  const sorted = [...data].sort((a, b) => b.emissions_kg - a.emissions_kg);
  const minChartWidth = Math.max(900, sorted.length * 58);

  return (
    <Card className={`${theme.cardClass} min-w-0 max-w-full overflow-hidden`}>
      <CardHeader>
        <CardTitle>Emissions by Team</CardTitle>
      </CardHeader>
      <CardContent className="h-[340px] max-w-full overflow-x-auto overflow-y-hidden">
        <div className="h-full min-w-full" style={{ width: `${minChartWidth}px` }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={sorted} margin={{ left: 12, right: 12, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.25} />
              <XAxis dataKey="team" tickLine={false} axisLine={false} interval={0} angle={-35} textAnchor="end" height={75} />
              <YAxis tickLine={false} axisLine={false} />
              <Tooltip formatter={(v: number) => `${v.toLocaleString()} kg`} />
              <Bar dataKey="emissions_kg" radius={[8, 8, 0, 0]} opacity={highlightedTeam ? 0.45 : 0.95}>
              {sorted.map((entry) => (
                <Cell
                  key={entry.team}
                  fill={getTeamColor(entry.team, theme.league)}
                />
              ))}
            </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
