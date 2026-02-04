import { MoreHorizontal, Pencil, Trash2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { CurrencyDisplay } from '@/components/shared/currency-display';
import { formatCurrency } from '@/lib/format';
import { formatDate } from '@/lib/format';
import { cn } from '@/lib/utils';
import type { Goal } from '@/types';

// ---------------------------------------------------------------------------
// GoalCard (TASK-056)
// Individual goal card with SVG circular progress ring, status badge,
// and edit/delete dropdown. All amounts are INTEGER CENTS.
// ---------------------------------------------------------------------------

interface GoalCardProps {
  goal: Goal;
  onEdit: (g: Goal) => void;
  onDelete: (id: string) => void;
}

const STATUS_CONFIG: Record<
  Goal['status'],
  { label: string; className: string }
> = {
  'on-track': { label: 'On Track', className: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' },
  behind: { label: 'Behind', className: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' },
  ahead: { label: 'Ahead', className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
  completed: { label: 'Completed', className: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400' },
};

export function GoalCard({ goal, onEdit, onDelete }: GoalCardProps) {
  const percentage = Math.min(
    goal.targetAmount > 0
      ? (goal.currentAmount / goal.targetAmount) * 100
      : 0,
    100,
  );
  const circumference = 2 * Math.PI * 40; // radius 40
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  const statusCfg = STATUS_CONFIG[goal.status];

  // Monthly contribution needed to reach goal by deadline
  const monthlyNeeded = (() => {
    if (!goal.deadline || goal.currentAmount >= goal.targetAmount) return null;
    const remaining = goal.targetAmount - goal.currentAmount;
    const now = new Date();
    const deadline = new Date(goal.deadline);
    const monthsLeft = Math.max(
      (deadline.getFullYear() - now.getFullYear()) * 12 +
        (deadline.getMonth() - now.getMonth()),
      1,
    );
    return Math.ceil(remaining / monthsLeft);
  })();

  return (
    <Card>
      <CardContent className="pt-0">
        {/* Header row */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3 min-w-0">
            {/* SVG Circular Progress Ring */}
            <div className="relative flex-shrink-0" style={{ width: 96, height: 96 }}>
              <svg
                width="96"
                height="96"
                viewBox="0 0 96 96"
                className="transform -rotate-90"
              >
                {/* Background ring */}
                <circle
                  cx="48"
                  cy="48"
                  r="40"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="6"
                  className="text-muted/30"
                />
                {/* Progress ring */}
                <circle
                  cx="48"
                  cy="48"
                  r="40"
                  fill="none"
                  stroke={goal.color}
                  strokeWidth="6"
                  strokeLinecap="round"
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  className="transition-all duration-500"
                />
              </svg>
              {/* Percentage label */}
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-xs">{goal.icon}</span>
                <span className="text-sm font-bold">{Math.round(percentage)}%</span>
              </div>
            </div>

            <div className="min-w-0">
              <p className="font-semibold text-sm truncate">{goal.name}</p>
              <Badge
                className={cn('mt-1', statusCfg.className)}
                variant="secondary"
              >
                {statusCfg.label}
              </Badge>
            </div>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8 flex-shrink-0">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onEdit(goal)}>
                <Pencil className="mr-2 h-4 w-4" />
                Edit
              </DropdownMenuItem>
              <DropdownMenuItem
                variant="destructive"
                onClick={() => onDelete(goal.id)}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Amount progress */}
        <div className="flex items-baseline gap-1 mb-2">
          <CurrencyDisplay amount={goal.currentAmount} className="text-base font-bold" />
          <span className="text-xs text-muted-foreground">
            / {formatCurrency(goal.targetAmount)}
          </span>
        </div>

        {/* Deadline */}
        {goal.deadline && (
          <p className="text-xs text-muted-foreground mb-1">
            Deadline: {formatDate(goal.deadline)}
          </p>
        )}

        {/* Monthly contribution needed */}
        {monthlyNeeded !== null && (
          <p className="text-xs text-muted-foreground">
            {formatCurrency(monthlyNeeded)}/mo needed to reach goal
          </p>
        )}
      </CardContent>
    </Card>
  );
}
