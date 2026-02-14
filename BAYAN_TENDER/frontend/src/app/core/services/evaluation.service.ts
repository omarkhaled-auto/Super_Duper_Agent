import { Injectable, inject, signal } from '@angular/core';
import { Observable, map, tap, catchError, throwError, switchMap } from 'rxjs';
import { ApiService } from './api.service';
import {
  EvaluationSetup,
  CreateEvaluationSetupDto,
  PanelMemberOption,
  BidderForScoring,
  SaveScoreDto,
  BidderScoreEntry,
  TechnicalSummary,
  PanelistScoreRow,
  PanelistComment,
  CombinedScorecard,
  UpdateWeightsDto,
  SensitivityAnalysis,
  BidException,
  CreateExceptionDto,
  AwardPack,
  ApprovalWorkflow,
  EvaluationCriterion,
  PanelMember,
  BidderAggregatedScore,
  ScorecardBidder,
  SensitivityRow
} from '../models/evaluation.model';

@Injectable({
  providedIn: 'root'
})
export class EvaluationService {
  private readonly api = inject(ApiService);

  private readonly _isLoading = signal<boolean>(false);
  private readonly _error = signal<string | null>(null);

  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();

  // ============================================================================
  // API ENDPOINTS
  // ============================================================================

  private evalUrl(tenderId: string | number): string {
    return `/tenders/${tenderId}/evaluation`;
  }

  // ============================================================================
  // EVALUATION SETUP
  // ============================================================================

