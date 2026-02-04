import { useState, useEffect, useCallback } from "react";
import api, { ApiError } from "@/lib/api";
import type { ProjectMember, ProjectRole } from "@/types";

// =============================================================================
// useMembers — manage project members (list, invite, update role, remove)
// =============================================================================

interface UseMembersReturn {
  /** List of project members. */
  members: ProjectMember[];
  /** True while the member list is being loaded. */
  isLoading: boolean;
  /** Non-null if the fetch failed. */
  error: string | null;
  /** Re-fetch the member list. */
  refetch: () => Promise<void>;
  /**
   * Invite a user to the project by email.
   * @returns The newly created ProjectMember on success.
   */
  inviteMember: (email: string, role: ProjectRole) => Promise<ProjectMember>;
  /**
   * Change an existing member's role.
   * @returns The updated ProjectMember on success.
   */
  updateRole: (memberId: string, role: ProjectRole) => Promise<ProjectMember>;
  /**
   * Remove a member from the project.
   */
  removeMember: (memberId: string) => Promise<void>;
}

/**
 * Hook that manages the members for a given project.
 *
 * Endpoints consumed:
 *  - `GET    /api/projects/:id/members`
 *  - `POST   /api/projects/:id/members`         (invite)
 *  - `PATCH  /api/projects/:id/members/:mid`     (role change)
 *  - `DELETE /api/projects/:id/members/:mid`     (remove)
 */
export function useMembers(projectId: string): UseMembersReturn {
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // ---------------------------------------------------------------------------
  // Fetch all members
  // ---------------------------------------------------------------------------
  const fetchMembers = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const res = await api.get<ProjectMember[]>(
        `/projects/${projectId}/members`,
      );
      setMembers(res);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load members.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    void fetchMembers();
  }, [fetchMembers]);

  // ---------------------------------------------------------------------------
  // Invite a member
  // ---------------------------------------------------------------------------
  const inviteMember = useCallback(
    async (email: string, role: ProjectRole): Promise<ProjectMember> => {
      const res = await api.post<ProjectMember>(
        `/projects/${projectId}/members`,
        { email, role },
      );
      // Append new member to local state
      setMembers((prev) => [...prev, res]);
      return res;
    },
    [projectId],
  );

  // ---------------------------------------------------------------------------
  // Update a member's role
  // ---------------------------------------------------------------------------
  const updateRole = useCallback(
    async (memberId: string, role: ProjectRole): Promise<ProjectMember> => {
      const res = await api.patch<ProjectMember>(
        `/projects/${projectId}/members/${memberId}`,
        { role },
      );
      // Update member in local state
      setMembers((prev) =>
        prev.map((m) => (m.id === memberId ? res : m)),
      );
      return res;
    },
    [projectId],
  );

  // ---------------------------------------------------------------------------
  // Remove a member
  // ---------------------------------------------------------------------------
  const removeMember = useCallback(
    async (memberId: string): Promise<void> => {
      await api.del(`/projects/${projectId}/members/${memberId}`);
      // Remove from local state
      setMembers((prev) => prev.filter((m) => m.id !== memberId));
    },
    [projectId],
  );

  return {
    members,
    isLoading,
    error,
    refetch: fetchMembers,
    inviteMember,
    updateRole,
    removeMember,
  };
}
