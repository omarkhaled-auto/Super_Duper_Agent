// =============================================================================
// User Routes — /api/users
// =============================================================================

import { Router, Request, Response, NextFunction } from "express";
import { requireAuth } from "../middleware/auth";
import { prisma } from "../lib/prisma";
import { AppError } from "../middleware/error-handler";
import {
  updateProfileSchema,
  type UpdateProfileInput,
} from "../validators/user.validators";

const router = Router();

// All user routes require authentication
router.use(requireAuth);

// -- Safe select (exclude password) -------------------------------------------

const safeUserSelect = {
  id: true,
  email: true,
  name: true,
  avatar: true,
  createdAt: true,
  updatedAt: true,
} as const;

// -- GET /api/users/profile — Get current user profile -----------------------

router.get("/profile", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const userId = req.user!.userId;

    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: safeUserSelect,
    });

    if (!user) {
      throw new AppError(404, "User not found");
    }

    res.json(user);
  } catch (err) {
    next(err);
  }
});

// -- PUT /api/users/profile — Update current user's name/avatar ---------------

router.put("/profile", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const userId = req.user!.userId;

    // Validate request body with Zod
    const data: UpdateProfileInput = updateProfileSchema.parse(req.body);

    // Build update payload (only include fields that were provided)
    const updateData: Record<string, unknown> = {};
    if (data.name !== undefined) {
      updateData.name = data.name;
    }
    if (data.avatar !== undefined) {
      updateData.avatar = data.avatar;
    }

    // Nothing to update
    if (Object.keys(updateData).length === 0) {
      throw new AppError(400, "No fields to update");
    }

    const user = await prisma.user.update({
      where: { id: userId },
      data: updateData,
      select: safeUserSelect,
    });

    res.json(user);
  } catch (err) {
    next(err);
  }
});

// -- GET /api/users — List all users (for assignment dropdowns) ---------------

router.get("/", async (_req: Request, res: Response, next: NextFunction) => {
  try {
    const users = await prisma.user.findMany({
      select: {
        id: true,
        name: true,
        email: true,
        avatar: true,
      },
      orderBy: { name: "asc" },
    });

    res.json(users);
  } catch (err) {
    next(err);
  }
});

// -- GET /api/users/:id — Get user by ID --------------------------------------

router.get("/:id", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { id } = req.params;

    const user = await prisma.user.findUnique({
      where: { id },
      select: safeUserSelect,
    });

    if (!user) {
      throw new AppError(404, "User not found");
    }

    res.json(user);
  } catch (err) {
    next(err);
  }
});

export default router;
