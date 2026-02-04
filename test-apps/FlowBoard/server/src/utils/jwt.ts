// =============================================================================
// JWT Utility Functions
//
// Access tokens: short-lived (15 min), contain userId + email
// Refresh tokens: long-lived (7 days), contain userId + type marker
// =============================================================================

import jwt from "jsonwebtoken";
import type { AuthPayload } from "../middleware/auth";

const JWT_SECRET = process.env.JWT_SECRET ?? "change-me";
const JWT_REFRESH_SECRET = process.env.JWT_REFRESH_SECRET ?? "change-me-refresh";

const ACCESS_TOKEN_EXPIRY = "15m";
const REFRESH_TOKEN_EXPIRY = "7d";

// ---- Access Tokens ----------------------------------------------------------

export interface AccessTokenPayload {
  userId: string;
  email: string;
}

/** Generate a signed access token (15 min) */
export function generateAccessToken(payload: AccessTokenPayload): string {
  return jwt.sign(payload, JWT_SECRET, {
    expiresIn: ACCESS_TOKEN_EXPIRY,
  });
}

/** Verify and decode an access token */
export function verifyAccessToken(token: string): AccessTokenPayload {
  return jwt.verify(token, JWT_SECRET) as AccessTokenPayload;
}

// ---- Refresh Tokens ---------------------------------------------------------

export interface RefreshTokenPayload {
  userId: string;
  type: "refresh";
}

/** Generate a signed refresh token (7 days) */
export function generateRefreshToken(userId: string): string {
  const payload: RefreshTokenPayload = { userId, type: "refresh" };
  return jwt.sign(payload, JWT_REFRESH_SECRET, {
    expiresIn: REFRESH_TOKEN_EXPIRY,
  });
}

/** Verify and decode a refresh token */
export function verifyRefreshToken(token: string): RefreshTokenPayload {
  const payload = jwt.verify(token, JWT_REFRESH_SECRET) as RefreshTokenPayload;
  if (payload.type !== "refresh") {
    throw new Error("Invalid token type");
  }
  return payload;
}

// ---- Backward-compatible aliases (used by existing middleware) ---------------

/** @deprecated Use generateAccessToken instead */
export function generateToken(payload: AuthPayload): string {
  return generateAccessToken(payload);
}

/** @deprecated Use verifyAccessToken instead */
export function verifyToken(token: string): AuthPayload {
  return verifyAccessToken(token);
}
