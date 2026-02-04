// =============================================================================
// Socket.io Event Types
// =============================================================================

import type { TaskStatus } from "./enums";
import type { Task } from "./task";

/** Map of all Socket.io events and their payload types */
export interface SocketEvents {
  // Task events
  "task:created": Task;
  "task:updated": TaskUpdatedPayload;
  "task:deleted": { taskId: string; projectId: string };
  "task:moved": TaskMovedPayload;

  // Comment events
  "comment:added": { taskId: string; commentId: string };
  "comment:updated": { taskId: string; commentId: string };
  "comment:deleted": { taskId: string; commentId: string };

  // Project events
  "project:updated": { projectId: string };
  "member:added": { projectId: string; userId: string };
  "member:removed": { projectId: string; userId: string };

  // Presence
  "presence:online": { userId: string };
  "presence:offline": { userId: string };
  "presence:list": PresencePayload;
}

export interface TaskMovedPayload {
  taskId: string;
  projectId: string;
  fromStatus: TaskStatus;
  toStatus: TaskStatus;
  newPosition: number;
}

export interface TaskUpdatedPayload {
  taskId: string;
  projectId: string;
  changes: Partial<Task>;
}

export interface PresencePayload {
  projectId: string;
  userIds: string[];
}
