/**
 * FlowBoard Design Tokens
 *
 * Typed constants for programmatic access to the design system.
 * CSS custom properties are the source of truth (globals.css);
 * these TypeScript values are for JS/TS code that cannot read CSS vars
 * (e.g., Recharts config, canvas drawing, email templates, tests).
 *
 * IMPORTANT: If you change values here, update globals.css to match.
 */

// ============================================================================
// COLOR PALETTE
// ============================================================================

/** Raw hex values for use outside CSS (charts, canvas, etc.) */
export const colors = {
  /** Violet accent — the FlowBoard signature color */
  accent: {
    DEFAULT: "#8B5CF6",
    hover: "#7C3AED",
    active: "#6D28D9",
    50: "#F5F3FF",
    100: "#EDE9FE",
    200: "#DDD6FE",
    300: "#C4B5FD",
    400: "#A78BFA",
    500: "#8B5CF6",
    600: "#7C3AED",
    700: "#6D28D9",
    800: "#5B21B6",
    900: "#4C1D95",
  },

  /** Priority levels */
  priority: {
    urgent: "#EF4444",
    high: "#F97316",
    medium: "#EAB308",
    low: "#3B82F6",
    none: "#595959",
  } as const,

  /** Kanban column / task status */
  status: {
    backlog: "#737373",
    todo: "#3B82F6",
    "in-progress": "#8B5CF6",
    "in-review": "#F97316",
    done: "#22C55E",
    cancelled: "#4D4D4D",
  } as const,

  /** Semantic feedback */
  semantic: {
    success: "#22C55E",
    warning: "#F59E0B",
    error: "#EF4444",
    info: "#0EA5E9",
  } as const,

  /** Dark theme backgrounds */
  dark: {
    bg: {
      primary: "#0A0A0B",
      secondary: "#0F1011",
      tertiary: "#151516",
      quaternary: "#1C1C1E",
      elevated: "#222224",
    },
    text: {
      primary: "#F2F2F2",
      secondary: "#B3B3B3",
      tertiary: "#808080",
      quaternary: "#595959",
    },
  } as const,

  /** Light theme backgrounds */
  light: {
    bg: {
      primary: "#FBFBFC",
      secondary: "#F6F6F7",
      tertiary: "#FFFFFF",
      quaternary: "#F2F2F3",
      elevated: "#FFFFFF",
    },
    text: {
      primary: "#191A1C",
      secondary: "#505153",
      tertiary: "#808080",
      quaternary: "#A6A6A6",
    },
  } as const,

  /** Recharts color palette (indexed 1-5) */
  chart: [
    "#8B5CF6", // violet
    "#22C55E", // green
    "#3B82F6", // blue
    "#F97316", // orange
    "#EF4444", // red
  ] as const,
} as const;

// ============================================================================
// TYPOGRAPHY
// ============================================================================

export const typography = {
  /** Font families (CSS variable names) */
  fonts: {
    heading: "Space Grotesk",
    body: "Plus Jakarta Sans",
    mono: "JetBrains Mono",
  },

  /** Font size scale in px */
  sizes: {
    "2xs": 10,
    xs: 12,
    sm: 13,
    base: 14,
    md: 15,
    lg: 16,
    xl: 18,
    "2xl": 20,
    "3xl": 24,
    "4xl": 30,
    "5xl": 36,
    display: 48,
  },

  /** Line heights paired with font sizes */
  lineHeights: {
    "2xs": 14,
    xs: 16,
    sm: 20,
    base: 22,
    md: 24,
    lg: 24,
    xl: 28,
    "2xl": 30,
    "3xl": 32,
    "4xl": 36,
    "5xl": 40,
    display: 52,
  },

  /** Font weights */
  weights: {
    light: 300,
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
    extrabold: 800,
  },

  /** Letter spacing presets */
  tracking: {
    tightest: "-0.035em",
    tighter: "-0.025em",
    tight: "-0.015em",
    normal: "0",
    wide: "0.025em",
  },
} as const;

// ============================================================================
// SPACING
// ============================================================================

