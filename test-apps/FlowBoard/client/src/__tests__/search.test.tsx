import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import { CommandPalette } from "@/components/search/command-palette";

// =============================================================================
// Mock: useSearch hook — controls what results and state the palette sees
// =============================================================================

const mockSetQuery = vi.fn();
const mockSetSelectedIndex = vi.fn();
const mockAddRecent = vi.fn();
const mockClearRecents = vi.fn();
const mockReset = vi.fn();

let mockSearchState = {
  query: "",
  setQuery: mockSetQuery,
  results: { tasks: [], projects: [], members: [] },
  flatResults: [] as Array<{ type: string; data: Record<string, unknown> }>,
  selectedIndex: 0,
  setSelectedIndex: mockSetSelectedIndex,
  isLoading: false,
  isDebouncing: false,
  error: null as string | null,
  recentSearches: [] as string[],
  addRecent: mockAddRecent,
  clearRecents: mockClearRecents,
  reset: mockReset,
};

vi.mock("@/hooks/use-search", () => ({
  useSearch: () => mockSearchState,
}));

// =============================================================================
// Mock: SearchResultItem — render a simple clickable div so we can test
// selection and grouping without the full component
// =============================================================================
vi.mock("@/components/search/search-result-item", () => ({
  SearchResultItem: ({
    item,
    isSelected,
    onClick,
    onMouseEnter,
  }: {
    item: { type: string; data: { id: string; title?: string; name?: string } };
    isSelected: boolean;
    onClick: () => void;
    onMouseEnter: () => void;
  }) => (
    <div
      role="option"
      aria-selected={isSelected}
      onClick={onClick}
      onMouseEnter={onMouseEnter}
      data-testid={`search-result-${item.data.id}`}
    >
      {item.data.title ?? item.data.name ?? item.data.id}
    </div>
  ),
}));

// =============================================================================
// Mock: Radix Dialog -- render children directly so the palette content is
// visible in the test DOM when open=true
// =============================================================================
vi.mock("@/components/ui/dialog", () => ({
  Dialog: ({
    children,
    open,
  }: {
    children: React.ReactNode;
    open: boolean;
    onOpenChange: (open: boolean) => void;
  }) => (open ? <div data-testid="dialog-root">{children}</div> : null),
  DialogPortal: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
  DialogOverlay: () => <div data-testid="dialog-overlay" />,
}));

vi.mock("@/components/ui/separator", () => ({
  Separator: () => <hr />,
}));

vi.mock("@/components/ui/skeleton", () => ({
  Skeleton: ({ className }: { className?: string }) => (
    <div data-testid="skeleton" className={className} />
  ),
}));

vi.mock("@/components/ui/scroll-area", () => ({
  ScrollArea: ({
    children,
    className,
  }: {
    children: React.ReactNode;
    className?: string;
  }) => <div className={className}>{children}</div>,
}));

describe("CommandPalette", () => {
  const mockOnOpenChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    // Reset to default state before each test
    mockSearchState = {
      query: "",
      setQuery: mockSetQuery,
      results: { tasks: [], projects: [], members: [] },
      flatResults: [],
      selectedIndex: 0,
      setSelectedIndex: mockSetSelectedIndex,
      isLoading: false,
      isDebouncing: false,
      error: null,
      recentSearches: [],
      addRecent: mockAddRecent,
      clearRecents: mockClearRecents,
      reset: mockReset,
    };
  });

  // ---------------------------------------------------------------------------
  // Test 1: Opens dialog and shows search input with placeholder
  // ---------------------------------------------------------------------------
  it("renders the search input with placeholder when open is true", () => {
    render(<CommandPalette open={true} onOpenChange={mockOnOpenChange} />);

    // The dialog content should be visible
    expect(screen.getByTestId("dialog-root")).toBeInTheDocument();

    // The search input should be present with the correct placeholder
    const searchInput = screen.getByPlaceholderText(
      "Search tasks, projects, members...",
    );
    expect(searchInput).toBeInTheDocument();
    expect(searchInput).toHaveAttribute("role", "combobox");

    // Keyboard hints should be visible
    expect(screen.getByText("Navigate")).toBeInTheDocument();
    expect(screen.getByText("Select")).toBeInTheDocument();
    expect(screen.getByText("Close")).toBeInTheDocument();
  });

  // ---------------------------------------------------------------------------
  // Test 2: Shows search results grouped by type (Tasks, Projects, Members)
  // ---------------------------------------------------------------------------
  it("displays search results with section headers for Tasks, Projects, and Members", () => {
    // Configure mock state with results from all three categories
    mockSearchState = {
      ...mockSearchState,
      query: "design",
      results: {
        tasks: [
          {
            id: "task-1",
            title: "Design system overhaul",
            status: "IN_PROGRESS",
            priority: "HIGH",
            projectId: "proj-1",
            projectName: "FlowBoard",
            projectColor: "violet",
          },
        ],
        projects: [
          {
            id: "proj-2",
            name: "Design System v2",
            color: "blue",
            icon: null,
            description: null,
          },
        ],
        members: [
          {
            id: "user-3",
            name: "Diana Designer",
            email: "diana@flowboard.io",
            avatarUrl: null,
          },
        ],
      },
      flatResults: [
        {
          type: "task",
          data: {
            id: "task-1",
            title: "Design system overhaul",
            status: "IN_PROGRESS",
            priority: "HIGH",
            projectId: "proj-1",
            projectName: "FlowBoard",
            projectColor: "violet",
          },
        },
        {
          type: "project",
          data: {
            id: "proj-2",
            name: "Design System v2",
            color: "blue",
            icon: null,
            description: null,
          },
        },
        {
          type: "member",
          data: {
            id: "user-3",
            name: "Diana Designer",
            email: "diana@flowboard.io",
            avatarUrl: null,
          },
        },
      ],
    };

    render(<CommandPalette open={true} onOpenChange={mockOnOpenChange} />);

    // Section headers should be visible
    expect(screen.getByText("Tasks")).toBeInTheDocument();
    expect(screen.getByText("Projects")).toBeInTheDocument();
    expect(screen.getByText("Members")).toBeInTheDocument();

    // Individual result items should be rendered
    expect(screen.getByTestId("search-result-task-1")).toBeInTheDocument();
    expect(screen.getByText("Design system overhaul")).toBeInTheDocument();

    expect(screen.getByTestId("search-result-proj-2")).toBeInTheDocument();
    expect(screen.getByText("Design System v2")).toBeInTheDocument();

    expect(screen.getByTestId("search-result-user-3")).toBeInTheDocument();
    expect(screen.getByText("Diana Designer")).toBeInTheDocument();
  });
});
