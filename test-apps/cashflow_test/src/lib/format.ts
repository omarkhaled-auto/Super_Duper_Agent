import { format, formatDistanceToNow } from "date-fns";

/**
 * Format an integer cents value as a currency string.
 * All monetary values in the app are stored as integer cents.
 * Example: formatCurrency(15000) => "$150.00"
 */
export function formatCurrency(amountInCents: number, currency: string = 'USD'): string {
  const amount = amountInCents / 100;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

/**
 * Format a date string or Date object using date-fns patterns.
 * Default pattern: "MMM d, yyyy" (e.g., "Jan 15, 2026")
 */
export function formatDate(date: string | Date, pattern: string = 'MMM d, yyyy'): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return format(d, pattern);
}

/**
 * Format a number as a percentage string with sign.
 * Example: formatPercent(12.3) => "+12.3%", formatPercent(-5.1) => "-5.1%"
 */
export function formatPercent(value: number): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
}

/**
 * Format a number in compact notation.
 * Example: formatCompactNumber(1500000) => "1.5M"
 */
export function formatCompactNumber(n: number): string {
  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(n);
}

/**
 * Format a date as a human-readable relative time string.
 * Example: formatRelativeDate("2026-01-15") => "3 days ago"
 */
export function formatRelativeDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return formatDistanceToNow(d, { addSuffix: true });
}
