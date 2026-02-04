// =============================================================================
// Server-Specific Types
//
// Express request extensions, authentication payloads, and shared server types.
// =============================================================================

// ---------------------------------------------------------------------------
// Auth payload carried in JWTs and attached to requests
// ---------------------------------------------------------------------------
export interface AuthPayload {
  userId: string;
  email: string;
}

// ---------------------------------------------------------------------------
// Extend the Express Request interface globally so `req.user` is typed
// throughout the application without per-file casting.
// ---------------------------------------------------------------------------
declare global {
  namespace Express {
    interface Request {
      /** Populated by auth middleware when a valid JWT is present */
      user?: AuthPayload;
    }
  }
}

// ---------------------------------------------------------------------------
// Standard API error response shape returned by the error handler
// ---------------------------------------------------------------------------
export interface ApiErrorResponse {
  error: string;
  details?: Array<{
    field: string;
    message: string;
    code: string;
  }>;
}

// ---------------------------------------------------------------------------
// Standard paginated list response wrapper
// ---------------------------------------------------------------------------
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// ---------------------------------------------------------------------------
// Generic ID parameter (used in route param validation)
// ---------------------------------------------------------------------------
export interface IdParam {
  id: string;
}

// ---------------------------------------------------------------------------
// Socket.io custom socket data (attached after auth handshake)
// ---------------------------------------------------------------------------
export interface SocketData {
  userId: string;
  email: string;
}
