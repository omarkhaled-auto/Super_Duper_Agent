"use client";

import { useParams } from "next/navigation";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useBoard } from "@/hooks/use-board";
import { KanbanBoard } from "@/components/board/kanban-board";
import { BoardSkeleton } from "@/components/board/board-skeleton";

// =============================================================================
// Board Page -- Kanban board view for a project
//
// - Fetches tasks grouped by status via useBoard hook
// - Renders the KanbanBoard with drag-and-drop
// - Shows loading skeleton and error states
// =============================================================================

export default function BoardPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;

  const { columns, isLoading, error, moveTask, addTask, updateTask, refetch } =
    useBoard(projectId);

  // ---- Loading state ----
  if (isLoading) {
    return <BoardSkeleton />;
  }

  // ---- Error state ----
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 text-center px-6">
        <div className="rounded-full bg-error-muted p-4">
          <AlertTriangle
            className="h-8 w-8 text-error"
            aria-hidden="true"
          />
        </div>
        <div>
          <h2 className="text-lg font-semibold font-heading text-text-primary">
            Failed to load board
          </h2>
          <p className="mt-1 text-sm text-text-tertiary max-w-md">
            {error}
          </p>
        </div>
        <Button variant="secondary" onClick={() => void refetch()}>
          Try again
        </Button>
      </div>
    );
  }

  // ---- Board view ----
  return (
    <KanbanBoard
      columns={columns}
      projectId={projectId}
      moveTask={moveTask}
      addTask={addTask}
      updateTask={updateTask}
    />
  );
}
