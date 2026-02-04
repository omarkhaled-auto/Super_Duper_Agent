import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { generateId } from '@/lib/utils';
import type { Transaction } from '@/types';

// ---------------------------------------------------------------------------
// Transaction Store (TASK-011)
// CRUD for transactions. All amounts are INTEGER CENTS, always positive.
// deleteTransaction returns the deleted item for cross-store coordination.
// ---------------------------------------------------------------------------

interface TransactionStoreState {
  transactions: Transaction[];
  addTransaction: (
    data: Omit<Transaction, 'id' | 'createdAt' | 'updatedAt'>,
  ) => void;
  updateTransaction: (id: string, updates: Partial<Transaction>) => void;
  deleteTransaction: (id: string) => Transaction | undefined;
  seedTransactions: (transactions: Transaction[]) => void;
  getTransactionById: (id: string) => Transaction | undefined;
}

export const useTransactionStore = create<TransactionStoreState>()(
  persist(
    (set, get) => ({
      // --- Default state ---
      transactions: [],

      // --- Actions ---
      addTransaction: (data) => {
        const now = new Date().toISOString();
        const transaction: Transaction = {
          ...data,
          id: generateId(),
          createdAt: now,
          updatedAt: now,
        };
        set((state) => ({
          transactions: [...state.transactions, transaction],
        }));
      },

      updateTransaction: (id, updates) =>
        set((state) => ({
          transactions: state.transactions.map((t) =>
            t.id === id
              ? { ...t, ...updates, id, updatedAt: new Date().toISOString() }
              : t,
          ),
        })),

      deleteTransaction: (id) => {
        const deleted = get().transactions.find((t) => t.id === id);
        if (deleted) {
          set((state) => ({
            transactions: state.transactions.filter((t) => t.id !== id),
          }));
        }
        return deleted;
      },

      seedTransactions: (transactions) => set({ transactions }),

      getTransactionById: (id) => get().transactions.find((t) => t.id === id),
    }),
    {
      name: 'cashflow-transactions',
    },
  ),
);
