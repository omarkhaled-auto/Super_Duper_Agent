import "@testing-library/jest-dom";
import { vi } from "vitest";

// =============================================================================
// Global Mocks for Next.js, third-party libraries, and browser APIs
// =============================================================================

// -----------------------------------------------------------------------------
// next/navigation
// -----------------------------------------------------------------------------
const mockPush = vi.fn();
const mockReplace = vi.fn();
const mockBack = vi.fn();
const mockPrefetch = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    back: mockBack,
    prefetch: mockPrefetch,
    pathname: "/",
    query: {},
  }),
  usePathname: () => "/dashboard",
  useSearchParams: () => new URLSearchParams(),
  useParams: () => ({}),
}));

// -----------------------------------------------------------------------------
// next/link -- render as a plain anchor so tests can inspect href
// -----------------------------------------------------------------------------
vi.mock("next/link", () => ({
  __esModule: true,
  default: ({
    children,
    href,
    ...rest
  }: {
    children: React.ReactNode;
    href: string;
    [key: string]: unknown;
  }) => {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { prefetch, ...safeRest } = rest;
    return (
      <a href={href} {...safeRest}>
        {children}
      </a>
    );
  },
}));

// -----------------------------------------------------------------------------
// next-themes
// -----------------------------------------------------------------------------
vi.mock("next-themes", () => ({
  useTheme: () => ({
    theme: "dark",
    setTheme: vi.fn(),
    resolvedTheme: "dark",
    themes: ["light", "dark"],
  }),
}));

// -----------------------------------------------------------------------------
// sonner (toast)
// -----------------------------------------------------------------------------
vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    warning: vi.fn(),
  },
}));

// -----------------------------------------------------------------------------
// @/lib/api -- mock the API client
// -----------------------------------------------------------------------------
vi.mock("@/lib/api", () => {
  const mockGet = vi.fn().mockResolvedValue({ data: [] });
  const mockPost = vi.fn().mockResolvedValue({ data: {} });
  const mockPut = vi.fn().mockResolvedValue({ data: {} });
  const mockPatch = vi.fn().mockResolvedValue({ data: {} });
  const mockDel = vi.fn().mockResolvedValue({ data: {} });

  return {
    __esModule: true,
    default: {
      get: mockGet,
      post: mockPost,
      put: mockPut,
      patch: mockPatch,
      del: mockDel,
    },
    get: mockGet,
    post: mockPost,
    put: mockPut,
    patch: mockPatch,
    del: mockDel,
    ApiError: class ApiError extends Error {
      status: number;
      errors?: Array<{ field: string; message: string }>;
      constructor(
        status: number,
        message: string,
        errors?: Array<{ field: string; message: string }>,
      ) {
        super(message);
        this.name = "ApiError";
        this.status = status;
        this.errors = errors;
      }
    },
    setTokens: vi.fn(),
    clearTokens: vi.fn(),
  };
});

// -----------------------------------------------------------------------------
// socket.io-client
// -----------------------------------------------------------------------------
vi.mock("socket.io-client", () => ({
  __esModule: true,
  default: vi.fn(() => ({
    on: vi.fn(),
    off: vi.fn(),
    emit: vi.fn(),
    connect: vi.fn(),
    disconnect: vi.fn(),
    connected: false,
  })),
  io: vi.fn(() => ({
    on: vi.fn(),
    off: vi.fn(),
    emit: vi.fn(),
    connect: vi.fn(),
    disconnect: vi.fn(),
    connected: false,
  })),
}));

// -----------------------------------------------------------------------------
// @dnd-kit -- mock to avoid complex drag-and-drop internals in unit tests
// -----------------------------------------------------------------------------
vi.mock("@dnd-kit/core", () => ({
  DndContext: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  DragOverlay: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
  PointerSensor: vi.fn(),
  KeyboardSensor: vi.fn(),
  useSensor: vi.fn(),
  useSensors: vi.fn().mockReturnValue([]),
  closestCorners: vi.fn(),
  useDroppable: vi.fn().mockReturnValue({
    setNodeRef: vi.fn(),
    isOver: false,
  }),
}));

vi.mock("@dnd-kit/sortable", () => ({
  SortableContext: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
  verticalListSortingStrategy: {},
  sortableKeyboardCoordinates: vi.fn(),
  useSortable: vi.fn().mockReturnValue({
    attributes: {},
    listeners: {},
    setNodeRef: vi.fn(),
    transform: null,
    transition: null,
    isDragging: false,
  }),
}));

vi.mock("@dnd-kit/utilities", () => ({
  CSS: {
    Transform: {
      toString: vi.fn().mockReturnValue(null),
    },
  },
}));

// -----------------------------------------------------------------------------
// @radix-ui -- Dialog, ScrollArea, Tooltip: render children directly
// -----------------------------------------------------------------------------
vi.mock("@radix-ui/react-dialog", () => ({
  Root: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  Portal: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  Overlay: (props: React.HTMLAttributes<HTMLDivElement>) => (
    <div {...props} />
  ),
  Content: ({
    children,
    ...props
  }: React.HTMLAttributes<HTMLDivElement> & { children: React.ReactNode }) => (
    <div role="dialog" {...props}>
      {children}
    </div>
  ),
  Title: ({
    children,
    ...props
  }: React.HTMLAttributes<HTMLHeadingElement> & {
    children: React.ReactNode;
  }) => <h2 {...props}>{children}</h2>,
  Description: ({
    children,
    ...props
  }: React.HTMLAttributes<HTMLParagraphElement> & {
    children: React.ReactNode;
  }) => <p {...props}>{children}</p>,
  Close: ({
    children,
    ...props
  }: React.HTMLAttributes<HTMLButtonElement> & {
    children: React.ReactNode;
  }) => <button {...props}>{children}</button>,
}));

// -----------------------------------------------------------------------------
// @uiw/react-md-editor -- simplify for tests
// -----------------------------------------------------------------------------
vi.mock("@uiw/react-md-editor", () => ({
  __esModule: true,
  default: (props: { value?: string; onChange?: (val?: string) => void }) => (
    <textarea
      data-testid="md-editor"
      value={props.value ?? ""}
      onChange={(e) => props.onChange?.(e.target.value)}
    />
  ),
}));

// -----------------------------------------------------------------------------
// Browser APIs
// -----------------------------------------------------------------------------

// IntersectionObserver
class MockIntersectionObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}
Object.defineProperty(window, "IntersectionObserver", {
  value: MockIntersectionObserver,
});

// ResizeObserver
class MockResizeObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}
Object.defineProperty(window, "ResizeObserver", {
  value: MockResizeObserver,
});

// matchMedia
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// scrollIntoView
Element.prototype.scrollIntoView = vi.fn();

// localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] ?? null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
    get length() {
      return Object.keys(store).length;
    },
    key: vi.fn((index: number) => Object.keys(store)[index] ?? null),
  };
})();

Object.defineProperty(window, "localStorage", {
  value: localStorageMock,
});

// Global fetch mock (tests can override per-test)
global.fetch = vi.fn().mockResolvedValue({
  ok: true,
  status: 200,
  json: vi.fn().mockResolvedValue({}),
});

// -----------------------------------------------------------------------------
// Export mocks so tests can import and spy on them
// -----------------------------------------------------------------------------
export { mockPush, mockReplace, mockBack, mockPrefetch };
