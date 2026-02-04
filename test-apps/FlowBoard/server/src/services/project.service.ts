// =============================================================================
// Project Service — business logic for projects and membership
// =============================================================================

import { prisma } from "../lib/prisma";
type ProjectRole = string;
import { AppError } from "../middleware/error-handler";
import { createActivity } from "./activity.service";
import type {
  CreateProjectInput,
  UpdateProjectInput,
  AddMemberInput,
} from "../validators/project.validators";

// ── List Projects ───────────────────────────────────────────────────────────

/**
 * List all projects the user is a member of.
 * Includes member count and task count.
 */
export async function listProjects(userId: string) {
  const projects = await prisma.project.findMany({
    where: {
      members: { some: { userId } },
    },
    include: {
      _count: {
        select: { members: true, tasks: true },
      },
      members: {
        where: { userId },
        select: { role: true },
        take: 1,
      },
    },
    orderBy: { updatedAt: "desc" },
  });

  return projects.map((p) => ({
    id: p.id,
    name: p.name,
    description: p.description,
    icon: p.icon,
    color: p.color,
    archived: p.archived,
    createdAt: p.createdAt,
    updatedAt: p.updatedAt,
    memberCount: p._count.members,
    taskCount: p._count.tasks,
    myRole: p.members[0]?.role ?? null,
  }));
}

// ── Get Project ─────────────────────────────────────────────────────────────

/**
 * Get a single project by ID. Verifies the user is a member.
 * Includes members, labels, and task statistics.
 */
export async function getProject(id: string, userId: string) {
  const project = await prisma.project.findUnique({
    where: { id },
    include: {
      members: {
        include: {
          user: {
            select: { id: true, name: true, email: true, avatar: true },
          },
        },
        orderBy: { createdAt: "asc" },
      },
      labels: { orderBy: { name: "asc" } },
      _count: { select: { tasks: true, members: true } },
    },
  });

  if (!project) {
    throw new AppError(404, "Project not found");
  }

  // Verify membership
  const isMember = project.members.some((m) => m.userId === userId);
  if (!isMember) {
    throw new AppError(403, "You are not a member of this project");
  }

  return project;
}

// ── Create Project ──────────────────────────────────────────────────────────

/**
 * Create a new project and add the creator as ADMIN member.
 */
export async function createProject(input: CreateProjectInput, userId: string) {
  const project = await prisma.project.create({
    data: {
      name: input.name,
      description: input.description ?? null,
      icon: input.icon,
      color: input.color,
      members: {
        create: {
          userId,
          role: "ADMIN",
        },
      },
    },
    include: {
      members: {
        include: {
          user: {
            select: { id: true, name: true, email: true, avatar: true },
          },
        },
      },
      _count: { select: { members: true, tasks: true } },
    },
  });

  // Log activity
  await createActivity({
    action: "project.created",
    details: { projectName: project.name },
    projectId: project.id,
    actorId: userId,
  });

  return project;
}

// ── Update Project ──────────────────────────────────────────────────────────

/**
 * Update a project. Caller must already be verified as ADMIN via middleware.
 */
export async function updateProject(
  id: string,
  input: UpdateProjectInput,
  userId: string,
) {
  const project = await prisma.project.findUnique({ where: { id } });
  if (!project) {
    throw new AppError(404, "Project not found");
  }

  const updated = await prisma.project.update({
    where: { id },
    data: {
      ...(input.name !== undefined && { name: input.name }),
      ...(input.description !== undefined && { description: input.description }),
      ...(input.icon !== undefined && { icon: input.icon }),
      ...(input.color !== undefined && { color: input.color }),
    },
    include: {
      members: {
        include: {
          user: {
            select: { id: true, name: true, email: true, avatar: true },
          },
        },
      },
      _count: { select: { members: true, tasks: true } },
    },
  });

  // Log activity
  await createActivity({
    action: "project.updated",
    details: { changes: input },
    projectId: id,
    actorId: userId,
  });

  return updated;
}

// ── Toggle Archive ──────────────────────────────────────────────────────────

/**
 * Toggle the archived status of a project.
 */
export async function toggleArchive(id: string, userId: string) {
  const project = await prisma.project.findUnique({ where: { id } });
  if (!project) {
    throw new AppError(404, "Project not found");
  }

  const updated = await prisma.project.update({
    where: { id },
    data: { archived: !project.archived },
  });

  await createActivity({
    action: updated.archived ? "project.archived" : "project.unarchived",
    projectId: id,
    actorId: userId,
  });

  return updated;
}

// ── Add Member ──────────────────────────────────────────────────────────────

/**
 * Add a member to a project by email. The inviting user must be ADMIN.
 */
