// =============================================================================
// Socket.io Client — Singleton connection manager
//
// - Lazily creates a single Socket.io connection
// - Reads the JWT from localStorage for auth handshake
// - Provides connect / disconnect / reconnect helpers
// - Re-authenticates with a fresh token on reconnect
// =============================================================================

import { io, Socket } from "socket.io-client";
import { WS_URL } from "./utils";

const TOKEN_KEY = "flowboard_token" as const;

let socket: Socket | null = null;

/**
 * Get the current JWT token from localStorage.
 */
function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Get or create the singleton Socket.io client instance.
 *
 * The socket is created with `autoConnect: false` so the SocketProvider
 * can manage the connection lifecycle explicitly.
 */
export function getSocket(): Socket {
  if (!socket) {
    const token = getToken();

    socket = io(WS_URL, {
      autoConnect: false,
      auth: { token },
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1_000,
      reconnectionDelayMax: 10_000,
      timeout: 20_000,
    });

    // On reconnect attempt, refresh the token in case it was refreshed
    socket.on("reconnect_attempt", () => {
      const freshToken = getToken();
      if (socket) {
        socket.auth = { token: freshToken };
      }
    });
  }

  return socket;
}

/**
 * Connect the socket (call after login or on app mount with valid token).
 * Updates the auth token before connecting in case it was refreshed.
 */
export function connectSocket(): void {
  const s = getSocket();

  // Always refresh the auth token before connecting
  const token = getToken();
  s.auth = { token };

  if (!s.connected) {
    s.connect();
  }
}

/**
 * Disconnect the socket (call on logout).
 */
export function disconnectSocket(): void {
  if (socket?.connected) {
    socket.disconnect();
  }
}

/**
 * Destroy the socket instance entirely (used when tokens are cleared).
 * The next call to `getSocket()` will create a fresh instance.
 */
export function destroySocket(): void {
  if (socket) {
    socket.removeAllListeners();
    socket.disconnect();
    socket = null;
  }
}
