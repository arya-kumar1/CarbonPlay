import { League } from "@/lib/types";
import { getTeamMeta } from "@/lib/team-meta";

const TEAM_COLORS: Record<string, string> = {
  ATL: "#E03A3E",
  BOS: "#007A33",
  BKN: "#111111",
  CHA: "#1D1160",
  CHI: "#CE1141",
  CLE: "#860038",
  DAL: "#00538C",
  DEN: "#0E2240",
  DET: "#C8102E",
  GSW: "#1D428A",
  HOU: "#CE1141",
  IND: "#002D62",
  LAC: "#C8102E",
  LAL: "#552583",
  MEM: "#5D76A9",
  MIA: "#98002E",
  MIL: "#00471B",
  MIN: "#0C2340",
  NOP: "#0C2340",
  NYK: "#006BB6",
  OKC: "#007AC1",
  ORL: "#0077C0",
  PHI: "#006BB6",
  PHX: "#1D1160",
  POR: "#E03A3E",
  SAC: "#5A2D81",
  SAS: "#8A8D8F",
  TOR: "#CE1141",
  UTA: "#002B5C",
  WAS: "#002B5C",
  ANA: "#F47A38",
  BUF: "#003087",
  CAR: "#CC0000",
  CBJ: "#002654",
  CGY: "#C8102E",
  COL: "#6F263D",
  EDM: "#FF4C00",
  FLA: "#C8102E",
  LAK: "#111111",
  MTL: "#AF1E2D",
  NJD: "#CE1126",
  NSH: "#FFB81C",
  NYI: "#F47D30",
  NYR: "#0038A8",
  OTT: "#C52032",
  PIT: "#FCB514",
  SEA: "#005C73",
  SJS: "#006D75",
  STL: "#002F87",
  TBL: "#002868",
  VAN: "#00205B",
  VGK: "#B4975A",
  WPG: "#041E42",
  WSH: "#C8102E"
};

const NBA_FALLBACK = ["#F97316", "#FB923C", "#F59E0B", "#EA580C", "#22D3EE", "#0EA5E9"];
const NHL_FALLBACK = ["#38BDF8", "#60A5FA", "#22D3EE", "#0284C7", "#94A3B8", "#0EA5E9"];

function hashCode(input: string): number {
  let h = 0;
  for (let i = 0; i < input.length; i += 1) {
    h = (h << 5) - h + input.charCodeAt(i);
    h |= 0;
  }
  return Math.abs(h);
}

export function getTeamColor(team: string, league: League): string {
  const fromMeta = getTeamMeta(team, league).color;
  if (fromMeta) return fromMeta;
  if (TEAM_COLORS[team]) return TEAM_COLORS[team];
  const palette = league === "NHL" ? NHL_FALLBACK : NBA_FALLBACK;
  return palette[hashCode(team) % palette.length];
}

export function hexToRgba(hex: string, alpha: number): string {
  const normalized = hex.replace("#", "");
  const value = normalized.length === 3
    ? normalized.split("").map((c) => `${c}${c}`).join("")
    : normalized;
  const r = Number.parseInt(value.slice(0, 2), 16);
  const g = Number.parseInt(value.slice(2, 4), 16);
  const b = Number.parseInt(value.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
