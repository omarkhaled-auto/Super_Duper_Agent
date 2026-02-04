// =============================================================================
// Task Types
// =============================================================================

import type { TaskStatus, TaskPriority } from "./enums";
import type { UserProfile } from "./user";
import type { Label } from "./label";

/** Full task object (detail view / Kanban card) */
export interface Task {
  id: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  position: number;
  dueDate: string | null;
  createdAt: string;
  updatedAt: string;

  projectId: string;
  creatorId: string;
  assigneeId: string | null;

  assignee: UserProfile | null;
  creator: UserProfile;
  labels: Label[];
  subtasks: SubTask[];
  subtaskTotal: number;
  subtaskCompleted: number;

  /** Sequential task number within the project (e.g. #42). */
  taskNumber?: number;
  /** Number of comments on this task (returned by detail endpoint). */
  commentCount: number;
  /** Project name -- included when fetching tasks across projects (e.g. /tasks/me). */
  projectName?: string;
  /** Project color -- included when fetching tasks across projects. */
  projectColor?: string;
}

/** Lightweight task for list views (no description, no subtask details) */
export interface TaskSummary {
  id: string;
  title: string;
  status: TaskStatus;
  priority: TaskPriority;
  dueDate: string | null;
  assignee: UserProfile | null;
  labels: Label[];
  subtaskTotal: number;
  subtaskCompleted: number;
}

export interface SubTask {
  id: string;
  title: string;
  completed: boolean;
  position: number;
}

export interface TaskLabel {
  taskId: string;
  labelId: string;
}
