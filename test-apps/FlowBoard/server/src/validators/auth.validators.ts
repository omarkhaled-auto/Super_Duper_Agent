// =============================================================================
// Auth Validators — Zod schemas for authentication endpoints
// =============================================================================

import { z } from "zod";

// -- Signup -------------------------------------------------------------------

export const signupSchema = z.object({
  email: z
    .string({ required_error: "Email is required" })
    .email("Invalid email address"),
  password: z
    .string({ required_error: "Password is required" })
    .min(8, "Password must be at least 8 characters"),
  name: z
    .string({ required_error: "Name is required" })
    .min(1, "Name must be at least 1 character"),
});

export type SignupInput = z.infer<typeof signupSchema>;

// -- Login --------------------------------------------------------------------

export const loginSchema = z.object({
  email: z
    .string({ required_error: "Email is required" })
    .email("Invalid email address"),
  password: z
    .string({ required_error: "Password is required" })
    .min(1, "Password is required"),
});

export type LoginInput = z.infer<typeof loginSchema>;

// -- Refresh ------------------------------------------------------------------

export const refreshSchema = z.object({
  refreshToken: z.string().optional(),
});

export type RefreshInput = z.infer<typeof refreshSchema>;
