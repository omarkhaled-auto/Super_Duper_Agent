/**
 * ============================================================================
 * FlowBoard — Complete API Specification
 * ============================================================================
 *
 * Stack: Node.js/Express, PostgreSQL + Prisma, Socket.io, JWT, Zod
 * Base URL: /api/v1
 *
 * Table of Contents:
 *   0. Conventions (errors, auth, pagination, rate limits)
 *   1. Auth          — /api/v1/auth/*
 *   2. Users         — /api/v1/users/*
 *   3. Projects      — /api/v1/projects/*
 *   4. Members       — /api/v1/projects/:projectId/members/*
 *   5. Tasks         — /api/v1/projects/:projectId/tasks/*
 *   6. Sub-tasks     — /api/v1/tasks/:taskId/subtasks/*
 *   7. Labels        — /api/v1/projects/:projectId/labels/*
 *   8. Comments      — /api/v1/tasks/:taskId/comments/*
 *   9. Activity      — /api/v1/activity/*
 *  10. Search        — /api/v1/search
 *  11. Analytics     — /api/v1/projects/:projectId/analytics/*
 *  12. WebSocket     — Socket.io events
 *
 * ============================================================================
 */

import { z } from "zod";

// ============================================================================
// 0. CONVENTIONS
// ============================================================================

// ---------------------------------------------------------------------------
// 0.1 Error Response Format (every error follows this shape)
// ---------------------------------------------------------------------------

export const ErrorResponseSchema = z.object({
  success: z.literal(false),
  error: z.object({
    code: z.string(),             // Machine-readable: "VALIDATION_ERROR", "NOT_FOUND", etc.
    message: z.string(),          // Human-readable summary
    details: z.array(
      z.object({
        field: z.string().optional(),
        message: z.string(),
      })
    ).optional(),                 // Per-field validation errors
    requestId: z.string().uuid(), // For log correlation
  }),
});

/**
 * Standard error codes:
 *
 *  HTTP 400  VALIDATION_ERROR       — Zod parse failure
 *  HTTP 400  BAD_REQUEST            — Malformed request / business rule
 *  HTTP 401  UNAUTHORIZED           — Missing or expired JWT
 *  HTTP 403  FORBIDDEN              — Valid JWT but insufficient role
 *  HTTP 404  NOT_FOUND              — Resource does not exist
 *  HTTP 409  CONFLICT               — Duplicate email, slug collision, etc.
 *  HTTP 413  PAYLOAD_TOO_LARGE      — File upload exceeds limit
 *  HTTP 422  UNPROCESSABLE_ENTITY   — Semantic error (e.g., assign to non-member)
 *  HTTP 429  RATE_LIMIT_EXCEEDED    — Too many requests
 *  HTTP 500  INTERNAL_SERVER_ERROR  — Unexpected failure
 */

// ---------------------------------------------------------------------------
// 0.2 Success Response Wrapper
// ---------------------------------------------------------------------------

export const SuccessResponseSchema = <T extends z.ZodTypeAny>(dataSchema: T) =>
  z.object({
    success: z.literal(true),
    data: dataSchema,
  });

export const PaginatedResponseSchema = <T extends z.ZodTypeAny>(itemSchema: T) =>
  z.object({
    success: z.literal(true),
    data: z.array(itemSchema),
    pagination: z.object({
      page: z.number().int().positive(),
      limit: z.number().int().positive(),
      total: z.number().int().nonnegative(),
      totalPages: z.number().int().nonnegative(),
      hasNextPage: z.boolean(),
      hasPrevPage: z.boolean(),
    }),
  });

// ---------------------------------------------------------------------------
// 0.3 Pagination Query Parameters (reused across all list endpoints)
// ---------------------------------------------------------------------------

export const PaginationQuerySchema = z.object({
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  sortBy: z.string().optional(),
  sortOrder: z.enum(["asc", "desc"]).default("desc"),
});

// ---------------------------------------------------------------------------
// 0.4 Authentication
// ---------------------------------------------------------------------------

/**
 * Auth mechanism: JWT Bearer tokens.
 *
 * - Access token:  short-lived (15 min), sent in `Authorization: Bearer <token>`
 * - Refresh token: long-lived (7 days), sent as httpOnly cookie `refreshToken`
 *
 * Every endpoint except POST /auth/signup, POST /auth/login, and
 * POST /auth/refresh requires a valid access token (middleware: `requireAuth`).
 *
 * Role-gated endpoints additionally require `requireRole('admin')` or
 * `requireProjectRole('admin' | 'member')`.
 *
 * JWT payload shape:
 *   { sub: userId, email: string, iat: number, exp: number }
 */

// ---------------------------------------------------------------------------
// 0.5 Rate Limiting
// ---------------------------------------------------------------------------

/**
 * Rate limits (per IP + authenticated user combo):
 *
 *  Tier 1 — Auth endpoints:          10 req / min  (brute-force protection)
 *  Tier 2 — Write endpoints:         60 req / min
 *  Tier 3 — Read endpoints:         120 req / min
 *  Tier 4 — Search:                  30 req / min  (expensive queries)
 *  Tier 5 — File upload:              5 req / min
 *
 * Headers returned on every response:
 *   X-RateLimit-Limit:     max requests in window
 *   X-RateLimit-Remaining: requests remaining
 *   X-RateLimit-Reset:     unix timestamp when window resets
 *
 * When exceeded, returns 429 with ErrorResponseSchema and Retry-After header.
 */


// ============================================================================
// SHARED ENUMS & PRIMITIVES
// ============================================================================

export const TaskStatusEnum = z.enum([
  "BACKLOG",
  "TODO",
  "IN_PROGRESS",
  "IN_REVIEW",
  "DONE",
]);

export const TaskPriorityEnum = z.enum([
  "URGENT",
  "HIGH",
  "MEDIUM",
  "LOW",
  "NONE",
]);

export const ProjectRoleEnum = z.enum(["admin", "member", "viewer"]);

export const SortOrderEnum = z.enum(["asc", "desc"]);

// Common ID param
const UUIDParam = z.string().uuid();


// ============================================================================
// 1. AUTH — /api/v1/auth
// ============================================================================
// Rate limit: Tier 1 (10 req/min)
// All endpoints in this group are PUBLIC (no JWT required)
// except POST /auth/logout and GET /auth/me.

// ---------------------------------------------------------------------------
// POST /api/v1/auth/signup
// Register a new user account. Returns tokens + user profile.
// Auth: NONE
// ---------------------------------------------------------------------------

export const SignupRequestSchema = z.object({
  name: z.string().min(2).max(100).trim(),
  email: z.string().email().max(255).trim().toLowerCase(),
  password: z
    .string()
    .min(8)
    .max(128)
    .regex(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
      "Password must contain at least one lowercase letter, one uppercase letter, and one digit"
    ),
});

export const AuthTokensSchema = z.object({
  accessToken: z.string(),
  expiresIn: z.number(),           // seconds until access token expires
});

export const UserProfileSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  email: z.string().email(),
  avatarUrl: z.string().url().nullable(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
});

export const SignupResponseSchema = SuccessResponseSchema(
  z.object({
    user: UserProfileSchema,
    tokens: AuthTokensSchema,
  })
);
// Sets httpOnly cookie: refreshToken

// ---------------------------------------------------------------------------
// POST /api/v1/auth/login
// Authenticate with email + password. Returns tokens + user profile.
// Auth: NONE
// ---------------------------------------------------------------------------

export const LoginRequestSchema = z.object({
  email: z.string().email().trim().toLowerCase(),
  password: z.string().min(1),
});

export const LoginResponseSchema = SignupResponseSchema; // Same shape
// Sets httpOnly cookie: refreshToken

