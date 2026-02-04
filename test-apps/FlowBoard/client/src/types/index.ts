// Re-export all shared types for client-side consumption.
// Downstream components should import from "@/types" rather than
// reaching into the shared package directly.
export type {
  User,
  UserProfile,
  Project,
  Task,
  TaskSummary,
  SubTask,
  TaskLabel,
  Comment,
  Label,
  ProjectMember,
  ProjectRole,
  ActivityEvent,
} from "flowboard-shared";

export {
  TaskStatus,
  TaskPriority,
  ActivityType,
} from "flowboard-shared";
