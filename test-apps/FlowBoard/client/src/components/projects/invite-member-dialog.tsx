"use client";

import { useState, useCallback, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { UserPlus } from "lucide-react";
import { ApiError } from "@/lib/api";
import type { ProjectRole } from "@/types";

// =============================================================================
// InviteMemberDialog — invite a user to the project by email
// =============================================================================

interface InviteMemberDialogProps {
  /** Callback that fires when the invite form is submitted. */
  onInvite: (email: string, role: ProjectRole) => Promise<unknown>;
  /** Callback on success for toast notifications etc. */
  onSuccess?: () => void;
  /** Callback on error for toast notifications etc. */
  onError?: (message: string) => void;
  /** Custom trigger element. If omitted a default "Invite" button is rendered. */
  trigger?: React.ReactNode;
}

export function InviteMemberDialog({
  onInvite,
  onSuccess,
  onError,
  trigger,
}: InviteMemberDialogProps) {
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<ProjectRole>("MEMBER");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [fieldError, setFieldError] = useState<string | null>(null);

  // ---------------------------------------------------------------------------
  // Reset form state when dialog opens/closes
  // ---------------------------------------------------------------------------
  const handleOpenChange = useCallback((next: boolean) => {
    setOpen(next);
    if (!next) {
      setEmail("");
      setRole("MEMBER");
      setFieldError(null);
      setIsSubmitting(false);
    }
  }, []);

  // ---------------------------------------------------------------------------
  // Form submit
  // ---------------------------------------------------------------------------
  const handleSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();

      // Basic client-side validation
      const trimmed = email.trim();
      if (!trimmed) {
        setFieldError("Email is required.");
        return;
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
        setFieldError("Please enter a valid email address.");
        return;
      }

      setFieldError(null);
      setIsSubmitting(true);

      try {
        await onInvite(trimmed, role);
        onSuccess?.();
        handleOpenChange(false);
      } catch (err) {
        if (err instanceof ApiError) {
          // If the API returned a field-level error for email, show it inline
          const emailErr = err.errors?.find((e) => e.field === "email");
          if (emailErr) {
            setFieldError(emailErr.message);
          } else {
            setFieldError(err.message);
          }
          onError?.(err.message);
        } else {
          setFieldError("Something went wrong. Please try again.");
          onError?.("Something went wrong. Please try again.");
        }
      } finally {
        setIsSubmitting(false);
      }
    },
    [email, role, onInvite, onSuccess, onError, handleOpenChange],
  );

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        {trigger ?? (
          <Button size="sm">
            <UserPlus className="h-4 w-4 mr-1.5" aria-hidden="true" />
            Invite
          </Button>
        )}
      </DialogTrigger>

      <DialogContent className="sm:max-w-md">
        <form onSubmit={(e) => void handleSubmit(e)}>
          <DialogHeader>
            <DialogTitle>Invite a team member</DialogTitle>
            <DialogDescription>
              Enter an email address to invite someone to this project. They will
              receive a notification if they already have an account.
            </DialogDescription>
          </DialogHeader>

          <div className="mt-5 space-y-4">
            {/* Email */}
            <div className="space-y-2">
              <Label htmlFor="invite-email">Email address</Label>
              <Input
                id="invite-email"
                type="email"
                placeholder="colleague@example.com"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (fieldError) setFieldError(null);
                }}
                error={!!fieldError}
                disabled={isSubmitting}
                autoComplete="email"
                autoFocus
              />
              {fieldError && (
                <p className="text-xs text-destructive" role="alert">
                  {fieldError}
                </p>
              )}
            </div>

            {/* Role */}
            <div className="space-y-2">
              <Label htmlFor="invite-role">Role</Label>
              <Select
                value={role}
                onValueChange={(v) => setRole(v as ProjectRole)}
                disabled={isSubmitting}
              >
                <SelectTrigger id="invite-role" aria-label="Select role">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="MEMBER">
                    <div className="flex flex-col">
                      <span>Member</span>
                      <span className="text-xs text-text-tertiary">
                        Can create and edit tasks
                      </span>
                    </div>
                  </SelectItem>
                  <SelectItem value="VIEWER">
                    <div className="flex flex-col">
                      <span>Viewer</span>
                      <span className="text-xs text-text-tertiary">
                        Can view tasks only
                      </span>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter className="mt-6">
            <Button
              type="button"
              variant="secondary"
              onClick={() => handleOpenChange(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" loading={isSubmitting}>
              <UserPlus className="h-4 w-4 mr-1.5" aria-hidden="true" />
              Send invite
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
