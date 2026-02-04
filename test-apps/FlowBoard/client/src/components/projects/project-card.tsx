"use client";

import React from "react";
import Link from "next/link";
import {
  FolderKanban,
  Layers,
  Rocket,
  Bug,
  Lightbulb,
  Globe,
  Smartphone,
  Shield,
  Zap,
  BookOpen,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import type { Project } from "@/hooks/use-projects";

// =============================================================================
// Icon mapping for project icons
// =============================================================================

const ICON_MAP: Record<string, React.ElementType> = {
  folder: FolderKanban,
  layers: Layers,
  rocket: Rocket,
  bug: Bug,
  lightbulb: Lightbulb,
  globe: Globe,
  mobile: Smartphone,
  shield: Shield,
  zap: Zap,
  book: BookOpen,
};

function getProjectIcon(icon?: string): React.ElementType {
  if (icon && ICON_MAP[icon]) return ICON_MAP[icon];
  return FolderKanban;
}

// =============================================================================
// Color accent mapping
// =============================================================================

const COLOR_BG_MAP: Record<string, string> = {
  red: "bg-red-500/10 text-red-400",
  orange: "bg-orange-500/10 text-orange-400",
  yellow: "bg-yellow-500/10 text-yellow-400",
  green: "bg-green-500/10 text-green-400",
  blue: "bg-blue-500/10 text-blue-400",
  indigo: "bg-indigo-500/10 text-indigo-400",
  violet: "bg-violet-500/10 text-violet-400",
  pink: "bg-pink-500/10 text-pink-400",
  teal: "bg-teal-500/10 text-teal-400",
  cyan: "bg-cyan-500/10 text-cyan-400",
};

const COLOR_BAR_MAP: Record<string, string> = {
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

function getIconContainerClass(color: string): string {
  return COLOR_BG_MAP[color] ?? "bg-violet-500/10 text-violet-400";
}

function getBarClass(color: string): string {
  return COLOR_BAR_MAP[color] ?? "bg-violet-500";
}

// =============================================================================
// ProjectCard Component
// =============================================================================

interface ProjectCardProps {
  project: Project;
}

export function ProjectCard({ project }: ProjectCardProps) {
  const Icon = getProjectIcon(project.icon);
  const total = project.taskCounts?.total ?? 0;
  const completed = project.taskCounts?.completed ?? 0;
  const progressPercent = total > 0 ? Math.round((completed / total) * 100) : 0;

  return (
    <Link
      href={`/projects/${project.id}/board`}
      className="group block"
    >
      <Card
        className={cn(
          "relative overflow-hidden",
          "transition-all duration-200",
          "hover:shadow-card-hover hover:border-edge-strong",
          "group-focus-visible:ring-2 group-focus-visible:ring-ring group-focus-visible:ring-offset-2 group-focus-visible:ring-offset-background",
        )}
      >
        {/* Color accent bar at top */}
        <div className={cn("h-0.5", getBarClass(project.color))} />

        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div
                className={cn(
                  "flex h-9 w-9 items-center justify-center rounded-lg",
                  getIconContainerClass(project.color),
                )}
              >
                <Icon className="h-4.5 w-4.5" />
              </div>
              <div className="min-w-0">
                <h3 className="font-heading text-sm font-semibold text-text-primary truncate group-hover:text-primary transition-colors duration-fast">
                  {project.name}
                </h3>
                {project.description && (
                  <p className="text-xs text-text-tertiary line-clamp-1 mt-0.5">
                    {project.description}
                  </p>
                )}
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent className="pt-0">
          {/* Progress */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-text-tertiary">
                {completed}/{total} tasks
              </span>
              <span className="text-xs font-medium text-text-secondary">
                {progressPercent}%
              </span>
            </div>
            <div className="h-1 w-full rounded-full bg-surface-quaternary overflow-hidden">
              <div
                className={cn(
                  "h-full rounded-full transition-all duration-slow",
                  getBarClass(project.color),
                )}
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          {/* Member avatars */}
          {project.members && project.members.length > 0 && (
            <div className="flex items-center mt-3 -space-x-1.5">
              {project.members.slice(0, 4).map((member) => {
                const memberInitials = member.name
                  .split(" ")
                  .map((n) => n[0])
                  .join("")
                  .toUpperCase()
                  .slice(0, 2);

                return (
                  <Avatar
                    key={member.id}
                    size="xs"
                    className="border-2 border-card"
                  >
                    {member.avatar && (
                      <AvatarImage src={member.avatar} alt={member.name} />
                    )}
                    <AvatarFallback>{memberInitials}</AvatarFallback>
                  </Avatar>
                );
              })}
              {project.members.length > 4 && (
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-surface-quaternary text-2xs font-medium text-text-tertiary border-2 border-card">
                  +{project.members.length - 4}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}

// =============================================================================
// ProjectCard Skeleton -- Loading placeholder
// =============================================================================

export function ProjectCardSkeleton() {
  return (
    <Card className="overflow-hidden">
      <div className="h-0.5 bg-surface-tertiary" />
      <CardHeader className="pb-3">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg animate-skeleton bg-surface-tertiary" />
          <div className="space-y-1.5 flex-1">
            <div className="h-3.5 w-28 rounded animate-skeleton bg-surface-tertiary" />
            <div className="h-2.5 w-40 rounded animate-skeleton bg-surface-tertiary" />
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-2">
          <div className="flex justify-between">
            <div className="h-2.5 w-16 rounded animate-skeleton bg-surface-tertiary" />
            <div className="h-2.5 w-8 rounded animate-skeleton bg-surface-tertiary" />
          </div>
          <div className="h-1 w-full rounded-full bg-surface-tertiary" />
        </div>
        <div className="flex mt-3 -space-x-1.5">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="h-6 w-6 rounded-full animate-skeleton bg-surface-tertiary border-2 border-card"
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
