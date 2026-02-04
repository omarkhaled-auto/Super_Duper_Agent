// =============================================================================
// Search Routes — /api/search
// =============================================================================

import { Router, Request, Response, NextFunction } from "express";
import { requireAuth } from "../middleware/auth";
import { searchQuerySchema } from "../validators/user.validators";
import { searchAll } from "../services/search.service";

const router = Router();

// All search routes require authentication
router.use(requireAuth);

// -- GET /api/search?q=query — Global search -----------------------------------
//
// Searches across tasks (title, description), projects (name), and users (name, email).
// Returns grouped results: { tasks: [], projects: [], users: [] }
// Limited to 5 results per category.

router.get("/", async (req: Request, res: Response, next: NextFunction) => {
  try {
    // Validate query param with Zod
    const { q } = searchQuerySchema.parse(req.query);

    const userId = req.user!.userId;

    const results = await searchAll(q, userId);

    res.json(results);
  } catch (err) {
    next(err);
  }
});

export default router;
