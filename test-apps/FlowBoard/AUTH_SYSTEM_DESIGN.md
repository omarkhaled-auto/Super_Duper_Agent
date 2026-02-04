# FlowBoard Authentication & Authorization System Design

## Table of Contents
1. [Architecture Overview](#1-architecture-overview)
2. [JWT Token Design](#2-jwt-token-design)
3. [Token Storage Strategy](#3-token-storage-strategy)
4. [Password Hashing](#4-password-hashing)
5. [Database Schema (Prisma)](#5-database-schema-prisma)
6. [Auth Flow Diagrams](#6-auth-flow-diagrams)
7. [Server-Side Middleware (Express)](#7-server-side-middleware-express)
8. [Client-Side Middleware (Next.js)](#8-client-side-middleware-nextjs)
9. [Session Refresh Mechanism](#9-session-refresh-mechanism)
10. [Role-Based Access Control (RBAC)](#10-role-based-access-control-rbac)
11. [API Route Specifications](#11-api-route-specifications)
12. [Client-Side Auth State Management](#12-client-side-auth-state-management)
13. [Security Considerations](#13-security-considerations)
14. [Error Handling](#14-error-handling)
15. [File Structure](#15-file-structure)

---

## 1. Architecture Overview

```
Client (Next.js 14 App Router)          Server (Express + Prisma + PostgreSQL)
================================         ========================================

[Browser]                                [Express Server]
  |                                        |
  |-- Next.js Middleware (/middleware.ts)   |-- authMiddleware (JWT verify)
  |     Checks accessToken cookie          |     Extracts user from token
  |     Redirects to /login if missing     |     Attaches req.user
  |                                        |
  |-- AuthProvider (React Context)         |-- roleMiddleware (RBAC)
  |     Stores user state                  |     Checks project membership
  |     Provides login/logout/refresh      |     Validates role permissions
  |                                        |
  |-- API calls via fetch()               |-- Rate limiter (express-rate-limit)
  |     Cookies sent automatically         |     Brute-force protection
  |     (credentials: 'include')           |
```

**Key decision**: httpOnly cookies for token transport (not localStorage). This eliminates XSS-based token theft entirely.

---

## 2. JWT Token Design

### 2.1 Dual-Token Architecture

FlowBoard uses a **dual-token** system: a short-lived access token and a long-lived refresh token.

#### Access Token
```typescript
// Payload structure
interface AccessTokenPayload {
  sub: string;        // User ID (UUID)
  email: string;      // User email
  name: string;       // Display name
  avatar: string | null;
  iat: number;        // Issued at (Unix timestamp)
  exp: number;        // Expires at (Unix timestamp)
  type: 'access';     // Token type discriminator
}

// Example signed token payload:
{
  "sub": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "email": "omar@flowboard.io",
  "name": "Omar Khaled",
  "avatar": "/uploads/avatars/a1b2c3d4.jpg",
  "iat": 1706918400,
  "exp": 1706919300,   // 15 minutes after iat
  "type": "access"
}
```

- **Algorithm**: HS256 (HMAC-SHA256) -- sufficient for single-server deployments; switch to RS256 if microservices are introduced later.
- **Expiry**: 15 minutes.
- **Signing secret**: `JWT_ACCESS_SECRET` env var (minimum 64 characters, cryptographically random).

#### Refresh Token
```typescript
interface RefreshTokenPayload {
  sub: string;        // User ID (UUID)
  jti: string;        // Unique token ID (UUID) -- for revocation
  iat: number;
  exp: number;
  type: 'refresh';
}

// Example:
{
  "sub": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "jti": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "iat": 1706918400,
  "exp": 1707523200,   // 7 days after iat
  "type": "refresh"
}
```

- **Signing secret**: `JWT_REFRESH_SECRET` (separate from access secret).
- **Expiry**: 7 days.
- **`jti` field**: Stored in the database. Enables individual token revocation (logout from specific device) and **token rotation** (each refresh invalidates the old token and issues a new one).

### 2.2 Token Generation Implementation

```typescript
// server/src/lib/jwt.ts
import jwt from 'jsonwebtoken';
import { v4 as uuidv4 } from 'uuid';

const ACCESS_SECRET = process.env.JWT_ACCESS_SECRET!;
const REFRESH_SECRET = process.env.JWT_REFRESH_SECRET!;
const ACCESS_EXPIRY = '15m';
const REFRESH_EXPIRY = '7d';

export interface TokenUser {
  id: string;
  email: string;
  name: string;
  avatar: string | null;
}

export function generateAccessToken(user: TokenUser): string {
  return jwt.sign(
    {
      sub: user.id,
      email: user.email,
      name: user.name,
      avatar: user.avatar,
      type: 'access',
    },
    ACCESS_SECRET,
    { expiresIn: ACCESS_EXPIRY }
  );
}

export function generateRefreshToken(userId: string): { token: string; jti: string } {
  const jti = uuidv4();
  const token = jwt.sign(
    {
      sub: userId,
      jti,
      type: 'refresh',
    },
    REFRESH_SECRET,
    { expiresIn: REFRESH_EXPIRY }
  );
  return { token, jti };
}

export function verifyAccessToken(token: string): AccessTokenPayload {
  const payload = jwt.verify(token, ACCESS_SECRET) as AccessTokenPayload;
  if (payload.type !== 'access') throw new Error('Invalid token type');
  return payload;
}

export function verifyRefreshToken(token: string): RefreshTokenPayload {
  const payload = jwt.verify(token, REFRESH_SECRET) as RefreshTokenPayload;
  if (payload.type !== 'refresh') throw new Error('Invalid token type');
  return payload;
}
```

---

## 3. Token Storage Strategy

### Decision: httpOnly Cookies (NOT localStorage)

| Concern          | httpOnly Cookie         | localStorage           |
| ---------------- | ----------------------- | ---------------------- |
| XSS theft        | Immune (JS cannot read) | Fully exposed          |
| CSRF             | Requires mitigation     | N/A                    |
| Automatic send   | Yes (credentials incl.) | Manual header needed   |
| SSR access       | Yes (via cookie parse)  | No (client-only)       |
| Next.js compat   | Excellent               | No SSR support         |

### 3.1 Cookie Configuration

```typescript
// server/src/lib/cookies.ts
import { Response } from 'express';

const IS_PRODUCTION = process.env.NODE_ENV === 'production';

export const COOKIE_OPTIONS = {
  access: {
    httpOnly: true,
    secure: IS_PRODUCTION,               // HTTPS only in production
    sameSite: 'lax' as const,            // Protects against CSRF on cross-origin POST
    path: '/',
    maxAge: 15 * 60 * 1000,             // 15 minutes in ms
    domain: IS_PRODUCTION ? '.flowboard.io' : undefined,
  },
  refresh: {
    httpOnly: true,
    secure: IS_PRODUCTION,
    sameSite: 'lax' as const,
    path: '/api/auth',                   // ONLY sent to auth endpoints (minimize exposure)
    maxAge: 7 * 24 * 60 * 60 * 1000,   // 7 days in ms
    domain: IS_PRODUCTION ? '.flowboard.io' : undefined,
  },
};

export function setAuthCookies(
  res: Response,
  accessToken: string,
  refreshToken: string
): void {
  res.cookie('accessToken', accessToken, COOKIE_OPTIONS.access);
  res.cookie('refreshToken', refreshToken, COOKIE_OPTIONS.refresh);
}

export function clearAuthCookies(res: Response): void {
  res.clearCookie('accessToken', { path: COOKIE_OPTIONS.access.path });
  res.clearCookie('refreshToken', { path: COOKIE_OPTIONS.refresh.path });
}
```

**Critical details**:
- `sameSite: 'lax'` -- blocks cross-origin POST requests from sending cookies (CSRF protection), but allows top-level navigations (links) to work.
- Refresh token cookie path is restricted to `/api/auth` -- it is never sent to task/project/member endpoints.
- `secure: true` in production forces HTTPS.
- No `domain` in development allows `localhost` to work without issues.

---

## 4. Password Hashing

### bcrypt with cost factor 12

```typescript
// server/src/lib/password.ts
import bcrypt from 'bcrypt';

const SALT_ROUNDS = 12; // ~250ms on modern hardware -- good security/UX balance

export async function hashPassword(plaintext: string): Promise<string> {
  return bcrypt.hash(plaintext, SALT_ROUNDS);
}

export async function verifyPassword(
  plaintext: string,
  hash: string
): Promise<boolean> {
  return bcrypt.compare(plaintext, hash);
}
```

### Password Validation Rules (Zod)

```typescript
// server/src/validation/auth.schemas.ts
import { z } from 'zod';

export const passwordSchema = z
  .string()
  .min(8, 'Password must be at least 8 characters')
  .max(128, 'Password must not exceed 128 characters')
  .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
  .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
  .regex(/[0-9]/, 'Password must contain at least one number');

export const signupSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100).trim(),
  email: z.string().email('Invalid email address').toLowerCase().trim(),
  password: passwordSchema,
});

export const loginSchema = z.object({
  email: z.string().email('Invalid email address').toLowerCase().trim(),
  password: z.string().min(1, 'Password is required'),
});

export const updateProfileSchema = z.object({
  name: z.string().min(1).max(100).trim().optional(),
  avatar: z.string().url().nullable().optional(),
});

export const changePasswordSchema = z.object({
  currentPassword: z.string().min(1),
  newPassword: passwordSchema,
});
```

---

## 5. Database Schema (Prisma)

```prisma
// server/prisma/schema.prisma

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id             String   @id @default(uuid())
  email          String   @unique
  name           String
  passwordHash   String   @map("password_hash")
  avatar         String?  // URL to avatar image
  createdAt      DateTime @default(now()) @map("created_at")
  updatedAt      DateTime @updatedAt @map("updated_at")

  // Relations
  refreshTokens  RefreshToken[]
  projectMembers ProjectMember[]
  assignedTasks  Task[]          @relation("TaskAssignee")
  createdTasks   Task[]          @relation("TaskCreator")
  comments       Comment[]
  activities     Activity[]

  @@map("users")
}

model RefreshToken {
  id        String   @id @default(uuid())
  jti       String   @unique            // Maps to JWT 'jti' claim
  userId    String   @map("user_id")
  expiresAt DateTime @map("expires_at")
  revoked   Boolean  @default(false)
  createdAt DateTime @default(now()) @map("created_at")
  userAgent String?  @map("user_agent") // For "manage sessions" UI later
  ipAddress String?  @map("ip_address")

  user User @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@index([userId])
  @@index([jti])
  @@map("refresh_tokens")
}

enum ProjectRole {
  ADMIN
  MEMBER
  VIEWER
}

model ProjectMember {
  id        String      @id @default(uuid())
  userId    String      @map("user_id")
  projectId String      @map("project_id")
  role      ProjectRole @default(MEMBER)
  joinedAt  DateTime    @default(now()) @map("joined_at")

  user    User    @relation(fields: [userId], references: [id], onDelete: Cascade)
  project Project @relation(fields: [projectId], references: [id], onDelete: Cascade)

  @@unique([userId, projectId])  // One membership per user per project
  @@index([projectId])
  @@map("project_members")
}

// Minimal Project model -- full details designed by another agent
model Project {
  id          String   @id @default(uuid())
  name        String
  description String?
  icon        String?
  color       String   @default("#6366f1")
  archived    Boolean  @default(false)
  createdAt   DateTime @default(now()) @map("created_at")
  updatedAt   DateTime @updatedAt @map("updated_at")

  members ProjectMember[]
  tasks   Task[]

  @@map("projects")
}
```

### Key schema decisions:
- **RefreshToken table**: Enables server-side revocation, token rotation tracking, and "active sessions" UI.
- **ProjectMember with role enum**: Clean many-to-many with role attached to the join record (not the user).
- **`@@unique([userId, projectId])`**: Prevents duplicate memberships.
- **Cascade deletes**: Deleting a user removes their tokens and memberships.

---

## 6. Auth Flow Diagrams

### 6.1 Signup Flow

```
Client                              Server                              Database
  |                                   |                                    |
  |  POST /api/auth/signup            |                                    |
  |  { name, email, password }        |                                    |
  |---------------------------------->|                                    |
  |                                   |  Validate with Zod                 |
  |                                   |  Check email uniqueness            |
  |                                   |------------------------------->    |
  |                                   |  <-- user exists? 409 Conflict     |
  |                                   |                                    |
  |                                   |  bcrypt.hash(password, 12)         |
  |                                   |  INSERT INTO users                 |
  |                                   |------------------------------->    |
  |                                   |                                    |
  |                                   |  Generate accessToken (15m)        |
  |                                   |  Generate refreshToken (7d)        |
  |                                   |  INSERT INTO refresh_tokens        |
  |                                   |------------------------------->    |
  |                                   |                                    |
  |  <-- 201 Created                  |                                    |
  |  Set-Cookie: accessToken=...      |                                    |
  |  Set-Cookie: refreshToken=...     |                                    |
  |  Body: { user: { id, name,       |                                    |
  |          email, avatar } }        |                                    |
  |                                   |                                    |
  |  AuthProvider sets user state     |                                    |
  |  Router pushes to /dashboard      |                                    |
```

### 6.2 Login Flow

```
Client                              Server                              Database
  |                                   |                                    |
  |  POST /api/auth/login             |                                    |
  |  { email, password }              |                                    |
  |---------------------------------->|                                    |
  |                                   |  Validate with Zod                 |
  |                                   |  SELECT user WHERE email           |
  |                                   |------------------------------->    |
  |                                   |  <-- user row (or null)            |
  |                                   |                                    |
  |                                   |  if (!user || !bcrypt.compare)     |
  |                                   |    return 401 "Invalid creds"      |
  |                                   |    (constant-time response)        |
  |                                   |                                    |
  |                                   |  Generate accessToken + refresh    |
  |                                   |  INSERT refresh_token              |
  |                                   |------------------------------->    |
  |                                   |                                    |
  |  <-- 200 OK                       |                                    |
  |  Set-Cookie: accessToken=...      |                                    |
  |  Set-Cookie: refreshToken=...     |                                    |
  |  Body: { user: {...} }            |                                    |
```

### 6.3 Silent Token Refresh Flow

```
Client                              Server                              Database
  |                                   |                                    |
  |  Any API call                     |                                    |
  |  Cookie: accessToken=<expired>    |                                    |
  |---------------------------------->|                                    |
  |  <-- 401 { code: 'TOKEN_EXPIRED' }|                                   |
  |                                   |                                    |
  |  POST /api/auth/refresh           |                                    |
  |  Cookie: refreshToken=<valid>     |                                    |
  |---------------------------------->|                                    |
  |                                   |  Verify refresh JWT                |
  |                                   |  SELECT FROM refresh_tokens        |
  |                                   |    WHERE jti = token.jti           |
  |                                   |    AND revoked = false             |
  |                                   |------------------------------->    |
  |                                   |                                    |
  |                                   |  --- TOKEN ROTATION ---            |
  |                                   |  Revoke old token (revoked=true)   |
  |                                   |  Generate new access + refresh     |
  |                                   |  INSERT new refresh_token          |
  |                                   |------------------------------->    |
  |                                   |                                    |
  |  <-- 200 OK                       |                                    |
  |  Set-Cookie: accessToken=<new>    |                                    |
  |  Set-Cookie: refreshToken=<new>   |                                    |
  |  Body: { user: {...} }            |                                    |
  |                                   |                                    |
  |  Retry original API call          |                                    |
  |  Cookie: accessToken=<new>        |                                    |
  |---------------------------------->|                                    |
```

### 6.4 Logout Flow

```
Client                              Server                              Database
  |                                   |                                    |
  |  POST /api/auth/logout            |                                    |
  |  Cookie: refreshToken=...         |                                    |
  |---------------------------------->|                                    |
  |                                   |  Verify refresh token              |
  |                                   |  UPDATE refresh_tokens             |
  |                                   |    SET revoked = true              |
  |                                   |    WHERE jti = token.jti           |
  |                                   |------------------------------->    |
  |                                   |                                    |
  |  <-- 200 OK                       |                                    |
  |  Clear-Cookie: accessToken        |                                    |
  |  Clear-Cookie: refreshToken       |                                    |
  |                                   |                                    |
  |  AuthProvider clears user state   |                                    |
  |  Router pushes to /login          |                                    |
```

---

## 7. Server-Side Middleware (Express)

### 7.1 Authentication Middleware

```typescript
// server/src/middleware/auth.middleware.ts
import { Request, Response, NextFunction } from 'express';
import { verifyAccessToken, AccessTokenPayload } from '../lib/jwt';

// Extend Express Request type
declare global {
  namespace Express {
    interface Request {
      user?: {
        id: string;
        email: string;
        name: string;
        avatar: string | null;
      };
    }
  }
}

/**
 * Requires valid access token. Returns 401 if missing/invalid/expired.
 * Differentiates between "no token" and "expired token" so the client
 * knows whether to attempt a refresh.
 */
export function requireAuth(req: Request, res: Response, next: NextFunction): void {
  const token = req.cookies?.accessToken;

  if (!token) {
    res.status(401).json({
      error: 'Authentication required',
      code: 'NO_TOKEN',
    });
    return;
  }

  try {
    const payload = verifyAccessToken(token);
    req.user = {
      id: payload.sub,
      email: payload.email,
      name: payload.name,
      avatar: payload.avatar,
    };
    next();
  } catch (err: any) {
    if (err.name === 'TokenExpiredError') {
      res.status(401).json({
        error: 'Token expired',
        code: 'TOKEN_EXPIRED',
      });
      return;
    }
    res.status(401).json({
      error: 'Invalid token',
      code: 'INVALID_TOKEN',
    });
  }
}

/**
 * Optional auth -- attaches user if token present, but does not reject.
 * Useful for routes that behave differently for authenticated users.
 */
export function optionalAuth(req: Request, res: Response, next: NextFunction): void {
  const token = req.cookies?.accessToken;
  if (!token) {
    next();
    return;
  }
  try {
    const payload = verifyAccessToken(token);
    req.user = {
      id: payload.sub,
      email: payload.email,
      name: payload.name,
      avatar: payload.avatar,
    };
  } catch {
    // Silently ignore invalid tokens for optional auth
  }
  next();
}
```

### 7.2 Role-Based Authorization Middleware

```typescript
// server/src/middleware/role.middleware.ts
import { Request, Response, NextFunction } from 'express';
import { ProjectRole } from '@prisma/client';
import { prisma } from '../lib/prisma';

// Role hierarchy: ADMIN > MEMBER > VIEWER
const ROLE_HIERARCHY: Record<ProjectRole, number> = {
  VIEWER: 0,
  MEMBER: 1,
  ADMIN: 2,
};

/**
 * Checks that the authenticated user has AT LEAST the required role
 * for the project specified in req.params.projectId.
 *
 * Usage: router.put('/projects/:projectId', requireAuth, requireProjectRole('MEMBER'), handler)
 */
export function requireProjectRole(minimumRole: ProjectRole) {
  return async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    const userId = req.user?.id;
    const projectId = req.params.projectId;

    if (!userId) {
      res.status(401).json({ error: 'Authentication required', code: 'NO_TOKEN' });
      return;
    }

    if (!projectId) {
      res.status(400).json({ error: 'Project ID is required', code: 'MISSING_PROJECT_ID' });
      return;
    }

    try {
      const membership = await prisma.projectMember.findUnique({
        where: {
          userId_projectId: { userId, projectId },
        },
      });

      if (!membership) {
        res.status(403).json({
          error: 'You are not a member of this project',
          code: 'NOT_PROJECT_MEMBER',
        });
        return;
      }

      if (ROLE_HIERARCHY[membership.role] < ROLE_HIERARCHY[minimumRole]) {
        res.status(403).json({
          error: `This action requires ${minimumRole} role or higher`,
          code: 'INSUFFICIENT_ROLE',
        });
        return;
      }

      // Attach membership info for downstream use
      (req as any).projectMembership = membership;
      next();
    } catch (error) {
      next(error);
    }
  };
}

/**
 * Convenience: require the user to be a project admin.
 */
export const requireProjectAdmin = requireProjectRole('ADMIN');

/**
 * Convenience: require at least MEMBER role.
 */
export const requireProjectMember = requireProjectRole('MEMBER');

/**
 * Convenience: require at least VIEWER role (any project member).
 */
export const requireProjectViewer = requireProjectRole('VIEWER');
```

### 7.3 Rate Limiting

```typescript
// server/src/middleware/rateLimiter.middleware.ts
import rateLimit from 'express-rate-limit';

// General API rate limit
export const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100,                  // 100 requests per window per IP
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many requests, please try again later', code: 'RATE_LIMITED' },
});

// Strict limit for auth endpoints (brute-force protection)
export const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 10,                   // 10 attempts per window per IP
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many login attempts, please try again later', code: 'RATE_LIMITED' },
  skipSuccessfulRequests: true, // Only count failures
});
```

### 7.4 Validation Middleware (Zod)

```typescript
// server/src/middleware/validate.middleware.ts
import { Request, Response, NextFunction } from 'express';
import { ZodSchema, ZodError } from 'zod';

export function validate(schema: ZodSchema) {
  return (req: Request, res: Response, next: NextFunction): void => {
    try {
      req.body = schema.parse(req.body);
      next();
    } catch (err) {
      if (err instanceof ZodError) {
        res.status(400).json({
          error: 'Validation failed',
          code: 'VALIDATION_ERROR',
          details: err.errors.map((e) => ({
            field: e.path.join('.'),
            message: e.message,
          })),
        });
        return;
      }
      next(err);
    }
  };
}
```

---

## 8. Client-Side Middleware (Next.js)

### 8.1 Next.js Edge Middleware (Route Protection)

```typescript
// client/middleware.ts
import { NextRequest, NextResponse } from 'next/server';

// Routes that require authentication
const PROTECTED_ROUTES = [
  '/dashboard',
  '/projects',
  '/settings',
  '/analytics',
];

// Routes that should redirect TO dashboard if already authenticated
const AUTH_ROUTES = ['/login', '/signup'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const accessToken = request.cookies.get('accessToken')?.value;

  // Check if route needs protection
  const isProtectedRoute = PROTECTED_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(route + '/')
  );
  const isAuthRoute = AUTH_ROUTES.some((route) => pathname === route);

  // Not logged in, trying to access protected route -> redirect to login
  if (isProtectedRoute && !accessToken) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('redirect', pathname); // Preserve intended destination
    return NextResponse.redirect(loginUrl);
  }

  // Already logged in, trying to access login/signup -> redirect to dashboard
  if (isAuthRoute && accessToken) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  return NextResponse.next();
}

export const config = {
  // Run middleware on these paths only (skip static files, API routes, etc.)
  matcher: [
    '/dashboard/:path*',
    '/projects/:path*',
    '/settings/:path*',
    '/analytics/:path*',
    '/login',
    '/signup',
  ],
};
```

**Important limitation**: Next.js Edge Middleware can see that the `accessToken` cookie EXISTS, but cannot verify its signature (no Node.js crypto in Edge runtime without special setup). This is acceptable because:
1. The middleware acts as a fast **UX guard** (prevents flash of protected content).
2. The actual API calls from the page will fail with 401 if the token is invalid/expired.
3. The AuthProvider (client-side) handles the actual token validation feedback loop.

### 8.2 Server Component Auth Helper

```typescript
// client/src/lib/auth-server.ts
import { cookies } from 'next/headers';

/**
 * For use in Server Components to check auth status.
 * Does NOT verify the token -- just checks existence.
 * Actual verification happens when the server component fetches data from the API.
 */
export function getServerSideUser() {
  const cookieStore = cookies();
  const accessToken = cookieStore.get('accessToken')?.value;

  if (!accessToken) return null;

  // Decode (not verify) the JWT to get user info for SSR rendering.
  // The API layer handles real verification.
  try {
    const payload = JSON.parse(
      Buffer.from(accessToken.split('.')[1], 'base64').toString()
    );
    return {
      id: payload.sub,
      email: payload.email,
      name: payload.name,
      avatar: payload.avatar,
    };
  } catch {
    return null;
  }
}
```

---

## 9. Session Refresh Mechanism

### 9.1 API Client with Automatic Refresh

```typescript
// client/src/lib/api-client.ts

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001/api';

interface ApiError {
  error: string;
  code: string;
  details?: Array<{ field: string; message: string }>;
}

class ApiClient {
  private isRefreshing = false;
  private refreshPromise: Promise<boolean> | null = null;

  /**
   * Core fetch wrapper. Automatically retries with refresh on 401 TOKEN_EXPIRED.
   */
  async fetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const config: RequestInit = {
      ...options,
      credentials: 'include', // CRITICAL: sends cookies cross-origin
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    let response = await fetch(url, config);

    // If token expired, attempt silent refresh and retry ONCE
    if (response.status === 401) {
      const body: ApiError = await response.json();

      if (body.code === 'TOKEN_EXPIRED') {
        const refreshed = await this.refreshToken();
        if (refreshed) {
          // Retry original request with new cookie
          response = await fetch(url, config);
        } else {
          // Refresh failed -- force logout
          this.handleAuthFailure();
          throw new AuthError('Session expired. Please log in again.');
        }
      } else {
        this.handleAuthFailure();
        throw new AuthError('Authentication required.');
      }
    }

    if (!response.ok) {
      const errorBody: ApiError = await response.json().catch(() => ({
        error: 'Unknown error',
        code: 'UNKNOWN',
      }));
      throw new ApiRequestError(response.status, errorBody);
    }

    return response.json();
  }

  /**
   * Refresh token with deduplication.
   * If multiple requests fail simultaneously, only one refresh call is made.
   */
  private async refreshToken(): Promise<boolean> {
    if (this.isRefreshing && this.refreshPromise) {
      return this.refreshPromise;
    }

    this.isRefreshing = true;
    this.refreshPromise = this.doRefresh();

    try {
      return await this.refreshPromise;
    } finally {
      this.isRefreshing = false;
      this.refreshPromise = null;
    }
  }

  private async doRefresh(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
      });
      return response.ok;
    } catch {
      return false;
    }
  }

  private handleAuthFailure(): void {
    // Dispatch custom event that AuthProvider listens to
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('auth:logout'));
    }
  }

  // Convenience methods
  get<T>(endpoint: string) {
    return this.fetch<T>(endpoint, { method: 'GET' });
  }

  post<T>(endpoint: string, data?: unknown) {
    return this.fetch<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  put<T>(endpoint: string, data: unknown) {
    return this.fetch<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  patch<T>(endpoint: string, data: unknown) {
    return this.fetch<T>(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  delete<T>(endpoint: string) {
    return this.fetch<T>(endpoint, { method: 'DELETE' });
  }
}

export const api = new ApiClient();

// Custom error classes
export class AuthError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AuthError';
  }
}

export class ApiRequestError extends Error {
  constructor(
    public status: number,
    public body: ApiError
  ) {
    super(body.error);
    this.name = 'ApiRequestError';
  }
}
```

### 9.2 Proactive Token Refresh

```typescript
// client/src/hooks/useTokenRefresh.ts
import { useEffect, useCallback } from 'react';

/**
 * Proactively refreshes the access token before it expires.
 * Runs a timer that fires 1 minute before the 15-minute access token expires.
 */
export function useTokenRefresh() {
  const refresh = useCallback(async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/auth/refresh`,
        { method: 'POST', credentials: 'include' }
      );
      if (!response.ok) {
        window.dispatchEvent(new CustomEvent('auth:logout'));
      }
    } catch {
      // Network error -- will retry on next interval
    }
  }, []);

  useEffect(() => {
    // Refresh 1 minute before the 15-minute access token expires
    const REFRESH_INTERVAL = 14 * 60 * 1000; // 14 minutes
    const intervalId = setInterval(refresh, REFRESH_INTERVAL);

    return () => clearInterval(intervalId);
  }, [refresh]);
}
```

---

## 10. Role-Based Access Control (RBAC)

### 10.1 Permissions Matrix

| Operation                     | VIEWER | MEMBER | ADMIN |
| ----------------------------- | ------ | ------ | ----- |
| **Project**                   |        |        |       |
| View project                  | YES    | YES    | YES   |
| Edit project settings         | --     | --     | YES   |
| Archive/delete project        | --     | --     | YES   |
| Invite members                | --     | --     | YES   |
| Remove members                | --     | --     | YES   |
| Change member roles           | --     | --     | YES   |
| **Tasks**                     |        |        |       |
| View tasks                    | YES    | YES    | YES   |
| Create tasks                  | --     | YES    | YES   |
| Edit task fields              | --     | YES    | YES   |
| Move tasks (Kanban drag)      | --     | YES    | YES   |
| Delete tasks                  | --     | YES    | YES   |
| Bulk actions                  | --     | YES    | YES   |
| **Comments**                  |        |        |       |
| View comments                 | YES    | YES    | YES   |
| Add comments                  | YES    | YES    | YES   |
| Edit own comments             | YES    | YES    | YES   |
| Delete own comments           | YES    | YES    | YES   |
| Delete any comment            | --     | --     | YES   |
| **Analytics**                 |        |        |       |
| View analytics                | YES    | YES    | YES   |

### 10.2 Permissions Helper

```typescript
// server/src/lib/permissions.ts
import { ProjectRole } from '@prisma/client';

export type Permission =
  | 'project:view'
  | 'project:edit'
  | 'project:delete'
  | 'project:invite'
  | 'project:remove_member'
  | 'project:change_role'
  | 'task:view'
  | 'task:create'
  | 'task:edit'
  | 'task:delete'
  | 'task:move'
  | 'task:bulk_action'
  | 'comment:view'
  | 'comment:create'
  | 'comment:edit_own'
  | 'comment:delete_own'
  | 'comment:delete_any'
  | 'analytics:view';

const ROLE_PERMISSIONS: Record<ProjectRole, Set<Permission>> = {
  VIEWER: new Set([
    'project:view',
    'task:view',
    'comment:view',
    'comment:create',
    'comment:edit_own',
    'comment:delete_own',
    'analytics:view',
  ]),
  MEMBER: new Set([
    'project:view',
    'task:view',
    'task:create',
    'task:edit',
    'task:delete',
    'task:move',
    'task:bulk_action',
    'comment:view',
    'comment:create',
    'comment:edit_own',
    'comment:delete_own',
    'analytics:view',
  ]),
  ADMIN: new Set([
    'project:view',
    'project:edit',
    'project:delete',
    'project:invite',
    'project:remove_member',
    'project:change_role',
    'task:view',
    'task:create',
    'task:edit',
    'task:delete',
    'task:move',
    'task:bulk_action',
    'comment:view',
    'comment:create',
    'comment:edit_own',
    'comment:delete_own',
    'comment:delete_any',
    'analytics:view',
  ]),
};

export function hasPermission(role: ProjectRole, permission: Permission): boolean {
  return ROLE_PERMISSIONS[role].has(permission);
}

export function getPermissions(role: ProjectRole): Permission[] {
  return Array.from(ROLE_PERMISSIONS[role]);
}
```

### 10.3 Client-Side Permission Hook

```typescript
// client/src/hooks/usePermission.ts
import { useMemo } from 'react';
import { useProjectMembership } from './useProjectMembership';

type Permission = /* same union type as server */;

const ROLE_PERMISSIONS: Record<string, Set<Permission>> = { /* same map as server */ };

export function usePermission(permission: Permission): boolean {
  const { membership } = useProjectMembership();

  return useMemo(() => {
    if (!membership) return false;
    return ROLE_PERMISSIONS[membership.role]?.has(permission) ?? false;
  }, [membership, permission]);
}

// Usage in components:
// const canEditTask = usePermission('task:edit');
// {canEditTask && <EditButton />}
```

---

## 11. API Route Specifications

### 11.1 Auth Routes

```typescript
// server/src/routes/auth.routes.ts
import { Router } from 'express';
import { authLimiter } from '../middleware/rateLimiter.middleware';
import { validate } from '../middleware/validate.middleware';
import { requireAuth } from '../middleware/auth.middleware';
import { signupSchema, loginSchema, changePasswordSchema, updateProfileSchema } from '../validation/auth.schemas';
import * as authController from '../controllers/auth.controller';

const router = Router();

// Public auth endpoints (rate limited)
router.post('/signup',   authLimiter, validate(signupSchema),   authController.signup);
router.post('/login',    authLimiter, validate(loginSchema),    authController.login);
router.post('/refresh',  authLimiter,                           authController.refresh);
router.post('/logout',                                          authController.logout);

// Protected profile endpoints
router.get('/me',                requireAuth,                                      authController.getProfile);
router.patch('/me',              requireAuth, validate(updateProfileSchema),        authController.updateProfile);
router.put('/me/password',       requireAuth, validate(changePasswordSchema),       authController.changePassword);
router.post('/me/avatar',        requireAuth,                                      authController.uploadAvatar);

export default router;
```

### 11.2 Auth Controller Implementation

```typescript
// server/src/controllers/auth.controller.ts
import { Request, Response, NextFunction } from 'express';
import { prisma } from '../lib/prisma';
import { hashPassword, verifyPassword } from '../lib/password';
import { generateAccessToken, generateRefreshToken, verifyRefreshToken } from '../lib/jwt';
import { setAuthCookies, clearAuthCookies } from '../lib/cookies';

export async function signup(req: Request, res: Response, next: NextFunction) {
  try {
    const { name, email, password } = req.body;

    // Check for existing user
    const existingUser = await prisma.user.findUnique({ where: { email } });
    if (existingUser) {
      return res.status(409).json({
        error: 'An account with this email already exists',
        code: 'EMAIL_EXISTS',
      });
    }

    // Create user
    const passwordHash = await hashPassword(password);
    const user = await prisma.user.create({
      data: { name, email, passwordHash },
      select: { id: true, name: true, email: true, avatar: true },
    });

    // Generate tokens
    const accessToken = generateAccessToken(user);
    const { token: refreshToken, jti } = generateRefreshToken(user.id);

    // Store refresh token
    await prisma.refreshToken.create({
      data: {
        jti,
        userId: user.id,
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
        userAgent: req.headers['user-agent'] || null,
        ipAddress: req.ip || null,
      },
    });

    setAuthCookies(res, accessToken, refreshToken);
    res.status(201).json({ user });
  } catch (error) {
    next(error);
  }
}

export async function login(req: Request, res: Response, next: NextFunction) {
  try {
    const { email, password } = req.body;

    // Lookup user -- always run bcrypt.compare even if user not found (timing attack prevention)
    const user = await prisma.user.findUnique({ where: { email } });
    const dummyHash = '$2b$12$LJ3m4ys3Lg2VBe/5rJsH6.Dl8JEpQGKdBMY3K0jGFd/oCSNuyq2H.';
    const isValid = await verifyPassword(password, user?.passwordHash || dummyHash);

    if (!user || !isValid) {
      return res.status(401).json({
        error: 'Invalid email or password',
        code: 'INVALID_CREDENTIALS',
      });
    }

    // Generate tokens
    const accessToken = generateAccessToken({
      id: user.id,
      email: user.email,
      name: user.name,
      avatar: user.avatar,
    });
    const { token: refreshToken, jti } = generateRefreshToken(user.id);

    await prisma.refreshToken.create({
      data: {
        jti,
        userId: user.id,
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
        userAgent: req.headers['user-agent'] || null,
        ipAddress: req.ip || null,
      },
    });

    setAuthCookies(res, accessToken, refreshToken);
    res.json({
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
        avatar: user.avatar,
      },
    });
  } catch (error) {
    next(error);
  }
}

export async function refresh(req: Request, res: Response, next: NextFunction) {
  try {
    const token = req.cookies?.refreshToken;
    if (!token) {
      return res.status(401).json({ error: 'No refresh token', code: 'NO_TOKEN' });
    }

    // Verify JWT signature and expiry
    let payload;
    try {
      payload = verifyRefreshToken(token);
    } catch {
      clearAuthCookies(res);
      return res.status(401).json({ error: 'Invalid refresh token', code: 'INVALID_TOKEN' });
    }

    // Check database -- is this token revoked?
    const storedToken = await prisma.refreshToken.findUnique({
      where: { jti: payload.jti },
    });

    if (!storedToken || storedToken.revoked) {
      // POSSIBLE TOKEN THEFT: a revoked token was reused.
      // Revoke ALL tokens for this user as a safety measure.
      if (storedToken?.revoked) {
        await prisma.refreshToken.updateMany({
          where: { userId: payload.sub },
          data: { revoked: true },
        });
      }
      clearAuthCookies(res);
      return res.status(401).json({
        error: 'Token has been revoked',
        code: 'TOKEN_REVOKED',
      });
    }

    // TOKEN ROTATION: revoke old, issue new
    await prisma.refreshToken.update({
      where: { jti: payload.jti },
      data: { revoked: true },
    });

    // Get fresh user data
    const user = await prisma.user.findUnique({
      where: { id: payload.sub },
      select: { id: true, name: true, email: true, avatar: true },
    });

    if (!user) {
      clearAuthCookies(res);
      return res.status(401).json({ error: 'User not found', code: 'USER_NOT_FOUND' });
    }

    // Issue new token pair
    const newAccessToken = generateAccessToken(user);
    const { token: newRefreshToken, jti: newJti } = generateRefreshToken(user.id);

    await prisma.refreshToken.create({
      data: {
        jti: newJti,
        userId: user.id,
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
        userAgent: req.headers['user-agent'] || null,
        ipAddress: req.ip || null,
      },
    });

    setAuthCookies(res, newAccessToken, newRefreshToken);
    res.json({ user });
  } catch (error) {
    next(error);
  }
}

export async function logout(req: Request, res: Response, next: NextFunction) {
  try {
    const token = req.cookies?.refreshToken;
    if (token) {
      try {
        const payload = verifyRefreshToken(token);
        await prisma.refreshToken.update({
          where: { jti: payload.jti },
          data: { revoked: true },
        });
      } catch {
        // Token already invalid -- just clear cookies
      }
    }
    clearAuthCookies(res);
    res.json({ message: 'Logged out successfully' });
  } catch (error) {
    next(error);
  }
}

export async function getProfile(req: Request, res: Response) {
  const user = await prisma.user.findUnique({
    where: { id: req.user!.id },
    select: { id: true, name: true, email: true, avatar: true, createdAt: true },
  });
  res.json({ user });
}

export async function updateProfile(req: Request, res: Response, next: NextFunction) {
  try {
    const user = await prisma.user.update({
      where: { id: req.user!.id },
      data: req.body,
      select: { id: true, name: true, email: true, avatar: true },
    });
    res.json({ user });
  } catch (error) {
    next(error);
  }
}

export async function changePassword(req: Request, res: Response, next: NextFunction) {
  try {
    const { currentPassword, newPassword } = req.body;
    const user = await prisma.user.findUnique({ where: { id: req.user!.id } });

    if (!user || !(await verifyPassword(currentPassword, user.passwordHash))) {
      return res.status(400).json({
        error: 'Current password is incorrect',
        code: 'INVALID_PASSWORD',
      });
    }

    const newHash = await hashPassword(newPassword);
    await prisma.user.update({
      where: { id: req.user!.id },
      data: { passwordHash: newHash },
    });

    // Revoke all refresh tokens (force re-login on all devices)
    await prisma.refreshToken.updateMany({
      where: { userId: req.user!.id },
      data: { revoked: true },
    });

    // Issue fresh tokens for current session
    const tokenUser = { id: user.id, email: user.email, name: user.name, avatar: user.avatar };
    const accessToken = generateAccessToken(tokenUser);
    const { token: refreshToken, jti } = generateRefreshToken(user.id);

    await prisma.refreshToken.create({
      data: {
        jti,
        userId: user.id,
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
      },
    });

    setAuthCookies(res, accessToken, refreshToken);
    res.json({ message: 'Password changed successfully' });
  } catch (error) {
    next(error);
  }
}

export async function uploadAvatar(req: Request, res: Response, next: NextFunction) {
  // Implementation depends on file upload strategy (multer + local disk or S3)
  // Placeholder -- to be implemented with file upload middleware
  try {
    // After multer processes the file:
    // const avatarUrl = `/uploads/avatars/${req.file.filename}`;
    // const user = await prisma.user.update({ where: { id: req.user!.id }, data: { avatar: avatarUrl } });
    // res.json({ user });
    res.status(501).json({ error: 'Avatar upload not yet implemented' });
  } catch (error) {
    next(error);
  }
}
```

### 11.3 Route Application in Express App

```typescript
// server/src/app.ts
import express from 'express';
import cookieParser from 'cookie-parser';
import cors from 'cors';
import authRoutes from './routes/auth.routes';
import projectRoutes from './routes/project.routes';
import { apiLimiter } from './middleware/rateLimiter.middleware';
import { errorHandler } from './middleware/error.middleware';

const app = express();

// Global middleware
app.use(cors({
  origin: process.env.CLIENT_URL || 'http://localhost:3000',
  credentials: true,  // CRITICAL: allows cookies in cross-origin requests
}));
app.use(express.json({ limit: '10mb' }));
app.use(cookieParser());
app.use('/api', apiLimiter);

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/projects', projectRoutes);

// Global error handler (must be last)
app.use(errorHandler);

export default app;
```

---

## 12. Client-Side Auth State Management

### 12.1 AuthProvider Context

```typescript
// client/src/providers/AuthProvider.tsx
'use client';

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { api } from '@/lib/api-client';
import { useTokenRefresh } from '@/hooks/useTokenRefresh';

interface User {
  id: string;
  name: string;
  email: string;
  avatar: string | null;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (data: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  // Proactive token refresh (14-minute interval)
  useTokenRefresh();

  // Initial session check on mount
  useEffect(() => {
    async function checkSession() {
      try {
        const data = await api.get<{ user: User }>('/auth/me');
        setUser(data.user);
      } catch {
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    }
    checkSession();
  }, []);

  // Listen for forced logout events (from API client)
  useEffect(() => {
    function handleLogout() {
      setUser(null);
      router.push('/login');
    }
    window.addEventListener('auth:logout', handleLogout);
    return () => window.removeEventListener('auth:logout', handleLogout);
  }, [router]);

  const login = useCallback(async (email: string, password: string) => {
    const data = await api.post<{ user: User }>('/auth/login', { email, password });
    setUser(data.user);
    // Redirect to intended page or dashboard
    const params = new URLSearchParams(window.location.search);
    router.push(params.get('redirect') || '/dashboard');
  }, [router]);

  const signup = useCallback(async (name: string, email: string, password: string) => {
    const data = await api.post<{ user: User }>('/auth/signup', { name, email, password });
    setUser(data.user);
    router.push('/dashboard');
  }, [router]);

  const logout = useCallback(async () => {
    try {
      await api.post('/auth/logout');
    } catch {
      // Even if server logout fails, clear client state
    }
    setUser(null);
    router.push('/login');
  }, [router]);

  const updateUser = useCallback((data: Partial<User>) => {
    setUser((prev) => prev ? { ...prev, ...data } : null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, signup, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

### 12.2 Layout Integration

```typescript
// client/src/app/layout.tsx
import { AuthProvider } from '@/providers/AuthProvider';
import { ThemeProvider } from '@/providers/ThemeProvider';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider>
          <AuthProvider>
            {children}
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
```

---

## 13. Security Considerations

### 13.1 CSRF Protection

**Strategy**: `sameSite: 'lax'` cookies + custom header verification.

- `sameSite: 'lax'` prevents cookies from being sent on cross-origin POST/PUT/DELETE requests (the main CSRF vectors).
- As a defense-in-depth measure, the API client sends `Content-Type: application/json`, which cannot be sent by HTML forms (they can only send `application/x-www-form-urlencoded`, `multipart/form-data`, or `text/plain`). The server rejects requests without `Content-Type: application/json` on mutation endpoints.

```typescript
// server/src/middleware/csrf.middleware.ts
import { Request, Response, NextFunction } from 'express';

/**
 * Defense-in-depth: reject state-changing requests without JSON content type.
 * Prevents form-based CSRF attacks even if sameSite is somehow bypassed.
 */
export function csrfProtection(req: Request, res: Response, next: NextFunction): void {
  const safeMethods = ['GET', 'HEAD', 'OPTIONS'];
  if (safeMethods.includes(req.method)) {
    next();
    return;
  }

  const contentType = req.headers['content-type'];
  if (!contentType || !contentType.includes('application/json')) {
    res.status(403).json({
      error: 'Invalid content type',
      code: 'CSRF_VALIDATION_FAILED',
    });
    return;
  }

  next();
}
```

### 13.2 XSS Prevention

1. **httpOnly cookies**: JavaScript cannot access tokens. Even if XSS occurs, the attacker cannot steal the JWT.
2. **React's built-in escaping**: All JSX output is escaped by default.
3. **Sanitize user-generated content**: The markdown editor output (task descriptions) must be sanitized with DOMPurify before rendering.
4. **Content-Security-Policy header**: Added via Express middleware.

```typescript
// server/src/middleware/security.middleware.ts
import helmet from 'helmet';

export const securityHeaders = helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"], // Needed for Tailwind
      imgSrc: ["'self'", 'data:', 'blob:'],
      connectSrc: ["'self'", 'ws:', 'wss:'],  // WebSocket connections
    },
  },
  crossOriginEmbedderPolicy: false, // Can conflict with external images
});
```

### 13.3 Token Rotation (Refresh Token Theft Detection)

The refresh flow implements **automatic reuse detection**:

1. Each refresh token has a unique `jti` stored in the database.
2. When a refresh token is used, it is immediately revoked and a new one is issued.
3. If a **revoked** token is presented (indicating the old token was stolen and the legitimate user already used the new one), ALL tokens for that user are revoked, forcing re-authentication on every device.

This is implemented in the `refresh` controller (Section 11.2).

### 13.4 Brute Force Protection

- Auth endpoints limited to 10 requests per 15 minutes per IP (Section 7.3).
- Generic error messages ("Invalid email or password") -- never reveals whether the email exists.
- Constant-time bcrypt comparison (always runs bcrypt.compare, even for non-existent users).

### 13.5 Password Security

- bcrypt cost factor 12 (~250ms per hash).
- Minimum 8 characters, requires uppercase, lowercase, and number.
- Maximum 128 characters (prevents bcrypt DoS with extremely long passwords).
- Password change revokes all refresh tokens (forces re-login on all other devices).

### 13.6 Environment Variables

```bash
# server/.env (NEVER committed to git)
DATABASE_URL="postgresql://user:password@localhost:5432/flowboard"
JWT_ACCESS_SECRET="<64+ random characters>"  # openssl rand -hex 64
JWT_REFRESH_SECRET="<64+ random characters>" # openssl rand -hex 64 (DIFFERENT from access)
CLIENT_URL="http://localhost:3000"
PORT=3001
NODE_ENV="development"
```

---

## 14. Error Handling

### 14.1 Standardized Error Response Format

Every error response follows this shape:

```typescript
interface ErrorResponse {
  error: string;   // Human-readable message
  code: string;    // Machine-readable error code
  details?: Array<{ field: string; message: string }>; // Validation errors only
}
```

### 14.2 Error Code Reference

| HTTP Status | Code                   | When                                              |
| ----------- | ---------------------- | ------------------------------------------------- |
| 400         | VALIDATION_ERROR       | Zod validation fails                              |
| 400         | INVALID_PASSWORD       | Wrong current password on change                  |
| 401         | NO_TOKEN               | No access/refresh token in cookies                |
| 401         | TOKEN_EXPIRED          | Access token JWT has expired (trigger refresh)     |
| 401         | INVALID_TOKEN          | Token signature invalid or malformed              |
| 401         | TOKEN_REVOKED          | Refresh token was revoked (theft detection)       |
| 401         | INVALID_CREDENTIALS    | Wrong email/password on login                     |
| 401         | USER_NOT_FOUND         | User deleted after token was issued               |
| 403         | NOT_PROJECT_MEMBER     | User is not a member of the project               |
| 403         | INSUFFICIENT_ROLE      | User's role lacks required permission             |
| 403         | CSRF_VALIDATION_FAILED | Missing JSON content type on mutation              |
| 409         | EMAIL_EXISTS           | Email already registered                          |
| 429         | RATE_LIMITED           | Too many requests                                 |
| 500         | INTERNAL_ERROR         | Unexpected server error                           |

### 14.3 Global Error Handler

```typescript
// server/src/middleware/error.middleware.ts
import { Request, Response, NextFunction } from 'express';
import { Prisma } from '@prisma/client';

export function errorHandler(err: Error, req: Request, res: Response, next: NextFunction): void {
  console.error(`[ERROR] ${req.method} ${req.path}:`, err.message);

  // Prisma unique constraint violation
  if (err instanceof Prisma.PrismaClientKnownRequestError && err.code === 'P2002') {
    res.status(409).json({
      error: 'Resource already exists',
      code: 'DUPLICATE_RESOURCE',
    });
    return;
  }

  // Prisma record not found
  if (err instanceof Prisma.PrismaClientKnownRequestError && err.code === 'P2025') {
    res.status(404).json({
      error: 'Resource not found',
      code: 'NOT_FOUND',
    });
    return;
  }

  // Default: internal server error (never leak stack traces in production)
  res.status(500).json({
    error: process.env.NODE_ENV === 'production'
      ? 'Internal server error'
      : err.message,
    code: 'INTERNAL_ERROR',
  });
}
```

### 14.4 Client-Side Error Handling (Toast Notifications)

```typescript
// client/src/lib/error-handler.ts
import { toast } from 'sonner'; // or your toast library
import { ApiRequestError, AuthError } from './api-client';

export function handleApiError(error: unknown): void {
  if (error instanceof AuthError) {
    toast.error(error.message);
    return;
  }

  if (error instanceof ApiRequestError) {
    switch (error.body.code) {
      case 'VALIDATION_ERROR':
        // Show first validation error
        const firstDetail = error.body.details?.[0];
        toast.error(firstDetail ? `${firstDetail.field}: ${firstDetail.message}` : error.message);
        break;
      case 'RATE_LIMITED':
        toast.error('Too many requests. Please wait a moment and try again.');
        break;
      case 'EMAIL_EXISTS':
        toast.error('An account with this email already exists.');
        break;
      case 'INVALID_CREDENTIALS':
        toast.error('Invalid email or password.');
        break;
      case 'INSUFFICIENT_ROLE':
        toast.error('You do not have permission to perform this action.');
        break;
      case 'NOT_PROJECT_MEMBER':
        toast.error('You are not a member of this project.');
        break;
      default:
        toast.error(error.message || 'Something went wrong.');
    }
    return;
  }

  toast.error('An unexpected error occurred.');
}
```

---

## 15. File Structure

```
server/
  prisma/
    schema.prisma                 # Database schema (Section 5)
    seed.ts                       # Demo data seed (3 users, 3 projects)
  src/
    app.ts                        # Express app setup (Section 11.3)
    server.ts                     # Server entry point
    lib/
      prisma.ts                   # Prisma client singleton
      jwt.ts                      # Token generation/verification (Section 2.2)
      password.ts                 # bcrypt hash/verify (Section 4)
      cookies.ts                  # Cookie config/helpers (Section 3.1)
      permissions.ts              # RBAC permission maps (Section 10.2)
    middleware/
      auth.middleware.ts          # requireAuth, optionalAuth (Section 7.1)
      role.middleware.ts          # requireProjectRole (Section 7.2)
      rateLimiter.middleware.ts   # Rate limiters (Section 7.3)
      validate.middleware.ts      # Zod validation (Section 7.4)
      csrf.middleware.ts          # CSRF protection (Section 13.1)
      security.middleware.ts      # Helmet headers (Section 13.2)
      error.middleware.ts         # Global error handler (Section 14.3)
    validation/
      auth.schemas.ts             # Zod schemas for auth (Section 4)
    routes/
      auth.routes.ts              # Auth route definitions (Section 11.1)
    controllers/
      auth.controller.ts          # Auth route handlers (Section 11.2)

client/
  middleware.ts                   # Next.js Edge Middleware (Section 8.1)
  src/
    app/
      layout.tsx                  # Root layout with AuthProvider (Section 12.2)
      login/
        page.tsx                  # Login page
      signup/
        page.tsx                  # Signup page
      dashboard/
        layout.tsx                # Protected layout (sidebar, topbar)
        page.tsx                  # Dashboard home
      settings/
        page.tsx                  # Profile settings
    providers/
      AuthProvider.tsx            # Auth context & state (Section 12.1)
    lib/
      api-client.ts              # Fetch wrapper with auto-refresh (Section 9.1)
      auth-server.ts             # Server component auth helper (Section 8.2)
      error-handler.ts           # Toast error handler (Section 14.4)
    hooks/
      useAuth.ts                 # Re-export from AuthProvider
      useTokenRefresh.ts         # Proactive token refresh (Section 9.2)
      usePermission.ts           # Client-side RBAC check (Section 10.3)
      useProjectMembership.ts    # Current user's project role
```

---

## Summary of Key Design Decisions

| Decision                       | Choice                  | Rationale                                             |
| ------------------------------ | ----------------------- | ----------------------------------------------------- |
| Token transport                | httpOnly cookies        | Immune to XSS token theft; works with SSR             |
| Token architecture             | Access (15m) + Refresh (7d) | Short access = small attack window; refresh = UX  |
| Refresh token storage          | Database (PostgreSQL)   | Enables revocation, rotation, theft detection          |
| Password hashing               | bcrypt, cost 12         | Industry standard; 250ms = good UX/security balance   |
| CSRF protection                | sameSite:lax + JSON-only| Double defense; no CSRF tokens needed                  |
| Client route protection        | Next.js Edge Middleware | Fast redirect before page loads; no flash of content   |
| Server route protection        | Express middleware chain| Composable: requireAuth -> requireProjectRole -> handler |
| Role model                     | Per-project roles       | ADMIN/MEMBER/VIEWER on ProjectMember join table        |
| Error format                   | { error, code, details }| Machine-parseable codes for client-side handling       |
| Token refresh                  | Automatic + proactive   | 401 retry + 14-min interval prevents most expirations  |
