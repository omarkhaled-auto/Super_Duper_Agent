import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UserPreferences } from '@/types';

// ---------------------------------------------------------------------------
// Settings Store (TASK-009)
// Manages user preferences: theme, currency, locale, date format, sidebar.
// ---------------------------------------------------------------------------

interface SettingsStoreState extends UserPreferences {
  setTheme: (theme: UserPreferences['theme']) => void;
  setCurrency: (currency: string) => void;
  setLocale: (locale: string) => void;
  setDateFormat: (dateFormat: string) => void;
  toggleSidebar: () => void;
}

export const useSettingsStore = create<SettingsStoreState>()(
  persist(
    (set) => ({
      // --- Default state ---
      theme: 'dark',
      currency: 'USD',
      locale: 'en-US',
      dateFormat: 'MMM d, yyyy',
      sidebarCollapsed: false,

      // --- Actions ---
      setTheme: (theme) => set({ theme }),

      setCurrency: (currency) => set({ currency }),

      setLocale: (locale) => set({ locale }),

      setDateFormat: (dateFormat) => set({ dateFormat }),

      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
    }),
    {
      name: 'cashflow-settings',
    },
  ),
);
