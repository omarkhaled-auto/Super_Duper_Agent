// =============================================================================
// Activity Types
// =============================================================================

import type { ActivityType } from "./enums";
import type { UserProfile } from "./user";

export interface ActivityEvent {
  id: string;
  type: ActivityType;
  metadata: Record<string, unknown>;
  createdAt: string;
  projectId: string;
  actor: UserProfile;
}
