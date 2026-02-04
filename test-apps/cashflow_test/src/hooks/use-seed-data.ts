import { useState, useEffect } from 'react';
import { generateSeedData } from '@/data/seed';

// =============================================================================
// useSeedData Hook (TASK-018)
// Checks localStorage for existing data and seeds the stores if empty.
// Returns { isReady } so the app can wait before rendering.
// =============================================================================

export function useSeedData() {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const hasData = localStorage.getItem('cashflow-accounts');
    if (!hasData) {
      generateSeedData();
    }
    setIsReady(true);
  }, []);

  return { isReady };
}
