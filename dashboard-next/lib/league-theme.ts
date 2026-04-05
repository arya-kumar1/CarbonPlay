import { League } from "@/lib/types";

export interface LeagueTheme {
  league: League;
  label: string;
  icon: "flame" | "snowflake" | "shield";
  subtitle: string;
  primary: string;
  secondary: string;
  accent: string;
  chartPalette: [string, string, string, string];
  map: {
    marker: string;
    markerHighlight: string;
    route: string;
    heat: [string, string, string];
  };
  cardClass: string;
  headerClass: string;
  buttonGlowClass: string;
  borderClass: string;
  textureClass: string;
  motion: {
    stiffness: number;
    damping: number;
  };
  cssVars: React.CSSProperties;
}

export const LEAGUE_THEMES: Record<League, LeagueTheme> = {
  NBA: {
    league: "NBA",
    label: "NBA Sustainable Scheduler",
    icon: "flame",
    subtitle: "Carbon-aware schedule optimization and travel efficiency planning.",
    primary: "#f97316",
    secondary: "#fb923c",
    accent: "#22d3ee",
    chartPalette: ["#f97316", "#fb923c", "#22d3ee", "#f59e0b"],
    map: {
      marker: "#f8fafc",
      markerHighlight: "#f97316",
      route: "#f97316",
      heat: ["#fb923c", "#f97316", "#f59e0b"]
    },
    cardClass: "league-card-nba",
    headerClass: "league-hero-nba",
    buttonGlowClass: "league-glow-nba",
    borderClass: "league-border-nba",
    textureClass: "league-texture-nba",
    motion: { stiffness: 280, damping: 24 },
    cssVars: {
      ["--primary" as string]: "24 95% 53%",
      ["--secondary" as string]: "24 92% 92%",
      ["--accent" as string]: "188 95% 52%",
      ["--ring" as string]: "24 95% 53%",
      ["--league-gradient" as string]: "linear-gradient(140deg, rgba(249,115,22,0.15), rgba(6,182,212,0.08))"
    }
  },
  NHL: {
    league: "NHL",
    label: "NHL Sustainable Scheduler",
    icon: "snowflake",
    subtitle: "Carbon-aware schedule optimization and travel efficiency planning.",
    primary: "#38bdf8",
    secondary: "#7dd3fc",
    accent: "#94a3b8",
    chartPalette: ["#38bdf8", "#60a5fa", "#94a3b8", "#22d3ee"],
    map: {
      marker: "#e2e8f0",
      markerHighlight: "#38bdf8",
      route: "#7dd3fc",
      heat: ["#0ea5e9", "#38bdf8", "#a5f3fc"]
    },
    cardClass: "league-card-nhl",
    headerClass: "league-hero-nhl",
    buttonGlowClass: "league-glow-nhl",
    borderClass: "league-border-nhl",
    textureClass: "league-texture-nhl",
    motion: { stiffness: 340, damping: 30 },
    cssVars: {
      ["--primary" as string]: "198 93% 60%",
      ["--secondary" as string]: "210 30% 92%",
      ["--accent" as string]: "210 19% 70%",
      ["--ring" as string]: "198 93% 60%",
      ["--league-gradient" as string]: "linear-gradient(145deg, rgba(56,189,248,0.12), rgba(148,163,184,0.07))"
    }
  },
  NFL: {
    league: "NFL",
    label: "NFL Sustainable Scheduler",
    icon: "shield",
    subtitle: "Strategic, tactical schedule planning with league-operations precision.",
    primary: "#166534",
    secondary: "#dcfce7",
    accent: "#a3e635",
    chartPalette: ["#166534", "#65a30d", "#14532d", "#84cc16"],
    map: {
      marker: "#f8fafc",
      markerHighlight: "#84cc16",
      route: "#166534",
      heat: ["#14532d", "#166534", "#84cc16"]
    },
    cardClass: "league-card-nfl",
    headerClass: "league-hero-nfl",
    buttonGlowClass: "league-glow-nfl",
    borderClass: "league-border-nfl",
    textureClass: "league-texture-nfl",
    motion: { stiffness: 320, damping: 32 },
    cssVars: {
      ["--primary" as string]: "142 61% 25%",
      ["--secondary" as string]: "138 76% 96%",
      ["--accent" as string]: "84 81% 56%",
      ["--ring" as string]: "142 61% 25%",
      ["--league-gradient" as string]: "linear-gradient(145deg, rgba(22,101,52,0.16), rgba(132,204,22,0.08))"
    }
  }
};

export function getLeagueTheme(league: League): LeagueTheme {
  return LEAGUE_THEMES[league];
}
