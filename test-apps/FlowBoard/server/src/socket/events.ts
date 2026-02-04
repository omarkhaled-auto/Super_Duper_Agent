// =============================================================================
// Socket.io Event Constants
//
// Single source of truth for all real-time event names.
// Both server emitters and client listeners reference these constants.
// =============================================================================

export const SOCKET_EVENTS = {
  // ── Task lifecycle ──────────────────────────────────────────────────────
  TASK_CREATED: "task:created",
  TASK_UPDATED: "task:updated",
  TASK_DELETED: "task:deleted",
  TASK_REORDERED: "task:reordered",

  // ── Comments ────────────────────────────────────────────────────────────
  COMMENT_CREATED: "comment:created",
  COMMENT_DELETED: "comment:deleted",

  // ── Presence ────────────────────────────────────────────────────────────
  PRESENCE_JOIN: "presence:join",
  PRESENCE_LEAVE: "presence:leave",
  PRESENCE_LIST: "presence:list",

  // ── Project ─────────────────────────────────────────────────────────────
  PROJECT_UPDATED: "project:updated",

  // ── Client-to-server commands ───────────────────────────────────────────
  JOIN_PROJECT: "join-project",
  LEAVE_PROJECT: "leave-project",
} as const;

/** Union type of all event name values */
export type SocketEventName = (typeof SOCKET_EVENTS)[keyof typeof SOCKET_EVENTS];
