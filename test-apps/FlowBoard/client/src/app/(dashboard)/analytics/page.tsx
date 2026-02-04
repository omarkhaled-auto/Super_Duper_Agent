"use client";

import * as React from "react";
import { BarChart3, TrendingUp } from "lucide-react";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ChartCard } from "@/components/analytics/chart-card";
import { TasksOverTimeChart } from "@/components/analytics/tasks-over-time-chart";
import { TasksByStatusChart } from "@/components/analytics/tasks-by-status-chart";
import { TasksByPriorityChart } from "@/components/analytics/tasks-by-priority-chart";
import { VelocityChart } from "@/components/analytics/velocity-chart";
import { useProjects } from "@/hooks/use-projects";
import { useAnalytics } from "@/hooks/use-analytics";

// =============================================================================
// Analytics Page
// =============================================================================

/**
 * Analytics dashboard showing project-level metrics in four chart cards:
 *   1. Tasks Over Time   -- Area chart (last 30 days)
 *   2. Tasks by Status   -- Donut chart (status distribution)
 *   3. Tasks by Priority -- Bar chart (priority distribution)
 *   4. Team Velocity     -- Line chart (last 8 weeks)
 *
 * A project selector dropdown at the top lets users pick which project
 * to analyze. If no project is selected, a prompt is shown.
 */
export default function AnalyticsPage() {
  const { projects, isLoading: projectsLoading } = useProjects();
  const [selectedProjectId, setSelectedProjectId] = React.useState<
    string | null
  >(null);

  const { data, isLoading: analyticsLoading, error } = useAnalytics(
    selectedProjectId
  );

  // Auto-select the first project once loaded
  React.useEffect(() => {
    if (!selectedProjectId && projects.length > 0) {
      setSelectedProjectId(projects[0].id);
    }
  }, [projects, selectedProjectId]);

  const isLoading = projectsLoading || analyticsLoading;

  return (
    <div className="p-6 space-y-6 max-w-dashboard mx-auto">
      {/* ---- Page Header ---- */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-heading font-bold tracking-tight text-text-primary">
            Analytics
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Project performance metrics and task insights
          </p>
        </div>

        {/* ---- Project Selector ---- */}
        <div className="w-full sm:w-[260px]">
          <Select
            value={selectedProjectId ?? ""}
            onValueChange={(value) => setSelectedProjectId(value)}
            disabled={projectsLoading}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select a project" />
            </SelectTrigger>
            <SelectContent>
              {projects.map((project) => (
                <SelectItem key={project.id} value={project.id}>
                  <div className="flex items-center gap-2">
                    <span
                      className="h-2.5 w-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: project.color || "#8B5CF6" }}
                    />
                    <span className="truncate">{project.name}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* ---- Empty State ---- */}
      {!selectedProjectId && !projectsLoading && (
        <EmptyState />
      )}

      {/* ---- Error State ---- */}
      {error && (
        <div className="rounded-lg border border-error/30 bg-error-muted p-4 text-sm text-error">
          {error}
        </div>
      )}

      {/* ---- Charts Grid ---- */}
      {(selectedProjectId || isLoading) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <ChartCard
            title="Tasks Over Time"
            description="Task activity across the last 30 days"
            isLoading={isLoading}
          >
            {data?.tasksOverTime && (
              <TasksOverTimeChart data={data.tasksOverTime} />
            )}
          </ChartCard>

          <ChartCard
            title="Tasks by Status"
            description="Current distribution across workflow stages"
            isLoading={isLoading}
          >
            {data?.tasksByStatus && (
              <TasksByStatusChart data={data.tasksByStatus} />
            )}
          </ChartCard>

          <ChartCard
            title="Tasks by Priority"
            description="Breakdown by priority level"
            isLoading={isLoading}
          >
            {data?.tasksByPriority && (
              <TasksByPriorityChart data={data.tasksByPriority} />
            )}
          </ChartCard>

          <ChartCard
            title="Team Velocity"
            description="Tasks completed per week over the last 8 weeks"
            isLoading={isLoading}
          >
            {data?.velocity && <VelocityChart data={data.velocity} />}
          </ChartCard>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Empty State Component
// =============================================================================

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="flex items-center justify-center h-16 w-16 rounded-2xl bg-violet-subtle mb-4">
        <BarChart3 className="h-8 w-8 text-violet" />
      </div>
      <h3 className="text-lg font-heading font-semibold text-text-primary mb-1">
        Select a project to view analytics
      </h3>
      <p className="text-sm text-text-tertiary max-w-md">
        Choose a project from the dropdown above to see task metrics,
        status distribution, priority breakdown, and team velocity charts.
      </p>
    </div>
  );
}
