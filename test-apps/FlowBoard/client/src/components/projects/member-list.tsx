"use client";

import { useState, useCallback } from "react";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { MoreHorizontal, Shield, UserMinus, Crown } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { ProjectMember, ProjectRole } from "@/types";

// =============================================================================
// MemberList — displays project members with role management for admins
// =============================================================================

/** Maps a role to a human-readable label. */
function roleLabel(role: ProjectRole): string {
  switch (role) {
    case "ADMIN":
      return "Admin";
    case "MEMBER":
      return "Member";
    case "VIEWER":
      return "Viewer";
    default:
      return role;
  }
}

/** Maps a role to a badge variant-friendly class. */
function roleBadgeClass(role: ProjectRole): string {
  switch (role) {
    case "ADMIN":
      return "bg-primary/15 text-primary border-primary/25";
    case "MEMBER":
      return "bg-emerald-500/15 text-emerald-600 border-emerald-500/25";
    case "VIEWER":
      return "bg-sky-500/15 text-sky-600 border-sky-500/25";
    default:
      return "";
  }
}

/** Get initials from a user name. */
function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface MemberListProps {
  /** The list of project members to display. */
  members: ProjectMember[];
  /** Whether the member list is currently loading. */
  isLoading: boolean;
  /** Whether the current user has admin rights. */
  isAdmin: boolean;
  /** The current user's member ID (to prevent self-removal). */
  currentMemberId: string | null;
  /** Callback to change a member's role. */
  onRoleChange: (memberId: string, newRole: ProjectRole) => Promise<void>;
  /** Callback to remove a member. */
  onRemove: (memberId: string) => Promise<void>;
  /** Optional class name. */
  className?: string;
}

export function MemberList({
  members,
  isLoading,
  isAdmin,
  currentMemberId,
  onRoleChange,
  onRemove,
  className,
}: MemberListProps) {
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingRemove, setPendingRemove] = useState<ProjectMember | null>(null);
  const [updatingRoleId, setUpdatingRoleId] = useState<string | null>(null);

  // ---------------------------------------------------------------------------
  // Role change handler
  // ---------------------------------------------------------------------------
  const handleRoleChange = useCallback(
    async (memberId: string, role: ProjectRole) => {
      setUpdatingRoleId(memberId);
      try {
        await onRoleChange(memberId, role);
      } finally {
        setUpdatingRoleId(null);
      }
    },
    [onRoleChange],
  );

  // ---------------------------------------------------------------------------
  // Remove with confirmation
  // ---------------------------------------------------------------------------
  const openRemoveConfirm = useCallback((member: ProjectMember) => {
    setPendingRemove(member);
    setConfirmOpen(true);
  }, []);

  const confirmRemove = useCallback(async () => {
    if (!pendingRemove) return;
    setRemovingId(pendingRemove.id);
    try {
      await onRemove(pendingRemove.id);
    } finally {
      setRemovingId(null);
      setConfirmOpen(false);
      setPendingRemove(null);
    }
  }, [pendingRemove, onRemove]);

  // ---------------------------------------------------------------------------
  // Loading skeleton
  // ---------------------------------------------------------------------------
  if (isLoading) {
    return (
      <div className={cn("space-y-3", className)}>
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3 p-3">
            <Skeleton className="h-10 w-10 rounded-full" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-3 w-48" />
            </div>
            <Skeleton className="h-6 w-16 rounded-full" />
          </div>
        ))}
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Empty state
  // ---------------------------------------------------------------------------
  if (members.length === 0) {
    return (
      <div
        className={cn(
          "flex flex-col items-center justify-center py-12 text-center",
          className,
        )}
      >
        <div className="rounded-full bg-surface-tertiary p-4 mb-3">
          <Shield className="h-6 w-6 text-text-tertiary" aria-hidden="true" />
        </div>
        <p className="text-sm font-medium text-text-primary">No members yet</p>
        <p className="mt-1 text-sm text-text-tertiary">
          Invite team members to start collaborating.
        </p>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Member list
  // ---------------------------------------------------------------------------
  return (
    <>
      <div className={cn("divide-y divide-border-subtle rounded-lg border border-border-subtle", className)}>
        {members.map((member) => {
          const isSelf = member.id === currentMemberId;
          const isBeingRemoved = removingId === member.id;
          const isRoleUpdating = updatingRoleId === member.id;

          return (
            <div
              key={member.id}
              className={cn(
                "flex items-center gap-3 px-4 py-3",
                "transition-colors duration-fast",
                isBeingRemoved && "opacity-50",
              )}
            >
              {/* Avatar */}
              <Avatar size="md">
                {member.user.avatarUrl && (
                  <AvatarImage
                    src={member.user.avatarUrl}
                    alt={member.user.name}
                  />
                )}
                <AvatarFallback>
                  {getInitials(member.user.name)}
                </AvatarFallback>
              </Avatar>

              {/* Name & email */}
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-text-primary truncate">
                  {member.user.name}
                  {isSelf && (
                    <span className="ml-1.5 text-xs text-text-tertiary font-normal">
                      (you)
                    </span>
                  )}
                </p>
                <p className="text-xs text-text-tertiary truncate">
                  {member.user.email}
                </p>
              </div>

              {/* Role badge (for non-admins or the member's own row) */}
              {!isAdmin || isSelf ? (
                <Badge
                  variant="outline"
                  size="sm"
                  className={cn("shrink-0", roleBadgeClass(member.role))}
                >
                  {member.role === "ADMIN" && (
                    <Crown className="h-3 w-3 mr-0.5" aria-hidden="true" />
                  )}
                  {roleLabel(member.role)}
                </Badge>
              ) : (
                /* Role change dropdown (admin only, not for self) */
                <Select
                  value={member.role}
                  onValueChange={(val) =>
                    void handleRoleChange(member.id, val as ProjectRole)
                  }
                  disabled={isRoleUpdating}
                >
                  <SelectTrigger
                    className="w-[110px] h-7 text-xs shrink-0"
                    aria-label={`Change role for ${member.user.name}`}
                  >
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ADMIN">Admin</SelectItem>
                    <SelectItem value="MEMBER">Member</SelectItem>
                    <SelectItem value="VIEWER">Viewer</SelectItem>
                  </SelectContent>
                </Select>
              )}

              {/* Actions menu (admin only, not self) */}
              {isAdmin && !isSelf && (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 shrink-0"
                      aria-label={`More actions for ${member.user.name}`}
                    >
                      <MoreHorizontal className="h-4 w-4" aria-hidden="true" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-[180px]">
                    <DropdownMenuItem
                      onClick={() =>
                        void handleRoleChange(
                          member.id,
                          member.role === "ADMIN" ? "MEMBER" : "ADMIN",
                        )
                      }
                    >
                      <Shield className="h-4 w-4 mr-2" aria-hidden="true" />
                      {member.role === "ADMIN"
                        ? "Remove admin"
                        : "Make admin"}
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      className="text-destructive focus:text-destructive"
                      onClick={() => openRemoveConfirm(member)}
                    >
                      <UserMinus className="h-4 w-4 mr-2" aria-hidden="true" />
                      Remove from project
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              )}
            </div>
          );
        })}
      </div>

      {/* Removal confirmation dialog */}
      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove member</DialogTitle>
            <DialogDescription>
              Are you sure you want to remove{" "}
              <span className="font-medium text-text-primary">
                {pendingRemove?.user.name}
              </span>{" "}
              from this project? They will lose access to all project data.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="secondary"
              onClick={() => setConfirmOpen(false)}
              disabled={removingId !== null}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => void confirmRemove()}
              loading={removingId !== null}
            >
              Remove
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
