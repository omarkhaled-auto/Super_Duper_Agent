"use client";

import * as React from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { cn, formatRelativeDate } from "@/lib/utils";

import { useTaskPanelStore } from "@/stores/task-panel-store";
import { useTaskDetail } from "@/hooks/use-task-detail";
import { useMembers } from "@/hooks/use-members";
import { TaskMetadata } from "./task-metadata";
import { TaskDescription } from "./task-description";
import { SubTaskList } from "./sub-task-list";
import { TaskLabels } from "./task-labels";
import { CommentSection } from "./comment-section";
import { ActivityLog } from "./activity-log";

// =============================================================================
// Task Detail Panel — Linear-inspired slide-over panel
//
// 480px wide, slides from right.
// Controlled by useTaskPanelStore (Zustand).
// Sections:
//   - Header: editable title + close
//   - Metadata: status, priority, assignee, due date
//   - Description: markdown editor
//   - Sub-tasks
//   - Labels
//   - Tabs: Comments | Activity
//   - Timestamps footer
//
// Keyboard: Escape to close
// Loading: skeleton while fetching
// Auto-save: debounced for title/description
//
// Responsive behavior:
//   Mobile (<768px): Full-screen overlay, no side margin, full height
//   Tablet+ (768px+): 480px side panel from right
// =============================================================================

