"use client";

import { useMemo, useState } from "react";
import { useQueries } from "@tanstack/react-query";
import { CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, Bar, BarChart, Legend } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LeagueTheme } from "@/lib/league-theme";
import { optimizeSchedule } from "@/lib/api";
import { OptimizeResponse, OptimizePayload } from "@/lib/types";
import { useDashboardStore } from "@/store/dashboard-store";

type WeightTriplet = Pick<OptimizePayload, "sustainability_weight" | "fairness_weight" | "travel_burden_weight">;

function clamp(v: number, lo = 0.02, hi = 0.96) {
  return Math.max(lo, Math.min(hi, v));
}

function normalizeWeights(w: WeightTriplet): WeightTriplet {
  const sum = w.sustainability_weight + w.fairness_weight + w.travel_burden_weight;
  if (sum <= 0) return { sustainability_weight: 0.9, fairness_weight: 0.08, travel_burden_weight: 0.02 };
  return {
    sustainability_weight: w.sustainability_weight / sum,
    fairness_weight: w.fairness_weight / sum,
    travel_burden_weight: w.travel_burden_weight / sum
  };
}

function tweakWeight(base: WeightTriplet, key: keyof WeightTriplet, delta: number): WeightTriplet {
  const next = { ...base };
  next[key] = clamp(next[key] + delta);
  return normalizeWeights(next);
}

interface AdvancedInsightsProps {
  data: OptimizeResponse;
  theme: LeagueTheme;
}

export function AdvancedInsights({ data, theme }: AdvancedInsightsProps) {
  const { filters } = useDashboardStore();
  const [runNonce, setRunNonce] = useState(0);

  const baseWeights: WeightTriplet = useMemo(
    () =>
      normalizeWeights({
        sustainability_weight: filters.sustainability_weight,
        fairness_weight: filters.fairness_weight,
        travel_burden_weight: filters.travel_burden_weight
      }),
    [filters.fairness_weight, filters.sustainability_weight, filters.travel_burden_weight]
  );

  const tornadoScenarios = useMemo(
    () => [
      { id: "s-low", factor: "Sustainability", side: "Low", weights: tweakWeight(baseWeights, "sustainability_weight", -0.15), seedOffset: 201 },
      { id: "s-high", factor: "Sustainability", side: "High", weights: tweakWeight(baseWeights, "sustainability_weight", 0.15), seedOffset: 202 },
      { id: "f-low", factor: "Fairness", side: "Low", weights: tweakWeight(baseWeights, "fairness_weight", -0.15), seedOffset: 203 },
      { id: "f-high", factor: "Fairness", side: "High", weights: tweakWeight(baseWeights, "fairness_weight", 0.15), seedOffset: 204 },
      { id: "t-low", factor: "Travel Burden", side: "Low", weights: tweakWeight(baseWeights, "travel_burden_weight", -0.15), seedOffset: 205 },
      { id: "t-high", factor: "Travel Burden", side: "High", weights: tweakWeight(baseWeights, "travel_burden_weight", 0.15), seedOffset: 206 }
    ],
    [baseWeights]
  );

  const allScenarios = [...tornadoScenarios];
  const results = useQueries({
    queries: allScenarios.map((scenario) => ({
      queryKey: ["advanced-insights", runNonce, filters.league, scenario.id, scenario.weights],
      enabled: runNonce > 0,
      queryFn: async () => {
        const payload: OptimizePayload = {
          ...filters,
          ...scenario.weights,
          include_baseline: false,
          use_ticketmaster_blocks: false,
          seed: filters.seed + scenario.seedOffset
        };
        return optimizeSchedule(payload);
      }
    }))
  });

  const loading = runNonce > 0 && results.some((q) => q.isLoading || q.isFetching);
  const anyError = results.find((q) => q.error)?.error as Error | undefined;

  const tornadoRows = useMemo(() => {
    if (!runNonce) return [];
    const byFactor = new Map<string, { factor: string; low: number; high: number }>();
    for (let i = 0; i < tornadoScenarios.length; i += 1) {
      const s = tornadoScenarios[i];
      const q = results[i];
      if (!q.data) continue;
      const pct = ((q.data.league_metrics.league_emissions_kg - data.league_metrics.league_emissions_kg) / data.league_metrics.league_emissions_kg) * 100;
      const row = byFactor.get(s.factor) ?? { factor: s.factor, low: 0, high: 0 };
      if (s.side === "Low") row.low = pct;
      else row.high = pct;
      byFactor.set(s.factor, row);
    }
    return Array.from(byFactor.values());
  }, [data.league_metrics.league_emissions_kg, results, runNonce, tornadoScenarios]);

  return (
    <div className="space-y-4">
      <Card className={`${theme.cardClass} ${theme.borderClass}`}>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle>Advanced Scenario Insights</CardTitle>
          <Button onClick={() => setRunNonce((n) => n + 1)} disabled={loading}>
            {loading ? "Running..." : "Run Sensitivity Analysis"}
          </Button>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Runs six additional optimization scenarios around your current settings: each objective weight (Sustainability, Fairness, Travel Burden)
          is nudged lower and higher while the other weights are rebalanced. Ticketmaster blocks are disabled for this analysis to keep runs fast and comparable.
          The tornado chart shows the emissions percent change vs your current schedule.
        </CardContent>
      </Card>

      {anyError ? (
        <Card className={`${theme.cardClass} ${theme.borderClass}`}>
          <CardContent className="p-5 text-sm text-red-500">Scenario analysis failed: {anyError.message}</CardContent>
        </Card>
      ) : null}

      <Card className={`${theme.cardClass} ${theme.borderClass}`}>
        <CardHeader>
          <CardTitle>Sensitivity Tornado (Emissions % vs Current)</CardTitle>
        </CardHeader>
        <CardContent className="h-[320px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={tornadoRows} layout="vertical" margin={{ left: 16, right: 16 }}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis type="number" tickLine={false} axisLine={false} tickFormatter={(v: number) => `${v.toFixed(1)}%`} />
              <YAxis dataKey="factor" type="category" tickLine={false} axisLine={false} width={110} />
              <Tooltip formatter={(v: number) => `${v.toFixed(2)}%`} />
              <Legend />
              <Bar dataKey="low" name="Weight Lowered" fill={theme.chartPalette[3]} radius={[0, 6, 6, 0]} />
              <Bar dataKey="high" name="Weight Raised" fill={theme.chartPalette[0]} radius={[0, 6, 6, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
