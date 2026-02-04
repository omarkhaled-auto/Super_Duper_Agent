// =============================================================================
// FlowBoard — Shared TypeScript Types
//
// Single source of truth for types shared between client and server.
// These are API-level types (what flows over HTTP / WebSocket), intentionally
// decoupled from the database schema so sensitive fields like password hashes
// are never exposed.
// =============================================================================

// -----------------------------------------------------------------------------
// Enums
// -----------------------------------------------------------------------------

/** Task workflow status — must match Prisma schema enums exactly */
export enum TaskStatus {
  BACKLOG = "BACKLOG",
  TODO = "TODO",
  IN_PROGRESS = "IN_PROGRESS",
  IN_REVIEW = "IN_REVIEW",
  DONE = "DONE",
}

/** Task priority levels ordered from most to least urgent */
export enum TaskPriority {
  URGENT = "URGENT",
  HIGH = "HIGH",
  MEDIUM = "MEDIUM",
  LOW = "LOW",
  NONE = "NONE",
}

/** Roles a user can hold within a project */
export enum ProjectRole {
  OWNER = "OWNER",
  ADMIN = "ADMIN",
  MEMBER = "MEMBER",
  VIEWER = "VIEWER",
}

/** Activity event types for the audit/activity log */
export enum ActivityType {
  TASK_CREATED = "TASK_CREATED",
  TASK_UPDATED = "TASK_UPDATED",
  TASK_DELETED = "TASK_DELETED",
  TASK_MOVED = "TASK_MOVED",
  TASK_ASSIGNED = "TASK_ASSIGNED",
  TASK_UNASSIGNED = "TASK_UNASSIGNED",
  TASK_COMMENT_ADDED = "TASK_COMMENT_ADDED",
  TASK_COMMENT_UPDATED = "TASK_COMMENT_UPDATED",
  TASK_COMMENT_DELETED = "TASK_COMMENT_DELETED",
  TASK_LABEL_ADDED = "TASK_LABEL_ADDED",
  TASK_LABEL_REMOVED = "TASK_LABEL_REMOVED",
  TASK_DUE_DATE_CHANGED = "TASK_DUE_DATE_CHANGED",
  TASK_PRIORITY_CHANGED = "TASK_PRIORITY_CHANGED",
  SUBTASK_CREATED = "SUBTASK_CREATED",
  SUBTASK_COMPLETED = "SUBTASK_COMPLETED",
  SUBTASK_UNCOMPLETED = "SUBTASK_UNCOMPLETED",
  SUBTASK_DELETED = "SUBTASK_DELETED",
  PROJECT_CREATED = "PROJECT_CREATED",
  PROJECT_UPDATED = "PROJECT_UPDATED",
  PROJECT_ARCHIVED = "PROJECT_ARCHIVED",
  PROJECT_UNARCHIVED = "PROJECT_UNARCHIVED",
  PROJECT_DELETED = "PROJECT_DELETED",
  PROJECT_MEMBER_ADDED = "PROJECT_MEMBER_ADDED",
  PROJECT_MEMBER_REMOVED = "PROJECT_MEMBER_REMOVED",
  PROJECT_MEMBER_ROLE_CHANGED = "PROJECT_MEMBER_ROLE_CHANGED",
}

/** Notification types */
export enum NotificationType {
  TASK_ASSIGNED = "TASK_ASSIGNED",
  TASK_UPDATED = "TASK_UPDATED",
  TASK_COMMENTED = "TASK_COMMENTED",
  TASK_DUE_SOON = "TASK_DUE_SOON",
  TASK_OVERDUE = "TASK_OVERDUE",
  PROJECT_INVITED = "PROJECT_INVITED",
  PROJECT_ROLE_CHANGED = "PROJECT_ROLE_CHANGED",
  MENTION = "MENTION",
}

// -----------------------------------------------------------------------------
// User Types
// -----------------------------------------------------------------------------

/** Full user object returned by the API (never includes passwordHash) */
export interface User {
  id: string;
  email: string;
  name: string;
  avatarUrl: string | null;
  createdAt: string; // ISO 8601
  updatedAt: string; // ISO 8601
}

/** Lightweight user reference for embedding in other objects (e.g. assignee) */
export interface UserProfile {
  id: string;
  name: string;
  email: string;
  avatarUrl: string | null;
}

// -----------------------------------------------------------------------------
// Project Types
// -----------------------------------------------------------------------------

