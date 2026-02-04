// =============================================================================
// Task API Tests — /api/projects/:projectId/tasks and /api/tasks
//
// Tests task CRUD and bulk operations with mocked Prisma.
// All endpoints require authentication, so every request includes a JWT.
// =============================================================================

import { describe, it, expect, beforeEach } from "vitest";
import request from "supertest";
import app from "../app";
import {
  prismaMock,
  mockUser,
  mockTask,
  mockProject,
  mockMembership,
  authHeader,
} from "./setup";

// ---------------------------------------------------------------------------
// Common setup — the auth middleware (requireAuth) verifies the JWT then
// calls prisma.user.findUnique to confirm the user still exists. We need
// this to resolve for every authenticated request.
// ---------------------------------------------------------------------------
const TEST_USER_ID = "cluser000000000001";
const TEST_PROJECT_ID = "clproj000000000001";

/**
 * Set up the common mocks needed by the requireAuth and checkProjectRole
 * middleware before each test. Individual tests add their own mocks on top.
 */
function setupAuthAndRoleMocks() {
  // requireAuth — user lookup after JWT verification
  prismaMock.user.findUnique.mockResolvedValue(
    mockUser({ id: TEST_USER_ID, email: "test@example.com" }),
  );

  // checkProjectRole — membership lookup
  prismaMock.projectMember.findUnique.mockResolvedValue(
    mockMembership({
      userId: TEST_USER_ID,
      projectId: TEST_PROJECT_ID,
      role: "ADMIN",
    }),
  );
}

