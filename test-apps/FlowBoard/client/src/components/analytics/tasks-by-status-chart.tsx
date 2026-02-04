"use client";

import * as React from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { useTheme } from "next-themes";

// =============================================================================
// Types
// =============================================================================

export interface TasksByStatusDataPoint {
  status: string;
  count: number;
}

interface TasksByStatusChartProps {
  data: TasksByStatusDataPoint[];
}

// =============================================================================
// Status color mapping -- matches the design system
// =============================================================================

const STATUS_COLORS: Record<string, { dark: string; light: string }> = {
  backlog: { dark: "#737373", light: "#8C8C8C" },
  todo: { dark: "#3B82F6", light: "#2563EB" },
  "in-progress": { dark: "#8B5CF6", light: "#7C3AED" },
  "in-review": { dark: "#F59E0B", light: "#D97706" },
  done: { dark: "#22C55E", light: "#16A34A" },
  cancelled: { dark: "#4D4D4D", light: "#999999" },
};

const STATUS_LABELS: Record<string, string> = {
  backlog: "Backlog",
  todo: "To Do",
  "in-progress": "In Progress",
  "in-review": "In Review",
  done: "Done",
  cancelled: "Cancelled",
};

function getStatusColor(status: string, isDark: boolean): string {
  const key = status.toLowerCase();
  const colors = STATUS_COLORS[key];
  if (!colors) return isDark ? "#6B6B73" : "#A1A1AA";
  return isDark ? colors.dark : colors.light;
}

function getStatusLabel(status: string): string {
  const key = status.toLowerCase();
  return STATUS_LABELS[key] || status;
}

// =============================================================================
// Custom Tooltip
// =============================================================================

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    payload: TasksByStatusDataPoint;
  }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;

  const item = payload[0];
  return (
    <div
      className="rounded-lg border px-3 py-2 text-xs shadow-md"
      style={{
        backgroundColor: "var(--chart-tooltip-bg)",
        borderColor: "var(--chart-tooltip-border)",
      }}
    >
      <p
        className="font-medium mb-0.5"
        style={{ color: "var(--content-primary)" }}
      >
        {getStatusLabel(item.payload.status)}
      </p>
      <p style={{ color: "var(--content-secondary)" }}>
        {item.value} {item.value === 1 ? "task" : "tasks"}
      </p>
    </div>
  );
}

// =============================================================================
// Custom Legend
// =============================================================================

interface CustomLegendProps {
  payload?: Array<{
    value: string;
    color: string;
  }>;
}

function CustomLegend({ payload }: CustomLegendProps) {
  if (!payload?.length) return null;

  return (
    <div className="flex flex-wrap justify-center gap-x-4 gap-y-1 mt-2 px-2">
      {payload.map((entry, index) => (
        <div key={index} className="flex items-center gap-1.5 text-xs">
          <span
            className="inline-block h-2.5 w-2.5 rounded-full shrink-0"
            style={{ backgroundColor: entry.color }}
          />
          <span style={{ color: "var(--content-secondary)" }}>
            {entry.value}
          </span>
        </div>
      ))}
    </div>
  );
}

// =============================================================================
// Tasks by Status -- Donut Chart
// =============================================================================

/**
 * PieChart (donut style) showing task distribution across statuses.
 * Center label displays the total task count.
 * Colors match the design system status palette.
 */
export function TasksByStatusChart({ data }: TasksByStatusChartProps) {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  const isDark = resolvedTheme === "dark";
  const totalTasks = data.reduce((sum, d) => sum + d.count, 0);
  const centerColor = isDark ? "#EDEDEF" : "#09090B";
  const centerSubColor = isDark ? "#6B6B73" : "#A1A1AA";

  // Prepare data with labels for the legend
  const chartData = data.map((d) => ({
    ...d,
    label: getStatusLabel(d.status),
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="45%"
          innerRadius="55%"
          outerRadius="80%"
          paddingAngle={2}
          dataKey="count"
          nameKey="label"
          stroke="none"
        >
          {chartData.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={getStatusColor(entry.status, isDark)}
            />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend content={<CustomLegend />} />

        {/* Center label -- total tasks */}
        <text
          x="50%"
          y="42%"
          textAnchor="middle"
          dominantBaseline="middle"
          className="font-heading"
        >
          <tspan
            fill={centerColor}
            fontSize="28"
            fontWeight="700"
          >
            {totalTasks}
          </tspan>
        </text>
        <text
          x="50%"
          y="51%"
          textAnchor="middle"
          dominantBaseline="middle"
        >
          <tspan
            fill={centerSubColor}
            fontSize="11"
            fontWeight="400"
          >
            total tasks
          </tspan>
        </text>
      </PieChart>
    </ResponsiveContainer>
  );
}
