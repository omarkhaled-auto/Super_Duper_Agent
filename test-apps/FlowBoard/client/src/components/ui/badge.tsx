import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

/**
 * Badge — FlowBoard Design System
 *
 * Variants:
 *   default        — neutral bg, secondary text
 *   priority-urgent — urgent red muted bg
 *   priority-high   — orange muted bg
 *   priority-medium — yellow muted bg
 *   priority-low    — blue muted bg
 *   status         — neutral with colored dot (via CSS class)
 *   outline        — bordered, transparent bg
 */
const badgeVariants = cva(
  [
    "inline-flex items-center gap-1",
    "rounded-full font-medium font-body",
    "transition-colors duration-fast",
    "select-none",
  ].join(" "),
  {
    variants: {
      variant: {
        default: "bg-secondary text-text-secondary",
        "priority-urgent":
          "bg-[hsl(var(--color-priority-urgent)/0.15)] text-urgent",
        "priority-high":
          "bg-[hsl(var(--color-priority-high)/0.15)] text-high",
        "priority-medium":
          "bg-[hsl(var(--color-priority-medium)/0.15)] text-medium",
        "priority-low":
          "bg-[hsl(var(--color-priority-low)/0.15)] text-low",
        status: "bg-secondary text-text-secondary",
        outline: "border border-border text-text-secondary bg-transparent",
      },
      size: {
        sm: "px-1.5 py-px text-[10px]",
        md: "px-2 py-0.5 text-xs",
        lg: "px-2.5 py-1 text-xs",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(badgeVariants({ variant, size }), className)}
        {...props}
      />
    );
  }
);
Badge.displayName = "Badge";

export { Badge, badgeVariants };
