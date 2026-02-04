import { useState, useMemo, useCallback } from 'react';
import { differenceInMonths } from 'date-fns';
import { Plus, Target } from 'lucide-react';
import { toast } from 'sonner';
import { useGoalStore } from '@/stores/use-goal-store';
import { PageHeader } from '@/components/shared/page-header';
import { EmptyState } from '@/components/shared/empty-state';
import { ConfirmDialog } from '@/components/shared/confirm-dialog';
import { Button } from '@/components/ui/button';
import { GoalSummaryBar } from '@/components/goals/goal-summary-bar';
import { GoalList } from '@/components/goals/goal-list';
import { GoalModal } from '@/components/goals/goal-modal';
import type { Goal, GoalStatus } from '@/types';

// ---------------------------------------------------------------------------
// GoalsPage (TASK-056)
// Full CRUD page for savings/financial goals.
// Computes goal statuses dynamically by comparing current progress
// against expected progress based on the deadline.
// ---------------------------------------------------------------------------

/** Compute dynamic goal status based on deadline progress. */
function computeGoalStatus(goal: Goal): GoalStatus {
  // Already reached the target
  if (goal.currentAmount >= goal.targetAmount) return 'completed';

  // No deadline means we cannot assess ahead/behind
  if (!goal.deadline) return 'on-track';

  const now = new Date();
  const created = new Date(goal.createdAt);
  const deadline = new Date(goal.deadline);

  // If deadline has passed and not completed, it is behind
  if (deadline <= now) return 'behind';

  // Expected progress: linear interpolation between creation and deadline
  const totalMonths = Math.max(differenceInMonths(deadline, created), 1);
  const elapsedMonths = Math.max(differenceInMonths(now, created), 0);
  const expectedProgress = (elapsedMonths / totalMonths) * goal.targetAmount;

  if (goal.currentAmount >= expectedProgress * 1.1) return 'ahead';
  if (goal.currentAmount < expectedProgress * 0.9) return 'behind';
  return 'on-track';
}

export default function GoalsPage() {
  const goals = useGoalStore((s) => s.goals);
  const addGoal = useGoalStore((s) => s.addGoal);
  const updateGoal = useGoalStore((s) => s.updateGoal);
  const deleteGoal = useGoalStore((s) => s.deleteGoal);

  const [modalOpen, setModalOpen] = useState(false);
  const [editItem, setEditItem] = useState<Goal | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  // Apply dynamic statuses to goals
  const goalsWithStatus = useMemo(
    () =>
      goals.map((g) => ({
        ...g,
        status: computeGoalStatus(g),
      })),
    [goals],
  );

  // Summary stats
  const { activeCount, totalSaved, totalTarget } = useMemo(() => {
    const active = goalsWithStatus.filter((g) => g.status !== 'completed');
    return {
      activeCount: active.length,
      totalSaved: goalsWithStatus.reduce((sum, g) => sum + g.currentAmount, 0),
      totalTarget: goalsWithStatus.reduce((sum, g) => sum + g.targetAmount, 0),
    };
  }, [goalsWithStatus]);

  // -------------------------------------------------------------------------
  // Handlers
  // -------------------------------------------------------------------------

  const handleNewGoal = useCallback(() => {
    setEditItem(null);
    setModalOpen(true);
  }, []);

  const handleEdit = useCallback((goal: Goal) => {
    setEditItem(goal);
    setModalOpen(true);
  }, []);

  const handleDeleteRequest = useCallback((id: string) => {
    setDeleteTarget(id);
  }, []);

  const handleConfirmDelete = useCallback(() => {
    if (deleteTarget) {
      deleteGoal(deleteTarget);
      toast.success('Goal deleted');
      setDeleteTarget(null);
    }
  }, [deleteTarget, deleteGoal]);

  const handleSave = useCallback(
    (data: Omit<Goal, 'id' | 'createdAt' | 'updatedAt'>) => {
      if (editItem) {
        updateGoal(editItem.id, data);
        toast.success('Goal updated');
      } else {
        addGoal(data);
        toast.success('Goal created');
      }
      setModalOpen(false);
      setEditItem(null);
    },
    [editItem, addGoal, updateGoal],
  );

  return (
    <div>
      <PageHeader title="Goals" subtitle="Track your savings targets">
        <Button onClick={handleNewGoal}>
          <Plus className="mr-2 h-4 w-4" />
          New Goal
        </Button>
      </PageHeader>

      {goalsWithStatus.length > 0 ? (
        <>
          <GoalSummaryBar
            activeCount={activeCount}
            totalSaved={totalSaved}
            totalTarget={totalTarget}
          />
          <GoalList
            goals={goalsWithStatus}
            onEdit={handleEdit}
            onDelete={handleDeleteRequest}
          />
        </>
      ) : (
        <EmptyState
          icon={Target}
          title="No goals yet"
          description="Create your first savings goal to start tracking your progress toward financial milestones."
          actionLabel="New Goal"
          onAction={handleNewGoal}
        />
      )}

      {/* Create / Edit Modal */}
      <GoalModal
        open={modalOpen}
        onClose={() => {
          setModalOpen(false);
          setEditItem(null);
        }}
        editItem={editItem}
        onSave={handleSave}
      />

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleConfirmDelete}
        title="Delete Goal"
        description="Are you sure you want to delete this goal? This action cannot be undone."
        confirmLabel="Delete"
        variant="destructive"
      />
    </div>
  );
}
