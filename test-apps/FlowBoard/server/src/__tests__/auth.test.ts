// =============================================================================
// Auth API Tests — /api/auth
//
// Tests signup and login flows with mocked Prisma and bcrypt.
// =============================================================================

import { describe, it, expect } from "vitest";
import request from "supertest";
import bcrypt from "bcrypt";
import app from "../app";
import { prismaMock, mockUser, mockUserWithPassword } from "./setup";

describe("Auth Routes — /api/auth", () => {
  // ===========================================================================
  // POST /api/auth/signup
  // ===========================================================================
  describe("POST /api/auth/signup", () => {
    it("creates a user successfully and returns tokens", async () => {
      const newUser = mockUser();

      // The service first checks if email already exists — return null (no duplicate)
      prismaMock.user.findUnique.mockResolvedValueOnce(null);

      // Then it creates the user
      prismaMock.user.create.mockResolvedValueOnce(newUser);

      const res = await request(app)
        .post("/api/auth/signup")
        .send({
          email: "test@example.com",
          password: "SecurePass123",
          name: "Test User",
        })
        .expect(201);

      // Response shape
      expect(res.body).toHaveProperty("user");
      expect(res.body).toHaveProperty("accessToken");
      expect(res.body).toHaveProperty("refreshToken");

      // User data
      expect(res.body.user.email).toBe("test@example.com");
      expect(res.body.user.name).toBe("Test User");
      expect(res.body.user).not.toHaveProperty("password");

      // Tokens should be non-empty strings
      expect(typeof res.body.accessToken).toBe("string");
      expect(res.body.accessToken.length).toBeGreaterThan(0);
      expect(typeof res.body.refreshToken).toBe("string");
      expect(res.body.refreshToken.length).toBeGreaterThan(0);

      // Verify Prisma was called correctly
      expect(prismaMock.user.findUnique).toHaveBeenCalledWith({
        where: { email: "test@example.com" },
        select: { id: true },
      });
      expect(prismaMock.user.create).toHaveBeenCalledTimes(1);
    });

    it("rejects an invalid email format with 400", async () => {
      const res = await request(app)
        .post("/api/auth/signup")
        .send({
          email: "not-an-email",
          password: "SecurePass123",
          name: "Test User",
        })
        .expect(400);

      // Should return a validation error
      expect(res.body).toHaveProperty("message", "Validation failed");
      expect(res.body).toHaveProperty("errors");
      expect(Array.isArray(res.body.errors)).toBe(true);
      expect(res.body.errors.length).toBeGreaterThan(0);

      // The error should mention the email field
      const emailError = res.body.errors.find(
        (e: { field: string }) => e.field === "email",
      );
      expect(emailError).toBeDefined();

      // Prisma should never have been called
      expect(prismaMock.user.findUnique).not.toHaveBeenCalled();
      expect(prismaMock.user.create).not.toHaveBeenCalled();
    });
  });

  // ===========================================================================
  // POST /api/auth/login
  // ===========================================================================
  describe("POST /api/auth/login", () => {
    it("authenticates with correct credentials and returns tokens", async () => {
      const userWithPassword = mockUserWithPassword();

      // signIn finds user by email (needs password for bcrypt compare)
      prismaMock.user.findUnique.mockResolvedValueOnce(userWithPassword);

      // bcrypt.compare is already mocked to return true by default in setup.ts
      const res = await request(app)
        .post("/api/auth/login")
        .send({
          email: "test@example.com",
          password: "SecurePass123",
        })
        .expect(200);

      // Response shape
      expect(res.body).toHaveProperty("user");
      expect(res.body).toHaveProperty("accessToken");
      expect(res.body).toHaveProperty("refreshToken");

      // User data — should NOT include password
      expect(res.body.user.email).toBe("test@example.com");
      expect(res.body.user.name).toBe("Test User");
      expect(res.body.user).not.toHaveProperty("password");

      // Tokens
      expect(typeof res.body.accessToken).toBe("string");
      expect(typeof res.body.refreshToken).toBe("string");

      // Verify bcrypt.compare was called
      expect(bcrypt.compare).toHaveBeenCalledWith(
        "SecurePass123",
        "$2b$10$hashedpasswordmock",
      );
    });

    it("rejects wrong password with 401", async () => {
      const userWithPassword = mockUserWithPassword();

      // User exists
      prismaMock.user.findUnique.mockResolvedValueOnce(userWithPassword);

      // Override bcrypt.compare to return false for wrong password
      (bcrypt.compare as ReturnType<typeof vi.fn>).mockResolvedValueOnce(false);

      const res = await request(app)
        .post("/api/auth/login")
        .send({
          email: "test@example.com",
          password: "WrongPassword",
        })
        .expect(401);

      // Should return an error message
      expect(res.body).toHaveProperty("message");
      expect(res.body.message).toMatch(/invalid/i);
    });
  });
});
