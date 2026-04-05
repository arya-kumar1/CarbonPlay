"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ScheduleRow } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LeagueTheme } from "@/lib/league-theme";
import { Cell } from "recharts";

function parseLocalDate(iso: string): Date {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, (m ?? 1) - 1, d ?? 1, 12, 0, 0);
}

/** JS: Sun=0 … Fri=5, Sat=6 */
function shortWeekSlot(d: Date): "thu" | "mon" | "fri" | null {
  const wd = d.getDay();
  if (wd === 1) return "mon";
  if (wd === 4) return "thu";
  if (wd === 5) return "fri";
  return null;
}

export type NflShortWeekRow = {
  team: string;
  thu: number;
  mon: number;
  fri: number;
  total: number;
};

export function computeNflShortWeekCounts(schedule: ScheduleRow[]): NflShortWeekRow[] {
  const acc = new Map<string, { thu: number; mon: number; fri: number }>();
  for (const g of schedule) {
    acc.set(g.home, acc.get(g.home) ?? { thu: 0, mon: 0, fri: 0 });
    acc.set(g.away, acc.get(g.away) ?? { thu: 0, mon: 0, fri: 0 });
  }

  for (const g of schedule) {
    const slot = shortWeekSlot(parseLocalDate(g.date));
    if (!slot) continue;
    for (const code of [g.home, g.away]) {
      const row = acc.get(code)!;
      row[slot] += 1;
    }
  }

  return [...acc.entries()]
    .map(([team, c]) => ({
      team,
      thu: c.thu,
      mon: c.mon,
      fri: c.fri,
      total: c.thu + c.mon + c.fri,
    }))
    .sort((a, b) => b.total - a.total || a.team.localeCompare(b.team));
}

export function NflShortWeeksChart({
  schedule,
  highlightedTeam,
  theme,
}: {
  schedule: ScheduleRow[];
  highlightedTeam?: string | null;
  theme: LeagueTheme;
}) {
  const rows = computeNflShortWeekCounts(schedule);
  const minChartWidth = Math.max(900, rows.length * 58);
  const [c0, c1, c2] = theme.chartPalette;
  const dim = (team: string) => (highlightedTeam && highlightedTeam !== team ? 0.32 : 1);

  return (
    <Card className={`${theme.cardClass} min-w-0 max-w-full overflow-hidden`}>
      <CardHeader>
        <CardTitle>Short-week games by team</CardTitle>
        <p className="text-muted-foreground text-sm font-normal leading-snug">
          Count of games played on Monday, Thursday, or Friday (prime-time and short-rest windows).
        </p>
      </CardHeader>
      <CardContent className="h-[380px] max-w-full overflow-x-auto overflow-y-hidden">
        <div className="h-full min-w-full" style={{ width: `${minChartWidth}px` }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={rows} margin={{ left: 8, right: 12, bottom: 10, top: 8 }}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.25} />
              <XAxis dataKey="team" tickLine={false} axisLine={false} interval={0} angle={-35} textAnchor="end" height={75} />
              <YAxis tickLine={false} axisLine={false} allowDecimals={false} />
              <Tooltip
                content={({ active, label, payload }) => {
                  if (!active || !payload?.length) return null;
                  const thu = Number(payload.find((p) => p.dataKey === "thu")?.value ?? 0);
                  const mon = Number(payload.find((p) => p.dataKey === "mon")?.value ?? 0);
                  const fri = Number(payload.find((p) => p.dataKey === "fri")?.value ?? 0);
                  const total = thu + mon + fri;
                  return (
                    <div className="border-border bg-background/95 rounded-md border px-3 py-2 text-sm shadow-md backdrop-blur">
                      <div className="font-medium">{label}</div>
                      <div className="text-muted-foreground mt-1 space-y-0.5">
                        <div>Total: {total}</div>
                        <div style={{ color: c0 }}>Thursday: {thu}</div>
                        <div style={{ color: c1 }}>Monday: {mon}</div>
                        <div style={{ color: c2 }}>Friday: {fri}</div>
                      </div>
                    </div>
                  );
                }}
              />
              <Legend />
              <Bar dataKey="thu" name="Thursday" stackId="sw" fill={c0}>
                {rows.map((entry) => (
                  <Cell key={`${entry.team}-thu`} fill={c0} fillOpacity={dim(entry.team)} />
                ))}
              </Bar>
              <Bar dataKey="mon" name="Monday" stackId="sw" fill={c1}>
                {rows.map((entry) => (
                  <Cell key={`${entry.team}-mon`} fill={c1} fillOpacity={dim(entry.team)} />
                ))}
              </Bar>
              <Bar dataKey="fri" name="Friday" stackId="sw" fill={c2} radius={[8, 8, 0, 0]}>
                {rows.map((entry) => (
                  <Cell key={`${entry.team}-fri`} fill={c2} fillOpacity={dim(entry.team)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
