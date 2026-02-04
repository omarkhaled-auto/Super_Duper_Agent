"use client";

import * as React from "react";
import { useState, useCallback, useRef, useEffect } from "react";
import { Send, Trash2 } from "lucide-react";
import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { formatRelativeDate } from "@/lib/utils";
import type { Comment } from "@/types";

// =============================================================================
// Comment Section — list of comments + add new comment form
//
// Features:
//   - Chronological list of comments with author info
//   - Relative timestamps (e.g., "5 minutes ago")
//   - Expandable textarea for new comments
//   - Submit on Cmd/Ctrl+Enter
//   - Optimistic add (immediate display)
//   - Delete button on own comments (hover)
// =============================================================================

interface CommentSectionProps {
  comments: Comment[];
  onAddComment: (content: string) => Promise<void>;
  onDeleteComment: (commentId: string) => Promise<void>;
  onMount?: () => void;
}

export function CommentSection({
  comments,
  onAddComment,
  onDeleteComment,
  onMount,
}: CommentSectionProps) {
  const [newComment, setNewComment] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const listEndRef = useRef<HTMLDivElement>(null);

  // Fetch comments on mount
  useEffect(() => {
    onMount?.();
  }, [onMount]);

  // Auto-scroll to bottom when new comments are added
  useEffect(() => {
    listEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [comments.length]);

  // ---------------------------------------------------------------------------
  // Auto-resize textarea
  // ---------------------------------------------------------------------------

  const autoResize = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
  }, []);

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  const handleSubmit = useCallback(async () => {
    const trimmed = newComment.trim();
    if (!trimmed || isSubmitting) return;

    setIsSubmitting(true);
    setNewComment("");

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    try {
      await onAddComment(trimmed);
    } finally {
      setIsSubmitting(false);
    }
  }, [newComment, isSubmitting, onAddComment]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit],
  );

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="flex flex-col h-full">
      {/* Comment list */}
      <div className="flex-1 space-y-4 overflow-y-auto pb-3">
        {comments.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-sm text-text-quaternary">No comments yet</p>
            <p className="text-xs text-text-quaternary mt-1">
              Be the first to leave a comment
            </p>
          </div>
        ) : (
          comments.map((comment) => (
            <CommentItem
              key={comment.id}
              comment={comment}
              onDelete={onDeleteComment}
            />
          ))
        )}
        <div ref={listEndRef} />
      </div>

      {/* Add comment form */}
      <div className="border-t border-border-subtle pt-3 mt-auto">
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={newComment}
            onChange={(e) => {
              setNewComment(e.target.value);
              autoResize();
            }}
            onKeyDown={handleKeyDown}
            placeholder="Write a comment..."
            rows={1}
            className={cn(
              "w-full resize-none rounded-md px-3 py-2 pr-10 text-sm font-body",
              "bg-surface-elevated border border-input text-text-primary",
              "placeholder:text-text-quaternary",
              "transition-colors duration-fast",
              "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 ring-offset-background",
              "min-h-[36px] max-h-[120px]",
            )}
          />
          <Button
            variant="ghost"
            size="icon"
            className={cn(
              "absolute right-1 bottom-1 h-7 w-7",
              newComment.trim()
                ? "text-primary hover:text-primary"
                : "text-text-quaternary",
            )}
            onClick={handleSubmit}
            disabled={!newComment.trim() || isSubmitting}
          >
            <Send className="h-3.5 w-3.5" />
          </Button>
        </div>
        <p className="text-[10px] text-text-quaternary mt-1 select-none">
          Press{" "}
          <kbd className="px-1 py-0.5 bg-surface-tertiary rounded text-text-tertiary text-[10px]">
            {typeof navigator !== "undefined" &&
            navigator.userAgent.includes("Mac")
              ? "Cmd"
              : "Ctrl"}
            +Enter
          </kbd>{" "}
          to send
        </p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Comment Item
// ---------------------------------------------------------------------------

function CommentItem({
  comment,
  onDelete,
}: {
  comment: Comment;
  onDelete: (id: string) => Promise<void>;
}) {
  const [isHovered, setIsHovered] = useState(false);
  const isTemp = comment.id.startsWith("temp-");

  return (
    <div
      className={cn(
        "group flex gap-2.5",
        isTemp && "opacity-60",
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Author avatar */}
      <Avatar size="sm" className="shrink-0 mt-0.5">
        {comment.author.avatarUrl && (
          <AvatarImage
            src={comment.author.avatarUrl}
            alt={comment.author.name}
          />
        )}
        <AvatarFallback>
          {comment.author.name
            .split(" ")
            .map((p) => p[0])
            .filter(Boolean)
            .slice(0, 2)
            .join("")
            .toUpperCase()}
        </AvatarFallback>
      </Avatar>

      {/* Comment content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-text-primary truncate">
            {comment.author.name}
          </span>
          <span className="text-[11px] text-text-quaternary shrink-0">
            {formatRelativeDate(comment.createdAt)}
          </span>
          {/* Show edited indicator if updatedAt differs from createdAt */}
          {comment.updatedAt !== comment.createdAt && (
            <span className="text-[10px] text-text-quaternary italic">
              (edited)
            </span>
          )}
          {/* Delete button */}
          {isHovered && !isTemp && (
            <button
              type="button"
              onClick={() => onDelete(comment.id)}
              className={cn(
                "ml-auto shrink-0 p-0.5 rounded-sm",
                "text-text-quaternary hover:text-destructive",
                "transition-colors duration-fast",
              )}
              aria-label="Delete comment"
            >
              <Trash2 className="h-3 w-3" />
            </button>
          )}
        </div>
        <p className="text-sm text-text-secondary mt-0.5 whitespace-pre-wrap break-words leading-relaxed">
          {comment.content}
        </p>
      </div>
    </div>
  );
}
