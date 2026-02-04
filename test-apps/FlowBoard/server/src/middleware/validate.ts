// =============================================================================
// Zod Validation Middleware
//
// Factory that produces Express middleware to validate req.body, req.query,
// or req.params against a Zod schema.  On failure it returns 400 with a
// formatted error list.
// =============================================================================

import { Request, Response, NextFunction } from "express";
import { ZodSchema, ZodError } from "zod";

type RequestField = "body" | "query" | "params";

/**
 * Returns middleware that validates the specified request field against a Zod
 * schema.  Defaults to validating `req.body`.
 *
 * On success the parsed (and potentially transformed) value replaces the
 * original field so downstream handlers receive clean, typed data.
 *
 * On failure a 400 response is returned immediately with structured errors.
 *
 * @example
 *   router.post("/tasks", validate(createTaskSchema), taskController.create);
 *   router.get("/tasks", validate(listQuerySchema, "query"), taskController.list);
 */
export function validate(schema: ZodSchema, field: RequestField = "body") {
  return (req: Request, res: Response, next: NextFunction): void => {
    const result = schema.safeParse(req[field]);

    if (!result.success) {
      const details = result.error.errors.map((e) => ({
        field: e.path.join("."),
        message: e.message,
        code: e.code,
      }));

      res.status(400).json({
        error: "Validation failed",
        details,
      });
      return;
    }

    // Replace the raw value with the parsed (coerced / defaulted) value
    (req as unknown as Record<string, unknown>)[field] = result.data;
    next();
  };
}
