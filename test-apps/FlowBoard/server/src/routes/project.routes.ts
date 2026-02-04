// =============================================================================
// Project Routes — /api/projects
// =============================================================================

import { Router, Request, Response, NextFunction } from "express";
import { requireAuth } from "../middleware/auth";
import { validate } from "../middleware/validate";
import { checkProjectRole } from "../middleware/check-project-role";
import {
  createProjectSchema,
  updateProjectSchema,
  addMemberSchema,
  updateMemberRoleSchema,
  createLabelSchema,
} from "../validators/project.validators";
import * as projectService from "../services/project.service";
import { emitToProject, SOCKET_EVENTS } from "../socket";

const router = Router();

router.use(requireAuth);

// ── Project CRUD ────────────────────────────────────────────────────────────

// POST /api/projects — Create project
router.post("/", validate(createProjectSchema), async (req: Request, res: Response, next: NextFunction) => {
  try {
    const project = await projectService.createProject(req.body, req.user!.userId);
    res.status(201).json(project);
  } catch (err) {
    next(err);
  }
});

// GET /api/projects — List projects for the current user
router.get("/", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const projects = await projectService.listProjects(req.user!.userId);
    res.json(projects);
  } catch (err) {
    next(err);
  }
});

// GET /api/projects/:id — Get project details
router.get("/:id", checkProjectRole(), async (req: Request, res: Response, next: NextFunction) => {
  try {
    const id = req.params["id"] as string;
    const project = await projectService.getProject(id, req.user!.userId);
    res.json(project);
  } catch (err) {
    next(err);
  }
});

// PUT /api/projects/:id — Update project (Admin only)
router.put(
  "/:id",
  checkProjectRole(["ADMIN"]),
  validate(updateProjectSchema),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const id = req.params["id"] as string;
      const project = await projectService.updateProject(id, req.body, req.user!.userId);
      res.json(project);

      // Emit real-time project update event
      emitToProject(id, SOCKET_EVENTS.PROJECT_UPDATED, { projectId: id, project });
    } catch (err) {
      next(err);
    }
  },
);

// PUT /api/projects/:id/archive — Toggle archive (Admin only)
router.put(
  "/:id/archive",
  checkProjectRole(["ADMIN"]),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const id = req.params["id"] as string;
      const project = await projectService.toggleArchive(id, req.user!.userId);
      res.json(project);
    } catch (err) {
      next(err);
    }
  },
);

// ── Members ─────────────────────────────────────────────────────────────────

// GET /api/projects/:id/members — List members
router.get("/:id/members", checkProjectRole(), async (req: Request, res: Response, next: NextFunction) => {
  try {
    const id = req.params["id"] as string;
    const members = await projectService.listMembers(id);
    res.json(members);
  } catch (err) {
    next(err);
  }
});

// POST /api/projects/:id/members — Add member (Admin only)
router.post(
  "/:id/members",
  checkProjectRole(["ADMIN"]),
  validate(addMemberSchema),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const id = req.params["id"] as string;
      const member = await projectService.addMember(id, req.body, req.user!.userId);
      res.status(201).json(member);
    } catch (err) {
      next(err);
    }
  },
);

// PUT /api/projects/:id/members/:userId — Update member role (Admin only)
router.put(
  "/:id/members/:userId",
  checkProjectRole(["ADMIN"]),
  validate(updateMemberRoleSchema),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const id = req.params["id"] as string;
      const userId = req.params["userId"] as string;
      const member = await projectService.updateMemberRole(id, userId, req.body.role, req.user!.userId);
      res.json(member);
    } catch (err) {
      next(err);
    }
  },
);

// DELETE /api/projects/:id/members/:userId — Remove member (Admin only)
router.delete(
  "/:id/members/:userId",
  checkProjectRole(["ADMIN"]),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const id = req.params["id"] as string;
      const userId = req.params["userId"] as string;
      const result = await projectService.removeMember(id, userId, req.user!.userId);
      res.json(result);
    } catch (err) {
      next(err);
    }
  },
);

// ── Labels ──────────────────────────────────────────────────────────────────

// GET /api/projects/:id/labels — List labels
router.get("/:id/labels", checkProjectRole(), async (req: Request, res: Response, next: NextFunction) => {
  try {
    const id = req.params["id"] as string;
    const labels = await projectService.listLabels(id);
    res.json(labels);
  } catch (err) {
    next(err);
  }
});

// POST /api/projects/:id/labels — Create label
router.post(
  "/:id/labels",
  checkProjectRole(["ADMIN", "MEMBER"]),
  validate(createLabelSchema),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const id = req.params["id"] as string;
      const label = await projectService.createLabel(id, req.body.name, req.body.color, req.user!.userId);
      res.status(201).json(label);
    } catch (err) {
      next(err);
    }
  },
);

export default router;
