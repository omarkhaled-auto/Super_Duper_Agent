// =============================================================================
// Task Service — business logic for task CRUD and movement
// =============================================================================

import { prisma } from "../lib/prisma";
import { Prisma } from "@prisma/client";
import { AppError } from "../middleware/error-handler";
import { createActivity } from "./activity.service";
import type {
  CreateTaskInput,
  UpdateTaskInput,
  ReorderTaskInput,
  BulkActionInput,
  ListTasksQuery,
  CreateSubtaskInput,
  UpdateSubtaskInput,
} from "../validators/task.validators";

// ── List Tasks ──────────────────────────────────────────────────────────────

/**
 * List tasks for a project with filtering, sorting, and pagination.
 */
export async function listTasks(
  projectId: string,
  query: ListTasksQuery,
) {
  const {
    status,
    priority,
    assigneeId,
    search,
    sortBy,
    sortOrder,
    page,
    limit,
  } = query;

  const where: Prisma.TaskWhereInput = { projectId };

  if (status) where.status = status;
  if (priority) where.priority = priority;
  if (assigneeId) where.assigneeId = assigneeId;
  if (search) {
    where.OR = [
      { title: { contains: search, mode: "insensitive" } },
      { description: { contains: search, mode: "insensitive" } },
    ];
  }

  const skip = (page - 1) * limit;

  const [tasks, total] = await Promise.all([
    prisma.task.findMany({
      where,
      include: {
        assignee: {
          select: { id: true, name: true, avatar: true },
        },
        labels: {
          include: {
            label: { select: { id: true, name: true, color: true } },
          },
        },
        _count: { select: { subTasks: true, comments: true } },
      },
      orderBy: { [sortBy]: sortOrder },
      skip,
      take: limit,
    }),
    prisma.task.count({ where }),
  ]);

  // Flatten labels for the response
  const formattedTasks = tasks.map((t) => ({
    ...t,
    labels: t.labels.map((tl) => tl.label),
  }));

  return {
    tasks: formattedTasks,
    total,
    page,
    limit,
    totalPages: Math.ceil(total / limit),
  };
}

// ── Get Task ────────────────────────────────────────────────────────────────

/**
 * Get a single task with subtasks, labels, comments (last 10), and activity (last 20).
 */
export async function getTask(id: string) {
  const task = await prisma.task.findUnique({
    where: { id },
    include: {
      assignee: {
        select: { id: true, name: true, email: true, avatar: true },
      },
      creator: {
        select: { id: true, name: true, email: true, avatar: true },
      },
      subTasks: {
        orderBy: { position: "asc" },
      },
      labels: {
        include: {
          label: { select: { id: true, name: true, color: true } },
        },
      },
      comments: {
        orderBy: { createdAt: "desc" },
        take: 10,
        include: {
          author: {
            select: { id: true, name: true, avatar: true },
          },
        },
      },
      activities: {
        orderBy: { createdAt: "desc" },
        take: 20,
        include: {
          actor: {
            select: { id: true, name: true, avatar: true },
          },
        },
      },
    },
  });

  if (!task) {
    throw new AppError(404, "Task not found");
  }

  // Flatten labels
  return {
    ...task,
    labels: task.labels.map((tl) => tl.label),
  };
}

// ── Create Task ─────────────────────────────────────────────────────────────

/**
 * Create a new task. Automatically sets position to be last in the column.
 */
