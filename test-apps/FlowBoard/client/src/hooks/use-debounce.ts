import { useEffect, useState } from "react";

/**
 * Debounce a value by the specified delay in milliseconds.
 * Useful for search inputs and similar frequent-update scenarios.
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}
