import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { useSettingsStore } from '@/stores/use-settings-store';
import { useSeedData } from '@/hooks/use-seed-data';
import { LoadingSkeleton } from '@/components/shared/loading-skeleton';
import { AppShell } from '@/components/layout/app-shell';
import DashboardPage from '@/pages/dashboard-page';
import TransactionsPage from '@/pages/transactions-page';
import BudgetsPage from '@/pages/budgets-page';
import AccountsPage from '@/pages/accounts-page';
import AnalyticsPage from '@/pages/analytics-page';
import GoalsPage from '@/pages/goals-page';
import SettingsPage from '@/pages/settings-page';

export function App() {
  const { isReady } = useSeedData();
  const theme = useSettingsStore((s) => s.theme);

  // Apply theme class to document root
  useEffect(() => {
    const root = document.documentElement;

    const applyTheme = (resolvedTheme: 'dark' | 'light') => {
      root.classList.remove('dark', 'light');
      root.classList.add(resolvedTheme);
    };

    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      applyTheme(mediaQuery.matches ? 'dark' : 'light');

      const handler = (e: MediaQueryListEvent) => {
        applyTheme(e.matches ? 'dark' : 'light');
      };

      mediaQuery.addEventListener('change', handler);
      return () => mediaQuery.removeEventListener('change', handler);
    }

    applyTheme(theme);
  }, [theme]);

  if (!isReady) {
    return <LoadingSkeleton />;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="transactions" element={<TransactionsPage />} />
          <Route path="budgets" element={<BudgetsPage />} />
          <Route path="accounts" element={<AccountsPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="goals" element={<GoalsPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
      <Toaster
        theme={theme === 'system' ? undefined : theme}
        richColors
        position="bottom-right"
      />
    </BrowserRouter>
  );
}
