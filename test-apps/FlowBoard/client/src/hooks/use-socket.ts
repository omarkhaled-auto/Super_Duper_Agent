"use client";

// =============================================================================
// useSocket — Backward-compatible re-export
//
// This file re-exports the useSocket hook from the socket context and
// the useSocketEvent hook for direct event subscriptions.
// Existing consumers that import from "@/hooks/use-socket" will continue
// to work without changes.
// =============================================================================

export { useSocket } from "@/contexts/socket-context";
export { useSocketEvent, useSocketEvents } from "@/hooks/use-socket-events";
