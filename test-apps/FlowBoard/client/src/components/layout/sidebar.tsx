"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import {
  Home,
  CheckSquare,
  BarChart3,
  Plus,
  ChevronsLeft,
  ChevronsRight,
  LogOut,
  Settings,
  User,
  Sun,
  Moon,
  FolderKanban,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/auth-context";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import { useProjects, type Project } from "@/hooks/use-projects";

// =============================================================================
// Navigation items
// =============================================================================

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: Home },
  { label: "My Tasks", href: "/tasks", icon: CheckSquare },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
];

// =============================================================================
// Project Color Palette
// =============================================================================

const PROJECT_COLORS: Record<string, string> = {
  red: "bg-red-500",
  orange: "bg-orange-500",
  yellow: "bg-yellow-500",
  green: "bg-green-500",
  blue: "bg-blue-500",
  indigo: "bg-indigo-500",
  violet: "bg-violet-500",
  pink: "bg-pink-500",
  teal: "bg-teal-500",
  cyan: "bg-cyan-500",
};

function getProjectDotClass(color: string): string {
  return PROJECT_COLORS[color] ?? "bg-violet-500";
}

// =============================================================================
// Sidebar Component
// =============================================================================

interface SidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
  onCreateProject: () => void;
  /** When true, sidebar is rendered inside a mobile sheet overlay */
  isMobileSheet?: boolean;
}

