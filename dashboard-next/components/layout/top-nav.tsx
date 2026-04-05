"use client";

import { Download, Flame, RefreshCw, Shield, Snowflake } from "lucide-react";
import { motion } from "motion/react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/theme-toggle";
import { LeagueTheme } from "@/lib/league-theme";

interface TopNavProps {
  league: string;
  theme: LeagueTheme;
  onRefresh: () => void;
  onExport: () => void;
  isLoading: boolean;
}

export function TopNav({ league, theme, onRefresh, onExport, isLoading }: TopNavProps) {
  const LeagueIcon = theme.icon === "flame" ? Flame : theme.icon === "snowflake" ? Snowflake : Shield;

  return (
    <header className="sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur-xl">
      <div className="container flex h-16 items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <motion.div
            key={league}
            initial={{ scale: 0.9, opacity: 0.6 }}
            animate={{ scale: 1, opacity: 1 }}
            className={`h-8 w-8 rounded-lg ${theme.buttonGlowClass}`}
            style={{ background: `linear-gradient(135deg, ${theme.primary}, ${theme.accent})` }}
          />
          <div>
            <h1 className="text-base font-semibold">CarbonPlay</h1>
            <p className="text-sm text-muted-foreground">Sustainable Scheduler</p>
          </div>
          <div className="hidden h-5 w-px bg-border/80 md:block" />
          <Badge className={`ml-1 flex items-center gap-1 ${theme.borderClass}`}>
            <LeagueIcon className="h-3 w-3" />
            {league}
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={onRefresh} className={theme.borderClass}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button variant="secondary" size="sm" onClick={onExport}>
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
