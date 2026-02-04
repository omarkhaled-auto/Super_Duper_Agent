/**
 * FlowBoard — shadcn/ui Component Theme Customization Recipes
 *
 * This file provides class-variance-authority (CVA) variant definitions
 * for all core shadcn/ui components, customized to match the FlowBoard
 * design system.
 *
 * Usage: Import the variant config when creating/overriding shadcn components.
 *
 * Example:
 *   import { buttonVariants } from "@/lib/component-themes";
 *   const Button = forwardRef<HTMLButtonElement, ButtonProps>(({ variant, size, ...props }, ref) => (
 *     <button className={cn(buttonVariants({ variant, size }), props.className)} ref={ref} {...props} />
 *   ));
 */

import { cva, type VariantProps } from "class-variance-authority";

// ============================================================================
// BUTTON
// ============================================================================

/**
 * Button Variants
 *
 * primary    — Violet bg, white text. Main CTAs.
 * secondary  — Subtle bg, primary text. Secondary actions.
 * ghost      — Transparent bg, hover reveals surface. Toolbar buttons.
 * destructive — Red bg, white text. Delete, remove actions.
 * outline    — Bordered, transparent bg. Alternative secondary.
 * link       — Underlined text link appearance.
 */
export const buttonVariants = cva(
  [
    "inline-flex items-center justify-center gap-2",
    "whitespace-nowrap rounded-md font-medium",
    "ring-offset-background transition-all duration-fast",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
    "disabled:pointer-events-none disabled:opacity-50",
    "font-body",
  ].join(" "),
  {
    variants: {
      variant: {
        primary: [
          "bg-primary text-primary-foreground",
          "hover:bg-violet-hover",
          "active:bg-violet-active",
          "shadow-xs hover:shadow-sm",
        ].join(" "),
        secondary: [
          "bg-secondary text-secondary-foreground",
          "hover:bg-surface-hover",
          "border border-border",
        ].join(" "),
        ghost: [
          "text-text-secondary",
          "hover:bg-surface-hover hover:text-text-primary",
        ].join(" "),
        destructive: [
          "bg-destructive text-destructive-foreground",
          "hover:bg-destructive/90",
          "shadow-xs",
        ].join(" "),
        outline: [
          "border border-border bg-transparent",
          "text-text-primary",
          "hover:bg-surface-hover",
        ].join(" "),
        link: [
          "text-violet underline-offset-[2.5px] decoration-[1.5px]",
          "decoration-violet/40 hover:decoration-violet",
          "underline",
        ].join(" "),
      },
      size: {
        sm: "h-7 px-3 text-xs rounded-md",       // 28px
        md: "h-9 px-4 text-sm rounded-md",        // 36px — default
        lg: "h-11 px-5 text-base rounded-lg",     // 44px
        icon: "h-9 w-9 rounded-md",               // 36px square
        "icon-sm": "h-7 w-7 rounded-md",          // 28px square
        "icon-lg": "h-11 w-11 rounded-lg",        // 44px square
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  }
);

export type ButtonVariants = VariantProps<typeof buttonVariants>;

// ============================================================================
// CARD
// ============================================================================

/**
 * Card Variants
 *
 * default   — Standard card with subtle border and background.
 * elevated  — Card with shadow lift (dropdowns, modals).
 * ghost     — No border, no shadow. Used inside other containers.
 * interactive — Hoverable card (project cards, task list rows).
 */
export const cardVariants = cva(
  "rounded-lg font-body",
  {
    variants: {
      variant: {
        default: [
          "bg-card text-card-foreground",
          "border border-border-subtle",
          "shadow-card",
        ].join(" "),
        elevated: [
          "bg-surface-elevated text-card-foreground",
          "border border-border",
          "shadow-dropdown",
        ].join(" "),
        ghost: [
          "bg-transparent text-card-foreground",
        ].join(" "),
        interactive: [
          "bg-card text-card-foreground",
          "border border-border-subtle",
          "shadow-card",
          "transition-all duration-fast",
          "hover:shadow-card-hover hover:border-border",
          "cursor-pointer",
        ].join(" "),
      },
      padding: {
        none: "",
        sm: "p-3",      // 12px
        md: "p-4",      // 16px — default
        lg: "p-6",      // 24px
      },
    },
    defaultVariants: {
      variant: "default",
      padding: "md",
    },
  }
);

export type CardVariants = VariantProps<typeof cardVariants>;

// ============================================================================
// INPUT
// ============================================================================

/**
 * Input Variants
 *
 * Standardized input styling with focus ring, error state,
 * and consistent sizing.
 */
export const inputVariants = cva(
  [
    "flex w-full rounded-md font-body text-base",
    "bg-transparent",
    "border border-input",
    "ring-offset-background",
    "file:border-0 file:bg-transparent file:text-sm file:font-medium",
    "placeholder:text-text-quaternary",
    "transition-colors duration-fast",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
    "disabled:cursor-not-allowed disabled:opacity-50",
  ].join(" "),
  {
    variants: {
      inputSize: {
        sm: "h-7 px-2.5 text-xs",     // 28px
        md: "h-9 px-3 text-sm",        // 36px — default
        lg: "h-11 px-4 text-base",     // 44px
      },
      state: {
        default: "",
        error: "border-error focus-visible:ring-error",
        success: "border-success focus-visible:ring-success",
      },
    },
    defaultVariants: {
      inputSize: "md",
      state: "default",
    },
  }
);

export type InputVariants = VariantProps<typeof inputVariants>;

// ============================================================================
// BADGE
// ============================================================================

/**
 * Badge Variants
 *
 * priority  — Color-coded by priority level (urgent/high/medium/low).
 * status    — With colored dot prefix for kanban status.
 * label     — Custom color tag/label.
 * default   — Neutral badge.
 * outline   — Bordered badge with transparent bg.
 */
export const badgeVariants = cva(
  [
    "inline-flex items-center gap-1",
    "rounded-full font-medium font-body",
    "transition-colors duration-fast",
  ].join(" "),
  {
    variants: {
      variant: {
        default: "bg-secondary text-text-secondary",
        primary: "bg-violet-muted text-violet",
        outline: "border border-border text-text-secondary",
        success: "bg-success-muted text-success",
        warning: "bg-warning-muted text-warning",
        error: "bg-error-muted text-error",
        info: "bg-info-muted text-info",
      },
      size: {
        sm: "px-1.5 py-px text-[10px]",   // tiny
        md: "px-2 py-0.5 text-xs",         // default
        lg: "px-2.5 py-1 text-xs",         // larger
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
);

export type BadgeVariants = VariantProps<typeof badgeVariants>;

// ============================================================================
// AVATAR
// ============================================================================

/**
 * Avatar Sizes
 *
 * xs: 24px — inline mentions, tiny contexts
 * sm: 32px — task cards, compact lists
 * md: 40px — standard (comments, sidebar)
 * lg: 48px — profiles, large displays
 */
export const avatarVariants = cva(
  "relative flex shrink-0 overflow-hidden rounded-full",
  {
    variants: {
      size: {
        xs: "h-6 w-6 text-2xs",    // 24px
        sm: "h-8 w-8 text-xs",      // 32px
        md: "h-10 w-10 text-sm",    // 40px — default
        lg: "h-12 w-12 text-base",  // 48px
      },
    },
    defaultVariants: {
      size: "md",
    },
  }
);

export type AvatarVariants = VariantProps<typeof avatarVariants>;

// ============================================================================
// TOAST
// ============================================================================

/**
 * Toast Variants
 *
 * All toasts appear bottom-right, slide in from the right,
 * and have a colored left border per variant.
 */
export const toastVariants = cva(
  [
    "pointer-events-auto rounded-lg border px-4 py-3",
    "bg-surface-elevated",
    "shadow-dropdown",
    "animate-toast-in",
    "font-body text-sm",
  ].join(" "),
  {
    variants: {
      variant: {
        default: "border-border",
        success: "border-l-[3px] border-l-success border-border",
        error: "border-l-[3px] border-l-error border-border",
        warning: "border-l-[3px] border-l-warning border-border",
        info: "border-l-[3px] border-l-info border-border",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export type ToastVariants = VariantProps<typeof toastVariants>;

// ============================================================================
// SKELETON
// ============================================================================

/**
 * Skeleton loading placeholders.
 * Uses CSS shimmer animation defined in globals.css.
 */
export const skeletonVariants = cva(
  "skeleton",
  {
    variants: {
      shape: {
        text: "h-3 w-full rounded",          // text line
        title: "h-5 w-3/4 rounded",          // heading
        avatar: "rounded-full",               // avatar circle
        button: "h-9 w-24 rounded-md",       // button placeholder
        card: "h-32 w-full rounded-lg",       // full card
        thumbnail: "h-10 w-10 rounded-md",    // small image
      },
    },
    defaultVariants: {
      shape: "text",
    },
  }
);

export type SkeletonVariants = VariantProps<typeof skeletonVariants>;

// ============================================================================
// SIDEBAR ITEM
// ============================================================================

export const sidebarItemVariants = cva(
  [
    "flex items-center gap-3 rounded-md px-3 py-2",
    "text-sm font-body font-medium",
    "transition-colors duration-fast",
    "cursor-pointer",
  ].join(" "),
  {
    variants: {
      state: {
        default: "text-text-secondary hover:bg-surface-hover hover:text-text-primary",
        active: "bg-surface-selected text-text-primary",
        disabled: "text-text-quaternary pointer-events-none opacity-50",
      },
    },
    defaultVariants: {
      state: "default",
    },
  }
);

export type SidebarItemVariants = VariantProps<typeof sidebarItemVariants>;

// ============================================================================
// KANBAN CARD (CVA variant for React component)
// ============================================================================

export const kanbanCardVariants = cva(
  [
    "relative rounded-lg border font-body",
    "bg-card border-border-subtle",
    "shadow-card",
    "transition-all duration-fast",
    "hover:shadow-card-hover hover:border-border",
    "active:scale-[0.98]",
    "cursor-pointer",
  ].join(" "),
  {
    variants: {
      padding: {
        compact: "px-3 py-2",   // dense view
        default: "px-4 py-3",   // standard
      },
      dragging: {
        true: "opacity-50 cursor-grabbing",
        false: "",
      },
    },
    defaultVariants: {
      padding: "default",
      dragging: false,
    },
  }
);

export type KanbanCardVariants = VariantProps<typeof kanbanCardVariants>;
