// =============================================================================
// FlowBoard Server — Main Entry Point
//
// Imports the Express app from app.ts, attaches Socket.io, and starts the
// HTTP server. The app is defined separately in app.ts so tests can import it
// without triggering server.listen().
// =============================================================================

import http from "http";
import app from "./app";
import { initSocketServer } from "./socket";

// ---------------------------------------------------------------------------
// Environment
// ---------------------------------------------------------------------------
const PORT = parseInt(process.env.PORT ?? "3001", 10);
const CLIENT_URL = process.env.CLIENT_URL ?? "http://localhost:3000";
const NODE_ENV = process.env.NODE_ENV ?? "development";

// ---------------------------------------------------------------------------
// HTTP Server
// ---------------------------------------------------------------------------
const server = http.createServer(app);

// ---------------------------------------------------------------------------
// Socket.io — real-time event hub with JWT auth, rooms, and presence
// ---------------------------------------------------------------------------
const io = initSocketServer(server);

// Export io so route handlers / services can emit events
export { io };

// ---------------------------------------------------------------------------
// Start Server
// ---------------------------------------------------------------------------
server.listen(PORT, () => {
  console.log(`\n  FlowBoard server running on http://localhost:${PORT}`);
  console.log(`  Environment : ${NODE_ENV}`);
  console.log(`  Client URL  : ${CLIENT_URL}\n`);
});

// ---------------------------------------------------------------------------
// Graceful Shutdown
// ---------------------------------------------------------------------------
function gracefulShutdown(signal: string) {
  console.log(`\n[${signal}] Shutting down gracefully...`);

  server.close(() => {
    console.log("HTTP server closed.");
    io.close(() => {
      console.log("Socket.io server closed.");
      process.exit(0);
    });
  });

  // Force exit if graceful shutdown takes too long (10 seconds)
  setTimeout(() => {
    console.error("Forced shutdown — graceful close timed out.");
    process.exit(1);
  }, 10_000);
}

process.on("SIGINT", () => gracefulShutdown("SIGINT"));
process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));

// Catch unhandled promise rejections
process.on("unhandledRejection", (reason) => {
  console.error("Unhandled Rejection:", reason);
});

// Catch uncaught exceptions
process.on("uncaughtException", (err) => {
  console.error("Uncaught Exception:", err);
  gracefulShutdown("uncaughtException");
});

export default app;
