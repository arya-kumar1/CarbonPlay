"use client";

import { motion } from "motion/react";
import { Card, CardContent } from "@/components/ui/card";
import { LeagueTheme } from "@/lib/league-theme";

interface KpiCardProps {
  label: string;
  value: string;
  subtext?: string;
  theme: LeagueTheme;
}

export function KpiCard({ label, value, subtext, theme }: KpiCardProps) {
  return (
    <motion.div
      whileHover={{ y: -3 }}
      transition={{ type: "spring", stiffness: theme.motion.stiffness, damping: theme.motion.damping }}
    >
      <Card className={`${theme.cardClass} ${theme.borderClass}`}>
        <CardContent className="p-4">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
          <p className="mt-2 text-2xl font-semibold">{value}</p>
          {subtext ? <p className="mt-1 text-xs text-muted-foreground">{subtext}</p> : null}
        </CardContent>
      </Card>
    </motion.div>
  );
}
