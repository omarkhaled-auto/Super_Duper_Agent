// =============================================================================
// Global Error Handler Middleware
//
// Catches all errors thrown in route handlers / middleware and returns a
// consistent JSON shape: { error: string, details?: any }
// =============================================================================

import { Request, Response, NextFunction } from "express";
import { ZodError } from "zod";

/**
 * Custom application error with an HTTP status code.
 * Throw this from any route / service to return a known error response.
 */
export class AppError extends Error {
  constructor(
    public statusCode: number,
    message: string,
  ) {
    super(message);
    this.name = "AppError";
  }
}

/**
 * Express error-handling middleware (4 arguments).
 * Must be registered LAST via `app.use(errorHandler)`.
 */
export function errorHandler(
  err: Error,
  _req: Request,
  res: Response,
  _next: NextFunction,
): void {
  // -- Development logging --------------------------------------------------
  if (process.env.NODE_ENV !== "production") {
    console.error("[Error Handler]", err);
  }

  // -- Known application error ----------------------------------------------
  if (err instanceof AppError) {
    res.status(err.statusCode).json({ error: err.message });
    return;
  }

  // -- Zod validation error — format nicely ---------------------------------
  if (err instanceof ZodError) {
    const details = err.errors.map((e) => ({
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

  // -- Fallback: unexpected / unknown error ---------------------------------
  res.status(500).json({
    error:
      process.env.NODE_ENV === "production"
        ? "Internal server error"
        : err.message || "Internal server error",
  });
}
