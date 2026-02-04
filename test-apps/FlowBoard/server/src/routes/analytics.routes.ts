// =============================================================================
// Analytics Routes — /api/analytics
// =============================================================================

import { Router, Request, Response, NextFunction } from "express";
import { requireAuth } from "../middleware/auth";
import { prisma } from "../lib/prisma";
import { AppError } from "../middleware/error-handler";
import { getProjectAnalytics } from "../services/analytics.service";

const router = Router();

// All analytics routes require authentication
router.use(requireAuth);

// -- GET /api/analytics/projects/:id — Project analytics -----------------------
//
// Returns:
//   - tasksOverTime: Array of { date, count } for completed tasks over last 30 days
//   - tasksByStatus: Array of { status, count }
//   - tasksByPriority: Array of { priority, count }
//   - velocity: Array of { week, count } for tasks completed per week over last 8 weeks
//
// Requires: authenticated user must be a member of the project.

router.get(
  "/projects/:id",
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const projectId = req.params["id"] as string;
      const userId = req.user!.userId;

      if (!projectId) {
        throw new AppError(400, "Project ID is required");
      }

      // Verify the project exists
      const project = await prisma.project.findUnique({
        where: { id: projectId },
        select: { id: true },
      });

      if (!project) {
        throw new AppError(404, "Project not found");
      }

      // Verify the user is a member of the project
      const membership = await prisma.projectMember.findUnique({
        where: {
          userId_projectId: {
            userId,
            projectId,
          },
        },
        select: { id: true },
      });

      if (!membership) {
        throw new AppError(403, "You are not a member of this project");
      }

      // Compute analytics
      const analytics = await getProjectAnalytics(projectId);

      res.json(analytics);
    } catch (err) {
      next(err);
    }
  },
);

export default router;
