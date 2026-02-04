// =============================================================================
// Task Routes — /api/tasks and /api/projects/:projectId/tasks
//
// This router handles two mount points:
//   - /api/projects/:projectId/tasks  (project-scoped task endpoints)
//   - /api/tasks                      (task-level endpoints by task ID)
// The main index.ts mounts them accordingly.
// =============================================================================

import { Router, Request, Response, NextFunction } from "express";
import { requireAuth } from "../middleware/auth";
import { validate } from "../middleware/validate";
import { checkProjectRole } from "../middleware/check-project-role";
import {
  createTaskSchema,
  updateTaskSchema,
  reorderTaskSchema,
  bulkActionSchema,
  listTasksQuerySchema,
  createSubtaskSchema,
  updateSubtaskSchema,
  setTaskLabelsSchema,
} from "../validators/task.validators";
import * as taskService from "../services/task.service";
import { emitToProject, SOCKET_EVENTS } from "../socket";

// =============================================================================
// Project-scoped task router: mounted at /api/projects/:projectId/tasks
// =============================================================================
export const projectTaskRouter = Router({ mergeParams: true });
projectTaskRouter.use(requireAuth);

// POST /api/projects/:projectId/tasks — Create task
projectTaskRouter.post(
  "/",
  checkProjectRole(["ADMIN", "MEMBER"], "projectId"),
  validate(createTaskSchema),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const projectId = req.params["projectId"] as string;
      const task = await taskService.createTask(projectId, req.body, req.user!.userId);
      res.status(201).json(task);

      // Emit real-time event to all clients viewing this project
      emitToProject(projectId, SOCKET_EVENTS.TASK_CREATED, task);
    } catch (err) {
      next(err);
    }
  },
);

// GET /api/projects/:projectId/tasks — List tasks with filters
projectTaskRouter.get(
  "/",
  checkProjectRole(undefined, "projectId"),
  validate(listTasksQuerySchema, "query"),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const projectId = req.params["projectId"] as string;
      const result = await taskService.listTasks(projectId, req.query as any);
      res.json(result);
    } catch (err) {
      next(err);
    }
  },
);

// =============================================================================
// Task-level router: mounted at /api/tasks
// =============================================================================
const router = Router();
router.use(requireAuth);

// POST /api/tasks/bulk — Bulk action (must be above /:id routes)
router.post("/bulk", validate(bulkActionSchema), async (req: Request, res: Response, next: NextFunction) => {
  try {
    const result = await taskService.bulkAction(req.body, req.user!.userId);
    res.json(result);
  } catch (err) {
    next(err);
  }
});

// GET /api/tasks/:id — Get single task with details
router.get("/:id", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const id = req.params["id"] as string;
    const task = await taskService.getTask(id);
    res.json(task);
  } catch (err) {
    next(err);
  }
});

// PUT /api/tasks/:id — Update task
router.put("/:id", validate(updateTaskSchema), async (req: Request, res: Response, next: NextFunction) => {
  try {
    const id = req.params["id"] as string;
    const task = await taskService.updateTask(id, req.body, req.user!.userId);
    res.json(task);

    // Emit real-time update to project room
    if (task.projectId) {
      emitToProject(task.projectId, SOCKET_EVENTS.TASK_UPDATED, task);
    }
  } catch (err) {
    next(err);
  }
});

// DELETE /api/tasks/:id — Delete task
router.delete("/:id", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const id = req.params["id"] as string;

    // Fetch task info before deletion so we can emit the event
    const taskInfo = await taskService.getTask(id);
    const projectId = taskInfo.projectId;

    const result = await taskService.deleteTask(id, req.user!.userId);
    res.json(result);

    // Emit real-time deletion event to project room
    emitToProject(projectId, SOCKET_EVENTS.TASK_DELETED, {
      taskId: id,
      projectId,
    });
  } catch (err) {
    next(err);
  }
});

// PUT /api/tasks/:id/reorder — Reorder / move task (Kanban drag-and-drop)
router.put(
  "/:id/reorder",
  validate(reorderTaskSchema),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const id = req.params["id"] as string;
      const task = await taskService.reorderTask(id, req.body, req.user!.userId);
      res.json(task);

      // Emit real-time reorder event to project room
      if (task?.projectId) {
        emitToProject(task.projectId, SOCKET_EVENTS.TASK_REORDERED, {
          task,
          status: req.body.status,
          position: req.body.position,
        });
      }
    } catch (err) {
      next(err);
    }
  },
);

// PUT /api/tasks/:id/labels — Set task labels
router.put(
  "/:id/labels",
  validate(setTaskLabelsSchema),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const id = req.params["id"] as string;
      const result = await taskService.setTaskLabels(id, req.body.labelIds, req.user!.userId);
      res.json(result);
    } catch (err) {
      next(err);
    }
  },
);

// ── Sub-tasks ─────────────────────────────────────────────────────────────

// POST /api/tasks/:id/subtasks — Create subtask
router.post(
  "/:id/subtasks",
  validate(createSubtaskSchema),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const id = req.params["id"] as string;
      const subtask = await taskService.createSubtask(id, req.body, req.user!.userId);
      res.status(201).json(subtask);
    } catch (err) {
      next(err);
    }
  },
);

// ── Comments on tasks ───────────────────────────────────────────────────────

// POST /api/tasks/:id/comments — Create comment
router.post("/:id/comments", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const id = req.params["id"] as string;
    const { content } = req.body;
    if (!content || typeof content !== "string" || content.trim().length === 0) {
      res.status(400).json({ error: "Comment content is required" });
      return;
    }
    if (content.length > 5000) {
      res.status(400).json({ error: "Comment must be 5000 characters or fewer" });
      return;
    }
    const comment = await taskService.createComment(id, content.trim(), req.user!.userId);
    res.status(201).json(comment);

    // Emit real-time comment event — need to look up the task's projectId
    const taskInfo = await taskService.getTask(id);
    emitToProject(taskInfo.projectId, SOCKET_EVENTS.COMMENT_CREATED, {
      taskId: id,
      comment,
    });
  } catch (err) {
    next(err);
  }
});

// GET /api/tasks/:id/comments — List comments
router.get("/:id/comments", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const id = req.params["id"] as string;
    const comments = await taskService.listComments(id);
    res.json(comments);
  } catch (err) {
    next(err);
  }
});

// GET /api/tasks/:id/activity — Task activity log
router.get("/:id/activity", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const id = req.params["id"] as string;
    const { getTaskActivity } = await import("../services/activity.service");
    const activity = await getTaskActivity(id);
    res.json(activity);
  } catch (err) {
    next(err);
  }
});

export default router;
