// =============================================================================
// Subtask Routes — /api/subtasks
//
// Routes for subtask-level operations (by subtask ID).
// Task-scoped subtask creation is on the task router (POST /api/tasks/:id/subtasks).
// =============================================================================

import { Router, Request, Response, NextFunction } from "express";
import { requireAuth } from "../middleware/auth";
import { validate } from "../middleware/validate";
import { updateSubtaskSchema } from "../validators/task.validators";
import * as taskService from "../services/task.service";

const router = Router();

router.use(requireAuth);

// PUT /api/subtasks/:id — Update subtask (title, completed)
router.put("/:id", validate(updateSubtaskSchema), async (req: Request, res: Response, next: NextFunction) => {
  try {
    const id = req.params["id"] as string;
    const subtask = await taskService.updateSubtask(id, req.body, req.user!.userId);
    res.json(subtask);
  } catch (err) {
    next(err);
  }
});

// DELETE /api/subtasks/:id — Delete subtask
router.delete("/:id", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const id = req.params["id"] as string;
    const result = await taskService.deleteSubtask(id, req.user!.userId);
    res.json(result);
  } catch (err) {
    next(err);
  }
});

export default router;
