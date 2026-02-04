import type { Config } from "tailwindcss";

/**
 * FlowBoard — Tailwind CSS Design System Configuration
 *
 * Design direction: Minimal Modern with Industrial Precision (Linear.app inspired)
 *
 * Typography:
 *   Heading  — Space Grotesk     (--font-heading / --font-space-grotesk)
 *   Body     — Plus Jakarta Sans (--font-body / --font-plus-jakarta)
 *   Mono     — JetBrains Mono    (--font-mono / --font-jetbrains)
 *
 * Color system:
 *   All semantic colors reference CSS custom properties defined in globals.css
 *   so dark/light theming works automatically via class switching.
 *   The `brand` palette provides static violet hex values for contexts that
 *   cannot consume CSS variables (e.g. OG images, emails, favicons).
 *
 * Spacing:
 *   4px base grid. All values are multiples of 4px (or 2px for sub-grid).
 *
 * Animations:
 *   150ms ease-out for hover, 200ms for state changes, 300ms for panels.
 */
const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/**/*.{ts,tsx}",
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./src/lib/**/*.{ts,tsx}",
    "./src/hooks/**/*.{ts,tsx}",
  ],
  theme: {
    /* ----------------------------------------------------------------
       CONTAINER
       ---------------------------------------------------------------- */
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1440px",
      },
    },

    /* ----------------------------------------------------------------
       CORE EXTENSIONS
       ---------------------------------------------------------------- */
    extend: {
      /* ==============================================================
         FONT FAMILIES
         Supports both CSS variable naming conventions:
           --font-heading / --font-space-grotesk
           --font-body    / --font-plus-jakarta
           --font-mono    / --font-jetbrains
         ============================================================== */
      fontFamily: {
        heading: [
          "var(--font-space-grotesk, var(--font-heading))",
          "system-ui",
          "-apple-system",
          "sans-serif",
        ],
        sans: [
          "var(--font-plus-jakarta, var(--font-body))",
          "system-ui",
          "-apple-system",
          "sans-serif",
        ],
        body: [
          "var(--font-plus-jakarta, var(--font-body))",
          "system-ui",
          "-apple-system",
          "sans-serif",
        ],
        mono: [
          "var(--font-jetbrains, var(--font-mono))",
          "Menlo",
          "Courier New",
          "monospace",
        ],
      },

      /* ==============================================================
         FONT SIZE SCALE
         xs (12px) through display (48px) with paired line-heights
         and tracking for larger sizes.
         ============================================================== */
      fontSize: {
        "2xs": ["0.625rem", { lineHeight: "0.875rem" }],
        xs: ["0.75rem", { lineHeight: "1rem", letterSpacing: "0.01em" }],
        sm: ["0.8125rem", { lineHeight: "1.25rem" }],
        base: ["0.875rem", { lineHeight: "1.5rem" }],
        md: ["0.9375rem", { lineHeight: "1.5rem" }],
        lg: ["1rem", { lineHeight: "1.5rem" }],
        xl: ["1.125rem", { lineHeight: "1.75rem" }],
        "2xl": ["1.5rem", { lineHeight: "2rem", letterSpacing: "-0.01em" }],
        "3xl": ["1.875rem", { lineHeight: "2.25rem", letterSpacing: "-0.02em" }],
        "4xl": ["2.5rem", { lineHeight: "3rem", letterSpacing: "-0.02em" }],
        "5xl": ["3rem", { lineHeight: "3.25rem", letterSpacing: "-0.025em" }],
        display: ["3.5rem", { lineHeight: "3.75rem", letterSpacing: "-0.03em" }],
      },

      /* ==============================================================
         FONT WEIGHT
         ============================================================== */
      fontWeight: {
        light: "300",
        normal: "400",
        medium: "500",
        semibold: "600",
        bold: "700",
        extrabold: "800",
      },

      /* ==============================================================
         LETTER SPACING
         ============================================================== */
      letterSpacing: {
        tightest: "-0.035em",
        tighter: "-0.025em",
        tight: "-0.015em",
        normal: "0",
        wide: "0.025em",
        wider: "0.05em",
        widest: "0.1em",
      },

      /* ==============================================================
         COLORS
         Themed colors reference CSS custom properties from globals.css.
         Static `brand` palette is available for non-themed contexts.
         ============================================================== */
      colors: {
        /* --- Brand palette (static violet hex) ---
           Use for OG images, emails, meta tags, or anywhere
           CSS variables are unavailable. */
        brand: {
          DEFAULT: "#8B5CF6",
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
          950: "#2E1065",
        },

        /* --- shadcn/ui core palette --- */
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },

        /* --- FlowBoard surface palette (themed via CSS vars) --- */
        surface: {
          primary: "hsl(var(--color-bg-primary))",
          secondary: "hsl(var(--color-bg-secondary))",
          tertiary: "hsl(var(--color-bg-tertiary))",
          quaternary: "hsl(var(--color-bg-quaternary))",
          elevated: "hsl(var(--color-bg-elevated))",
          overlay: "hsl(var(--color-surface-overlay))",
          hover: "hsl(var(--color-surface-hover))",
          active: "hsl(var(--color-surface-active))",
          selected: "hsl(var(--color-surface-selected))",
        },

        /* --- Content / text hierarchy (themed via CSS vars) --- */
        content: {
          primary: "hsl(var(--color-text-primary))",
          secondary: "hsl(var(--color-text-secondary))",
          tertiary: "hsl(var(--color-text-tertiary))",
          quaternary: "hsl(var(--color-text-quaternary))",
          inverse: "hsl(var(--color-text-on-accent))",
        },

        /* --- Text hierarchy (alias — backward compat) --- */
        text: {
          primary: "hsl(var(--color-text-primary))",
          secondary: "hsl(var(--color-text-secondary))",
          tertiary: "hsl(var(--color-text-tertiary))",
          quaternary: "hsl(var(--color-text-quaternary))",
        },

        /* --- Edge / border colors (themed via CSS vars) --- */
        edge: {
          DEFAULT: "hsl(var(--color-border-default))",
          subtle: "hsl(var(--color-border-subtle))",
          strong: "hsl(var(--color-border-strong))",
        },

        /* --- Border variants (direct access) --- */
        "border-subtle": "hsl(var(--color-border-subtle))",
        "border-strong": "hsl(var(--color-border-strong))",
        "border-accent": "hsl(var(--color-border-accent))",

        /* --- Violet accent shades (themed via CSS vars) --- */
        violet: {
          DEFAULT: "hsl(var(--color-accent))",
          hover: "hsl(var(--color-accent-hover))",
          active: "hsl(var(--color-accent-active))",
          muted: "hsl(var(--color-accent-muted))",
          subtle: "hsl(var(--color-accent-subtle))",
        },

        /* --- Priority colors (themed via CSS vars) --- */
        priority: {
          urgent: "hsl(var(--color-priority-urgent))",
          high: "hsl(var(--color-priority-high))",
          medium: "hsl(var(--color-priority-medium))",
          low: "hsl(var(--color-priority-low))",
          none: "hsl(var(--color-priority-none))",
        },
        /* Direct-access aliases */
        urgent: "hsl(var(--color-priority-urgent))",
        high: "hsl(var(--color-priority-high))",
        medium: "hsl(var(--color-priority-medium))",
        low: "hsl(var(--color-priority-low))",
        "priority-none": "hsl(var(--color-priority-none))",

        /* --- Status colors (themed via CSS vars) --- */
        status: {
          backlog: "hsl(var(--color-status-backlog))",
          todo: "hsl(var(--color-status-todo))",
          "in-progress": "hsl(var(--color-status-in-progress))",
          "in-review": "hsl(var(--color-status-in-review))",
          done: "hsl(var(--color-status-done))",
          cancelled: "hsl(var(--color-status-cancelled))",
        },

        /* --- Semantic colors (themed via CSS vars) --- */
        success: {
          DEFAULT: "hsl(var(--color-success))",
          muted: "hsl(var(--color-success-muted))",
          light: "#DCFCE7",
          dark: "#166534",
        },
        warning: {
          DEFAULT: "hsl(var(--color-warning))",
          muted: "hsl(var(--color-warning-muted))",
          light: "#FEF9C3",
          dark: "#854D0E",
        },
        error: {
          DEFAULT: "hsl(var(--color-error))",
          muted: "hsl(var(--color-error-muted))",
          light: "#FEE2E2",
          dark: "#991B1B",
        },
        info: {
          DEFAULT: "hsl(var(--color-info))",
          muted: "hsl(var(--color-info-muted))",
          light: "#DBEAFE",
          dark: "#1E40AF",
        },

        /* --- Chart palette --- */
        chart: {
          1: "hsl(var(--chart-1))",
          2: "hsl(var(--chart-2))",
          3: "hsl(var(--chart-3))",
          4: "hsl(var(--chart-4))",
          5: "hsl(var(--chart-5))",
        },

        /* --- Sidebar --- */
        sidebar: {
          DEFAULT: "hsl(var(--sidebar-background))",
          foreground: "hsl(var(--sidebar-foreground))",
          primary: "hsl(var(--sidebar-primary))",
          "primary-foreground": "hsl(var(--sidebar-primary-foreground))",
          accent: "hsl(var(--sidebar-accent))",
          "accent-foreground": "hsl(var(--sidebar-accent-foreground))",
          border: "hsl(var(--sidebar-border))",
          ring: "hsl(var(--sidebar-ring))",
        },
      },

      /* ==============================================================
         BORDER RADIUS
         ============================================================== */
      borderRadius: {
        sm: "var(--radius-sm, 4px)",
        DEFAULT: "var(--radius-md, 6px)",
        md: "var(--radius-md, 6px)",
        lg: "var(--radius-lg, 8px)",
        xl: "var(--radius-xl, 12px)",
        "2xl": "var(--radius-2xl, 16px)",
        full: "var(--radius-full, 9999px)",
      },

      /* ==============================================================
         SPACING (4px base grid)
         Standard Tailwind scale + custom layout tokens
         ============================================================== */
      spacing: {
        "0.5": "2px",
        "1": "4px",
        "1.5": "6px",
        "2": "8px",
        "2.5": "10px",
        "3": "12px",
        "3.5": "14px",
        "4": "16px",
        "5": "20px",
        "6": "24px",
        "7": "28px",
        "8": "32px",
        "9": "36px",
        "10": "40px",
        "11": "44px",
        "12": "48px",
        "14": "56px",
        "16": "64px",
        "18": "72px",
        "20": "80px",
        "24": "96px",
        "28": "112px",
        "32": "128px",
        /* Layout-specific spacing */
        sidebar: "var(--sidebar-width, 240px)",
        "sidebar-collapsed": "var(--sidebar-width-collapsed, 64px)",
        header: "var(--header-height, 48px)",
        panel: "var(--panel-width, 480px)",
        "panel-lg": "var(--panel-width-lg, 640px)",
      },

      /* ==============================================================
         WIDTH
         ============================================================== */
      width: {
        sidebar: "var(--sidebar-width, 240px)",
        "sidebar-collapsed": "var(--sidebar-width-collapsed, 64px)",
        panel: "var(--panel-width, 480px)",
        "panel-lg": "var(--panel-width-lg, 640px)",
        "kanban-col": "var(--kanban-column-width, 320px)",
      },

      /* ==============================================================
         MIN WIDTH
         ============================================================== */
      minWidth: {
        "kanban-col": "var(--kanban-column-min-width, 280px)",
      },

      /* ==============================================================
         MAX WIDTH
         ============================================================== */
      maxWidth: {
        content: "1280px",
        dashboard: "1440px",
      },

      /* ==============================================================
         HEIGHT
         ============================================================== */
      height: {
        header: "var(--header-height, 48px)",
      },

      /* ==============================================================
         Z-INDEX
         ============================================================== */
      zIndex: {
        dropdown: "var(--z-dropdown, 50)",
        sticky: "var(--z-sticky, 100)",
        overlay: "var(--z-overlay, 200)",
        modal: "var(--z-modal, 300)",
        popover: "var(--z-popover, 400)",
        toast: "var(--z-toast, 500)",
        command: "var(--z-command-palette, 600)",
        tooltip: "var(--z-tooltip, 700)",
      },

      /* ==============================================================
         BOX SHADOW
         ============================================================== */
      boxShadow: {
        xs: "var(--shadow-xs, 0 1px 2px rgba(0, 0, 0, 0.05))",
        sm: "var(--shadow-sm, 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06))",
        md: "var(--shadow-md, 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1))",
        lg: "var(--shadow-lg, 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1))",
        xl: "var(--shadow-xl, 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1))",
        glow: "var(--shadow-glow, 0 0 20px rgba(139, 92, 246, 0.15))",
        card: "var(--shadow-xs, 0 1px 2px rgba(0, 0, 0, 0.05))",
        "card-hover": "var(--shadow-sm, 0 1px 3px rgba(0, 0, 0, 0.1))",
        panel: "var(--shadow-xl, 0 20px 25px -5px rgba(0, 0, 0, 0.1))",
        dropdown: "var(--shadow-lg, 0 10px 15px -3px rgba(0, 0, 0, 0.1))",
        overlay: "var(--shadow-xl, 0 20px 25px -5px rgba(0, 0, 0, 0.1))",
      },

      /* ==============================================================
         TRANSITIONS
         ============================================================== */
      transitionDuration: {
        "150": "150ms",
        "200": "200ms",
        "300": "300ms",
        fast: "150ms",
        base: "200ms",
        slow: "300ms",
      },
      transitionTimingFunction: {
        default: "ease-out",
        spring: "cubic-bezier(0.34, 1.56, 0.64, 1)",
      },

      /* ==============================================================
         KEYFRAMES & ANIMATIONS
         ============================================================== */
      keyframes: {
        /* shadcn accordion */
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        /* Skeleton pulse */
        skeleton: {
          "0%": { opacity: "0.4" },
          "50%": { opacity: "0.7" },
          "100%": { opacity: "0.4" },
        },
        /* Shimmer (gradient-based skeleton) */
        shimmer: {
          "0%": { backgroundPosition: "200% 0" },
          "100%": { backgroundPosition: "-200% 0" },
        },
        /* Slide-over panels */
        "slide-in-right": {
          from: { transform: "translateX(100%)", opacity: "0" },
          to: { transform: "translateX(0)", opacity: "1" },
        },
        "slide-out-right": {
          from: { transform: "translateX(0)", opacity: "1" },
          to: { transform: "translateX(100%)", opacity: "0" },
        },
        "slide-in-left": {
          from: { transform: "translateX(-100%)" },
          to: { transform: "translateX(0)" },
        },
        "slide-out-left": {
          from: { transform: "translateX(0)" },
          to: { transform: "translateX(-100%)" },
        },
        /* Fade */
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "fade-out": {
          from: { opacity: "1" },
          to: { opacity: "0" },
        },
        /* Scale (for popovers, dropdowns) */
        "scale-in": {
          from: { opacity: "0", transform: "scale(0.95)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
        "scale-out": {
          from: { opacity: "1", transform: "scale(1)" },
          to: { opacity: "0", transform: "scale(0.95)" },
        },
        /* Toast slide */
        "toast-in": {
          from: { opacity: "0", transform: "translateX(100%) scale(0.95)" },
          to: { opacity: "1", transform: "translateX(0) scale(1)" },
        },
        "toast-out": {
          from: { opacity: "1", transform: "translateX(0) scale(1)" },
          to: { opacity: "0", transform: "translateX(100%) scale(0.95)" },
        },
        /* Pulse glow for presence indicator */
        "pulse-glow": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
        /* Drag bounce (spring) */
        "bounce-in": {
          "0%": { transform: "scale(0.95)", opacity: "0" },
          "60%": { transform: "scale(1.02)" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 200ms ease-out",
        "accordion-up": "accordion-up 200ms ease-out",
        skeleton: "skeleton 1.5s ease-in-out infinite",
        shimmer: "shimmer 1.5s ease-in-out infinite",
        "slide-in-right": "slide-in-right 200ms ease-out",
        "slide-out-right": "slide-out-right 200ms ease-in",
        "slide-in-left": "slide-in-left 300ms ease-out",
        "slide-out-left": "slide-out-left 300ms ease-out",
        "fade-in": "fade-in 150ms ease-out",
        "fade-out": "fade-out 150ms ease-in",
        "scale-in": "scale-in 150ms ease-out",
        "scale-out": "scale-out 150ms ease-in",
        "toast-in": "toast-in 300ms ease-out",
        "toast-out": "toast-out 300ms ease-in",
        "pulse-glow": "pulse-glow 2s ease-in-out infinite",
        "bounce-in": "bounce-in 300ms cubic-bezier(0.34, 1.56, 0.64, 1)",
      },

      /* ==============================================================
         SCREENS (Responsive Breakpoints)
         ============================================================== */
      screens: {
        xs: "480px",
        sm: "640px",
        md: "768px",
        lg: "1024px",
        xl: "1280px",
        "2xl": "1440px",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
