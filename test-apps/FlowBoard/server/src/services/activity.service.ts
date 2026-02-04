// =============================================================================
// Activity Service — creates activity log entries
// =============================================================================

import { prisma } from "../lib/prisma";
export interface CreateActivityInput {
  action: string;
  details?: Record<string, unknown>;
  taskId?: string | null;
  projectId?: string | null;
  actorId: string;
}

/**
 * Create a single activity entry.
 */
export async function createActivity(input: CreateActivityInput) {
  return prisma.activity.create({
    data: {
      action: input.action,
      details: input.details ? JSON.stringify(input.details) : null,
      taskId: input.taskId ?? undefined,
      projectId: input.projectId ?? undefined,
      actorId: input.actorId,
    },
    include: {
      actor: { select: { id: true, name: true, avatar: true } },
    },
  });
}

/**
 * Get activity for a specific task, ordered newest first.
 */
export async function getTaskActivity(taskId: string, limit = 20) {
  return prisma.activity.findMany({
    where: { taskId },
    orderBy: { createdAt: "desc" },
    take: limit,
    include: {
      actor: { select: { id: true, name: true, avatar: true } },
    },
  });
}

/**
 * Get activity for a specific project, ordered newest first.
 */
export async function getProjectActivity(projectId: string, limit = 50) {
  return prisma.activity.findMany({
    where: { projectId },
    orderBy: { createdAt: "desc" },
    take: limit,
    include: {
      actor: { select: { id: true, name: true, avatar: true } },
      task: { select: { id: true, title: true } },
    },
  });
}

/**
 * Get activity for a specific user (actor), ordered newest first.
 */
export async function getUserActivity(actorId: string, limit = 50) {
  return prisma.activity.findMany({
    where: { actorId },
    orderBy: { createdAt: "desc" },
    take: limit,
    include: {
      actor: { select: { id: true, name: true, avatar: true } },
      task: { select: { id: true, title: true } },
      project: { select: { id: true, name: true } },
    },
  });
}
