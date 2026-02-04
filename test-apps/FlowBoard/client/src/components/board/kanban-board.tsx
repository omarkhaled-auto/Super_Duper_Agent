"use client";

import { useCallback, useState, useRef, useEffect } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragStartEvent,
  type DragOverEvent,
  type DragEndEvent,
} from "@dnd-kit/core";
import { sortableKeyboardCoordinates } from "@dnd-kit/sortable";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { KanbanColumn } from "./kanban-column";
import { KanbanCard } from "./kanban-card";
import { BOARD_COLUMNS, type ColumnMap } from "@/hooks/use-board";
import api from "@/lib/api";
import type { Task, TaskStatus } from "@/types";

// =============================================================================
// KanbanBoard -- Main board component with drag-and-drop
//
// Uses @dnd-kit/core DndContext with pointer + keyboard sensors.
// Handles onDragStart, onDragOver, and onDragEnd for moving cards
// within and across columns with optimistic updates.
//
// Responsive behavior:
//   Mobile (<768px): Horizontal scroll-snap, each column full-width,
//                     swipe between columns, dot indicators shown
//   Tablet (768px+): Standard horizontal scroll with visible columns
//   Desktop (1024px+): All columns visible with overflow scroll
// =============================================================================

interface KanbanBoardProps {
  columns: ColumnMap;
  projectId: string;
  moveTask: (
    taskId: string,
    newStatus: TaskStatus,
    newPosition: number,
  ) => Promise<void>;
  addTask: (task: Task) => void;
  updateTask: (taskId: string, updates: Partial<Task>) => void;
}

