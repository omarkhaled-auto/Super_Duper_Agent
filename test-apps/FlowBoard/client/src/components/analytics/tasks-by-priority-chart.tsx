"use client";

import * as React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { useTheme } from "next-themes";

// =============================================================================
// Types
// =============================================================================

export interface TasksByPriorityDataPoint {
  priority: string;
  count: number;
}

interface TasksByPriorityChartProps {
  data: TasksByPriorityDataPoint[];
}

// =============================================================================
// Priority color mapping -- matches the design system
// =============================================================================

const PRIORITY_COLORS: Record<string, { dark: string; light: string }> = {
  urgent: { dark: "#EF4444", light: "#DC2626" },
  high: { dark: "#F59E0B", light: "#D97706" },
  medium: { dark: "#EAB308", light: "#CA8A04" },
  low: { dark: "#3B82F6", light: "#2563EB" },
  none: { dark: "#6B6B73", light: "#A1A1AA" },
};

const PRIORITY_LABELS: Record<string, string> = {
  urgent: "Urgent",
  high: "High",
  medium: "Medium",
  low: "Low",
  none: "None",
};

function getPriorityColor(priority: string, isDark: boolean): string {
  const key = priority.toLowerCase();
  const colors = PRIORITY_COLORS[key];
  if (!colors) return isDark ? "#6B6B73" : "#A1A1AA";
  return isDark ? colors.dark : colors.light;
}

function getPriorityLabel(priority: string): string {
  const key = priority.toLowerCase();
  return PRIORITY_LABELS[key] || priority;
}

// =============================================================================
// Custom Tooltip
// =============================================================================

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    value: number;
    payload: TasksByPriorityDataPoint;
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
        {getPriorityLabel(item.payload.priority)}
      </p>
      <p style={{ color: "var(--content-secondary)" }}>
        {item.value} {item.value === 1 ? "task" : "tasks"}
      </p>
    </div>
  );
}

// =============================================================================
// Tasks by Priority -- Bar Chart
// =============================================================================

/**
 * BarChart showing task distribution across priority levels.
 * Each bar is colored to match the priority's design system color.
 * Fully theme-aware for both dark and light modes.
 */
export function TasksByPriorityChart({ data }: TasksByPriorityChartProps) {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  const isDark = resolvedTheme === "dark";
  const gridColor = isDark ? "#2A2A2D" : "#E4E4E7";
  const textColor = isDark ? "#A0A0A6" : "#52525B";

  // Map priority keys to display labels for the X axis
  const chartData = data.map((d) => ({
    ...d,
    label: getPriorityLabel(d.priority),
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        data={chartData}
        margin={{ top: 8, right: 8, left: -16, bottom: 0 }}
        barCategoryGap="20%"
      >
        <CartesianGrid
          strokeDasharray="3 3"
          stroke={gridColor}
          vertical={false}
        />
        <XAxis
          dataKey="label"
          axisLine={false}
          tickLine={false}
          tick={{ fontSize: 11, fill: textColor }}
          dy={8}
        />
        <YAxis
          axisLine={false}
          tickLine={false}
          tick={{ fontSize: 11, fill: textColor }}
          allowDecimals={false}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: "transparent" }} />
        <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={48}>
          {chartData.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={getPriorityColor(entry.priority, isDark)}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
