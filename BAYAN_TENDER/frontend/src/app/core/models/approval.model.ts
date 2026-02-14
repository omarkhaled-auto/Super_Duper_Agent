/**
 * Approval Workflow Models for Bayan Tender Management System
 */

/**
 * Approval Level Status
 */
export type ApprovalLevelStatus =
  | 'waiting'    // Not yet reached in workflow
  | 'active'     // Currently awaiting decision
  | 'approved'   // Approver approved
  | 'rejected'   // Approver rejected
  | 'returned';  // Approver returned for revision

/**
 * Overall Workflow Status
 */
export type ApprovalWorkflowStatus =
  | 'not_initiated' // Workflow hasn't started
  | 'in_progress'   // At least one level pending
  | 'approved'      // All levels approved
  | 'rejected'      // Any level rejected
  | 'returned';     // Any level returned for revision

/**
 * Decision Type for Approvers
 */
export type ApprovalDecision = 'approve' | 'reject' | 'return';

/**
 * Approver User Reference
 */
export interface ApproverUser {
  id: string | number;
  firstName: string;
  lastName: string;
  email: string;
  avatar?: string;
}

/**
 * Approval Level Configuration
 */
export interface ApprovalLevel {
  level: number;
  approver: ApproverUser;
  status: ApprovalLevelStatus;
  deadline?: Date | string;
  decidedAt?: Date | string;
  decision?: ApprovalDecision;
  comment?: string;
}

/**
 * Approval Decision Timeline Entry
 */
export interface ApprovalTimelineEntry {
  id: number;
  level: number;
  approverName: string;
  decision: ApprovalDecision;
  comment?: string;
  timestamp: Date | string;
  avatarUrl?: string;
}

/**
 * Full Approval Workflow
 */
export interface ApprovalWorkflow {
  id: number;
  tenderId: number;
  status: ApprovalWorkflowStatus;
  currentLevel: number;
  levels: ApprovalLevel[];
  initiatedBy: ApproverUser;
  initiatedAt: Date | string;
  completedAt?: Date | string;
  awardPackUrl?: string;
  timeline: ApprovalTimelineEntry[];
}

/**
 * Initiate Approval Workflow DTO
 */
export interface InitiateApprovalDto {
  level1ApproverId: string | number;
  level1Deadline?: Date | string;
  level2ApproverId: string | number;
  level2Deadline?: Date | string;
  level3ApproverId: string | number;
  level3Deadline?: Date | string;
  approverChangeReason?: string;
}

/**
 * Submit Decision DTO
 */
export interface SubmitDecisionDto {
  decision: ApprovalDecision;
  comment?: string;
}

/**
 * Pending Approval Item (for dashboard widget)
 */
export interface PendingApprovalItem {
  id: number;
  tenderId: number;
  tenderTitle: string;
  tenderReference: string;
  tenderValue: number;
  currency: string;
  level: number;
  submittedAt: Date | string;
  deadline?: Date | string;
  isOverdue: boolean;
  isApproaching: boolean;
  initiatorName: string;
}

/**
 * Pending Approvals Response
 */
export interface PendingApprovalsResponse {
  items: PendingApprovalItem[];
  total: number;
}

/**
 * User with Approver role for dropdowns
 */
export interface ApproverOption {
  id: string | number;
  firstName: string;
  lastName: string;
  email: string;
  fullName: string;
}

/**
 * Status configuration for display
 */
export const APPROVAL_LEVEL_STATUS_CONFIG: Record<ApprovalLevelStatus, {
  label: string;
  severity: 'secondary' | 'success' | 'info' | 'warn' | 'danger' | 'contrast';
  icon: string;
}> = {
  waiting: { label: 'Waiting', severity: 'secondary', icon: 'pi-hourglass' },
  active: { label: 'Active', severity: 'info', icon: 'pi-clock' },
  approved: { label: 'Approved', severity: 'success', icon: 'pi-check-circle' },
  rejected: { label: 'Rejected', severity: 'danger', icon: 'pi-times-circle' },
  returned: { label: 'Returned', severity: 'warn', icon: 'pi-replay' }
};

/**
 * Workflow status configuration for display
 */
export const APPROVAL_WORKFLOW_STATUS_CONFIG: Record<ApprovalWorkflowStatus, {
  label: string;
  severity: 'secondary' | 'success' | 'info' | 'warn' | 'danger' | 'contrast';
  icon: string;
}> = {
  not_initiated: { label: 'Not Initiated', severity: 'secondary', icon: 'pi-minus-circle' },
  in_progress: { label: 'In Progress', severity: 'info', icon: 'pi-spin pi-spinner' },
  approved: { label: 'Approved', severity: 'success', icon: 'pi-check-circle' },
  rejected: { label: 'Rejected', severity: 'danger', icon: 'pi-times-circle' },
  returned: { label: 'Returned for Revision', severity: 'warn', icon: 'pi-replay' }
};

/**
 * Decision configuration for display
 */
export const APPROVAL_DECISION_CONFIG: Record<ApprovalDecision, {
  label: string;
  severity: 'secondary' | 'success' | 'info' | 'warn' | 'danger' | 'contrast';
  icon: string;
}> = {
  approve: { label: 'Approve', severity: 'success', icon: 'pi-check' },
  reject: { label: 'Reject', severity: 'danger', icon: 'pi-times' },
  return: { label: 'Return for Revision', severity: 'warn', icon: 'pi-replay' }
};
