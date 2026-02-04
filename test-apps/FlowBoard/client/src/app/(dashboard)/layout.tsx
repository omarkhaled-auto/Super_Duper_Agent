"use client";

import React, { useState, useCallback, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { AuthProvider } from "@/contexts/auth-context";
import { SocketProvider } from "@/contexts/socket-context";
import { Sidebar } from "@/components/layout/sidebar";
import { TopBar } from "@/components/layout/top-bar";
import { MobileNav } from "@/components/layout/mobile-nav";
import { CreateProjectDialog } from "@/components/projects/create-project-dialog";
import { CommandPalette } from "@/components/search/command-palette";
import { TaskDetailPanel } from "@/components/task/task-detail-panel";
import { useKeyboardShortcuts } from "@/hooks/use-keyboard-shortcuts";
import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";

// =============================================================================
// DashboardLayout -- Application shell with sidebar, top bar, and content area
//
// Responsive behavior:
//   Mobile  (<768px):  Sidebar hidden, content full-width, bottom nav visible
//   Tablet  (768-1023px): Sidebar collapsed (64px) by default, expandable
//   Desktop (1024px+): Sidebar full-width (240px), collapsible
// =============================================================================

const SIDEBAR_COLLAPSED_KEY = "flowboard_sidebar_collapsed";

function getInitialCollapsed(): boolean {
  if (typeof window === "undefined") return false;
  return localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === "true";
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthProvider>
      <SocketProvider>
        <DashboardShell>{children}</DashboardShell>
      </SocketProvider>
    </AuthProvider>
  );
}

// =============================================================================
// DashboardShell -- Inner component with access to AuthProvider & SocketProvider
// =============================================================================

function DashboardShell({
  children,
}: {
  children: React.ReactNode;
}) {
  // ---------------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------------
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [createProjectOpen, setCreateProjectOpen] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  const router = useRouter();
  const pathname = usePathname();

  // Hydrate collapsed state from localStorage after mount
  useEffect(() => {
    setSidebarCollapsed(getInitialCollapsed());
  }, []);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

  // ---------------------------------------------------------------------------
  // Command palette + keyboard shortcut handlers
  // ---------------------------------------------------------------------------
  const handleOpenCommandPalette = useCallback(() => {
    setCommandPaletteOpen(true);
  }, []);

  const handleBoardView = useCallback(() => {
    const projectMatch = pathname.match(/\/projects\/([^/]+)/);
    if (projectMatch) {
      router.push(`/projects/${projectMatch[1]}/board`);
    }
  }, [pathname, router]);

  const handleListView = useCallback(() => {
    const projectMatch = pathname.match(/\/projects\/([^/]+)/);
    if (projectMatch) {
      router.push(`/projects/${projectMatch[1]}/list`);
    }
  }, [pathname, router]);

  // Register global keyboard shortcuts
  useKeyboardShortcuts({
    onOpenCommandPalette: handleOpenCommandPalette,
    onBoardView: handleBoardView,
    onListView: handleListView,
  });

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------
  const handleToggleCollapse = useCallback(() => {
    setSidebarCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(next));
      return next;
    });
  }, []);

  const handleMobileMenuOpen = useCallback(() => {
    setMobileMenuOpen(true);
  }, []);

  const handleCreateProject = useCallback(() => {
    setCreateProjectOpen(true);
  }, []);

  const handleProjectCreated = useCallback(() => {
    // The useProjects hook will refetch via its own mechanism.
    // We could trigger a global event or use a context here.
  }, []);

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* ---- Desktop Sidebar (hidden on mobile) ---- */}
      <div className="hidden md:block shrink-0">
        <Sidebar
          collapsed={sidebarCollapsed}
          onToggleCollapse={handleToggleCollapse}
          onCreateProject={handleCreateProject}
        />
      </div>

      {/* ---- Mobile Sidebar Sheet (slides from left on <768px) ---- */}
      <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
        <SheetContent side="left" className="w-sidebar p-0">
          <SheetTitle className="sr-only">Navigation Menu</SheetTitle>
          <SheetDescription className="sr-only">
            Main navigation menu for FlowBoard
          </SheetDescription>
          <Sidebar
            collapsed={false}
            isMobileSheet
            onToggleCollapse={() => setMobileMenuOpen(false)}
            onCreateProject={() => {
              setMobileMenuOpen(false);
              setCreateProjectOpen(true);
            }}
          />
        </SheetContent>
      </Sheet>

      {/* ---- Main Content Area ---- */}
      <div className="flex flex-1 flex-col overflow-hidden min-w-0">
        {/* Top bar */}
        <TopBar
          onMobileMenuOpen={handleMobileMenuOpen}
          onOpenCommandPalette={handleOpenCommandPalette}
        />

        {/* Scrollable content area */}
        <main
          className={cn(
            "flex-1 overflow-y-auto",
            "bg-background",
            // Bottom padding for mobile nav (56px nav + safe area inset)
            // On tablet+ no bottom padding needed
            "pb-[calc(3.5rem+env(safe-area-inset-bottom,0px))] md:pb-0",
          )}
        >
          {children}
        </main>
      </div>

      {/* ---- Mobile Bottom Nav ---- */}
      <MobileNav />

      {/* ---- Create Project Dialog ---- */}
      <CreateProjectDialog
        open={createProjectOpen}
        onOpenChange={setCreateProjectOpen}
        onProjectCreated={handleProjectCreated}
      />

      {/* ---- Task Detail Panel (slide-over, driven by Zustand store) ---- */}
      <TaskDetailPanel />

      {/* ---- Command Palette (Cmd+K) ---- */}
      <CommandPalette
        open={commandPaletteOpen}
        onOpenChange={setCommandPaletteOpen}
      />
    </div>
  );
}
