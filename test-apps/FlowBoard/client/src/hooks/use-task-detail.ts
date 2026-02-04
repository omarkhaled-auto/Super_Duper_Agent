"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import api, { ApiError } from "@/lib/api";
import type {
  Task,
  SubTask,
  Comment,
  Label,
  ActivityEvent,
} from "@/types";

// =============================================================================
// useTaskDetail — single-task data fetching + mutation hook
//
// Provides:
//   - Full task data with all relations
//   - Optimistic field updates (title, description, status, priority, etc.)
//   - Sub-task CRUD
//   - Comment CRUD
//   - Label toggle
//   - Activity log
// =============================================================================

interface UseTaskDetailReturn {
  /** The full task object, or null if not yet loaded. */
  task: Task | null;
  /** Comments on this task. */
  comments: Comment[];
  /** Activity events for this task. */
  activities: ActivityEvent[];
  /** Project labels available for selection. */
  projectLabels: Label[];
  /** True while the initial task fetch is in-flight. */
  isLoading: boolean;
  /** Non-null if the fetch failed. */
  error: string | null;
  /** Update a single field on the task (optimistic + API). */
  updateField: (field: string, value: unknown) => Promise<void>;
  /** Add a comment to the task. */
  addComment: (content: string) => Promise<void>;
  /** Delete a comment. */
  deleteComment: (commentId: string) => Promise<void>;
  /** Add a sub-task. */
  addSubTask: (title: string) => Promise<void>;
  /** Toggle a sub-task's completion state. */
  toggleSubTask: (subtaskId: string) => Promise<void>;
  /** Delete a sub-task. */
  deleteSubTask: (subtaskId: string) => Promise<void>;
  /** Toggle a label on/off for this task. */
  toggleLabel: (labelId: string) => Promise<void>;
  /** Create a new project label. */
  createLabel: (name: string, color: string) => Promise<void>;
  /** Re-fetch all task data. */
  refetch: () => Promise<void>;
  /** Fetch comments for the task. */
  fetchComments: () => Promise<void>;
  /** Fetch activity log for the task. */
  fetchActivities: () => Promise<void>;
}

