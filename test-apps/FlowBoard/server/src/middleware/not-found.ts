// =============================================================================
// 404 Handler — catches any request that didn't match a route
// =============================================================================

import { Request, Response } from "express";

export function notFoundHandler(_req: Request, res: Response): void {
  res.status(404).json({ message: "Route not found" });
}
