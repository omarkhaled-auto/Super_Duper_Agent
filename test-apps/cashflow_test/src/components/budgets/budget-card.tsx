import { MoreHorizontal, Pencil, Trash2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { formatCurrency } from '@/lib/format';
import { cn } from '@/lib/utils';
import type { Budget } from '@/types';

interface BudgetCardProps {
  budget: Budget;
  spent: number;
  categoryName: string;
  categoryColor: string;
  categoryIcon: string;
  onEdit: (budget: Budget) => void;
  onDelete: (id: string) => void;
}

export function BudgetCard({
  budget,
  spent,
  categoryName,
  categoryColor,
  categoryIcon,
  onEdit,
  onDelete,
}: BudgetCardProps) {
  const percentage = budget.amount > 0 ? Math.round((spent / budget.amount) * 100) : 0;
  const clampedPercentage = Math.min(percentage, 100);

  const progressColor =
    percentage > 90
      ? 'bg-red-500'
      : percentage >= 75
        ? 'bg-amber-500'
        : 'bg-green-500';

  return (
    <Card>
      <CardContent className="pt-0">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-lg text-sm font-medium"
              style={{ backgroundColor: categoryColor + '20', color: categoryColor }}
            >
              {categoryIcon}
            </div>
            <div>
              <p className="font-semibold text-sm">{budget.name}</p>
              <p className="text-xs text-muted-foreground">{categoryName}</p>
            </div>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon-xs">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onEdit(budget)}>
                <Pencil className="mr-2 h-4 w-4" />
                Edit
              </DropdownMenuItem>
              <DropdownMenuItem
                variant="destructive"
                onClick={() => onDelete(budget.id)}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <div className={cn('rounded-full', progressColor.replace('bg-', '[&>div]:bg-'))}>
          <Progress value={clampedPercentage} className={cn(
            '[&>[data-slot=progress-indicator]]:transition-all',
            percentage > 90
              ? '[&>[data-slot=progress-indicator]]:bg-red-500'
              : percentage >= 75
                ? '[&>[data-slot=progress-indicator]]:bg-amber-500'
                : '[&>[data-slot=progress-indicator]]:bg-green-500',
          )} />
        </div>

        <div className="flex items-center justify-between mt-3">
          <span className="text-sm text-muted-foreground">
            {formatCurrency(spent)} / {formatCurrency(budget.amount)}
          </span>
          <span
            className={cn(
              'text-sm font-medium',
              percentage > 90
                ? 'text-red-500'
                : percentage >= 75
                  ? 'text-amber-500'
                  : 'text-green-500',
            )}
          >
            {percentage}%
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
