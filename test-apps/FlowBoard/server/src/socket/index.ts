// =============================================================================
// Socket.io Server — Real-time event hub
//
// - JWT authentication on every socket handshake
// - Project room management (join / leave)
// - Presence tracking (who is viewing which project)
// - Helper: emitToProject() used by route handlers after DB writes
// =============================================================================

import { Server as HttpServer } from "http";
import { Server, Socket } from "socket.io";
import jwt from "jsonwebtoken";
import type { AuthPayload } from "../middleware/auth";
import { SOCKET_EVENTS } from "./events";
import { prisma } from "../lib/prisma";

// ── Module-level singleton ───────────────────────────────────────────────────
let io: Server;

// Track which users are viewing which projects:
//   projectId -> Map<userId, { socketId, name, avatar }>
const presenceMap = new Map<
  string,
  Map<string, { userId: string; name: string; avatar: string | null }>
>();

// Track which socket belongs to which projects for cleanup on disconnect
const socketProjects = new Map<string, Set<string>>(); // socketId -> Set<projectId>

// =============================================================================
// Initialization
// =============================================================================

const JWT_SECRET = process.env.JWT_SECRET ?? "change-me";
const CLIENT_URL = process.env.CLIENT_URL ?? "http://localhost:3000";

export function initSocketServer(httpServer: HttpServer): Server {
  io = new Server(httpServer, {
    cors: {
      origin: CLIENT_URL,
      credentials: true,
    },
    transports: ["websocket", "polling"],
    pingInterval: 25_000,
    pingTimeout: 20_000,
  });

  // ── JWT Authentication Middleware ──────────────────────────────────────
  io.use(async (socket, next) => {
    const token = socket.handshake.auth.token as string | undefined;

    if (!token) {
      return next(new Error("Authentication required"));
    }

    try {
      const payload = jwt.verify(token, JWT_SECRET) as AuthPayload;

      // Fetch user details for presence display
      const user = await prisma.user.findUnique({
        where: { id: payload.userId },
        select: { id: true, name: true, avatar: true },
      });

      if (!user) {
        return next(new Error("User not found"));
      }

      // Attach user data to the socket for use in event handlers
      socket.data.userId = user.id;
      socket.data.userName = user.name;
      socket.data.userAvatar = user.avatar;
      socket.data.email = payload.email;

      next();
    } catch {
      next(new Error("Invalid or expired token"));
    }
  });

  // ── Connection Handler ────────────────────────────────────────────────
  io.on("connection", (socket: Socket) => {
    const userId = socket.data.userId as string;
    const userName = socket.data.userName as string;
    const userAvatar = socket.data.userAvatar as string | null;

    console.log(`[WS] Connected: ${userName} (${userId}) — socket ${socket.id}`);

    // Initialize socket's project set
    socketProjects.set(socket.id, new Set());

    // ── Join project room ───────────────────────────────────────────
    socket.on(SOCKET_EVENTS.JOIN_PROJECT, (projectId: string) => {
      if (!projectId || typeof projectId !== "string") return;

      const roomName = `project:${projectId}`;
      socket.join(roomName);

      // Track this socket's project membership
      socketProjects.get(socket.id)?.add(projectId);

      // Update presence map
      if (!presenceMap.has(projectId)) {
        presenceMap.set(projectId, new Map());
      }
      presenceMap.get(projectId)!.set(userId, {
        userId,
        name: userName,
        avatar: userAvatar,
      });

      // Notify all clients in the room that this user joined
      io.to(roomName).emit(SOCKET_EVENTS.PRESENCE_JOIN, {
        userId,
        name: userName,
        avatar: userAvatar,
        projectId,
      });

      // Send the full presence list to the newly joined socket
      const onlineUsers = Array.from(presenceMap.get(projectId)?.values() ?? []);
      socket.emit(SOCKET_EVENTS.PRESENCE_LIST, {
        projectId,
        users: onlineUsers,
      });

      console.log(`[WS] ${userName} joined project:${projectId} (${onlineUsers.length} online)`);
    });

    // ── Leave project room ──────────────────────────────────────────
    socket.on(SOCKET_EVENTS.LEAVE_PROJECT, (projectId: string) => {
      if (!projectId || typeof projectId !== "string") return;

      leaveProject(socket, projectId, userId, userName);
    });

    // ── Presence ping (client can emit to stay visible) ─────────────
    socket.on("presence:ping", (projectId: string) => {
      if (!projectId || typeof projectId !== "string") return;

      // Refresh the user's presence entry
      if (presenceMap.has(projectId)) {
        presenceMap.get(projectId)!.set(userId, {
          userId,
          name: userName,
          avatar: userAvatar,
        });
      }
    });

    // ── Disconnect ──────────────────────────────────────────────────
    socket.on("disconnect", (reason) => {
      console.log(`[WS] Disconnected: ${userName} (${userId}) — ${reason}`);

      // Leave all projects this socket was in
      const projects = socketProjects.get(socket.id);
      if (projects) {
        for (const projectId of projects) {
          leaveProject(socket, projectId, userId, userName);
        }
      }
      socketProjects.delete(socket.id);
    });
  });

  return io;
}

// =============================================================================
// Helpers
// =============================================================================

/**
 * Remove a user from a project's presence and notify the room.
 */
function leaveProject(
  socket: Socket,
  projectId: string,
  userId: string,
  userName: string,
): void {
  const roomName = `project:${projectId}`;
  socket.leave(roomName);

  // Remove from socket's tracked projects
  socketProjects.get(socket.id)?.delete(projectId);

  // Remove from presence map
  const projectPresence = presenceMap.get(projectId);
  if (projectPresence) {
    projectPresence.delete(userId);

    // Clean up empty maps
    if (projectPresence.size === 0) {
      presenceMap.delete(projectId);
    }
  }

  // Notify remaining clients
  io.to(roomName).emit(SOCKET_EVENTS.PRESENCE_LEAVE, {
    userId,
    projectId,
  });

  console.log(`[WS] ${userName} left project:${projectId}`);
}

/**
 * Get the Socket.io server instance.
 * Used by route handlers and services to emit events after DB operations.
 */
export function getIO(): Server {
  if (!io) {
    throw new Error("Socket.io not initialized — call initSocketServer() first");
  }
  return io;
}

/**
 * Emit an event to all clients in a project room.
 *
 * @param projectId  The project whose room should receive the event
 * @param event      The event name (use SOCKET_EVENTS constants)
 * @param data       The payload to send
 *
 * @example
 *   emitToProject(task.projectId, SOCKET_EVENTS.TASK_CREATED, task);
 */
export function emitToProject(
  projectId: string,
  event: string,
  data: unknown,
): void {
  try {
    getIO().to(`project:${projectId}`).emit(event, data);
  } catch (err) {
    // Swallow errors so a socket failure never breaks a route handler
    console.error(`[WS] Failed to emit ${event} to project:${projectId}:`, err);
  }
}

// Re-export events for convenience
export { SOCKET_EVENTS } from "./events";
