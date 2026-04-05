"use client";

import { Flame, Shield, Snowflake, Trophy } from "lucide-react";
import { motion } from "motion/react";
import { LeagueTheme } from "@/lib/league-theme";
import { Card, CardContent } from "@/components/ui/card";

export function LeagueHero({ theme }: { theme: LeagueTheme }) {
  const Icon = theme.icon === "flame" ? Flame : theme.icon === "snowflake" ? Snowflake : Shield;

  return (
    <motion.div
      key={theme.league}
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.24 }}
    >
      <Card className={`overflow-hidden ${theme.headerClass} ${theme.borderClass}`}>
        <CardContent className="relative p-5">
          <div className="absolute inset-0 opacity-60" style={{ background: "var(--league-gradient)" }} />
          <div className="relative flex items-center justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">League</p>
              <h2 className="mt-1 text-xl font-semibold">{theme.label}</h2>
              <p className="mt-1 text-sm text-muted-foreground">{theme.subtitle}</p>
            </div>
            <div className="flex items-center gap-2">
              <Icon className="h-6 w-6" />
              <Trophy className="h-5 w-5 text-muted-foreground" />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
