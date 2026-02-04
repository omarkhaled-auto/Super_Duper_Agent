"use client";

import * as React from "react";
import { Moon, Sun, Monitor } from "lucide-react";
import { useTheme } from "next-themes";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

/**
 * ThemeToggle -- Compact theme switcher for sidebar placement.
 *
 * Displays a Sun/Moon icon button that opens a dropdown with three options:
 *   Light, Dark, System.
 *
 * The icon smoothly transitions between Sun (light) and Moon (dark).
 * Uses next-themes useTheme hook for state management.
 */
export function ThemeToggle({ className }: { className?: string }) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  // Avoid hydration mismatch -- only render icon after mount
  React.useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className={cn(
            "h-8 w-8 rounded-md text-text-secondary hover:text-text-primary",
            className
          )}
          aria-label="Toggle theme"
        >
          {mounted ? (
            <>
              <Sun
                className={cn(
                  "h-4 w-4 transition-all duration-200",
                  theme === "light"
                    ? "rotate-0 scale-100"
                    : "-rotate-90 scale-0"
                )}
                style={{
                  position: theme === "light" ? "relative" : "absolute",
                }}
              />
              <Moon
                className={cn(
                  "h-4 w-4 transition-all duration-200",
                  theme === "dark" ? "rotate-0 scale-100" : "rotate-90 scale-0"
                )}
                style={{
                  position: theme === "dark" ? "relative" : "absolute",
                }}
              />
              {theme === "system" && (
                <Monitor className="h-4 w-4 transition-all duration-200" />
              )}
            </>
          ) : (
            <div className="h-4 w-4" />
          )}
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="min-w-[140px]">
        <DropdownMenuItem
          onClick={() => setTheme("light")}
          className={cn(
            "gap-2 cursor-pointer",
            theme === "light" && "text-violet"
          )}
        >
          <Sun className="h-4 w-4" />
          <span>Light</span>
          {theme === "light" && (
            <span className="ml-auto text-xs text-text-tertiary">Active</span>
          )}
        </DropdownMenuItem>

        <DropdownMenuItem
          onClick={() => setTheme("dark")}
          className={cn(
            "gap-2 cursor-pointer",
            theme === "dark" && "text-violet"
          )}
        >
          <Moon className="h-4 w-4" />
          <span>Dark</span>
          {theme === "dark" && (
            <span className="ml-auto text-xs text-text-tertiary">Active</span>
          )}
        </DropdownMenuItem>

        <DropdownMenuItem
          onClick={() => setTheme("system")}
          className={cn(
            "gap-2 cursor-pointer",
            theme === "system" && "text-violet"
          )}
        >
          <Monitor className="h-4 w-4" />
          <span>System</span>
          {theme === "system" && (
            <span className="ml-auto text-xs text-text-tertiary">Active</span>
          )}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