export async function createTask(
  projectId: string,
  input: CreateTaskInput,
  userId: string,
) {
  // Verify project exists
  const project = await prisma.project.findUnique({
    where: { id: projectId },
    select: { id: true, name: true },
  });
  if (!project) {
    throw new AppError(404, "Project not found");
  }

  // Calculate position: last in the status column
  const lastTask = await prisma.task.findFirst({
    where: { projectId, status: input.status },
    orderBy: { position: "desc" },
    select: { position: true },
  });
  const position = (lastTask?.position ?? -1) + 1;

  const task = await prisma.task.create({
    data: {
      title: input.title,
      description: input.description ?? null,
      status: input.status,
      priority: input.priority,
      position,
      projectId,
      creatorId: userId,
      assigneeId: input.assigneeId ?? null,
      dueDate: input.dueDate ?? null,
      ...(input.labelIds && input.labelIds.length > 0
        ? {
            labels: {
              create: input.labelIds.map((labelId) => ({ labelId })),
            },
          }
        : {}),
    },
    include: {
      assignee: {
        select: { id: true, name: true, avatar: true },
      },
      creator: {
        select: { id: true, name: true, avatar: true },
      },
      labels: {
        include: {
          label: { select: { id: true, name: true, color: true } },
        },
      },
      _count: { select: { subTasks: true, comments: true } },
    },
  });

  // Log activity
  await createActivity({
    action: "task.created",
    details: { title: task.title, status: task.status },
    taskId: task.id,
    projectId,
    actorId: userId,
  });

  return {
    ...task,
    labels: task.labels.map((tl) => tl.label),
  };
}

// ── Update Task ─────────────────────────────────────────────────────────────

/**
 * Update task fields. Creates activity entries for each changed field.
 */
export async function updateTask(
  id: string,
  input: UpdateTaskInput,
  userId: string,
) {
  const existing = await prisma.task.findUnique({
    where: { id },
    include: {
      labels: { select: { labelId: true } },
    },
  });
  if (!existing) {
    throw new AppError(404, "Task not found");
  }

  // Build the data object, excluding labelIds which are handled separately
  const { labelIds, ...fields } = input;

  // Build update data carefully, only including defined fields
  const updateData: Prisma.TaskUpdateInput = {};
  if (fields.title !== undefined) updateData.title = fields.title;
  if (fields.description !== undefined) updateData.description = fields.description;
  if (fields.status !== undefined) updateData.status = fields.status;
  if (fields.priority !== undefined) updateData.priority = fields.priority;
  if (fields.dueDate !== undefined) updateData.dueDate = fields.dueDate;
  if (fields.assigneeId !== undefined) {
    if (fields.assigneeId === null) {
      updateData.assignee = { disconnect: true };
    } else {
      updateData.assignee = { connect: { id: fields.assigneeId } };
    }
  }

  // Update labels if provided
  if (labelIds !== undefined) {
    // Delete existing labels and recreate
    await prisma.taskLabel.deleteMany({ where: { taskId: id } });
    if (labelIds.length > 0) {
      await prisma.taskLabel.createMany({
        data: labelIds.map((labelId) => ({ taskId: id, labelId })),
      });
    }
  }

  const updated = await prisma.task.update({
    where: { id },
    data: updateData,
    include: {
      assignee: {
        select: { id: true, name: true, email: true, avatar: true },
      },
      creator: {
        select: { id: true, name: true, email: true, avatar: true },
      },
      labels: {
        include: {
          label: { select: { id: true, name: true, color: true } },
        },
      },
      _count: { select: { subTasks: true, comments: true } },
    },
  });

  // Build change details for activity log
  const changes: Record<string, { from: unknown; to: unknown }> = {};
  if (fields.title !== undefined && fields.title !== existing.title) {
    changes.title = { from: existing.title, to: fields.title };
  }
  if (fields.status !== undefined && fields.status !== existing.status) {
    changes.status = { from: existing.status, to: fields.status };
  }
  if (fields.priority !== undefined && fields.priority !== existing.priority) {
    changes.priority = { from: existing.priority, to: fields.priority };
  }
  if (fields.assigneeId !== undefined && fields.assigneeId !== existing.assigneeId) {
    changes.assignee = { from: existing.assigneeId, to: fields.assigneeId };
  }
  if (fields.description !== undefined && fields.description !== existing.description) {
    changes.description = { from: "(previous)", to: "(updated)" };
  }

  if (Object.keys(changes).length > 0) {
    await createActivity({
      action: "task.updated",
      details: { changes },
      taskId: id,
      projectId: existing.projectId,
      actorId: userId,
    });
  }

  return {
    ...updated,
    labels: updated.labels.map((tl) => tl.label),
  };
}

