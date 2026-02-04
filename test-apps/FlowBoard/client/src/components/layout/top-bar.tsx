"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ChevronRight,
  Search,
  LayoutGrid,
  List,
  Menu,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

// =============================================================================
// Breadcrumb path parser
// =============================================================================

interface BreadcrumbItem {
  label: string;
  href: string;
}

function parseBreadcrumbs(pathname: string): BreadcrumbItem[] {
  const segments = pathname.split("/").filter(Boolean);
  const crumbs: BreadcrumbItem[] = [];

  // Always start with Dashboard as the root
  crumbs.push({ label: "Dashboard", href: "/dashboard" });

  const labelMap: Record<string, string> = {
    projects: "Projects",
    tasks: "My Tasks",
    analytics: "Analytics",
    settings: "Settings",
    board: "Board",
    list: "List",
  };

  let currentPath = "";

  segments.forEach((segment) => {
    currentPath += `/${segment}`;

    // Skip the dashboard segment (already in crumbs)
    if (segment === "dashboard") return;

    // Skip the "projects" segment itself
    if (segment === "projects") return;

    // Detect project IDs (UUID-like or long alphanumeric)
    const isId = segment.length > 8 && /^[a-f0-9-]+$/i.test(segment);

    if (isId) {
      crumbs.push({
        label: "Project",
        href: `${currentPath}/board`,
      });
      return;
    }

    const label =
      labelMap[segment] ??
      segment.charAt(0).toUpperCase() + segment.slice(1);

    crumbs.push({ label, href: currentPath });
  });

  return crumbs;
}

// =============================================================================
// TopBar Component
// =============================================================================

interface TopBarProps {
  /** Callback to open the mobile sidebar sheet */
  onMobileMenuOpen: () => void;
  /** Callback to open the command palette */
  onOpenCommandPalette?: () => void;
  /** Optional project name override for the breadcrumb */
  projectName?: string;
}

export function TopBar({ onMobileMenuOpen, onOpenCommandPalette, projectName }: TopBarProps) {
  const pathname = usePathname();
  const breadcrumbs = parseBreadcrumbs(pathname);

  // Determine if we're inside a project view (show view switcher)
  const isProjectView = pathname.includes("/projects/");

  // Extract project ID for view switcher links
  const projectIdMatch = pathname.match(/\/projects\/([^/]+)/);
  const projectId = projectIdMatch?.[1];

  // Replace "Project" breadcrumb label with actual project name
  const resolvedBreadcrumbs = breadcrumbs.map((crumb) =>
    crumb.label === "Project" && projectName
      ? { ...crumb, label: projectName }
      : crumb,
  );

  // Determine the active view (board or list)
  const isListView = pathname.endsWith("/list");
  const isBoardView = pathname.endsWith("/board") || (isProjectView && !isListView && !pathname.endsWith("/settings"));

  return (
    <TooltipProvider delayDuration={200}>
      <header
        className={cn(
          "flex h-header items-center justify-between gap-4",
          "border-b border-edge-subtle bg-surface-primary",
          "px-4 lg:px-6 shrink-0",
        )}
      >
        {/* ---- Left: Mobile menu + Breadcrumbs ---- */}
        <div className="flex items-center gap-3 min-w-0">
          {/* Mobile hamburger -- visible below md, 44px touch target */}
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden text-text-secondary min-w-[44px] min-h-[44px]"
            onClick={onMobileMenuOpen}
          >
            <Menu className="h-5 w-5" />
            <span className="sr-only">Open menu</span>
          </Button>

          {/* Breadcrumbs */}
          <nav
            aria-label="Breadcrumb"
            className="flex items-center gap-1 min-w-0"
          >
            {resolvedBreadcrumbs.map((crumb, index) => (
              <React.Fragment key={crumb.href}>
                {index > 0 && (
                  <ChevronRight className="h-3.5 w-3.5 shrink-0 text-text-quaternary" />
                )}
                {index === resolvedBreadcrumbs.length - 1 ? (
                  <span className="truncate text-sm font-medium text-text-primary">
                    {crumb.label}
                  </span>
                ) : (
                  <Link
                    href={crumb.href}
                    className="truncate text-sm text-text-tertiary hover:text-text-primary transition-colors duration-fast"
                  >
                    {crumb.label}
                  </Link>
                )}
              </React.Fragment>
            ))}
          </nav>
        </div>

        {/* ---- Right: View switcher + Search ---- */}
        <div className="flex items-center gap-2">
          {/* View switcher -- only inside a project */}
          {isProjectView && projectId && (
            <div className="hidden sm:flex items-center gap-0.5 rounded-md bg-surface-secondary p-0.5">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Link
                    href={`/projects/${projectId}/board`}
                    className={cn(
                      "flex items-center gap-1.5 rounded-sm px-2.5 py-1 text-xs font-medium",
                      "transition-colors duration-fast",
                      isBoardView
                        ? "bg-surface-hover text-text-primary shadow-xs"
                        : "text-text-tertiary hover:text-text-secondary",
                    )}
                  >
                    <LayoutGrid className="h-3.5 w-3.5" />
                    Board
                  </Link>
                </TooltipTrigger>
                <TooltipContent>Board view</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Link
                    href={`/projects/${projectId}/list`}
                    className={cn(
                      "flex items-center gap-1.5 rounded-sm px-2.5 py-1 text-xs font-medium",
                      "transition-colors duration-fast",
                      isListView
                        ? "bg-surface-hover text-text-primary shadow-xs"
                        : "text-text-tertiary hover:text-text-secondary",
                    )}
                  >
                    <List className="h-3.5 w-3.5" />
                    List
                  </Link>
                </TooltipTrigger>
                <TooltipContent>List view</TooltipContent>
              </Tooltip>
            </div>
          )}

          {/* Search trigger — opens command palette */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="gap-2 text-text-tertiary hover:text-text-primary"
                onClick={onOpenCommandPalette}
              >
                <Search className="h-4 w-4" />
                <span className="hidden lg:inline text-xs text-text-quaternary">
                  Search...
                </span>
                <kbd className="hidden lg:inline-flex h-5 items-center gap-0.5 rounded border border-edge-subtle bg-surface-secondary px-1.5 font-mono text-[10px] text-text-quaternary">
                  <span className="text-xs">&#8984;</span>K
                </kbd>
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              Search <kbd className="ml-1 font-mono text-[10px]">Cmd+K</kbd>
            </TooltipContent>
          </Tooltip>
        </div>
      </header>
    </TooltipProvider>
  );
}
