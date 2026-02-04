import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { formatCurrency } from '@/lib/format';

// ---------------------------------------------------------------------------
// CategoryBreakdown (TASK-053)
// Donut chart + table showing expense distribution across categories.
// All amounts are INTEGER CENTS.
// ---------------------------------------------------------------------------

interface CategoryData {
  categoryId: string;
  categoryName: string;
  categoryColor: string;
  amount: number; // cents
  percentage: number;
}

interface CategoryBreakdownProps {
  data: CategoryData[];
}

/** Custom tooltip rendering formatted currency values. */
function ChartTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: CategoryData }>;
}) {
  if (!active || !payload?.length) return null;
  const item = payload[0]!.payload;

  return (
    <div className="rounded-lg border bg-card px-3 py-2 shadow-md">
      <p className="mb-1 text-sm font-medium text-foreground">
        {item.categoryName}
      </p>
      <p className="text-xs text-muted-foreground">
        {formatCurrency(item.amount)} ({item.percentage.toFixed(1)}%)
      </p>
    </div>
  );
}

export function CategoryBreakdown({ data }: CategoryBreakdownProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Category Breakdown</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Donut Chart */}
          <div className="flex-shrink-0">
            <ResponsiveContainer width={240} height={240}>
              <PieChart>
                <Pie
                  data={data}
                  dataKey="amount"
                  nameKey="categoryName"
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                >
                  {data.map((entry) => (
                    <Cell
                      key={entry.categoryId}
                      fill={entry.categoryColor}
                    />
                  ))}
                </Pie>
                <Tooltip content={<ChartTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Category Table */}
          <div className="flex-1 min-w-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 text-muted-foreground font-medium">
                    Category
                  </th>
                  <th className="text-right py-2 text-muted-foreground font-medium">
                    Amount
                  </th>
                  <th className="text-right py-2 text-muted-foreground font-medium">
                    %
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.map((item) => (
                  <tr key={item.categoryId} className="border-b last:border-0">
                    <td className="py-2">
                      <div className="flex items-center gap-2">
                        <span
                          className="inline-block h-3 w-3 rounded-full flex-shrink-0"
                          style={{ backgroundColor: item.categoryColor }}
                        />
                        <span className="truncate">{item.categoryName}</span>
                      </div>
                    </td>
                    <td className="text-right py-2 font-mono tabular-nums">
                      {formatCurrency(item.amount)}
                    </td>
                    <td className="text-right py-2 text-muted-foreground">
                      {item.percentage.toFixed(1)}%
                    </td>
                  </tr>
                ))}
                {data.length === 0 && (
                  <tr>
                    <td colSpan={3} className="py-6 text-center text-muted-foreground">
                      No expense data available.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