// ── Delete Task ─────────────────────────────────────────────────────────────

/**
 * Delete a task. Cascades to subtasks, comments, labels via schema.
 */
export async function deleteTask(id: string, userId: string) {
  const task = await prisma.task.findUnique({
    where: { id },
    select: { id: true, title: true, projectId: true },
  });
  if (!task) {
    throw new AppError(404, "Task not found");
  }

  // Log activity before deletion (since taskId will be set null on cascade)
  await createActivity({
    action: "task.deleted",
    details: { title: task.title },
    projectId: task.projectId,
    actorId: userId,
  });

  await prisma.task.delete({ where: { id } });

  return { deleted: true };
}

// ── Reorder Task (Kanban drag-and-drop) ─────────────────────────────────────

/**
 * Move a task to a new status column and/or position.
 * Updates positions of all affected tasks in source and target columns.
 */
export async function reorderTask(
  id: string,
  input: ReorderTaskInput,
  userId: string,
) {
  const task = await prisma.task.findUnique({
    where: { id },
    select: {
      id: true,
      title: true,
      status: true,
      position: true,
      projectId: true,
    },
  });
  if (!task) {
    throw new AppError(404, "Task not found");
  }

  const oldStatus = task.status;
  const newStatus = input.status;
  const newPosition = input.position;

  await prisma.$transaction(async (tx) => {
    if (oldStatus === newStatus) {
      // Same column reorder
      const oldPos = task.position;
      if (newPosition > oldPos) {
        // Moving down: shift items between old+1 and new up by 1
        await tx.task.updateMany({
          where: {
            projectId: task.projectId,
            status: newStatus,
            position: { gt: oldPos, lte: newPosition },
            id: { not: id },
          },
          data: { position: { decrement: 1 } },
        });
      } else if (newPosition < oldPos) {
        // Moving up: shift items between new and old-1 down by 1
        await tx.task.updateMany({
          where: {
            projectId: task.projectId,
            status: newStatus,
            position: { gte: newPosition, lt: oldPos },
            id: { not: id },
          },
          data: { position: { increment: 1 } },
        });
      }
    } else {
      // Cross-column move
      // Close the gap in old column
      await tx.task.updateMany({
        where: {
          projectId: task.projectId,
          status: oldStatus,
          position: { gt: task.position },
        },
        data: { position: { decrement: 1 } },
      });

      // Make space in new column
      await tx.task.updateMany({
        where: {
          projectId: task.projectId,
          status: newStatus,
          position: { gte: newPosition },
        },
        data: { position: { increment: 1 } },
      });
    }

    // Update the task itself
    await tx.task.update({
      where: { id },
      data: { status: newStatus, position: newPosition },
    });
  });

  // Re-fetch the updated task
  const updated = await prisma.task.findUnique({
    where: { id },
    include: {
      assignee: { select: { id: true, name: true, avatar: true } },
      labels: {
        include: {
          label: { select: { id: true, name: true, color: true } },
        },
      },
      _count: { select: { subTasks: true, comments: true } },
    },
  });

  // Activity log
  if (oldStatus !== newStatus) {
    await createActivity({
      action: "task.moved",
      details: { from: oldStatus, to: newStatus },
      taskId: id,
      projectId: task.projectId,
      actorId: userId,
    });
  }

  return updated
    ? {
        ...updated,
        labels: updated.labels.map((tl) => tl.label),
      }
    : null;
}

// ── Bulk Action ─────────────────────────────────────────────────────────────

/**
 * Perform bulk actions on multiple tasks.
 */
