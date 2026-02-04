"use client";

import * as React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useTheme } from "next-themes";

// =============================================================================
// Types
// =============================================================================

export interface TasksOverTimeDataPoint {
  date: string;
  count: number;
}

interface TasksOverTimeChartProps {
  data: TasksOverTimeDataPoint[];
}

// =============================================================================
// Custom Tooltip
// =============================================================================

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ value: number }>;
  label?: string;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;

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
        {label}
      </p>
      <p style={{ color: "var(--chart-brand)" }}>
        {payload[0].value} {payload[0].value === 1 ? "task" : "tasks"}
      </p>
    </div>
  );
}

// =============================================================================
// Tasks Over Time -- Area Chart
// =============================================================================

/**
 * AreaChart showing task creation/completion over the last 30 days.
 * Uses the brand violet color for fill and stroke.
 * Fully theme-aware via CSS custom properties.
 */
export function TasksOverTimeChart({ data }: TasksOverTimeChartProps) {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  const isDark = resolvedTheme === "dark";
  const brandColor = isDark ? "#8B5CF6" : "#7C3AED";
  const gridColor = isDark ? "#2A2A2D" : "#E4E4E7";
  const axisColor = isDark ? "#6B6B73" : "#A1A1AA";
  const textColor = isDark ? "#A0A0A6" : "#52525B";

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart
        data={data}
        margin={{ top: 8, right: 8, left: -16, bottom: 0 }}
      >
        <defs>
          <linearGradient id="taskAreaGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={brandColor} stopOpacity={0.3} />
            <stop offset="95%" stopColor={brandColor} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke={gridColor}
          vertical={false}
        />
        <XAxis
          dataKey="date"
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
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="count"
          stroke={brandColor}
          strokeWidth={2}
          fill="url(#taskAreaGradient)"
          dot={false}
          activeDot={{
            r: 4,
            fill: brandColor,
            stroke: isDark ? "#0A0A0B" : "#FFFFFF",
            strokeWidth: 2,
          }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