export function TaskDetailPanel() {
  const { isOpen, taskId, closePanel } = useTaskPanelStore();

  const {
    task,
    comments,
    activities,
    projectLabels,
    isLoading,
    error,
    updateField,
    addComment,
    deleteComment,
    addSubTask,
    toggleSubTask,
    deleteSubTask,
    toggleLabel,
    createLabel,
    fetchComments,
    fetchActivities,
  } = useTaskDetail(isOpen ? taskId : null);

  // Fetch members for the assignee picker
  const { members } = useMembers(task?.projectId ?? "");

  // ---------------------------------------------------------------------------
  // Editable title
  // ---------------------------------------------------------------------------

  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [titleValue, setTitleValue] = useState("");
  const titleInputRef = useRef<HTMLInputElement>(null);
  const titleSaveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(
    null,
  );

  // Sync title when task loads or changes externally
  useEffect(() => {
    if (task && !isEditingTitle) {
      setTitleValue(task.title);
    }
  }, [task, isEditingTitle]);

  const handleTitleStartEdit = useCallback(() => {
    setIsEditingTitle(true);
    setTimeout(() => {
      titleInputRef.current?.focus();
      titleInputRef.current?.select();
    }, 0);
  }, []);

  const handleTitleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const val = e.target.value;
      setTitleValue(val);

      // Debounced auto-save
      if (titleSaveTimeoutRef.current) {
        clearTimeout(titleSaveTimeoutRef.current);
      }
      titleSaveTimeoutRef.current = setTimeout(() => {
        if (val.trim()) {
          updateField("title", val.trim());
        }
      }, 500);
    },
    [updateField],
  );

  const handleTitleBlur = useCallback(() => {
    setIsEditingTitle(false);
    if (titleSaveTimeoutRef.current) {
      clearTimeout(titleSaveTimeoutRef.current);
    }
    const trimmed = titleValue.trim();
    if (trimmed && trimmed !== task?.title) {
      updateField("title", trimmed);
    } else if (!trimmed && task) {
      // Revert to original if empty
      setTitleValue(task.title);
    }
  }, [titleValue, task, updateField]);

  const handleTitleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        e.preventDefault();
        titleInputRef.current?.blur();
      }
      if (e.key === "Escape") {
        // Revert and close edit
        if (task) {
          setTitleValue(task.title);
        }
        setIsEditingTitle(false);
      }
    },
    [task],
  );

  // Cleanup title save timeout
  useEffect(() => {
    return () => {
      if (titleSaveTimeoutRef.current) {
        clearTimeout(titleSaveTimeoutRef.current);
      }
    };
  }, []);

  // ---------------------------------------------------------------------------
  // Description save handler
  // ---------------------------------------------------------------------------

  const handleDescriptionSave = useCallback(
    async (value: string | null) => {
      await updateField("description", value);
    },
    [updateField],
  );

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && closePanel()}>
      <SheetContent
        side="right"
        className={cn(
          // Mobile: full-screen overlay
          "w-full h-full",
          // Tablet+: 480px side panel
          "md:w-[480px] md:max-w-[100vw]",
          // Common
          "p-0 flex flex-col",
        )}
        onEscapeKeyDown={closePanel}
      >
        {/* Accessible title (hidden, required by Radix) */}
        <SheetTitle className="sr-only">Task Details</SheetTitle>
        <SheetDescription className="sr-only">
          View and edit task details
        </SheetDescription>

        {isLoading ? (
          <LoadingSkeleton />
        ) : error ? (
          <ErrorState message={error} />
        ) : task ? (
          <>
            {/* ---- Mobile close button (visible <768px) ---- */}
            <div className="flex md:hidden items-center justify-between px-4 pt-3 pb-1">
              <span className="text-xs text-text-quaternary font-medium uppercase tracking-wider">
                Task Details
              </span>
              <button
                type="button"
                onClick={closePanel}
                className={cn(
                  "flex items-center justify-center",
                  "h-9 w-9 rounded-md",
                  "text-text-secondary hover:text-text-primary",
                  "hover:bg-surface-hover",
                  "motion-safe:transition-colors duration-fast",
                )}
                aria-label="Close task details"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>

            {/* ---- Header: Editable Title ---- */}
            <div className="px-4 md:px-6 pt-3 md:pt-6 pb-3 pr-4 md:pr-12">
              {isEditingTitle ? (
                <input
                  ref={titleInputRef}
                  value={titleValue}
                  onChange={handleTitleChange}
                  onBlur={handleTitleBlur}
                  onKeyDown={handleTitleKeyDown}
                  className={cn(
                    "w-full text-lg font-semibold font-heading",
                    "text-text-primary bg-transparent",
                    "border-none outline-none",
                    "focus:ring-0 p-0 m-0",
                    "placeholder:text-text-quaternary",
                  )}
                  placeholder="Task title..."
                />
              ) : (
                <h2
                  onClick={handleTitleStartEdit}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      handleTitleStartEdit();
                    }
                  }}
                  role="button"
                  tabIndex={0}
                  className={cn(
                    "text-lg font-semibold font-heading text-text-primary",
                    "cursor-pointer hover:text-primary",
                    "transition-colors duration-fast",
                    "rounded px-1 -mx-1 py-0.5",
                    "hover:bg-surface-hover",
                  )}
                >
                  {task.title}
                </h2>
              )}
              {task.taskNumber !== undefined && (
                <p className="text-xs text-text-quaternary mt-1 select-none">
                  Task #{task.taskNumber}
                </p>
              )}
            </div>

            <Separator />

            {/* ---- Scrollable Content ---- */}
            <ScrollArea className="flex-1">
              <div className="px-4 md:px-6 py-4 space-y-5">
                {/* Metadata */}
                <TaskMetadata
                  task={task}
                  members={members}
                  updateField={updateField}
                />

                <Separator />

                {/* Description */}
                <TaskDescription
                  description={task.description}
                  onSave={handleDescriptionSave}
                />

                <Separator />

                {/* Sub-tasks */}
                <SubTaskList
                  subtasks={task.subtasks}
                  subtaskTotal={task.subtaskTotal}
                  subtaskCompleted={task.subtaskCompleted}
                  onToggle={toggleSubTask}
                  onAdd={addSubTask}
                  onDelete={deleteSubTask}
                />

                <Separator />

                {/* Labels */}
                <TaskLabels
                  labels={task.labels}
                  projectLabels={projectLabels}
                  onToggle={toggleLabel}
                  onCreate={createLabel}
                />

                <Separator />

                {/* Tabs: Comments | Activity */}
                <Tabs defaultValue="comments" className="w-full">
                  <TabsList>
                    <TabsTrigger value="comments">
                      Comments
                      {task.commentCount > 0 && (
                        <span className="ml-1.5 text-[10px] tabular-nums bg-surface-tertiary px-1.5 py-0.5 rounded-full">
                          {task.commentCount}
                        </span>
                      )}
                    </TabsTrigger>
                    <TabsTrigger value="activity">Activity</TabsTrigger>
                  </TabsList>

                  <TabsContent value="comments" className="min-h-[200px]">
                    <CommentSection
                      comments={comments}
                      onAddComment={addComment}
                      onDeleteComment={deleteComment}
                      onMount={fetchComments}
                    />
                  </TabsContent>

                  <TabsContent value="activity" className="min-h-[200px]">
                    <ActivityLog
                      activities={activities}
                      onMount={fetchActivities}
                    />
                  </TabsContent>
                </Tabs>
              </div>

              {/* ---- Footer: Timestamps ---- */}
              <div className="px-4 md:px-6 py-3 border-t border-border-subtle">
                <div className="flex items-center gap-4 text-[11px] text-text-quaternary">
                  <span>Created {formatRelativeDate(task.createdAt)}</span>
                  <span className="h-3 w-px bg-border-subtle" />
                  <span>Updated {formatRelativeDate(task.updatedAt)}</span>
                </div>
              </div>
            </ScrollArea>
          </>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}