export async function addMember(
  projectId: string,
  input: AddMemberInput,
  actorId: string,
) {
  // Find the user by email
  const targetUser = await prisma.user.findUnique({
    where: { email: input.email },
    select: { id: true, name: true, email: true },
  });

  if (!targetUser) {
    throw new AppError(404, "No user found with that email address");
  }

  // Check if already a member
  const existing = await prisma.projectMember.findUnique({
    where: {
      userId_projectId: { userId: targetUser.id, projectId },
    },
  });

  if (existing) {
    throw new AppError(409, "User is already a member of this project");
  }

  const membership = await prisma.projectMember.create({
    data: {
      userId: targetUser.id,
      projectId,
      role: input.role,
    },
    include: {
      user: {
        select: { id: true, name: true, email: true, avatar: true },
      },
    },
  });

  await createActivity({
    action: "member.added",
    details: {
      memberName: targetUser.name,
      memberEmail: targetUser.email,
      role: input.role,
    },
    projectId,
    actorId,
  });

  return membership;
}

// ── Update Member Role ──────────────────────────────────────────────────────

/**
 * Update a member's role within a project.
 */
export async function updateMemberRole(
  projectId: string,
  targetUserId: string,
  role: ProjectRole,
  actorId: string,
) {
  const membership = await prisma.projectMember.findUnique({
    where: {
      userId_projectId: { userId: targetUserId, projectId },
    },
    include: {
      user: { select: { id: true, name: true } },
    },
  });

  if (!membership) {
    throw new AppError(404, "Member not found in this project");
  }

  // Prevent demoting yourself from ADMIN if you are the last admin
  if (targetUserId === actorId && membership.role === "ADMIN" && role !== "ADMIN") {
    const adminCount = await prisma.projectMember.count({
      where: { projectId, role: "ADMIN" },
    });
    if (adminCount <= 1) {
      throw new AppError(
        400,
        "Cannot change your role: you are the only admin",
      );
    }
  }

  const updated = await prisma.projectMember.update({
    where: {
      userId_projectId: { userId: targetUserId, projectId },
    },
    data: { role },
    include: {
      user: {
        select: { id: true, name: true, email: true, avatar: true },
      },
    },
  });

  await createActivity({
    action: "member.role_updated",
    details: {
      memberName: membership.user.name,
      oldRole: membership.role,
      newRole: role,
    },
    projectId,
    actorId,
  });

  return updated;
}

// ── Remove Member ───────────────────────────────────────────────────────────

/**
 * Remove a member from a project.
 */
export async function removeMember(
  projectId: string,
  targetUserId: string,
  actorId: string,
) {
  const membership = await prisma.projectMember.findUnique({
    where: {
      userId_projectId: { userId: targetUserId, projectId },
    },
    include: {
      user: { select: { id: true, name: true } },
    },
  });

  if (!membership) {
    throw new AppError(404, "Member not found in this project");
  }

  // Prevent removing yourself if you are the only admin
  if (targetUserId === actorId) {
    if (membership.role === "ADMIN") {
      const adminCount = await prisma.projectMember.count({
        where: { projectId, role: "ADMIN" },
      });
      if (adminCount <= 1) {
        throw new AppError(
          400,
          "Cannot remove yourself: you are the only admin",
        );
      }
    }
  }

  await prisma.projectMember.delete({
    where: {
      userId_projectId: { userId: targetUserId, projectId },
    },
  });

  await createActivity({
    action: "member.removed",
    details: { memberName: membership.user.name },
    projectId,
    actorId,
  });

  return { removed: true };
}

// ── List Members ────────────────────────────────────────────────────────────

/**
 * List all members of a project with user details.
 */
export async function listMembers(projectId: string) {
  return prisma.projectMember.findMany({
    where: { projectId },
    include: {
      user: {
        select: { id: true, name: true, email: true, avatar: true },
      },
    },
    orderBy: { createdAt: "asc" },
  });
}

// ── Labels ──────────────────────────────────────────────────────────────────

/**
 * Create a new label for a project.
 */
export async function createLabel(
  projectId: string,
  name: string,
  color: string,
  actorId: string,
) {
  // Check for duplicate name
  const existing = await prisma.label.findUnique({
    where: { name_projectId: { name, projectId } },
  });

  if (existing) {
    throw new AppError(409, "A label with that name already exists in this project");
  }

  const label = await prisma.label.create({
    data: { name, color, projectId },
  });

  await createActivity({
    action: "label.created",
    details: { labelName: name, color },
    projectId,
    actorId,
  });

  return label;
}

/**
 * List all labels for a project.
 */
export async function listLabels(projectId: string) {
  return prisma.label.findMany({
    where: { projectId },
    orderBy: { name: "asc" },
  });
}
