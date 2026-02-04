import { Card, CardContent } from '@/components/ui/card';
import { CurrencyDisplay } from '@/components/shared/currency-display';
import { formatCurrency } from '@/lib/format';
import { cn } from '@/lib/utils';

interface NetWorthSummaryProps {
  totalAssets: number; // cents (positive)
  totalLiabilities: number; // cents (positive value representing liability amount)
}

export function NetWorthSummary({ totalAssets, totalLiabilities }: NetWorthSummaryProps) {
  const netWorth = totalAssets - totalLiabilities;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
      <Card>
        <CardContent className="pt-0">
          <p className="text-sm text-muted-foreground mb-1">Total Assets</p>
          <p className="text-2xl font-bold font-mono tabular-nums text-green-500">
            {formatCurrency(totalAssets)}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-0">
          <p className="text-sm text-muted-foreground mb-1">Total Liabilities</p>
          <p className="text-2xl font-bold font-mono tabular-nums text-red-500">
            {formatCurrency(totalLiabilities)}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-0">
          <p className="text-sm text-muted-foreground mb-1">Net Worth</p>
          <CurrencyDisplay
            amount={netWorth}
            className={cn(
              'text-2xl font-bold',
              netWorth >= 0 ? 'text-green-500' : 'text-red-500',
            )}
          />
        </CardContent>
      </Card>
    </div>
  );
}
