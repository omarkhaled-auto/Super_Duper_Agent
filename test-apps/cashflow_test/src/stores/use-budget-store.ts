import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { generateId } from '@/lib/utils';
import type { Budget } from '@/types';

// ---------------------------------------------------------------------------
// Budget Store (TASK-012)
// CRUD for budgets. All amounts are INTEGER CENTS.
// NOTE: "spent" is NOT stored here -- it is computed at the page level by
// aggregating transactions that match the budget's categoryId + period.
// ---------------------------------------------------------------------------

interface BudgetStoreState {
  budgets: Budget[];
  addBudget: (data: Omit<Budget, 'id' | 'createdAt' | 'updatedAt'>) => void;
  updateBudget: (id: string, updates: Partial<Budget>) => void;
  deleteBudget: (id: string) => void;
  seedBudgets: (budgets: Budget[]) => void;
}

export const useBudgetStore = create<BudgetStoreState>()(
  persist(
    (set) => ({
      // --- Default state ---
      budgets: [],

      // --- Actions ---
      addBudget: (data) => {
        const now = new Date().toISOString();
        const budget: Budget = {
          ...data,
          id: generateId(),
          createdAt: now,
          updatedAt: now,
        };
        set((state) => ({ budgets: [...state.budgets, budget] }));
      },

      updateBudget: (id, updates) =>
        set((state) => ({
          budgets: state.budgets.map((b) =>
            b.id === id
              ? { ...b, ...updates, id, updatedAt: new Date().toISOString() }
              : b,
          ),
        })),

      deleteBudget: (id) =>
        set((state) => ({
          budgets: state.budgets.filter((b) => b.id !== id),
        })),

      seedBudgets: (budgets) => set({ budgets }),
    }),
    {
      name: 'cashflow-budgets',
    },
  ),
);
