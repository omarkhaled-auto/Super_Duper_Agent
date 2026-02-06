import { Injectable, inject, signal } from '@angular/core';
import { Observable, of, delay, map, tap, catchError, throwError } from 'rxjs';
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
  SensitivityRow,
  DEFAULT_WEIGHT_SPLITS
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
  // MOCK DATA
  // ============================================================================

  private mockPanelMembers: PanelMemberOption[] = [
    { id: 1, userId: 1, firstName: 'Ahmed', lastName: 'Al-Rashid', email: 'ahmed@bayan.sa', fullName: 'Ahmed Al-Rashid', department: 'Engineering', isAvailable: true },
    { id: 2, userId: 2, firstName: 'Fatima', lastName: 'Al-Saud', email: 'fatima@bayan.sa', fullName: 'Fatima Al-Saud', department: 'Procurement', isAvailable: true },
    { id: 3, userId: 3, firstName: 'Mohammed', lastName: 'Al-Harbi', email: 'mohammed@bayan.sa', fullName: 'Mohammed Al-Harbi', department: 'Technical', isAvailable: true },
    { id: 4, userId: 4, firstName: 'Sara', lastName: 'Al-Otaibi', email: 'sara@bayan.sa', fullName: 'Sara Al-Otaibi', department: 'Quality', isAvailable: true },
    { id: 5, userId: 5, firstName: 'Khalid', lastName: 'Al-Dosari', email: 'khalid@bayan.sa', fullName: 'Khalid Al-Dosari', department: 'Operations', isAvailable: false }
  ];

  private mockBidders: BidderForScoring[] = [
    {
      id: 1, bidderId: 1, bidderName: 'Tech Solutions Ltd', blindCode: 'Bidder 001', isScored: false,
      documents: [
        { id: 1, type: 'methodology', filename: 'Technical_Methodology.pdf', url: '/api/documents/1' },
        { id: 2, type: 'team_cvs', filename: 'Team_CVs.pdf', url: '/api/documents/2' },
        { id: 3, type: 'work_program', filename: 'Work_Program.pdf', url: '/api/documents/3' },
        { id: 4, type: 'hse_plan', filename: 'HSE_Plan.pdf', url: '/api/documents/4' }
      ]
    },
    {
      id: 2, bidderId: 2, bidderName: 'SecureTech Solutions', blindCode: 'Bidder 002', isScored: false,
      documents: [
        { id: 5, type: 'methodology', filename: 'Technical_Methodology.pdf', url: '/api/documents/5' },
        { id: 6, type: 'team_cvs', filename: 'Team_CVs.pdf', url: '/api/documents/6' },
        { id: 7, type: 'work_program', filename: 'Work_Program.pdf', url: '/api/documents/7' },
        { id: 8, type: 'hse_plan', filename: 'HSE_Plan.pdf', url: '/api/documents/8' }
      ]
    },
    {
      id: 3, bidderId: 3, bidderName: 'Global IT Partners', blindCode: 'Bidder 003', isScored: false,
      documents: [
        { id: 9, type: 'methodology', filename: 'Technical_Methodology.pdf', url: '/api/documents/9' },
        { id: 10, type: 'team_cvs', filename: 'Team_CVs.pdf', url: '/api/documents/10' },
        { id: 11, type: 'work_program', filename: 'Work_Program.pdf', url: '/api/documents/11' },
        { id: 12, type: 'hse_plan', filename: 'HSE_Plan.pdf', url: '/api/documents/12' }
      ]
    }
  ];

  private mockCriteria: EvaluationCriterion[] = [
    { id: 1, name: 'Technical Methodology', weight: 25, maxScore: 10, category: 'technical', description: 'Quality of proposed technical approach', guidanceNotes: 'Evaluate the clarity, feasibility, and innovation of the proposed methodology.' },
    { id: 2, name: 'Team Qualifications', weight: 20, maxScore: 10, category: 'technical', description: 'Experience and qualifications of proposed team', guidanceNotes: 'Consider relevant experience, certifications, and track record.' },
    { id: 3, name: 'Work Program', weight: 20, maxScore: 10, category: 'technical', description: 'Quality of proposed schedule and milestones', guidanceNotes: 'Assess realism, detailed planning, and risk mitigation strategies.' },
    { id: 4, name: 'HSE Plan', weight: 15, maxScore: 10, category: 'technical', description: 'Health, Safety and Environment policies', guidanceNotes: 'Review compliance with regulations and proactive safety measures.' },
    { id: 5, name: 'Quality Assurance', weight: 10, maxScore: 10, category: 'technical', description: 'Quality control procedures', guidanceNotes: 'Evaluate QA/QC processes and documentation.' },
    { id: 6, name: 'Innovation', weight: 10, maxScore: 10, category: 'technical', description: 'Innovative approaches and value engineering', guidanceNotes: 'Consider creative solutions and potential improvements.' }
  ];

  private evaluationSetup: EvaluationSetup | null = null;
  private savedScores: Record<number, BidderScoreEntry[]> = {}; // panelistId -> scores

  // ============================================================================
  // EVALUATION SETUP
  // ============================================================================

  /**
   * Get available panel members (with TechnicalPanelist role)
   */
  getAvailablePanelMembers(): Observable<PanelMemberOption[]> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(500),
      map(() => this.mockPanelMembers.filter(m => m.isAvailable)),
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
   */
  getEvaluationCriteria(tenderId: number): Observable<EvaluationCriterion[]> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(300),
      map(() => this.mockCriteria),
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
   */
  getEvaluationSetup(tenderId: number): Observable<EvaluationSetup | null> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(500),
      map(() => this.evaluationSetup),
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
   */
  startEvaluation(dto: CreateEvaluationSetupDto): Observable<EvaluationSetup> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(1000),
      map(() => {
        const panelMembers: PanelMember[] = dto.panelMemberIds.map((id, index) => {
          const member = this.mockPanelMembers.find(m => m.id === id);
          return {
            id: index + 1,
            userId: member?.userId || id,
            firstName: member?.firstName || 'Unknown',
            lastName: member?.lastName || 'User',
            email: member?.email || '',
            role: 'TechnicalPanelist',
            isLead: index === 0,
            assignedAt: new Date(),
            status: 'pending' as const
          };
        });

        this.evaluationSetup = {
          id: 1,
          tenderId: dto.tenderId,
          status: 'in_progress',
          scoringMethod: dto.scoringMethod,
          blindMode: dto.blindMode,
          deadline: dto.deadline,
          panelMembers,
          criteria: this.mockCriteria,
          createdAt: new Date(),
          createdBy: 1,
          startedAt: new Date(),
          startedBy: 1
        };

        return this.evaluationSetup;
      }),
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
   */
  getBiddersForScoring(tenderId: number): Observable<BidderForScoring[]> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(500),
      map(() => this.mockBidders),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load bidders');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get current panelist's scores
   */
  getPanelistScores(tenderId: number, panelistId: number): Observable<BidderScoreEntry[]> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(300),
      map(() => this.savedScores[panelistId] || []),
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
   */
  saveScore(dto: SaveScoreDto): Observable<BidderScoreEntry> {
    this._isLoading.set(true);
    this._error.set(null);

    const panelistId = 1; // Current user's panelist ID

    return of(null).pipe(
      delay(500),
      map(() => {
        const totalScore = dto.criteriaScores.reduce((sum, cs) => sum + cs.score, 0);
        const maxTotal = this.mockCriteria.length * 10;
        const weightedScore = (totalScore / maxTotal) * 100;

        const entry: BidderScoreEntry = {
          bidderId: dto.bidderId,
          criteriaScores: dto.criteriaScores,
          totalScore,
          weightedScore: Math.round(weightedScore * 100) / 100,
          submittedAt: dto.isDraft ? undefined : new Date(),
          isDraft: dto.isDraft
        };

        // Store the score
        if (!this.savedScores[panelistId]) {
          this.savedScores[panelistId] = [];
        }
        const existingIndex = this.savedScores[panelistId].findIndex(s => s.bidderId === dto.bidderId);
        if (existingIndex >= 0) {
          this.savedScores[panelistId][existingIndex] = entry;
        } else {
          this.savedScores[panelistId].push(entry);
        }

        // Update bidder scored status
        const bidder = this.mockBidders.find(b => b.bidderId === dto.bidderId);
        if (bidder && !dto.isDraft) {
          bidder.isScored = true;
        }

        return entry;
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
   */
  getTechnicalSummary(tenderId: number): Observable<TechnicalSummary> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(800),
      map(() => this.generateMockTechnicalSummary(tenderId)),
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
   */
  getDetailedComments(tenderId: number): Observable<PanelistComment[]> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(500),
      map(() => this.generateMockComments()),
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
   */
  lockTechnicalScores(tenderId: number): Observable<void> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(1000),
      map(() => {
        if (this.evaluationSetup) {
          this.evaluationSetup.status = 'locked';
          this.evaluationSetup.lockedAt = new Date();
          this.evaluationSetup.lockedBy = 1;
        }
      }),
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
   */
  getCombinedScorecard(tenderId: number): Observable<CombinedScorecard> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(500),
      map(() => this.generateMockScorecard(tenderId, 40, 60)),
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
   */
  updateWeights(dto: UpdateWeightsDto): Observable<CombinedScorecard> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(500),
      map(() => this.generateMockScorecard(dto.tenderId, dto.technicalWeight, dto.commercialWeight)),
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
   */
  getSensitivityAnalysis(tenderId: number): Observable<SensitivityAnalysis> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(800),
      map(() => this.generateMockSensitivityAnalysis(tenderId)),
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

  private mockExceptions: BidException[] = [];

  /**
   * Get exceptions for a tender
   */
  getExceptions(tenderId: number): Observable<BidException[]> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(300),
      map(() => this.mockExceptions.filter(e => e.tenderId === tenderId)),
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
   */
  addException(dto: CreateExceptionDto): Observable<BidException> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(500),
      map(() => {
        const bidder = this.mockBidders.find(b => b.bidderId === dto.bidderId);
        const exception: BidException = {
          id: this.mockExceptions.length + 1,
          ...dto,
          bidderName: bidder?.bidderName || 'Unknown Bidder',
          createdAt: new Date(),
          createdBy: 1,
          createdByName: 'Admin User'
        };
        this.mockExceptions.push(exception);
        return exception;
      }),
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
   */
  deleteException(exceptionId: number): Observable<void> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(300),
      map(() => {
        this.mockExceptions = this.mockExceptions.filter(e => e.id !== exceptionId);
      }),
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
   */
  generateAwardPack(tenderId: number): Observable<AwardPack> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(2000),
      map(() => ({
        tenderId,
        recommendedBidderId: 1,
        recommendedBidderName: 'Tech Solutions Ltd',
        technicalScore: 82.5,
        commercialScore: 88.3,
        combinedScore: 85.98,
        exceptions: this.mockExceptions.filter(e => e.tenderId === tenderId),
        sensitivitySummary: 'Tech Solutions Ltd remains the recommended bidder across all tested weight scenarios (30/70 to 70/30).',
        generatedAt: new Date(),
        downloadUrl: '/api/tenders/' + tenderId + '/award-pack'
      })),
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
   */
  startApproval(tenderId: number): Observable<ApprovalWorkflow> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(1000),
      map(() => ({
        tenderId,
        currentStep: 1,
        totalSteps: 3,
        steps: [
          { id: 1, tenderId, stepOrder: 1, approverUserId: 2, approverName: 'Technical Director', status: 'pending' as const },
          { id: 2, tenderId, stepOrder: 2, approverUserId: 3, approverName: 'Procurement Manager', status: 'pending' as const },
          { id: 3, tenderId, stepOrder: 3, approverUserId: 4, approverName: 'CEO', status: 'pending' as const }
        ],
        isComplete: false,
        finalStatus: 'pending' as const
      })),
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

  private generateMockTechnicalSummary(tenderId: number): TechnicalSummary {
    // Mock panelist scores
    const panelistScores: PanelistScoreRow[] = [
      {
        panelistId: 1,
        panelistName: 'Ahmed Al-Rashid',
        scores: {
          1: { 1: 8, 2: 7, 3: 8, 4: 9, 5: 7, 6: 8 },
          2: { 1: 7, 2: 8, 3: 7, 4: 8, 5: 8, 6: 6 },
          3: { 1: 9, 2: 8, 3: 9, 4: 8, 5: 8, 6: 9 }
        },
        completedAt: new Date()
      },
      {
        panelistId: 2,
        panelistName: 'Fatima Al-Saud',
        scores: {
          1: { 1: 9, 2: 8, 3: 8, 4: 8, 5: 8, 6: 7 },
          2: { 1: 6, 2: 7, 3: 8, 4: 7, 5: 7, 6: 7 },
          3: { 1: 8, 2: 9, 3: 8, 4: 9, 5: 9, 6: 8 }
        },
        completedAt: new Date()
      },
      {
        panelistId: 3,
        panelistName: 'Mohammed Al-Harbi',
        scores: {
          1: { 1: 8, 2: 8, 3: 9, 4: 8, 5: 7, 6: 8 },
          2: { 1: 7, 2: 6, 3: 7, 4: 8, 5: 7, 6: 5 },
          3: { 1: 9, 2: 8, 3: 8, 4: 8, 5: 8, 6: 9 }
        },
        completedAt: new Date()
      }
    ];

    // Calculate aggregated scores
    const aggregatedScores: BidderAggregatedScore[] = this.mockBidders.map(bidder => {
      const criteriaScores: Record<number, { scores: number[]; average: number; stdDev: number; hasVarianceAlert: boolean }> = {};
      let hasVarianceAlerts = false;

      this.mockCriteria.forEach(criterion => {
        const scores = panelistScores.map(p => p.scores[bidder.bidderId]?.[criterion.id] || 0);
        const average = scores.reduce((a, b) => a + b, 0) / scores.length;
        const variance = scores.reduce((sum, s) => sum + Math.pow(s - average, 2), 0) / scores.length;
        const stdDev = Math.sqrt(variance);
        const hasVarianceAlert = stdDev > 2;

        if (hasVarianceAlert) hasVarianceAlerts = true;

        criteriaScores[criterion.id] = {
          scores,
          average: Math.round(average * 100) / 100,
          stdDev: Math.round(stdDev * 100) / 100,
          hasVarianceAlert
        };
      });

      const totalAverage = Object.values(criteriaScores).reduce((sum, cs) => sum + cs.average, 0) / this.mockCriteria.length;

      return {
        bidderId: bidder.bidderId,
        bidderName: bidder.bidderName,
        blindCode: bidder.blindCode,
        criteriaScores,
        totalAverage: Math.round(totalAverage * 100) / 100,
        rank: 0,
        hasVarianceAlerts
      };
    });

    // Calculate ranks
    aggregatedScores.sort((a, b) => b.totalAverage - a.totalAverage);
    aggregatedScores.forEach((score, index) => score.rank = index + 1);

    return {
      tenderId,
      status: 'completed',
      totalPanelists: 3,
      completedPanelists: 3,
      panelistScores,
      aggregatedScores,
      criteria: this.mockCriteria,
      bidders: this.mockBidders,
      varianceThreshold: 2
    };
  }

  private generateMockComments(): PanelistComment[] {
    return [
      { panelistId: 1, panelistName: 'Ahmed Al-Rashid', bidderId: 1, bidderName: 'Tech Solutions Ltd', criterionId: 1, criterionName: 'Technical Methodology', score: 8, comment: 'Strong methodology with clear implementation steps.', submittedAt: new Date() },
      { panelistId: 1, panelistName: 'Ahmed Al-Rashid', bidderId: 2, bidderName: 'SecureTech Solutions', criterionId: 6, criterionName: 'Innovation', score: 6, comment: 'Limited innovation, mostly standard approaches.', submittedAt: new Date() },
      { panelistId: 2, panelistName: 'Fatima Al-Saud', bidderId: 3, bidderName: 'Global IT Partners', criterionId: 2, criterionName: 'Team Qualifications', score: 9, comment: 'Excellent team with extensive relevant experience.', submittedAt: new Date() },
      { panelistId: 3, panelistName: 'Mohammed Al-Harbi', bidderId: 2, bidderName: 'SecureTech Solutions', criterionId: 6, criterionName: 'Innovation', score: 5, comment: 'Very basic proposal, lacks innovative elements.', submittedAt: new Date() }
    ];
  }

  private generateMockScorecard(tenderId: number, techWeight: number, commWeight: number): CombinedScorecard {
    const bidders: ScorecardBidder[] = [
      { bidderId: 1, bidderName: 'Tech Solutions Ltd', technicalScore: 82.5, technicalRank: 2, commercialScore: 88.3, commercialRank: 1, combinedScore: 0, finalRank: 0, isWinner: false, isDisqualified: false },
      { bidderId: 2, bidderName: 'SecureTech Solutions', technicalScore: 70.2, technicalRank: 3, commercialScore: 78.5, commercialRank: 3, combinedScore: 0, finalRank: 0, isWinner: false, isDisqualified: false },
      { bidderId: 3, bidderName: 'Global IT Partners', technicalScore: 85.8, technicalRank: 1, commercialScore: 82.1, commercialRank: 2, combinedScore: 0, finalRank: 0, isWinner: false, isDisqualified: false }
    ];

    // Calculate combined scores
    bidders.forEach(b => {
      b.combinedScore = Math.round(((b.technicalScore * techWeight / 100) + (b.commercialScore * commWeight / 100)) * 100) / 100;
    });

    // Calculate final ranks
    bidders.sort((a, b) => b.combinedScore - a.combinedScore);
    bidders.forEach((b, i) => {
      b.finalRank = i + 1;
      b.isWinner = i === 0;
    });

    return {
      tenderId,
      technicalWeight: techWeight,
      commercialWeight: commWeight,
      bidders,
      recommendedBidderId: bidders[0].bidderId,
      recommendedBidderName: bidders[0].bidderName,
      generatedAt: new Date()
    };
  }

  private generateMockSensitivityAnalysis(tenderId: number): SensitivityAnalysis {
    const rows: SensitivityRow[] = this.mockBidders.map(bidder => {
      const techScore = bidder.bidderId === 1 ? 82.5 : bidder.bidderId === 2 ? 70.2 : 85.8;
      const commScore = bidder.bidderId === 1 ? 88.3 : bidder.bidderId === 2 ? 78.5 : 82.1;

      const ranks: Record<string, number> = {};
      const winnerAtSplits: string[] = [];

      DEFAULT_WEIGHT_SPLITS.forEach(split => {
        const key = `${split.technicalWeight}/${split.commercialWeight}`;
        const combined = (techScore * split.technicalWeight / 100) + (commScore * split.commercialWeight / 100);

        // Calculate rank for this split (simplified - would need all bidders)
        if (bidder.bidderId === 1) {
          ranks[key] = split.technicalWeight >= 50 ? 2 : 1;
          if (split.technicalWeight < 50) winnerAtSplits.push(key);
        } else if (bidder.bidderId === 3) {
          ranks[key] = split.technicalWeight >= 50 ? 1 : 2;
          if (split.technicalWeight >= 50) winnerAtSplits.push(key);
        } else {
          ranks[key] = 3;
        }
      });

      return {
        bidderId: bidder.bidderId,
        bidderName: bidder.bidderName,
        ranks,
        winnerAtSplits,
        hasRankChange: new Set(Object.values(ranks)).size > 1
      };
    });

    return {
      tenderId,
      weightSplits: DEFAULT_WEIGHT_SPLITS,
      rows,
      winnerChanges: [
        { split: '50/50', previousWinner: 'Tech Solutions Ltd', newWinner: 'Global IT Partners' }
      ]
    };
  }
}
