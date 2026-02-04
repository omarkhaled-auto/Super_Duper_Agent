"use client";

import * as React from "react";
import {
  LineChart,
  Line,
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

export interface VelocityDataPoint {
  week: string;
  completed: number;
}

interface VelocityChartProps {
  data: VelocityDataPoint[];
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
        {payload[0].value} completed
      </p>
    </div>
  );
}

// =============================================================================
// Custom Dot
// =============================================================================

interface CustomDotProps {
  cx?: number;
  cy?: number;
  isDark: boolean;
  brandColor: string;
}

function CustomDot({ cx, cy, isDark, brandColor }: CustomDotProps) {
  if (cx === undefined || cy === undefined) return null;

  return (
    <circle
      cx={cx}
      cy={cy}
      r={4}
      fill={brandColor}
      stroke={isDark ? "#0A0A0B" : "#FFFFFF"}
      strokeWidth={2}
    />
  );
}

// =============================================================================
// Velocity -- Line Chart
// =============================================================================

/**
 * LineChart showing team velocity (tasks completed per week) over the last 8 weeks.
 * Uses the brand violet color for the line stroke and data points.
 * Fully theme-aware for both dark and light modes.
 */
export function VelocityChart({ data }: VelocityChartProps) {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  const isDark = resolvedTheme === "dark";
  const brandColor = isDark ? "#8B5CF6" : "#7C3AED";
  const gridColor = isDark ? "#2A2A2D" : "#E4E4E7";
  const textColor = isDark ? "#A0A0A6" : "#52525B";

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart
        data={data}
        margin={{ top: 8, right: 8, left: -16, bottom: 0 }}
      >
        <defs>
          <linearGradient id="velocityGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={brandColor} stopOpacity={0.15} />
            <stop offset="100%" stopColor={brandColor} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke={gridColor}
          vertical={false}
        />
        <XAxis
          dataKey="week"
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
        <Line
          type="monotone"
          dataKey="completed"
          stroke={brandColor}
          strokeWidth={2.5}
          dot={(props) => (
            <CustomDot
              key={`dot-${props.cx}-${props.cy}`}
              cx={props.cx}
              cy={props.cy}
              isDark={isDark}
              brandColor={brandColor}
            />
          )}
          activeDot={{
            r: 6,
            fill: brandColor,
            stroke: isDark ? "#0A0A0B" : "#FFFFFF",
            strokeWidth: 2,
          }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