/** 4px base grid. All values in px. */
export const spacing = {
  0: 0,
  0.5: 2,
  1: 4,
  1.5: 6,
  2: 8,
  2.5: 10,
  3: 12,
  3.5: 14,
  4: 16,
  5: 20,
  6: 24,
  7: 28,
  8: 32,
  9: 36,
  10: 40,
  11: 44,
  12: 48,
  14: 56,
  16: 64,
  18: 72,
  20: 80,
  24: 96,
  28: 112,
  32: 128,
} as const;

// ============================================================================
// LAYOUT
// ============================================================================

export const layout = {
  sidebar: {
    width: 240,
    collapsedWidth: 64,
  },
  header: {
    height: 48,
  },
  panel: {
    width: 480,
    widthLg: 640,
  },
  kanban: {
    columnWidth: 320,
    columnMinWidth: 280,
    cardGap: 8,
  },
  container: {
    maxWidth: 1400,
    padding: 32,
  },
} as const;

// ============================================================================
// BORDER RADIUS
// ============================================================================

export const radii = {
  sm: 4,
  md: 6,
  lg: 8,
  xl: 12,
  "2xl": 16,
  full: 9999,
} as const;

// ============================================================================
// ANIMATION
// ============================================================================

export const animation = {
  duration: {
    fast: 150,  // hover effects
    base: 200,  // state changes
    slow: 300,  // panels, modals
  },
  easing: {
    default: "ease-out",
    spring: "cubic-bezier(0.34, 1.56, 0.64, 1)",
  },
} as const;

// ============================================================================
// BREAKPOINTS
// ============================================================================

export const breakpoints = {
  xs: 480,
  sm: 640,   // mobile
  md: 768,   // tablet
  lg: 1024,
  xl: 1280,
  "2xl": 1400,
} as const;

// ============================================================================
// Z-INDEX
// ============================================================================

export const zIndex = {
  base: 0,
  dropdown: 50,
  sticky: 100,
  overlay: 200,
  modal: 300,
  popover: 400,
  toast: 500,
  commandPalette: 600,
  tooltip: 700,
} as const;

// ============================================================================
// AVATAR SIZES
// ============================================================================

export const avatarSizes = {
  xs: 24,
  sm: 32,
  md: 40,
  lg: 48,
} as const;

// ============================================================================
// COMPONENT SPECS
// ============================================================================

/**
 * Component-level design specifications.
 * Use these when building custom components that need to match
 * the design system but cannot use Tailwind classes directly.
 */
export const componentSpecs = {
  button: {
    heightSm: 28,
    heightMd: 36,
    heightLg: 44,
    paddingX: { sm: 12, md: 16, lg: 20 },
    borderRadius: radii.md,
    fontSize: typography.sizes.sm,
    fontWeight: typography.weights.medium,
    transition: `${animation.duration.fast}ms ${animation.easing.default}`,
  },

  input: {
    height: 36,
    paddingX: 12,
    borderRadius: radii.md,
    fontSize: typography.sizes.base,
  },

  card: {
    padding: 16,
    borderRadius: radii.lg,
  },

  kanbanCard: {
    paddingX: 16,
    paddingY: 12,
    borderRadius: radii.lg,
    priorityStripeWidth: 3,
  },

  badge: {
    paddingX: 8,
    paddingY: 2,
    borderRadius: radii.full,
    fontSize: typography.sizes.xs,
    fontWeight: typography.weights.medium,
  },

  toast: {
    maxWidth: 420,
    paddingX: 16,
    paddingY: 12,
    borderRadius: radii.lg,
  },
} as const;

// ============================================================================
// PRIORITY & STATUS ENUMS (for type-safe usage in components)
// ============================================================================

export type Priority = "urgent" | "high" | "medium" | "low" | "none";
export type Status = "backlog" | "todo" | "in-progress" | "in-review" | "done" | "cancelled";

export const PRIORITIES: Priority[] = ["urgent", "high", "medium", "low", "none"];
export const STATUSES: Status[] = ["backlog", "todo", "in-progress", "in-review", "done", "cancelled"];

/** Human-readable labels */
export const PRIORITY_LABELS: Record<Priority, string> = {
  urgent: "Urgent",
  high: "High",
  medium: "Medium",
  low: "Low",
  none: "No Priority",
};

export const STATUS_LABELS: Record<Status, string> = {
  backlog: "Backlog",
  todo: "Todo",
  "in-progress": "In Progress",
  "in-review": "In Review",
  done: "Done",
  cancelled: "Cancelled",
};