/** Full project object */
export interface Project {
  id: string;
  name: string;
  description: string | null;
  key: string; // short identifier e.g. "FB" for task prefixes like FB-123
  icon: string | null;
  color: string | null;
  archived: boolean;
  ownerId: string;
  createdAt: string;
  updatedAt: string;
}

/** Project with aggregated statistics for the dashboard view */
export interface ProjectWithStats extends Project {
  taskCount: number;
  completedTaskCount: number;
  memberCount: number;
  recentActivity: ActivityEvent[];
}

/** A member of a project with their role and profile */
export interface ProjectMember {
  id: string;
  projectId: string;
  userId: string;
  role: ProjectRole;
  joinedAt: string;
  user: UserProfile;
}

/** Invitation to join a project */
export interface ProjectInvite {
  id: string;
  projectId: string;
  email: string;
  role: ProjectRole;
  invitedBy: UserProfile;
  createdAt: string;
  expiresAt: string;
}

// -----------------------------------------------------------------------------
// Task Types
// -----------------------------------------------------------------------------

/** Full task object (detail view / Kanban card) */
export interface Task {
  id: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  position: number; // ordering within a status column
  taskNumber: number; // human-readable number e.g. 123 in FB-123
  dueDate: string | null;
  completedAt: string | null;
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
  commentCount: number;
  attachmentCount: number;
}

/** Lightweight task for list/board views (no description, no subtask details) */
export interface TaskSummary {
  id: string;
  title: string;
  taskNumber: number;
  status: TaskStatus;
  priority: TaskPriority;
  position: number;
  dueDate: string | null;
  assignee: UserProfile | null;
  labels: Label[];
  subtaskTotal: number;
  subtaskCompleted: number;
  commentCount: number;
}

/** Subtask within a parent task */
export interface SubTask {
  id: string;
  title: string;
  completed: boolean;
  position: number;
  taskId: string;
  createdAt: string;
  updatedAt: string;
}

/** Junction type for task-label associations */
export interface TaskLabel {
  taskId: string;
  labelId: string;
}

/** Task attachment (file uploads) */
export interface Attachment {
  id: string;
  fileName: string;
  fileUrl: string;
  fileSize: number;
  mimeType: string;
  taskId: string;
  uploadedBy: UserProfile;
  createdAt: string;
}

// -----------------------------------------------------------------------------
// Label Types
// -----------------------------------------------------------------------------

/** Project-scoped label for categorizing tasks */
export interface Label {
  id: string;
  name: string;
  color: string;
  description: string | null;
  projectId: string;
}

// -----------------------------------------------------------------------------
// Comment Types
// -----------------------------------------------------------------------------

/** Comment on a task */
export interface Comment {
  id: string;
  content: string;
  createdAt: string;
  updatedAt: string;
  taskId: string;
  authorId: string;
  author: UserProfile;
  editedAt: string | null;
}

// -----------------------------------------------------------------------------
// Activity Types
// -----------------------------------------------------------------------------

/** An activity event in the project audit log */
export interface ActivityEvent {
  id: string;
  type: ActivityType;
  entityType: "task" | "project" | "subtask" | "comment" | "member" | "label";
  entityId: string;
  metadata: Record<string, unknown>;
  createdAt: string;
  projectId: string;
  taskId: string | null;
  actorId: string;
  actor: UserProfile;
}

// -----------------------------------------------------------------------------
// Notification Types
// -----------------------------------------------------------------------------

/** User notification */
export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  read: boolean;
  readAt: string | null;
  createdAt: string;
  userId: string;
  projectId: string | null;
  taskId: string | null;
  actorId: string | null;
  actor: UserProfile | null;
}

// -----------------------------------------------------------------------------
// API Response Types
// -----------------------------------------------------------------------------

/** Standard successful API response wrapper */
export interface ApiResponse<T> {
  success: true;
  data: T;
  message?: string;
}

/** Standard error API response */
export interface ApiErrorResponse {
  success: false;
  message: string;
  errors?: ValidationError[];
}

/** Field-level validation error */
export interface ValidationError {
  field: string;
  message: string;
  code?: string;
}

/** Paginated API response with cursor-based pagination */
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
}

/** Cursor-based paginated response (for infinite scroll) */
export interface CursorPaginatedResponse<T> {
  data: T[];
  total: number;
  pageInfo: {
    hasNextPage: boolean;
    hasPreviousPage: boolean;
    endCursor: string | null;
    startCursor: string | null;
  };
}

