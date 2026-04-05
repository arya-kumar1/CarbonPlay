"use client";

import { useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Input } from "@/components/ui/input";
import { OptimizeResponse } from "@/lib/types";
import { useDashboardStore } from "@/store/dashboard-store";
import { LeagueTheme } from "@/lib/league-theme";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getTeamColor, hexToRgba } from "@/lib/team-colors";
import { getTeamMeta } from "@/lib/team-meta";
import Image from "next/image";

function parseIsoDay(value: string): Date {
  return new Date(`${value}T00:00:00`);
}

function monthLabel(date: Date): string {
  return date.toLocaleDateString(undefined, { month: "long", year: "numeric" });
}

export function ScheduleView({ data, theme }: { data: OptimizeResponse; theme: LeagueTheme }) {
  const { selectedTeam, setSelectedTeam, filters } = useDashboardStore();
  const [monthCursor, setMonthCursor] = useState<Date>(() => {
    const start = parseIsoDay(data.meta.season_start);
    return new Date(start.getFullYear(), start.getMonth(), 1);
  });

  const rows = useMemo(() => {
    if (!selectedTeam) return data.schedule;
    return data.schedule.filter((g) => g.home === selectedTeam || g.away === selectedTeam);
  }, [data.schedule, selectedTeam]);

  const teams = [...new Set(data.team_metrics.map((t) => t.team))].sort();
  const seasonStartMonth = useMemo(() => {
    const d = parseIsoDay(data.meta.season_start);
    return new Date(d.getFullYear(), d.getMonth(), 1);
  }, [data.meta.season_start]);
  const seasonEndMonth = useMemo(() => {
    const d = parseIsoDay(data.meta.season_end);
    return new Date(d.getFullYear(), d.getMonth(), 1);
  }, [data.meta.season_end]);
  const selectedTeamGames = useMemo(
    () => (selectedTeam ? data.schedule.filter((g) => g.home === selectedTeam || g.away === selectedTeam) : []),
    [data.schedule, selectedTeam]
  );

  useEffect(() => {
    if (!selectedTeamGames.length) {
      setMonthCursor(seasonStartMonth);
      return;
    }
    const firstGame = parseIsoDay(selectedTeamGames[0].date);
    setMonthCursor(new Date(firstGame.getFullYear(), firstGame.getMonth(), 1));
  }, [seasonStartMonth, selectedTeamGames]);

  const gamesByDate = useMemo(() => {
    const map = new Map<string, (typeof selectedTeamGames)[number]>();
    for (const game of selectedTeamGames) {
      map.set(game.date, game);
    }
    return map;
  }, [selectedTeamGames]);

  const monthCells = useMemo(() => {
    const year = monthCursor.getFullYear();
    const month = monthCursor.getMonth();
    const first = new Date(year, month, 1);
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const leading = first.getDay();
    const total = Math.ceil((leading + daysInMonth) / 7) * 7;

    return Array.from({ length: total }).map((_, idx) => {
      const dayNumber = idx - leading + 1;
      const inMonth = dayNumber >= 1 && dayNumber <= daysInMonth;
      const dateObj = new Date(year, month, dayNumber);
      const iso = inMonth
        ? `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, "0")}-${String(dateObj.getDate()).padStart(2, "0")}`
        : "";
      return { dateObj, iso, inMonth };
    });
  }, [monthCursor]);

  const canPrev = monthCursor > seasonStartMonth;
  const canNext = monthCursor < seasonEndMonth;
  const allStarStart = parseIsoDay(filters.all_star_break_start);
  const allStarEnd = parseIsoDay(filters.all_star_break_end);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Input
          list="teams"
          placeholder="Filter by team"
          value={selectedTeam ?? ""}
          onChange={(e) => setSelectedTeam(e.target.value || null)}
          className="max-w-xs"
        />
        <datalist id="teams">
          {teams.map((t) => (
            <option value={t} key={t} />
          ))}
        </datalist>
      </div>

      <Card className={`${theme.cardClass} ${theme.borderClass}`}>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle>Team Calendar</CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={!canPrev}
              onClick={() => setMonthCursor((prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1))}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="min-w-40 text-center text-sm font-medium">{monthLabel(monthCursor)}</span>
            <Button
              variant="outline"
              size="sm"
              disabled={!canNext}
              onClick={() => setMonthCursor((prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1))}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {!selectedTeam ? (
            <div className="rounded-lg border border-dashed border-border/60 p-8 text-center text-sm text-muted-foreground">
              Select a team to view the interactive schedule calendar.
            </div>
          ) : (
            <div className="space-y-3">
              <div className="grid grid-cols-7 gap-2 text-center text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((d) => (
                  <div key={d}>{d}</div>
                ))}
              </div>
              <div className="grid grid-cols-7 gap-2">
                {monthCells.map(({ iso, inMonth, dateObj }) => {
                  const game = inMonth ? gamesByDate.get(iso) : undefined;
                  const isAllStarBreak =
                    inMonth &&
                    dateObj.getTime() >= allStarStart.getTime() &&
                    dateObj.getTime() <= allStarEnd.getTime();
                  const isHome = !!game && game.home === selectedTeam;
                  const opponent = game ? (isHome ? game.away : game.home) : "";
                  const opponentColor = opponent ? getTeamColor(opponent, data.meta.league) : undefined;
                  const opponentMeta = opponent ? getTeamMeta(opponent, data.meta.league) : null;
                  const venueMeta = game ? getTeamMeta(game.home, data.meta.league) : null;
                  const matchup = game ? `${game.away} @ ${game.home}` : "";

                  return (
                    <div
                      key={`${iso || dateObj.toISOString()}-${inMonth ? "in" : "out"}`}
                      className="group relative min-h-[90px] rounded-lg border border-border/50 p-2"
                      style={
                        game && opponentColor
                          ? {
                              background: `linear-gradient(155deg, ${hexToRgba(opponentColor, 0.28)}, ${hexToRgba(opponentColor, 0.1)})`
                            }
                          : isAllStarBreak
                            ? {
                                background: `linear-gradient(155deg, ${hexToRgba(theme.accent, 0.28)}, ${hexToRgba(theme.accent, 0.1)})`
                              }
                            : undefined
                      }
                    >
                      <div className={`text-xs ${inMonth ? "text-foreground" : "text-muted-foreground/40"}`}>
                        {inMonth ? dateObj.getDate() : ""}
                      </div>
                      {game ? (
                        <div className="mt-2 space-y-1">
                          <div className="flex items-center justify-between gap-2">
                            <div className="text-xs font-semibold">{isHome ? `${opponent}` : `@ ${opponent}`}</div>
                            {opponentMeta?.logo ? (
                              <Image
                                src={opponentMeta.logo}
                                alt={`${opponent} logo`}
                                width={28}
                                height={28}
                                className="h-7 w-7 object-contain"
                              />
                            ) : null}
                          </div>
                          <div className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold ${isHome ? "bg-blue-500/20 text-blue-200" : "bg-red-500/20 text-red-200"}`}>
                            {isHome ? "HOME" : "AWAY"}
                          </div>
                          <div className="pointer-events-none absolute left-2 top-2 z-20 hidden w-56 rounded-md border border-border/70 bg-card/95 p-2 text-[11px] shadow-xl backdrop-blur group-hover:block">
                            <p className="font-semibold">{matchup}</p>
                            <p className="mt-1 text-muted-foreground">{venueMeta?.city}</p>
                            <p className="text-muted-foreground">{venueMeta?.arena}</p>
                          </div>
                        </div>
                      ) : isAllStarBreak ? (
                        <div className="mt-2 rounded-md bg-accent/25 px-2 py-1 text-[10px] font-semibold text-foreground">
                          ALL-STAR BREAK
                        </div>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <div className={`overflow-auto rounded-xl border border-border/60 ${theme.borderClass}`}>
        <table className="w-full min-w-[680px] text-left text-sm">
          <thead className={`league-table-head text-xs uppercase tracking-wide text-muted-foreground ${theme.headerClass}`}>
            <tr>
              <th className="px-3 py-2">Date</th>
              <th className="px-3 py-2">Game</th>
              <th className="px-3 py-2">Venue</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 500).map((g) => (
              <tr key={g.game_id} className="border-t border-border/50">
                <td className="px-3 py-2">{g.date}</td>
                <td className="px-3 py-2 font-medium">{g.away} @ {g.home}</td>
                <td className="px-3 py-2 text-muted-foreground">{g.venue}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
