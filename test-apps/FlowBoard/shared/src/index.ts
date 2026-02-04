// =============================================================================
// FlowBoard Shared Types
//
// This package is the single source of truth for types shared between
// the client and server. Both workspaces import from "flowboard-shared".
//
// Strategy:
//   - Prisma generates the database models on the server side.
//   - This package defines the API-level types (what flows over HTTP / WebSocket).
//   - These are intentionally separate from Prisma types to decouple the API
//     contract from the database schema (e.g. password hashes are never exposed).
// =============================================================================

export type {
  User,
  UserProfile,
} from "./types/user";

export type {
  Project,
  ProjectWithStats,
  ProjectMember,
} from "./types/project";

export type {
  Task,
  TaskSummary,
  SubTask,
  TaskLabel,
} from "./types/task";

export type {
  Comment,
} from "./types/comment";

export type {
  Label,
} from "./types/label";

export type {
  ActivityEvent,
} from "./types/activity";

export type {
  ApiResponse,
  PaginatedResponse,
  ApiError,
} from "./types/api";

export {
  TaskStatus,
  TaskPriority,
  ProjectRole,
  ActivityType,
} from "./types/enums";

export type {
  SocketEvents,
  TaskMovedPayload,
  TaskUpdatedPayload,
  PresencePayload,
} from "./types/socket";
