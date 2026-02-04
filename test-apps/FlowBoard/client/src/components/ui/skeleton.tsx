import { cn } from "@/lib/utils";

/**
 * Skeleton — Animated placeholder for loading states.
 *
 * Uses the `animate-skeleton` keyframe (opacity pulse) by default.
 * Apply the `.skeleton` CSS class from globals.css instead if you
 * prefer the gradient shimmer variant.
 *
 * @example
 *   <Skeleton className="h-4 w-48" />           // text line
 *   <Skeleton className="h-10 w-10 rounded-full" /> // avatar
 *   <Skeleton className="h-32 w-full" />         // card
 */
function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "animate-skeleton rounded-md bg-surface-tertiary",
        className
      )}
      {...props}
    />
  );
}

export { Skeleton };
