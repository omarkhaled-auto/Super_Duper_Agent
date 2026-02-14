import { UserRole } from '../models/user.model';

// Keep this aligned with BAYAN_SPECIFICATIONS_CONDENSED.md (Permission Matrix).
export const RoleGroups = {
  tenderLifecycleManagers: [UserRole.ADMIN, UserRole.TENDER_MANAGER] as const,
  boqManagers: [UserRole.ADMIN, UserRole.TENDER_MANAGER, UserRole.COMMERCIAL_ANALYST] as const,
  bidManagers: [UserRole.ADMIN, UserRole.TENDER_MANAGER, UserRole.COMMERCIAL_ANALYST] as const,
  evaluationViewers: [UserRole.ADMIN, UserRole.TENDER_MANAGER, UserRole.COMMERCIAL_ANALYST, UserRole.APPROVER, UserRole.AUDITOR] as const,
  evaluationEditors: [UserRole.ADMIN, UserRole.TENDER_MANAGER, UserRole.COMMERCIAL_ANALYST] as const,
  technicalScorers: [UserRole.TECHNICAL_PANELIST] as const,
  technicalScoresViewers: [UserRole.ADMIN, UserRole.TENDER_MANAGER, UserRole.TECHNICAL_PANELIST, UserRole.APPROVER, UserRole.AUDITOR] as const,
  approvalInitiators: [UserRole.ADMIN, UserRole.TENDER_MANAGER] as const,
  approvalDeciders: [UserRole.APPROVER] as const,
  auditLogViewers: [UserRole.ADMIN, UserRole.AUDITOR] as const,
  vendorPricingViewers: [UserRole.ADMIN, UserRole.TENDER_MANAGER, UserRole.COMMERCIAL_ANALYST, UserRole.AUDITOR] as const,
} as const;

