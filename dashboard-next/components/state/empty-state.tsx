import { Card, CardContent } from "@/components/ui/card";
import { LeagueTheme } from "@/lib/league-theme";

export function EmptyState({ message, theme }: { message: string; theme: LeagueTheme }) {
  return (
    <Card className={`border-dashed ${theme.cardClass} ${theme.borderClass}`}>
      <CardContent className="flex h-72 items-center justify-center text-center">
        <p className="max-w-md text-sm text-muted-foreground">
          {theme.league === "NBA" ? "Fast-break mode waiting for data. " : "Rink view is waiting for data. "}
          {message}
        </p>
      </CardContent>
    </Card>
  );
}
