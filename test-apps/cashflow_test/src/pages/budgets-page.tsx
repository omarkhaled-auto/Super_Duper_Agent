import { useMemo, useState } from 'react';
import {
  startOfWeek,
  endOfWeek,
  startOfMonth,
  endOfMonth,
  startOfYear,
  endOfYear,
  isWithinInterval,
} from 'date-fns';
import { Plus, Wallet } from 'lucide-react';
import { toast } from 'sonner';
import { useBudgetStore } from '@/stores/use-budget-store';
import { useTransactionStore } from '@/stores/use-transaction-store';
import { useCategoryStore } from '@/stores/use-category-store';
import { PageHeader } from '@/components/shared/page-header';
import { EmptyState } from '@/components/shared/empty-state';
import { ConfirmDialog } from '@/components/shared/confirm-dialog';
import { BudgetSummaryBar } from '@/components/budgets/budget-summary-bar';
import { BudgetList } from '@/components/budgets/budget-list';
import { BudgetModal } from '@/components/budgets/budget-modal';
import { Button } from '@/components/ui/button';
import type { Budget } from '@/types';

/**
 * Return the date range for the current period of a budget.
 * "monthly"  -> first/last day of current month
 * "weekly"   -> Monday-Sunday of current week
 * "yearly"   -> Jan 1 - Dec 31 of current year
 */
function getCurrentPeriodRange(period: 'weekly' | 'monthly' | 'yearly') {
  const now = new Date();
  switch (period) {
    case 'weekly':
      return { start: startOfWeek(now, { weekStartsOn: 1 }), end: endOfWeek(now, { weekStartsOn: 1 }) };
    case 'monthly':
      return { start: startOfMonth(now), end: endOfMonth(now) };
    case 'yearly':
      return { start: startOfYear(now), end: endOfYear(now) };
  }
}

export default function BudgetsPage() {
  const { budgets, addBudget, updateBudget, deleteBudget } = useBudgetStore();
  const { transactions } = useTransactionStore();
  const { categories } = useCategoryStore();

  const [modalOpen, setModalOpen] = useState(false);
  const [editingBudget, setEditingBudget] = useState<Budget | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);

  // Compute spent per budget category for the current period (WIRE-024)
  const spentByCategory = useMemo(() => {
    const result: Record<string, number> = {};

    for (const budget of budgets) {
      const range = getCurrentPeriodRange(budget.period);
      const spent = transactions
        .filter(
          (t) =>
            t.type === 'expense' &&
            t.categoryId === budget.categoryId &&
            isWithinInterval(new Date(t.date), { start: range.start, end: range.end }),
        )
        .reduce((sum, t) => sum + t.amount, 0);

      // Accumulate -- if multiple budgets share a category, each gets the full spent
      result[budget.categoryId] = spent;
    }

    return result;
  }, [budgets, transactions]);

  const activeBudgets = budgets.filter((b) => b.isActive);

  const totalBudgeted = activeBudgets.reduce((sum, b) => sum + b.amount, 0);
  const totalSpent = activeBudgets.reduce(
    (sum, b) => sum + (spentByCategory[b.categoryId] ?? 0),
    0,
  );

  // --- Handlers ---
  const handleOpenCreate = () => {
    setEditingBudget(null);
    setModalOpen(true);
  };

  const handleEdit = (budget: Budget) => {
    setEditingBudget(budget);
    setModalOpen(true);
  };

  const handleSave = (data: {
    name: string;
    categoryId: string;
    amount: number;
    period: 'monthly' | 'weekly' | 'yearly';
    alertThreshold: number;
    isActive: boolean;
  }) => {
    if (editingBudget) {
      updateBudget(editingBudget.id, data);
      toast.success('Budget updated successfully');
    } else {
      addBudget(data);
      toast.success('Budget created successfully');
    }
  };

  const handleRequestDelete = (id: string) => {
    setDeleteId(id);
  };

  const handleConfirmDelete = () => {
    if (deleteId) {
      deleteBudget(deleteId);
      toast.success('Budget deleted');
      setDeleteId(null);
    }
  };

  return (
    <div className="p-6">
      <PageHeader title="Budgets" subtitle="Track spending against your budget limits">
        <Button onClick={handleOpenCreate}>
          <Plus className="mr-2 h-4 w-4" />
          Create Budget
        </Button>
      </PageHeader>

      {activeBudgets.length > 0 ? (
        <>
          <BudgetSummaryBar totalBudgeted={totalBudgeted} totalSpent={totalSpent} />
          <BudgetList
            budgets={activeBudgets}
            spentByCategory={spentByCategory}
            categories={categories}
            onEdit={handleEdit}
            onDelete={handleRequestDelete}
          />
        </>
      ) : (
        <EmptyState
          icon={Wallet}
          title="No budgets yet"
          description="Create your first budget to start tracking your spending against limits."
          actionLabel="Create Budget"
          onAction={handleOpenCreate}
        />
      )}

      <BudgetModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        editItem={editingBudget}
        onSave={handleSave}
        categories={categories}
      />

      <ConfirmDialog
        open={deleteId !== null}
        onClose={() => setDeleteId(null)}
        onConfirm={handleConfirmDelete}
        title="Delete Budget"
        description="Are you sure you want to delete this budget? This action cannot be undone."
        confirmLabel="Delete"
        variant="destructive"
      />
    </div>
  );
}
