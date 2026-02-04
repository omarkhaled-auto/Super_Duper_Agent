import { create } from "zustand";

// =============================================================================
// Task Panel Store — Zustand store for slide-over panel state
//
// Controls which task detail panel is visible. Consumed by:
//   - Board / List views to open the panel on card click
//   - TaskDetailPanel to know which task to display
// =============================================================================

interface TaskPanelState {
  /** Whether the slide-over panel is open. */
  isOpen: boolean;
  /** The ID of the currently displayed task (null when closed). */
  taskId: string | null;
  /** Open the panel for a specific task. */
  openPanel: (taskId: string) => void;
  /** Close the panel and clear the task ID. */
  closePanel: () => void;
}

export const useTaskPanelStore = create<TaskPanelState>((set) => ({
  isOpen: false,
  taskId: null,

  openPanel: (taskId: string) => set({ isOpen: true, taskId }),

  closePanel: () => set({ isOpen: false, taskId: null }),
}));
