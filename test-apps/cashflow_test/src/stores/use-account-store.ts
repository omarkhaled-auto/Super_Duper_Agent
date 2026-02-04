import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { generateId } from '@/lib/utils';
import type { Account } from '@/types';

// ---------------------------------------------------------------------------
// Account Store (TASK-010)
// CRUD for financial accounts. All balances are INTEGER CENTS.
// ---------------------------------------------------------------------------

interface AccountStoreState {
  accounts: Account[];
  addAccount: (data: Omit<Account, 'id' | 'createdAt' | 'updatedAt'>) => void;
  updateAccount: (id: string, updates: Partial<Account>) => void;
  deleteAccount: (id: string) => void;
  updateBalance: (accountId: string, deltaInCents: number) => void;
  seedAccounts: (accounts: Account[]) => void;
  getAccountById: (id: string) => Account | undefined;
}

export const useAccountStore = create<AccountStoreState>()(
  persist(
    (set, get) => ({
      // --- Default state ---
      accounts: [],

      // --- Actions ---
      addAccount: (data) => {
        const now = new Date().toISOString();
        const account: Account = {
          ...data,
          id: generateId(),
          createdAt: now,
          updatedAt: now,
        };
        set((state) => ({ accounts: [...state.accounts, account] }));
      },

      updateAccount: (id, updates) =>
        set((state) => ({
          accounts: state.accounts.map((a) =>
            a.id === id
              ? { ...a, ...updates, id, updatedAt: new Date().toISOString() }
              : a,
          ),
        })),

      deleteAccount: (id) =>
        set((state) => ({
          accounts: state.accounts.filter((a) => a.id !== id),
        })),

      updateBalance: (accountId, deltaInCents) =>
        set((state) => ({
          accounts: state.accounts.map((a) =>
            a.id === accountId
              ? {
                  ...a,
                  balance: a.balance + deltaInCents,
                  updatedAt: new Date().toISOString(),
                }
              : a,
          ),
        })),

      seedAccounts: (accounts) => set({ accounts }),

      getAccountById: (id) => get().accounts.find((a) => a.id === id),
    }),
    {
      name: 'cashflow-accounts',
    },
  ),
);
