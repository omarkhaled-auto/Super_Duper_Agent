import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { formatCurrency } from '@/lib/format';
import { cn } from '@/lib/utils';

// ---------------------------------------------------------------------------
// BudgetSummary (TASK-034)
// Compact list of budget progress bars. Max 5 displayed.
// All monetary values are INTEGER CENTS.
// ---------------------------------------------------------------------------

interface BudgetItem {
  name: string;
  spent: number; // cents
  limit: number; // cents
  categoryColor: string;
}

interface BudgetSummaryProps {
  budgets: BudgetItem[];
}

/** Determine progress bar color based on utilization percentage. */
function getProgressColor(percent: number): string {
  if (percent > 90) return 'text-negative';
  if (percent > 75) return 'text-warning';
  return 'text-positive';
}

function getProgressBg(percent: number): string {
  if (percent > 90) return '[&>[data-slot=progress-indicator]]:bg-negative';
  if (percent > 75) return '[&>[data-slot=progress-indicator]]:bg-warning';
  return '[&>[data-slot=progress-indicator]]:bg-positive';
}

export function BudgetSummary({ budgets }: BudgetSummaryProps) {
  // Only show the top 5 budgets
  const displayBudgets = budgets.slice(0, 5);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Budget Progress</CardTitle>
      </CardHeader>
      <CardContent>
        {displayBudgets.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            No budgets set
          </p>
        ) : (
          <div className="space-y-4">
            {displayBudgets.map((budget) => {
              const percent =
                budget.limit > 0
                  ? Math.min((budget.spent / budget.limit) * 100, 100)
                  : 0;
              const colorClass = getProgressColor(percent);

              return (
                <div key={budget.name} className="space-y-1.5">
                  {/* Category name + spent/limit */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div
                        className="h-2.5 w-2.5 rounded-full"
                        style={{ backgroundColor: budget.categoryColor }}
                      />
                      <span className="text-sm font-medium text-foreground">
                        {budget.name}
                      </span>
                    </div>
                    <span className={cn('text-xs font-medium', colorClass)}>
                      {formatCurrency(budget.spent)} / {formatCurrency(budget.limit)}
                    </span>
                  </div>

                  {/* Progress bar */}
                  <Progress
                    value={percent}
                    className={cn('h-2', getProgressBg(percent))}
                  />
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
