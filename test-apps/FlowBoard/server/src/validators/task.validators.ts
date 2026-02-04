// =============================================================================
// Task Zod Validators
// =============================================================================

import { z } from "zod";

const taskStatusEnum = z.enum([
  "BACKLOG",
  "TODO",
  "IN_PROGRESS",
  "IN_REVIEW",
  "DONE",
]);

const taskPriorityEnum = z.enum(["URGENT", "HIGH", "MEDIUM", "LOW"]);

// ── Create Task ─────────────────────────────────────────────────────────────
export const createTaskSchema = z.object({
  title: z
    .string()
    .min(1, "Task title is required")
    .max(200, "Task title must be 200 characters or fewer"),
  description: z
    .string()
    .max(5000, "Description must be 5000 characters or fewer")
    .optional()
    .nullable(),
  status: taskStatusEnum.optional().default("BACKLOG"),
  priority: taskPriorityEnum.optional().default("MEDIUM"),
  assigneeId: z.string().cuid().optional().nullable(),
  dueDate: z
    .string()
    .datetime({ offset: true })
    .optional()
    .nullable()
    .transform((val) => (val ? new Date(val) : null)),
  labelIds: z.array(z.string().cuid()).optional(),
});

export type CreateTaskInput = z.infer<typeof createTaskSchema>;

// ── Update Task ─────────────────────────────────────────────────────────────
export const updateTaskSchema = z.object({
  title: z
    .string()
    .min(1, "Task title is required")
    .max(200, "Task title must be 200 characters or fewer")
    .optional(),
  description: z
    .string()
    .max(5000, "Description must be 5000 characters or fewer")
    .optional()
    .nullable(),
  status: taskStatusEnum.optional(),
  priority: taskPriorityEnum.optional(),
  assigneeId: z.string().cuid().optional().nullable(),
  dueDate: z
    .string()
    .datetime({ offset: true })
    .optional()
    .nullable()
    .transform((val) => (val !== undefined ? (val ? new Date(val) : null) : undefined)),
  labelIds: z.array(z.string().cuid()).optional(),
});

export type UpdateTaskInput = z.infer<typeof updateTaskSchema>;

// ── Reorder Task ────────────────────────────────────────────────────────────
export const reorderTaskSchema = z.object({
  status: taskStatusEnum,
  position: z.number().int().min(0),
});

export type ReorderTaskInput = z.infer<typeof reorderTaskSchema>;

// ── Bulk Action ─────────────────────────────────────────────────────────────
export const bulkActionSchema = z.object({
  taskIds: z.array(z.string().cuid()).min(1, "At least one task ID is required"),
  action: z.enum(["updateStatus", "updatePriority", "updateAssignee", "delete"]),
  data: z
    .object({
      status: taskStatusEnum.optional(),
      priority: taskPriorityEnum.optional(),
      assigneeId: z.string().cuid().optional().nullable(),
    })
    .optional(),
});

export type BulkActionInput = z.infer<typeof bulkActionSchema>;

// ── List Tasks Query ────────────────────────────────────────────────────────
export const listTasksQuerySchema = z.object({
  status: taskStatusEnum.optional(),
  priority: taskPriorityEnum.optional(),
  assigneeId: z.string().optional(),
  search: z.string().optional(),
  sortBy: z
    .enum(["createdAt", "updatedAt", "priority", "dueDate", "position", "title"])
    .optional()
    .default("position"),
  sortOrder: z.enum(["asc", "desc"]).optional().default("asc"),
  page: z.coerce.number().int().min(1).optional().default(1),
  limit: z.coerce.number().int().min(1).max(100).optional().default(50),
});

export type ListTasksQuery = z.infer<typeof listTasksQuerySchema>;

// ── Create Subtask ──────────────────────────────────────────────────────────
export const createSubtaskSchema = z.object({
  title: z
    .string()
    .min(1, "Subtask title is required")
    .max(200, "Subtask title must be 200 characters or fewer"),
});

export type CreateSubtaskInput = z.infer<typeof createSubtaskSchema>;

// ── Update Subtask ──────────────────────────────────────────────────────────
export const updateSubtaskSchema = z.object({
  title: z
    .string()
    .min(1, "Subtask title is required")
    .max(200, "Subtask title must be 200 characters or fewer")
    .optional(),
  completed: z.boolean().optional(),
});

export type UpdateSubtaskInput = z.infer<typeof updateSubtaskSchema>;

// ── Set Task Labels ─────────────────────────────────────────────────────────
export const setTaskLabelsSchema = z.object({
  labelIds: z.array(z.string().cuid()),
});

export type SetTaskLabelsInput = z.infer<typeof setTaskLabelsSchema>;

// ── Create Comment ──────────────────────────────────────────────────────────
export const createCommentSchema = z.object({
  content: z
    .string()
    .min(1, "Comment cannot be empty")
    .max(5000, "Comment must be 5000 characters or fewer"),
});

export type CreateCommentInput = z.infer<typeof createCommentSchema>;
