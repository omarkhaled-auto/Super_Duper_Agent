import { Skeleton } from "@/components/ui/skeleton";

// =============================================================================
// BoardSkeleton -- Loading placeholder for the kanban board
//
// Renders 5 column skeletons with varying card counts and shimmer animation.
// =============================================================================

const COLUMN_CARD_COUNTS = [3, 4, 2, 5, 3];

export function BoardSkeleton() {
  return (
    <div className="flex h-full gap-4 p-6 overflow-x-auto">
      {COLUMN_CARD_COUNTS.map((cardCount, colIndex) => (
        <div
          key={colIndex}
          className="flex flex-col shrink-0 w-kanban-col min-w-kanban-col"
        >
          {/* Column header skeleton */}
          <div className="flex items-center gap-2 px-2 pb-3">
            <Skeleton className="h-3 w-3 rounded-full" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-5 w-6 rounded-full" />
          </div>

          {/* Card skeletons */}
          <div className="flex flex-col gap-2">
            {Array.from({ length: cardCount }).map((_, cardIndex) => (
              <div
                key={cardIndex}
                className="rounded-lg border border-border-subtle bg-surface-elevated p-3 space-y-2.5"
              >
                {/* Title line */}
                <Skeleton
                  className="h-4"
                  style={{ width: `${60 + Math.random() * 35}%` }}
                />

                {/* Second line (sometimes) */}
                {cardIndex % 2 === 0 && (
                  <Skeleton
                    className="h-3"
                    style={{ width: `${40 + Math.random() * 30}%` }}
                  />
                )}

                {/* Bottom row: badge + avatar */}
                <div className="flex items-center justify-between pt-1">
                  <Skeleton className="h-5 w-14 rounded-full" />
                  <Skeleton className="h-6 w-6 rounded-full" />
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
