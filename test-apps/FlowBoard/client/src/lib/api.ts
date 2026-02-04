import { API_URL } from "./utils";

// =============================================================================
// API Client -- typed fetch wrapper with auth, error handling, token refresh
// =============================================================================

/** Custom error class that carries the HTTP status code. */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly errors?: Array<{ field: string; message: string }>,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// ---------------------------------------------------------------------------
// Token helpers
// ---------------------------------------------------------------------------

const TOKEN_KEY = "flowboard_token" as const;
const REFRESH_TOKEN_KEY = "flowboard_refresh_token" as const;

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(accessToken: string, refreshToken?: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, accessToken);
  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }
  // Also set a cookie so Next.js middleware can detect the session.
  // The actual auth is still via the Authorization header; this cookie
  // is purely a flag for route-level middleware redirects.
  document.cookie = `access_token=${accessToken}; path=/; max-age=${60 * 60 * 24 * 7}; SameSite=Lax`;
}

export function clearTokens(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  // Remove the middleware flag cookie.
  document.cookie = "access_token=; path=/; max-age=0; SameSite=Lax";
}

// ---------------------------------------------------------------------------
// Refresh logic
// ---------------------------------------------------------------------------

/** Mutex to prevent multiple concurrent refresh calls. */
let refreshPromise: Promise<boolean> | null = null;

/**
 * Attempt to refresh the access token using the stored refresh token.
 * Returns `true` on success, `false` on failure.
 */
async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  try {
    const res = await fetch(`${API_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refreshToken }),
    });

    if (!res.ok) return false;

    const data = (await res.json()) as {
      accessToken: string; refreshToken?: string;
    };

    setTokens(data.accessToken, data.refreshToken);
    return true;
  } catch {
    return false;
  }
}

// ---------------------------------------------------------------------------
// Core fetch wrapper
// ---------------------------------------------------------------------------

interface RequestOptions extends Omit<RequestInit, "body"> {
  /** If `true` (default), attach the bearer token to the request. */
  auth?: boolean;
  /** Request body -- will be JSON-stringified automatically. */
  body?: unknown;
}

/**
 * Low-level fetch wrapper that handles:
 *  - Prepending the API base URL
 *  - Attaching the Authorization header
 *  - JSON serialization / parsing
 *  - 401 -> automatic token refresh -> retry once
 *  - Throwing `ApiError` on non-2xx responses
 */
async function request<T>(
  endpoint: string,
  options: RequestOptions = {},
): Promise<T> {
  const { auth = true, body, headers: customHeaders, ...rest } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(customHeaders as Record<string, string> | undefined),
  };

  if (auth) {
    const token = getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  const fetchOptions: RequestInit = {
    ...rest,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  };

  let response = await fetch(`${API_URL}${endpoint}`, fetchOptions);

  // ---- Handle 401 with automatic token refresh ----
  if (response.status === 401 && auth) {
    // Deduplicate concurrent refresh attempts
    if (!refreshPromise) {
      refreshPromise = refreshAccessToken().finally(() => {
        refreshPromise = null;
      });
    }

    const refreshed = await refreshPromise;

    if (refreshed) {
      // Retry the original request with the new token
      const newToken = getToken();
      if (newToken) {
        headers["Authorization"] = `Bearer ${newToken}`;
      }
      response = await fetch(`${API_URL}${endpoint}`, {
        ...fetchOptions,
        headers,
      });
    } else {
      // Refresh failed -- clear tokens and redirect to login
      clearTokens();
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login") && !window.location.pathname.startsWith("/signup")) {
        window.location.href = "/login";
      }
      throw new ApiError(401, "Session expired. Please log in again.");
    }
  }

  // ---- Handle non-2xx responses ----
  if (!response.ok) {
    let message = response.statusText;
    let errors: Array<{ field: string; message: string }> | undefined;

    try {
      const errorBody = (await response.json()) as {
        message?: string;
        errors?: Array<{ field: string; message: string }>;
      };
      message = errorBody.message ?? message;
      errors = errorBody.errors;
    } catch {
      // Response body was not JSON -- use statusText
    }

    throw new ApiError(response.status, message, errors);
  }

  // ---- Handle 204 No Content ----
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

// =============================================================================
// Public API methods
// =============================================================================

/** HTTP GET */
export function get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
  return request<T>(endpoint, { ...options, method: "GET" });
}

/** HTTP POST */
export function post<T>(
  endpoint: string,
  body?: unknown,
  options?: RequestOptions,
): Promise<T> {
  return request<T>(endpoint, { ...options, method: "POST", body });
}

/** HTTP PUT */
export function put<T>(
  endpoint: string,
  body?: unknown,
  options?: RequestOptions,
): Promise<T> {
  return request<T>(endpoint, { ...options, method: "PUT", body });
}

/** HTTP PATCH */
export function patch<T>(
  endpoint: string,
  body?: unknown,
  options?: RequestOptions,
): Promise<T> {
  return request<T>(endpoint, { ...options, method: "PATCH", body });
}

/** HTTP DELETE */
export function del<T>(
  endpoint: string,
  options?: RequestOptions,
): Promise<T> {
  return request<T>(endpoint, { ...options, method: "DELETE" });
}

// Default export as a namespace-like object for convenience
const api = { get, post, put, patch, del } as const;
export default api;
