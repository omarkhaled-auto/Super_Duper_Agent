"use client";

import { useState, useCallback, useEffect, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useProjectContext } from "@/contexts/project-context";
import { useMembers } from "@/hooks/use-members";
import api, { ApiError } from "@/lib/api";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

// UI components
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

// Project components
import { ColorPicker } from "@/components/projects/color-picker";
import { IconPicker } from "@/components/projects/icon-picker";
import { MemberList } from "@/components/projects/member-list";
import { InviteMemberDialog } from "@/components/projects/invite-member-dialog";

// Icons
import {
  Settings,
  Users,
  Shield,
  Save,
} from "lucide-react";

import type { Project, ProjectRole } from "@/types";

// =============================================================================
// Project Settings Page
//
// Tabs: General | Members
// - General: edit project name, description, icon, color
// - Members: member list, invite, role change, remove
// Only accessible to project admins.
// =============================================================================

export default function ProjectSettingsPage() {
  const { project, currentMember, isLoading, setProject } =
    useProjectContext();
  const router = useRouter();

  // ---- Guard: only admins can see settings ----
  if (!isLoading && currentMember && currentMember.role !== "ADMIN") {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 text-center px-6">
        <div className="rounded-full bg-surface-tertiary p-4">
          <Shield className="h-8 w-8 text-text-tertiary" aria-hidden="true" />
        </div>
        <div>
          <h2 className="text-lg font-semibold font-heading text-text-primary">
            Admin access required
          </h2>
          <p className="mt-1 text-sm text-text-tertiary max-w-md">
            Only project administrators can access the settings page. Contact a
            project admin if you need changes made.
          </p>
        </div>
        <Button
          variant="secondary"
          onClick={() => router.push(`/projects/${project?.id}/board`)}
        >
          Back to board
        </Button>
      </div>
    );
  }

  // ---- Loading ----
  if (isLoading || !project) {
    return <SettingsSkeleton />;
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-3xl mx-auto px-6 py-8">
        <div className="mb-6">
          <h2 className="text-xl font-semibold font-heading text-text-primary">
            Project Settings
          </h2>
          <p className="mt-1 text-sm text-text-tertiary">
            Manage your project details and team members.
          </p>
        </div>

        <Tabs defaultValue="general" className="space-y-6">
          <TabsList>
            <TabsTrigger value="general" className="gap-1.5">
              <Settings className="h-4 w-4" aria-hidden="true" />
              General
            </TabsTrigger>
            <TabsTrigger value="members" className="gap-1.5">
              <Users className="h-4 w-4" aria-hidden="true" />
              Members
            </TabsTrigger>
          </TabsList>

          {/* General Tab */}
          <TabsContent value="general">
            <GeneralSettingsTab project={project} onSave={setProject} />
          </TabsContent>

          {/* Members Tab */}
          <TabsContent value="members">
            <MembersSettingsTab
              projectId={project.id}
              currentMemberId={currentMember?.id ?? null}
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

// =============================================================================
// General Settings Tab
// =============================================================================

interface GeneralSettingsTabProps {
  project: Project;
  onSave: (project: Project) => void;
}

function GeneralSettingsTab({ project, onSave }: GeneralSettingsTabProps) {
  const [name, setName] = useState(project.name);
  const [description, setDescription] = useState(project.description ?? "");
  const [icon, setIcon] = useState(project.icon ?? "folder");
  const [color, setColor] = useState(project.color ?? "#7c3aed");
  const [isSaving, setIsSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Sync form state when project changes (e.g. from refetch)
  useEffect(() => {
    setName(project.name);
    setDescription(project.description ?? "");
    setIcon(project.icon ?? "folder");
    setColor(project.color ?? "#7c3aed");
  }, [project]);

  const handleSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();

      // Client-side validation
      const newErrors: Record<string, string> = {};
      if (!name.trim()) {
        newErrors["name"] = "Project name is required.";
      } else if (name.trim().length < 2) {
        newErrors["name"] = "Project name must be at least 2 characters.";
      } else if (name.trim().length > 100) {
        newErrors["name"] = "Project name must be 100 characters or fewer.";
      }
      if (description.length > 500) {
        newErrors["description"] =
          "Description must be 500 characters or fewer.";
      }

      if (Object.keys(newErrors).length > 0) {
        setErrors(newErrors);
        return;
      }

      setErrors({});
      setIsSaving(true);

      try {
        const res = await api.patch<Project>(
          `/projects/${project.id}`,
          {
            name: name.trim(),
            description: description.trim() || null,
            icon,
            color,
          },
        );
        onSave(res);
        toast.success("Project updated", {
          description: "Your changes have been saved.",
        });
      } catch (err) {
        if (err instanceof ApiError) {
          // Map field errors
          if (err.errors) {
            const fieldErrors: Record<string, string> = {};
            for (const e of err.errors) {
              fieldErrors[e.field] = e.message;
            }
            setErrors(fieldErrors);
          }
          toast.error("Failed to save", { description: err.message });
        } else {
          toast.error("Something went wrong", {
            description: "Please try again.",
          });
        }
      } finally {
        setIsSaving(false);
      }
    },
    [name, description, icon, color, project.id, onSave],
  );

  const hasChanges =
    name !== project.name ||
    (description || "") !== (project.description || "") ||
    icon !== (project.icon || "folder") ||
    color !== (project.color || "#7c3aed");

  return (
    <form onSubmit={(e) => void handleSubmit(e)} className="space-y-6">
      {/* Project Name */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Project details</CardTitle>
          <CardDescription>
            Update your project name, description, and visual identity.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          {/* Name */}
          <div className="space-y-2">
            <Label htmlFor="project-name">Name</Label>
            <Input
              id="project-name"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                if (errors["name"]) {
                  setErrors((prev) => {
                    const next = { ...prev };
                    delete next["name"];
                    return next;
                  });
                }
              }}
              placeholder="My Project"
              error={!!errors["name"]}
              disabled={isSaving}
              maxLength={100}
            />
            {errors["name"] && (
              <p className="text-xs text-destructive" role="alert">
                {errors["name"]}
              </p>
            )}
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="project-description">Description</Label>
            <textarea
              id="project-description"
              value={description}
              onChange={(e) => {
                setDescription(e.target.value);
                if (errors["description"]) {
                  setErrors((prev) => {
                    const next = { ...prev };
                    delete next["description"];
                    return next;
                  });
                }
              }}
              placeholder="A brief description of what this project is about..."
              disabled={isSaving}
              maxLength={500}
              rows={3}
              className={cn(
                "flex w-full rounded-md font-body",
                "bg-surface-elevated",
                "border border-input",
                "text-text-primary text-sm",
                "ring-offset-background",
                "placeholder:text-text-quaternary",
                "transition-colors duration-fast",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                "disabled:cursor-not-allowed disabled:opacity-50",
                "resize-none px-3 py-2",
                errors["description"] &&
                  "border-error focus-visible:ring-error",
              )}
            />
            <div className="flex justify-between">
              {errors["description"] ? (
                <p className="text-xs text-destructive" role="alert">
                  {errors["description"]}
                </p>
              ) : (
                <span />
              )}
              <span className="text-xs text-text-quaternary">
                {description.length}/500
              </span>
            </div>
          </div>

          <Separator />

          {/* Color */}
          <div className="space-y-2">
            <Label>Color</Label>
            <p className="text-xs text-text-tertiary mb-2">
              Choose a color to identify this project.
            </p>
            <ColorPicker value={color} onChange={setColor} />
          </div>

          <Separator />

          {/* Icon */}
          <div className="space-y-2">
            <Label>Icon</Label>
            <p className="text-xs text-text-tertiary mb-2">
              Pick an icon that represents this project.
            </p>
            <IconPicker value={icon} onChange={setIcon} color={color} />
          </div>
        </CardContent>

        <CardFooter className="flex justify-between pt-4">
          <p className="text-xs text-text-quaternary">
            {hasChanges ? "You have unsaved changes." : "All changes saved."}
          </p>
          <Button type="submit" loading={isSaving} disabled={!hasChanges}>
            <Save className="h-4 w-4 mr-1.5" aria-hidden="true" />
            Save changes
          </Button>
        </CardFooter>
      </Card>
    </form>
  );
}

