import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { generateId } from '@/lib/utils';
import type { Category } from '@/types';

// ---------------------------------------------------------------------------
// Category Store (TASK-013)
// CRUD for transaction / budget categories.
// ---------------------------------------------------------------------------

interface CategoryStoreState {
  categories: Category[];
  addCategory: (
    data: Omit<Category, 'id' | 'createdAt' | 'updatedAt'>,
  ) => void;
  updateCategory: (id: string, updates: Partial<Category>) => void;
  deleteCategory: (id: string) => void;
  seedCategories: (categories: Category[]) => void;
  getCategoryById: (id: string) => Category | undefined;
}

export const useCategoryStore = create<CategoryStoreState>()(
  persist(
    (set, get) => ({
      // --- Default state ---
      categories: [],

      // --- Actions ---
      addCategory: (data) => {
        const now = new Date().toISOString();
        const category: Category = {
          ...data,
          id: generateId(),
          createdAt: now,
          updatedAt: now,
        };
        set((state) => ({ categories: [...state.categories, category] }));
      },

      updateCategory: (id, updates) =>
        set((state) => ({
          categories: state.categories.map((c) =>
            c.id === id
              ? { ...c, ...updates, id, updatedAt: new Date().toISOString() }
              : c,
          ),
        })),

      deleteCategory: (id) =>
        set((state) => ({
          categories: state.categories.filter((c) => c.id !== id),
        })),

      seedCategories: (categories) => set({ categories }),

      getCategoryById: (id) => get().categories.find((c) => c.id === id),
    }),
    {
      name: 'cashflow-categories',
    },
  ),
);
