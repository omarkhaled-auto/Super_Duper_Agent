"use client";

import * as React from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { Pencil, Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// =============================================================================
// Task Description — Markdown editor with edit/preview toggle
//
// Uses @uiw/react-md-editor for markdown editing.
// Loaded dynamically to avoid SSR issues.
// Auto-saves on blur after a 500ms debounce.
// Dark mode compatible via CSS data attributes.
// =============================================================================

// Dynamic import: MDEditor is not SSR-compatible
const MDEditor = dynamic(() => import("@uiw/react-md-editor"), {
  ssr: false,
  loading: () => (
    <div className="h-[200px] rounded-md bg-surface-elevated animate-pulse" />
  ),
});

// Markdown preview component (for read mode)
const MDPreview = dynamic(
  () => import("@uiw/react-md-editor").then((mod) => mod.default.Markdown),
  {
    ssr: false,
    loading: () => (
      <div className="h-[100px] rounded-md bg-surface-elevated animate-pulse" />
    ),
  },
);

interface TaskDescriptionProps {
  description: string | null;
  onSave: (value: string | null) => Promise<void>;
}

export function TaskDescription({ description, onSave }: TaskDescriptionProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [value, setValue] = useState(description ?? "");
  const saveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isDirtyRef = useRef(false);

  // Sync external changes into local state (when task data refetches)
  useEffect(() => {
    if (!isEditing) {
      setValue(description ?? "");
    }
  }, [description, isEditing]);

  // ---------------------------------------------------------------------------
  // Auto-save with debounce
  // ---------------------------------------------------------------------------

  const debouncedSave = useCallback(
    (newValue: string) => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
      saveTimeoutRef.current = setTimeout(() => {
        const trimmed = newValue.trim();
        onSave(trimmed || null);
        isDirtyRef.current = false;
      }, 500);
    },
    [onSave],
  );

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, []);

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  const handleChange = useCallback(
    (newValue: string | undefined) => {
      const v = newValue ?? "";
      setValue(v);
      isDirtyRef.current = true;
      debouncedSave(v);
    },
    [debouncedSave],
  );

  const handleBlur = useCallback(() => {
    // Flush any pending save immediately
    if (isDirtyRef.current) {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
      const trimmed = value.trim();
      onSave(trimmed || null);
      isDirtyRef.current = false;
    }
    setIsEditing(false);
  }, [value, onSave]);

  const handleStartEditing = useCallback(() => {
    setIsEditing(true);
  }, []);

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold text-text-tertiary uppercase tracking-wider select-none">
          Description
        </h3>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 px-2 text-xs"
          onClick={() => setIsEditing(!isEditing)}
        >
          {isEditing ? (
            <>
              <Eye className="h-3 w-3 mr-1" />
              Preview
            </>
          ) : (
            <>
              <Pencil className="h-3 w-3 mr-1" />
              Edit
            </>
          )}
        </Button>
      </div>

      {isEditing ? (
        <div
          data-color-mode="dark"
          className={cn(
            "rounded-md overflow-hidden",
            "[&_.w-md-editor]:!bg-surface-elevated [&_.w-md-editor]:!border-border",
            "[&_.w-md-editor-toolbar]:!bg-surface-tertiary [&_.w-md-editor-toolbar]:!border-border-subtle",
            "[&_.w-md-editor-text-pre>code]:!font-mono",
            "[&_.w-md-editor-text-input]:!font-body",
            "[&_.w-md-editor-text]:!font-body",
            "[&_.wmde-markdown]:!bg-surface-elevated [&_.wmde-markdown]:!font-body",
            "[&_.wmde-markdown]:!text-text-primary",
          )}
          onBlur={(e) => {
            // Only trigger blur if focus leaves the editor container entirely
            if (!e.currentTarget.contains(e.relatedTarget)) {
              handleBlur();
            }
          }}
        >
          <MDEditor
            value={value}
            onChange={handleChange}
            height={200}
            preview="edit"
            hideToolbar={false}
            visibleDragbar={false}
          />
        </div>
      ) : (
        <div
          onClick={handleStartEditing}
          className={cn(
            "min-h-[60px] rounded-md px-3 py-2 cursor-pointer",
            "bg-surface-elevated/50 hover:bg-surface-hover",
            "transition-colors duration-fast",
            "text-sm font-body",
            !value && "text-text-quaternary italic",
          )}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              handleStartEditing();
            }
          }}
        >
          {value ? (
            <div
              data-color-mode="dark"
              className={cn(
                "[&_.wmde-markdown]:!bg-transparent [&_.wmde-markdown]:!font-body",
                "[&_.wmde-markdown]:!text-text-primary [&_.wmde-markdown]:text-sm",
                "[&_.wmde-markdown_p]:!my-1",
                "[&_.wmde-markdown_h1]:!text-base [&_.wmde-markdown_h1]:!font-semibold",
                "[&_.wmde-markdown_h2]:!text-sm [&_.wmde-markdown_h2]:!font-semibold",
                "[&_.wmde-markdown_code]:!bg-surface-tertiary [&_.wmde-markdown_code]:!text-text-secondary",
                "[&_.wmde-markdown_pre]:!bg-surface-tertiary",
                "[&_.wmde-markdown_a]:!text-primary",
                "[&_.wmde-markdown_ul]:!pl-4 [&_.wmde-markdown_ol]:!pl-4",
              )}
            >
              <MDPreview source={value} />
            </div>
          ) : (
            "Add a description..."
          )}
        </div>
      )}
    </div>
  );
}
