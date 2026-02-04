// =============================================================================
// Project Zod Validators
// =============================================================================

import { z } from "zod";

// ── Create Project ──────────────────────────────────────────────────────────
export const createProjectSchema = z.object({
  name: z
    .string()
    .min(1, "Project name is required")
    .max(100, "Project name must be 100 characters or fewer"),
  description: z
    .string()
    .max(500, "Description must be 500 characters or fewer")
    .optional()
    .nullable(),
  icon: z.string().max(50).optional().default("folder"),
  color: z
    .string()
    .regex(/^#[0-9A-Fa-f]{6}$/, "Color must be a valid hex color")
    .optional()
    .default("#8B5CF6"),
});

export type CreateProjectInput = z.infer<typeof createProjectSchema>;

// ── Update Project ──────────────────────────────────────────────────────────
export const updateProjectSchema = z.object({
  name: z
    .string()
    .min(1, "Project name is required")
    .max(100, "Project name must be 100 characters or fewer")
    .optional(),
  description: z
    .string()
    .max(500, "Description must be 500 characters or fewer")
    .optional()
    .nullable(),
  icon: z.string().max(50).optional(),
  color: z
    .string()
    .regex(/^#[0-9A-Fa-f]{6}$/, "Color must be a valid hex color")
    .optional(),
});

export type UpdateProjectInput = z.infer<typeof updateProjectSchema>;

// ── Add Member ──────────────────────────────────────────────────────────────
export const addMemberSchema = z.object({
  email: z.string().email("Valid email is required"),
  role: z.enum(["ADMIN", "MEMBER", "VIEWER"]).default("MEMBER"),
});

export type AddMemberInput = z.infer<typeof addMemberSchema>;

// ── Update Member Role ──────────────────────────────────────────────────────
export const updateMemberRoleSchema = z.object({
  role: z.enum(["ADMIN", "MEMBER", "VIEWER"]),
});

export type UpdateMemberRoleInput = z.infer<typeof updateMemberRoleSchema>;

// ── Create Label ────────────────────────────────────────────────────────────
export const createLabelSchema = z.object({
  name: z
    .string()
    .min(1, "Label name is required")
    .max(50, "Label name must be 50 characters or fewer"),
  color: z
    .string()
    .regex(/^#[0-9A-Fa-f]{6}$/, "Color must be a valid hex color"),
});

export type CreateLabelInput = z.infer<typeof createLabelSchema>;