export async function bulkAction(input: BulkActionInput, userId: string) {
  const { taskIds, action, data } = input;

  // Verify all tasks exist and get their project IDs
  const tasks = await prisma.task.findMany({
    where: { id: { in: taskIds } },
    select: { id: true, title: true, projectId: true, status: true, priority: true },
  });

  if (tasks.length !== taskIds.length) {
    throw new AppError(404, "One or more tasks not found");
  }

  const projectId = tasks[0]?.projectId;

  switch (action) {
    case "updateStatus": {
      if (!data?.status) {
        throw new AppError(400, "Status is required for updateStatus action");
      }
      await prisma.task.updateMany({
        where: { id: { in: taskIds } },
        data: { status: data.status },
      });
      await createActivity({
        action: "task.bulk_status_update",
        details: {
          taskCount: taskIds.length,
          newStatus: data.status,
        },
        projectId,
        actorId: userId,
      });
      break;
    }

    case "updatePriority": {
      if (!data?.priority) {
        throw new AppError(400, "Priority is required for updatePriority action");
      }
      await prisma.task.updateMany({
        where: { id: { in: taskIds } },
        data: { priority: data.priority },
      });
      await createActivity({
        action: "task.bulk_priority_update",
        details: {
          taskCount: taskIds.length,
          newPriority: data.priority,
        },
        projectId,
        actorId: userId,
      });
      break;
    }

    case "updateAssignee": {
      if (data?.assigneeId === undefined) {
        throw new AppError(
          400,
          "assigneeId is required for updateAssignee action",
        );
      }
      await prisma.task.updateMany({
        where: { id: { in: taskIds } },
        data: { assigneeId: data.assigneeId },
      });
      await createActivity({
        action: "task.bulk_assignee_update",
        details: {
          taskCount: taskIds.length,
          assigneeId: data.assigneeId,
        },
        projectId,
        actorId: userId,
      });
      break;
    }

    case "delete": {
      // Log before deleting
      await createActivity({
        action: "task.bulk_delete",
        details: {
          taskCount: taskIds.length,
          titles: tasks.map((t) => t.title),
        },
        projectId,
        actorId: userId,
      });
      await prisma.task.deleteMany({
        where: { id: { in: taskIds } },
      });
      break;
    }

    default:
      throw new AppError(400, `Unknown bulk action: ${action}`);
  }

  return { success: true, affected: taskIds.length };
}

// ── Subtask CRUD ────────────────────────────────────────────────────────────

/**
 * Create a subtask for a task.
 */
export async function createSubtask(
  taskId: string,
  input: CreateSubtaskInput,
  userId: string,
) {
  const task = await prisma.task.findUnique({
    where: { id: taskId },
    select: { id: true, projectId: true },
  });
  if (!task) {
    throw new AppError(404, "Task not found");
  }

  // Calculate position
  const lastSubtask = await prisma.subTask.findFirst({
    where: { taskId },
    orderBy: { position: "desc" },
    select: { position: true },
  });
  const position = (lastSubtask?.position ?? -1) + 1;

  const subtask = await prisma.subTask.create({
    data: {
      title: input.title,
      taskId,
      position,
    },
  });

  await createActivity({
    action: "subtask.created",
    details: { subtaskTitle: input.title },
    taskId,
    projectId: task.projectId,
    actorId: userId,
  });

  return subtask;
}

/**
 * Update a subtask.
 */
export async function updateSubtask(
  subtaskId: string,
  input: UpdateSubtaskInput,
  userId: string,
) {
  const subtask = await prisma.subTask.findUnique({
    where: { id: subtaskId },
    include: {
      task: { select: { id: true, projectId: true } },
    },
  });
  if (!subtask) {
    throw new AppError(404, "Subtask not found");
  }

  const updated = await prisma.subTask.update({
    where: { id: subtaskId },
    data: {
      ...(input.title !== undefined && { title: input.title }),
      ...(input.completed !== undefined && { completed: input.completed }),
    },
  });

  const action =
    input.completed !== undefined
      ? input.completed
        ? "subtask.completed"
        : "subtask.uncompleted"
      : "subtask.updated";

  await createActivity({
    action,
    details: { subtaskTitle: updated.title },
    taskId: subtask.taskId,
    projectId: subtask.task.projectId,
    actorId: userId,
  });

  return updated;
}