export function Sidebar({
  collapsed,
  onToggleCollapse,
  onCreateProject,
  isMobileSheet = false,
}: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const { projects, isLoading: projectsLoading } = useProjects();
  const { user, logout } = useAuth();

  // Derive user display info from auth context
  const displayName = user?.name ?? "User";
  const displayEmail = user?.email ?? "";
  const initials = displayName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------
  function handleLogout() {
    void logout();
  }

  function toggleTheme() {
    setTheme(theme === "dark" ? "light" : "dark");
  }

  // ---------------------------------------------------------------------------
  // Render helpers
  // ---------------------------------------------------------------------------
  function renderNavItem(item: NavItem) {
    const isActive =
      item.href === "/dashboard"
        ? pathname === "/dashboard"
        : pathname.startsWith(item.href);

    const Icon = item.icon;

    const link = (
      <Link
        href={item.href}
        className={cn(
          "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium",
          "motion-safe:transition-colors duration-fast",
          // Min 44px touch target on mobile (inside sheet)
          isMobileSheet && "min-h-[44px]",
          isActive
            ? "bg-surface-selected text-text-primary"
            : "text-text-secondary hover:bg-surface-hover hover:text-text-primary",
          collapsed && !isMobileSheet && "justify-center px-0",
        )}
      >
        <Icon className="h-4 w-4 shrink-0" />
        {(!collapsed || isMobileSheet) && <span className="truncate">{item.label}</span>}
      </Link>
    );

    if (collapsed) {
      return (
        <Tooltip key={item.href}>
          <TooltipTrigger asChild>{link}</TooltipTrigger>
          <TooltipContent side="right" sideOffset={8}>
            {item.label}
          </TooltipContent>
        </Tooltip>
      );
    }

    return <React.Fragment key={item.href}>{link}</React.Fragment>;
  }

  function renderProjectItem(project: Project) {
    const href = `/projects/${project.id}/board`;
    const isActive = pathname.startsWith(`/projects/${project.id}`);

    const link = (
      <Link
        href={href}
        className={cn(
          "flex items-center gap-3 rounded-md px-3 py-1.5 text-sm",
          "transition-colors duration-fast",
          isActive
            ? "bg-surface-selected text-text-primary"
            : "text-text-secondary hover:bg-surface-hover hover:text-text-primary",
          collapsed && "justify-center px-0",
        )}
      >
        <span
          className={cn(
            "h-2 w-2 shrink-0 rounded-full",
            getProjectDotClass(project.color),
          )}
        />
        {!collapsed && (
          <span className="truncate">{project.name}</span>
        )}
      </Link>
    );

    if (collapsed) {
      return (
        <Tooltip key={project.id}>
          <TooltipTrigger asChild>{link}</TooltipTrigger>
          <TooltipContent side="right" sideOffset={8}>
            {project.name}
          </TooltipContent>
        </Tooltip>
      );
    }

    return <React.Fragment key={project.id}>{link}</React.Fragment>;
  }

  // ---------------------------------------------------------------------------
  // Main render
  // ---------------------------------------------------------------------------
  return (
    <TooltipProvider delayDuration={200}>
      <aside
        className={cn(
          "flex h-full flex-col",
          "bg-surface-secondary border-r border-edge-subtle",
          "motion-safe:transition-[width] motion-safe:duration-200 motion-safe:ease-out",
          // Mobile sheet gets full sidebar width always
          isMobileSheet
            ? "w-sidebar"
            : cn(
                // Hidden on mobile (shown via sheet overlay instead)
                "hidden md:flex",
                // Tablet (md): starts collapsed 64px, expandable
                // Desktop (lg+): full width 240px, collapsible
                collapsed ? "w-sidebar-collapsed" : "md:w-sidebar-collapsed lg:w-sidebar",
                // When explicitly expanded on tablet, show full width overlay
                !collapsed && "md:w-sidebar",
              ),
        )}
      >
        {/* ============================================================
            Logo / Brand
            ============================================================ */}
        <div
          className={cn(
            "flex h-header items-center border-b border-edge-subtle shrink-0",
            collapsed ? "justify-center px-2" : "px-4",
          )}
        >
          <Link
            href="/dashboard"
            className="flex items-center gap-2.5 group"
          >
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary">
              <FolderKanban className="h-4 w-4 text-primary-foreground" />
            </div>
            {!collapsed && (
              <span className="font-heading text-lg font-bold tracking-tight text-text-primary">
                FlowBoard
              </span>
            )}
          </Link>
        </div>

        {/* ============================================================
            Navigation Links
            ============================================================ */}
        <div className={cn("flex flex-col gap-1 px-3 pt-4", collapsed && "px-2")}>
          {NAV_ITEMS.map(renderNavItem)}
        </div>

        <Separator className="mx-3 mt-4" />

        {/* ============================================================
            Projects Section
            ============================================================ */}
        <div className="flex flex-1 flex-col overflow-hidden pt-4">
          {!collapsed && (
            <div className="flex items-center justify-between px-4 pb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-text-quaternary">
                Projects
              </span>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-5 w-5 text-text-quaternary hover:text-text-primary"
                    onClick={onCreateProject}
                  >
                    <Plus className="h-3.5 w-3.5" />
                    <span className="sr-only">New Project</span>
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="right">New Project</TooltipContent>
              </Tooltip>
            </div>
          )}

          {collapsed && (
            <div className="flex justify-center pb-2">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 text-text-quaternary hover:text-text-primary"
                    onClick={onCreateProject}
                  >
                    <Plus className="h-4 w-4" />
                    <span className="sr-only">New Project</span>
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="right">New Project</TooltipContent>
              </Tooltip>
            </div>
          )}

          <ScrollArea className="flex-1 px-3">
            <div className={cn("flex flex-col gap-0.5", collapsed && "px-0")}>
              {projectsLoading ? (
                <>
                  {Array.from({ length: 4 }).map((_, i) => (
                    <div
                      key={i}
                      className={cn(
                        "flex items-center gap-3 px-3 py-1.5",
                        collapsed && "justify-center px-0",
                      )}
                    >
                      <Skeleton className="h-2 w-2 rounded-full" />
                      {!collapsed && <Skeleton className="h-3 w-24" />}
                    </div>
                  ))}
                </>
              ) : projects.length === 0 ? (
                !collapsed && (
                  <p className="px-3 py-2 text-xs text-text-quaternary">
                    No projects yet
                  </p>
                )
              ) : (
                projects.map(renderProjectItem)
              )}
            </div>
          </ScrollArea>
        </div>

        {/* ============================================================
            Bottom Section: Collapse Toggle, Theme, User
            ============================================================ */}
        <div
          className={cn(
            "mt-auto flex flex-col gap-1 border-t border-edge-subtle px-3 py-3",
            collapsed && "items-center px-2",
          )}
        >
          {/* Collapse toggle */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size={collapsed ? "icon" : "sm"}
                className={cn(
                  "text-text-tertiary hover:text-text-primary",
                  !collapsed && "w-full justify-start gap-3",
                )}
                onClick={onToggleCollapse}
              >
                {collapsed ? (
                  <ChevronsRight className="h-4 w-4" />
                ) : (
                  <>
                    <ChevronsLeft className="h-4 w-4" />
                    <span>Collapse</span>
                  </>
                )}
              </Button>
            </TooltipTrigger>
            {collapsed && (
              <TooltipContent side="right">Expand sidebar</TooltipContent>
            )}
          </Tooltip>

          {/* Theme toggle */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size={collapsed ? "icon" : "sm"}
                className={cn(
                  "text-text-tertiary hover:text-text-primary",
                  !collapsed && "w-full justify-start gap-3",
                )}
                onClick={toggleTheme}
              >
                {theme === "dark" ? (
                  <Sun className="h-4 w-4" />
                ) : (
                  <Moon className="h-4 w-4" />
                )}
                {!collapsed && (
                  <span>{theme === "dark" ? "Light mode" : "Dark mode"}</span>
                )}
              </Button>
            </TooltipTrigger>
            {collapsed && (
              <TooltipContent side="right">
                {theme === "dark" ? "Light mode" : "Dark mode"}
              </TooltipContent>
            )}
          </Tooltip>

          <Separator className="my-1" />

          {/* User dropdown */}
          <DropdownMenu>
            <Tooltip>
              <TooltipTrigger asChild>
                <DropdownMenuTrigger asChild>
                  <button
                    className={cn(
                      "flex w-full items-center gap-3 rounded-md px-2 py-1.5",
                      "text-sm text-text-secondary",
                      "hover:bg-surface-hover transition-colors duration-fast",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                      collapsed && "justify-center px-0",
                    )}
                  >
                    <Avatar size="sm">
                      {user?.avatarUrl && <AvatarImage src={user.avatarUrl} alt={displayName} />}
                      <AvatarFallback>{initials}</AvatarFallback>
                    </Avatar>
                    {!collapsed && (
                      <div className="flex flex-col items-start overflow-hidden">
                        <span className="truncate text-sm font-medium text-text-primary">
                          {displayName}
                        </span>
                        <span className="truncate text-xs text-text-quaternary">
                          {displayEmail}
                        </span>
                      </div>
                    )}
                  </button>
                </DropdownMenuTrigger>
              </TooltipTrigger>
              {collapsed && (
                <TooltipContent side="right">{displayName}</TooltipContent>
              )}
            </Tooltip>

            <DropdownMenuContent
              side={collapsed ? "right" : "top"}
              align="start"
              sideOffset={8}
              className="w-56"
            >
              <DropdownMenuLabel className="flex flex-col">
                <span className="text-sm font-medium text-text-primary">
                  {displayName}
                </span>
                <span className="text-xs font-normal text-text-tertiary">
                  {displayEmail}
                </span>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => router.push("/settings")}
              >
                <User className="mr-2 h-4 w-4" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => router.push("/settings")}
              >
                <Settings className="mr-2 h-4 w-4" />
                Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={handleLogout}
                className="text-destructive focus:text-destructive"
              >
                <LogOut className="mr-2 h-4 w-4" />
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </aside>
    </TooltipProvider>
  );
}
