import { League } from "@/lib/types";

export interface TeamMeta {
  color: string;
  city: string;
  arena: string;
  logo: string;
}

const NBA_META: Record<string, TeamMeta> = {
  ATL: { color: "#E03A3E", city: "Atlanta", arena: "State Farm Arena", logo: "/nbalogos/hawks.png" },
  BOS: { color: "#007A33", city: "Boston", arena: "TD Garden", logo: "/nbalogos/celtics.svg" },
  BKN: { color: "#111111", city: "Brooklyn", arena: "Barclays Center", logo: "/nbalogos/nets.png" },
  CHA: { color: "#1D1160", city: "Charlotte", arena: "Spectrum Center", logo: "/nbalogos/hornets.png" },
  CHI: { color: "#CE1141", city: "Chicago", arena: "United Center", logo: "/nbalogos/bulls.png" },
  CLE: { color: "#860038", city: "Cleveland", arena: "Rocket Arena", logo: "/nbalogos/cavs.png" },
  DAL: { color: "#00538C", city: "Dallas", arena: "American Airlines Center", logo: "/nbalogos/mavs.png" },
  DEN: { color: "#0E2240", city: "Denver", arena: "Ball Arena", logo: "/nbalogos/nuggets.png" },
  DET: { color: "#C8102E", city: "Detroit", arena: "Little Caesars Arena", logo: "/nbalogos/pistons.png" },
  GSW: { color: "#1D428A", city: "San Francisco", arena: "Chase Center", logo: "/nbalogos/warriors.png" },
  HOU: { color: "#CE1141", city: "Houston", arena: "Toyota Center", logo: "/nbalogos/rockets.svg" },
  IND: { color: "#002D62", city: "Indianapolis", arena: "Gainbridge Fieldhouse", logo: "/nbalogos/pacers.png" },
  LAC: { color: "#C8102E", city: "Inglewood", arena: "Intuit Dome", logo: "/nbalogos/clippers.png" },
  LAL: { color: "#552583", city: "Los Angeles", arena: "Crypto.com Arena", logo: "/nbalogos/lakers.png" },
  MEM: { color: "#5D76A9", city: "Memphis", arena: "FedExForum", logo: "/nbalogos/grizzlies.png" },
  MIA: { color: "#98002E", city: "Miami", arena: "Kaseya Center", logo: "/nbalogos/heat.png" },
  MIL: { color: "#00471B", city: "Milwaukee", arena: "Fiserv Forum", logo: "/nbalogos/bucks.png" },
  MIN: { color: "#0C2340", city: "Minneapolis", arena: "Target Center", logo: "/nbalogos/timberwolves.png" },
  NOP: { color: "#0C2340", city: "New Orleans", arena: "Smoothie King Center", logo: "/nbalogos/pelicans.png" },
  NYK: { color: "#006BB6", city: "New York", arena: "Madison Square Garden", logo: "/nbalogos/knicks.png" },
  OKC: { color: "#007AC1", city: "Oklahoma City", arena: "Paycom Center", logo: "/nbalogos/thunder.png" },
  ORL: { color: "#0077C0", city: "Orlando", arena: "Kia Center", logo: "/nbalogos/magic.png" },
  PHI: { color: "#006BB6", city: "Philadelphia", arena: "Xfinity Mobile Arena", logo: "/nbalogos/76ers.png" },
  PHX: { color: "#1D1160", city: "Phoenix", arena: "Footprint Center", logo: "/nbalogos/suns.png" },
  POR: { color: "#E03A3E", city: "Portland", arena: "Moda Center", logo: "/nbalogos/blazers.png" },
  SAC: { color: "#5A2D81", city: "Sacramento", arena: "Golden 1 Center", logo: "/nbalogos/kings.png" },
  SAS: { color: "#8A8D8F", city: "San Antonio", arena: "Frost Bank Center", logo: "/nbalogos/spurs.svg" },
  TOR: { color: "#CE1141", city: "Toronto", arena: "Scotiabank Arena", logo: "/nbalogos/raptors.png" },
  UTA: { color: "#002B5C", city: "Salt Lake City", arena: "Delta Center", logo: "/nbalogos/jazz.svg" },
  WAS: { color: "#002B5C", city: "Washington", arena: "Capital One Arena", logo: "/nbalogos/wizards.png" }
};

