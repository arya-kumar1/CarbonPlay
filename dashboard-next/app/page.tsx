"use client";

import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "motion/react";
import { Tabs, TabList, Tab, TabPanel } from "react-aria-components";
import toast from "react-hot-toast";

import { optimizeSchedule } from "@/lib/api";
import { downloadCsv, downloadJson } from "@/lib/export";
import { SidebarFilters } from "@/components/layout/sidebar-filters";
import { TopNav } from "@/components/layout/top-nav";
import { LeagueHero } from "@/components/layout/league-hero";
import { EmptyState } from "@/components/state/empty-state";
import { SkeletonGrid } from "@/components/state/skeleton-grid";
import { useDashboardStore } from "@/store/dashboard-store";
import { OverviewView } from "@/components/views/overview-view";
import { ScheduleView } from "@/components/views/schedule-view";
import { TravelMapView } from "@/components/views/travel-map-view";
import { EmissionsView } from "@/components/views/emissions-view";
import { ComparisonsView } from "@/components/views/comparisons-view";
import { cn } from "@/lib/utils";
import { getLeagueTheme } from "@/lib/league-theme";

const TABS = ["overview", "schedule", "travel", "emissions", "comparisons"] as const;

type TabKey = (typeof TABS)[number];

export default function DashboardPage() {
  const [mounted, setMounted] = useState(false);
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [runNonce, setRunNonce] = useState(0);
  const { filters, hoveredTeam } = useDashboardStore();
  const theme = getLeagueTheme(filters.league);

  useEffect(() => {
    setMounted(true);
  }, []);

  const query = useQuery({
    queryKey: ["optimize", filters, runNonce],
    queryFn: () => optimizeSchedule(filters),
    enabled: runNonce > 0
  });

  const handleRun = () => {
    setRunNonce((n) => n + 1);
    toast.promise(query.refetch(), {
      loading: "Generating optimized schedule...",
      success: "Schedule generated",
      error: (e) => e?.message ?? "Failed to generate schedule"
    });
  };

  const handleExport = () => {
    if (!query.data) {
      toast.error("No data to export yet.");
      return;
    }
    downloadCsv("schedule.csv", query.data.schedule);
    downloadJson("summary.json", query.data);
    toast.success("Exports downloaded");
  };

  const body = useMemo(() => {
    if (query.isLoading || query.isFetching) return <SkeletonGrid theme={theme} />;
    if (query.isError) return <EmptyState message={(query.error as Error).message} theme={theme} />;
    if (!query.data) return <EmptyState message="Adjust filters and run optimization to start exploring scenarios." theme={theme} />;

    return (
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.22 }}
        >
          {activeTab === "overview" && <OverviewView data={query.data} highlightedTeam={hoveredTeam} theme={theme} />}
          {activeTab === "schedule" && <ScheduleView data={query.data} theme={theme} />}
          {activeTab === "travel" && <TravelMapView data={query.data} theme={theme} />}
          {activeTab === "emissions" && <EmissionsView data={query.data} theme={theme} />}
          {activeTab === "comparisons" && <ComparisonsView data={query.data} theme={theme} />}
        </motion.div>
      </AnimatePresence>
    );
  }, [activeTab, hoveredTeam, query.data, query.error, query.isError, query.isFetching, query.isLoading, theme]);

  if (!mounted) {
    return (
      <div className="min-h-screen" style={theme.cssVars} data-league={theme.league}>
        <main className="container py-6">
          <SkeletonGrid theme={theme} />
        </main>
      </div>
    );
  }

  return (
    <div className={cn("min-h-screen transition-colors duration-500", theme.textureClass)} style={theme.cssVars} data-league={theme.league}>
      <TopNav league={filters.league} theme={theme} onRefresh={handleRun} onExport={handleExport} isLoading={query.isFetching} />

      <main className="container py-6">
        <div className="mb-6">
          <LeagueHero theme={theme} />
        </div>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[280px_1fr]">
          <SidebarFilters onRun={handleRun} theme={theme} />

          <section className="min-w-0 space-y-4">
            <Tabs
              selectedKey={activeTab}
              onSelectionChange={(key) => setActiveTab(String(key) as TabKey)}
              aria-label="Dashboard sections"
            >
              <TabList className={cn("flex flex-wrap gap-2 rounded-xl border border-border/60 bg-card/70 p-2", theme.borderClass)} aria-label="Sections">
                {TABS.map((t) => (
                  <Tab
                    id={t}
                    key={t}
                    className={({ isSelected }) =>
                      cn(
                        "cursor-pointer rounded-lg px-3 py-2 text-sm capitalize outline-none transition",
                        isSelected ? "league-pill-active" : "text-muted-foreground hover:bg-accent"
                      )
                    }
                  >
                    {t}
                  </Tab>
                ))}
              </TabList>

              {TABS.map((t) => (
                <TabPanel key={t} id={t} className="min-w-0 outline-none">
                  {activeTab === t ? body : null}
                </TabPanel>
              ))}
            </Tabs>
          </section>
        </div>
      </main>
    </div>
  );
}
