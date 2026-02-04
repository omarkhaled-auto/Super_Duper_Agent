import { useEffect, useCallback } from 'react';

// =============================================================================
// useKeyboardShortcut Hook (TASK-019)
// Registers a global keyboard shortcut. Supports modifier keys (Ctrl / Meta).
// Ignores key presses when the user is typing in an input/textarea.
// =============================================================================

export function useKeyboardShortcut(
  key: string,
  callback: () => void,
  options?: { ctrlKey?: boolean; metaKey?: boolean },
) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      const ctrlOrMeta =
        options?.ctrlKey !== undefined
          ? event.ctrlKey
          : options?.metaKey !== undefined
            ? event.metaKey
            : false;

      if (options?.ctrlKey || options?.metaKey) {
        if (
          (event.ctrlKey || event.metaKey) &&
          event.key.toLowerCase() === key.toLowerCase()
        ) {
          event.preventDefault();
          callback();
        }
      } else if (
        event.key.toLowerCase() === key.toLowerCase() &&
        !event.ctrlKey &&
        !event.metaKey &&
        !event.altKey
      ) {
        // Only trigger if no modifier keys unless specified
        const target = event.target as HTMLElement;
        if (
          target.tagName === 'INPUT' ||
          target.tagName === 'TEXTAREA' ||
          target.isContentEditable
        )
          return;
        event.preventDefault();
        callback();
      }
    },
    [key, callback, options],
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}
