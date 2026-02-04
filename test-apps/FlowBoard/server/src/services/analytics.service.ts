// =============================================================================
// Analytics Service — project analytics with Prisma groupBy/aggregate queries
// =============================================================================

import { prisma } from "../lib/prisma";

// -- Types --------------------------------------------------------------------

export interface TasksOverTimeEntry {
  date: string;
  count: number;
}

export interface TasksByStatusEntry {
  status: string;
  count: number;
}

export interface TasksByPriorityEntry {
  priority: string;
  count: number;
}

export interface VelocityEntry {
  week: string;
  count: number;
}

export interface ProjectAnalytics {
  tasksOverTime: TasksOverTimeEntry[];
  tasksByStatus: TasksByStatusEntry[];
  tasksByPriority: TasksByPriorityEntry[];
  velocity: VelocityEntry[];
}

// -- Helpers ------------------------------------------------------------------

/**
 * Get the start of day for a given date in ISO string format (YYYY-MM-DD).
 */
function formatDateKey(date: Date): string {
  return date.toISOString().split("T")[0] ?? "";
}

/**
 * Get the ISO week string (YYYY-Www) for a given date.
 */
function getWeekKey(date: Date): string {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  // Set to nearest Thursday (current date + 4 - current day number, making Sunday = 7)
  d.setDate(d.getDate() + 4 - (d.getDay() || 7));
  const yearStart = new Date(d.getFullYear(), 0, 1);
  const weekNumber = Math.ceil(
    ((d.getTime() - yearStart.getTime()) / 86400000 + 1) / 7,
  );
  return `${d.getFullYear()}-W${String(weekNumber).padStart(2, "0")}`;
}

// -- Service Functions --------------------------------------------------------

/**
 * Compute all analytics data for a project.
 *
 * - tasksOverTime: completed tasks per day over the last 30 days
 * - tasksByStatus: task count grouped by status
 * - tasksByPriority: task count grouped by priority
 * - velocity: completed tasks per week over the last 8 weeks
 */
export async function getProjectAnalytics(
  projectId: string,
): Promise<ProjectAnalytics> {
  const now = new Date();
  const thirtyDaysAgo = new Date(now);
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

  const eightWeeksAgo = new Date(now);
  eightWeeksAgo.setDate(eightWeeksAgo.getDate() - 56); // 8 weeks = 56 days

  // Run all queries in parallel for performance
  const [tasksByStatus, tasksByPriority, completedTasksLast30, completedTasksLast8Weeks] =
    await Promise.all([
      // -- Tasks by status (groupBy) --
      prisma.task.groupBy({
        by: ["status"],
        where: { projectId },
        _count: { id: true },
      }),

      // -- Tasks by priority (groupBy) --
      prisma.task.groupBy({
        by: ["priority"],
        where: { projectId },
        _count: { id: true },
      }),

      // -- Completed tasks in last 30 days (for tasksOverTime) --
      prisma.task.findMany({
        where: {
          projectId,
          status: "DONE",
          updatedAt: { gte: thirtyDaysAgo },
        },
        select: { updatedAt: true },
        orderBy: { updatedAt: "asc" },
      }),

      // -- Completed tasks in last 8 weeks (for velocity) --
      prisma.task.findMany({
        where: {
          projectId,
          status: "DONE",
          updatedAt: { gte: eightWeeksAgo },
        },
        select: { updatedAt: true },
        orderBy: { updatedAt: "asc" },
      }),
    ]);

  // -- Format tasksByStatus --
  const formattedStatus: TasksByStatusEntry[] = tasksByStatus.map((entry) => ({
    status: entry.status,
    count: entry._count.id,
  }));

  // -- Format tasksByPriority --
  const formattedPriority: TasksByPriorityEntry[] = tasksByPriority.map(
    (entry) => ({
      priority: entry.priority,
      count: entry._count.id,
    }),
  );

  // -- Compute tasksOverTime (group completed tasks by date) --
  const dailyCounts = new Map<string, number>();

  // Initialize all 30 days with 0
  for (let i = 30; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    dailyCounts.set(formatDateKey(d), 0);
  }

  // Count completed tasks per day
  for (const task of completedTasksLast30) {
    const key = formatDateKey(task.updatedAt);
    if (dailyCounts.has(key)) {
      dailyCounts.set(key, (dailyCounts.get(key) ?? 0) + 1);
    }
  }

  const tasksOverTime: TasksOverTimeEntry[] = Array.from(
    dailyCounts.entries(),
  ).map(([date, count]) => ({ date, count }));

  // -- Compute velocity (group completed tasks by week) --
  const weeklyCounts = new Map<string, number>();

  // Initialize last 8 weeks with 0
  for (let i = 7; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i * 7);
    const weekKey = getWeekKey(d);
    if (!weeklyCounts.has(weekKey)) {
      weeklyCounts.set(weekKey, 0);
    }
  }

  // Count completed tasks per week
  for (const task of completedTasksLast8Weeks) {
    const weekKey = getWeekKey(task.updatedAt);
    if (weeklyCounts.has(weekKey)) {
      weeklyCounts.set(weekKey, (weeklyCounts.get(weekKey) ?? 0) + 1);
    }
  }

  const velocity: VelocityEntry[] = Array.from(weeklyCounts.entries()).map(
    ([week, count]) => ({ week, count }),
  );

  return {
    tasksOverTime,
    tasksByStatus: formattedStatus,
    tasksByPriority: formattedPriority,
    velocity,
  };
}
