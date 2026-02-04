"use client";

import * as React from "react";
import { ThemeProvider as NextThemesProvider } from "next-themes";

/**
 * ThemeProvider -- FlowBoard Design System
 *
 * Wraps next-themes to provide dark/light/system theme switching.
 * - attribute="class"  => toggles .dark / .light on <html>
 * - defaultTheme="dark" => dark mode is the primary experience
 * - enableSystem        => respects OS-level prefers-color-scheme
 * - storageKey          => persists preference to localStorage
 */
export function ThemeProvider({
  children,
  ...props
}: React.ComponentProps<typeof NextThemesProvider>) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="dark"
      enableSystem={true}
      storageKey="flowboard-theme"
      disableTransitionOnChange={false}
      {...props}
    >
      {children}
    </NextThemesProvider>
  );
}
