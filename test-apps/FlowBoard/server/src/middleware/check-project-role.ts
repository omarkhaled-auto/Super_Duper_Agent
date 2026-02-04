// =============================================================================
// Check Project Role Middleware
//
// Verifies the authenticated user is a member of the specified project and
// optionally has one of the allowed roles. Attaches the membership record to
// req so downstream handlers can use it.
// =============================================================================

import { Request, Response, NextFunction } from "express";
import { prisma } from "../lib/prisma";
type ProjectRole = string;

// Extend Express Request with project membership
declare global {
  namespace Express {
    interface Request {
      projectMember?: {
        id: string;
        role: ProjectRole;
        userId: string;
        projectId: string;
      };
    }
  }
}

/**
 * Factory that returns middleware enforcing project membership.
 *
 * @param allowedRoles - If provided, at least one must match. If omitted, any
 *   membership suffices.
 * @param projectIdParam - The name of the request param holding the project ID.
 *   Defaults to "id" (for /api/projects/:id routes) but can be set to
 *   "projectId" for nested routes.
 */
export function checkProjectRole(
  allowedRoles?: ProjectRole[],
  projectIdParam: string = "id",
) {
  return async (
    req: Request,
    res: Response,
    next: NextFunction,
  ): Promise<void> => {
    const userId = req.user?.userId;
    if (!userId) {
      res.status(401).json({ error: "Authentication required" });
      return;
    }

    const projectId = req.params[projectIdParam];
    if (!projectId) {
      res.status(400).json({ error: "Project ID is required" });
      return;
    }

    try {
      const membership = await prisma.projectMember.findUnique({
        where: {
          userId_projectId: { userId, projectId },
        },
        select: { id: true, role: true, userId: true, projectId: true },
      });

      if (!membership) {
        res.status(403).json({ error: "You are not a member of this project" });
        return;
      }

      if (allowedRoles && !allowedRoles.includes(membership.role)) {
        res.status(403).json({
          error: `Requires one of the following roles: ${allowedRoles.join(", ")}`,
        });
        return;
      }

      req.projectMember = membership;
      next();
    } catch (err) {
      next(err);
    }
  };
}
