"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

// =============================================================================
// TablePagination -- Pagination bar for the task list table.
//
// Shows:
//   - Items per page selector (10 / 25 / 50)
//   - "Showing X-Y of Z tasks"
//   - Previous / page numbers / Next navigation
// =============================================================================

const PAGE_SIZE_OPTIONS = [10, 25, 50] as const;

interface TablePaginationProps {
  page: number;
  limit: number;
  total: number;
  onPageChange: (page: number) => void;
  onLimitChange: (limit: number) => void;
  className?: string;
}

/**
 * Generate an array of page numbers to display, with ellipsis markers (-1).
 * Always shows first, last, current, and 1 page on each side of current.
 */
function getPageNumbers(current: number, totalPages: number): number[] {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, i) => i + 1);
  }

  const pages: number[] = [];
  const addPage = (p: number) => {
    if (p >= 1 && p <= totalPages && !pages.includes(p)) {
      pages.push(p);
    }
  };

  // Always include first page
  addPage(1);

  // Pages around current
  for (let i = current - 1; i <= current + 1; i++) {
    addPage(i);
  }

  // Always include last page
  addPage(totalPages);

  // Sort and insert ellipsis markers
  pages.sort((a, b) => a - b);

  const result: number[] = [];
  for (let i = 0; i < pages.length; i++) {
    if (i > 0 && pages[i] - pages[i - 1] > 1) {
      result.push(-1); // ellipsis marker
    }
    result.push(pages[i]);
  }

  return result;
}

export function TablePagination({
  page,
  limit,
  total,
  onPageChange,
  onLimitChange,
  className,
}: TablePaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / limit));
  const startItem = total === 0 ? 0 : (page - 1) * limit + 1;
  const endItem = Math.min(page * limit, total);
  const pageNumbers = getPageNumbers(page, totalPages);

  const canPrev = page > 1;
  const canNext = page < totalPages;

  return (
    <div
      className={cn(
        "flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between",
        "px-3 py-3 border-t border-border",
        className,
      )}
    >
      {/* ---- Left side: per-page selector + count ---- */}
      <div className="flex items-center gap-3 text-xs text-text-tertiary">
        <div className="flex items-center gap-1.5">
          <span className="whitespace-nowrap">Rows per page</span>
          <Select
            value={String(limit)}
            onValueChange={(v) => onLimitChange(Number(v))}
          >
            <SelectTrigger className="h-7 w-[4.5rem] border-border bg-transparent text-xs px-2 [&>svg]:h-3 [&>svg]:w-3">
              <SelectValue />
            </SelectTrigger>
            <SelectContent align="start" className="min-w-[4.5rem]">
              {PAGE_SIZE_OPTIONS.map((size) => (
                <SelectItem key={size} value={String(size)} className="text-xs">
                  {size}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <span className="whitespace-nowrap">
          {total === 0
            ? "No tasks"
            : `Showing ${startItem}\u2013${endItem} of ${total} tasks`}
        </span>
      </div>

      {/* ---- Right side: page navigation ---- */}
      <div className="flex items-center gap-1">
        {/* Previous */}
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          disabled={!canPrev}
          onClick={() => onPageChange(page - 1)}
          aria-label="Previous page"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>

        {/* Page numbers */}
        {pageNumbers.map((p, idx) =>
          p === -1 ? (
            <span
              key={`ellipsis-${idx}`}
              className="flex h-7 w-7 items-center justify-center text-xs text-text-quaternary select-none"
              aria-hidden="true"
            >
              ...
            </span>
          ) : (
            <Button
              key={p}
              variant={p === page ? "default" : "ghost"}
              size="icon"
              className={cn(
                "h-7 w-7 text-xs",
                p === page &&
                  "pointer-events-none",
              )}
              onClick={() => onPageChange(p)}
              aria-label={`Page ${p}`}
              aria-current={p === page ? "page" : undefined}
            >
              {p}
            </Button>
          ),
        )}

        {/* Next */}
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          disabled={!canNext}
          onClick={() => onPageChange(page + 1)}
          aria-label="Next page"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
