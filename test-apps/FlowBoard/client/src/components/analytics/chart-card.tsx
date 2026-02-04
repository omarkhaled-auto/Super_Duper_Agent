"use client";

import * as React from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

/**
 * ChartCard -- Consistent wrapper for analytics chart tiles.
 *
 * Provides:
 *  - Card with title and optional description
 *  - Loading skeleton state
 *  - Consistent height for chart area (min 280px)
 *  - Dark/light theme aware via design system tokens
 */
interface ChartCardProps {
  title: string;
  description?: string;
  isLoading?: boolean;
  className?: string;
  children: React.ReactNode;
}

export function ChartCard({
  title,
  description,
  isLoading = false,
  className,
  children,
}: ChartCardProps) {
  return (
    <Card className={cn("flex flex-col overflow-hidden", className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-semibold">{title}</CardTitle>
        {description && (
          <CardDescription className="text-xs">{description}</CardDescription>
        )}
      </CardHeader>
      <CardContent className="flex-1 pt-0 pb-4">
        {isLoading ? (
          <ChartSkeleton />
        ) : (
          <div className="h-[280px] w-full">{children}</div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Loading skeleton that mimics a chart shape.
 * Shows animated placeholder bars/lines for visual loading feedback.
 */
function ChartSkeleton() {
  return (
    <div className="h-[280px] w-full flex flex-col justify-end gap-2 p-4">
      {/* Chart area skeleton */}
      <div className="flex-1 flex items-end gap-3 pb-2">
        <Skeleton className="w-full h-[40%] rounded-sm" />
        <Skeleton className="w-full h-[65%] rounded-sm" />
        <Skeleton className="w-full h-[50%] rounded-sm" />
        <Skeleton className="w-full h-[80%] rounded-sm" />
        <Skeleton className="w-full h-[55%] rounded-sm" />
        <Skeleton className="w-full h-[70%] rounded-sm" />
        <Skeleton className="w-full h-[45%] rounded-sm" />
      </div>
      {/* X-axis skeleton */}
      <div className="flex gap-3">
        {Array.from({ length: 7 }).map((_, i) => (
          <Skeleton key={i} className="h-3 w-full rounded-sm" />
        ))}
      </div>
    </div>
  );
}