// =============================================================================
// Members Settings Tab
// =============================================================================

interface MembersSettingsTabProps {
  projectId: string;
  currentMemberId: string | null;
}

function MembersSettingsTab({
  projectId,
  currentMemberId,
}: MembersSettingsTabProps) {
  const {
    members,
    isLoading,
    inviteMember,
    updateRole,
    removeMember,
  } = useMembers(projectId);

  // ---------------------------------------------------------------------------
  // Handlers with toast notifications
  // ---------------------------------------------------------------------------

  const handleRoleChange = useCallback(
    async (memberId: string, role: ProjectRole) => {
      try {
        await updateRole(memberId, role);
        toast.success("Role updated", {
          description: "The member's role has been changed.",
        });
      } catch (err) {
        const message =
          err instanceof ApiError ? err.message : "Failed to update role.";
        toast.error("Error", { description: message });
        throw err; // re-throw so the UI component can handle it
      }
    },
    [updateRole],
  );

  const handleRemove = useCallback(
    async (memberId: string) => {
      try {
        await removeMember(memberId);
        toast.success("Member removed", {
          description: "The member has been removed from the project.",
        });
      } catch (err) {
        const message =
          err instanceof ApiError ? err.message : "Failed to remove member.";
        toast.error("Error", { description: message });
        throw err;
      }
    },
    [removeMember],
  );

  const handleInviteSuccess = useCallback(() => {
    toast.success("Invitation sent", {
      description: "The team member has been invited to the project.",
    });
  }, []);

  const handleInviteError = useCallback((message: string) => {
    toast.error("Invite failed", { description: message });
  }, []);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base">Team members</CardTitle>
            <CardDescription>
              Manage who has access to this project and their roles.
            </CardDescription>
          </div>
          <InviteMemberDialog
            onInvite={inviteMember}
            onSuccess={handleInviteSuccess}
            onError={handleInviteError}
          />
        </div>
      </CardHeader>

      <CardContent>
        {/* Member count */}
        {!isLoading && members.length > 0 && (
          <p className="text-xs text-text-tertiary mb-3">
            {members.length} member{members.length !== 1 ? "s" : ""}
          </p>
        )}

        <MemberList
          members={members}
          isLoading={isLoading}
          isAdmin={true}
          currentMemberId={currentMemberId}
          onRoleChange={handleRoleChange}
          onRemove={handleRemove}
        />
      </CardContent>
    </Card>
  );
}

// =============================================================================
// Loading Skeleton
// =============================================================================

function SettingsSkeleton() {
  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-3xl mx-auto px-6 py-8">
        <div className="mb-6 space-y-2">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-4 w-72" />
        </div>

        <div className="flex gap-2 mb-6">
          <Skeleton className="h-10 w-24" />
          <Skeleton className="h-10 w-24" />
        </div>

        <div className="space-y-4">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
      </div>
    </div>
  );
}
