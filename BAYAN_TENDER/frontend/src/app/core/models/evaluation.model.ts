/**
 * Evaluation Module Models
 * Models for tender bid evaluation workflow
 */

// ============================================================================
// ENUMS AND TYPES
// ============================================================================

export type EvaluationStatus =
  | 'pending'      // Not started
  | 'in_progress'  // Panel members scoring
  | 'completed'    // All scores submitted
  | 'locked';      // Scores locked, cannot be changed

export type ScoringMethod = 'numeric' | 'star';

export type ExceptionType = 'technical' | 'commercial' | 'contractual';

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export type ApprovalStatus = 'pending' | 'approved' | 'rejected';

// ============================================================================
// PANEL MEMBER INTERFACES
// ============================================================================

export interface PanelMember {
  id: number;
  userId: number;
  firstName: string;
  lastName: string;
  email: string;
  role: string;
  isLead: boolean;
  assignedAt?: Date | string;
  completedAt?: Date | string;
  status: 'pending' | 'in_progress' | 'completed';
}

export interface PanelMemberOption {
  id: number;
  userId: number;
  firstName: string;
  lastName: string;
  email: string;
  fullName: string;
  department?: string;
  isAvailable: boolean;
}

// ============================================================================
// EVALUATION CRITERIA
// ============================================================================

export interface EvaluationCriterion {
  id: number;
  name: string;
  weight: number;
  description?: string;
  guidanceNotes?: string;
  maxScore: number;
  category: 'technical' | 'commercial';
}

// ============================================================================
// EVALUATION SETUP
// ============================================================================

export interface EvaluationSetup {
  id: number;
  tenderId: number;
  status: EvaluationStatus;
  scoringMethod: ScoringMethod;
  blindMode: boolean;
  deadline: Date | string;
  panelMembers: PanelMember[];
  criteria: EvaluationCriterion[];
  createdAt: Date | string;
  createdBy: number;
  startedAt?: Date | string;
  startedBy?: number;
  completedAt?: Date | string;
  lockedAt?: Date | string;
  lockedBy?: number;
}

export interface CreateEvaluationSetupDto {
  tenderId: number;
  panelMemberIds: number[];
  scoringMethod: ScoringMethod;
  blindMode: boolean;
  deadline: Date | string;
}

// ============================================================================
// TECHNICAL SCORING
// ============================================================================

export interface BidderForScoring {
  id: number;
  bidderId: number;
  bidderName: string;
  blindCode: string;  // "Bidder 001", "Bidder 002", etc.
  isScored: boolean;
  documents: BidderDocument[];
}

export interface BidderDocument {
  id: number;
  type: 'methodology' | 'team_cvs' | 'work_program' | 'hse_plan' | 'other';
  filename: string;
  url: string;
}

export interface CriterionScore {
  criterionId: number;
  score: number;
  comment?: string;
  isDraft: boolean;
}

export interface BidderScoreEntry {
  bidderId: number;
  criteriaScores: CriterionScore[];
  totalScore: number;
  weightedScore: number;
  submittedAt?: Date | string;
  isDraft: boolean;
}

export interface SaveScoreDto {
  tenderId: number;
  bidderId: number;
  criteriaScores: CriterionScore[];
  isDraft: boolean;
}

// ============================================================================
// TECHNICAL SUMMARY
// ============================================================================

export interface PanelistScoreRow {
  panelistId: number;
  panelistName: string;
  scores: Record<number, Record<number, number>>; // bidderId -> criterionId -> score
  completedAt?: Date | string;
}

export interface BidderAggregatedScore {
  bidderId: number;
  bidderName: string;
  blindCode: string;
  criteriaScores: Record<number, {
    scores: number[];
    average: number;
    stdDev: number;
    hasVarianceAlert: boolean;
  }>;
  totalAverage: number;
  rank: number;
  hasVarianceAlerts: boolean;
}

export interface TechnicalSummary {
  tenderId: number;
  status: EvaluationStatus;
  totalPanelists: number;
  completedPanelists: number;
  panelistScores: PanelistScoreRow[];
  aggregatedScores: BidderAggregatedScore[];
  criteria: EvaluationCriterion[];
  bidders: BidderForScoring[];
  varianceThreshold: number;  // StdDev threshold for alerts (default 2)
}

export interface PanelistComment {
  panelistId: number;
  panelistName: string;
  bidderId: number;
  bidderName: string;
  criterionId: number;
  criterionName: string;
  score: number;
  comment: string;
  submittedAt: Date | string;
}

// ============================================================================
// COMBINED SCORECARD
// ============================================================================

export interface ScorecardBidder {
  bidderId: number;
  bidderName: string;
  technicalScore: number;
  technicalRank: number;
  commercialScore: number;
  commercialRank: number;
  combinedScore: number;
  finalRank: number;
  isWinner: boolean;
  isDisqualified: boolean;
}