  /**
   * Get available panel members (with TechnicalPanelist role)
   * Backend: GET /api/admin/users?role=TechnicalPanelist&isActive=true
   * Returns PanelistDto[] from panelists endpoint, mapped to PanelMemberOption[]
   */
  getAvailablePanelMembers(tenderId: string | number): Observable<PanelMemberOption[]> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<any[]>(`${this.evalUrl(tenderId)}/panelists`).pipe(
      map((panelists: any[]) => panelists.map(p => ({
        id: p.id,
        userId: p.userId,
        firstName: (p.fullName || '').split(' ')[0] || '',
        lastName: (p.fullName || '').split(' ').slice(1).join(' ') || '',
        email: p.email || '',
        fullName: p.fullName || '',
        department: p.department,
        isAvailable: !p.isComplete
      } as PanelMemberOption))),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load panel members');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get evaluation criteria for a tender
   * Backend: GET /api/tenders/{tenderId}/evaluation/setup -> EvaluationSetupDto.Criteria
   */
  getEvaluationCriteria(tenderId: string | number): Observable<EvaluationCriterion[]> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<any>(`${this.evalUrl(tenderId)}/setup`).pipe(
      map((setup: any) => (setup.criteria || []).map((c: any) => ({
        id: c.id,
        name: c.name,
        weight: c.weightPercentage,
        maxScore: 10,
        category: 'technical' as const,
        description: c.name,
        guidanceNotes: c.guidanceNotes
      } as EvaluationCriterion))),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load criteria');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get current evaluation setup for a tender
   * Backend: GET /api/tenders/{tenderId}/evaluation/setup -> EvaluationSetupDto
   */
  getEvaluationSetup(tenderId: string | number): Observable<EvaluationSetup | null> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<any>(`${this.evalUrl(tenderId)}/setup`).pipe(
      map((dto: any) => {
        if (!dto) return null;

        const panelMembers: PanelMember[] = (dto.panelists || []).map((p: any) => ({
          id: p.id,
          userId: p.userId,
          firstName: (p.fullName || '').split(' ')[0] || '',
          lastName: (p.fullName || '').split(' ').slice(1).join(' ') || '',
          email: p.email || '',
          role: 'TechnicalPanelist',
          isLead: false,
          assignedAt: p.assignedAt,
          completedAt: p.completedAt,
          status: p.isComplete ? 'completed' as const : p.biddersScored > 0 ? 'in_progress' as const : 'pending' as const
        }));

        const criteria: EvaluationCriterion[] = (dto.criteria || []).map((c: any) => ({
          id: c.id,
          name: c.name,
          weight: c.weightPercentage,
          maxScore: 10,
          category: 'technical' as const,
          description: c.name,
          guidanceNotes: c.guidanceNotes
        }));

        const status = dto.technicalScoresLocked ? 'locked'
          : dto.isSetupComplete ? 'in_progress'
          : 'pending';

        return {
          id: dto.tenderId,
          tenderId: dto.tenderId,
          status,
          scoringMethod: dto.scoringMethod === 0 || (typeof dto.scoringMethod === 'string' && dto.scoringMethod.toLowerCase() === 'numeric') ? 'numeric' : 'star',
          blindMode: dto.blindMode,
          deadline: dto.technicalEvaluationDeadline,
          panelMembers,
          criteria,
          createdAt: dto.technicalEvaluationDeadline || new Date(),
          createdBy: 0,
          lockedAt: dto.technicalLockedAt,
          lockedBy: dto.technicalLockedByName ? 1 : undefined
        } as EvaluationSetup;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load evaluation setup');
        return throwError(() => error);
      })
    );
  }

  /**
   * Create and start evaluation
   * Backend: POST /api/tenders/{tenderId}/evaluation/setup
   * Body: { scoringMethod, blindMode, technicalEvaluationDeadline, panelistUserIds, sendNotificationEmails }
   * Returns SetupTechnicalEvaluationResult, then re-fetches setup for full EvaluationSetup
   */
  startEvaluation(dto: CreateEvaluationSetupDto): Observable<EvaluationSetup> {
    this._isLoading.set(true);
    this._error.set(null);

    const body = {
      scoringMethod: dto.scoringMethod === 'numeric' ? 0 : 1,
      blindMode: dto.blindMode,
      technicalEvaluationDeadline: dto.deadline,
      panelistUserIds: dto.panelMemberIds,
      sendNotificationEmails: true
    };

    const tenderId = String(dto.tenderId);

    return this.api.post<any>(`${this.evalUrl(tenderId)}/setup`, body).pipe(
      switchMap(() => this.getEvaluationSetup(tenderId)),
      map(setup => setup!),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to start evaluation');
        return throwError(() => error);
      })
    );
  }

  // ============================================================================
  // TECHNICAL SCORING
  // ============================================================================

  /**
   * Get bidders for scoring (respects blind mode)
   * Backend: GET /api/tenders/{tenderId}/evaluation/my-assignments -> PanelistAssignmentDto
   * Maps PanelistAssignmentDto.Bidders to BidderForScoring[]
   */
  getBiddersForScoring(tenderId: string | number): Observable<BidderForScoring[]> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<any>(`${this.evalUrl(tenderId)}/my-assignments`).pipe(
      map((assignment: any) => (assignment.bidders || []).map((b: any) => ({
        id: b.bidderId,
        bidderId: b.bidderId,
        bidderName: b.companyName || b.anonymousId,
        blindCode: b.anonymousId,
        isScored: b.isFullySubmitted,
        documents: []
      } as BidderForScoring))),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load bidders');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get current panelist's scores for a specific bidder
   * Backend: GET /api/tenders/{tenderId}/evaluation/scores/{bidderId} -> List<TechnicalScoreDto>
   * Maps TechnicalScoreDto[] to BidderScoreEntry[]
   */
  getPanelistScores(tenderId: string | number, bidderId: string | number): Observable<BidderScoreEntry[]> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<any[]>(`${this.evalUrl(tenderId)}/scores/${bidderId}`).pipe(
      map((scores: any[]) => {
        if (!scores || scores.length === 0) return [];
        const criteriaScores = scores.map(s => ({
          criterionId: s.criterionId,
          score: s.score,
          comment: s.comment,
          isDraft: s.isDraft
        }));
        const totalScore = criteriaScores.reduce((sum, cs) => sum + cs.score, 0);
        const weightedScore = scores.reduce((sum, s) => sum + (s.score * (s.criterionWeight || 0) / 100), 0);
        const anyDraft = scores.some(s => s.isDraft);
        const submittedAt = scores.find(s => s.submittedAt)?.submittedAt;

        return [{
          bidderId: scores[0].bidderId,
          criteriaScores,
          totalScore,
          weightedScore: Math.round(weightedScore * 100) / 100,
          submittedAt: anyDraft ? undefined : submittedAt,
          isDraft: anyDraft
        } as BidderScoreEntry];
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load scores');
        return throwError(() => error);
      })
    );
  }

  /**
   * Save score (draft or submit)
   * Backend: POST /api/tenders/{tenderId}/evaluation/scores
   * Body: { scores: [{ bidderId, criterionId, score, comment }], isFinalSubmission }
   * Returns SaveTechnicalScoresResult, mapped to BidderScoreEntry
   */
  saveScore(dto: SaveScoreDto): Observable<BidderScoreEntry> {
    this._isLoading.set(true);
    this._error.set(null);

    const tenderId = String(dto.tenderId);
    const body = {
      scores: dto.criteriaScores.map(cs => ({
        bidderId: dto.bidderId,
        criterionId: cs.criterionId,
        score: cs.score,
        comment: cs.comment || null
      })),
      isFinalSubmission: !dto.isDraft
    };

    return this.api.post<any>(`${this.evalUrl(tenderId)}/scores`, body).pipe(
      map(() => {
        const totalScore = dto.criteriaScores.reduce((sum, cs) => sum + cs.score, 0);
        return {
          bidderId: dto.bidderId,
          criteriaScores: dto.criteriaScores,
          totalScore,
          weightedScore: 0,
          submittedAt: dto.isDraft ? undefined : new Date(),
          isDraft: dto.isDraft
        } as BidderScoreEntry;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to save score');
        return throwError(() => error);
      })
    );
  }

  // ============================================================================
  // TECHNICAL SUMMARY
  // ============================================================================

  /**
   * Get technical evaluation summary
   * Backend: GET /api/tenders/{tenderId}/evaluation/summary -> TechnicalScoresSummaryDto
   * Maps to frontend TechnicalSummary shape
   */
  getTechnicalSummary(tenderId: string | number): Observable<TechnicalSummary> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<any>(`${this.evalUrl(tenderId)}/summary`).pipe(
      map((dto: any) => this.mapTechnicalSummary(dto, tenderId)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load technical summary');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get detailed comments from all panelists
   * Backend: GET /api/tenders/{tenderId}/evaluation/summary -> TechnicalScoresSummaryDto
   * Extracts PanelistCriterionScoreDto entries that have comments
   */
  getDetailedComments(tenderId: string | number): Observable<PanelistComment[]> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<any>(`${this.evalUrl(tenderId)}/summary`).pipe(
      map((dto: any) => {
        const comments: PanelistComment[] = [];
        for (const bidder of (dto.bidderScores || [])) {
          for (const ps of (bidder.panelistScores || [])) {
            if (ps.comment) {
              comments.push({
                panelistId: ps.panelistUserId,
                panelistName: ps.panelistName || '',
                bidderId: bidder.bidderId,
                bidderName: bidder.companyName || bidder.anonymousId || '',
                criterionId: ps.criterionId,
                criterionName: ps.criterionName || '',
                score: ps.score,
                comment: ps.comment,
                submittedAt: ps.submittedAt || new Date()
              });
            }
          }
        }
        return comments;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load comments');
        return throwError(() => error);
      })
    );
  }

  /**
   * Lock technical scores (irreversible)
   * Backend: POST /api/tenders/{tenderId}/evaluation/lock-scores
   * Body: { confirm: true }
   * Returns LockTechnicalScoresResult
   */
  lockTechnicalScores(tenderId: string | number): Observable<void> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.post<any>(`${this.evalUrl(tenderId)}/lock-scores`, { confirm: true }).pipe(
      map(() => void 0),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to lock scores');
        return throwError(() => error);
      })
    );
  }

  // ============================================================================
  // COMBINED SCORECARD
  // ============================================================================

  /**
   * Get combined scorecard
   * Backend: GET /api/tenders/{tenderId}/evaluation/combined-scorecard -> CombinedScorecardDto
   */
  getCombinedScorecard(tenderId: string | number): Observable<CombinedScorecard> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<any>(`${this.evalUrl(tenderId)}/combined-scorecard`).pipe(
      map((dto: any) => this.mapCombinedScorecard(dto)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load scorecard');
        return throwError(() => error);
      })
    );
  }

  /**
   * Update weights and recalculate
   * Backend: POST /api/tenders/{tenderId}/evaluation/calculate-combined
   * Body: { technicalWeight, commercialWeight }
   * Returns CombinedScorecardDto
   */
  updateWeights(dto: UpdateWeightsDto): Observable<CombinedScorecard> {
    this._isLoading.set(true);
    this._error.set(null);

    const tenderId = String(dto.tenderId);
    const body = {
      technicalWeight: dto.technicalWeight,
      commercialWeight: dto.commercialWeight
    };

    return this.api.post<any>(`${this.evalUrl(tenderId)}/calculate-combined`, body).pipe(
      map((result: any) => this.mapCombinedScorecard(result)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to update weights');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get sensitivity analysis
   * Backend: GET /api/tenders/{tenderId}/evaluation/sensitivity-analysis -> SensitivityAnalysisDto
   */
  getSensitivityAnalysis(tenderId: string | number): Observable<SensitivityAnalysis> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<any>(`${this.evalUrl(tenderId)}/sensitivity-analysis`).pipe(
      map((dto: any) => this.mapSensitivityAnalysis(dto)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load sensitivity analysis');
        return throwError(() => error);
      })
    );
  }

  // ============================================================================
  // EXCEPTIONS
  // ============================================================================

  /**
   * Get exceptions for a tender
   * Backend: GET /api/tenders/{tenderId}/exceptions -> BidExceptionListDto
   */
  getExceptions(tenderId: string | number): Observable<BidException[]> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<any>(`/tenders/${tenderId}/exceptions`).pipe(
      map((dto: any) => (dto.exceptions || []).map((e: any) => this.mapBidException(e, tenderId))),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load exceptions');
        return throwError(() => error);
      })
    );
  }

  /**
   * Add an exception
   * Backend: POST /api/tenders/{tenderId}/exceptions
   * Body: { bidderId, exceptionType, description, costImpact, timeImpactDays, riskLevel, mitigation }
   * Returns BidExceptionDto
   */
  addException(dto: CreateExceptionDto): Observable<BidException> {
    this._isLoading.set(true);
    this._error.set(null);

    const tenderId = String(dto.tenderId);
    const exceptionTypeMap: Record<string, number> = { technical: 0, commercial: 1, contractual: 2 };
    const riskLevelMap: Record<string, number> = { low: 0, medium: 1, high: 2, critical: 3 };

    const body = {
      bidderId: dto.bidderId,
      exceptionType: exceptionTypeMap[dto.type] ?? 0,
      description: dto.description,
      costImpact: dto.costImpact || null,
      timeImpactDays: dto.timeImpact ? parseInt(dto.timeImpact, 10) || null : null,
      riskLevel: riskLevelMap[dto.riskLevel] ?? 0,
      mitigation: dto.mitigation || null
    };

    return this.api.post<any>(`/tenders/${tenderId}/exceptions`, body).pipe(
      map((result: any) => this.mapBidException(result, tenderId)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to add exception');
        return throwError(() => error);
      })
    );
  }

  /**
   * Delete an exception
   * Note: Backend DELETE endpoint not yet implemented. Using conventional REST path.
   * Backend (expected): DELETE /api/tenders/{tenderId}/exceptions/{exceptionId}
   */
  deleteException(tenderId: string | number, exceptionId: string | number): Observable<void> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.delete<any>(`/tenders/${tenderId}/exceptions/${exceptionId}`).pipe(
      map(() => void 0),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to delete exception');
        return throwError(() => error);
      })
    );
  }

  // ============================================================================
  // AWARD PACK
  // ============================================================================

  /**
   * Generate award pack
   * Backend: POST /api/tenders/{tenderId}/evaluation/generate-award-pack
   * Returns AwardPackDto with downloadUrl
   */
  generateAwardPack(tenderId: string | number): Observable<AwardPack> {
    this._isLoading.set(true);
    this._error.set(null);

    const body = {
      includeTechnicalDetails: true,
      includeCommercialDetails: true,
      includeSensitivityAnalysis: true,
      includeExceptions: true
    };

    return this.api.post<any>(`${this.evalUrl(tenderId)}/generate-award-pack`, body).pipe(
      map((dto: any) => ({
        tenderId: dto.tenderId,
        recommendedBidderId: 0,
        recommendedBidderName: '',
        technicalScore: 0,
        commercialScore: 0,
        combinedScore: 0,
        exceptions: [],
        sensitivitySummary: '',
        generatedAt: dto.generatedAt,
        downloadUrl: dto.downloadUrl || `/api/tenders/${tenderId}/evaluation/award-pack/download`
      } as AwardPack)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to generate award pack');
        return throwError(() => error);
      })
    );
  }

  /**
   * Start approval workflow
   * Backend: POST /api/tenders/{tenderId}/approval/initiate
   * Body: { awardPackPdfPath, approverUserIds, levelDeadlines }
   * Returns InitiateApprovalResult, then fetches the approval status
   */
  startApproval(tenderId: string | number, approverUserIds: string[] = [], awardPackPdfPath: string = ''): Observable<ApprovalWorkflow> {
    this._isLoading.set(true);
    this._error.set(null);

    const body = {
      awardPackPdfPath,
      approverUserIds,
      levelDeadlines: [] as string[]
    };

    return this.api.post<any>(`/tenders/${tenderId}/approval/initiate`, body).pipe(
      switchMap(() => this.api.get<any>(`/tenders/${tenderId}/approval`)),
      map((dto: any) => {
        const statusMap: Record<number, string> = { 0: 'pending', 1: 'in_progress', 2: 'approved', 3: 'rejected', 4: 'returned' };
        const statusNameMap: Record<string, string> = { pending: 'pending', inprogress: 'in_progress', approved: 'approved', rejected: 'rejected', revisionneeded: 'returned' };
        const decisionMap: Record<number, string> = { 0: 'approved', 1: 'rejected', 2: 'returned' };
        const decisionNameMap: Record<string, string> = { approve: 'approved', reject: 'rejected', returnforrevision: 'returned' };
        const mapStatus = (v: any) => typeof v === 'number' ? (statusMap[v] || 'pending') : (statusNameMap[String(v || '').toLowerCase()] || String(v || 'pending').toLowerCase());
        const mapDecision = (v: any) => typeof v === 'number' ? (decisionMap[v] || 'pending') : (decisionNameMap[String(v || '').toLowerCase()] || String(v || 'pending').toLowerCase());

        return {
          tenderId: dto.tenderId || tenderId,
          currentStep: dto.currentLevel || 1,
          totalSteps: (dto.levels || []).length,
          steps: (dto.levels || []).map((l: any) => ({
            id: l.id,
            tenderId: dto.tenderId || tenderId,
            stepOrder: l.levelNumber || l.levelOrder || l.level,
            approverUserId: l.approverUserId,
            approverName: l.approverName || '',
            status: (l.decision != null ? mapDecision(l.decision) : 'pending') as 'pending' | 'approved' | 'rejected',
            comments: l.decisionComment || l.comments,
            decidedAt: l.decidedAt
          })),
          isComplete: dto.isComplete || mapStatus(dto.status) === 'approved' || mapStatus(dto.status) === 'rejected',
          finalStatus: mapStatus(dto.status) as 'pending' | 'approved' | 'rejected'
        } as ApprovalWorkflow;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to start approval');
        return throwError(() => error);
      })
    );
  }

  // ============================================================================
  // HELPER METHODS
  // ============================================================================

  clearError(): void {
    this._error.set(null);
  }

  // ============================================================================
  // MAPPING HELPERS (Backend DTO -> Frontend Model)
  // ============================================================================

  /**
   * Maps backend TechnicalScoresSummaryDto to frontend TechnicalSummary
   */
  private mapTechnicalSummary(dto: any, tenderId: string | number): TechnicalSummary {
    const criteria: EvaluationCriterion[] = (dto.criteria || []).map((c: any) => ({
      id: c.id,
      name: c.name,
      weight: c.weightPercentage,
      maxScore: 10,
      category: 'technical' as const,
      description: c.name
    }));

    // Build panelist score rows from bidderScores.panelistScores
    const panelistMap: Record<string, PanelistScoreRow> = {};
    for (const bidder of (dto.bidderScores || [])) {
      for (const ps of (bidder.panelistScores || [])) {
        const pKey = ps.panelistUserId;
        if (!panelistMap[pKey]) {
          panelistMap[pKey] = {
            panelistId: ps.panelistUserId,
            panelistName: ps.panelistName || '',
            scores: {},
            completedAt: ps.submittedAt
          };
        }
        if (!panelistMap[pKey].scores[bidder.bidderId]) {
          panelistMap[pKey].scores[bidder.bidderId] = {};
        }
        panelistMap[pKey].scores[bidder.bidderId][ps.criterionId] = ps.score;
      }
    }
    const panelistScores = Object.values(panelistMap);

    // Build aggregated scores
    const aggregatedScores: BidderAggregatedScore[] = (dto.bidderScores || []).map((bidder: any) => {
      const criteriaScores: Record<string, { scores: number[]; average: number; stdDev: number; hasVarianceAlert: boolean }> = {};
      let hasVarianceAlerts = false;

      for (const cs of (bidder.criterionScores || [])) {
        // Collect individual panelist scores for this criterion
        const pScores = (bidder.panelistScores || [])
          .filter((ps: any) => ps.criterionId === cs.criterionId)
          .map((ps: any) => ps.score);
        const avg = cs.averageScore;
        const stdDev = Math.sqrt(cs.variance || 0);
        const hasAlert = stdDev > 2;
        if (hasAlert) hasVarianceAlerts = true;

        criteriaScores[cs.criterionId] = {
          scores: pScores,
          average: Math.round(avg * 100) / 100,
          stdDev: Math.round(stdDev * 100) / 100,
          hasVarianceAlert: hasAlert
        };
      }

      return {
        bidderId: bidder.bidderId,
        bidderName: bidder.companyName || bidder.anonymousId || '',
        blindCode: bidder.anonymousId || '',
        criteriaScores,
        totalAverage: Math.round(bidder.totalWeightedScore * 100) / 100,
        rank: bidder.rank,
        hasVarianceAlerts
      } as BidderAggregatedScore;
    });

    const bidders: BidderForScoring[] = (dto.bidderScores || []).map((b: any) => ({
      id: b.bidderId,
      bidderId: b.bidderId,
      bidderName: b.companyName || b.anonymousId || '',
      blindCode: b.anonymousId || '',
      isScored: b.isFullyScored,
      documents: []
    }));

    const status = dto.technicalScoresLocked ? 'locked'
      : dto.allPanelistsComplete ? 'completed'
      : dto.completedPanelistCount > 0 ? 'in_progress'
      : 'pending';

    return {
      tenderId: tenderId as any,
      status: status as any,
      totalPanelists: dto.totalPanelistCount || 0,
      completedPanelists: dto.completedPanelistCount || 0,
      panelistScores,
      aggregatedScores,
      criteria,
      bidders,
      varianceThreshold: 2
    };
  }

  /**
   * Maps backend CombinedScorecardDto to frontend CombinedScorecard
   */
  private mapCombinedScorecard(dto: any): CombinedScorecard {
    const entries = dto.entries || [];
    const bidders: ScorecardBidder[] = entries.map((e: any) => ({
      bidderId: e.bidderId,
      bidderName: e.companyName || '',
      technicalScore: e.technicalScoreAvg || 0,
      technicalRank: e.technicalRank || 0,
      commercialScore: e.commercialScoreValue || 0,
      commercialRank: e.commercialRank || 0,
      combinedScore: e.combinedScore || 0,
      finalRank: e.finalRank || 0,
      isWinner: e.isRecommended || false,
      isDisqualified: false
    }));

    const recommended = entries.find((e: any) => e.isRecommended);

    return {
      tenderId: dto.tenderId,
      technicalWeight: dto.technicalWeight || 0,
      commercialWeight: dto.commercialWeight || 0,
      bidders,
      recommendedBidderId: recommended?.bidderId || (bidders[0]?.bidderId ?? 0),
      recommendedBidderName: recommended?.companyName || (bidders[0]?.bidderName ?? ''),
      generatedAt: dto.calculatedAt || new Date()
    };
  }

  /**
   * Maps backend SensitivityAnalysisDto to frontend SensitivityAnalysis
   */
  private mapSensitivityAnalysis(dto: any): SensitivityAnalysis {
    const weightSplitStrings: string[] = dto.weightSplits || [];
    const weightSplits = weightSplitStrings.map(s => {
      const [tech, comm] = s.split('/').map(Number);
      return { technicalWeight: tech, commercialWeight: comm };
    });

    const rows: SensitivityRow[] = (dto.rows || []).map((row: any) => {
      const ranks = row.ranksByWeightSplit || {};
      const winnerAtSplits = Object.entries(ranks)
        .filter(([, rank]) => rank === 1)
        .map(([split]) => split);

      return {
        bidderId: row.bidderId,
        bidderName: row.companyName || '',
        ranks,
        winnerAtSplits,
        hasRankChange: row.hasRankVariation || false
      } as SensitivityRow;
    });

    // Build winnerChanges from dto.winnerByWeightSplit
    const winnerByWeightSplit = dto.winnerByWeightSplit || {};
    const winnerChanges: { split: string; previousWinner: string; newWinner: string }[] = [];
    const splits = Object.keys(winnerByWeightSplit);
    for (let i = 1; i < splits.length; i++) {
      const prev = winnerByWeightSplit[splits[i - 1]];
      const curr = winnerByWeightSplit[splits[i]];
      if (prev && curr && prev !== curr) {
        winnerChanges.push({ split: splits[i], previousWinner: prev, newWinner: curr });
      }
    }

    return {
      tenderId: dto.tenderId,
      weightSplits,
      rows,
      winnerChanges
    };
  }

  /**
   * Maps a backend BidExceptionDto to frontend BidException
   */
  private mapBidException(e: any, tenderId: string | number): BidException {
    const exceptionTypeMap: Record<number, string> = { 0: 'technical', 1: 'commercial', 2: 'contractual' };
    const riskLevelMap: Record<number, string> = { 0: 'low', 1: 'medium', 2: 'high', 3: 'critical' };
    const mapExType = (v: any) => typeof v === 'string' ? v.toLowerCase() : exceptionTypeMap[v];
    const mapRisk = (v: any) => typeof v === 'string' ? v.toLowerCase() : riskLevelMap[v];

    return {
      id: e.id,
      tenderId: tenderId as any,
      bidderId: e.bidderId,
      bidderName: e.bidderCompanyName || '',
      type: (e.exceptionTypeName?.toLowerCase() || mapExType(e.exceptionType) || 'technical') as any,
      description: e.description || '',
      costImpact: e.costImpact,
      timeImpact: e.timeImpactDays != null ? String(e.timeImpactDays) : undefined,
      riskLevel: (e.riskLevelName?.toLowerCase() || mapRisk(e.riskLevel) || 'low') as any,
      mitigation: e.mitigation,
      createdAt: e.createdAt,
      createdBy: e.loggedBy,
      createdByName: e.loggedByName || ''
    };
  }
}
