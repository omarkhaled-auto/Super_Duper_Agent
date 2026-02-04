import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { generateId } from '@/lib/utils';
import type { RecurringTransaction } from '@/types';

// ---------------------------------------------------------------------------
// Recurring Transaction Store (TASK-015)
// CRUD for recurring transaction rules. All amounts are INTEGER CENTS.
// ---------------------------------------------------------------------------

interface RecurringStoreState {
  recurringTransactions: RecurringTransaction[];
  addRecurring: (
    data: Omit<RecurringTransaction, 'id' | 'createdAt' | 'updatedAt'>,
  ) => void;
  updateRecurring: (
    id: string,
    updates: Partial<RecurringTransaction>,
  ) => void;
  deleteRecurring: (id: string) => void;
  seedRecurring: (recurringTransactions: RecurringTransaction[]) => void;
}

export const useRecurringStore = create<RecurringStoreState>()(
  persist(
    (set) => ({
      // --- Default state ---
      recurringTransactions: [],

      // --- Actions ---
      addRecurring: (data) => {
        const now = new Date().toISOString();
        const recurring: RecurringTransaction = {
          ...data,
          id: generateId(),
          createdAt: now,
          updatedAt: now,
        };
        set((state) => ({
          recurringTransactions: [...state.recurringTransactions, recurring],
        }));
      },

      updateRecurring: (id, updates) =>
        set((state) => ({
          recurringTransactions: state.recurringTransactions.map((r) =>
            r.id === id
              ? { ...r, ...updates, id, updatedAt: new Date().toISOString() }
              : r,
          ),
        })),

      deleteRecurring: (id) =>
        set((state) => ({
          recurringTransactions: state.recurringTransactions.filter(
            (r) => r.id !== id,
          ),
        })),

      seedRecurring: (recurringTransactions) => set({ recurringTransactions }),
    }),
    {
      name: 'cashflow-recurring',
    },
  ),
);
