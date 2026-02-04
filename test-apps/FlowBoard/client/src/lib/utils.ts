import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import {
  format,
  formatDistanceToNow,
  isToday,
  isYesterday,
  isThisWeek,
  parseISO,
} from "date-fns";

// =============================================================================
// Class Name Utility
// =============================================================================

/**
 * Merge Tailwind classes with clsx -- the shadcn/ui standard utility.
 * Handles conditional classes and removes conflicting Tailwind utilities.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

// =============================================================================
// API URL
// =============================================================================

/** Base URL for backend API calls. Defaults to local dev server. */
export const API_URL: string =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:3001/api";

/** Base URL for WebSocket connections. Defaults to local dev server. */
export const WS_URL: string =
  process.env.NEXT_PUBLIC_WS_URL ?? "http://localhost:3001";

// =============================================================================
// Date Formatting Helpers
// =============================================================================

/**
 * Format an ISO 8601 date string into a human-readable format.
 *
 * @param dateStr - An ISO 8601 date string (e.g. "2024-01-15T10:30:00Z")
 * @param formatStr - A date-fns format pattern. Defaults to "MMM d, yyyy".
 * @returns The formatted date string, or an empty string if input is invalid.
 *
 * @example
 * formatDate("2024-01-15T10:30:00Z")
 * // => "Jan 15, 2024"
 *
 * formatDate("2024-01-15T10:30:00Z", "yyyy-MM-dd")
 * // => "2024-01-15"
 */
export function formatDate(
  dateStr: string | null | undefined,
  formatStr: string = "MMM d, yyyy",
): string {
  if (!dateStr) return "";
  try {
    const date = parseISO(dateStr);
    return format(date, formatStr);
  } catch {
    return "";
  }
}

/**
 * Format an ISO 8601 date string into a relative description such as
 * "just now", "5 minutes ago", "Yesterday", etc.
 *
 * Logic:
 *   - Less than 1 minute ago   => "just now"
 *   - Less than 1 hour ago     => "X minutes ago"
 *   - Today                    => "Today at 10:30 AM"
 *   - Yesterday                => "Yesterday at 10:30 AM"
 *   - Within the current week  => "Monday at 10:30 AM"
 *   - Older                    => "Jan 15, 2024"
 *
 * @param dateStr - An ISO 8601 date string
 * @returns A human-friendly relative date string
 */
export function formatRelativeDate(
  dateStr: string | null | undefined,
): string {
  if (!dateStr) return "";

  try {
    const date = parseISO(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMinutes = Math.floor(diffMs / 60_000);

    if (diffMinutes < 1) {
      return "just now";
    }

    if (diffMinutes < 60) {
      return formatDistanceToNow(date, { addSuffix: true });
    }

    if (isToday(date)) {
      return `Today at ${format(date, "h:mm a")}`;
    }

    if (isYesterday(date)) {
      return `Yesterday at ${format(date, "h:mm a")}`;
    }

    if (isThisWeek(date)) {
      return format(date, "EEEE 'at' h:mm a");
    }

    return format(date, "MMM d, yyyy");
  } catch {
    return "";
  }
}
