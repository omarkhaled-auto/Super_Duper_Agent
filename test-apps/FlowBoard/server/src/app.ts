// =============================================================================
// FlowBoard Server — Express Application
//
// This module creates and configures the Express app without starting a server.
// Exported separately so tests can use supertest without calling server.listen().
// The main entry point (index.ts) imports this and attaches it to an HTTP server.
// =============================================================================

import express, { Request, Response } from "express";
import cors from "cors";
import cookieParser from "cookie-parser";
import { errorHandler } from "./middleware/error-handler";
import { notFoundHandler } from "./middleware/not-found";
import authRoutes from "./routes/auth.routes";
import userRoutes from "./routes/user.routes";
import projectRoutes from "./routes/project.routes";
import taskRoutes, { projectTaskRouter } from "./routes/task.routes";
import commentRoutes from "./routes/comment.routes";
import activityRoutes from "./routes/activity.routes";
import labelRoutes from "./routes/label.routes";
import subtaskRoutes from "./routes/subtask.routes";
import searchRoutes from "./routes/search.routes";
import analyticsRoutes from "./routes/analytics.routes";

// ---------------------------------------------------------------------------
// Environment
// ---------------------------------------------------------------------------
const CLIENT_URL = process.env.CLIENT_URL ?? "http://localhost:3000";

// ---------------------------------------------------------------------------
// Express Application
// ---------------------------------------------------------------------------
const app = express();

// -- CORS -------------------------------------------------------------------
app.use(
  cors({
    origin: CLIENT_URL,
    credentials: true,
  }),
);

// -- Body Parsing -----------------------------------------------------------
app.use(express.json({ limit: "1mb" }));
app.use(express.urlencoded({ extended: true }));

// -- Cookie Parser ----------------------------------------------------------
app.use(cookieParser());

// ---------------------------------------------------------------------------
// Health Check
// ---------------------------------------------------------------------------
app.get("/api/health", (_req: Request, res: Response) => {
  res.json({
    status: "ok",
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
  });
});

// ---------------------------------------------------------------------------
// API Routes
// ---------------------------------------------------------------------------
app.use("/api/auth", authRoutes);
app.use("/api/users", userRoutes);
app.use("/api/projects", projectRoutes);
app.use("/api/projects/:projectId/tasks", projectTaskRouter);
app.use("/api/tasks", taskRoutes);
app.use("/api/subtasks", subtaskRoutes);
app.use("/api/comments", commentRoutes);
app.use("/api/activity", activityRoutes);
app.use("/api/labels", labelRoutes);
app.use("/api/search", searchRoutes);
app.use("/api/analytics", analyticsRoutes);

// ---------------------------------------------------------------------------
// 404 handler — must come after all route registrations
// ---------------------------------------------------------------------------
app.use(notFoundHandler);

// ---------------------------------------------------------------------------
// Global Error Handler — must be the very last middleware
// ---------------------------------------------------------------------------
app.use(errorHandler);

export default app;
