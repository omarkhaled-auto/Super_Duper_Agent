"use client";

// =============================================================================
// useRealtimeTasks — Subscribes to real-time task events via WebSocket
//
// Listens for task:created, task:updated, task:deleted, task:reordered events
// and calls the provided mutation callbacks to update the local UI state.
//
// This hook is designed to work with both the board view (useBoard) and the
// list view (useTasks) — just pass in the appropriate callbacks.
//
// Note: The hook only processes events for the specified projectId to prevent
// cross-project interference when multiple tabs/views are open.
// =============================================================================

import { useCallback } from "react";
import { SOCKET_EVENTS } from "@/contexts/socket-context";
import { useSocketEvent } from "@/hooks/use-socket-events";
import type { Task, TaskStatus } from "@/types";

// ── Payload types from the server ───────────────────────────────────────────

interface TaskDeletedPayload {
  taskId: string;
  projectId: string;
}

interface TaskReorderedPayload {
  task: Task;
  status: TaskStatus;
  position: number;
}

// ── Hook configuration ──────────────────────────────────────────────────────

interface UseRealtimeTasksOptions {
  /** Only process events for this project. */
  projectId: string;

  /** Called when a new task is created by another user. */
  onTaskCreated?: (task: Task) => void;

  /** Called when a task is updated by another user. */
  onTaskUpdated?: (task: Task) => void;

  /** Called when a task is deleted by another user. */
  onTaskDeleted?: (taskId: string) => void;

  /**
   * Called when a task is reordered (moved between columns or within a column).
   * The task object contains the updated status and position.
   */
  onTaskReordered?: (task: Task) => void;

  /**
   * Fallback: refetch all tasks when a complex event happens.
   * Called for task:reordered if no specific handler is provided.
   */
  onRefetch?: () => void;
}

/**
 * Subscribe to real-time task events for a project and update local state.
 *
 * @example
 * // With the board hook:
 * const board = useBoard(projectId);
 * useRealtimeTasks({
 *   projectId,
 *   onTaskCreated: board.addTask,
 *   onTaskUpdated: (task) => board.updateTask(task.id, task),
 *   onTaskDeleted: board.removeTask,
 *   onTaskReordered: board.refetch,  // Refetch to get correct positions
 * });
 *
 * @example
 * // With the list hook:
 * const { tasks, refetch } = useTasks({ projectId });
 * useRealtimeTasks({
 *   projectId,
 *   onTaskCreated: () => refetch(),
 *   onTaskUpdated: () => refetch(),
 *   onTaskDeleted: () => refetch(),
 *   onRefetch: refetch,
 * });
 */
export function useRealtimeTasks({
  projectId,
  onTaskCreated,
  onTaskUpdated,
  onTaskDeleted,
  onTaskReordered,
  onRefetch,
}: UseRealtimeTasksOptions): void {
  // ── task:created ──────────────────────────────────────────────────────
  useSocketEvent<Task>(
    SOCKET_EVENTS.TASK_CREATED,
    useCallback(
      (task) => {
        if (task.projectId !== projectId) return;
        onTaskCreated?.(task);
      },
      [projectId, onTaskCreated],
    ),
  );

  // ── task:updated ──────────────────────────────────────────────────────
  useSocketEvent<Task>(
    SOCKET_EVENTS.TASK_UPDATED,
    useCallback(
      (task) => {
        if (task.projectId !== projectId) return;
        onTaskUpdated?.(task);
      },
      [projectId, onTaskUpdated],
    ),
  );

  // ── task:deleted ──────────────────────────────────────────────────────
  useSocketEvent<TaskDeletedPayload>(
    SOCKET_EVENTS.TASK_DELETED,
    useCallback(
      (data) => {
        if (data.projectId !== projectId) return;
        onTaskDeleted?.(data.taskId);
      },
      [projectId, onTaskDeleted],
    ),
  );

  // ── task:reordered ────────────────────────────────────────────────────
  useSocketEvent<TaskReorderedPayload>(
    SOCKET_EVENTS.TASK_REORDERED,
    useCallback(
      (data) => {
        if (data.task?.projectId !== projectId) return;

        if (onTaskReordered) {
          onTaskReordered(data.task);
        } else {
          // Fallback: refetch all tasks since reorder affects multiple positions
          onRefetch?.();
        }
      },
      [projectId, onTaskReordered, onRefetch],
    ),
  );
}

// =============================================================================
// useRealtimeComments — Subscribes to real-time comment events
// =============================================================================

interface CommentCreatedPayload {
  taskId: string;
  comment: {
    id: string;
    content: string;
    createdAt: string;
    author: { id: string; name: string; avatar: string | null };
  };
}

interface CommentDeletedPayload {
  commentId: string;
  taskId: string;
}

interface UseRealtimeCommentsOptions {
  /** Only process events for this task. */
  taskId: string;
  /** Called when a new comment is added. */
  onCommentCreated?: (comment: CommentCreatedPayload["comment"]) => void;
  /** Called when a comment is deleted. */
  onCommentDeleted?: (commentId: string) => void;
  /** Fallback: refetch comments. */
  onRefetch?: () => void;
}

/**
 * Subscribe to real-time comment events for a specific task.
 */
export function useRealtimeComments({
  taskId,
  onCommentCreated,
  onCommentDeleted,
  onRefetch,
}: UseRealtimeCommentsOptions): void {
  useSocketEvent<CommentCreatedPayload>(
    SOCKET_EVENTS.COMMENT_CREATED,
    useCallback(
      (data) => {
        if (data.taskId !== taskId) return;
        if (onCommentCreated) {
          onCommentCreated(data.comment);
        } else {
          onRefetch?.();
        }
      },
      [taskId, onCommentCreated, onRefetch],
    ),
  );

  useSocketEvent<CommentDeletedPayload>(
    SOCKET_EVENTS.COMMENT_DELETED,
    useCallback(
      (data) => {
        if (data.taskId !== taskId) return;
        if (onCommentDeleted) {
          onCommentDeleted(data.commentId);
        } else {
          onRefetch?.();
        }
      },
      [taskId, onCommentDeleted, onRefetch],
    ),
  );
}
