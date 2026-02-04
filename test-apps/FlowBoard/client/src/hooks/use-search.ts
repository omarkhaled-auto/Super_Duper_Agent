"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import api, { ApiError } from "@/lib/api";
import { useDebounce } from "@/hooks/use-debounce";

// =============================================================================
// Search Result Types
// =============================================================================

export interface SearchTaskResult {
  id: string;
  title: string;
  status: string;
  priority: string;
  projectId: string;
  projectName: string;
  projectColor: string | null;
}

export interface SearchProjectResult {
  id: string;
  name: string;
  color: string | null;
  icon: string | null;
  description: string | null;
}

export interface SearchMemberResult {
  id: string;
  name: string;
  email: string;
  avatarUrl: string | null;
}

export interface SearchResults {
  tasks: SearchTaskResult[];
  projects: SearchProjectResult[];
  members: SearchMemberResult[];
}

// Server returns SearchResults directly, no wrapper

// Flat result type for keyboard navigation
export type SearchResultItem =
  | { type: "task"; data: SearchTaskResult }
  | { type: "project"; data: SearchProjectResult }
  | { type: "member"; data: SearchMemberResult };

// =============================================================================
// Recent Searches — persisted in localStorage
// =============================================================================

const RECENT_SEARCHES_KEY = "flowboard_recent_searches";
const MAX_RECENT_SEARCHES = 5;

function getRecentSearches(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const stored = localStorage.getItem(RECENT_SEARCHES_KEY);
    return stored ? (JSON.parse(stored) as string[]) : [];
  } catch {
    return [];
  }
}

function addRecentSearch(query: string): void {
  if (typeof window === "undefined" || !query.trim()) return;
  try {
    const existing = getRecentSearches().filter(
      (s) => s.toLowerCase() !== query.toLowerCase(),
    );
    const updated = [query.trim(), ...existing].slice(0, MAX_RECENT_SEARCHES);
    localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(updated));
  } catch {
    // Ignore storage errors
  }
}

function clearRecentSearches(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(RECENT_SEARCHES_KEY);
}

// =============================================================================
// useSearch — debounced search with grouped results and keyboard nav index
// =============================================================================

interface UseSearchReturn {
  /** Current raw query input value. */
  query: string;
  /** Setter for the query input. */
  setQuery: (q: string) => void;
  /** Grouped search results. */
  results: SearchResults;
  /** Flattened list of all results (for keyboard navigation). */
  flatResults: SearchResultItem[];
  /** Currently highlighted index in flatResults. */
  selectedIndex: number;
  /** Setter for keyboard navigation index. */
  setSelectedIndex: (i: number) => void;
  /** True while the API call is in flight. */
  isLoading: boolean;
  /** True when query is non-empty but debounce hasn't fired yet. */
  isDebouncing: boolean;
  /** Non-null if the search failed. */
  error: string | null;
  /** List of recently searched queries. */
  recentSearches: string[];
  /** Save a query to recents. */
  addRecent: (q: string) => void;
  /** Clear all recent searches. */
  clearRecents: () => void;
  /** Reset search state (called when palette closes). */
  reset: () => void;
}

const EMPTY_RESULTS: SearchResults = {
  tasks: [],
  projects: [],
  members: [],
};

export function useSearch(debounceMs: number = 300): UseSearchReturn {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResults>(EMPTY_RESULTS);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);

  const debouncedQuery = useDebounce(query.trim(), debounceMs);
  const abortRef = useRef<AbortController | null>(null);

  // Hydrate recent searches on mount
  useEffect(() => {
    setRecentSearches(getRecentSearches());
  }, []);

  // Detect debouncing state (user typed but debounce hasn't resolved yet)
  const isDebouncing = query.trim() !== "" && query.trim() !== debouncedQuery;

  // ---------------------------------------------------------------------------
  // Fetch search results whenever debouncedQuery changes
  // ---------------------------------------------------------------------------
  useEffect(() => {
    // If query is empty, clear results
    if (!debouncedQuery) {
      setResults(EMPTY_RESULTS);
      setIsLoading(false);
      setError(null);
      setSelectedIndex(0);
      return;
    }

    // Abort any in-flight request
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    let cancelled = false;

    async function fetchResults() {
      setIsLoading(true);
      setError(null);

      try {
        const encoded = encodeURIComponent(debouncedQuery);
        const res = await api.get<SearchResults>(
          `/search?q=${encoded}`,
          { signal: controller.signal } as never,
        );

        if (!cancelled) {
          setResults(res);
          setSelectedIndex(0);
        }
      } catch (err) {
        if (cancelled) return;
        if (err instanceof DOMException && err.name === "AbortError") return;

        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Search failed. Please try again.");
        }
        setResults(EMPTY_RESULTS);
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    fetchResults();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [debouncedQuery]);

  // ---------------------------------------------------------------------------
  // Flatten results for keyboard navigation
  // ---------------------------------------------------------------------------
  const flatResults: SearchResultItem[] = [
    ...results.tasks.map(
      (t): SearchResultItem => ({ type: "task", data: t }),
    ),
    ...results.projects.map(
      (p): SearchResultItem => ({ type: "project", data: p }),
    ),
    ...results.members.map(
      (m): SearchResultItem => ({ type: "member", data: m }),
    ),
  ];

  // ---------------------------------------------------------------------------
  // Recent search management
  // ---------------------------------------------------------------------------
  const addRecent = useCallback((q: string) => {
    addRecentSearch(q);
    setRecentSearches(getRecentSearches());
  }, []);

  const clearRecents = useCallback(() => {
    clearRecentSearches();
    setRecentSearches([]);
  }, []);

  // ---------------------------------------------------------------------------
  // Reset — called when closing the palette
  // ---------------------------------------------------------------------------
  const reset = useCallback(() => {
    setQuery("");
    setResults(EMPTY_RESULTS);
    setIsLoading(false);
    setError(null);
    setSelectedIndex(0);
    abortRef.current?.abort();
  }, []);

  return {
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
  };
}
