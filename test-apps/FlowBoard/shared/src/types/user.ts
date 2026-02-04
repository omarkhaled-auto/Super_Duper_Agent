// =============================================================================
// User Types — API-level (never includes passwordHash)
// =============================================================================

/** Full user object returned by the API (excludes sensitive fields) */
export interface User {
  id: string;
  email: string;
  name: string;
  avatarUrl: string | null;
  createdAt: string; // ISO 8601
  updatedAt: string;
}

/** Lightweight user reference for embedding in other objects (e.g. assignee) */
export interface UserProfile {
  id: string;
  name: string;
  email: string;
  avatarUrl: string | null;
}
