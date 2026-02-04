import { useMemo } from 'react';
import {
  startOfMonth,
  endOfMonth,
  subMonths,
  format,
  isWithinInterval,
} from 'date-fns';
import { useTransactionStore } from '@/stores/use-transaction-store';
import { useAccountStore } from '@/stores/use-account-store';
import { useBudgetStore } from '@/stores/use-budget-store';
import { useCategoryStore } from '@/stores/use-category-store';
import { PageHeader } from '@/components/shared/page-header';
import { KPIGrid } from '@/components/dashboard/kpi-grid';
import { SpendingChart } from '@/components/dashboard/spending-chart';
import { RecentTransactions } from '@/components/dashboard/recent-transactions';
import { BudgetSummary } from '@/components/dashboard/budget-summary';
import { AccountBalances } from '@/components/dashboard/account-balances';

// ---------------------------------------------------------------------------
// DashboardPage (TASK-031 through TASK-035)
// Main dashboard view composing all dashboard widgets.
// All monetary values are INTEGER CENTS throughout.
// ---------------------------------------------------------------------------

/** Sum transactions matching a type within a date interval. Returns cents. */
function sumTransactions(
  transactions: { type: string; amount: number; date: string }[],
  type: 'income' | 'expense',
  start: Date,
  end: Date,
): number {
  return transactions
    .filter(
      (t) =>
        t.type === type &&
        isWithinInterval(new Date(t.date), { start, end }),
    )
    .reduce((sum, t) => sum + t.amount, 0);
}

export default function DashboardPage() {
  const { transactions } = useTransactionStore();
  const { accounts } = useAccountStore();
  const { budgets } = useBudgetStore();
  const { categories } = useCategoryStore();

  const now = new Date();

  // ---- Current month boundaries ----
  const currentMonthStart = startOfMonth(now);
  const currentMonthEnd = endOfMonth(now);

  // ---- Previous month boundaries ----
  const prevMonthDate = subMonths(now, 1);
  const prevMonthStart = startOfMonth(prevMonthDate);
  const prevMonthEnd = endOfMonth(prevMonthDate);

  // ---- KPI calculations ----
  const kpiData = useMemo(() => {
    // Total balance: sum all active account balances (cents)
    const totalBalance = accounts
      .filter((a) => a.isActive)
      .reduce((sum, a) => sum + a.balance, 0);

    // Current month income/expenses
    const monthlyIncome = sumTransactions(
      transactions,
      'income',
      currentMonthStart,
      currentMonthEnd,
    );
    const monthlyExpenses = sumTransactions(
      transactions,
      'expense',
      currentMonthStart,
      currentMonthEnd,
    );

    // Savings rate: percentage of income saved
    const savingsRate =
      monthlyIncome > 0
        ? ((monthlyIncome - monthlyExpenses) / monthlyIncome) * 100
        : 0;

    // Previous month metrics for trend comparison
    const prevIncome = sumTransactions(
      transactions,
      'income',
      prevMonthStart,
      prevMonthEnd,
    );
    const prevExpenses = sumTransactions(
      transactions,
      'expense',
      prevMonthStart,
      prevMonthEnd,
    );
    const prevSavingsRate =
      prevIncome > 0
        ? ((prevIncome - prevExpenses) / prevIncome) * 100
        : 0;

    // Approximate previous total balance by subtracting current month's net
    const currentMonthDelta = monthlyIncome - monthlyExpenses;
    const prevTotalBalance = totalBalance - currentMonthDelta;

    return {
      totalBalance,
      monthlyIncome,
      monthlyExpenses,
      savingsRate: Math.max(0, savingsRate),
      prevTotalBalance,
      prevIncome,
      prevExpenses,
      prevSavingsRate: Math.max(0, prevSavingsRate),
    };
  }, [
    transactions,
    accounts,
    currentMonthStart,
    currentMonthEnd,
    prevMonthStart,
    prevMonthEnd,
  ]);

  // ---- Monthly chart data (last 6 months) ----
  const chartData = useMemo(() => {
    const months: Array<{ month: string; income: number; expenses: number }> = [];

    for (let i = 5; i >= 0; i--) {
      const monthDate = subMonths(now, i);
      const start = startOfMonth(monthDate);
      const end = endOfMonth(monthDate);

      months.push({
        month: format(monthDate, 'MMM yyyy'),
        income: sumTransactions(transactions, 'income', start, end),
        expenses: sumTransactions(transactions, 'expense', start, end),
      });
    }

    return months;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [transactions]);

  // ---- Budget progress ----
  const budgetSummaryData = useMemo(() => {
    const categoryMap = new Map(categories.map((c) => [c.id, c]));

    return budgets
      .filter((b) => b.isActive)
      .map((budget) => {
        const category = categoryMap.get(budget.categoryId);

        // Sum expense transactions for this category in the current month
        const spent = transactions
          .filter(
            (t) =>
              t.type === 'expense' &&
              t.categoryId === budget.categoryId &&
              isWithinInterval(new Date(t.date), {
                start: currentMonthStart,
                end: currentMonthEnd,
              }),
          )
          .reduce((sum, t) => sum + t.amount, 0);

        return {
          name: budget.name || category?.name || 'Unknown',
          spent,
          limit: budget.amount,
          categoryColor: category?.color ?? '#6b7280',
        };
      })
      .sort((a, b) => {
        // Sort by utilization percentage descending (highest usage first)
        const aPercent = a.limit > 0 ? a.spent / a.limit : 0;
        const bPercent = b.limit > 0 ? b.spent / b.limit : 0;
        return bPercent - aPercent;
      });
  }, [budgets, categories, transactions, currentMonthStart, currentMonthEnd]);

  // ---- Recent transactions (10 most recent) ----
  const recentTransactions = useMemo(() => {
    return [...transactions]
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
      .slice(0, 10);
  }, [transactions]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        subtitle="Your financial overview at a glance"
      />

      {/* KPI Cards */}
      <KPIGrid
        totalBalance={kpiData.totalBalance}
        monthlyIncome={kpiData.monthlyIncome}
        monthlyExpenses={kpiData.monthlyExpenses}
        savingsRate={kpiData.savingsRate}
        prevTotalBalance={kpiData.prevTotalBalance}
        prevIncome={kpiData.prevIncome}
        prevExpenses={kpiData.prevExpenses}
        prevSavingsRate={kpiData.prevSavingsRate}
      />

      {/* Two-column layout: 8/4 split */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left column (8 cols): chart + recent transactions */}
        <div className="space-y-6 lg:col-span-8">
          <SpendingChart data={chartData} />
          <RecentTransactions
            transactions={recentTransactions}
            categories={categories}
            accounts={accounts}
          />
        </div>

        {/* Right column (4 cols): budgets + accounts */}
        <div className="space-y-6 lg:col-span-4">
          <BudgetSummary budgets={budgetSummaryData} />
          <AccountBalances accounts={accounts} />
        </div>
      </div>
    </div>
  );
}
