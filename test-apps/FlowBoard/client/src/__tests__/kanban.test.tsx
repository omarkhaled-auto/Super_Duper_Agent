import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { KanbanBoard } from "@/components/board/kanban-board";
import type { ColumnMap } from "@/hooks/use-board";

// =============================================================================
// Mock: AddTaskInline — the inline task creation widget at the bottom of each
// column. We stub it out since it has its own API integration.
// =============================================================================
vi.mock("@/components/board/add-task-inline", () => ({
  AddTaskInline: () => <div data-testid="add-task-inline" />,
}));

// =============================================================================
// Fixtures: realistic task data matching the shared Task interface
// =============================================================================
function makeTask(overrides: Record<string, unknown> = {}) {
  return {
    id: "task-1",
    title: "Implement dark mode",
    description: null,
    status: "TODO",
    priority: "HIGH",
    position: 0,
    dueDate: null,
    createdAt: "2024-01-15T10:00:00Z",
    updatedAt: "2024-01-15T10:00:00Z",
    projectId: "proj-1",
    creatorId: "user-1",
    assigneeId: "user-2",
    assignee: {
      id: "user-2",
      name: "Alice Johnson",
      email: "alice@flowboard.io",
      avatarUrl: null,
    },
    creator: {
      id: "user-1",
      name: "Omar Khaled",
      email: "omar@flowboard.io",
      avatarUrl: null,
    },
    labels: [],
    subtasks: [],
    subtaskTotal: 0,
    subtaskCompleted: 0,
    ...overrides,
  };
}

// =============================================================================
// Helpers
// =============================================================================

/** Build a ColumnMap with empty arrays for all five statuses. */
function emptyColumns(): ColumnMap {
  return {
    BACKLOG: [],
    TODO: [],
    IN_PROGRESS: [],
    IN_REVIEW: [],
    DONE: [],
  };
}

describe("KanbanBoard", () => {
  const mockMoveTask = vi.fn().mockResolvedValue(undefined);
  const mockAddTask = vi.fn();
  const mockUpdateTask = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ---------------------------------------------------------------------------
  // Test 1: Renders all 5 status columns with correct headers
  // ---------------------------------------------------------------------------
  it("renders all five status columns with header labels and task counts", () => {
    const columns: ColumnMap = {
      ...emptyColumns(),
      TODO: [makeTask({ id: "t-1", title: "Task A" }), makeTask({ id: "t-2", title: "Task B" })],
      IN_PROGRESS: [makeTask({ id: "t-3", title: "Task C", status: "IN_PROGRESS" })],
    };

    render(
      <KanbanBoard
        columns={columns}
        projectId="proj-1"
        moveTask={mockMoveTask}
        addTask={mockAddTask}
        updateTask={mockUpdateTask}
      />,
    );

    // All five column labels should be visible
    expect(screen.getByText("Backlog")).toBeInTheDocument();
    expect(screen.getByText("To Do")).toBeInTheDocument();
    expect(screen.getByText("In Progress")).toBeInTheDocument();
    expect(screen.getByText("In Review")).toBeInTheDocument();
    expect(screen.getByText("Done")).toBeInTheDocument();

    // Task count badges: TODO has 2, IN_PROGRESS has 1, rest have 0
    const badges = screen.getAllByText("2");
    expect(badges.length).toBeGreaterThanOrEqual(1); // At least the TODO column shows "2"

    const oneBadge = screen.getAllByText("1");
    expect(oneBadge.length).toBeGreaterThanOrEqual(1); // IN_PROGRESS shows "1"
  });

  // ---------------------------------------------------------------------------
  // Test 2: Renders task cards with title, priority badge, and assignee
  // ---------------------------------------------------------------------------
  it("renders task cards showing title, priority badge, and assignee avatar", () => {
    const columns: ColumnMap = {
      ...emptyColumns(),
      TODO: [
        makeTask({
          id: "t-1",
          title: "Fix login redirect bug",
          priority: "URGENT",
          assignee: {
            id: "user-2",
            name: "Alice Johnson",
            email: "alice@flowboard.io",
            avatarUrl: null,
          },
        }),
        makeTask({
          id: "t-2",
          title: "Add unit tests for API client",
          priority: "MEDIUM",
          assignee: {
            id: "user-3",
            name: "Bob Smith",
            email: "bob@flowboard.io",
            avatarUrl: null,
          },
        }),
      ],
    };

    render(
      <KanbanBoard
        columns={columns}
        projectId="proj-1"
        moveTask={mockMoveTask}
        addTask={mockAddTask}
        updateTask={mockUpdateTask}
      />,
    );

    // Task titles
    expect(screen.getByText("Fix login redirect bug")).toBeInTheDocument();
    expect(screen.getByText("Add unit tests for API client")).toBeInTheDocument();

    // Priority badges
    expect(screen.getByText("Urgent")).toBeInTheDocument();
    expect(screen.getByText("Medium")).toBeInTheDocument();

    // Assignee initials (avatar fallback)
    expect(screen.getByText("AJ")).toBeInTheDocument(); // Alice Johnson
    expect(screen.getByText("BS")).toBeInTheDocument(); // Bob Smith
  });
});