// -----------------------------------------------------------------------------
// Auth Types
// -----------------------------------------------------------------------------

/** Login request payload */
export interface LoginRequest {
  email: string;
  password: string;
}

/** Signup / registration request payload */
export interface SignupRequest {
  name: string;
  email: string;
  password: string;
}

/** Successful authentication response */
export interface AuthResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
}

/** JWT access token payload (decoded) */
export interface TokenPayload {
  sub: string; // user ID
  email: string;
  iat: number;
  exp: number;
}

/** JWT refresh token payload (decoded) */
export interface RefreshTokenPayload {
  sub: string; // user ID
  tokenVersion: number;
  iat: number;
  exp: number;
}

/** Request to refresh an access token */
export interface RefreshTokenRequest {
  refreshToken: string;
}

/** Request to change password */
export interface ChangePasswordRequest {
  currentPassword: string;
  newPassword: string;
}

/** Request to reset password (forgot password flow) */
export interface ForgotPasswordRequest {
  email: string;
}

/** Request to set new password via reset token */
export interface ResetPasswordRequest {
  token: string;
  newPassword: string;
}

/** Request to update user profile */
export interface UpdateProfileRequest {
  name?: string;
  avatarUrl?: string | null;
}

// -----------------------------------------------------------------------------
// Project Request Types
// -----------------------------------------------------------------------------

/** Request to create a new project */
export interface CreateProjectRequest {
  name: string;
  description?: string;
  key: string;
  icon?: string;
  color?: string;
}

/** Request to update an existing project */
export interface UpdateProjectRequest {
  name?: string;
  description?: string | null;
  icon?: string | null;
  color?: string | null;
}

/** Request to invite a member to a project */
export interface InviteMemberRequest {
  email: string;
  role: ProjectRole;
}

/** Request to update a member's role */
export interface UpdateMemberRoleRequest {
  role: ProjectRole;
}

// -----------------------------------------------------------------------------
// Task Request Types
// -----------------------------------------------------------------------------

/** Request to create a new task */
export interface CreateTaskRequest {
  title: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  assigneeId?: string;
  labelIds?: string[];
  dueDate?: string;
}

/** Request to update an existing task */
export interface UpdateTaskRequest {
  title?: string;
  description?: string | null;
  status?: TaskStatus;
  priority?: TaskPriority;
  assigneeId?: string | null;
  dueDate?: string | null;
}

/** Request to reorder a task (drag and drop) */
export interface ReorderTaskRequest {
  status: TaskStatus;
  position: number;
}

/** Request to bulk update multiple tasks */
export interface BulkUpdateTasksRequest {
  taskIds: string[];
  update: {
    status?: TaskStatus;
    priority?: TaskPriority;
    assigneeId?: string | null;
    labelIds?: string[];
  };
}

/** Request to create a subtask */
export interface CreateSubTaskRequest {
  title: string;
}

/** Request to update a subtask */
export interface UpdateSubTaskRequest {
  title?: string;
  completed?: boolean;
  position?: number;
}

/** Request to create a comment */
export interface CreateCommentRequest {
  content: string;
}

/** Request to update a comment */
export interface UpdateCommentRequest {
  content: string;
}

/** Request to create a label */
export interface CreateLabelRequest {
  name: string;
  color: string;
  description?: string;
}

/** Request to update a label */
export interface UpdateLabelRequest {
  name?: string;
  color?: string;
  description?: string | null;
}

// -----------------------------------------------------------------------------
// Filter & Sort Types
// -----------------------------------------------------------------------------

/** Task filtering options */
export interface TaskFilter {
  status?: TaskStatus[];
  priority?: TaskPriority[];
  assigneeId?: string | null;
  labelIds?: string[];
  search?: string;
  dueBefore?: string;
  dueAfter?: string;
  createdAfter?: string;
  createdBefore?: string;
}

/** Sort direction */
export type SortDirection = "asc" | "desc";

/** Task sort options */
export interface TaskSort {
  field: "title" | "status" | "priority" | "dueDate" | "createdAt" | "updatedAt" | "position" | "taskNumber";
  direction: SortDirection;
}

/** Pagination query params */
export interface PaginationParams {
  page?: number;
  pageSize?: number;
  cursor?: string;
}