// ---------------------------------------------------------------------------
// POST /api/v1/auth/refresh
// Exchange refresh token (from httpOnly cookie) for new access token.
// Auth: NONE (uses cookie)
// ---------------------------------------------------------------------------

// No request body — refresh token is read from cookie.

export const RefreshResponseSchema = SuccessResponseSchema(
  z.object({
    tokens: AuthTokensSchema,
  })
);
// Also rotates the refreshToken cookie (refresh token rotation).

// ---------------------------------------------------------------------------
// POST /api/v1/auth/logout
// Invalidate the current refresh token and clear cookie.
// Auth: requireAuth
// ---------------------------------------------------------------------------

// No request body.

export const LogoutResponseSchema = SuccessResponseSchema(
  z.object({ message: z.literal("Logged out successfully") })
);

// ---------------------------------------------------------------------------
// GET /api/v1/auth/me
// Get the currently authenticated user's profile.
// Auth: requireAuth
// ---------------------------------------------------------------------------

export const MeResponseSchema = SuccessResponseSchema(UserProfileSchema);


// ============================================================================
// 2. USERS — /api/v1/users
// ============================================================================
// Rate limit: Tier 3 (read), Tier 2 (write), Tier 5 (upload)

// ---------------------------------------------------------------------------
// PATCH /api/v1/users/profile
// Update own profile (name, email).
// Auth: requireAuth
// ---------------------------------------------------------------------------

export const UpdateProfileRequestSchema = z.object({
  name: z.string().min(2).max(100).trim().optional(),
  email: z.string().email().max(255).trim().toLowerCase().optional(),
}).refine(data => data.name || data.email, {
  message: "At least one field must be provided",
});

export const UpdateProfileResponseSchema = SuccessResponseSchema(UserProfileSchema);

// ---------------------------------------------------------------------------
// PATCH /api/v1/users/password
// Change own password.
// Auth: requireAuth
// ---------------------------------------------------------------------------

export const ChangePasswordRequestSchema = z.object({
  currentPassword: z.string().min(1),
  newPassword: z
    .string()
    .min(8)
    .max(128)
    .regex(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
      "Password must contain at least one lowercase letter, one uppercase letter, and one digit"
    ),
}).refine(data => data.currentPassword !== data.newPassword, {
  message: "New password must be different from current password",
});

export const ChangePasswordResponseSchema = SuccessResponseSchema(
  z.object({ message: z.literal("Password updated successfully") })
);

// ---------------------------------------------------------------------------
// POST /api/v1/users/avatar
// Upload/replace profile avatar. Accepts multipart/form-data.
// Auth: requireAuth
// Rate limit: Tier 5 (5 req/min)
// Max file size: 5 MB
// Allowed types: image/jpeg, image/png, image/webp, image/gif
// ---------------------------------------------------------------------------

export const AvatarUploadResponseSchema = SuccessResponseSchema(
  z.object({
    avatarUrl: z.string().url(),
  })
);

// ---------------------------------------------------------------------------
// DELETE /api/v1/users/avatar
// Remove own profile avatar.
// Auth: requireAuth
// ---------------------------------------------------------------------------

export const AvatarDeleteResponseSchema = SuccessResponseSchema(
  z.object({ message: z.literal("Avatar removed") })
);

// ---------------------------------------------------------------------------
// GET /api/v1/users
// List all users (for assignee dropdowns, member search).
// Auth: requireAuth
// Query: ?search=<name|email>&page=1&limit=20
// ---------------------------------------------------------------------------

export const ListUsersQuerySchema = PaginationQuerySchema.extend({
  search: z.string().max(100).optional(),
});

export const UserSummarySchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  email: z.string().email(),
  avatarUrl: z.string().url().nullable(),
  isOnline: z.boolean(),
});

// Response: PaginatedResponseSchema(UserSummarySchema)

// ---------------------------------------------------------------------------
// GET /api/v1/users/presence
// Get online presence for a list of user IDs.
// Auth: requireAuth
// Query: ?userIds=uuid1,uuid2,uuid3
// ---------------------------------------------------------------------------

export const PresenceQuerySchema = z.object({
  userIds: z.string().transform((val) => val.split(",").map((id) => id.trim())),
});

export const PresenceResponseSchema = SuccessResponseSchema(
  z.array(
    z.object({
      userId: z.string().uuid(),
      isOnline: z.boolean(),
      lastSeenAt: z.string().datetime().nullable(),
    })
  )
);


// ============================================================================
// 3. PROJECTS — /api/v1/projects
// ============================================================================
// Rate limit: Tier 3 (read), Tier 2 (write)

// ---------------------------------------------------------------------------
// Shared project schemas
// ---------------------------------------------------------------------------

export const ProjectSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  description: z.string().nullable(),
  slug: z.string(),
  icon: z.string().nullable(),          // emoji or icon identifier
  color: z.string().nullable(),         // hex color, e.g. "#6366f1"
  isArchived: z.boolean(),
  ownerId: z.string().uuid(),
  taskCount: z.number().int().nonnegative(),
  completedTaskCount: z.number().int().nonnegative(),
  memberCount: z.number().int().positive(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
});

export const ProjectDetailSchema = ProjectSchema.extend({
  members: z.array(
    z.object({
      userId: z.string().uuid(),
      name: z.string(),
      email: z.string().email(),
      avatarUrl: z.string().url().nullable(),
      role: ProjectRoleEnum,
      joinedAt: z.string().datetime(),
    })
  ),
});

// ---------------------------------------------------------------------------
// POST /api/v1/projects
// Create a new project. Creator becomes admin.
// Auth: requireAuth
// ---------------------------------------------------------------------------

