"use client";

import { useEffect, useRef, useCallback } from "react";

// =============================================================================
// Global Keyboard Shortcuts — FlowBoard
//
// Provides a hook for registering global keyboard shortcuts and a registry
// system so individual components can add/remove their own shortcuts.
//
// Built-in shortcuts:
//   Cmd/Ctrl+K  -> open command palette
//   N           -> create new task (when not in input/textarea)
//   B           -> board view   (when in project context, not in input/textarea)
//   L           -> list view    (when in project context, not in input/textarea)
//   Escape      -> close any open panel/modal
// =============================================================================

/** A registered shortcut handler. */
export interface ShortcutHandler {
  /** Unique identifier for this handler (used for unregistering). */
  id: string;
  /** The key to listen for (lowercase, e.g. "k", "n", "escape"). */
  key: string;
  /** Whether Cmd (Mac) / Ctrl (Win/Linux) must be held. Default: false. */
  meta?: boolean;
  /** Whether Shift must be held. Default: false. */
  shift?: boolean;
  /**
   * If true, the handler fires even when focus is on an input/textarea.
   * Default: false — most shortcuts should NOT fire inside inputs.
   */
  allowInInput?: boolean;
  /** Priority for ordering — higher fires first. Default: 0. */
  priority?: number;
  /** The callback to invoke when the shortcut matches. */
  handler: (e: KeyboardEvent) => void;
}

// ---------------------------------------------------------------------------
// Shortcut Registry — singleton shared across all hook instances
// ---------------------------------------------------------------------------

const registry: Map<string, ShortcutHandler> = new Map();

function registerShortcut(shortcut: ShortcutHandler): void {
  registry.set(shortcut.id, shortcut);
}

function unregisterShortcut(id: string): void {
  registry.delete(id);
}

/** Check if the currently focused element is a text input. */
function isInputFocused(): boolean {
  const el = document.activeElement;
  if (!el) return false;

  const tag = el.tagName.toLowerCase();
  if (tag === "input" || tag === "textarea" || tag === "select") return true;
  if ((el as HTMLElement).isContentEditable) return true;

  return false;
}

// ---------------------------------------------------------------------------
// useKeyboardShortcuts — mounts the global keydown listener once
// ---------------------------------------------------------------------------

export interface KeyboardShortcutActions {
  onOpenCommandPalette?: () => void;
  onCreateTask?: () => void;
  onBoardView?: () => void;
  onListView?: () => void;
  onEscape?: () => void;
}

/**
 * Global keyboard shortcuts hook.
 *
 * Mount this once at the dashboard layout level. The provided callbacks
 * are called when the corresponding shortcut fires.
 *
 * Additional shortcuts can be dynamically registered/unregistered by
 * any component via the returned `register` / `unregister` functions.
 */
export function useKeyboardShortcuts(actions: KeyboardShortcutActions = {}) {
  const actionsRef = useRef(actions);
  actionsRef.current = actions;

  // ---------------------------------------------------------------------------
  // Register built-in shortcuts
  // ---------------------------------------------------------------------------
  useEffect(() => {
    // Cmd/Ctrl+K -> Command palette
    registerShortcut({
      id: "__cmd_k",
      key: "k",
      meta: true,
      allowInInput: true,
      priority: 100,
      handler: (e) => {
        e.preventDefault();
        actionsRef.current.onOpenCommandPalette?.();
      },
    });

    // N -> Create new task
    registerShortcut({
      id: "__new_task",
      key: "n",
      priority: 10,
      handler: () => {
        actionsRef.current.onCreateTask?.();
      },
    });

    // B -> Board view
    registerShortcut({
      id: "__board_view",
      key: "b",
      priority: 10,
      handler: () => {
        actionsRef.current.onBoardView?.();
      },
    });

    // L -> List view
    registerShortcut({
      id: "__list_view",
      key: "l",
      priority: 10,
      handler: () => {
        actionsRef.current.onListView?.();
      },
    });

    // Escape -> Close
    registerShortcut({
      id: "__escape",
      key: "escape",
      allowInInput: true,
      priority: 50,
      handler: () => {
        actionsRef.current.onEscape?.();
      },
    });

    return () => {
      unregisterShortcut("__cmd_k");
      unregisterShortcut("__new_task");
      unregisterShortcut("__board_view");
      unregisterShortcut("__list_view");
      unregisterShortcut("__escape");
    };
  }, []);

  // ---------------------------------------------------------------------------
  // Global keydown listener
  // ---------------------------------------------------------------------------
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      const key = e.key.toLowerCase();
      const meta = e.metaKey || e.ctrlKey;
      const shift = e.shiftKey;
      const inputFocused = isInputFocused();

      // Collect matching shortcuts, sorted by priority (highest first)
      const matches = Array.from(registry.values())
        .filter((s) => {
          if (s.key !== key) return false;
          if (s.meta && !meta) return false;
          if (!s.meta && meta && key !== "escape") return false;
          if (s.shift && !shift) return false;
          if (!s.allowInInput && inputFocused) return false;
          return true;
        })
        .sort((a, b) => (b.priority ?? 0) - (a.priority ?? 0));

      // Fire the highest-priority match
      if (matches.length > 0) {
        matches[0].handler(e);
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  // ---------------------------------------------------------------------------
  // Dynamic registration API for external components
  // ---------------------------------------------------------------------------
  const register = useCallback((shortcut: ShortcutHandler) => {
    registerShortcut(shortcut);
  }, []);

  const unregister = useCallback((id: string) => {
    unregisterShortcut(id);
  }, []);

  return { register, unregister };
}
