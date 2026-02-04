// =============================================================================
// Activity Routes — /api/activity
// =============================================================================

import { Router, Request, Response, NextFunction } from "express";
import { requireAuth } from "../middleware/auth";
import { checkProjectRole } from "../middleware/check-project-role";
import {
  getTaskActivity,
  getProjectActivity,
  getUserActivity,
} from "../services/activity.service";

const router = Router();

router.use(requireAuth);

// GET /api/activity/me — Current user's recent activity
router.get("/me", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const activity = await getUserActivity(req.user!.userId);
    res.json(activity);
  } catch (err) {
    next(err);
  }
});

// GET /api/activity/tasks/:id — Task activity log
router.get("/tasks/:id", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const id = req.params["id"] as string;
    const limit = parseInt(req.query["limit"] as string) || 20;
    const activity = await getTaskActivity(id, limit);
    res.json(activity);
  } catch (err) {
    next(err);
  }
});

// GET /api/activity/projects/:id — Project activity feed (last 50)
router.get(
  "/projects/:id",
  checkProjectRole(),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const id = req.params["id"] as string;
      const limit = parseInt(req.query["limit"] as string) || 50;
      const activity = await getProjectActivity(id, limit);
      res.json(activity);
    } catch (err) {
      next(err);
    }
  },
);

export default router;
