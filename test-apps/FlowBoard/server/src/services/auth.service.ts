// =============================================================================
// Auth Service — business logic for authentication
// =============================================================================

import { prisma } from "../lib/prisma";
import { hashPassword, comparePassword } from "../utils/password";
import {
  generateAccessToken,
  generateRefreshToken,
  verifyRefreshToken,
} from "../utils/jwt";
import {
  signupSchema,
  loginSchema,
  type SignupInput,
  type LoginInput,
} from "../validators/auth.validators";

// -- Types --------------------------------------------------------------------

/** User object returned to the client (password excluded) */
export interface SafeUser {
  id: string;
  email: string;
  name: string;
  avatar: string | null;
  createdAt: Date;
  updatedAt: Date;
}

export interface AuthResult {
  user: SafeUser;
  accessToken: string;
  refreshToken: string;
}

// -- Helpers ------------------------------------------------------------------

/** Select clause that omits the password field */
const safeUserSelect = {
  id: true,
  email: true,
  name: true,
  avatar: true,
  createdAt: true,
  updatedAt: true,
} as const;

// -- Service Functions --------------------------------------------------------

/**
 * Sign up a new user.
 *
 * 1. Validate input with Zod
 * 2. Check if email already taken  -> throw 409
 * 3. Hash password with bcrypt (10 rounds)
 * 4. Create user in DB
 * 5. Generate access + refresh tokens
 * 6. Return user (sans password) + tokens
 */
export async function signUp(input: SignupInput): Promise<AuthResult> {
  // 1. Validate
  const data = signupSchema.parse(input);

  // 2. Check for existing email
  const existing = await prisma.user.findUnique({
    where: { email: data.email },
    select: { id: true },
  });

  if (existing) {
    const error = new Error("An account with this email already exists");
    (error as any).statusCode = 409;
    throw error;
  }

  // 3. Hash password
  const hashedPassword = await hashPassword(data.password);

  // 4. Create user
  const user = await prisma.user.create({
    data: {
      email: data.email,
      password: hashedPassword,
      name: data.name,
    },
    select: safeUserSelect,
  });

  // 5. Generate tokens
  const accessToken = generateAccessToken({
    userId: user.id,
    email: user.email,
  });
  const refreshToken = generateRefreshToken(user.id);

  // 6. Return
  return { user, accessToken, refreshToken };
}

/**
 * Sign in an existing user.
 *
 * 1. Validate input with Zod
 * 2. Find user by email           -> throw 401
 * 3. Compare password with bcrypt  -> throw 401
 * 4. Generate access + refresh tokens
 * 5. Return user (sans password) + tokens
 */
export async function signIn(input: LoginInput): Promise<AuthResult> {
  // 1. Validate
  const data = loginSchema.parse(input);

  // 2. Find user (need password for comparison)
  const user = await prisma.user.findUnique({
    where: { email: data.email },
  });

  if (!user) {
    const error = new Error("Invalid email or password");
    (error as any).statusCode = 401;
    throw error;
  }

  // 3. Compare password
  const valid = await comparePassword(data.password, user.password);
  if (!valid) {
    const error = new Error("Invalid email or password");
    (error as any).statusCode = 401;
    throw error;
  }

  // 4. Generate tokens
  const accessToken = generateAccessToken({
    userId: user.id,
    email: user.email,
  });
  const refreshToken = generateRefreshToken(user.id);

  // 5. Return user without password
  const { password: _, ...safeUser } = user;
  return { user: safeUser, accessToken, refreshToken };
}

/**
 * Refresh an access token using a valid refresh token.
 *
 * 1. Verify refresh token         -> throw 401
 * 2. Verify user still exists     -> throw 401
 * 3. Issue new access token
 * 4. Return new access token
 */
export async function refreshAccessToken(
  token: string,
): Promise<{ accessToken: string }> {
  // 1. Verify
  let payload;
  try {
    payload = verifyRefreshToken(token);
  } catch {
    const error = new Error("Invalid or expired refresh token");
    (error as any).statusCode = 401;
    throw error;
  }

  // 2. Check user still exists
  const user = await prisma.user.findUnique({
    where: { id: payload.userId },
    select: { id: true, email: true },
  });

  if (!user) {
    const error = new Error("User no longer exists");
    (error as any).statusCode = 401;
    throw error;
  }

  // 3. Generate new access token
  const accessToken = generateAccessToken({
    userId: user.id,
    email: user.email,
  });

  return { accessToken };
}

/**
 * Get the current user's profile by ID (password excluded).
 */
export async function getMe(userId: string): Promise<SafeUser | null> {
  return prisma.user.findUnique({
    where: { id: userId },
    select: safeUserSelect,
  });
}
