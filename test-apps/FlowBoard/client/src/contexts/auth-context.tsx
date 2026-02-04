"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import api, { ApiError, setTokens, clearTokens } from "@/lib/api";
import type { User } from "@/types";

// =============================================================================
// Auth Context -- manages user session state, login, signup, logout.
//
// - On mount, calls GET /auth/me to rehydrate the user from the stored token.
// - login()  -> POST /auth/login  -> stores tokens + sets user.
// - signup() -> POST /auth/signup -> stores tokens + sets user + redirect.
// - logout() -> POST /auth/logout -> clears tokens + redirects to /login.
// =============================================================================

/** Shape of the auth response from login / signup endpoints */
interface AuthResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
}

/** Shape of the "me" response (just the user, no tokens) */
interface MeResponse {
  user: User;
}

/** Context value exposed to consumers */
interface AuthContextValue {
  /** The currently authenticated user, or `null` if not logged in. */
  user: User | null;
  /** `true` while the initial auth check (GET /auth/me) is in flight. */
  loading: boolean;
  /** Authenticate with email + password. Throws on failure. */
  login: (email: string, password: string) => Promise<void>;
  /** Create a new account. Throws on failure. Redirects to /dashboard on success. */
  signup: (name: string, email: string, password: string) => Promise<void>;
  /** End the current session and redirect to /login. */
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // ---- Rehydrate session on mount ----
  const checkAuth = useCallback(async () => {
    try {
      const res = await api.get<MeResponse>("/auth/me");
      setUser(res.user);
    } catch {
      // Not authenticated or token expired -- that's fine.
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // ---- Login ----
  const login = useCallback(
    async (email: string, password: string) => {
      const res = await api.post<AuthResponse>("/auth/login", {
        email,
        password,
      });
      setTokens(res.accessToken, res.refreshToken);
      setUser(res.user);
      router.push("/dashboard");
    },
    [router],
  );

  // ---- Signup ----
  const signup = useCallback(
    async (name: string, email: string, password: string) => {
      const res = await api.post<AuthResponse>(
        "/auth/signup",
        { name, email, password },
        { auth: false },
      );
      setTokens(res.accessToken, res.refreshToken);
      setUser(res.user);
      router.push("/dashboard");
    },
    [router],
  );

  // ---- Logout ----
  const logout = useCallback(async () => {
    try {
      await api.post("/auth/logout");
    } catch {
      // Even if the server call fails, we still clear local state.
    } finally {
      clearTokens();
      setUser(null);
      router.push("/login");
    }
  }, [router]);

  // ---- Memoize context value ----
  const value = useMemo<AuthContextValue>(
    () => ({ user, loading, login, signup, logout }),
    [user, loading, login, signup, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

/**
 * Access the auth context. Must be used inside an `<AuthProvider>`.
 *
 * @example
 * const { user, login, logout } = useAuth();
 */
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (ctx === undefined) {
    throw new Error("useAuth must be used within an <AuthProvider>");
  }
  return ctx;
}

export { ApiError };
