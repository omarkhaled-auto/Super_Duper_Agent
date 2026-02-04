// =============================================================================
// Project API Tests — /api/projects
//
// Tests project creation, listing, and member invitation with mocked Prisma.
// All endpoints require authentication, so every request includes a JWT.
// =============================================================================

import { describe, it, expect, beforeEach } from "vitest";
import request from "supertest";
import app from "../app";
import {
  prismaMock,
  mockUser,
  mockProject,
  mockMembership,
  authHeader,
} from "./setup";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const TEST_USER_ID = "cluser000000000001";
const TEST_PROJECT_ID = "clproj000000000001";

/**
 * Set up the common auth mock so requireAuth passes for every request.
 * Individual tests add their own mocks for specific service calls.
 */
function setupAuthMock() {
  prismaMock.user.findUnique.mockResolvedValue(
    mockUser({ id: TEST_USER_ID, email: "test@example.com" }),
  );
}

describe("Project Routes — /api/projects", () => {
  beforeEach(() => {
    setupAuthMock();
  });

  // ===========================================================================
  // POST /api/projects — Create project
  // ===========================================================================
  describe("POST /api/projects", () => {
    it("creates a project and adds the creator as ADMIN member", async () => {
      const createdProject = {
        ...mockProject({ id: TEST_PROJECT_ID, name: "My Board" }),
        members: [
          {
            id: "clmemb001",
            role: "ADMIN",
            userId: TEST_USER_ID,
            projectId: TEST_PROJECT_ID,
            createdAt: new Date(),
            user: {
              id: TEST_USER_ID,
              name: "Test User",
              email: "test@example.com",
              avatar: null,
            },
          },
        ],
        _count: { members: 1, tasks: 0 },
      };

      // createProject service creates the project
      prismaMock.project.create.mockResolvedValueOnce(createdProject);

      // Activity log
      prismaMock.activity.create.mockResolvedValueOnce({ id: "act1" });

      const res = await request(app)
        .post("/api/projects")
        .set("Authorization", authHeader())
        .send({
          name: "My Board",
          description: "Project management board",
        })
        .expect(201);

      // Response shape
      expect(res.body).toHaveProperty("id", TEST_PROJECT_ID);
      expect(res.body).toHaveProperty("name", "My Board");
      expect(res.body).toHaveProperty("members");
      expect(Array.isArray(res.body.members)).toBe(true);
      expect(res.body.members).toHaveLength(1);

      // Creator should be an ADMIN member
      expect(res.body.members[0]).toHaveProperty("role", "ADMIN");
      expect(res.body.members[0].user).toHaveProperty("id", TEST_USER_ID);

      // Count metadata
      expect(res.body._count).toHaveProperty("members", 1);
      expect(res.body._count).toHaveProperty("tasks", 0);

      // Verify Prisma create was called
      expect(prismaMock.project.create).toHaveBeenCalledTimes(1);

      // Verify the create call includes the nested member creation with ADMIN role
      const createCall = prismaMock.project.create.mock.calls[0]![0];
      expect(createCall.data).toHaveProperty("name", "My Board");
      expect(createCall.data.members).toEqual({
        create: { userId: TEST_USER_ID, role: "ADMIN" },
      });
    });
  });

  // ===========================================================================
  // GET /api/projects — List user's projects
  // ===========================================================================
  describe("GET /api/projects", () => {
    it("lists projects the authenticated user belongs to", async () => {
      const projects = [
        {
          ...mockProject({ id: "clproj01", name: "Project Alpha" }),
          _count: { members: 3, tasks: 12 },
          members: [{ role: "ADMIN" }],
        },
        {
          ...mockProject({ id: "clproj02", name: "Project Beta" }),
          _count: { members: 2, tasks: 5 },
          members: [{ role: "MEMBER" }],
        },
      ];

      // listProjects service queries projects where user is a member
      prismaMock.project.findMany.mockResolvedValueOnce(projects);

      const res = await request(app)
        .get("/api/projects")
        .set("Authorization", authHeader())
        .expect(200);

      // Response should be an array of projects
      expect(Array.isArray(res.body)).toBe(true);
      expect(res.body).toHaveLength(2);

      // First project
      expect(res.body[0]).toHaveProperty("id", "clproj01");
      expect(res.body[0]).toHaveProperty("name", "Project Alpha");
      expect(res.body[0]).toHaveProperty("memberCount", 3);
      expect(res.body[0]).toHaveProperty("taskCount", 12);
      expect(res.body[0]).toHaveProperty("myRole", "ADMIN");

      // Second project
      expect(res.body[1]).toHaveProperty("id", "clproj02");
      expect(res.body[1]).toHaveProperty("name", "Project Beta");
      expect(res.body[1]).toHaveProperty("myRole", "MEMBER");

      // Verify Prisma was called
      expect(prismaMock.project.findMany).toHaveBeenCalledTimes(1);
    });
  });

  // ===========================================================================
  // POST /api/projects/:id/members — Invite member
  // ===========================================================================
  describe("POST /api/projects/:id/members", () => {
    it("invites a new member to the project", async () => {
      const invitedUserId = "cluser000000000002";
      const invitedUser = mockUser({
        id: invitedUserId,
        email: "invited@example.com",
        name: "Invited User",
      });

      // checkProjectRole middleware: verify caller is ADMIN
      prismaMock.projectMember.findUnique
        .mockResolvedValueOnce(
          mockMembership({
            userId: TEST_USER_ID,
            projectId: TEST_PROJECT_ID,
            role: "ADMIN",
          }),
        )
        // addMember service: check if target user is already a member (return null = not yet)
        .mockResolvedValueOnce(null);

      // addMember service: find the invited user by email
      // NOTE: user.findUnique is already mocked for requireAuth (returns test user).
      // The addMember service calls findUnique with a different where clause.
      // We add a new resolved value — the mock will serve them in order.
      prismaMock.user.findUnique
        .mockResolvedValueOnce(
          // This is consumed by the requireAuth middleware
          mockUser({ id: TEST_USER_ID, email: "test@example.com" }),
        )
        .mockResolvedValueOnce(
          // This is consumed by addMember to find the target user by email
          { id: invitedUserId, name: "Invited User", email: "invited@example.com" },
        );

      // Create the membership
      const createdMembership = {
        id: "clmemb002",
        role: "MEMBER",
        userId: invitedUserId,
        projectId: TEST_PROJECT_ID,
        createdAt: new Date(),
        user: {
          id: invitedUserId,
          name: "Invited User",
          email: "invited@example.com",
          avatar: null,
        },
      };
      prismaMock.projectMember.create.mockResolvedValueOnce(createdMembership);

      // Activity log
      prismaMock.activity.create.mockResolvedValueOnce({ id: "act5" });

      const res = await request(app)
        .post(`/api/projects/${TEST_PROJECT_ID}/members`)
        .set("Authorization", authHeader())
        .send({
          email: "invited@example.com",
          role: "MEMBER",
        })
        .expect(201);

      // Response shape
      expect(res.body).toHaveProperty("id", "clmemb002");
      expect(res.body).toHaveProperty("role", "MEMBER");
      expect(res.body).toHaveProperty("user");
      expect(res.body.user).toHaveProperty("email", "invited@example.com");
      expect(res.body.user).toHaveProperty("name", "Invited User");

      // Verify the membership was created
      expect(prismaMock.projectMember.create).toHaveBeenCalledTimes(1);
    });
  });
});
