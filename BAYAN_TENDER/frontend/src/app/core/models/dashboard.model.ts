/**
 * Dashboard-related models and interfaces
 */

// =============== Tender Manager Dashboard ===============

export interface TenderManagerDashboard {
  kpis: DashboardKpi[];
  activeTenders: ActiveTender[];
  upcomingDeadlines: DeadlineItem[];
  recentActivity: ActivityFeedItem[];
}

export interface DashboardKpi {
  name: string;
  value: number;
  icon: string;
  color: 'blue' | 'green' | 'orange' | 'red' | 'purple' | 'gray' | string;
  change?: number;
  changeIsPositive?: boolean;
}

export interface ActiveTender {
  id: string;
  reference: string;
  title: string;
  clientName: string;
  status: TenderDashboardStatus;
  statusText: string;
  submissionDeadline: string;
  bidsReceived: number;
  invitedBidders: number;
  daysRemaining: number;
  createdAt: string;
}

export type TenderDashboardStatus = 'Draft' | 'Active' | 'Evaluation' | 'Awarded' | 'Cancelled';

export interface DeadlineItem {
  tenderId: string;
  tenderReference: string;
  tenderTitle: string;
  deadlineType: 'Submission' | 'Clarification' | 'Opening' | string;
  deadline: string;
  daysRemaining: number;
  hoursRemaining: number;
  isOverdue: boolean;
  isUrgent: boolean;
}

export interface ActivityFeedItem {
  id: string;
  activityType: string;
  description: string;
  entityType: string;
  entityId?: string;
  performedBy?: string;
  occurredAt: string;
  icon: string;
  color: string;
}

// =============== Approver Dashboard ===============

export interface ApproverDashboard {
  pendingApprovals: PendingApprovalItem[];
  recentDecisions: RecentDecision[];
  stats: ApprovalStats;
}

export interface PendingApprovalItem {
  workflowId: string;
  tenderId: string;
  tenderReference: string;
  tenderTitle: string;
  clientName: string;
  tenderValue?: number;
  currency: string;
  currentLevel: number;
  totalLevels: number;
  initiatedByName: string;
  submittedAt: string;
  deadline?: string;
  daysUntilDeadline?: number;
  isOverdue: boolean;
  isUrgent: boolean;
}

export interface RecentDecision {
  id: string;
  tenderId: string;
  tenderReference: string;
  tenderTitle: string;
  decision: ApprovalDecisionType;
  decisionText: string;
  comment?: string;
  decidedAt: string;
}

export type ApprovalDecisionType = 'Approve' | 'Reject' | 'ReturnForRevision';

export interface ApprovalStats {
  pendingCount: number;
  approvedCount: number;
  rejectedCount: number;
  returnedCount: number;
  totalThisMonth: number;
  averageResponseTimeHours?: number;
}

// =============== Query Parameters ===============

export interface TenderManagerDashboardParams {
  deadlineDaysAhead?: number;
  activityLimit?: number;
  activeTendersLimit?: number;
}

export interface ApproverDashboardParams {
  recentDecisionsLimit?: number;
}
