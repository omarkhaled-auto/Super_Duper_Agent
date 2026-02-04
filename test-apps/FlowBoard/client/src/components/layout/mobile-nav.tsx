"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  BarChart3,
  Settings,
  CheckSquare,
} from "lucide-react";

import { cn } from "@/lib/utils";

// =============================================================================
// Mobile Navigation Items
// =============================================================================

interface MobileNavItem {
  label: string;
  href: string;
  icon: React.ElementType;
}

const MOBILE_NAV_ITEMS: MobileNavItem[] = [
  { label: "Home", href: "/dashboard", icon: Home },
  { label: "Tasks", href: "/tasks", icon: CheckSquare },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
  { label: "Settings", href: "/settings", icon: Settings },
];

// =============================================================================
// MobileNav Component -- Bottom navigation bar for mobile viewports (<768px)
//
// - Fixed to bottom of screen
// - 5 icons: Home, Projects, Tasks, Search, Settings
// - 44px minimum touch targets
// - Active state indicator (top bar + color)
// - Surface-secondary background with blur
// - Safe area padding for notched devices (iPhone etc.)
// - Only visible on mobile (<768px), hidden on tablet+
// =============================================================================

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav
      className={cn(
        // Only visible on mobile
        "fixed bottom-0 left-0 right-0 z-sticky",
        "md:hidden",
        // Layout
        "flex items-stretch justify-around",
        // Height: 56px nav + safe area inset
        "h-14 border-t border-edge-subtle",
        // Frosted glass background
        "bg-surface-secondary/95 backdrop-blur-md",
        // Safe area for notched devices (iOS)
        "pb-[env(safe-area-inset-bottom,0px)]",
      )}
      role="navigation"
      aria-label="Mobile navigation"
    >
      {MOBILE_NAV_ITEMS.map((item) => {
        const Icon = item.icon;
        const isActive =
          item.href === "/dashboard"
            ? pathname === "/dashboard"
            : pathname.startsWith(item.href);

        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              // Touch target: min 44x44px
              "relative flex flex-col items-center justify-center",
              "min-w-[44px] min-h-[44px] py-1 px-2",
              // Typography
              "text-[10px] font-medium leading-tight",
              // Transition
              "motion-safe:transition-colors duration-fast",
              // Active / inactive states
              isActive
                ? "text-primary"
                : "text-text-quaternary active:text-text-secondary",
            )}
            aria-current={isActive ? "page" : undefined}
          >
            {/* Active indicator bar at top */}
            {isActive && (
              <span
                className={cn(
                  "absolute top-0 left-1/2 -translate-x-1/2",
                  "h-0.5 w-6 rounded-full bg-primary",
                  "motion-safe:animate-in motion-safe:fade-in motion-safe:duration-200",
                )}
                aria-hidden="true"
              />
            )}

            <Icon
              className={cn(
                "h-5 w-5 mb-0.5",
                isActive ? "text-primary" : "text-text-tertiary",
              )}
              aria-hidden="true"
            />
            <span className="select-none">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
