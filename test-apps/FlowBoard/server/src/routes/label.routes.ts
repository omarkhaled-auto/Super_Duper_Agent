// =============================================================================
// Label Routes — /api/labels
//
// Label routes that operate on individual labels (by label ID).
// Project-scoped label routes (create/list) are on the project router.
// =============================================================================

import { Router, Request, Response, NextFunction } from "express";
import { requireAuth } from "../middleware/auth";
import { validate } from "../middleware/validate";
import { setTaskLabelsSchema } from "../validators/task.validators";
import * as taskService from "../services/task.service";

const router = Router();

router.use(requireAuth);

// PUT /api/labels/tasks/:taskId — Set task labels (alternative path)
router.put(
  "/tasks/:taskId",
  validate(setTaskLabelsSchema),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const taskId = req.params["taskId"] as string;
      const result = await taskService.setTaskLabels(taskId, req.body.labelIds, req.user!.userId);
      res.json(result);
    } catch (err) {
      next(err);
    }
  },
);

export default router;
