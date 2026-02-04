import { useMemo } from 'react';
import {
  startOfMonth,
  endOfMonth,
  isWithinInterval,
  differenceInDays,
  startOfDay,
} from 'date-fns';
import { TrendingUp, TrendingDown, Calendar, Tag } from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { CurrencyDisplay } from '@/components/shared/currency-display';
import { formatCurrency } from '@/lib/format';
import type { Transaction, Account, Category } from '@/types';

// ---------------------------------------------------------------------------
// AnalyticsOverview (TASK-051)
// Stat cards showing current-month income, expenses, avg daily spending,
// and top spending category. All amounts are INTEGER CENTS.
// ---------------------------------------------------------------------------

interface AnalyticsOverviewProps {
  transactions: Transaction[];
  accounts: Account[];
  categories: Category[];
}

export function AnalyticsOverview({
  transactions,
  accounts,
  categories,
}: AnalyticsOverviewProps) {
  const stats = useMemo(() => {
    const now = new Date();
    const monthStart = startOfMonth(now);
    const monthEnd = endOfMonth(now);

    // Filter transactions that fall within the current month
    const currentMonthTxns = transactions.filter((t) => {
      const d = new Date(t.date);
      return isWithinInterval(d, { start: monthStart, end: monthEnd });
    });

    const totalIncome = currentMonthTxns
      .filter((t) => t.type === 'income')
      .reduce((sum, t) => sum + t.amount, 0);

    const totalExpenses = currentMonthTxns
      .filter((t) => t.type === 'expense')
      .reduce((sum, t) => sum + t.amount, 0);

    // Days elapsed in the current month (at least 1 to avoid division by 0)
    const daysPassed = Math.max(
      differenceInDays(startOfDay(now), monthStart) + 1,
      1,
    );
    const avgDailySpending = Math.round(totalExpenses / daysPassed);

    // Top spending category
    const categorySpending = new Map<string, number>();
    currentMonthTxns
      .filter((t) => t.type === 'expense')
      .forEach((t) => {
        categorySpending.set(
          t.categoryId,
          (categorySpending.get(t.categoryId) ?? 0) + t.amount,
        );
      });

    let topCategoryName = 'N/A';
    let topCategoryAmount = 0;
    categorySpending.forEach((amount, catId) => {
      if (amount > topCategoryAmount) {
        topCategoryAmount = amount;
        const cat = categories.find((c) => c.id === catId);
        topCategoryName = cat?.name ?? 'Unknown';
      }
    });

    return { totalIncome, totalExpenses, avgDailySpending, topCategoryName, topCategoryAmount };
  }, [transactions, categories]);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Total Income */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Monthly Income
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-positive" />
          </div>
        </CardHeader>
        <CardContent>
          <CurrencyDisplay amount={stats.totalIncome} className="text-2xl font-bold" />
        </CardContent>
      </Card>

      {/* Total Expenses */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Monthly Expenses
            </CardTitle>
            <TrendingDown className="h-4 w-4 text-negative" />
          </div>
        </CardHeader>
        <CardContent>
          <CurrencyDisplay amount={-stats.totalExpenses} className="text-2xl font-bold" />
        </CardContent>
      </Card>

      {/* Average Daily Spending */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Avg Daily Spending
            </CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </div>
        </CardHeader>
        <CardContent>
          <CurrencyDisplay amount={-stats.avgDailySpending} className="text-2xl font-bold" />
        </CardContent>
      </Card>

      {/* Top Category */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Top Category
            </CardTitle>
            <Tag className="h-4 w-4 text-muted-foreground" />
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-lg font-bold text-foreground truncate">
            {stats.topCategoryName}
          </p>
          <p className="text-xs text-muted-foreground">
            {formatCurrency(stats.topCategoryAmount)} this month
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
