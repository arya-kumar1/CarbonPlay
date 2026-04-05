"use client";

import { Scatter, ScatterChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { TeamMetric } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LeagueTheme } from "@/lib/league-theme";
import { Cell } from "recharts";
import { getTeamColor } from "@/lib/team-colors";

export function TravelFairnessChart({ data, theme }: { data: TeamMetric[]; theme: LeagueTheme }) {
  const xValues = data.map((d) => d.distance_miles);
  const yValues = data.map((d) => d.back_to_backs);
  const xMin = xValues.length ? Math.min(...xValues) : 0;
  const xMax = xValues.length ? Math.max(...xValues) : 1;
  const yMin = yValues.length ? Math.min(...yValues) : 0;
  const yMax = yValues.length ? Math.max(...yValues) : 1;
  const xPad = Math.max(150, (xMax - xMin) * 0.08);
  const yPad = 1;

  return (
    <Card className={theme.cardClass}>
      <CardHeader>
        <CardTitle>Travel Burden vs Back-to-Backs</CardTitle>
      </CardHeader>
      <CardContent className="h-[320px]">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ left: 6, right: 16, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.25} />
            <XAxis
              type="number"
              dataKey="distance_miles"
              name="Distance"
              tickLine={false}
              axisLine={false}
              domain={[Math.max(0, Math.floor(xMin - xPad)), Math.ceil(xMax + xPad)]}
              tickFormatter={(v: number) => `${Math.round(v).toLocaleString()}`}
            />
            <YAxis
              type="number"
              dataKey="back_to_backs"
              name="Back-to-backs"
              tickLine={false}
              axisLine={false}
              allowDecimals={false}
              domain={[Math.max(0, Math.floor(yMin - yPad)), Math.ceil(yMax + yPad)]}
            />
            <Tooltip
              cursor={{ strokeDasharray: "4 4" }}
              content={({ active, payload }) => {
                if (!active || !payload || !payload.length) return null;
                const point = payload[0]?.payload as TeamMetric;
                return (
                  <div className="rounded-md border border-border/80 bg-card/95 p-2 text-xs shadow-sm">
                    <p className="font-semibold">{point.team}</p>
                    <p>Distance: {Math.round(point.distance_miles).toLocaleString()} mi</p>
                    <p>Back-to-backs: {point.back_to_backs}</p>
                  </div>
                );
              }}
            />
            <Scatter data={data}>
              {data.map((row) => (
                <Cell key={row.team} fill={getTeamColor(row.team, theme.league)} />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
