"use client";

// =============================================================================
// useSocketEvent — Subscribe to a specific Socket.io event
//
// - Type-safe event name and callback
// - Automatically subscribes on mount, unsubscribes on unmount
// - Uses a ref for the callback so changing the handler doesn't re-subscribe
// - Safely handles the case where the socket is not yet connected
// =============================================================================

import { useEffect, useRef } from "react";
import { useSocket, type SocketEventName } from "@/contexts/socket-context";

/**
 * Subscribe to a Socket.io event with automatic cleanup.
 *
 * @param event    The event name to listen for (use SOCKET_EVENTS constants)
 * @param callback The handler called when the event fires
 *
 * @example
 * useSocketEvent(SOCKET_EVENTS.TASK_CREATED, (task) => {
 *   console.log("New task:", task);
 * });
 */
export function useSocketEvent<T = unknown>(
  event: SocketEventName | string,
  callback: (data: T) => void,
): void {
  const { socket } = useSocket();
  const callbackRef = useRef(callback);

  // Keep the ref up to date so we always call the latest callback
  callbackRef.current = callback;

  useEffect(() => {
    if (!socket) return;

    const handler = (data: T) => {
      callbackRef.current(data);
    };

    socket.on(event, handler as (...args: unknown[]) => void);

    return () => {
      socket.off(event, handler as (...args: unknown[]) => void);
    };
  }, [socket, event]);
}

/**
 * Subscribe to multiple Socket.io events with a single hook.
 *
 * @param events  A map of event name -> handler
 *
 * @example
 * useSocketEvents({
 *   [SOCKET_EVENTS.TASK_CREATED]: (task) => addTask(task),
 *   [SOCKET_EVENTS.TASK_DELETED]: ({ taskId }) => removeTask(taskId),
 * });
 */
export function useSocketEvents(
  events: Record<string, (data: unknown) => void>,
): void {
  const { socket } = useSocket();
  const eventsRef = useRef(events);

  eventsRef.current = events;

  useEffect(() => {
    if (!socket) return;

    const handlers: Array<[string, (...args: unknown[]) => void]> = [];

    for (const [event, callback] of Object.entries(eventsRef.current)) {
      const handler = (data: unknown) => {
        // Always call the latest version of the callback
        eventsRef.current[event]?.(data);
      };
      socket.on(event, handler);
      handlers.push([event, handler]);
    }

    return () => {
      for (const [event, handler] of handlers) {
        socket.off(event, handler);
      }
    };
    // Re-subscribe when the socket instance changes or event keys change
  }, [socket, Object.keys(events).join(",")]);
}
