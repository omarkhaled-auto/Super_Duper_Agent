import { Card, CardContent } from '@/components/ui/card';
import { CurrencyDisplay } from '@/components/shared/currency-display';
import { formatCurrency } from '@/lib/format';
import { cn } from '@/lib/utils';

interface BudgetSummaryBarProps {
  totalBudgeted: number; // cents
  totalSpent: number; // cents
}

export function BudgetSummaryBar({ totalBudgeted, totalSpent }: BudgetSummaryBarProps) {
  const remaining = totalBudgeted - totalSpent;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
      <Card>
        <CardContent className="pt-0">
          <p className="text-sm text-muted-foreground mb-1">Total Budgeted</p>
          <p className="text-2xl font-bold font-mono tabular-nums">
            {formatCurrency(totalBudgeted)}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-0">
          <p className="text-sm text-muted-foreground mb-1">Total Spent</p>
          <p className="text-2xl font-bold font-mono tabular-nums">
            {formatCurrency(totalSpent)}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-0">
          <p className="text-sm text-muted-foreground mb-1">Remaining</p>
          <CurrencyDisplay
            amount={remaining}
            className={cn(
              'text-2xl font-bold',
              remaining >= 0 ? 'text-green-500' : 'text-red-500',
            )}
          />
        </CardContent>
      </Card>
    </div>
  );
}