/**
 * Delete a subtask.
 */
export async function deleteSubtask(subtaskId: string, userId: string) {
  const subtask = await prisma.subTask.findUnique({
    where: { id: subtaskId },
    include: {
      task: { select: { id: true, projectId: true } },
    },
  });
  if (!subtask) {
    throw new AppError(404, "Subtask not found");
  }

  await prisma.subTask.delete({ where: { id: subtaskId } });

  await createActivity({
    action: "subtask.deleted",
    details: { subtaskTitle: subtask.title },
    taskId: subtask.taskId,
    projectId: subtask.task.projectId,
    actorId: userId,
  });

  return { deleted: true };
}

// ── Set Task Labels ─────────────────────────────────────────────────────────

/**
 * Replace all labels on a task with a new set.
 */
export async function setTaskLabels(
  taskId: string,
  labelIds: string[],
  userId: string,
) {
  const task = await prisma.task.findUnique({
    where: { id: taskId },
    select: { id: true, projectId: true },
  });
  if (!task) {
    throw new AppError(404, "Task not found");
  }

  // Delete all existing labels for the task, then create new ones
  await prisma.$transaction(async (tx) => {
    await tx.taskLabel.deleteMany({ where: { taskId } });
    if (labelIds.length > 0) {
      await tx.taskLabel.createMany({
        data: labelIds.map((labelId) => ({ taskId, labelId })),
      });
    }
  });

  // Re-fetch to return the updated labels
  const updatedTask = await prisma.task.findUnique({
    where: { id: taskId },
    include: {
      labels: {
        include: {
          label: { select: { id: true, name: true, color: true } },
        },
      },
    },
  });

  await createActivity({
    action: "task.labels_updated",
    details: { labelIds },
    taskId,
    projectId: task.projectId,
    actorId: userId,
  });

  return updatedTask
    ? {
        ...updatedTask,
        labels: updatedTask.labels.map((tl) => tl.label),
      }
    : null;
}

// ── Comments ────────────────────────────────────────────────────────────────

/**
 * Create a comment on a task.
 */
export async function createComment(
  taskId: string,
  content: string,
  userId: string,
) {
  const task = await prisma.task.findUnique({
    where: { id: taskId },
    select: { id: true, projectId: true },
  });
  if (!task) {
    throw new AppError(404, "Task not found");
  }

  const comment = await prisma.comment.create({
    data: {
      content,
      taskId,
      authorId: userId,
    },
    include: {
      author: {
        select: { id: true, name: true, avatar: true },
      },
    },
  });

  await createActivity({
    action: "comment.created",
    details: { commentPreview: content.slice(0, 100) },
    taskId,
    projectId: task.projectId,
    actorId: userId,
  });

  return comment;
}

/**
 * List comments on a task, ordered newest first.
 */
export async function listComments(taskId: string) {
  return prisma.comment.findMany({
    where: { taskId },
    include: {
      author: {
        select: { id: true, name: true, email: true, avatar: true },
      },
    },
    orderBy: { createdAt: "desc" },
  });
}

/**
 * Delete a comment. Only the author may delete their own comment.
 */
export async function deleteComment(commentId: string, userId: string) {
  const comment = await prisma.comment.findUnique({
    where: { id: commentId },
    include: {
      task: { select: { id: true, projectId: true } },
    },
  });
  if (!comment) {
    throw new AppError(404, "Comment not found");
  }

  if (comment.authorId !== userId) {
    throw new AppError(403, "You can only delete your own comments");
  }

  await prisma.comment.delete({ where: { id: commentId } });

  await createActivity({
    action: "comment.deleted",
    taskId: comment.taskId,
    projectId: comment.task.projectId,
    actorId: userId,
  });

  return { deleted: true };
}
