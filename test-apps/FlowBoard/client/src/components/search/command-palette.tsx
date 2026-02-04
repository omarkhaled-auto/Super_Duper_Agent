"use client";

import React, { useCallback, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  Clock,
  X,
  FileText,
  FolderKanban,
  Users,
  Loader2,
} from "lucide-react";

import { cn } from "@/lib/utils";
import {
  Dialog,
  DialogPortal,
  DialogOverlay,
} from "@/components/ui/dialog";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SearchResultItem } from "@/components/search/search-result-item";
import { useSearch } from "@/hooks/use-search";
import type { SearchResultItem as SearchResultItemType } from "@/hooks/use-search";

// =============================================================================
// CommandPalette — Linear-inspired Cmd+K search modal
//
// Features:
//   - Full-width dialog, centered, max-w-xl
//   - Large search input at top with magnifying glass icon (auto-focused)
//   - Debounced search (300ms) calling GET /api/search?q=
//   - Results grouped by section: Tasks, Projects, Members
//   - Keyboard navigation: Up/Down arrows, Enter to select, Escape to close
//   - Recent searches shown when query is empty
//   - Loading skeleton, empty state, error state
//   - On select: navigates to the appropriate route and closes palette
// =============================================================================

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const {
    query,
    setQuery,
    results,
    flatResults,
    selectedIndex,
    setSelectedIndex,
    isLoading,
    isDebouncing,
    error,
    recentSearches,
    addRecent,
    clearRecents,
    reset,
  } = useSearch(300);

  // ---------------------------------------------------------------------------
  // Close handler — resets search state
  // ---------------------------------------------------------------------------
  const handleClose = useCallback(() => {
    onOpenChange(false);
    // Delay reset so the closing animation plays with current content
    setTimeout(reset, 200);
  }, [onOpenChange, reset]);

  // ---------------------------------------------------------------------------
  // Result selection handler
  // ---------------------------------------------------------------------------
  const handleSelect = useCallback(
    (item: SearchResultItemType) => {
      // Save to recent searches
      if (query.trim()) {
        addRecent(query.trim());
      }

      handleClose();

      // Navigate based on result type
      switch (item.type) {
        case "task":
          // Navigate to the project board and potentially open the task detail
          router.push(
            `/projects/${item.data.projectId}/board?task=${item.data.id}`,
          );
          break;
        case "project":
          router.push(`/projects/${item.data.id}/board`);
          break;
        case "member":
          // Navigate to member profile or filter tasks by member
          router.push(`/tasks?assignee=${item.data.id}`);
          break;
      }
    },
    [query, addRecent, handleClose, router],
  );

  // ---------------------------------------------------------------------------
  // Recent search click handler
  // ---------------------------------------------------------------------------
  const handleRecentClick = useCallback(
    (recentQuery: string) => {
      setQuery(recentQuery);
      inputRef.current?.focus();
    },
    [setQuery],
  );

  // ---------------------------------------------------------------------------
  // Keyboard navigation within the palette
  // ---------------------------------------------------------------------------
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      const totalResults = flatResults.length;

      switch (e.key) {
        case "ArrowDown": {
          e.preventDefault();
          setSelectedIndex(
            totalResults > 0 ? (selectedIndex + 1) % totalResults : 0,
          );
          break;
        }
        case "ArrowUp": {
          e.preventDefault();
          setSelectedIndex(
            totalResults > 0
              ? (selectedIndex - 1 + totalResults) % totalResults
              : 0,
          );
          break;
        }
        case "Enter": {
          e.preventDefault();
          if (flatResults[selectedIndex]) {
            handleSelect(flatResults[selectedIndex]);
          }
          break;
        }
        case "Escape": {
          e.preventDefault();
          handleClose();
          break;
        }
      }
    },
    [flatResults, selectedIndex, setSelectedIndex, handleSelect, handleClose],
  );

  // ---------------------------------------------------------------------------
  // Scroll selected item into view
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (!listRef.current) return;
    const selectedEl = listRef.current.querySelector(
      '[aria-selected="true"]',
    ) as HTMLElement | null;
    if (selectedEl) {
      selectedEl.scrollIntoView({ block: "nearest" });
    }
  }, [selectedIndex]);

  // ---------------------------------------------------------------------------
  // Auto-focus input when dialog opens
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (open) {
      // Small delay to ensure the dialog has mounted
      requestAnimationFrame(() => {
        inputRef.current?.focus();
      });
    }
  }, [open]);

  // ---------------------------------------------------------------------------
  // Derive display state
  // ---------------------------------------------------------------------------
  const hasQuery = query.trim().length > 0;
  const hasResults = flatResults.length > 0;
  const showLoading = isLoading || isDebouncing;
  const showEmpty = hasQuery && !showLoading && !hasResults && !error;
  const showResults = hasQuery && hasResults;
  const showRecents = !hasQuery && recentSearches.length > 0;

  // ---------------------------------------------------------------------------
  // Section header positions for group labels
  // ---------------------------------------------------------------------------
  function getSectionHeaders(): Array<{
    label: string;
    icon: React.ReactNode;
    index: number;
  }> {
    const headers: Array<{
      label: string;
      icon: React.ReactNode;
      index: number;
    }> = [];
    let idx = 0;

    if (results.tasks.length > 0) {
      headers.push({
        label: "Tasks",
        icon: <FileText className="h-3.5 w-3.5" />,
        index: idx,
      });
      idx += results.tasks.length;
    }
    if (results.projects.length > 0) {
      headers.push({
        label: "Projects",
        icon: <FolderKanban className="h-3.5 w-3.5" />,
        index: idx,
      });
      idx += results.projects.length;
    }
    if (results.members.length > 0) {
      headers.push({
        label: "Members",
        icon: <Users className="h-3.5 w-3.5" />,
        index: idx,
      });
    }

    return headers;
  }

  const sectionHeaders = getSectionHeaders();

  // Compute a set of indices that start a new section (for rendering headers)
  const sectionStartIndices = new Map(
    sectionHeaders.map((h) => [h.index, h]),
  );

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogPortal>
        <DialogOverlay />
        <DialogPrimitive.Content
          className={cn(
            "fixed z-modal",
            // Mobile: nearly full width, centered, closer to top for thumb reach
            "left-[50%] translate-x-[-50%]",
            "top-[10%] md:top-[20%]",
            "w-[calc(100vw-1rem)] sm:w-[calc(100vw-2rem)] max-w-xl",
            // Visual design
            "bg-surface-elevated border border-border",
            "rounded-xl shadow-2xl",
            "text-text-primary font-body",
            // Animations with reduced-motion support
            "motion-safe:data-[state=open]:animate-scale-in motion-safe:data-[state=closed]:animate-scale-out",
            "motion-reduce:data-[state=open]:animate-in motion-reduce:data-[state=open]:fade-in",
            "focus:outline-none",
            "overflow-hidden",
          )}
          onKeyDown={handleKeyDown}
          aria-label="Command palette"
        >
          {/* Hidden title for accessibility */}
          <DialogPrimitive.Title className="sr-only">
            Search FlowBoard
          </DialogPrimitive.Title>
          <DialogPrimitive.Description className="sr-only">
            Search for tasks, projects, and members. Use arrow keys to navigate
            and Enter to select.
          </DialogPrimitive.Description>

          {/* ---- Search Input (larger touch target on mobile) ---- */}
          <div className="flex items-center gap-3 px-4 py-3 md:py-3 min-h-[52px]">
            {showLoading ? (
              <Loader2 className="h-5 w-5 text-text-quaternary animate-spin shrink-0" />
            ) : (
              <Search className="h-5 w-5 text-text-quaternary shrink-0" />
            )}
            <input
              ref={inputRef}
              type="text"
              placeholder="Search tasks, projects, members..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className={cn(
                "flex-1 bg-transparent",
                // Larger text on mobile for readability, standard on desktop
                "text-base md:text-sm",
                "text-text-primary",
                "placeholder:text-text-quaternary",
                "outline-none border-none",
                "font-body",
                // Prevent iOS zoom on focus (font-size >= 16px)
                "touch-manipulation",
              )}
              autoComplete="off"
              autoCorrect="off"
              autoCapitalize="off"
              spellCheck={false}
              role="combobox"
              aria-expanded={showResults}
              aria-controls="command-palette-results"
              aria-activedescendant={
                showResults ? `search-result-${selectedIndex}` : undefined
              }
            />
            {hasQuery && (
              <button
                type="button"
                onClick={() => setQuery("")}
                className="shrink-0 rounded-md p-1.5 min-w-[44px] min-h-[44px] md:min-w-0 md:min-h-0 md:p-0.5 flex items-center justify-center text-text-quaternary hover:text-text-secondary motion-safe:transition-colors duration-75"
                aria-label="Clear search"
              >
                <X className="h-4 w-4" />
              </button>
            )}
            <kbd className="hidden sm:inline-flex h-5 items-center gap-0.5 rounded border border-edge-subtle bg-surface-secondary px-1.5 font-mono text-[10px] text-text-quaternary shrink-0">
              Esc
            </kbd>
          </div>

          <Separator />

          {/* ---- Results Area ---- */}
          <ScrollArea className="max-h-[60vh]">
            <div
              ref={listRef}
              id="command-palette-results"
              role="listbox"
              aria-label="Search results"
              className="p-2"
            >
              {/* Loading skeleton */}
              {showLoading && !hasResults && (
                <div className="space-y-1 p-1">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <div key={i} className="flex items-center gap-3 px-3 py-2">
                      <Skeleton className="h-3.5 w-3.5 rounded-full shrink-0" />
                      <Skeleton className="h-4 flex-1" />
                      <Skeleton className="h-4 w-16 shrink-0" />
                    </div>
                  ))}
                </div>
              )}

              {/* Error state */}
              {error && (
                <div className="flex flex-col items-center justify-center py-8 px-4 text-center">
                  <p className="text-sm text-text-tertiary">{error}</p>
                </div>
              )}

              {/* Empty state */}
              {showEmpty && (
                <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
                  <Search className="h-8 w-8 text-text-quaternary mb-3" />
                  <p className="text-sm text-text-secondary font-medium">
                    No results found
                  </p>
                  <p className="text-xs text-text-tertiary mt-1">
                    Try a different search term
                  </p>
                </div>
              )}

              {/* Search results — grouped with section headers */}
              {showResults &&
                flatResults.map((item, index) => {
                  const section = sectionStartIndices.get(index);
                  return (
                    <React.Fragment key={`${item.type}-${item.data.id}`}>
                      {section && (
                        <div className="flex items-center gap-2 px-3 pt-3 pb-1.5">
                          <span className="text-text-quaternary">
                            {section.icon}
                          </span>
                          <span className="text-[11px] font-semibold uppercase tracking-wider text-text-quaternary">
                            {section.label}
                          </span>
                        </div>
                      )}
                      <div id={`search-result-${index}`}>
                        <SearchResultItem
                          item={item}
                          isSelected={index === selectedIndex}
                          onClick={() => handleSelect(item)}
                          onMouseEnter={() => setSelectedIndex(index)}
                        />
                      </div>
                    </React.Fragment>
                  );
                })}

              {/* Recent searches */}
              {showRecents && (
                <div>
                  <div className="flex items-center justify-between px-3 pt-2 pb-1.5">
                    <div className="flex items-center gap-2">
                      <Clock className="h-3.5 w-3.5 text-text-quaternary" />
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-text-quaternary">
                        Recent Searches
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={clearRecents}
                      className="text-[11px] text-text-quaternary hover:text-text-secondary transition-colors duration-75"
                    >
                      Clear
                    </button>
                  </div>
                  {recentSearches.map((recent) => (
                    <button
                      key={recent}
                      type="button"
                      className={cn(
                        "flex w-full items-center gap-3 px-3 py-2 rounded-lg",
                        "text-left text-sm text-text-secondary",
                        "hover:bg-surface-hover/50 transition-colors duration-75",
                        "cursor-pointer outline-none",
                      )}
                      onClick={() => handleRecentClick(recent)}
                    >
                      <Search className="h-3.5 w-3.5 text-text-quaternary shrink-0" />
                      <span className="truncate">{recent}</span>
                    </button>
                  ))}
                </div>
              )}

              {/* Default state — no query, no recents */}
              {!hasQuery && recentSearches.length === 0 && (
                <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
                  <Search className="h-8 w-8 text-text-quaternary mb-3" />
                  <p className="text-sm text-text-secondary font-medium">
                    Search FlowBoard
                  </p>
                  <p className="text-xs text-text-tertiary mt-1">
                    Find tasks, projects, and team members
                  </p>
                </div>
              )}
            </div>
          </ScrollArea>

          {/* ---- Footer with keyboard hints (hidden on mobile, no keyboard) ---- */}
          <Separator />
          <div className="hidden sm:flex items-center justify-between px-4 py-2.5 text-[11px] text-text-quaternary">
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1">
                <kbd className="inline-flex h-[18px] min-w-[18px] items-center justify-center rounded border border-edge-subtle bg-surface-secondary px-1 font-mono text-[10px]">
                  &uarr;
                </kbd>
                <kbd className="inline-flex h-[18px] min-w-[18px] items-center justify-center rounded border border-edge-subtle bg-surface-secondary px-1 font-mono text-[10px]">
                  &darr;
                </kbd>
                <span className="ml-0.5">Navigate</span>
              </span>
              <span className="flex items-center gap-1">
                <kbd className="inline-flex h-[18px] min-w-[18px] items-center justify-center rounded border border-edge-subtle bg-surface-secondary px-1 font-mono text-[10px]">
                  &crarr;
                </kbd>
                <span className="ml-0.5">Select</span>
              </span>
              <span className="flex items-center gap-1">
                <kbd className="inline-flex h-[18px] min-w-[18px] items-center justify-center rounded border border-edge-subtle bg-surface-secondary px-1 font-mono text-[10px]">
                  Esc
                </kbd>
                <span className="ml-0.5">Close</span>
              </span>
            </div>
          </div>
        </DialogPrimitive.Content>
      </DialogPortal>
    </Dialog>
  );
}
