// =============================================================================
// Project Types
// =============================================================================

import type { ProjectRole } from "./enums";
import type { UserProfile } from "./user";

export interface Project {
  id: string;
  name: string;
  description: string | null;
  icon: string | null;
  color: string | null;
  archived: boolean;
  createdAt: string;
  updatedAt: string;
}

/** Project with aggregated statistics for the dashboard view */
export interface ProjectWithStats extends Project {
  taskCount: number;
  completedTaskCount: number;
  memberCount: number;
}

export interface ProjectMember {
  id: string;
  role: ProjectRole;
  joinedAt: string;
  user: UserProfile;
}
