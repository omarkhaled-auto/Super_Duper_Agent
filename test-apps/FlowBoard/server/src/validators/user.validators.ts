// =============================================================================
// User Validators — Zod schemas for user endpoints
// =============================================================================

import { z } from "zod";

// -- Update Profile -----------------------------------------------------------

export const updateProfileSchema = z.object({
  name: z
    .string()
    .min(1, "Name must be at least 1 character")
    .max(100, "Name must be at most 100 characters")
    .optional(),
  avatar: z
    .string()
    .url("Avatar must be a valid URL")
    .nullable()
    .optional(),
});

export type UpdateProfileInput = z.infer<typeof updateProfileSchema>;

// -- Search Query (used by search routes) ------------------------------------

export const searchQuerySchema = z.object({
  q: z
    .string({ required_error: "Search query is required" })
    .min(1, "Search query must not be empty")
    .max(200, "Search query must be at most 200 characters"),
});

export type SearchQueryInput = z.infer<typeof searchQuerySchema>;
