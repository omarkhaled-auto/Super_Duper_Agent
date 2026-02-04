// =============================================================================
// Comment Routes — /api/comments
//
// Task-scoped comment create/list are on the task router.
// This router handles comment-level operations (by comment ID).
// =============================================================================

import { Router, Request, Response, NextFunction } from "express";
import { requireAuth } from "../middleware/auth";
import * as taskService from "../services/task.service";
import { emitToProject, SOCKET_EVENTS } from "../socket";

const router = Router();

router.use(requireAuth);

// DELETE /api/comments/:id — Delete comment (author only)
router.delete("/:id", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const id = req.params["id"] as string;

    // Look up comment's task + project before deletion for socket emission
    const { prisma } = await import("../lib/prisma");
    const comment = await prisma.comment.findUnique({
      where: { id },
      select: { taskId: true, task: { select: { projectId: true } } },
    });

    const result = await taskService.deleteComment(id, req.user!.userId);
    res.json(result);

    // Emit real-time comment deletion event
    if (comment?.task?.projectId) {
      emitToProject(comment.task.projectId, SOCKET_EVENTS.COMMENT_DELETED, {
        commentId: id,
        taskId: comment.taskId,
      });
    }
  } catch (err) {
    next(err);
  }
});

export default router;