describe("Task Routes", () => {
  beforeEach(() => {
    setupAuthAndRoleMocks();
  });

  // ===========================================================================
  // POST /api/projects/:projectId/tasks — Create task
  // ===========================================================================
  describe("POST /api/projects/:projectId/tasks", () => {
    it("creates a task with valid data and returns 201", async () => {
      const createdTask = {
        ...mockTask(),
        title: "New Feature",
        status: "TODO",
        priority: "HIGH",
        assignee: null,
        creator: { id: TEST_USER_ID, name: "Test User", avatar: null },
        labels: [],
        _count: { subTasks: 0, comments: 0 },
      };

      // createTask service: verify project exists
      prismaMock.project.findUnique.mockResolvedValueOnce(
        mockProject({ id: TEST_PROJECT_ID }),
      );

      // Calculate position: no existing tasks in the column
      prismaMock.task.findFirst.mockResolvedValueOnce(null);

      // Create the task
      prismaMock.task.create.mockResolvedValueOnce(createdTask);

      // Activity log
      prismaMock.activity.create.mockResolvedValueOnce({ id: "act1" });

      const res = await request(app)
        .post(`/api/projects/${TEST_PROJECT_ID}/tasks`)
        .set("Authorization", authHeader())
        .send({
          title: "New Feature",
          status: "TODO",
          priority: "HIGH",
        })
        .expect(201);

      // Response shape
      expect(res.body).toHaveProperty("id");
      expect(res.body).toHaveProperty("title", "New Feature");
      expect(res.body).toHaveProperty("status", "TODO");
      expect(res.body).toHaveProperty("priority", "HIGH");
      expect(res.body).toHaveProperty("creator");
      expect(res.body).toHaveProperty("labels");
      expect(Array.isArray(res.body.labels)).toBe(true);

      // Verify the task was created via Prisma
      expect(prismaMock.task.create).toHaveBeenCalledTimes(1);
    });
  });

  // ===========================================================================
  // GET /api/projects/:projectId/tasks — List tasks with pagination
  // ===========================================================================
  describe("GET /api/projects/:projectId/tasks", () => {
    it("returns tasks with pagination metadata", async () => {
      const tasks = [
        {
          ...mockTask({ id: "cltask1", title: "Task One" }),
          assignee: null,
          labels: [],
          _count: { subTasks: 0, comments: 0 },
        },
        {
          ...mockTask({ id: "cltask2", title: "Task Two" }),
          assignee: null,
          labels: [],
          _count: { subTasks: 1, comments: 2 },
        },
      ];

      // listTasks service uses Promise.all([findMany, count])
      prismaMock.task.findMany.mockResolvedValueOnce(tasks);
      prismaMock.task.count.mockResolvedValueOnce(2);

      const res = await request(app)
        .get(`/api/projects/${TEST_PROJECT_ID}/tasks`)
        .set("Authorization", authHeader())
        .expect(200);

      // Response shape
      expect(res.body).toHaveProperty("tasks");
      expect(res.body).toHaveProperty("total", 2);
      expect(res.body).toHaveProperty("page", 1);
      expect(res.body).toHaveProperty("limit", 50);
      expect(res.body).toHaveProperty("totalPages", 1);

      // Tasks array
      expect(Array.isArray(res.body.tasks)).toBe(true);
      expect(res.body.tasks).toHaveLength(2);
      expect(res.body.tasks[0]).toHaveProperty("title", "Task One");
      expect(res.body.tasks[1]).toHaveProperty("title", "Task Two");

      // Verify Prisma calls
      expect(prismaMock.task.findMany).toHaveBeenCalledTimes(1);
      expect(prismaMock.task.count).toHaveBeenCalledTimes(1);
    });
  });

  // ===========================================================================
  // PUT /api/tasks/:id — Update task status
  // ===========================================================================
  describe("PUT /api/tasks/:id", () => {
    it("updates task status and returns updated task", async () => {
      const taskId = "cltask000000000001";
      const existingTask = {
        ...mockTask({ id: taskId, status: "BACKLOG" }),
        labels: [],
      };
      const updatedTask = {
        ...mockTask({ id: taskId, status: "IN_PROGRESS" }),
        assignee: null,
        creator: { id: TEST_USER_ID, name: "Test User", email: "test@example.com", avatar: null },
        labels: [],
        _count: { subTasks: 0, comments: 0 },
      };

      // updateTask service: fetch existing task
      prismaMock.task.findUnique.mockResolvedValueOnce(existingTask);

      // Update the task
      prismaMock.task.update.mockResolvedValueOnce(updatedTask);

      // Activity log for status change
      prismaMock.activity.create.mockResolvedValueOnce({ id: "act2" });

      const res = await request(app)
        .put(`/api/tasks/${taskId}`)
        .set("Authorization", authHeader())
        .send({ status: "IN_PROGRESS" })
        .expect(200);

      // Response
      expect(res.body).toHaveProperty("id", taskId);
      expect(res.body).toHaveProperty("status", "IN_PROGRESS");
      expect(res.body).toHaveProperty("labels");
      expect(Array.isArray(res.body.labels)).toBe(true);

      // Verify update was called
      expect(prismaMock.task.update).toHaveBeenCalledTimes(1);
    });
  });

  // ===========================================================================
  // DELETE /api/tasks/:id — Delete task
  // ===========================================================================
  describe("DELETE /api/tasks/:id", () => {
    it("deletes a task and returns { deleted: true }", async () => {
      const taskId = "cltask000000000001";
      const taskInfo = {
        ...mockTask({ id: taskId }),
        assignee: null,
        creator: { id: TEST_USER_ID, name: "Test User", email: "test@example.com", avatar: null },
        subTasks: [],
        labels: [],
        comments: [],
        activities: [],
      };

      // getTask (called before delete to get projectId for socket emit)
      prismaMock.task.findUnique
        .mockResolvedValueOnce(taskInfo)       // getTask call in route handler
        .mockResolvedValueOnce({               // deleteTask service: verify task exists
          id: taskId,
          title: "Test Task",
          projectId: TEST_PROJECT_ID,
        });

      // Activity log before deletion
      prismaMock.activity.create.mockResolvedValueOnce({ id: "act3" });

      // Delete the task
      prismaMock.task.delete.mockResolvedValueOnce({ id: taskId });

      const res = await request(app)
        .delete(`/api/tasks/${taskId}`)
        .set("Authorization", authHeader())
        .expect(200);

      // Response
      expect(res.body).toHaveProperty("deleted", true);

      // Verify delete was called
      expect(prismaMock.task.delete).toHaveBeenCalledWith({
        where: { id: taskId },
      });
    });
  });

  // ===========================================================================
  // POST /api/tasks/bulk — Bulk update multiple tasks
  // ===========================================================================
  describe("POST /api/tasks/bulk", () => {
    it("bulk-updates status of multiple tasks", async () => {
      const taskIds = [
        "cltaskbulk00000001",
        "cltaskbulk00000002",
        "cltaskbulk00000003",
      ];
      const existingTasks = taskIds.map((id) => ({
        id,
        title: `Task ${id}`,
        projectId: TEST_PROJECT_ID,
        status: "BACKLOG",
        priority: "MEDIUM",
      }));

      // bulkAction service: verify all tasks exist
      prismaMock.task.findMany.mockResolvedValueOnce(existingTasks);

      // updateMany for the bulk status change
      prismaMock.task.updateMany.mockResolvedValueOnce({ count: 3 });

      // Activity log
      prismaMock.activity.create.mockResolvedValueOnce({ id: "act4" });

      const res = await request(app)
        .post("/api/tasks/bulk")
        .set("Authorization", authHeader())
        .send({
          taskIds,
          action: "updateStatus",
          data: { status: "DONE" },
        })
        .expect(200);

      // Response
      expect(res.body).toHaveProperty("success", true);
      expect(res.body).toHaveProperty("affected", 3);

      // Verify updateMany was called with correct IDs and status
      expect(prismaMock.task.updateMany).toHaveBeenCalledWith({
        where: { id: { in: taskIds } },
        data: { status: "DONE" },
      });
    });
  });
});
