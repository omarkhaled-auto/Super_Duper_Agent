// =============================================================================
// Search Service — global search across tasks, projects, and users
// =============================================================================

import { prisma } from "../lib/prisma";

// -- Types --------------------------------------------------------------------

export interface SearchResults {
  tasks: Array<{
    id: string;
    title: string;
    description: string | null;
    status: string;
    priority: string;
    projectId: string;
    projectName: string;
    assignee: { id: string; name: string; avatar: string | null } | null;
  }>;
  projects: Array<{
    id: string;
    name: string;
    description: string | null;
    icon: string | null;
    color: string | null;
  }>;
  users: Array<{
    id: string;
    name: string;
    email: string;
    avatar: string | null;
  }>;
}

// -- Helpers ------------------------------------------------------------------

const RESULTS_PER_CATEGORY = 5;

// -- Service Functions --------------------------------------------------------

/**
 * Search across tasks, projects, and users.
 *
 * 1. Tasks: search title and description (ILIKE), only in projects the user has access to
 * 2. Projects: search name (ILIKE), only projects the user is a member of
 * 3. Users: search name and email (ILIKE)
 *
 * Returns grouped results limited to 5 per category.
 */
export async function searchAll(
  query: string,
  userId: string,
): Promise<SearchResults> {
  // Get project IDs the user has access to
  const userMemberships = await prisma.projectMember.findMany({
    where: { userId },
    select: { projectId: true },
  });
  const accessibleProjectIds = userMemberships.map((m) => m.projectId);

  // Run all three searches in parallel
  const [tasks, projects, users] = await Promise.all([
    // -- Search tasks --
    prisma.task.findMany({
      where: {
        projectId: { in: accessibleProjectIds },
        OR: [
          { title: { contains: query, mode: "insensitive" } },
          { description: { contains: query, mode: "insensitive" } },
        ],
      },
      select: {
        id: true,
        title: true,
        description: true,
        status: true,
        priority: true,
        projectId: true,
        project: {
          select: { name: true },
        },
        assignee: {
          select: { id: true, name: true, avatar: true },
        },
      },
      take: RESULTS_PER_CATEGORY,
      orderBy: { updatedAt: "desc" },
    }),

    // -- Search projects --
    prisma.project.findMany({
      where: {
        id: { in: accessibleProjectIds },
        archived: false,
        name: { contains: query, mode: "insensitive" },
      },
      select: {
        id: true,
        name: true,
        description: true,
        icon: true,
        color: true,
      },
      take: RESULTS_PER_CATEGORY,
      orderBy: { updatedAt: "desc" },
    }),

    // -- Search users --
    prisma.user.findMany({
      where: {
        OR: [
          { name: { contains: query, mode: "insensitive" } },
          { email: { contains: query, mode: "insensitive" } },
        ],
      },
      select: {
        id: true,
        name: true,
        email: true,
        avatar: true,
      },
      take: RESULTS_PER_CATEGORY,
      orderBy: { name: "asc" },
    }),
  ]);

  // Flatten task results to include projectName at top level
  const formattedTasks = tasks.map((task) => ({
    id: task.id,
    title: task.title,
    description: task.description,
    status: task.status,
    priority: task.priority,
    projectId: task.projectId,
    projectName: task.project.name,
    assignee: task.assignee,
  }));

  return {
    tasks: formattedTasks,
    projects,
    users,
  };
}
