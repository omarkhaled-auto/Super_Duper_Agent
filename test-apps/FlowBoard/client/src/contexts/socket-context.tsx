"use client";

// =============================================================================
// Socket Context — manages the WebSocket lifecycle and project room membership
//
// - Connects/disconnects based on auth state (user logged in or out)
// - Provides joinProject / leaveProject for room management
// - Exposes connection status for UI indicators
// - Provides the raw socket instance for direct event subscriptions
// =============================================================================

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import type { Socket } from "socket.io-client";
import {
  getSocket,
  connectSocket,
  disconnectSocket,
  destroySocket,
} from "@/lib/socket";
import { useAuth } from "@/contexts/auth-context";

// ── Socket event constants (mirrored from server) ───────────────────────────
export const SOCKET_EVENTS = {
  TASK_CREATED: "task:created",
  TASK_UPDATED: "task:updated",
  TASK_DELETED: "task:deleted",
  TASK_REORDERED: "task:reordered",
  COMMENT_CREATED: "comment:created",
  COMMENT_DELETED: "comment:deleted",
  PRESENCE_JOIN: "presence:join",
  PRESENCE_LEAVE: "presence:leave",
  PRESENCE_LIST: "presence:list",
  PROJECT_UPDATED: "project:updated",
  JOIN_PROJECT: "join-project",
  LEAVE_PROJECT: "leave-project",
} as const;

export type SocketEventName = (typeof SOCKET_EVENTS)[keyof typeof SOCKET_EVENTS];

// ── Connection status ───────────────────────────────────────────────────────
export type ConnectionStatus = "connected" | "connecting" | "disconnected" | "error";

// ── Context value ───────────────────────────────────────────────────────────
interface SocketContextValue {
  /** The Socket.io client instance (or null before initialization). */
  socket: Socket | null;
  /** Current connection status. */
  status: ConnectionStatus;
  /** Whether the socket is connected and ready. */
  isConnected: boolean;
  /** Join a project room to receive real-time events for that project. */
  joinProject: (projectId: string) => void;
  /** Leave a project room to stop receiving events. */
  leaveProject: (projectId: string) => void;
}

const SocketContext = createContext<SocketContextValue | null>(null);

// =============================================================================
// Provider
// =============================================================================

export function SocketProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [status, setStatus] = useState<ConnectionStatus>("disconnected");
  const [socketInstance, setSocketInstance] = useState<Socket | null>(null);

  // Track which project rooms we've joined so we can rejoin on reconnect
  const joinedProjectsRef = useRef<Set<string>>(new Set());

  // ── Connect / disconnect based on auth state ──────────────────────────
  useEffect(() => {
    if (!user) {
      // User logged out — destroy the socket entirely
      destroySocket();
      setSocketInstance(null);
      setStatus("disconnected");
      joinedProjectsRef.current.clear();
      return;
    }

    // User is logged in — establish the WebSocket connection
    const socket = getSocket();
    setSocketInstance(socket);

    // ── Socket lifecycle events ──────────────────────────────────────
    const onConnect = () => {
      setStatus("connected");
      console.log("[Socket] Connected:", socket.id);

      // Rejoin any project rooms we were in before reconnect
      for (const projectId of joinedProjectsRef.current) {
        socket.emit(SOCKET_EVENTS.JOIN_PROJECT, projectId);
      }
    };

    const onDisconnect = (reason: string) => {
      setStatus("disconnected");
      console.log("[Socket] Disconnected:", reason);
    };

    const onConnectError = (error: Error) => {
      setStatus("error");
      console.error("[Socket] Connection error:", error.message);
    };

    const onReconnectAttempt = () => {
      setStatus("connecting");
    };

    socket.on("connect", onConnect);
    socket.on("disconnect", onDisconnect);
    socket.on("connect_error", onConnectError);
    socket.io.on("reconnect_attempt", onReconnectAttempt);

    // Initiate the connection
    setStatus("connecting");
    connectSocket();

    return () => {
      socket.off("connect", onConnect);
      socket.off("disconnect", onDisconnect);
      socket.off("connect_error", onConnectError);
      socket.io.off("reconnect_attempt", onReconnectAttempt);
    };
  }, [user]);

  // ── Join a project room ───────────────────────────────────────────────
  const joinProject = useCallback(
    (projectId: string) => {
      if (!projectId) return;

      joinedProjectsRef.current.add(projectId);

      if (socketInstance?.connected) {
        socketInstance.emit(SOCKET_EVENTS.JOIN_PROJECT, projectId);
      }
    },
    [socketInstance],
  );

  // ── Leave a project room ──────────────────────────────────────────────
  const leaveProject = useCallback(
    (projectId: string) => {
      if (!projectId) return;

      joinedProjectsRef.current.delete(projectId);

      if (socketInstance?.connected) {
        socketInstance.emit(SOCKET_EVENTS.LEAVE_PROJECT, projectId);
      }
    },
    [socketInstance],
  );

  // ── Memoize context value ─────────────────────────────────────────────
  const value = useMemo<SocketContextValue>(
    () => ({
      socket: socketInstance,
      status,
      isConnected: status === "connected",
      joinProject,
      leaveProject,
    }),
    [socketInstance, status, joinProject, leaveProject],
  );

  return (
    <SocketContext.Provider value={value}>{children}</SocketContext.Provider>
  );
}

// =============================================================================
// Hook
// =============================================================================

/**
 * Access the socket context. Must be used inside a `<SocketProvider>`.
 *
 * @example
 * const { socket, isConnected, joinProject, leaveProject } = useSocket();
 */
export function useSocket(): SocketContextValue {
  const ctx = useContext(SocketContext);
  if (!ctx) {
    throw new Error("useSocket must be used within a <SocketProvider>");
  }
  return ctx;
}
