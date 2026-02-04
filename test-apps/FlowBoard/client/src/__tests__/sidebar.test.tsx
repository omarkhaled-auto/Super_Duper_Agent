import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Sidebar } from "@/components/layout/sidebar";

// =============================================================================
// Mock: useAuth from auth-context — the sidebar uses this for user info + logout
// =============================================================================

const mockLogout = vi.fn().mockResolvedValue(undefined);

vi.mock("@/contexts/auth-context", () => ({
  useAuth: () => ({
    user: {
      id: "user-1",
      name: "Omar Khaled",
      email: "omar@flowboard.io",
      avatarUrl: null,
    },
    loading: false,
    login: vi.fn(),
    signup: vi.fn(),
    logout: mockLogout,
  }),
  ApiError: class ApiError extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  },
}));

// =============================================================================
// Mock: useProjects hook — controls the project list shown in the sidebar
// =============================================================================

const mockProjects = [
  {
    id: "proj-1",
    name: "FlowBoard Core",
    color: "violet",
    description: "Main product",
    ownerId: "user-1",
    members: [],
    createdAt: "2024-01-01T00:00:00Z",
    updatedAt: "2024-01-15T00:00:00Z",
  },
  {
    id: "proj-2",
    name: "Marketing Website",
    color: "blue",
    description: "Company site",
    ownerId: "user-1",
    members: [],
    createdAt: "2024-01-02T00:00:00Z",
    updatedAt: "2024-01-15T00:00:00Z",
  },
  {
    id: "proj-3",
    name: "Mobile App",
    color: "green",
    description: "iOS/Android app",
    ownerId: "user-1",
    members: [],
    createdAt: "2024-01-03T00:00:00Z",
    updatedAt: "2024-01-15T00:00:00Z",
  },
];

