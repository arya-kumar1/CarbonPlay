import { Skeleton } from "@/components/ui/skeleton";
import { LeagueTheme } from "@/lib/league-theme";

export function SkeletonGrid({ theme }: { theme: LeagueTheme }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className={`h-28 ${theme.cardClass}`} />
        ))}
      </div>
      <Skeleton className={`h-[360px] ${theme.cardClass}`} />
    </div>
  );
}
