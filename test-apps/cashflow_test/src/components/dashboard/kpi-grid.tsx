import { Wallet, TrendingUp, TrendingDown, PiggyBank } from 'lucide-react';
import { KPICard } from '@/components/dashboard/kpi-card';
import { formatCurrency } from '@/lib/format';

// ---------------------------------------------------------------------------
// KPIGrid (TASK-031)
// Responsive grid of 4 KPI cards for the dashboard header.
// All monetary values are INTEGER CENTS. savingsRate is 0-100.
// ---------------------------------------------------------------------------

interface KPIGridProps {
  totalBalance: number;
  monthlyIncome: number;
  monthlyExpenses: number;
  savingsRate: number;
  prevTotalBalance?: number;
  prevIncome?: number;
  prevExpenses?: number;
  prevSavingsRate?: number;
}

/** Compute % change from previous to current. Returns 0 when previous is 0. */
function computeTrend(current: number, previous?: number): number {
  if (previous === undefined || previous === 0) return 0;
  return ((current - previous) / Math.abs(previous)) * 100;
}

export function KPIGrid({
  totalBalance,
  monthlyIncome,
  monthlyExpenses,
  savingsRate,
  prevTotalBalance,
  prevIncome,
  prevExpenses,
  prevSavingsRate,
}: KPIGridProps) {
  const balanceTrend = computeTrend(totalBalance, prevTotalBalance);
  const incomeTrend = computeTrend(monthlyIncome, prevIncome);
  const expensesTrend = computeTrend(monthlyExpenses, prevExpenses);
  const savingsTrend = computeTrend(savingsRate, prevSavingsRate);

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <KPICard
        title="Total Balance"
        value={formatCurrency(totalBalance)}
        trend={balanceTrend}
        trendDirection="up"
        icon={Wallet}
      />
      <KPICard
        title="Monthly Income"
        value={formatCurrency(monthlyIncome)}
        trend={incomeTrend}
        trendDirection="up"
        icon={TrendingUp}
      />
      <KPICard
        title="Monthly Expenses"
        value={formatCurrency(monthlyExpenses)}
        trend={expensesTrend}
        trendDirection="down"
        icon={TrendingDown}
      />
      <KPICard
        title="Savings Rate"
        value={`${savingsRate.toFixed(1)}%`}
        trend={savingsTrend}
        trendDirection="up"
        icon={PiggyBank}
      />
    </div>
  );
}
