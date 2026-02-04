import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { KanbanCard } from "@/components/board/kanban-card";

// =============================================================================
// Mock: AddTaskInline (imported transitively by kanban-column)
// =============================================================================
vi.mock("@/components/board/add-task-inline", () => ({
  AddTaskInline: () => <div data-testid="add-task-inline" />,
}));

// =============================================================================
// Fixtures
// =============================================================================

function makeTask(overrides: Record<string, unknown> = {}) {
  return {
    id: "task-1",
    title: "Default Task Title",
    description: null,
    status: "TODO",
    priority: "MEDIUM",
    position: 0,
    dueDate: null,
    createdAt: "2024-01-15T10:00:00Z",
    updatedAt: "2024-01-15T10:00:00Z",
    projectId: "proj-1",
    creatorId: "user-1",
    assigneeId: null,
    assignee: null,
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
  } as never;
}

describe("KanbanCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ---------------------------------------------------------------------------
  // Test 1: Displays task title and correct priority badge
  // ---------------------------------------------------------------------------
  it("renders the task title and the correct priority badge label", () => {
    const urgentTask = makeTask({
      id: "task-urgent",
      title: "Critical production hotfix",
      priority: "URGENT",
    });

    const { unmount } = render(<KanbanCard task={urgentTask} />);

    // Title is rendered
    expect(screen.getByText("Critical production hotfix")).toBeInTheDocument();

    // Priority badge shows "Urgent"
    expect(screen.getByText("Urgent")).toBeInTheDocument();

    unmount();

    // Now test a LOW priority task
    const lowTask = makeTask({
      id: "task-low",
      title: "Update README documentation",
      priority: "LOW",
    });

    render(<KanbanCard task={lowTask} />);

    expect(screen.getByText("Update README documentation")).toBeInTheDocument();
    expect(screen.getByText("Low")).toBeInTheDocument();
  });

  // ---------------------------------------------------------------------------
  // Test 2: Shows due date warning when the task is overdue
  // ---------------------------------------------------------------------------
  it("displays the due date in error styling when the date is in the past", () => {
    // Use a date that is definitely in the past
    const overdueTask = makeTask({
      id: "task-overdue",
      title: "Submit quarterly report",
      priority: "HIGH",
      dueDate: "2023-06-15T00:00:00Z", // Well in the past
    });

    render(<KanbanCard task={overdueTask} />);

    // The task title should be present
    expect(screen.getByText("Submit quarterly report")).toBeInTheDocument();

    // Priority badge
    expect(screen.getByText("High")).toBeInTheDocument();

    // The due date label should render the formatted date (e.g., "Jun 15")
    // and it should be styled with the error color class
    const dueDateElement = screen.getByText("Jun 15");
    expect(dueDateElement).toBeInTheDocument();

    // The parent span wrapping the due date has the "text-error" class
    // indicating overdue status
    expect(dueDateElement.closest("span")).toHaveClass("text-error");
  });
});
