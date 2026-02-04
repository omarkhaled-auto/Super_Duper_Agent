import { BudgetCard } from './budget-card';
import type { Budget, Category } from '@/types';

interface BudgetListProps {
  budgets: Budget[];
  spentByCategory: Record<string, number>;
  categories: Category[];
  onEdit: (b: Budget) => void;
  onDelete: (id: string) => void;
}

export function BudgetList({
  budgets,
  spentByCategory,
  categories,
  onEdit,
  onDelete,
}: BudgetListProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {budgets.map((budget) => {
        const category = categories.find((c) => c.id === budget.categoryId);
        const spent = spentByCategory[budget.categoryId] ?? 0;

        return (
          <BudgetCard
            key={budget.id}
            budget={budget}
            spent={spent}
            categoryName={category?.name ?? 'Unknown'}
            categoryColor={category?.color ?? '#6B7280'}
            categoryIcon={category?.icon ?? '?'}
            onEdit={onEdit}
            onDelete={onDelete}
          />
        );
      })}
    </div>
  );
}
