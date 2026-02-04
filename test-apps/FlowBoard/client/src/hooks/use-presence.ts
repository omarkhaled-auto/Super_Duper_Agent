"use client";

// =============================================================================
// usePresence — Track which users are currently viewing a project
//
// - Joins the project room on mount, leaves on unmount
// - Listens for presence:join, presence:leave, presence:list events
// - Returns the list of online users with { userId, name, avatar }
// =============================================================================

import { useCallback, useEffect, useState } from "react";
import { useSocket, SOCKET_EVENTS } from "@/contexts/socket-context";
import { useSocketEvent } from "@/hooks/use-socket-events";

export interface OnlineUser {
  userId: string;
  name: string;
  avatar: string | null;
}

interface PresenceListPayload {
  projectId: string;
  users: OnlineUser[];
}

interface PresenceJoinPayload {
  userId: string;
  name: string;
  avatar: string | null;
  projectId: string;
}

interface PresenceLeavePayload {
  userId: string;
  projectId: string;
}

interface UsePresenceReturn {
  /** Array of users currently viewing the project. */
  onlineUsers: OnlineUser[];
  /** Number of online users. */
  onlineCount: number;
}

/**
 * Hook to track online presence for a specific project.
 *
 * Automatically joins the project room on mount and leaves on unmount.
 * Listens for presence events to maintain the live user list.
 *
 * @param projectId  The project to track presence for
 *
 * @example
 * const { onlineUsers, onlineCount } = usePresence(project.id);
 */
export function usePresence(projectId: string | undefined): UsePresenceReturn {
  const { joinProject, leaveProject } = useSocket();
  const [onlineUsers, setOnlineUsers] = useState<OnlineUser[]>([]);

  // ── Join / leave the project room ─────────────────────────────────────
  useEffect(() => {
    if (!projectId) return;

    joinProject(projectId);

    return () => {
      leaveProject(projectId);
      setOnlineUsers([]);
    };
  }, [projectId, joinProject, leaveProject]);

  // ── Handle the full presence list (sent when we first join) ───────────
  useSocketEvent<PresenceListPayload>(
    SOCKET_EVENTS.PRESENCE_LIST,
    useCallback(
      (data) => {
        if (data.projectId === projectId) {
          setOnlineUsers(data.users);
        }
      },
      [projectId],
    ),
  );

  // ── Handle a user joining ─────────────────────────────────────────────
  useSocketEvent<PresenceJoinPayload>(
    SOCKET_EVENTS.PRESENCE_JOIN,
    useCallback(
      (data) => {
        if (data.projectId !== projectId) return;

        setOnlineUsers((prev) => {
          // Avoid duplicates
          if (prev.some((u) => u.userId === data.userId)) return prev;
          return [
            ...prev,
            { userId: data.userId, name: data.name, avatar: data.avatar },
          ];
        });
      },
      [projectId],
    ),
  );

  // ── Handle a user leaving ─────────────────────────────────────────────
  useSocketEvent<PresenceLeavePayload>(
    SOCKET_EVENTS.PRESENCE_LEAVE,
    useCallback(
      (data) => {
        if (data.projectId !== projectId) return;

        setOnlineUsers((prev) =>
          prev.filter((u) => u.userId !== data.userId),
        );
      },
      [projectId],
    ),
  );

  return {
    onlineUsers,
    onlineCount: onlineUsers.length,
  };
}
