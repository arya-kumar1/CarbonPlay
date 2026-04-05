"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useDashboardStore } from "@/store/dashboard-store";
import { toast } from "react-hot-toast";
import { LeagueTheme } from "@/lib/league-theme";

export function SidebarFilters({ onRun, theme }: { onRun: () => void; theme: LeagueTheme }) {
  const { filters, setFilter, setLeague } = useDashboardStore();

  return (
    <aside className={`sticky top-20 h-[calc(100vh-6rem)] overflow-auto rounded-xl border border-border/60 bg-card/80 p-4 shadow-card ${theme.cardClass} ${theme.borderClass}`}>
      <div className="space-y-4">
        <div>
          <Label>League</Label>
          <div className="mt-1 grid grid-cols-3 gap-2">
            <Button variant={filters.league === "NBA" ? "default" : "outline"} size="sm" onClick={() => setLeague("NBA")}>
              NBA
            </Button>
            <Button variant={filters.league === "NHL" ? "default" : "outline"} size="sm" onClick={() => setLeague("NHL")}>
              NHL
            </Button>
            <Button variant={filters.league === "NFL" ? "default" : "outline"} size="sm" onClick={() => setLeague("NFL")}>
              NFL
            </Button>
          </div>
        </div>

        <div>
          <Label htmlFor="team-games">Games per Team</Label>
          <Input id="team-games" type="number" value={filters.games_per_team} onChange={(e) => setFilter("games_per_team", Number(e.target.value))} />
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div>
            <Label>Sustainability</Label>
            <Input type="number" step="0.01" value={filters.sustainability_weight} onChange={(e) => setFilter("sustainability_weight", Number(e.target.value))} />
          </div>
          <div>
            <Label>Fairness</Label>
            <Input type="number" step="0.01" value={filters.fairness_weight} onChange={(e) => setFilter("fairness_weight", Number(e.target.value))} />
          </div>
        </div>

        <div>
          <Label>Travel Burden Weight</Label>
          <Input type="number" step="0.01" value={filters.travel_burden_weight} onChange={(e) => setFilter("travel_burden_weight", Number(e.target.value))} />
        </div>

        <div>
          <Label>Date Range</Label>
          <div className="grid grid-cols-1 gap-2">
            <Input type="date" value={filters.season_start} onChange={(e) => setFilter("season_start", e.target.value)} />
            <Input type="date" value={filters.season_end} onChange={(e) => setFilter("season_end", e.target.value)} />
          </div>
        </div>

        <div className="space-y-2">
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={filters.use_ticketmaster_blocks} onChange={(e) => setFilter("use_ticketmaster_blocks", e.target.checked)} />
            Ticketmaster venue conflicts
          </label>
          <Input
            placeholder="Ticketmaster API key (optional)"
            type="password"
            value={filters.ticketmaster_api_key ?? ""}
            onChange={(e) => setFilter("ticketmaster_api_key", e.target.value)}
          />
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={filters.include_baseline} onChange={(e) => setFilter("include_baseline", e.target.checked)} />
            Include baseline comparison
          </label>
        </div>

        <Button
          className={`w-full ${theme.buttonGlowClass}`}
          onClick={() => {
            if (filters.sustainability_weight + filters.fairness_weight + filters.travel_burden_weight > 1.5) {
              toast.error("Weights are unusually high. Consider normalizing for stable behavior.");
            }
            onRun();
          }}
        >
          Generate Optimized Schedule
        </Button>
      </div>
    </aside>
  );
}
