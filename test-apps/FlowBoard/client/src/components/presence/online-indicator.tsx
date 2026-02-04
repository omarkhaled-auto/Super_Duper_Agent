"use client";

// =============================================================================
// OnlineIndicator — Shows avatars of users currently viewing the project
//
// - Displays a row of overlapping avatar circles
// - Green dot indicator for online status
// - Tooltip with user names on hover
// - Collapses into "+N more" when too many users are online
// =============================================================================

import { cn } from "@/lib/utils";
import {
  Avatar,
  AvatarImage,
  AvatarFallback,
} from "@/components/ui/avatar";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  TooltipProvider,
} from "@/components/ui/tooltip";
import { usePresence, type OnlineUser } from "@/hooks/use-presence";
import { useSocket } from "@/contexts/socket-context";

// ── Helpers ─────────────────────────────────────────────────────────────────

/** Extract initials from a name (e.g. "John Doe" -> "JD") */
function getInitials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

/** Maximum number of avatars to show before collapsing into "+N" */
const MAX_VISIBLE = 5;

// ── Component Props ─────────────────────────────────────────────────────────

interface OnlineIndicatorProps {
  /** The project ID to show presence for. */
  projectId: string;
  /** Additional className for the root container. */
  className?: string;
  /** Avatar size: "xs" | "sm" | "md". Defaults to "sm". */
  size?: "xs" | "sm";
  /** Whether to show the connection status badge. Defaults to true. */
  showStatus?: boolean;
}

// ── Online User Avatar ──────────────────────────────────────────────────────

function UserAvatar({
  user,
  size = "sm",
}: {
  user: OnlineUser;
  size?: "xs" | "sm";
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div className="relative">
          <Avatar
            size={size}
            className={cn(
              "ring-2 ring-surface-primary",
              "transition-transform hover:scale-110 hover:z-10",
            )}
          >
            {user.avatar ? (
              <AvatarImage src={user.avatar} alt={user.name} />
            ) : null}
            <AvatarFallback>{getInitials(user.name)}</AvatarFallback>
          </Avatar>
          {/* Green online dot */}
          <span
            className={cn(
              "absolute bottom-0 right-0 block rounded-full bg-green-500",
              "ring-2 ring-surface-primary",
              size === "xs" ? "h-1.5 w-1.5" : "h-2 w-2",
            )}
          />
        </div>
      </TooltipTrigger>
      <TooltipContent side="bottom" className="text-xs">
        {user.name}
      </TooltipContent>
    </Tooltip>
  );
}

// ── Main Component ──────────────────────────────────────────────────────────

export function OnlineIndicator({
  projectId,
  className,
  size = "sm",
  showStatus = true,
}: OnlineIndicatorProps) {
  const { onlineUsers, onlineCount } = usePresence(projectId);
  const { status } = useSocket();

  if (onlineCount === 0 && !showStatus) return null;

  const visibleUsers = onlineUsers.slice(0, MAX_VISIBLE);
  const overflow = onlineCount - MAX_VISIBLE;

  return (
    <TooltipProvider delayDuration={200}>
      <div
        className={cn(
          "flex items-center gap-2",
          className,
        )}
      >
        {/* Connection status indicator */}
        {showStatus && (
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex items-center gap-1.5">
                <span
                  className={cn(
                    "block h-2 w-2 rounded-full transition-colors",
                    status === "connected" && "bg-green-500",
                    status === "connecting" && "bg-yellow-500 animate-pulse",
                    status === "disconnected" && "bg-muted-foreground/30",
                    status === "error" && "bg-red-500",
                  )}
                />
                {onlineCount > 0 && (
                  <span className="text-xs text-text-secondary font-body">
                    {onlineCount} online
                  </span>
                )}
              </div>
            </TooltipTrigger>
            <TooltipContent side="bottom">
              {status === "connected" && "Real-time sync active"}
              {status === "connecting" && "Connecting to server..."}
              {status === "disconnected" && "Disconnected from server"}
              {status === "error" && "Connection error — retrying..."}
            </TooltipContent>
          </Tooltip>
        )}

        {/* Avatar stack */}
        {onlineCount > 0 && (
          <div className="flex items-center -space-x-2">
            {visibleUsers.map((user) => (
              <UserAvatar key={user.userId} user={user} size={size} />
            ))}

            {/* Overflow indicator */}
            {overflow > 0 && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <div
                    className={cn(
                      "flex items-center justify-center rounded-full",
                      "bg-surface-tertiary text-text-secondary font-medium font-body",
                      "ring-2 ring-surface-primary",
                      size === "xs" ? "h-6 w-6 text-2xs" : "h-8 w-8 text-xs",
                    )}
                  >
                    +{overflow}
                  </div>
                </TooltipTrigger>
                <TooltipContent side="bottom">
                  <div className="flex flex-col gap-0.5">
                    {onlineUsers.slice(MAX_VISIBLE).map((user) => (
                      <span key={user.userId} className="text-xs">
                        {user.name}
                      </span>
                    ))}
                  </div>
                </TooltipContent>
              </Tooltip>
            )}
          </div>
        )}
      </div>
    </TooltipProvider>
  );
}
