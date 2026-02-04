import {
  BarChart,
  Bar,
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
// IncomeExpenseChart (TASK-052)
// Bar chart comparing income vs expenses by month (Recharts).
// Input amounts are INTEGER CENTS. Converted to dollars for display.
// ---------------------------------------------------------------------------

interface IncomeExpenseChartProps {
  data: Array<{ month: string; income: number; expenses: number }>;
}

/** Convert cent-based data to dollar-based for chart rendering. */
function toDollars(data: IncomeExpenseChartProps['data']) {
  return data.map((d) => ({
    month: d.month,
    income: d.income / 100,
    expenses: d.expenses / 100,
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

export function IncomeExpenseChart({ data }: IncomeExpenseChartProps) {
  const chartData = toDollars(data);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Income vs Expenses</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart
            data={chartData}
            margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
          >
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
            <Bar
              dataKey="income"
              name="Income"
              fill="#2DA44E"
              radius={[4, 4, 0, 0]}
            />
            <Bar
              dataKey="expenses"
              name="Expenses"
              fill="#DA3633"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
