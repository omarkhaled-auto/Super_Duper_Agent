// =============================================================================
// Test Setup — Mock Prisma, JWT helpers, and test data factories
//
// This file is loaded by vitest before every test file via setupFiles config.
// It mocks the Prisma client and the Socket.io emitter so route handlers can
// execute their logic without hitting a real database or socket server.
// =============================================================================

import { vi, beforeEach } from "vitest";
import jwt from "jsonwebtoken";

// ---------------------------------------------------------------------------
// JWT secret used in the real app (defaults to "change-me" in dev)
// ---------------------------------------------------------------------------
const JWT_SECRET = process.env.JWT_SECRET ?? "change-me";

// ---------------------------------------------------------------------------
// Mock Prisma Client
//
// Every Prisma model method is replaced with a vi.fn() that returns undefined
// by default. Individual tests override return values with mockResolvedValue.
// ---------------------------------------------------------------------------
export const prismaMock = {
  user: {
    findUnique: vi.fn(),
    findMany: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    count: vi.fn(),
  },
  project: {
    findUnique: vi.fn(),
    findMany: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    count: vi.fn(),
  },
  projectMember: {
    findUnique: vi.fn(),
    findMany: vi.fn(),
    create: vi.fn(),
    createMany: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    deleteMany: vi.fn(),
    count: vi.fn(),
  },
  task: {
    findUnique: vi.fn(),
    findFirst: vi.fn(),
    findMany: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    updateMany: vi.fn(),
    delete: vi.fn(),
    deleteMany: vi.fn(),
    count: vi.fn(),
  },
  subTask: {
    findUnique: vi.fn(),
    findFirst: vi.fn(),
    findMany: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    count: vi.fn(),
  },
  taskLabel: {
    findUnique: vi.fn(),
    findMany: vi.fn(),
    create: vi.fn(),
    createMany: vi.fn(),
    delete: vi.fn(),
    deleteMany: vi.fn(),
  },
  label: {
    findUnique: vi.fn(),
    findMany: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
  },
  comment: {
    findUnique: vi.fn(),
    findMany: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
  },
  activity: {
    findMany: vi.fn(),
    create: vi.fn(),
  },
  $transaction: vi.fn().mockImplementation(async (fn: (tx: any) => any) => {
    // Execute the transaction callback with the same mock prisma
    return fn(prismaMock);
  }),
};

// Mock the prisma module — every import of "../lib/prisma" gets our mock
vi.mock("../lib/prisma", () => ({
  prisma: prismaMock,
  default: prismaMock,
}));

// ---------------------------------------------------------------------------
// Mock Socket.io emitter — prevents route handlers from failing when they
// try to emit events after DB mutations
// ---------------------------------------------------------------------------
vi.mock("../socket", () => ({
  initSocketServer: vi.fn(),
  getIO: vi.fn(() => ({
    to: vi.fn(() => ({ emit: vi.fn() })),
  })),
  emitToProject: vi.fn(),
  SOCKET_EVENTS: {
    TASK_CREATED: "task:created",
    TASK_UPDATED: "task:updated",
    TASK_DELETED: "task:deleted",
    TASK_REORDERED: "task:reordered",
    COMMENT_CREATED: "comment:created",
    COMMENT_DELETED: "comment:deleted",
    PRESENCE_JOIN: "presence:join",
    PRESENCE_LEAVE: "presence:leave",
    PRESENCE_LIST: "presence:list",
    PROJECT_UPDATED: "project:updated",
    JOIN_PROJECT: "join-project",
    LEAVE_PROJECT: "leave-project",
  },
}));

// ---------------------------------------------------------------------------
// Mock bcrypt — speeds up tests by skipping real hashing (10 salt rounds)
// ---------------------------------------------------------------------------
vi.mock("bcrypt", () => ({
  default: {
    hash: vi.fn().mockResolvedValue("$2b$10$hashedpasswordmock"),
    compare: vi.fn().mockResolvedValue(true),
  },
  hash: vi.fn().mockResolvedValue("$2b$10$hashedpasswordmock"),
  compare: vi.fn().mockResolvedValue(true),
}));

// ---------------------------------------------------------------------------
// Reset all mocks before each test
// ---------------------------------------------------------------------------
beforeEach(() => {
  vi.clearAllMocks();
});

// =============================================================================
// Test Data Factories
// =============================================================================

const NOW = new Date("2025-01-15T12:00:00.000Z");

/** Generate a mock user object matching the Prisma User model (without password) */
export function mockUser(overrides: Record<string, unknown> = {}) {
  return {
    id: "cluser000000000001",
    email: "test@example.com",
    name: "Test User",
    avatar: null,
    createdAt: NOW,
    updatedAt: NOW,
    ...overrides,
  };
}

/** Generate a mock user with password (for signIn flows that need comparison) */
export function mockUserWithPassword(overrides: Record<string, unknown> = {}) {
  return {
    ...mockUser(overrides),
    password: "$2b$10$hashedpasswordmock",
  };
}

/** Generate a mock project object matching the Prisma Project model */
export function mockProject(overrides: Record<string, unknown> = {}) {
  return {
    id: "clproj000000000001",
    name: "Test Project",
    description: "A test project",
    icon: "folder",
    color: "#8B5CF6",
    archived: false,
    createdAt: NOW,
    updatedAt: NOW,
    ...overrides,
  };
}

/** Generate a mock task object matching the Prisma Task model */
export function mockTask(overrides: Record<string, unknown> = {}) {
  return {
    id: "cltask000000000001",
    title: "Test Task",
    description: "A test task description",
    status: "BACKLOG",
    priority: "MEDIUM",
    position: 0,
    projectId: "clproj000000000001",
    assigneeId: null,
    creatorId: "cluser000000000001",
    dueDate: null,
    createdAt: NOW,
    updatedAt: NOW,
    ...overrides,
  };
}

/** Generate a mock project membership record */
export function mockMembership(overrides: Record<string, unknown> = {}) {
  return {
    id: "clmemb000000000001",
    role: "ADMIN",
    userId: "cluser000000000001",
    projectId: "clproj000000000001",
    createdAt: NOW,
    ...overrides,
  };
}

// =============================================================================
// JWT Helpers for Tests
// =============================================================================

/**
 * Generate a valid JWT access token for a test user.
 * This token will pass the requireAuth middleware when paired with a
 * prisma.user.findUnique mock that returns the matching user.
 */
export function generateTestToken(
  userId = "cluser000000000001",
  email = "test@example.com",
): string {
  return jwt.sign({ userId, email }, JWT_SECRET, { expiresIn: "15m" });
}

/**
 * Build an Authorization header value for test requests.
 */
export function authHeader(
  userId = "cluser000000000001",
  email = "test@example.com",
): string {
  return `Bearer ${generateTestToken(userId, email)}`;
}