const NHL_META: Record<string, TeamMeta> = {
  ANA: { color: "#F47A38", city: "Anaheim", arena: "Honda Center", logo: "/nhllogos/ducks.png" },
  BOS: { color: "#FFB81C", city: "Boston", arena: "TD Garden", logo: "/nhllogos/bruins.png" },
  BUF: { color: "#003087", city: "Buffalo", arena: "KeyBank Center", logo: "/nhllogos/sabres.png" },
  CAR: { color: "#CC0000", city: "Raleigh", arena: "Lenovo Center", logo: "/nhllogos/hurricanes.png" },
  CBJ: { color: "#002654", city: "Columbus", arena: "Nationwide Arena", logo: "/nhllogos/bluejackets.png" },
  CGY: { color: "#C8102E", city: "Calgary", arena: "Scotiabank Saddledome", logo: "/nhllogos/flames.png" },
  CHI: { color: "#CF0A2C", city: "Chicago", arena: "United Center", logo: "/nhllogos/blackhawks.png" },
  COL: { color: "#6F263D", city: "Denver", arena: "Ball Arena", logo: "/nhllogos/avalanche.png" },
  DAL: { color: "#006847", city: "Dallas", arena: "American Airlines Center", logo: "/nhllogos/stars.png" },
  DET: { color: "#CE1126", city: "Detroit", arena: "Little Caesars Arena", logo: "/nhllogos/redwings.png" },
  EDM: { color: "#FF4C00", city: "Edmonton", arena: "Rogers Place", logo: "/nhllogos/oilers.png" },
  FLA: { color: "#C8102E", city: "Sunrise", arena: "Amerant Bank Arena", logo: "/nhllogos/panthers.png" },
  LAK: { color: "#111111", city: "Los Angeles", arena: "Crypto.com Arena", logo: "/nhllogos/kings.png" },
  MIN: { color: "#154734", city: "Saint Paul", arena: "Xcel Energy Center", logo: "/nhllogos/wild.png" },
  MTL: { color: "#AF1E2D", city: "Montreal", arena: "Bell Centre", logo: "/nhllogos/canadiens.png" },
  NJD: { color: "#CE1126", city: "Newark", arena: "Prudential Center", logo: "/nhllogos/devils.png" },
  NSH: { color: "#FFB81C", city: "Nashville", arena: "Bridgestone Arena", logo: "/nhllogos/predators.png" },
  NYI: { color: "#F47D30", city: "Elmont", arena: "UBS Arena", logo: "/nhllogos/islanders.png" },
  NYR: { color: "#0038A8", city: "New York", arena: "Madison Square Garden", logo: "/nhllogos/rangers.png" },
  OTT: { color: "#C52032", city: "Ottawa", arena: "Canadian Tire Centre", logo: "/nhllogos/senators.png" },
  PHI: { color: "#F74902", city: "Philadelphia", arena: "Xfinity Mobile Arena", logo: "/nhllogos/flyers.png" },
  PIT: { color: "#FCB514", city: "Pittsburgh", arena: "PPG Paints Arena", logo: "/nhllogos/penguins.png" },
  SEA: { color: "#005C73", city: "Seattle", arena: "Climate Pledge Arena", logo: "/nhllogos/kraken.png" },
  SJS: { color: "#006D75", city: "San Jose", arena: "SAP Center", logo: "/nhllogos/sharks.png" },
  STL: { color: "#002F87", city: "St. Louis", arena: "Enterprise Center", logo: "/nhllogos/blues.png" },
  TBL: { color: "#002868", city: "Tampa", arena: "Benchmark International Arena", logo: "/nhllogos/lightning.svg" },
  TOR: { color: "#003E7E", city: "Toronto", arena: "Scotiabank Arena", logo: "/nhllogos/mapleleafs.png" },
  UTA: { color: "#6EA2B9", city: "Salt Lake City", arena: "Delta Center", logo: "/nhllogos/mammoth.png" },
  VAN: { color: "#00205B", city: "Vancouver", arena: "Rogers Arena", logo: "/nhllogos/canucks.png" },
  VGK: { color: "#B4975A", city: "Las Vegas", arena: "T-Mobile Arena", logo: "/nhllogos/goldenknights.png" },
  WPG: { color: "#041E42", city: "Winnipeg", arena: "Canada Life Centre", logo: "/nhllogos/jets.png" },
  WSH: { color: "#C8102E", city: "Washington", arena: "Capital One Arena", logo: "/nhllogos/capitals.png" }
};

