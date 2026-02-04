// =============================================================================
// Auth Routes — /api/auth
//
// POST /signup   — Register a new account
// POST /login    — Authenticate with email + password
// POST /refresh  — Get a new access token using a refresh token
// POST /logout   — Clear auth cookies
// GET  /me       — Return the authenticated user's profile
// =============================================================================

import { Router, Request, Response, NextFunction } from "express";
import { ZodError } from "zod";
import { requireAuth } from "../middleware/auth";
import {
  signUp,
  signIn,
  refreshAccessToken,
  getMe,
} from "../services/auth.service";

const router = Router();

// -- Cookie configuration -----------------------------------------------------

const IS_PRODUCTION = process.env.NODE_ENV === "production";

const COOKIE_OPTIONS_BASE = {
  httpOnly: true,
  secure: IS_PRODUCTION,
  sameSite: "lax" as const,
  path: "/",
};

const ACCESS_COOKIE_MAX_AGE = 15 * 60 * 1000; // 15 minutes
const REFRESH_COOKIE_MAX_AGE = 7 * 24 * 60 * 60 * 1000; // 7 days

/** Set both access and refresh token cookies on the response */
function setAuthCookies(
  res: Response,
  accessToken: string,
  refreshToken: string,
): void {
  res.cookie("accessToken", accessToken, {
    ...COOKIE_OPTIONS_BASE,
    maxAge: ACCESS_COOKIE_MAX_AGE,
  });
  res.cookie("refreshToken", refreshToken, {
    ...COOKIE_OPTIONS_BASE,
    maxAge: REFRESH_COOKIE_MAX_AGE,
  });
}

/** Clear both auth cookies */
function clearAuthCookies(res: Response): void {
  res.clearCookie("accessToken", COOKIE_OPTIONS_BASE);
  res.clearCookie("refreshToken", COOKIE_OPTIONS_BASE);
}

// =============================================================================
// POST /api/auth/signup
// =============================================================================
router.post("/signup", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const result = await signUp(req.body);

    // Set httpOnly cookies
    setAuthCookies(res, result.accessToken, result.refreshToken);

    // Return tokens in body as well
    res.status(201).json({
      user: result.user,
      accessToken: result.accessToken,
      refreshToken: result.refreshToken,
    });
  } catch (err: any) {
    // Zod validation errors -> 400
    if (err instanceof ZodError) {
      res.status(400).json({
        message: "Validation failed",
        errors: err.errors.map((e) => ({
          field: e.path.join("."),
          message: e.message,
        })),
      });
      return;
    }
    // Known status code errors (409, 401, etc.)
    if (err.statusCode) {
      res.status(err.statusCode).json({ message: err.message });
      return;
    }
    next(err);
  }
});

// =============================================================================
// POST /api/auth/login
// =============================================================================
router.post("/login", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const result = await signIn(req.body);

    // Set httpOnly cookies
    setAuthCookies(res, result.accessToken, result.refreshToken);

    // Return tokens in body as well
    res.status(200).json({
      user: result.user,
      accessToken: result.accessToken,
      refreshToken: result.refreshToken,
    });
  } catch (err: any) {
    if (err instanceof ZodError) {
      res.status(400).json({
        message: "Validation failed",
        errors: err.errors.map((e) => ({
          field: e.path.join("."),
          message: e.message,
        })),
      });
      return;
    }
    if (err.statusCode) {
      res.status(err.statusCode).json({ message: err.message });
      return;
    }
    next(err);
  }
});

// =============================================================================
// POST /api/auth/refresh
// =============================================================================
router.post("/refresh", async (req: Request, res: Response, next: NextFunction) => {
  try {
    // Read refresh token from cookie first, then fall back to request body
    const token: string | undefined =
      req.cookies?.refreshToken || req.body?.refreshToken;

    if (!token) {
      res.status(401).json({ message: "Refresh token is required" });
      return;
    }

    const result = await refreshAccessToken(token);

    // Update the access token cookie
    res.cookie("accessToken", result.accessToken, {
      ...COOKIE_OPTIONS_BASE,
      maxAge: ACCESS_COOKIE_MAX_AGE,
    });

    res.status(200).json({
      accessToken: result.accessToken,
    });
  } catch (err: any) {
    if (err.statusCode) {
      res.status(err.statusCode).json({ message: err.message });
      return;
    }
    next(err);
  }
});

// =============================================================================
// POST /api/auth/logout
// =============================================================================
router.post("/logout", async (_req: Request, res: Response, next: NextFunction) => {
  try {
    clearAuthCookies(res);
    res.status(200).json({ message: "Logged out successfully" });
  } catch (err) {
    next(err);
  }
});

// =============================================================================
// GET /api/auth/me — Protected
// =============================================================================
router.get("/me", requireAuth, async (req: Request, res: Response, next: NextFunction) => {
  try {
    const user = await getMe(req.user!.userId);

    if (!user) {
      res.status(404).json({ message: "User not found" });
      return;
    }

    res.status(200).json({ user });
  } catch (err) {
    next(err);
  }
});

export default router;
