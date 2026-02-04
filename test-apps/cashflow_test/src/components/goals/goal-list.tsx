import { GoalCard } from '@/components/goals/goal-card';
import type { Goal } from '@/types';

// ---------------------------------------------------------------------------
// GoalList (TASK-056)
// Responsive grid of GoalCard components.
// ---------------------------------------------------------------------------

interface GoalListProps {
  goals: Goal[];
  onEdit: (goal: Goal) => void;
  onDelete: (id: string) => void;
}

export function GoalList({ goals, onEdit, onDelete }: GoalListProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {goals.map((goal) => (
        <GoalCard
          key={goal.id}
          goal={goal}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}