vi.mock("@/hooks/use-projects", () => ({
  useProjects: () => ({
    projects: mockProjects,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
}));

// =============================================================================
// Mock: Radix UI Tooltip, DropdownMenu, ScrollArea -- render children directly
// =============================================================================

vi.mock("@/components/ui/tooltip", () => ({
  TooltipProvider: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
  Tooltip: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  TooltipTrigger: ({
    children,
    asChild,
    ...rest
  }: {
    children: React.ReactNode;
    asChild?: boolean;
  }) => <>{children}</>,
  TooltipContent: ({
    children,
  }: {
    children: React.ReactNode;
    side?: string;
    sideOffset?: number;
  }) => <span data-testid="tooltip-content">{children}</span>,
}));

vi.mock("@/components/ui/dropdown-menu", () => ({
  DropdownMenu: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
  DropdownMenuTrigger: ({
    children,
    asChild,
  }: {
    children: React.ReactNode;
    asChild?: boolean;
  }) => <>{children}</>,
  DropdownMenuContent: ({
    children,
  }: {
    children: React.ReactNode;
    side?: string;
    align?: string;
    sideOffset?: number;
    className?: string;
  }) => <div data-testid="dropdown-content">{children}</div>,
  DropdownMenuItem: ({
    children,
    onClick,
    className,
  }: {
    children: React.ReactNode;
    onClick?: () => void;
    className?: string;
  }) => (
    <button onClick={onClick} className={className}>
      {children}
    </button>
  ),
  DropdownMenuLabel: ({
    children,
    className,
  }: {
    children: React.ReactNode;
    className?: string;
  }) => <div className={className}>{children}</div>,
  DropdownMenuSeparator: () => <hr />,
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

vi.mock("@/components/ui/separator", () => ({
  Separator: ({ className }: { className?: string }) => (
    <hr className={className} />
  ),
}));

vi.mock("@/components/ui/skeleton", () => ({
  Skeleton: ({ className }: { className?: string }) => (
    <div data-testid="skeleton" className={className} />
  ),
}));

describe("Sidebar", () => {
  const mockToggleCollapse = vi.fn();
  const mockCreateProject = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ---------------------------------------------------------------------------
  // Test 1: Renders navigation links, project list, and user info
  // ---------------------------------------------------------------------------
  it("renders the brand logo, navigation links, project list, and user avatar", () => {
    render(
      <Sidebar
        collapsed={false}
        onToggleCollapse={mockToggleCollapse}
        onCreateProject={mockCreateProject}
      />,
    );

    // Brand name
    expect(screen.getByText("FlowBoard")).toBeInTheDocument();

    // Navigation items (from NAV_ITEMS constant)
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("My Tasks")).toBeInTheDocument();
    expect(screen.getByText("Analytics")).toBeInTheDocument();

    // Navigation links should point to the correct routes
    const dashboardLink = screen.getByText("Dashboard").closest("a");
    expect(dashboardLink).toHaveAttribute("href", "/dashboard");

    const myTasksLink = screen.getByText("My Tasks").closest("a");
    expect(myTasksLink).toHaveAttribute("href", "/tasks");

    const analyticsLink = screen.getByText("Analytics").closest("a");
    expect(analyticsLink).toHaveAttribute("href", "/analytics");

    // Projects section header
    expect(screen.getByText("Projects")).toBeInTheDocument();

    // Project names from mock data
    expect(screen.getByText("FlowBoard Core")).toBeInTheDocument();
    expect(screen.getByText("Marketing Website")).toBeInTheDocument();
    expect(screen.getByText("Mobile App")).toBeInTheDocument();

    // User information from the auth context mock
    const nameElements = screen.getAllByText("Omar Khaled");
    expect(nameElements.length).toBeGreaterThanOrEqual(1);

    const emailElements = screen.getAllByText("omar@flowboard.io");
    expect(emailElements.length).toBeGreaterThanOrEqual(1);

    // Avatar initials fallback
    expect(screen.getByText("OK")).toBeInTheDocument();

    // Collapse button should say "Collapse" in expanded mode
    expect(screen.getByText("Collapse")).toBeInTheDocument();

    // Theme toggle: since mock returns "dark", it should offer light mode
    expect(screen.getByText("Light mode")).toBeInTheDocument();
  });

  // ---------------------------------------------------------------------------
  // Test 2: Collapsed mode hides text labels and shows only icons
  // ---------------------------------------------------------------------------
  it("hides text labels and the project section header when collapsed", () => {
    render(
      <Sidebar
        collapsed={true}
        onToggleCollapse={mockToggleCollapse}
        onCreateProject={mockCreateProject}
      />,
    );

    // In collapsed mode, the brand wordmark "FlowBoard" is hidden
    // (only the icon remains, the text is conditionally rendered)
    expect(screen.queryByText("FlowBoard")).not.toBeInTheDocument();

    // The inline <span> nav labels are NOT rendered.
    // However, our Tooltip mock still renders tooltip content into the DOM.
    // We verify the nav labels only appear inside tooltip containers
    // (data-testid="tooltip-content"), NOT as direct link children.
    const navLinks = screen.getAllByRole("link");

    // No link should contain a <span> child with "Dashboard" text
    // (in expanded mode, the label is a <span> sibling to the icon inside the link)
    for (const link of navLinks) {
      const spanChild = link.querySelector("span.truncate");
      expect(spanChild).toBeNull();
    }

    // "Projects" section header is hidden in collapsed mode
    // (guarded by `!collapsed &&`)
    const projectHeaders = screen.queryAllByText("Projects");
    // Tooltip content may still show "Projects" text, but the section header span is gone
    const sectionHeader = projectHeaders.find(
      (el) => el.closest("[data-testid='tooltip-content']") === null &&
              el.tagName === "SPAN" &&
              el.textContent === "Projects"
    );
    expect(sectionHeader).toBeUndefined();

    // Project names are NOT rendered as link text in collapsed mode
    // (guarded by `!collapsed &&` around the <span> with name)
    for (const link of navLinks) {
      const textContent = link.textContent ?? "";
      expect(textContent).not.toContain("FlowBoard Core");
      expect(textContent).not.toContain("Marketing Website");
      expect(textContent).not.toContain("Mobile App");
    }

    // The "Collapse" text is hidden (only chevron icon shown)
    expect(screen.queryByText("Collapse")).not.toBeInTheDocument();

    // But the avatar initials should still be visible (icon-only mode)
    expect(screen.getByText("OK")).toBeInTheDocument();

    // Navigation links still exist (for icon-only click targets)
    expect(navLinks.length).toBeGreaterThan(0);
  });
});
