"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { ProjectProvider, useProjectContext } from "@/contexts/project-context";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  LayoutGrid,
  List,
  Settings,
  AlertTriangle,
  ArrowLeft,
  Folder,
} from "lucide-react";
import { getProjectIcon } from "@/components/projects/icon-picker";

// =============================================================================
// Project Layout — wraps all /projects/:id/* pages
//
// - Fetches project data via ProjectProvider context
// - Renders project header with name, view-toggle tabs, settings link
// - Shows loading skeleton, 404 / error states
// =============================================================================

interface ProjectLayoutProps {
  children: React.ReactNode;
  params: { projectId: string };
}

export default function ProjectLayout({
  children,
  params,
}: ProjectLayoutProps) {
  return (
    <ProjectProvider projectId={params.projectId}>
      <ProjectLayoutInner projectId={params.projectId}>
        {children}
      </ProjectLayoutInner>
    </ProjectProvider>
  );
}

// -----------------------------------------------------------------------------
// Inner layout (has access to ProjectContext)
// -----------------------------------------------------------------------------

function ProjectLayoutInner({
  children,
  projectId,
}: {
  children: React.ReactNode;
  projectId: string;
}) {
  const { project, isLoading, error, errorStatus } = useProjectContext();
  const pathname = usePathname();

  // ---- Loading skeleton ----
  if (isLoading) {
    return (
      <div className="flex flex-col h-full">
        <ProjectHeaderSkeleton />
        <div className="flex-1 overflow-hidden p-6">
          <div className="space-y-4">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-4 w-96" />
            <div className="grid grid-cols-3 gap-4 mt-6">
              <Skeleton className="h-32" />
              <Skeleton className="h-32" />
              <Skeleton className="h-32" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ---- 404 / Error states ----
  if (error || !project) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 text-center px-6">
        <div className="rounded-full bg-surface-tertiary p-4">
          <AlertTriangle
            className="h-8 w-8 text-text-tertiary"
            aria-hidden="true"
          />
        </div>
        <div>
          <h2 className="text-lg font-semibold font-heading text-text-primary">
            {errorStatus === 404
              ? "Project not found"
              : errorStatus === 403
                ? "Access denied"
                : "Something went wrong"}
          </h2>
          <p className="mt-1 text-sm text-text-tertiary max-w-md">
            {errorStatus === 404
              ? "The project you're looking for doesn't exist or has been deleted."
              : errorStatus === 403
                ? "You don't have permission to view this project."
                : error ?? "An unexpected error occurred while loading the project."}
          </p>
        </div>
        <Button variant="secondary" asChild>
          <Link href="/dashboard">
            <ArrowLeft className="h-4 w-4 mr-1.5" aria-hidden="true" />
            Back to dashboard
          </Link>
        </Button>
      </div>
    );
  }

  // ---- Navigation tabs ----
  const basePath = `/projects/${projectId}`;
  const navItems = [
    {
      label: "Board",
      href: `${basePath}/board`,
      icon: LayoutGrid,
      match: /\/board$/,
    },
    {
      label: "List",
      href: `${basePath}/list`,
      icon: List,
      match: /\/list$/,
    },
    {
      label: "Settings",
      href: `${basePath}/settings`,
      icon: Settings,
      match: /\/settings$/,
    },
  ];

  // Resolve the project icon
  const ProjectIcon = getProjectIcon(project.icon) ?? Folder;

  return (
    <div className="flex flex-col h-full">
      {/* Project header */}
      <header className="shrink-0 border-b border-border-subtle bg-surface-secondary px-6">
        <div className="flex items-center gap-4 pt-4 pb-2">
          {/* Project icon */}
          <div
            className="flex items-center justify-center h-9 w-9 rounded-lg shrink-0"
            style={{
              backgroundColor: project.color
                ? `${project.color}20`
                : undefined,
            }}
          >
            <ProjectIcon
              className="h-5 w-5"
              style={{ color: project.color ?? undefined }}
              aria-hidden="true"
            />
          </div>

          {/* Project name */}
          <div className="min-w-0 flex-1">
            <h1 className="text-lg font-semibold font-heading text-text-primary truncate">
              {project.name}
            </h1>
            {project.description && (
              <p className="text-xs text-text-tertiary truncate">
                {project.description}
              </p>
            )}
          </div>
        </div>

        {/* View toggle navigation */}
        <nav
          className="flex items-center gap-1 -mb-px"
          aria-label="Project views"
        >
          {navItems.map((item) => {
            const isActive = item.match.test(pathname);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "inline-flex items-center gap-1.5 px-3 pb-2.5 pt-2 text-sm font-medium font-body",
                  "border-b-2 -mb-[1px] transition-all duration-fast",
                  isActive
                    ? "text-text-primary border-b-primary"
                    : "text-text-tertiary border-transparent hover:text-text-primary hover:border-b-border",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ring-offset-background rounded-t-md",
                )}
                aria-current={isActive ? "page" : undefined}
              >
                <Icon className="h-4 w-4" aria-hidden="true" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </header>

      {/* Page content */}
      <div className="flex-1 overflow-hidden">{children}</div>
    </div>
  );
}

// -----------------------------------------------------------------------------
// Loading skeleton for the header
// -----------------------------------------------------------------------------

function ProjectHeaderSkeleton() {
  return (
    <header className="shrink-0 border-b border-border-subtle bg-surface-secondary px-6">
      <div className="flex items-center gap-4 pt-4 pb-2">
        <Skeleton className="h-9 w-9 rounded-lg" />
        <div className="space-y-1.5 flex-1">
          <Skeleton className="h-5 w-40" />
          <Skeleton className="h-3 w-64" />
        </div>
      </div>
      <div className="flex items-center gap-1 pb-2.5 pt-2">
        <Skeleton className="h-5 w-16" />
        <Skeleton className="h-5 w-12 ml-2" />
        <Skeleton className="h-5 w-18 ml-2" />
      </div>
    </header>
  );
}