// -----------------------------------------------------------------------------
// WebSocket Event Types
// -----------------------------------------------------------------------------

/** Map of all server-to-client Socket.io events and their payload types */
export interface ServerToClientEvents {
  // Task events
  "task:created": (payload: TaskCreatedPayload) => void;
  "task:updated": (payload: TaskUpdatedPayload) => void;
  "task:deleted": (payload: TaskDeletedPayload) => void;
  "task:moved": (payload: TaskMovedPayload) => void;

  // Comment events
  "comment:added": (payload: CommentEventPayload) => void;
  "comment:updated": (payload: CommentEventPayload) => void;
  "comment:deleted": (payload: CommentEventPayload) => void;

  // Project events
  "project:updated": (payload: ProjectUpdatedPayload) => void;
  "member:added": (payload: MemberEventPayload) => void;
  "member:removed": (payload: MemberEventPayload) => void;
  "member:role-changed": (payload: MemberRoleChangedPayload) => void;

  // Notification events
  "notification:new": (payload: Notification) => void;
  "notification:read": (payload: { notificationId: string }) => void;

  // Presence events
  "presence:online": (payload: { userId: string; projectId: string }) => void;
  "presence:offline": (payload: { userId: string; projectId: string }) => void;
  "presence:list": (payload: PresencePayload) => void;
}

/** Map of all client-to-server Socket.io events and their payload types */
export interface ClientToServerEvents {
  // Room management
  "project:join": (payload: { projectId: string }) => void;
  "project:leave": (payload: { projectId: string }) => void;
  "task:join": (payload: { taskId: string }) => void;
  "task:leave": (payload: { taskId: string }) => void;

  // Real-time collaboration
  "task:move": (payload: TaskMovedPayload) => void;
  "task:update": (payload: TaskUpdatedPayload) => void;

  // Presence
  "presence:ping": (payload: { projectId: string }) => void;

  // Typing indicator for comments
  "comment:typing": (payload: { taskId: string }) => void;
  "comment:stop-typing": (payload: { taskId: string }) => void;
}

/** Payload for task creation event */
export interface TaskCreatedPayload {
  task: Task;
  projectId: string;
}

/** Payload for task update event */
export interface TaskUpdatedPayload {
  taskId: string;
  projectId: string;
  changes: Partial<Task>;
  updatedBy: string;
}

/** Payload for task deletion event */
export interface TaskDeletedPayload {
  taskId: string;
  projectId: string;
  deletedBy: string;
}

/** Payload for task movement (status change / reorder) event */
export interface TaskMovedPayload {
  taskId: string;
  projectId: string;
  fromStatus: TaskStatus;
  toStatus: TaskStatus;
  newPosition: number;
  movedBy: string;
}

/** Payload for comment events */
export interface CommentEventPayload {
  commentId: string;
  taskId: string;
  projectId: string;
  userId: string;
}

/** Payload for project update event */
export interface ProjectUpdatedPayload {
  projectId: string;
  changes: Partial<Project>;
  updatedBy: string;
}

/** Payload for member events */
export interface MemberEventPayload {
  projectId: string;
  userId: string;
  user: UserProfile;
}

/** Payload for member role change event */
export interface MemberRoleChangedPayload {
  projectId: string;
  userId: string;
  oldRole: ProjectRole;
  newRole: ProjectRole;
  changedBy: string;
}

/** Presence payload listing online users */
export interface PresencePayload {
  projectId: string;
  userIds: string[];
}

/** Typing indicator payload */
export interface TypingPayload {
  taskId: string;
  userId: string;
  userName: string;
}

// -----------------------------------------------------------------------------
// Dashboard / Analytics Types
// -----------------------------------------------------------------------------

/** Aggregated statistics for a project dashboard */
export interface ProjectDashboard {
  project: Project;
  tasksByStatus: Record<TaskStatus, number>;
  tasksByPriority: Record<TaskPriority, number>;
  totalTasks: number;
  completedTasks: number;
  overdueTasks: number;
  unassignedTasks: number;
  memberCount: number;
  recentActivity: ActivityEvent[];
  upcomingDueDates: TaskSummary[];
}

/** User's personal dashboard stats across all projects */
export interface UserDashboard {
  assignedToMe: TaskSummary[];
  createdByMe: TaskSummary[];
  overdueTasks: TaskSummary[];
  recentProjects: ProjectWithStats[];
  unreadNotifications: number;
}