export function KanbanBoard({
  columns,
  projectId,
  moveTask,
  addTask,
  updateTask,
}: KanbanBoardProps) {
  const [activeTask, setActiveTask] = useState<Task | null>(null);
  const previousColumnsRef = useRef<ColumnMap | null>(null);

  // ---- Sensors ----
  const pointerSensor = useSensor(PointerSensor, {
    activationConstraint: {
      // Require 5px of movement before starting a drag.
      // Prevents accidental drags on click.
      distance: 5,
    },
  });

  const keyboardSensor = useSensor(KeyboardSensor, {
    coordinateGetter: sortableKeyboardCoordinates,
  });

  const sensors = useSensors(pointerSensor, keyboardSensor);

  // ---- Find which column a task belongs to ----
  const findColumnForTask = useCallback(
    (taskId: string): TaskStatus | null => {
      for (const status of BOARD_COLUMNS) {
        const key = status as string;
        if (columns[key]?.some((t) => t.id === taskId)) {
          return status;
        }
      }
      return null;
    },
    [columns],
  );

  // ---- Drag handlers ----

  function handleDragStart(event: DragStartEvent) {
    const { active } = event;
    const task = active.data.current?.task as Task | undefined;
    if (task) {
      setActiveTask(task);
      // Save snapshot for potential rollback
      previousColumnsRef.current = { ...columns };
    }
  }

  function handleDragOver(event: DragOverEvent) {
    const { active, over } = event;
    if (!over) return;

    const activeId = active.id as string;
    const overId = over.id as string;

    // Determine source and destination columns
    const activeColumn = findColumnForTask(activeId);
    let overColumn: TaskStatus | null = null;

    // Check if hovering over a column directly
    if (overId.startsWith("column-")) {
      overColumn = overId.replace("column-", "") as TaskStatus;
    } else {
      // Hovering over another task card
      overColumn = findColumnForTask(overId);
    }

    // If source and destination are the same column, no cross-column logic needed
    if (!activeColumn || !overColumn || activeColumn === overColumn) return;

    // No-op here -- we handle the actual move in onDragEnd to prevent
    // excessive re-renders during drag. The visual indication is handled
    // by the column's isOver state from useDroppable.
  }

  async function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    setActiveTask(null);

    if (!over) return;

    const activeId = active.id as string;
    const overId = over.id as string;

    // Determine the source column
    const sourceColumn = findColumnForTask(activeId);
    if (!sourceColumn) return;

    // Determine target column
    let targetColumn: TaskStatus;
    let targetPosition: number;

    if (overId.startsWith("column-")) {
      // Dropped directly on a column (empty area)
      targetColumn = overId.replace("column-", "") as TaskStatus;
      targetPosition = columns[targetColumn as string]?.length ?? 0;
    } else {
      // Dropped on another task card
      const overTaskColumn = findColumnForTask(overId);
      if (!overTaskColumn) return;
      targetColumn = overTaskColumn;

      // Find the position of the task we dropped on
      const overIndex = columns[targetColumn as string]?.findIndex(
        (t) => t.id === overId,
      );
      if (overIndex === undefined || overIndex === -1) {
        targetPosition = columns[targetColumn as string]?.length ?? 0;
      } else {
        // If dragging within the same column
        if (sourceColumn === targetColumn) {
          const activeIndex = columns[sourceColumn as string]?.findIndex(
            (t) => t.id === activeId,
          );
          // If moving down, place after the over item; if moving up, place at the over index
          targetPosition =
            activeIndex !== undefined && activeIndex < overIndex
              ? overIndex
              : overIndex;
        } else {
          // Cross-column: insert at the over item's position
          targetPosition = overIndex;
        }
      }
    }

    // Skip if no actual change
    if (sourceColumn === targetColumn) {
      const currentIndex = columns[sourceColumn as string]?.findIndex(
        (t) => t.id === activeId,
      );
      if (currentIndex === targetPosition) return;
    }

    // Perform the optimistic move + API call
    try {
      await moveTask(activeId, targetColumn, targetPosition);
    } catch {
      toast.error("Failed to move task", {
        description: "The change has been reverted. Please try again.",
      });
    }
  }

  // ---- Inline task creation handler ----
  function handleTaskCreated(task: Task) {
    addTask(task);
  }

  // ---- Inline title update handler ----
  function handleTitleUpdate(taskId: string, newTitle: string) {
    // Optimistic update
    updateTask(taskId, { title: newTitle });

    // Persist to API (fire-and-forget with error toast)
    api
      .patch(`/tasks/${taskId}`, { title: newTitle })
      .catch(() => {
        toast.error("Failed to update task title");
      });
  }

  // ---- Task click handler (dispatch custom event for detail panel) ----
  function handleTaskClick(taskId: string) {
    // Dispatch a custom event that the layout or a task detail panel can listen to
    const event = new CustomEvent("flowboard:open-task", {
      detail: { taskId },
    });
    window.dispatchEvent(event);
  }

  // ---- Mobile scroll-snap: track active column index for dot indicators ----
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [activeColumnIndex, setActiveColumnIndex] = useState(0);

  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    function handleScroll() {
      if (!container) return;
      const scrollLeft = container.scrollLeft;
      const columnWidth = container.clientWidth;
      if (columnWidth > 0) {
        const index = Math.round(scrollLeft / columnWidth);
        setActiveColumnIndex(Math.min(index, BOARD_COLUMNS.length - 1));
      }
    }

    container.addEventListener("scroll", handleScroll, { passive: true });
    return () => container.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
    >
      <div className="flex flex-col h-full">
        <div
          ref={scrollContainerRef}
          className={cn(
            "flex h-full overflow-x-auto",
            // Mobile: scroll-snap for swipe between full-width columns
            "snap-x snap-mandatory md:snap-none",
            // Mobile: no gap (columns are full viewport width)
            // Tablet+: standard gap and padding
            "gap-0 md:gap-4",
            "p-4 md:p-6",
            // Scrollbar styling
            "scrollbar-thin",
            // Hide scrollbar on mobile for cleaner swipe UX
            "max-md:no-scrollbar",
          )}
        >
          {BOARD_COLUMNS.map((status) => (
            <div
              key={status}
              className={cn(
                // Mobile: each column is full width minus padding, snap to center
                "snap-center shrink-0",
                "w-[calc(100vw-2rem)] md:w-auto",
                // Tablet+: use standard kanban column width
                "md:shrink-0",
              )}
            >
              <KanbanColumn
                status={status}
                tasks={columns[status as string] ?? []}
                projectId={projectId}
                onTaskClick={handleTaskClick}
                onTitleUpdate={handleTitleUpdate}
                onTaskCreated={handleTaskCreated}
              />
            </div>
          ))}
        </div>

        {/* Mobile swipe indicators (dots) -- only visible on <768px */}
        <div className="flex md:hidden items-center justify-center gap-1.5 pb-3 pt-1">
          {BOARD_COLUMNS.map((status, index) => (
            <button
              key={status}
              type="button"
              className={cn(
                "h-1.5 rounded-full motion-safe:transition-all motion-safe:duration-200",
                index === activeColumnIndex
                  ? "w-4 bg-primary"
                  : "w-1.5 bg-text-quaternary/50",
              )}
              onClick={() => {
                scrollContainerRef.current?.scrollTo({
                  left: index * (scrollContainerRef.current?.clientWidth ?? 0),
                  behavior: "smooth",
                });
              }}
              aria-label={`Go to column ${index + 1}`}
            />
          ))}
        </div>
      </div>

      {/* Drag overlay -- floating card copy while dragging */}
      <DragOverlay
        dropAnimation={{
          duration: 200,
          easing: "ease-out",
        }}
      >
        {activeTask ? (
          <KanbanCard task={activeTask} isDragOverlay />
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}