export const CreateProjectRequestSchema = z.object({
  name: z.string().min(1).max(100).trim(),
  description: z.string().max(500).trim().optional(),
  icon: z.string().max(10).optional(),
  color: z
    .string()
    .regex(/^#[0-9a-fA-F]{6}$/, "Must be a valid hex color")
    .optional(),
});

export const CreateProjectResponseSchema = SuccessResponseSchema(ProjectDetailSchema);

// ---------------------------------------------------------------------------
// GET /api/v1/projects
// List projects the authenticated user is a member of.
// Auth: requireAuth
// Query: ?page=1&limit=20&sortBy=updatedAt&sortOrder=desc&archived=false&search=<name>
// ---------------------------------------------------------------------------

export const ListProjectsQuerySchema = PaginationQuerySchema.extend({
  sortBy: z.enum(["name", "createdAt", "updatedAt"]).default("updatedAt"),
  archived: z.coerce.boolean().default(false),
  search: z.string().max(100).optional(),
});

// Response: PaginatedResponseSchema(ProjectSchema)

// ---------------------------------------------------------------------------
// GET /api/v1/projects/:projectId
// Get a single project with full details.
// Auth: requireAuth + requireProjectMember
// ---------------------------------------------------------------------------

// Response: SuccessResponseSchema(ProjectDetailSchema)

// ---------------------------------------------------------------------------
// PATCH /api/v1/projects/:projectId
// Update project settings.
// Auth: requireAuth + requireProjectRole('admin')
// ---------------------------------------------------------------------------

export const UpdateProjectRequestSchema = z.object({
  name: z.string().min(1).max(100).trim().optional(),
  description: z.string().max(500).trim().optional(),
  icon: z.string().max(10).optional(),
  color: z
    .string()
    .regex(/^#[0-9a-fA-F]{6}$/, "Must be a valid hex color")
    .optional(),
}).refine(data => Object.values(data).some(v => v !== undefined), {
  message: "At least one field must be provided",
});

export const UpdateProjectResponseSchema = SuccessResponseSchema(ProjectDetailSchema);

// ---------------------------------------------------------------------------
// DELETE /api/v1/projects/:projectId
// Permanently delete a project and all its data.
// Auth: requireAuth + requireProjectRole('admin')
// ---------------------------------------------------------------------------

export const DeleteProjectResponseSchema = SuccessResponseSchema(
  z.object({ message: z.literal("Project deleted") })
);

// ---------------------------------------------------------------------------
// PATCH /api/v1/projects/:projectId/archive
// Archive or unarchive a project.
// Auth: requireAuth + requireProjectRole('admin')
// ---------------------------------------------------------------------------

export const ArchiveProjectRequestSchema = z.object({
  archived: z.boolean(),
});

export const ArchiveProjectResponseSchema = SuccessResponseSchema(ProjectSchema);


// ============================================================================
// 4. PROJECT MEMBERS — /api/v1/projects/:projectId/members
// ============================================================================
// Rate limit: Tier 3 (read), Tier 2 (write)

// ---------------------------------------------------------------------------
// GET /api/v1/projects/:projectId/members
// List all members of a project.
// Auth: requireAuth + requireProjectMember
// ---------------------------------------------------------------------------

export const ProjectMemberSchema = z.object({
  id: z.string().uuid(),           // membership record id
  userId: z.string().uuid(),
  name: z.string(),
  email: z.string().email(),
  avatarUrl: z.string().url().nullable(),
  role: ProjectRoleEnum,
  isOnline: z.boolean(),
  joinedAt: z.string().datetime(),
});

// Response: SuccessResponseSchema(z.array(ProjectMemberSchema))
// (No pagination — member lists are small enough)

// ---------------------------------------------------------------------------
// POST /api/v1/projects/:projectId/members
// Invite a user to the project by email.
// Auth: requireAuth + requireProjectRole('admin')
// ---------------------------------------------------------------------------

export const InviteMemberRequestSchema = z.object({
  email: z.string().email().trim().toLowerCase(),
  role: ProjectRoleEnum.default("member"),
});

export const InviteMemberResponseSchema = SuccessResponseSchema(ProjectMemberSchema);

// ---------------------------------------------------------------------------
// PATCH /api/v1/projects/:projectId/members/:userId
// Change a member's role.
// Auth: requireAuth + requireProjectRole('admin')
// Cannot change own role. Cannot demote the last admin.
// ---------------------------------------------------------------------------

export const ChangeMemberRoleRequestSchema = z.object({
  role: ProjectRoleEnum,
});

export const ChangeMemberRoleResponseSchema = SuccessResponseSchema(ProjectMemberSchema);

// ---------------------------------------------------------------------------
// DELETE /api/v1/projects/:projectId/members/:userId
// Remove a member from the project.
// Auth: requireAuth + requireProjectRole('admin')
// Cannot remove self if last admin. Members can also remove themselves.
// ---------------------------------------------------------------------------

export const RemoveMemberResponseSchema = SuccessResponseSchema(
  z.object({ message: z.literal("Member removed") })
);


// ============================================================================
// 5. TASKS — /api/v1/projects/:projectId/tasks
// ============================================================================
// Rate limit: Tier 3 (read), Tier 2 (write)

// ---------------------------------------------------------------------------
// Shared task schemas
// ---------------------------------------------------------------------------

export const TaskSchema = z.object({
  id: z.string().uuid(),
  projectId: z.string().uuid(),
  title: z.string(),
  description: z.string().nullable(),  // Markdown content
  status: TaskStatusEnum,
  priority: TaskPriorityEnum,
  position: z.number(),                // Float for drag-drop ordering
  assigneeId: z.string().uuid().nullable(),
  assignee: UserSummarySchema.nullable(),
  dueDate: z.string().datetime().nullable(),
  labels: z.array(
    z.object({
      id: z.string().uuid(),
      name: z.string(),
      color: z.string(),
    })
  ),
  subtaskCount: z.number().int().nonnegative(),
  completedSubtaskCount: z.number().int().nonnegative(),
  commentCount: z.number().int().nonnegative(),
  createdById: z.string().uuid(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
});

export const TaskDetailSchema = TaskSchema.extend({
  subtasks: z.array(
    z.object({
      id: z.string().uuid(),
      title: z.string(),
      isCompleted: z.boolean(),
      position: z.number(),
      createdAt: z.string().datetime(),
    })
  ),
});

// ---------------------------------------------------------------------------
// POST /api/v1/projects/:projectId/tasks
// Create a new task.
// Auth: requireAuth + requireProjectRole('admin' | 'member')
// ---------------------------------------------------------------------------

export const CreateTaskRequestSchema = z.object({
  title: z.string().min(1).max(255).trim(),
  description: z.string().max(10000).trim().optional(),
  status: TaskStatusEnum.default("BACKLOG"),
  priority: TaskPriorityEnum.default("NONE"),
  assigneeId: z.string().uuid().optional(),
  dueDate: z.string().datetime().optional(),
  labelIds: z.array(z.string().uuid()).max(10).optional(),
});

export const CreateTaskResponseSchema = SuccessResponseSchema(TaskSchema);

// ---------------------------------------------------------------------------
// GET /api/v1/projects/:projectId/tasks
// List tasks with filtering, sorting, pagination.
// Auth: requireAuth + requireProjectMember
// ---------------------------------------------------------------------------

export const ListTasksQuerySchema = PaginationQuerySchema.extend({
  sortBy: z
    .enum(["title", "status", "priority", "dueDate", "createdAt", "updatedAt", "position"])
    .default("position"),
  status: z.union([TaskStatusEnum, z.string().transform(v => v.split(","))]).optional(),
  priority: z.union([TaskPriorityEnum, z.string().transform(v => v.split(","))]).optional(),
  assigneeId: z.string().uuid().optional(),
  labelId: z.string().uuid().optional(),
  dueBefore: z.string().datetime().optional(),
  dueAfter: z.string().datetime().optional(),
  search: z.string().max(100).optional(),
});

// Response: PaginatedResponseSchema(TaskSchema)

// ---------------------------------------------------------------------------
// GET /api/v1/projects/:projectId/tasks/board
// Get tasks grouped by status column (optimized for Kanban view).
// Auth: requireAuth + requireProjectMember
// Returns tasks in each column sorted by `position`.
// ---------------------------------------------------------------------------

export const BoardResponseSchema = SuccessResponseSchema(
  z.object({
    columns: z.array(
      z.object({
        status: TaskStatusEnum,
        tasks: z.array(TaskSchema),
        count: z.number().int().nonnegative(),
      })
    ),
  })
);

// ---------------------------------------------------------------------------
// GET /api/v1/projects/:projectId/tasks/:taskId
// Get a single task with full detail (subtasks included).
// Auth: requireAuth + requireProjectMember
// ---------------------------------------------------------------------------

// Response: SuccessResponseSchema(TaskDetailSchema)

// ---------------------------------------------------------------------------
// PATCH /api/v1/projects/:projectId/tasks/:taskId
// Update any task field(s).
// Auth: requireAuth + requireProjectRole('admin' | 'member')
// ---------------------------------------------------------------------------

export const UpdateTaskRequestSchema = z.object({
  title: z.string().min(1).max(255).trim().optional(),
  description: z.string().max(10000).trim().optional(),
  status: TaskStatusEnum.optional(),
  priority: TaskPriorityEnum.optional(),
  assigneeId: z.string().uuid().nullable().optional(),
  dueDate: z.string().datetime().nullable().optional(),
}).refine(data => Object.values(data).some(v => v !== undefined), {
  message: "At least one field must be provided",
});

export const UpdateTaskResponseSchema = SuccessResponseSchema(TaskSchema);

// ---------------------------------------------------------------------------
// DELETE /api/v1/projects/:projectId/tasks/:taskId
// Delete a task and its subtasks/comments.
// Auth: requireAuth + requireProjectRole('admin' | 'member')
// ---------------------------------------------------------------------------

export const DeleteTaskResponseSchema = SuccessResponseSchema(
  z.object({ message: z.literal("Task deleted") })
);

// ---------------------------------------------------------------------------
// PATCH /api/v1/projects/:projectId/tasks/:taskId/reorder
// Move a task to a new position (drag-and-drop).
// Auth: requireAuth + requireProjectRole('admin' | 'member')
// ---------------------------------------------------------------------------

export const ReorderTaskRequestSchema = z.object({
  status: TaskStatusEnum,           // Target column (may have changed)
  afterTaskId: z.string().uuid().nullable(),  // Insert after this task (null = first)
  beforeTaskId: z.string().uuid().nullable(), // Insert before this task (null = last)
});

export const ReorderTaskResponseSchema = SuccessResponseSchema(
  z.object({
    taskId: z.string().uuid(),
    status: TaskStatusEnum,
    position: z.number(),
  })
);

// ---------------------------------------------------------------------------
// POST /api/v1/projects/:projectId/tasks/bulk
// Bulk actions on multiple tasks.
// Auth: requireAuth + requireProjectRole('admin' | 'member')
// ---------------------------------------------------------------------------

export const BulkTaskActionRequestSchema = z.object({
  taskIds: z.array(z.string().uuid()).min(1).max(50),
  action: z.discriminatedUnion("type", [
    z.object({
      type: z.literal("changeStatus"),
      status: TaskStatusEnum,
    }),
    z.object({
      type: z.literal("changePriority"),
      priority: TaskPriorityEnum,
    }),
    z.object({
      type: z.literal("changeAssignee"),
      assigneeId: z.string().uuid().nullable(),
    }),
    z.object({
      type: z.literal("addLabel"),
      labelId: z.string().uuid(),
    }),
    z.object({
      type: z.literal("removeLabel"),
      labelId: z.string().uuid(),
    }),
    z.object({
      type: z.literal("delete"),
    }),
  ]),
});

export const BulkTaskActionResponseSchema = SuccessResponseSchema(
  z.object({
    modifiedCount: z.number().int().nonnegative(),
    taskIds: z.array(z.string().uuid()),
  })
);

// ---------------------------------------------------------------------------
// GET /api/v1/users/me/tasks
// Get all tasks assigned to the current user across all projects.
// Auth: requireAuth
// Query: same as ListTasksQuerySchema minus project-specific filters
// ---------------------------------------------------------------------------

export const MyTasksQuerySchema = PaginationQuerySchema.extend({
  sortBy: z.enum(["dueDate", "priority", "createdAt", "updatedAt"]).default("dueDate"),
  status: z.union([TaskStatusEnum, z.string().transform(v => v.split(","))]).optional(),
  priority: z.union([TaskPriorityEnum, z.string().transform(v => v.split(","))]).optional(),
  dueBefore: z.string().datetime().optional(),
  dueAfter: z.string().datetime().optional(),
});

export const MyTaskSchema = TaskSchema.extend({
  projectName: z.string(),
  projectColor: z.string().nullable(),
});

// Response: PaginatedResponseSchema(MyTaskSchema)


// ============================================================================
// 6. SUB-TASKS — /api/v1/tasks/:taskId/subtasks
// ============================================================================
// Rate limit: Tier 3 (read), Tier 2 (write)

export const SubtaskSchema = z.object({
  id: z.string().uuid(),
  taskId: z.string().uuid(),
  title: z.string(),
  isCompleted: z.boolean(),
  position: z.number(),
  createdById: z.string().uuid(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
});

// ---------------------------------------------------------------------------
// POST /api/v1/tasks/:taskId/subtasks
// Create a sub-task.
// Auth: requireAuth + requireProjectRole('admin' | 'member') via parent task
// ---------------------------------------------------------------------------

export const CreateSubtaskRequestSchema = z.object({
  title: z.string().min(1).max(255).trim(),
});

export const CreateSubtaskResponseSchema = SuccessResponseSchema(SubtaskSchema);

// ---------------------------------------------------------------------------
// GET /api/v1/tasks/:taskId/subtasks
// List all sub-tasks for a task, ordered by position.
// Auth: requireAuth + requireProjectMember via parent task
// ---------------------------------------------------------------------------

// Response: SuccessResponseSchema(z.array(SubtaskSchema))

// ---------------------------------------------------------------------------
// PATCH /api/v1/tasks/:taskId/subtasks/:subtaskId
// Update sub-task title or completion status.
// Auth: requireAuth + requireProjectRole('admin' | 'member')
// ---------------------------------------------------------------------------

export const UpdateSubtaskRequestSchema = z.object({
  title: z.string().min(1).max(255).trim().optional(),
  isCompleted: z.boolean().optional(),
}).refine(data => data.title !== undefined || data.isCompleted !== undefined, {
  message: "At least one field must be provided",
});

export const UpdateSubtaskResponseSchema = SuccessResponseSchema(SubtaskSchema);

// ---------------------------------------------------------------------------
// PATCH /api/v1/tasks/:taskId/subtasks/:subtaskId/toggle
// Toggle sub-task completion (convenience endpoint).
// Auth: requireAuth + requireProjectRole('admin' | 'member')
// ---------------------------------------------------------------------------

export const ToggleSubtaskResponseSchema = SuccessResponseSchema(SubtaskSchema);

// ---------------------------------------------------------------------------
// DELETE /api/v1/tasks/:taskId/subtasks/:subtaskId
// Delete a sub-task.
// Auth: requireAuth + requireProjectRole('admin' | 'member')
// ---------------------------------------------------------------------------

export const DeleteSubtaskResponseSchema = SuccessResponseSchema(
  z.object({ message: z.literal("Subtask deleted") })
);

// ---------------------------------------------------------------------------
// PATCH /api/v1/tasks/:taskId/subtasks/reorder
// Reorder sub-tasks within a task.
// Auth: requireAuth + requireProjectRole('admin' | 'member')
// ---------------------------------------------------------------------------

export const ReorderSubtasksRequestSchema = z.object({
  subtaskIds: z.array(z.string().uuid()).min(1), // Full ordered list
});

export const ReorderSubtasksResponseSchema = SuccessResponseSchema(
  z.array(SubtaskSchema)
);


// ============================================================================
// 7. LABELS — /api/v1/projects/:projectId/labels
// ============================================================================
// Rate limit: Tier 3 (read), Tier 2 (write)

export const LabelSchema = z.object({
  id: z.string().uuid(),
  projectId: z.string().uuid(),
  name: z.string(),
  color: z.string(),                // Hex color
  taskCount: z.number().int().nonnegative(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
});

// ---------------------------------------------------------------------------
// POST /api/v1/projects/:projectId/labels
// Create a label for a project.
// Auth: requireAuth + requireProjectRole('admin' | 'member')
// ---------------------------------------------------------------------------

export const CreateLabelRequestSchema = z.object({
  name: z.string().min(1).max(50).trim(),
  color: z.string().regex(/^#[0-9a-fA-F]{6}$/, "Must be a valid hex color"),
});

export const CreateLabelResponseSchema = SuccessResponseSchema(LabelSchema);

// ---------------------------------------------------------------------------
// GET /api/v1/projects/:projectId/labels
// List all labels in a project.
// Auth: requireAuth + requireProjectMember
// ---------------------------------------------------------------------------

// Response: SuccessResponseSchema(z.array(LabelSchema))
// (No pagination — label lists are small)

// ---------------------------------------------------------------------------
// PATCH /api/v1/projects/:projectId/labels/:labelId
// Update a label's name or color.
// Auth: requireAuth + requireProjectRole('admin' | 'member')
// ---------------------------------------------------------------------------

export const UpdateLabelRequestSchema = z.object({
  name: z.string().min(1).max(50).trim().optional(),
  color: z
    .string()
    .regex(/^#[0-9a-fA-F]{6}$/, "Must be a valid hex color")
    .optional(),
}).refine(data => data.name || data.color, {
  message: "At least one field must be provided",
});

export const UpdateLabelResponseSchema = SuccessResponseSchema(LabelSchema);

// ---------------------------------------------------------------------------
// DELETE /api/v1/projects/:projectId/labels/:labelId
// Delete a label. Removes it from all tasks.
// Auth: requireAuth + requireProjectRole('admin')
// ---------------------------------------------------------------------------

export const DeleteLabelResponseSchema = SuccessResponseSchema(
  z.object({ message: z.literal("Label deleted") })
);

// ---------------------------------------------------------------------------
// POST /api/v1/projects/:projectId/tasks/:taskId/labels
// Assign a label to a task.
// Auth: requireAuth + requireProjectRole('admin' | 'member')
// ---------------------------------------------------------------------------

export const AssignLabelRequestSchema = z.object({
  labelId: z.string().uuid(),
});

export const AssignLabelResponseSchema = SuccessResponseSchema(
  z.object({
    taskId: z.string().uuid(),
    labels: z.array(LabelSchema.pick({ id: true, name: true, color: true })),
  })
);

// ---------------------------------------------------------------------------
// DELETE /api/v1/projects/:projectId/tasks/:taskId/labels/:labelId
// Remove a label from a task.
// Auth: requireAuth + requireProjectRole('admin' | 'member')
// ---------------------------------------------------------------------------

export const UnassignLabelResponseSchema = SuccessResponseSchema(
  z.object({
    taskId: z.string().uuid(),
    labels: z.array(LabelSchema.pick({ id: true, name: true, color: true })),
  })
);


// ============================================================================
// 8. COMMENTS — /api/v1/tasks/:taskId/comments
// ============================================================================
// Rate limit: Tier 3 (read), Tier 2 (write)

export const CommentSchema = z.object({
  id: z.string().uuid(),
  taskId: z.string().uuid(),
  content: z.string(),               // Markdown
  authorId: z.string().uuid(),
  author: z.object({
    id: z.string().uuid(),
    name: z.string(),
    avatarUrl: z.string().url().nullable(),
  }),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
  isEdited: z.boolean(),
});

// ---------------------------------------------------------------------------
// POST /api/v1/tasks/:taskId/comments
// Create a comment on a task.
// Auth: requireAuth + requireProjectMember via parent task
// ---------------------------------------------------------------------------

export const CreateCommentRequestSchema = z.object({
  content: z.string().min(1).max(5000).trim(),
});

export const CreateCommentResponseSchema = SuccessResponseSchema(CommentSchema);

// ---------------------------------------------------------------------------
// GET /api/v1/tasks/:taskId/comments
// List all comments on a task, paginated.
// Auth: requireAuth + requireProjectMember via parent task
// Query: ?page=1&limit=20&sortOrder=asc (oldest first by default)
// ---------------------------------------------------------------------------

export const ListCommentsQuerySchema = PaginationQuerySchema.extend({
  sortOrder: SortOrderEnum.default("asc"), // Comments: oldest first
});

// Response: PaginatedResponseSchema(CommentSchema)

// ---------------------------------------------------------------------------
// PATCH /api/v1/tasks/:taskId/comments/:commentId
// Edit a comment. Only the author can edit.
// Auth: requireAuth + requireCommentAuthor
// ---------------------------------------------------------------------------

export const UpdateCommentRequestSchema = z.object({
  content: z.string().min(1).max(5000).trim(),
});

export const UpdateCommentResponseSchema = SuccessResponseSchema(CommentSchema);

// ---------------------------------------------------------------------------
// DELETE /api/v1/tasks/:taskId/comments/:commentId
// Delete a comment. Author or project admin can delete.
// Auth: requireAuth + (requireCommentAuthor | requireProjectRole('admin'))
// ---------------------------------------------------------------------------

export const DeleteCommentResponseSchema = SuccessResponseSchema(
  z.object({ message: z.literal("Comment deleted") })
);


// ============================================================================
// 9. ACTIVITY — /api/v1/activity
// ============================================================================
// Rate limit: Tier 3

export const ActivityActionEnum = z.enum([
  // Tasks
  "task.created",
  "task.updated",
  "task.deleted",
  "task.status_changed",
  "task.priority_changed",
  "task.assignee_changed",
  "task.moved",
  // Subtasks
  "subtask.created",
  "subtask.completed",
  "subtask.uncompleted",
  "subtask.deleted",
  // Comments
  "comment.created",
  "comment.updated",
  "comment.deleted",
  // Labels
  "label.assigned",
  "label.unassigned",
  // Members
  "member.invited",
  "member.removed",
  "member.role_changed",
  // Project
  "project.created",
  "project.updated",
  "project.archived",
  "project.unarchived",
]);

export const ActivityEntrySchema = z.object({
  id: z.string().uuid(),
  action: ActivityActionEnum,
  actorId: z.string().uuid(),
  actor: z.object({
    id: z.string().uuid(),
    name: z.string(),
    avatarUrl: z.string().url().nullable(),
  }),
  projectId: z.string().uuid(),
  taskId: z.string().uuid().nullable(),
  metadata: z.record(z.unknown()),    // Action-specific data
  createdAt: z.string().datetime(),
});

/**
 * Activity metadata examples:
 *
 * task.status_changed:
 *   { from: "TODO", to: "IN_PROGRESS", taskTitle: "Fix header" }
 *
 * task.assignee_changed:
 *   { from: { id, name } | null, to: { id, name } | null, taskTitle: "..." }
 *
 * member.role_changed:
 *   { userId: "...", userName: "...", from: "member", to: "admin" }
 *
 * comment.created:
 *   { taskTitle: "...", preview: "First 100 chars..." }
 */

// ---------------------------------------------------------------------------
// GET /api/v1/projects/:projectId/activity
// Fetch activity log for a project.
// Auth: requireAuth + requireProjectMember
// Query: ?page=1&limit=30&action=task.created,task.updated&actorId=uuid
// ---------------------------------------------------------------------------

export const ProjectActivityQuerySchema = PaginationQuerySchema.extend({
  limit: z.coerce.number().int().min(1).max(100).default(30),
  action: z
    .string()
    .transform((v) => v.split(","))
    .optional(),
  actorId: z.string().uuid().optional(),
  taskId: z.string().uuid().optional(),
  since: z.string().datetime().optional(),   // Only entries after this time
});

// Response: PaginatedResponseSchema(ActivityEntrySchema)

// ---------------------------------------------------------------------------
// GET /api/v1/tasks/:taskId/activity
// Fetch activity log for a specific task.
// Auth: requireAuth + requireProjectMember via parent task
// Query: ?page=1&limit=30
// ---------------------------------------------------------------------------

// Response: PaginatedResponseSchema(ActivityEntrySchema)


// ============================================================================
// 10. SEARCH — /api/v1/search
// ============================================================================
// Rate limit: Tier 4 (30 req/min)

// ---------------------------------------------------------------------------
// GET /api/v1/search
// Global search across tasks, projects, and members.
// Auth: requireAuth
// Only returns results from projects the user has access to.
// Query: ?q=<query>&type=tasks,projects,members&limit=10
// ---------------------------------------------------------------------------

export const SearchQuerySchema = z.object({
  q: z.string().min(1).max(100).trim(),
  type: z
    .string()
    .transform((v) => v.split(","))
    .pipe(z.array(z.enum(["tasks", "projects", "members"])))
    .optional()
    .default(["tasks", "projects", "members"] as unknown as string),
  limit: z.coerce.number().int().min(1).max(50).default(10),
});

export const SearchResultSchema = z.object({
  tasks: z
    .array(
      z.object({
        id: z.string().uuid(),
        title: z.string(),
        status: TaskStatusEnum,
        priority: TaskPriorityEnum,
        projectId: z.string().uuid(),
        projectName: z.string(),
        assignee: UserSummarySchema.pick({ id: true, name: true, avatarUrl: true }).nullable(),
      })
    )
    .optional(),
  projects: z
    .array(
      z.object({
        id: z.string().uuid(),
        name: z.string(),
        icon: z.string().nullable(),
        color: z.string().nullable(),
        memberCount: z.number(),
      })
    )
    .optional(),
  members: z
    .array(
      z.object({
        id: z.string().uuid(),
        name: z.string(),
        email: z.string().email(),
        avatarUrl: z.string().url().nullable(),
      })
    )
    .optional(),
});

export const SearchResponseSchema = SuccessResponseSchema(SearchResultSchema);


// ============================================================================
// 11. ANALYTICS — /api/v1/projects/:projectId/analytics
// ============================================================================
// Rate limit: Tier 3

// ---------------------------------------------------------------------------
// GET /api/v1/projects/:projectId/analytics/completion
// Tasks completed over time (area chart data).
// Auth: requireAuth + requireProjectMember
// Query: ?period=30d|90d|6m|1y&granularity=day|week|month
// ---------------------------------------------------------------------------

export const AnalyticsCompletionQuerySchema = z.object({
  period: z.enum(["7d", "30d", "90d", "6m", "1y"]).default("30d"),
  granularity: z.enum(["day", "week", "month"]).default("day"),
});

export const AnalyticsCompletionResponseSchema = SuccessResponseSchema(
  z.object({
    series: z.array(
      z.object({
        date: z.string(),            // ISO date string
        completed: z.number().int().nonnegative(),
        created: z.number().int().nonnegative(),
      })
    ),
    totals: z.object({
      completed: z.number().int().nonnegative(),
      created: z.number().int().nonnegative(),
    }),
  })
);

// ---------------------------------------------------------------------------
// GET /api/v1/projects/:projectId/analytics/by-status
// Tasks grouped by status (donut chart data).
// Auth: requireAuth + requireProjectMember
// ---------------------------------------------------------------------------

export const AnalyticsByStatusResponseSchema = SuccessResponseSchema(
  z.object({
    statuses: z.array(
      z.object({
        status: TaskStatusEnum,
        count: z.number().int().nonnegative(),
        percentage: z.number().min(0).max(100),
      })
    ),
    total: z.number().int().nonnegative(),
  })
);

// ---------------------------------------------------------------------------
// GET /api/v1/projects/:projectId/analytics/by-priority
// Tasks grouped by priority (bar chart data).
// Auth: requireAuth + requireProjectMember
// ---------------------------------------------------------------------------

export const AnalyticsByPriorityResponseSchema = SuccessResponseSchema(
  z.object({
    priorities: z.array(
      z.object({
        priority: TaskPriorityEnum,
        count: z.number().int().nonnegative(),
        percentage: z.number().min(0).max(100),
      })
    ),
    total: z.number().int().nonnegative(),
  })
);

// ---------------------------------------------------------------------------
// GET /api/v1/projects/:projectId/analytics/velocity
// Team velocity — tasks completed per week (line chart data).
// Auth: requireAuth + requireProjectMember
// Query: ?weeks=12
// ---------------------------------------------------------------------------

export const AnalyticsVelocityQuerySchema = z.object({
  weeks: z.coerce.number().int().min(4).max(52).default(12),
});

export const AnalyticsVelocityResponseSchema = SuccessResponseSchema(
  z.object({
    series: z.array(
      z.object({
        weekStart: z.string(),       // ISO date, Monday
        weekEnd: z.string(),         // ISO date, Sunday
        completed: z.number().int().nonnegative(),
      })
    ),
    average: z.number().nonnegative(),
    trend: z.enum(["up", "down", "stable"]),
  })
);


// ============================================================================
// 12. WEBSOCKET — Socket.io Events
// ============================================================================

/**
 * Connection:
 *   Client connects to the Socket.io server at ws://<host> with:
 *     { auth: { token: "<accessToken>" } }
 *
 *   The server validates the JWT on connection. Invalid token = disconnect.
 *
 * Rooms:
 *   project:<projectId>    — joined when user opens a project
 *   task:<taskId>          — joined when user opens task detail panel
 *   user:<userId>          — private room for user-specific events
 *
 * Client-to-server events:
 *   "join:project"         { projectId: string }
 *   "leave:project"        { projectId: string }
 *   "join:task"            { taskId: string }
 *   "leave:task"           { taskId: string }
 *   "presence:heartbeat"   { projectId: string }         — sent every 30s
 *   "typing:start"         { taskId: string }             — typing in comment
 *   "typing:stop"          { taskId: string }
 */

// ---------------------------------------------------------------------------
// Server-to-client event payloads
// ---------------------------------------------------------------------------

// Task events — broadcast to project:<projectId>
export const WsTaskCreatedPayload = z.object({
  event: z.literal("task:created"),
  data: TaskSchema,
});

export const WsTaskUpdatedPayload = z.object({
  event: z.literal("task:updated"),
  data: z.object({
    task: TaskSchema,
    changes: z.record(z.object({
      from: z.unknown(),
      to: z.unknown(),
    })),
  }),
});

export const WsTaskDeletedPayload = z.object({
  event: z.literal("task:deleted"),
  data: z.object({
    taskId: z.string().uuid(),
    projectId: z.string().uuid(),
  }),
});

export const WsTaskMovedPayload = z.object({
  event: z.literal("task:moved"),
  data: z.object({
    taskId: z.string().uuid(),
    projectId: z.string().uuid(),
    fromStatus: TaskStatusEnum,
    toStatus: TaskStatusEnum,
    position: z.number(),
  }),
});

export const WsBulkTasksUpdatedPayload = z.object({
  event: z.literal("tasks:bulk_updated"),
  data: z.object({
    taskIds: z.array(z.string().uuid()),
    projectId: z.string().uuid(),
    action: z.string(),
  }),
});

// Subtask events — broadcast to task:<taskId> AND project:<projectId>
export const WsSubtaskCreatedPayload = z.object({
  event: z.literal("subtask:created"),
  data: z.object({
    subtask: SubtaskSchema,
    taskId: z.string().uuid(),
    projectId: z.string().uuid(),
  }),
});

export const WsSubtaskUpdatedPayload = z.object({
  event: z.literal("subtask:updated"),
  data: z.object({
    subtask: SubtaskSchema,
    taskId: z.string().uuid(),
    projectId: z.string().uuid(),
  }),
});

export const WsSubtaskDeletedPayload = z.object({
  event: z.literal("subtask:deleted"),
  data: z.object({
    subtaskId: z.string().uuid(),
    taskId: z.string().uuid(),
    projectId: z.string().uuid(),
  }),
});

// Comment events — broadcast to task:<taskId>
export const WsCommentCreatedPayload = z.object({
  event: z.literal("comment:created"),
  data: z.object({
    comment: CommentSchema,
    taskId: z.string().uuid(),
  }),
});

export const WsCommentUpdatedPayload = z.object({
  event: z.literal("comment:updated"),
  data: z.object({
    comment: CommentSchema,
    taskId: z.string().uuid(),
  }),
});

export const WsCommentDeletedPayload = z.object({
  event: z.literal("comment:deleted"),
  data: z.object({
    commentId: z.string().uuid(),
    taskId: z.string().uuid(),
  }),
});

// Label events — broadcast to project:<projectId>
export const WsLabelCreatedPayload = z.object({
  event: z.literal("label:created"),
  data: LabelSchema,
});

export const WsLabelUpdatedPayload = z.object({
  event: z.literal("label:updated"),
  data: LabelSchema,
});

export const WsLabelDeletedPayload = z.object({
  event: z.literal("label:deleted"),
  data: z.object({
    labelId: z.string().uuid(),
    projectId: z.string().uuid(),
  }),
});

// Member events — broadcast to project:<projectId>
export const WsMemberJoinedPayload = z.object({
  event: z.literal("member:joined"),
  data: ProjectMemberSchema,
});

export const WsMemberRemovedPayload = z.object({
  event: z.literal("member:removed"),
  data: z.object({
    userId: z.string().uuid(),
    projectId: z.string().uuid(),
  }),
});

export const WsMemberRoleChangedPayload = z.object({
  event: z.literal("member:role_changed"),
  data: z.object({
    userId: z.string().uuid(),
    projectId: z.string().uuid(),
    role: ProjectRoleEnum,
  }),
});

// Presence events — broadcast to project:<projectId>
export const WsPresenceUpdatePayload = z.object({
  event: z.literal("presence:update"),
  data: z.object({
    userId: z.string().uuid(),
    projectId: z.string().uuid(),
    isOnline: z.boolean(),
    lastSeenAt: z.string().datetime(),
  }),
});

// Typing indicator — broadcast to task:<taskId> (excluding sender)
export const WsTypingPayload = z.object({
  event: z.literal("typing:update"),
  data: z.object({
    userId: z.string().uuid(),
    userName: z.string(),
    taskId: z.string().uuid(),
    isTyping: z.boolean(),
  }),
});

// Project events — broadcast to project:<projectId>
export const WsProjectUpdatedPayload = z.object({
  event: z.literal("project:updated"),
  data: ProjectSchema,
});

export const WsProjectArchivedPayload = z.object({
  event: z.literal("project:archived"),
  data: z.object({
    projectId: z.string().uuid(),
    isArchived: z.boolean(),
  }),
});

// Activity event — broadcast to project:<projectId>
export const WsActivityPayload = z.object({
  event: z.literal("activity:new"),
  data: ActivityEntrySchema,
});

// Notification — sent to user:<userId> room (private)
export const WsNotificationPayload = z.object({
  event: z.literal("notification"),
  data: z.object({
    type: z.enum(["assigned", "mentioned", "comment", "status_change"]),
    message: z.string(),
    taskId: z.string().uuid().optional(),
    projectId: z.string().uuid(),
    actorId: z.string().uuid(),
    actorName: z.string(),
    createdAt: z.string().datetime(),
  }),
});


// ============================================================================
// COMPLETE ENDPOINT REGISTRY
// ============================================================================

/**
 * All 47 REST endpoints in one table.
 *
 * Legend:
 *   [P] = Public (no auth)
 *   [A] = requireAuth
 *   [M] = requireAuth + requireProjectMember
 *   [W] = requireAuth + requireProjectRole('admin' | 'member')
 *   [O] = requireAuth + requireProjectRole('admin')
 *
 * ┌─────────┬──────────────────────────────────────────────────────────────┬──────┬──────────┐
 * │ METHOD  │ PATH                                                       │ AUTH │ RATE     │
 * ├─────────┼──────────────────────────────────────────────────────────────┼──────┼──────────┤
 * │ AUTH                                                                                    │
 * ├─────────┼──────────────────────────────────────────────────────────────┼──────┼──────────┤
 * │ POST    │ /api/v1/auth/signup                                        │ [P]  │ Tier 1   │
 * │ POST    │ /api/v1/auth/login                                         │ [P]  │ Tier 1   │
 * │ POST    │ /api/v1/auth/refresh                                       │ [P]  │ Tier 1   │
 * │ POST    │ /api/v1/auth/logout                                        │ [A]  │ Tier 1   │
 * │ GET     │ /api/v1/auth/me                                            │ [A]  │ Tier 3   │
 * ├─────────┼──────────────────────────────────────────────────────────────┼──────┼──────────┤
 * │ USERS                                                                                   │
 * ├─────────┼──────────────────────────────────────────────────────────────┼──────┼──────────┤
 * │ PATCH   │ /api/v1/users/profile                                      │ [A]  │ Tier 2   │
 * │ PATCH   │ /api/v1/users/password                                     │ [A]  │ Tier 2   │
 * │ POST    │ /api/v1/users/avatar                                       │ [A]  │ Tier 5   │
 * │ DELETE  │ /api/v1/users/avatar                                       │ [A]  │ Tier 2   │
 * │ GET     │ /api/v1/users                                              │ [A]  │ Tier 3   │
 * │ GET     │ /api/v1/users/presence                                     │ [A]  │ Tier 3   │
 * │ GET     │ /api/v1/users/me/tasks                                     │ [A]  │ Tier 3   │
 * ├─────────┼──────────────────────────────────────────────────────────────┼──────┼──────────┤
 * │ PROJECTS                                                                                │
 * ├─────────┼──────────────────────────────────────────────────────────────┼──────┼──────────┤
 * │ POST    │ /api/v1/projects                                           │ [A]  │ Tier 2   │
 * │ GET     │ /api/v1/projects                                           │ [A]  │ Tier 3   │
 * │ GET     │ /api/v1/projects/:projectId                                │ [M]  │ Tier 3   │
 * │ PATCH   │ /api/v1/projects/:projectId                                │ [O]  │ Tier 2   │
 * │ DELETE  │ /api/v1/projects/:projectId                                │ [O]  │ Tier 2   │
 * │ PATCH   │ /api/v1/projects/:projectId/archive                        │ [O]  │ Tier 2   │
 * ├─────────┼──────────────────────────────────────────────────────────────┼──────┼──────────┤
 * │ PROJECT MEMBERS                                                                         │
 * ├─────────┼──────────────────────────────────────────────────────────────┼──────┼──────────┤
 * │ GET     │ /api/v1/projects/:projectId/members                        │ [M]  │ Tier 3   │
 * │ POST    │ /api/v1/projects/:projectId/members                        │ [O]  │ Tier 2   │
 * │ PATCH   │ /api/v1/projects/:projectId/members/:userId                │ [O]  │ Tier 2   │
 * │ DELETE  │ /api/v1/projects/:projectId/members/:userId                │ [O]  │ Tier 2   │
 * ├─────────┼──────────────────────────────────────────────────────────────┼──────┼──────────┤
 * │ TASKS                                                                                   │
 * ├─────────┼──────────────────────────────────────────────────────────────┼──────┼──────────┤
 * │ POST    │ /api/v1/projects/:projectId/tasks                          │ [W]  │ Tier 2   │
 * │ GET     │ /api/v1/projects/:projectId/tasks                          │ [M]  │ Tier 3   │
 * │ GET     │ /api/v1/projects/:projectId/tasks/board                    │ [M]  │ Tier 3   │
 * │ GET     │ /api/v1/projects/:projectId/tasks/:taskId                  │ [M]  │ Tier 3   │
 * │ PATCH   │ /api/v1/projects/:projectId/tasks/:taskId                  │ [W]  │ Tier 2   │
 * │ DELETE  │ /api/v1/projects/:projectId/tasks/:taskId                  │ [W]  │ Tier 2   │
 * │ PATCH   │ /api/v1/projects/:projectId/tasks/:taskId/reorder          │ [W]  │ Tier 2   │
 * │ POST    │ /api/v1/projects/:projectId/tasks/bulk                     │ [W]  │ Tier 2   │
 * ├─────────┼──────────────────────────────────────────────────────────────┼──────┼──────────┤
 * │ SUBTASKS                                                                                │
 * ├─────────┼──────────────────────────────────────────────────────────────┼──────┼──────────┤
 * │ POST    │ /api/v1/tasks/:taskId/subtasks                             │ [W]  │ Tier 2   │
 * │ GET     │ /api/v1/tasks/:taskId/subtasks                             │ [M]  │ Tier 3   │
 * │ PATCH   │ /api/v1/tasks/:taskId/subtasks/:subtaskId                  │ [W]  │ Tier 2   │
 * │ PATCH   │ /api/v1/tasks/:taskId/subtasks/:subtaskId/toggle           │ [W]  │ Tier 2   │
 * │ DELETE  │ /api/v1/tasks/:taskId/subtasks/:subtaskId                  │ [W]  │ Tier 2   │
 * │ PATCH   │ /api/v1/tasks/:taskId/subtasks/reorder                     │ [W]  │ Tier 2   │
 * ├─────────┼──────────────────────────────────────────────────────────────┼──────┼──────────┤
 * │ LABELS                                                                                  │
 * ├─────────┼──────────────────────────────────────────────────────────────┼──────┼──────────┤
 * │ POST    │ /api/v1/projects/:projectId/labels                         │ [W]  │ Tier 2   │
 * │ GET     │ /api/v1/projects/:projectId/labels                         │ [M]  │ Tier 3   │
 * │ PATCH   │ /api/v1/projects/:projectId/labels/:labelId                │ [W]  │ Tier 2   │
 * │ DELETE  │ /api/v1/projects/:projectId/labels/:labelId                │ [O]  │ Tier 2   │
 * │ POST    │ /api/v1/projects/:projectId/tasks/:taskId/labels           │ [W]  │ Tier 2   │
 * │ DELETE  │ /api/v1/projects/:projectId/tasks/:taskId/labels/:labelId  │ [W]  │ Tier 2   │
 * ├─────────┼──────────────────────────────────────────────────────────────┼──────┼──────────┤
 * │ COMMENTS                                                                                │
 * ├─────────┼──────────────────────────────────────────────────────────────┼──────┼──────────┤
 * │ POST    │ /api/v1/tasks/:taskId/comments                             │ [M]  │ Tier 2   │
 * │ GET     │ /api/v1/tasks/:taskId/comments                             │ [M]  │ Tier 3   │
 * │ PATCH   │ /api/v1/tasks/:taskId/comments/:commentId                  │ [A]* │ Tier 2   │
 * │ DELETE  │ /api/v1/tasks/:taskId/comments/:commentId                  │ [A]* │ Tier 2   │
 * ├─────────┼──────────────────────────────────────────────────────────────┼──────┼──────────┤
 * │ ACTIVITY                                                                                │
 * ├─────────┼──────────────────────────────────────────────────────────────┼──────┼──────────┤
 * │ GET     │ /api/v1/projects/:projectId/activity                       │ [M]  │ Tier 3   │
 * │ GET     │ /api/v1/tasks/:taskId/activity                             │ [M]  │ Tier 3   │
 * ├─────────┼──────────────────────────────────────────────────────────────┼──────┼──────────┤
 * │ SEARCH                                                                                  │
 * ├─────────┼──────────────────────────────────────────────────────────────┼──────┼──────────┤
 * │ GET     │ /api/v1/search                                             │ [A]  │ Tier 4   │
 * ├─────────┼──────────────────────────────────────────────────────────────┼──────┼──────────┤
 * │ ANALYTICS                                                                               │
 * ├─────────┼──────────────────────────────────────────────────────────────┼──────┼──────────┤
 * │ GET     │ /api/v1/projects/:projectId/analytics/completion            │ [M]  │ Tier 3   │
 * │ GET     │ /api/v1/projects/:projectId/analytics/by-status             │ [M]  │ Tier 3   │
 * │ GET     │ /api/v1/projects/:projectId/analytics/by-priority           │ [M]  │ Tier 3   │
 * │ GET     │ /api/v1/projects/:projectId/analytics/velocity              │ [M]  │ Tier 3   │
 * └─────────┴──────────────────────────────────────────────────────────────┴──────┴──────────┘
 *
 * [A]* = requireAuth + author-or-admin check
 *
 * Total: 47 REST endpoints + 12 WebSocket event types
 */


// ============================================================================
// WEBSOCKET EVENT REGISTRY (summary)
// ============================================================================

/**
 * Server-to-Client Events:
 *
 * ┌──────────────────────────┬────────────────────────────────────┬───────────────────────────┐
 * │ EVENT NAME               │ PAYLOAD SCHEMA                     │ BROADCAST ROOM            │
 * ├──────────────────────────┼────────────────────────────────────┼───────────────────────────┤
 * │ task:created             │ WsTaskCreatedPayload               │ project:<projectId>       │
 * │ task:updated             │ WsTaskUpdatedPayload               │ project:<projectId>       │
 * │ task:deleted             │ WsTaskDeletedPayload               │ project:<projectId>       │
 * │ task:moved               │ WsTaskMovedPayload                 │ project:<projectId>       │
 * │ tasks:bulk_updated       │ WsBulkTasksUpdatedPayload          │ project:<projectId>       │
 * │ subtask:created          │ WsSubtaskCreatedPayload            │ task + project rooms      │
 * │ subtask:updated          │ WsSubtaskUpdatedPayload            │ task + project rooms      │
 * │ subtask:deleted          │ WsSubtaskDeletedPayload            │ task + project rooms      │
 * │ comment:created          │ WsCommentCreatedPayload            │ task:<taskId>             │
 * │ comment:updated          │ WsCommentUpdatedPayload            │ task:<taskId>             │
 * │ comment:deleted          │ WsCommentDeletedPayload            │ task:<taskId>             │
 * │ label:created            │ WsLabelCreatedPayload              │ project:<projectId>       │
 * │ label:updated            │ WsLabelUpdatedPayload              │ project:<projectId>       │
 * │ label:deleted            │ WsLabelDeletedPayload              │ project:<projectId>       │
 * │ member:joined            │ WsMemberJoinedPayload              │ project:<projectId>       │
 * │ member:removed           │ WsMemberRemovedPayload             │ project:<projectId>       │
 * │ member:role_changed      │ WsMemberRoleChangedPayload         │ project:<projectId>       │
 * │ presence:update          │ WsPresenceUpdatePayload            │ project:<projectId>       │
 * │ typing:update            │ WsTypingPayload                    │ task:<taskId>             │
 * │ project:updated          │ WsProjectUpdatedPayload            │ project:<projectId>       │
 * │ project:archived         │ WsProjectArchivedPayload           │ project:<projectId>       │
 * │ activity:new             │ WsActivityPayload                  │ project:<projectId>       │
 * │ notification             │ WsNotificationPayload              │ user:<userId> (private)   │
 * └──────────────────────────┴────────────────────────────────────┴───────────────────────────┘
 *
 * Client-to-Server Events:
 *
 * ┌──────────────────────────┬────────────────────────────────────┐
 * │ EVENT NAME               │ PAYLOAD                            │
 * ├──────────────────────────┼────────────────────────────────────┤
 * │ join:project             │ { projectId: string }              │
 * │ leave:project            │ { projectId: string }              │
 * │ join:task                │ { taskId: string }                 │
 * │ leave:task               │ { taskId: string }                 │
 * │ presence:heartbeat       │ { projectId: string }              │
 * │ typing:start             │ { taskId: string }                 │
 * │ typing:stop              │ { taskId: string }                 │
 * └──────────────────────────┴────────────────────────────────────┘
 */
