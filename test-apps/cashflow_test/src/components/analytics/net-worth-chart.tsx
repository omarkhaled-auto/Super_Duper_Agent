import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { formatCurrency } from '@/lib/format';

// ---------------------------------------------------------------------------
// NetWorthChart (TASK-054)
// Area chart showing assets, liabilities, and net worth over time (Recharts).
// Input amounts are INTEGER CENTS. Converted to dollars for display.
// ---------------------------------------------------------------------------

interface NetWorthChartProps {
  data: Array<{
    month: string;
    assets: number;
    liabilities: number;
    netWorth: number;
  }>;
}

/** Convert cent-based data to dollar-based for chart rendering. */
function toDollars(data: NetWorthChartProps['data']) {
  return data.map((d) => ({
    month: d.month,
    assets: d.assets / 100,
    liabilities: Math.abs(d.liabilities) / 100,
    netWorth: d.netWorth / 100,
  }));
}

/** Custom tooltip rendering formatted currency values. */
function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number; name: string; color: string }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;

  return (
    <div className="rounded-lg border bg-card px-3 py-2 shadow-md">
      <p className="mb-1 text-sm font-medium text-foreground">{label}</p>
      {payload.map((entry) => (
        <p
          key={entry.name}
          className="text-xs"
          style={{ color: entry.color }}
        >
          {entry.name}: {formatCurrency(Math.round(entry.value * 100))}
        </p>
      ))}
    </div>
  );
}

export function NetWorthChart({ data }: NetWorthChartProps) {
  const chartData = toDollars(data);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Net Worth Over Time</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart
            data={chartData}
            margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
          >
            <defs>
              <linearGradient id="assetsGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#2DA44E" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#2DA44E" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="liabilitiesGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#DA3633" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#DA3633" stopOpacity={0} />
              </linearGradient>
            </defs>

            <CartesianGrid
              strokeDasharray="3 3"
              className="stroke-border"
              vertical={false}
            />
            <XAxis
              dataKey="month"
              tick={{ fontSize: 12 }}
              className="text-muted-foreground"
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              className="text-muted-foreground"
              tickLine={false}
              axisLine={false}
              tickFormatter={(value: number) =>
                new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: 'USD',
                  notation: 'compact',
                  maximumFractionDigits: 1,
                }).format(value)
              }
            />
            <Tooltip content={<ChartTooltip />} />
            <Legend
              verticalAlign="top"
              height={36}
              iconType="circle"
              iconSize={8}
            />
            <Area
              type="monotone"
              dataKey="assets"
              name="Assets"
              stroke="#2DA44E"
              fill="url(#assetsGradient)"
              strokeWidth={2}
            />
            <Area
              type="monotone"
              dataKey="liabilities"
              name="Liabilities"
              stroke="#DA3633"
              fill="url(#liabilitiesGradient)"
              strokeWidth={2}
            />
            <Area
              type="monotone"
              dataKey="netWorth"
              name="Net Worth"
              stroke="#5E6AD2"
              fill="none"
              strokeWidth={3}
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
