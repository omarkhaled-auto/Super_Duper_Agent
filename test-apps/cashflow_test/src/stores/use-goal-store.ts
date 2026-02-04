import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { generateId } from '@/lib/utils';
import type { Goal } from '@/types';

// ---------------------------------------------------------------------------
// Goal Store (TASK-014)
// CRUD for savings / financial goals. All amounts are INTEGER CENTS.
// ---------------------------------------------------------------------------

interface GoalStoreState {
  goals: Goal[];
  addGoal: (data: Omit<Goal, 'id' | 'createdAt' | 'updatedAt'>) => void;
  updateGoal: (id: string, updates: Partial<Goal>) => void;
  deleteGoal: (id: string) => void;
  seedGoals: (goals: Goal[]) => void;
}

export const useGoalStore = create<GoalStoreState>()(
  persist(
    (set) => ({
      // --- Default state ---
      goals: [],

      // --- Actions ---
      addGoal: (data) => {
        const now = new Date().toISOString();
        const goal: Goal = {
          ...data,
          id: generateId(),
          createdAt: now,
          updatedAt: now,
        };
        set((state) => ({ goals: [...state.goals, goal] }));
      },

      updateGoal: (id, updates) =>
        set((state) => ({
          goals: state.goals.map((g) =>
            g.id === id
              ? { ...g, ...updates, id, updatedAt: new Date().toISOString() }
              : g,
          ),
        })),

      deleteGoal: (id) =>
        set((state) => ({
          goals: state.goals.filter((g) => g.id !== id),
        })),

      seedGoals: (goals) => set({ goals }),
    }),
    {
      name: 'cashflow-goals',
    },
  ),
);