export function useTaskDetail(taskId: string | null): UseTaskDetailReturn {
  const [task, setTask] = useState<Task | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [activities, setActivities] = useState<ActivityEvent[]>([]);
  const [projectLabels, setProjectLabels] = useState<Label[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Track the current taskId to prevent stale updates
  const currentTaskIdRef = useRef<string | null>(taskId);
  currentTaskIdRef.current = taskId;

  // ---------------------------------------------------------------------------
  // Fetch the full task
  // ---------------------------------------------------------------------------

  const fetchTask = useCallback(async () => {
    if (!taskId) {
      setTask(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const res = await api.get<Task>(`/tasks/${taskId}`);
      if (currentTaskIdRef.current === taskId) {
        setTask(res);
      }
    } catch (err) {
      if (currentTaskIdRef.current === taskId) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Failed to load task.");
        }
      }
    } finally {
      if (currentTaskIdRef.current === taskId) {
        setIsLoading(false);
      }
    }
  }, [taskId]);

  // ---------------------------------------------------------------------------
  // Fetch comments
  // ---------------------------------------------------------------------------

  const fetchComments = useCallback(async () => {
    if (!taskId) return;

    try {
      const res = await api.get<Comment[]>(
        `/tasks/${taskId}/comments`,
      );
      if (currentTaskIdRef.current === taskId) {
        setComments(res);
      }
    } catch {
      // Silently fail -- comments are non-critical
    }
  }, [taskId]);

  // ---------------------------------------------------------------------------
  // Fetch activity log
  // ---------------------------------------------------------------------------

  const fetchActivities = useCallback(async () => {
    if (!taskId) return;

    try {
      const res = await api.get<ActivityEvent[]>(
        `/tasks/${taskId}/activity`,
      );
      if (currentTaskIdRef.current === taskId) {
        setActivities(res);
      }
    } catch {
      // Silently fail -- activity is non-critical
    }
  }, [taskId]);

  // ---------------------------------------------------------------------------
  // Fetch project labels (for the label picker)
  // ---------------------------------------------------------------------------

  const fetchProjectLabels = useCallback(async () => {
    if (!task?.projectId) return;

    try {
      const res = await api.get<Label[]>(
        `/projects/${task.projectId}/labels`,
      );
      setProjectLabels(res);
    } catch {
      // Silently fail
    }
  }, [task?.projectId]);

  // ---------------------------------------------------------------------------
  // Initial data loading
  // ---------------------------------------------------------------------------

  useEffect(() => {
    if (taskId) {
      setTask(null);
      setComments([]);
      setActivities([]);
      setProjectLabels([]);
      fetchTask();
    }
  }, [taskId, fetchTask]);

  // Fetch project labels once we know the projectId
  useEffect(() => {
    if (task?.projectId) {
      fetchProjectLabels();
    }
  }, [task?.projectId, fetchProjectLabels]);

  // ---------------------------------------------------------------------------
  // Update a task field (optimistic + API)
  // ---------------------------------------------------------------------------

  const updateField = useCallback(
    async (field: string, value: unknown) => {
      if (!taskId || !task) return;

      // Optimistic update
      const previousTask = { ...task };
      setTask((prev) => (prev ? { ...prev, [field]: value } : prev));

      try {
        const res = await api.patch<Task>(`/tasks/${taskId}`, {
          [field]: value,
        });
        // Reconcile with server response
        if (currentTaskIdRef.current === taskId) {
          setTask(res);
        }
      } catch {
        // Rollback on failure
        if (currentTaskIdRef.current === taskId) {
          setTask(previousTask);
        }
      }
    },
    [taskId, task],
  );

  // ---------------------------------------------------------------------------
  // Comments
  // ---------------------------------------------------------------------------

  const addComment = useCallback(
    async (content: string) => {
      if (!taskId) return;

      // Optimistic: add a temporary comment.
      // Note: the server Comment type may include additional fields like
      // authorId and editedAt. We use a type assertion for the temp comment
      // since it will be replaced by the real server response.
      const tempComment = {
        id: `temp-${Date.now()}`,
        content,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        taskId,
        author: { id: "", name: "You", email: "", avatarUrl: null },
      } as Comment;

      setComments((prev) => [...prev, tempComment]);

      try {
        const res = await api.post<Comment>(
          `/tasks/${taskId}/comments`,
          { content },
        );
        if (currentTaskIdRef.current === taskId) {
          // Replace temp comment with real one
          setComments((prev) =>
            prev.map((c) => (c.id === tempComment.id ? res : c)),
          );
          // Update comment count on task
          setTask((prev) =>
            prev ? { ...prev, commentCount: prev.commentCount + 1 } : prev,
          );
        }
      } catch {
        // Remove temp comment on failure
        if (currentTaskIdRef.current === taskId) {
          setComments((prev) => prev.filter((c) => c.id !== tempComment.id));
        }
      }
    },
    [taskId],
  );

  const deleteComment = useCallback(
    async (commentId: string) => {
      if (!taskId) return;

      const previousComments = [...comments];
      setComments((prev) => prev.filter((c) => c.id !== commentId));

      try {
        await api.del(`/tasks/${taskId}/comments/${commentId}`);
        setTask((prev) =>
          prev
            ? { ...prev, commentCount: Math.max(0, prev.commentCount - 1) }
            : prev,
        );
      } catch {
        if (currentTaskIdRef.current === taskId) {
          setComments(previousComments);
        }
      }
    },
    [taskId, comments],
  );

  // ---------------------------------------------------------------------------
  // Sub-tasks
  // ---------------------------------------------------------------------------

  const addSubTask = useCallback(
    async (title: string) => {
      if (!taskId || !task) return;

      // Create a temp subtask with required fields. Additional fields like
      // taskId, createdAt, updatedAt may exist on the server response and
      // will be merged when the real subtask replaces this temp one.
      const tempSubtask = {
        id: `temp-${Date.now()}`,
        title,
        completed: false,
        position: task.subtasks.length,
      } as SubTask;

      setTask((prev) =>
        prev
          ? {
              ...prev,
              subtasks: [...prev.subtasks, tempSubtask],
              subtaskTotal: prev.subtaskTotal + 1,
            }
          : prev,
      );

      try {
        const res = await api.post<SubTask>(
          `/tasks/${taskId}/subtasks`,
          { title },
        );
        if (currentTaskIdRef.current === taskId) {
          setTask((prev) =>
            prev
              ? {
                  ...prev,
                  subtasks: prev.subtasks.map((st) =>
                    st.id === tempSubtask.id ? res : st,
                  ),
                }
              : prev,
          );
        }
      } catch {
        if (currentTaskIdRef.current === taskId) {
          setTask((prev) =>
            prev
              ? {
                  ...prev,
                  subtasks: prev.subtasks.filter(
                    (st) => st.id !== tempSubtask.id,
                  ),
                  subtaskTotal: prev.subtaskTotal - 1,
                }
              : prev,
          );
        }
      }
    },
    [taskId, task],
  );

  const toggleSubTask = useCallback(
    async (subtaskId: string) => {
      if (!taskId || !task) return;

      const subtask = task.subtasks.find((st) => st.id === subtaskId);
      if (!subtask) return;

      const newCompleted = !subtask.completed;
      const completedDelta = newCompleted ? 1 : -1;

      // Optimistic
      setTask((prev) =>
        prev
          ? {
              ...prev,
              subtasks: prev.subtasks.map((st) =>
                st.id === subtaskId ? { ...st, completed: newCompleted } : st,
              ),
              subtaskCompleted: prev.subtaskCompleted + completedDelta,
            }
          : prev,
      );

      try {
        await api.patch(`/tasks/${taskId}/subtasks/${subtaskId}`, {
          completed: newCompleted,
        });
      } catch {
        // Rollback
        if (currentTaskIdRef.current === taskId) {
          setTask((prev) =>
            prev
              ? {
                  ...prev,
                  subtasks: prev.subtasks.map((st) =>
                    st.id === subtaskId
                      ? { ...st, completed: !newCompleted }
                      : st,
                  ),
                  subtaskCompleted: prev.subtaskCompleted - completedDelta,
                }
              : prev,
          );
        }
      }
    },
    [taskId, task],
  );

  const deleteSubTask = useCallback(
    async (subtaskId: string) => {
      if (!taskId || !task) return;

      const subtask = task.subtasks.find((st) => st.id === subtaskId);
      if (!subtask) return;

      const wasCompleted = subtask.completed;

      // Optimistic
      setTask((prev) =>
        prev
          ? {
              ...prev,
              subtasks: prev.subtasks.filter((st) => st.id !== subtaskId),
              subtaskTotal: prev.subtaskTotal - 1,
              subtaskCompleted: wasCompleted
                ? prev.subtaskCompleted - 1
                : prev.subtaskCompleted,
            }
          : prev,
      );

      try {
        await api.del(`/tasks/${taskId}/subtasks/${subtaskId}`);
      } catch {
        // Refetch to resync on failure
        if (currentTaskIdRef.current === taskId) {
          fetchTask();
        }
      }
    },
    [taskId, task, fetchTask],
  );

  // ---------------------------------------------------------------------------
  // Labels
  // ---------------------------------------------------------------------------

  const toggleLabel = useCallback(
    async (labelId: string) => {
      if (!taskId || !task) return;

      const hasLabel = task.labels.some((l) => l.id === labelId);
      const targetLabel = projectLabels.find((l) => l.id === labelId);

      if (hasLabel) {
        // Remove label (optimistic)
        setTask((prev) =>
          prev
            ? { ...prev, labels: prev.labels.filter((l) => l.id !== labelId) }
            : prev,
        );

        try {
          await api.del(`/tasks/${taskId}/labels/${labelId}`);
        } catch {
          if (currentTaskIdRef.current === taskId) {
            fetchTask();
          }
        }
      } else if (targetLabel) {
        // Add label (optimistic)
        setTask((prev) =>
          prev
            ? { ...prev, labels: [...prev.labels, targetLabel] }
            : prev,
        );

        try {
          await api.post(`/tasks/${taskId}/labels`, { labelId });
        } catch {
          if (currentTaskIdRef.current === taskId) {
            fetchTask();
          }
        }
      }
    },
    [taskId, task, projectLabels, fetchTask],
  );

  const createLabel = useCallback(
    async (name: string, color: string) => {
      if (!task?.projectId) return;

      try {
        const res = await api.post<Label>(
          `/projects/${task.projectId}/labels`,
          { name, color },
        );
        setProjectLabels((prev) => [...prev, res]);
      } catch {
        // Silently fail
      }
    },
    [task?.projectId],
  );

  // ---------------------------------------------------------------------------
  // Refetch all
  // ---------------------------------------------------------------------------

  const refetch = useCallback(async () => {
    await fetchTask();
  }, [fetchTask]);

  return {
    task,
    comments,
    activities,
    projectLabels,
    isLoading,
    error,
    updateField,
    addComment,
    deleteComment,
    addSubTask,
    toggleSubTask,
    deleteSubTask,
    toggleLabel,
    createLabel,
    refetch,
    fetchComments,
    fetchActivities,
  };
}