const NFL_META: Record<string, TeamMeta> = {
  ARI: { color: "#97233F", city: "Glendale", arena: "State Farm Stadium", logo: "/nfllogos/cardinals.png" },
  ATL: { color: "#A71930", city: "Atlanta", arena: "Mercedes-Benz Stadium", logo: "/nfllogos/falcons.png" },
  BAL: { color: "#241773", city: "Baltimore", arena: "M&T Bank Stadium", logo: "/nfllogos/ravens.png" },
  BUF: { color: "#00338D", city: "Orchard Park", arena: "Highmark Stadium", logo: "/nfllogos/bills.png" },
  CAR: { color: "#0085CA", city: "Charlotte", arena: "Bank of America Stadium", logo: "/nfllogos/panthers.png" },
  CHI: { color: "#0B162A", city: "Chicago", arena: "Soldier Field", logo: "/nfllogos/bears.png" },
  CIN: { color: "#FB4F14", city: "Cincinnati", arena: "Paycor Stadium", logo: "/nfllogos/bengals.png" },
  CLE: { color: "#FF3C00", city: "Cleveland", arena: "Huntington Bank Field", logo: "/nfllogos/browns.png" },
  DAL: { color: "#003594", city: "Arlington", arena: "AT&T Stadium", logo: "/nfllogos/cowboys.png" },
  DEN: { color: "#FB4F14", city: "Denver", arena: "Empower Field at Mile High", logo: "/nfllogos/broncos.png" },
  DET: { color: "#0076B6", city: "Detroit", arena: "Ford Field", logo: "/nfllogos/lions.png" },
  GB: { color: "#203731", city: "Green Bay", arena: "Lambeau Field", logo: "/nfllogos/packers.png" },
  HOU: { color: "#03202F", city: "Houston", arena: "NRG Stadium", logo: "/nfllogos/texans.png" },
  IND: { color: "#002C5F", city: "Indianapolis", arena: "Lucas Oil Stadium", logo: "/nfllogos/colts.png" },
  JAX: { color: "#006778", city: "Jacksonville", arena: "EverBank Stadium", logo: "/nfllogos/jaguars.png" },
  KC: { color: "#E31837", city: "Kansas City", arena: "GEHA Field at Arrowhead Stadium", logo: "/nfllogos/chiefs.png" },
  LAC: { color: "#0080C6", city: "Inglewood", arena: "SoFi Stadium", logo: "/nfllogos/chargers.png" },
  LAR: { color: "#003594", city: "Inglewood", arena: "SoFi Stadium", logo: "/nfllogos/rams.png" },
  LV: { color: "#000000", city: "Las Vegas", arena: "Allegiant Stadium", logo: "/nfllogos/raiders.png" },
  MIA: { color: "#008E97", city: "Miami Gardens", arena: "Hard Rock Stadium", logo: "/nfllogos/dolphins.png" },
  MIN: { color: "#4F2683", city: "Minneapolis", arena: "U.S. Bank Stadium", logo: "/nfllogos/vikings.png" },
  NE: { color: "#002244", city: "Foxborough", arena: "Gillette Stadium", logo: "/nfllogos/patriots.png" },
  NO: { color: "#D3BC8D", city: "New Orleans", arena: "Caesars Superdome", logo: "/nfllogos/saints.png" },
  NYG: { color: "#0B2265", city: "East Rutherford", arena: "MetLife Stadium", logo: "/nfllogos/giants.png" },
  NYJ: { color: "#125740", city: "East Rutherford", arena: "MetLife Stadium", logo: "/nfllogos/jets.png" },
  PHI: { color: "#004C54", city: "Philadelphia", arena: "Lincoln Financial Field", logo: "/nfllogos/eagles.png" },
  PIT: { color: "#FFB612", city: "Pittsburgh", arena: "Acrisure Stadium", logo: "/nfllogos/steelers.png" },
  SEA: { color: "#002244", city: "Seattle", arena: "Lumen Field", logo: "/nfllogos/seahawks.png" },
  SF: { color: "#AA0000", city: "Santa Clara", arena: "Levi's Stadium", logo: "/nfllogos/49ers.png" },
  TB: { color: "#D50A0A", city: "Tampa", arena: "Raymond James Stadium", logo: "/nfllogos/bucs.png" },
  TEN: { color: "#4B92DB", city: "Nashville", arena: "Nissan Stadium", logo: "/nfllogos/titans.png" },
  WAS: { color: "#5A1414", city: "Landover", arena: "Northwest Stadium", logo: "/nfllogos/commanders.png" }
};

export function getTeamMeta(team: string, league: League): TeamMeta {
  const meta = league === "NHL" ? NHL_META[team] : league === "NFL" ? NFL_META[team] : NBA_META[team];
  if (meta) return meta;
  return {
    color: league === "NHL" ? "#38BDF8" : "#F97316",
    city: team,
    arena: "Home Arena",
    logo: ""
  };
}
