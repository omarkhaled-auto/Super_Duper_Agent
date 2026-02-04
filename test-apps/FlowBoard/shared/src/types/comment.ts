// =============================================================================
// Comment Types
// =============================================================================

import type { UserProfile } from "./user";

export interface Comment {
  id: string;
  content: string;
  createdAt: string;
  updatedAt: string;
  taskId: string;
  author: UserProfile;
}