// =============================================================================
// Loading Skeleton
// =============================================================================

function LoadingSkeleton() {
  return (
    <div className="px-4 md:px-6 py-6 space-y-6 motion-safe:animate-pulse">
      {/* Title skeleton */}
      <div className="space-y-2">
        <div className="h-6 w-3/4 bg-surface-tertiary rounded" />
        <div className="h-3 w-1/4 bg-surface-tertiary rounded" />
      </div>

      <div className="h-px bg-border-subtle" />

      {/* Metadata skeleton */}
      <div className="space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex items-center gap-3">
            <div className="h-3 w-[80px] bg-surface-tertiary rounded" />
            <div className="h-8 w-[160px] bg-surface-tertiary rounded" />
          </div>
        ))}
      </div>

      <div className="h-px bg-border-subtle" />

      {/* Description skeleton */}
      <div className="space-y-2">
        <div className="h-3 w-20 bg-surface-tertiary rounded" />
        <div className="h-[80px] w-full bg-surface-tertiary rounded" />
      </div>

      <div className="h-px bg-border-subtle" />

      {/* Sub-tasks skeleton */}
      <div className="space-y-2">
        <div className="h-3 w-16 bg-surface-tertiary rounded" />
        <div className="h-8 w-full bg-surface-tertiary rounded" />
        <div className="h-8 w-full bg-surface-tertiary rounded" />
      </div>

      <div className="h-px bg-border-subtle" />

      {/* Labels skeleton */}
      <div className="space-y-2">
        <div className="h-3 w-12 bg-surface-tertiary rounded" />
        <div className="flex gap-2">
          <div className="h-5 w-16 bg-surface-tertiary rounded-full" />
          <div className="h-5 w-20 bg-surface-tertiary rounded-full" />
        </div>
      </div>

      <div className="h-px bg-border-subtle" />

      {/* Tabs skeleton */}
      <div className="space-y-3">
        <div className="flex gap-4">
          <div className="h-6 w-20 bg-surface-tertiary rounded" />
          <div className="h-6 w-16 bg-surface-tertiary rounded" />
        </div>
        <div className="h-[100px] w-full bg-surface-tertiary rounded" />
      </div>
    </div>
  );
}

// =============================================================================
// Error State
// =============================================================================

function ErrorState({ message }: { message: string }) {
  const closePanel = useTaskPanelStore((s) => s.closePanel);

  return (
    <div className="flex flex-col items-center justify-center h-full px-6 py-12 text-center">
      <div className="h-12 w-12 rounded-full bg-destructive/10 flex items-center justify-center mb-4">
        <span className="text-destructive text-lg font-bold">!</span>
      </div>
      <h3 className="text-sm font-medium text-text-primary mb-1">
        Failed to load task
      </h3>
      <p className="text-xs text-text-secondary mb-4">{message}</p>
      <button
        type="button"
        onClick={closePanel}
        className={cn(
          "text-xs text-primary hover:text-primary/80",
          "transition-colors duration-fast",
        )}
      >
        Close panel
      </button>
    </div>
  );
}
