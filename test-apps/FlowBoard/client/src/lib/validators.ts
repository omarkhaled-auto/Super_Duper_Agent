import { z } from "zod";

/** ── Auth ──────────────────────────────────────────────────── */
export const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

export const signupSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Invalid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

/** ── Tasks ─────────────────────────────────────────────────── */
export const createTaskSchema = z.object({
  title: z.string().min(1, "Title is required").max(200),
  description: z.string().optional(),
  status: z.enum(["BACKLOG", "TODO", "IN_PROGRESS", "IN_REVIEW", "DONE"]).optional(),
  priority: z.enum(["URGENT", "HIGH", "MEDIUM", "LOW"]).optional(),
  assigneeId: z.string().uuid().optional(),
  projectId: z.string().uuid(),
  dueDate: z.string().datetime().optional(),
  labels: z.array(z.string()).optional(),
});

export const updateTaskSchema = createTaskSchema.partial().omit({ projectId: true });

/** ── Projects ──────────────────────────────────────────────── */
export const createProjectSchema = z.object({
  name: z.string().min(1, "Project name is required").max(100),
  description: z.string().max(500).optional(),
  icon: z.string().max(10).optional(),
  color: z.string().regex(/^#[0-9a-fA-F]{6}$/, "Invalid hex color").optional(),
});

export const updateProjectSchema = createProjectSchema.partial();

/** ── Comments ──────────────────────────────────────────────── */
export const createCommentSchema = z.object({
  content: z.string().min(1, "Comment cannot be empty").max(5000),
  taskId: z.string().uuid(),
});

export type LoginInput = z.infer<typeof loginSchema>;
export type SignupInput = z.infer<typeof signupSchema>;
export type CreateTaskInput = z.infer<typeof createTaskSchema>;
export type UpdateTaskInput = z.infer<typeof updateTaskSchema>;
export type CreateProjectInput = z.infer<typeof createProjectSchema>;
export type UpdateProjectInput = z.infer<typeof updateProjectSchema>;
export type CreateCommentInput = z.infer<typeof createCommentSchema>;