export interface CombinedScorecard {
  tenderId: number;
  technicalWeight: number;
  commercialWeight: number;
  bidders: ScorecardBidder[];
  recommendedBidderId: number;
  recommendedBidderName: string;
  generatedAt: Date | string;
}

export interface UpdateWeightsDto {
  tenderId: number;
  technicalWeight: number;
  commercialWeight: number;
}

// ============================================================================
// SENSITIVITY ANALYSIS
// ============================================================================

export interface WeightSplit {
  technicalWeight: number;
  commercialWeight: number;
}

export interface SensitivityRow {
  bidderId: number;
  bidderName: string;
  ranks: Record<string, number>; // "30/70" -> rank
  winnerAtSplits: string[];      // List of splits where this bidder wins
  hasRankChange: boolean;
}

export interface SensitivityAnalysis {
  tenderId: number;
  weightSplits: WeightSplit[];
  rows: SensitivityRow[];
  winnerChanges: {
    split: string;
    previousWinner: string;
    newWinner: string;
  }[];
}

// ============================================================================
// EXCEPTIONS
// ============================================================================

export interface BidException {
  id: number;
  tenderId: number;
  bidderId: number;
  bidderName: string;
  type: ExceptionType;
  description: string;
  costImpact?: number;
  timeImpact?: string;
  riskLevel: RiskLevel;
  mitigation?: string;
  createdAt: Date | string;
  createdBy: number;
  createdByName: string;
  resolvedAt?: Date | string;
  resolvedBy?: number;
  resolution?: string;
}

export interface CreateExceptionDto {
  tenderId: number;
  bidderId: number;
  type: ExceptionType;
  description: string;
  costImpact?: number;
  timeImpact?: string;
  riskLevel: RiskLevel;
  mitigation?: string;
}

// ============================================================================
// AWARD PACK
// ============================================================================

export interface AwardPack {
  tenderId: number;
  recommendedBidderId: number;
  recommendedBidderName: string;
  technicalScore: number;
  commercialScore: number;
  combinedScore: number;
  exceptions: BidException[];
  sensitivitySummary: string;
  generatedAt: Date | string;
  downloadUrl: string;
}

// ============================================================================
// APPROVAL WORKFLOW
// ============================================================================

export interface ApprovalStep {
  id: number;
  tenderId: number;
  stepOrder: number;
  approverUserId: number;
  approverName: string;
  status: ApprovalStatus;
  comments?: string;
  decidedAt?: Date | string;
}

export interface ApprovalWorkflow {
  tenderId: number;
  currentStep: number;
  totalSteps: number;
  steps: ApprovalStep[];
  isComplete: boolean;
  finalStatus: ApprovalStatus;
}

// ============================================================================
// CONFIGURATION
// ============================================================================

export const SCORING_METHOD_OPTIONS: { label: string; value: ScoringMethod; description: string }[] = [
  { label: 'Numeric (0-10)', value: 'numeric', description: 'Score each criterion from 0 to 10' },
  { label: 'Star Rating (1-5)', value: 'star', description: 'Rate each criterion with 1 to 5 stars' }
];

export const EXCEPTION_TYPE_OPTIONS: { label: string; value: ExceptionType }[] = [
  { label: 'Technical', value: 'technical' },
  { label: 'Commercial', value: 'commercial' },
  { label: 'Contractual', value: 'contractual' }
];

export const RISK_LEVEL_OPTIONS: { label: string; value: RiskLevel; severity: 'success' | 'info' | 'warn' | 'danger' }[] = [
  { label: 'Low', value: 'low', severity: 'success' },
  { label: 'Medium', value: 'medium', severity: 'info' },
  { label: 'High', value: 'high', severity: 'warn' },
  { label: 'Critical', value: 'critical', severity: 'danger' }
];

export const EVALUATION_STATUS_CONFIG: Record<EvaluationStatus, { label: string; severity: 'secondary' | 'success' | 'info' | 'warn' | 'danger'; icon: string }> = {
  pending: { label: 'Pending', severity: 'secondary', icon: 'pi-clock' },
  in_progress: { label: 'In Progress', severity: 'info', icon: 'pi-spinner' },
  completed: { label: 'Completed', severity: 'success', icon: 'pi-check-circle' },
  locked: { label: 'Locked', severity: 'warn', icon: 'pi-lock' }
};

export const DEFAULT_WEIGHT_SPLITS: WeightSplit[] = [
  { technicalWeight: 30, commercialWeight: 70 },
  { technicalWeight: 35, commercialWeight: 65 },
  { technicalWeight: 40, commercialWeight: 60 },
  { technicalWeight: 45, commercialWeight: 55 },
  { technicalWeight: 50, commercialWeight: 50 },
  { technicalWeight: 55, commercialWeight: 45 },
  { technicalWeight: 60, commercialWeight: 40 },
  { technicalWeight: 65, commercialWeight: 35 },
  { technicalWeight: 70, commercialWeight: 30 }
];
