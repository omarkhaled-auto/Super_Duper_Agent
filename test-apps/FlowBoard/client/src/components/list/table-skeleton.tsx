"use client";

import { Skeleton } from "@/components/ui/skeleton";

// =============================================================================
// TableSkeleton -- Loading placeholder for the task table.
// Renders a header row + 10 shimmer rows to match the real table layout.
// =============================================================================

const SKELETON_ROWS = 10;

export function TableSkeleton() {
  return (
    <div className="w-full overflow-x-auto">
      <table className="w-full min-w-[900px] table-fixed border-collapse">
        {/* ---- Header ---- */}
        <thead>
          <tr className="border-b border-border">
            <th className="w-10 px-3 py-3">
              <Skeleton className="h-4 w-4 rounded-sm" />
            </th>
            <th className="w-[30%] px-3 py-3 text-left">
              <Skeleton className="h-3.5 w-16" />
            </th>
            <th className="w-[14%] px-3 py-3 text-left">
              <Skeleton className="h-3.5 w-14" />
            </th>
            <th className="w-[12%] px-3 py-3 text-left">
              <Skeleton className="h-3.5 w-14" />
            </th>
            <th className="w-[16%] px-3 py-3 text-left">
              <Skeleton className="h-3.5 w-16" />
            </th>
            <th className="w-[14%] px-3 py-3 text-left">
              <Skeleton className="h-3.5 w-16" />
            </th>
            <th className="w-[14%] px-3 py-3 text-left">
              <Skeleton className="h-3.5 w-16" />
            </th>
          </tr>
        </thead>

        {/* ---- Body rows ---- */}
        <tbody>
          {Array.from({ length: SKELETON_ROWS }).map((_, i) => (
            <tr key={i} className="border-b border-border-subtle">
              {/* Checkbox */}
              <td className="px-3 py-3">
                <Skeleton className="h-4 w-4 rounded-sm" />
              </td>
              {/* Title */}
              <td className="px-3 py-3">
                <Skeleton
                  className="h-4"
                  style={{ width: `${55 + Math.random() * 30}%` }}
                />
              </td>
              {/* Status */}
              <td className="px-3 py-3">
                <Skeleton className="h-5 w-20 rounded-full" />
              </td>
              {/* Priority */}
              <td className="px-3 py-3">
                <Skeleton className="h-5 w-16 rounded-full" />
              </td>
              {/* Assignee */}
              <td className="px-3 py-3">
                <div className="flex items-center gap-2">
                  <Skeleton className="h-6 w-6 rounded-full" />
                  <Skeleton className="h-3.5 w-20" />
                </div>
              </td>
              {/* Due date */}
              <td className="px-3 py-3">
                <Skeleton className="h-3.5 w-20" />
              </td>
              {/* Created */}
              <td className="px-3 py-3">
                <Skeleton className="h-3.5 w-24" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
