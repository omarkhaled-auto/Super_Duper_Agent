import { useState, useMemo } from 'react';
import {
  format,
  subMonths,
  startOfMonth,
  endOfMonth,
  isWithinInterval,
  eachMonthOfInterval,
} from 'date-fns';
import { useTransactionStore } from '@/stores/use-transaction-store';
import { useAccountStore } from '@/stores/use-account-store';
import { useCategoryStore } from '@/stores/use-category-store';
import { PageHeader } from '@/components/shared/page-header';
import { AnalyticsTabs } from '@/components/analytics/analytics-tabs';
import { AnalyticsOverview } from '@/components/analytics/analytics-overview';
import { IncomeExpenseChart } from '@/components/analytics/income-expense-chart';
import { CategoryBreakdown } from '@/components/analytics/category-breakdown';
import { NetWorthChart } from '@/components/analytics/net-worth-chart';

// ---------------------------------------------------------------------------
// AnalyticsPage (TASK-055)
// Orchestrates analytics sub-views: overview, income/expenses, category
// breakdown, and net-worth chart.
// ---------------------------------------------------------------------------

export default function AnalyticsPage() {
  const transactions = useTransactionStore((s) => s.transactions);
  const accounts = useAccountStore((s) => s.accounts);
  const categories = useCategoryStore((s) => s.categories);

  const [activeTab, setActiveTab] = useState('overview');

  // -------------------------------------------------------------------------
  // Monthly income / expenses for the last 12 months
  // -------------------------------------------------------------------------
  const monthlyData = useMemo(() => {
    const now = new Date();
    const start = startOfMonth(subMonths(now, 11));
    const end = endOfMonth(now);
    const months = eachMonthOfInterval({ start, end });

    return months.map((monthDate) => {
      const mStart = startOfMonth(monthDate);
      const mEnd = endOfMonth(monthDate);

      const monthTxns = transactions.filter((t) => {
        const d = new Date(t.date);
        return isWithinInterval(d, { start: mStart, end: mEnd });
      });

      const income = monthTxns
        .filter((t) => t.type === 'income')
        .reduce((sum, t) => sum + t.amount, 0);

      const expenses = monthTxns
        .filter((t) => t.type === 'expense')
        .reduce((sum, t) => sum + t.amount, 0);

      return {
        month: format(monthDate, 'MMM yyyy'),
        income,
        expenses,
      };
    });
  }, [transactions]);

  // -------------------------------------------------------------------------
  // Category breakdown (current month expenses)
  // -------------------------------------------------------------------------
  const categoryData = useMemo(() => {
    const now = new Date();
    const mStart = startOfMonth(now);
    const mEnd = endOfMonth(now);

    const expenseTxns = transactions.filter((t) => {
      const d = new Date(t.date);
      return (
        t.type === 'expense' &&
        isWithinInterval(d, { start: mStart, end: mEnd })
      );
    });

    const categoryTotals = new Map<string, number>();
    expenseTxns.forEach((t) => {
      categoryTotals.set(
        t.categoryId,
        (categoryTotals.get(t.categoryId) ?? 0) + t.amount,
      );
    });

    const totalExpenses = expenseTxns.reduce((sum, t) => sum + t.amount, 0);

    const result = Array.from(categoryTotals.entries())
      .map(([catId, amount]) => {
        const cat = categories.find((c) => c.id === catId);
        return {
          categoryId: catId,
          categoryName: cat?.name ?? 'Unknown',
          categoryColor: cat?.color ?? '#888888',
          amount,
          percentage: totalExpenses > 0 ? (amount / totalExpenses) * 100 : 0,
        };
      })
      .sort((a, b) => b.amount - a.amount);

    return result;
  }, [transactions, categories]);

  // -------------------------------------------------------------------------
  // Net worth history: simulate monthly snapshots
  // Uses current account balances as the latest snapshot and works backwards
  // by reversing the cumulative transaction impact per month.
  // -------------------------------------------------------------------------
  const netWorthData = useMemo(() => {
    const now = new Date();
    const start = startOfMonth(subMonths(now, 11));
    const end = endOfMonth(now);
    const months = eachMonthOfInterval({ start, end });

    // Current totals from account balances
    const currentAssets = accounts
      .filter((a) => a.isActive && a.type !== 'credit')
      .reduce((sum, a) => sum + a.balance, 0);

    const currentLiabilities = accounts
      .filter((a) => a.isActive && a.type === 'credit')
      .reduce((sum, a) => sum + Math.abs(a.balance), 0);

    // Compute the net impact of transactions per month (income adds, expense subtracts)
    // We'll work forward from the earliest month.
    const monthlyImpact = months.map((monthDate) => {
      const mStart = startOfMonth(monthDate);
      const mEnd = endOfMonth(monthDate);
      const monthTxns = transactions.filter((t) => {
        const d = new Date(t.date);
        return isWithinInterval(d, { start: mStart, end: mEnd });
      });

      const income = monthTxns
        .filter((t) => t.type === 'income')
        .reduce((sum, t) => sum + t.amount, 0);

      const expenses = monthTxns
        .filter((t) => t.type === 'expense')
        .reduce((sum, t) => sum + t.amount, 0);

      return { income, expenses, net: income - expenses };
    });

    // Calculate the total net impact across all 12 months
    const totalNetImpact = monthlyImpact.reduce((sum, m) => sum + m.net, 0);

    // Starting assets = current assets minus total net impact
    let runningAssets = currentAssets - totalNetImpact;
    // Liabilities are simulated as roughly constant for simplicity
    const liabilities = currentLiabilities;

    return months.map((monthDate, i) => {
      runningAssets += monthlyImpact[i]!.net;
      const netWorth = runningAssets - liabilities;

      return {
        month: format(monthDate, 'MMM yyyy'),
        assets: runningAssets,
        liabilities: liabilities,
        netWorth,
      };
    });
  }, [transactions, accounts]);

  return (
    <div>
      <PageHeader
        title="Analytics"
        subtitle="Track your financial trends and insights"
      />

      <AnalyticsTabs activeTab={activeTab} onTabChange={setActiveTab} />

      <div className="mt-4">
        {activeTab === 'overview' && (
          <AnalyticsOverview
            transactions={transactions}
            accounts={accounts}
            categories={categories}
          />
        )}

        {activeTab === 'income-expenses' && (
          <IncomeExpenseChart data={monthlyData} />
        )}

        {activeTab === 'categories' && (
          <CategoryBreakdown data={categoryData} />
        )}

        {activeTab === 'net-worth' && (
          <NetWorthChart data={netWorthData} />
        )}
      </div>
    </div>
  );
}
