import { Component, OnInit, OnDestroy, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { Subject, takeUntil, interval, forkJoin, filter, switchMap, catchError, EMPTY } from 'rxjs';
import { TabViewModule } from 'primeng/tabview';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { TableModule } from 'primeng/table';
import { TooltipModule } from 'primeng/tooltip';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { DialogModule } from 'primeng/dialog';
import { BadgeModule } from 'primeng/badge';
import { BreadcrumbModule } from 'primeng/breadcrumb';
import { TimelineModule } from 'primeng/timeline';
import { DividerModule } from 'primeng/divider';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { ConfirmationService, MessageService, MenuItem } from 'primeng/api';
import { AuthService } from '../../../core/auth/auth.service';
import {
  Bidder,
  TenderBidder,
  InvitationStatus,
  PrequalificationStatus
} from '../../../core/models/bidder.model';
import { BidderService } from '../../../core/services/bidder.service';
import { TenderService } from '../../../core/services/tender.service';
import {
  Tender as TenderModel,
  TenderInvitedBidder,
  TenderActivity,
  TENDER_STATUS_CONFIG,
  TenderStatus
} from '../../../core/models/tender.model';
import { InviteBiddersComponent } from './invite-bidders/invite-bidders.component';
import { BoqTabComponent } from './boq/boq-tab.component';
import { ClarificationsTabComponent } from './clarifications/clarifications-tab.component';
import { BidsTabComponent } from './bids/bids-tab.component';
import { ComparableSheetComponent } from './evaluation/comparable-sheet.component';
import { EvaluationSetupComponent } from './evaluation/evaluation-setup.component';
import { TechnicalScoringComponent } from './evaluation/technical-scoring.component';
import { CombinedScorecardComponent } from './evaluation/combined-scorecard.component';
import { TechnicalSummaryComponent } from './evaluation/technical-summary.component';
import { ApprovalTabComponent } from './approval/approval-tab.component';
import { DocumentsTabComponent } from './documents/documents-tab.component';
import { EvaluationService } from '../../../core/services/evaluation.service';
import { EvaluationSetup } from '../../../core/models/evaluation.model';
import { UserRole } from '../../../core/models/user.model';

interface Tender {
  id: number;
  title: string;
  titleAr?: string;
  referenceNumber: string;
  description?: string;
  status: 'draft' | 'published' | 'open' | 'evaluation' | 'closed' | 'awarded' | 'cancelled';
  organization: string;
  category: string;
  publishDate?: Date;
  deadline: Date;
  budget: number | null;
  currency: string;
}

interface CountdownTime {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
  expired: boolean;
}

@Component({
  selector: 'app-tender-details',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    TabViewModule,
    CardModule,
    ButtonModule,
    TagModule,
    TableModule,
    TooltipModule,
    ToastModule,
    ConfirmDialogModule,
    DialogModule,
    BadgeModule,
    BreadcrumbModule,
    TimelineModule,
    DividerModule,
    ProgressSpinnerModule,
    InviteBiddersComponent,
    BoqTabComponent,
    ClarificationsTabComponent,
    BidsTabComponent,
    ComparableSheetComponent,
    EvaluationSetupComponent,
    TechnicalScoringComponent,
    CombinedScorecardComponent,
    TechnicalSummaryComponent,
    ApprovalTabComponent,
    DocumentsTabComponent
  ],
  providers: [MessageService, ConfirmationService],
  template: `
    <p-toast></p-toast>
    <div class="tender-details-container">
      <!-- Polished Header Section -->
      <div class="page-header-wrapper">
        <!-- Breadcrumb Navigation -->
        <nav class="breadcrumb-nav">
          <a routerLink="/home" class="breadcrumb-link">
            <i class="pi pi-home"></i>
          </a>
          <i class="pi pi-chevron-right breadcrumb-separator"></i>
          <a routerLink="/tenders" class="breadcrumb-link">Tenders</a>
          <i class="pi pi-chevron-right breadcrumb-separator"></i>
          <span class="breadcrumb-current">{{ tender()?.title || 'Loading...' }}</span>
        </nav>

        <!-- Main Header -->
        <div class="page-header">
          <div class="header-content">
            <div class="tender-title-section">
              <div class="title-row">
                <h1 data-testid="tender-title">{{ tender()?.title }}</h1>
                <p-tag
                  [value]="getStatusLabel(tender()?.status)"
                  [severity]="getStatusSeverity(tender()?.status)"
                  data-testid="tender-status"
                  styleClass="status-badge"
                ></p-tag>
              </div>
              <div class="tender-meta">
                <span class="reference" data-testid="tender-reference">
                  <i class="pi pi-hashtag"></i>
                  {{ tender()?.referenceNumber }}
                </span>
                @if (tender()?.organization) {
                  <span class="meta-divider">•</span>
                  <span class="organization">
                    <i class="pi pi-building"></i>
                    {{ tender()?.organization }}
                  </span>
                }
                @if (tender()?.deadline) {
                  <span class="meta-divider">•</span>
                  <span class="deadline">
                    <i class="pi pi-calendar"></i>
                    Due {{ tender()?.deadline | date:'mediumDate' }}
                  </span>
                }
              </div>
            </div>
          </div>
          <div class="header-actions">
            @if (canManageTender()) {
              @if (tender()?.status === 'draft') {
                <button
                  pButton
                  label="Edit"
                  icon="pi pi-pencil"
                  class="p-button-outlined"
                  data-testid="edit-tender-btn"
                  (click)="editTender()"
                ></button>
                <button
                  pButton
                  label="Publish"
                  icon="pi pi-send"
                  data-testid="publish-tender-btn"
                  (click)="publishTender()"
                ></button>
              }
              @if (tender()?.status === 'open') {
                <button
                  pButton
                  label="Close Tender"
                  icon="pi pi-stop-circle"
                  class="p-button-outlined p-button-warning"
                  (click)="closeTender()"
                ></button>
              }
              @if (tender()?.status !== 'cancelled' && tender()?.status !== 'awarded') {
                <button
                  pButton
                  label="Archive"
                  icon="pi pi-inbox"
                  class="p-button-outlined p-button-secondary"
                  (click)="archiveTender()"
                ></button>
              }
            }
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <p-tabView [(activeIndex)]="activeTabIndex">
        <!-- Overview Tab -->
        <p-tabPanel header="Overview">
          <div class="overview-grid">
            <!-- Key Dates Card with Countdown -->
            <p-card header="Key Dates" styleClass="dates-card">
              <div class="dates-grid">
                <div class="date-item">
                  <div class="date-label">Issue Date</div>
                  <div class="date-value">{{ tender()?.publishDate | date:'mediumDate' }}</div>
                </div>
                <div class="date-item highlight">
                  <div class="date-label">Submission Deadline</div>
                  <div class="date-value">{{ tender()?.deadline | date:'mediumDate' }}</div>
                  @if (submissionCountdown() && !submissionCountdown()!.expired) {
                    <div class="countdown">
                      <span class="countdown-item">{{ submissionCountdown()!.days }}d</span>
                      <span class="countdown-item">{{ submissionCountdown()!.hours }}h</span>
                      <span class="countdown-item">{{ submissionCountdown()!.minutes }}m</span>
                      <span class="countdown-item">{{ submissionCountdown()!.seconds }}s</span>
                    </div>
                  } @else if (submissionCountdown()?.expired) {
                    <p-tag value="Expired" severity="danger"></p-tag>
                  }
                </div>
              </div>
            </p-card>

            <!-- Bidder Status Card -->
            <p-card header="Bidder Status" styleClass="stats-card">
              <div class="bidder-stats">
                <div class="stat-item">
                  <div class="stat-value">{{ invitedBidders().length }}</div>
                  <div class="stat-label">Invited</div>
                </div>
                <div class="stat-divider"></div>
                <div class="stat-item">
                  <div class="stat-value">{{ getAcceptedCount() }}</div>
                  <div class="stat-label">Accepted</div>
                </div>
                <div class="stat-divider"></div>
                <div class="stat-item">
                  <div class="stat-value">{{ getSubmittedCount() }}</div>
                  <div class="stat-label">Submitted</div>
                </div>
              </div>
              <div class="submission-progress">
                <div class="progress-bar">
                  <div
                    class="progress-fill"
                    [style.width.%]="submissionRate()"
                  ></div>
                </div>
                <span class="progress-label">{{ submissionRate() | number:'1.0-0' }}% submission rate</span>
              </div>
            </p-card>

            <!-- Tender Information Card -->
            <p-card header="Tender Information" styleClass="info-card full-width">
              <div class="info-grid">
                <div class="info-item">
                  <label>Organization</label>
                  <span>{{ tender()?.organization }}</span>
                </div>
                <div class="info-item">
                  <label>Category</label>
                  <span>{{ tender()?.category }}</span>
                </div>
                <div class="info-item">
                  <label>Budget</label>
                  @if (tender()?.budget) {
                    <span>{{ tender()?.budget | currency:tender()?.currency:'symbol':'1.0-0' }}</span>
                  } @else {
                    <span>Not specified</span>
                  }
                </div>
                <div class="info-item">
                  <label>Currency</label>
                  <span>{{ tender()?.currency }}</span>
                </div>
                <div class="info-item full-width">
                  <label>Description</label>
                  @if (tender()?.description) {
                    <div class="description-content" [innerHTML]="tender()!.description"></div>
                  } @else {
                    <p>No description provided.</p>
                  }
                </div>
              </div>
            </p-card>

            <!-- Timeline Visualization -->
            <p-card header="Timeline" styleClass="timeline-card">
              <p-timeline [value]="timelineEvents()" layout="vertical">
                <ng-template pTemplate="marker" let-event>
                  <span
                    class="timeline-marker"
                    [style.background-color]="event.color"
                  >
                    <i [class]="event.icon"></i>
                  </span>
                </ng-template>
                <ng-template pTemplate="content" let-event>
                  <div class="timeline-content">
                    <span class="timeline-title">{{ event.title }}</span>
                    <span class="timeline-date">{{ event.date | date:'medium' }}</span>
                  </div>
                </ng-template>
              </p-timeline>
            </p-card>

            @if (canManageTender()) {
              <!-- Invited Bidders Preview -->
              <p-card header="Invited Bidders" styleClass="bidders-preview-card full-width">
                <p-table
                  [value]="invitedBidders().slice(0, 5)"
                  styleClass="p-datatable-sm"
                >
                  <ng-template pTemplate="header">
                    <tr>
                      <th>Company</th>
                      <th>Email</th>
                      <th>Status</th>
                      <th>Invited</th>
                    </tr>
                  </ng-template>
                  <ng-template pTemplate="body" let-tenderBidder>
                    <tr>
                      <td>{{ tenderBidder.bidder.companyNameEn }}</td>
                      <td>{{ tenderBidder.bidder.email }}</td>
                      <td>
                        <p-tag
                          [value]="getInvitationStatusLabel(tenderBidder.invitationStatus)"
                          [severity]="getInvitationStatusSeverity(tenderBidder.invitationStatus)"
                        ></p-tag>
                      </td>
                      <td>{{ tenderBidder.invitedAt | date:'shortDate' }}</td>
                    </tr>
                  </ng-template>
                  <ng-template pTemplate="emptymessage">
                    <tr>
                      <td colspan="4" class="text-center p-3">No bidders invited yet</td>
                    </tr>
                  </ng-template>
                </p-table>
                @if (invitedBidders().length > 5) {
                  <div class="view-all-link">
                    <button pButton label="View All Bidders" class="p-button-text" (click)="activeTabIndex = 1"></button>
                  </div>
                }
              </p-card>
            }

            <!-- Activity Feed -->
            <p-card header="Recent Activity" styleClass="activity-card full-width">
              <div class="activity-feed">
                @for (activity of activities().slice(0, 5); track activity.id) {
                  <div class="activity-item">
                    <div class="activity-icon" [class]="getActivityIconClass(activity.action)">
                      <i [class]="getActivityIcon(activity.action)"></i>
                    </div>
                    <div class="activity-content">
                      <span class="activity-description">{{ activity.description }}</span>
                      <div class="activity-meta">
                        <span class="activity-user">{{ activity.userName }}</span>
                        <span class="activity-time">{{ activity.timestamp | date:'medium' }}</span>
                      </div>
                    </div>
                  </div>
                }
                @if (activities().length === 0) {
                  <p class="no-activity">No activity recorded yet</p>
                }
              </div>
            </p-card>
          </div>
        </p-tabPanel>

        @if (canManageTender()) {
          <!-- Bidders Tab -->
          <p-tabPanel>
            <ng-template pTemplate="header">
              <span>Bidders</span>
              @if (invitedBidders().length > 0) {
                <p-badge [value]="invitedBidders().length.toString()" styleClass="ml-2"></p-badge>
              }
            </ng-template>

            <div class="bidders-tab">
              <div class="bidders-header">
                <h3>Invited Bidders</h3>
                <button
                  pButton
                  label="Invite Bidders"
                  icon="pi pi-user-plus"
                  (click)="showInviteBiddersDialog = true"
                ></button>
              </div>

              @if (invitedBidders().length > 0) {
                <p-table
                  [value]="invitedBidders()"
                  [paginator]="true"
                  [rows]="10"
                  styleClass="p-datatable-striped"
                >
                  <ng-template pTemplate="header">
                    <tr>
                      <th pSortableColumn="bidder.companyNameEn">Company <p-sortIcon field="bidder.companyNameEn"></p-sortIcon></th>
                      <th pSortableColumn="bidder.email">Email <p-sortIcon field="bidder.email"></p-sortIcon></th>
                      <th pSortableColumn="invitationStatus">Invitation Status <p-sortIcon field="invitationStatus"></p-sortIcon></th>
                      <th pSortableColumn="invitedAt">Invited At <p-sortIcon field="invitedAt"></p-sortIcon></th>
                      <th>Actions</th>
                    </tr>
                  </ng-template>
                  <ng-template pTemplate="body" let-tenderBidder>
                    <tr>
                      <td>
                        <div class="bidder-info">
                          <span class="company-name">{{ tenderBidder.bidder.companyNameEn }}</span>
                          @if (tenderBidder.bidder.companyNameAr) {
                            <span class="company-name-ar">{{ tenderBidder.bidder.companyNameAr }}</span>
                          }
                        </div>
                      </td>
                      <td>{{ tenderBidder.bidder.email }}</td>
                      <td>
                        <p-tag
                          [value]="getInvitationStatusLabel(tenderBidder.invitationStatus)"
                          [severity]="getInvitationStatusSeverity(tenderBidder.invitationStatus)"
                        ></p-tag>
                      </td>
                      <td>{{ tenderBidder.invitedAt | date:'medium' }}</td>
                      <td>
                        <div class="action-buttons">
                          <button
                            pButton
                            icon="pi pi-refresh"
                            class="p-button-text p-button-sm"
                            pTooltip="Resend Invitation"
                            [disabled]="tenderBidder.invitationStatus === 'accepted'"
                            (click)="resendInvitation(tenderBidder)"
                          ></button>
                          <button
                            pButton
                            icon="pi pi-trash"
                            class="p-button-text p-button-sm p-button-danger"
                            pTooltip="Remove Bidder"
                            (click)="confirmRemoveBidder(tenderBidder)"
                          ></button>
                        </div>
                      </td>
                    </tr>
                  </ng-template>
                </p-table>
              } @else {
                <div class="empty-state">
                  <i class="pi pi-users" style="font-size: 3rem; color: var(--bayan-border, #E2E8F0);"></i>
                  <p>No bidders have been invited yet.</p>
                  <button
                    pButton
                    label="Invite Bidders"
                    icon="pi pi-user-plus"
                    class="p-button-outlined"
                    (click)="showInviteBiddersDialog = true"
                  ></button>
                </div>
              }
            </div>
          </p-tabPanel>
        }

        <!-- Documents Tab -->
        <p-tabPanel header="Documents">
          @if (tender()) {
            <app-documents-tab
              [tenderId]="tender()!.id"
            ></app-documents-tab>
          }
        </p-tabPanel>

        @if (canManageTender()) {
          <!-- Clarifications Tab -->
          <p-tabPanel header="Clarifications">
            @if (tender()) {
              <app-clarifications-tab
                [tenderId]="tender()!.id"
              ></app-clarifications-tab>
            }
          </p-tabPanel>
        }

        @if (canManageBoq()) {
          <!-- BOQ Tab -->
          <p-tabPanel header="BOQ">
            @if (tender()) {
              <app-boq-tab
                [tenderId]="tender()!.id"
              ></app-boq-tab>
            }
          </p-tabPanel>
        }

        @if (canViewBids()) {
          <!-- Bids Tab -->
          <p-tabPanel header="Bids">
            @if (tender()) {
              <app-bids-tab
                [tenderId]="tender()!.id"
              ></app-bids-tab>
            }
          </p-tabPanel>
        }

        <!-- Evaluation Tab -->
        <p-tabPanel header="Evaluation">
          @if (tender()) {
            <div class="evaluation-sub-nav">
              @if (canViewComparable()) {
                <button pButton
                  label="Comparable Sheet"
                  [outlined]="evaluationSubView() !== 'comparable'"
                  icon="pi pi-table"
                  class="p-button-sm"
                  (click)="evaluationSubView.set('comparable')"></button>
              }
              @if (canConfigureEvaluation()) {
                <button pButton
                  label="Evaluation Setup"
                  [outlined]="evaluationSubView() !== 'setup'"
                  icon="pi pi-cog"
                  class="p-button-sm"
                  (click)="evaluationSubView.set('setup')"></button>
              }
              @if (canScoreTechnical()) {
                <button pButton
                  label="Technical Scoring"
                  [outlined]="evaluationSubView() !== 'technical'"
                  icon="pi pi-check-square"
                  class="p-button-sm"
                  (click)="evaluationSubView.set('technical')"></button>
              }
              @if (canViewTechnicalScores()) {
                <button pButton
                  label="Technical Summary"
                  [outlined]="evaluationSubView() !== 'technical-summary'"
                  icon="pi pi-chart-line"
                  class="p-button-sm"
                  (click)="evaluationSubView.set('technical-summary')"></button>
              }
              @if (canViewCombined()) {
                <button pButton
                  label="Combined Scorecard"
                  [outlined]="evaluationSubView() !== 'scorecard'"
                  icon="pi pi-chart-bar"
                  class="p-button-sm"
                  (click)="evaluationSubView.set('scorecard')"></button>
              }
            </div>
            @switch (evaluationSubView()) {
              @case ('comparable') {
                <app-comparable-sheet [tenderId]="tender()!.id"></app-comparable-sheet>
              }
              @case ('setup') {
                <app-evaluation-setup [tenderId]="tender()!.id"></app-evaluation-setup>
              }
              @case ('technical') {
                @if (evaluationSetup()) {
                  <app-technical-scoring [tenderId]="tender()!.id" [setup]="evaluationSetup()!"></app-technical-scoring>
                } @else {
                  <div class="empty-state">
                    <i class="pi pi-spin pi-spinner" style="font-size: 2rem; color: var(--bayan-muted-foreground, #64748B);"></i>
                    <p>Loading evaluation configuration...</p>
                  </div>
                }
              }
              @case ('technical-summary') {
                <app-technical-summary [tenderId]="tender()!.id"></app-technical-summary>
              }
              @case ('scorecard') {
                <app-combined-scorecard [tenderId]="tender()!.id"></app-combined-scorecard>
              }
            }
          }
        </p-tabPanel>

        <!-- Approval Tab -->
        <p-tabPanel header="Approval">
          @if (tender()) {
            <app-approval-tab
              [tenderId]="tender()!.id"
            ></app-approval-tab>
          }
        </p-tabPanel>
      </p-tabView>

      @if (canManageTender()) {
        <!-- Invite Bidders Dialog -->
        <p-dialog
          header="Invite Bidders to Tender"
          [(visible)]="showInviteBiddersDialog"
          [modal]="true"
          [style]="{ width: '90vw', maxWidth: '1200px' }"
          [contentStyle]="{ overflow: 'auto' }"
        >
          <app-invite-bidders
            [tender]="tender() ?? undefined"
            [existingBidderIds]="getExistingBidderIds()"
            (invitationsSent)="onInvitationsSent($event)"
            (cancelled)="showInviteBiddersDialog = false"
          ></app-invite-bidders>
        </p-dialog>
      }

      <p-confirmDialog></p-confirmDialog>
    </div>
  `,
  styleUrl: './tender-details.component.scss'
})
export class TenderDetailsComponent implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly authService = inject(AuthService);
  private readonly bidderService = inject(BidderService);
  private readonly tenderService = inject(TenderService);
  private readonly evaluationService = inject(EvaluationService);
  private readonly messageService = inject(MessageService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly destroy$ = new Subject<void>();

  tender = signal<Tender | null>(null);
  invitedBidders = signal<TenderBidder[]>([]);
  activities = signal<TenderActivity[]>([]);
  submissionCountdown = signal<CountdownTime | null>(null);
  activeTabIndex = 0;
  showInviteBiddersDialog = false;
  evaluationSubView = signal<'comparable' | 'setup' | 'technical' | 'technical-summary' | 'scorecard'>('comparable');
  evaluationSetup = signal<EvaluationSetup | null>(null);

  canManageTender = computed(() => this.authService.hasRole([UserRole.ADMIN, UserRole.TENDER_MANAGER]));
  canManageBoq = computed(() => this.authService.hasRole([UserRole.ADMIN, UserRole.TENDER_MANAGER, UserRole.COMMERCIAL_ANALYST]));
  canViewBids = computed(() => this.authService.hasRole([UserRole.ADMIN, UserRole.TENDER_MANAGER, UserRole.COMMERCIAL_ANALYST]));
  canViewComparable = computed(() => this.authService.hasRole([UserRole.ADMIN, UserRole.TENDER_MANAGER, UserRole.COMMERCIAL_ANALYST, UserRole.APPROVER, UserRole.AUDITOR]));
  canViewCombined = computed(() => this.authService.hasRole([UserRole.ADMIN, UserRole.TENDER_MANAGER, UserRole.COMMERCIAL_ANALYST, UserRole.APPROVER, UserRole.AUDITOR]));
  canConfigureEvaluation = computed(() => this.canManageTender());
  canScoreTechnical = computed(() => this.authService.hasRole([UserRole.TECHNICAL_PANELIST]));
  canViewTechnicalScores = computed(() => this.authService.hasRole([UserRole.ADMIN, UserRole.TENDER_MANAGER, UserRole.TECHNICAL_PANELIST, UserRole.APPROVER, UserRole.AUDITOR]));

  breadcrumbItems: MenuItem[] = [];
  homeItem: MenuItem = { icon: 'pi pi-home', routerLink: '/home' };

  submissionRate = computed(() => {
    const total = this.invitedBidders().length || 0;
    const submitted = this.getSubmittedCount();
    return total > 0 ? (submitted / total) * 100 : 0;
  });

  timelineEvents = computed(() => {
    const t = this.tender();
    if (!t) return [];

    const events = [];

    if (t.publishDate) {
      events.push({
        title: 'Issue Date',
        date: new Date(t.publishDate),
        icon: 'pi pi-calendar',
        color: '#0F172A'
      });
    }

    events.push({
      title: 'Submission Deadline',
      date: new Date(t.deadline),
      icon: 'pi pi-send',
      color: '#16A34A'
    });

    return events.sort((a, b) => a.date.getTime() - b.date.getTime());
  });

  ngOnInit(): void {
    this.setDefaultEvaluationSubView();
    this.loadTenderDetails();
    this.loadInvitedBidders();
    this.loadActivities();
    this.loadEvaluationSetup();
    this.startCountdown();
    this.startAutoRefresh();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private startCountdown(): void {
    interval(1000).pipe(takeUntil(this.destroy$)).subscribe(() => {
      const t = this.tender();
      if (t) {
        this.submissionCountdown.set(
          this.calculateCountdown(new Date(t.deadline))
        );
      }
    });
  }

  private startAutoRefresh(): void {
    const nonPollingStatuses: Tender['status'][] = ['draft', 'awarded', 'cancelled'];
    const tenderId = this.route.snapshot.params['id'];
    if (!tenderId) return;

    interval(15000).pipe(
      takeUntil(this.destroy$),
      filter(() => {
        const status = this.tender()?.status;
        return !!status && !nonPollingStatuses.includes(status);
      }),
      switchMap(() => this.tenderService.getTenderById(tenderId).pipe(
        catchError(() => EMPTY)
      ))
    ).subscribe({
      next: (apiTender) => {
        const tender: Tender = {
          id: apiTender.id as number,
          title: apiTender.title,
          referenceNumber: apiTender.reference,
          description: apiTender.description,
          status: this.mapServiceStatus(apiTender.status),
          organization: apiTender.clientName || '',
          category: apiTender.type || 'open',
          publishDate: apiTender.dates?.issueDate ? new Date(String(apiTender.dates.issueDate)) : undefined,
          deadline: apiTender.dates?.submissionDeadline ? new Date(String(apiTender.dates.submissionDeadline)) : new Date(),
          budget: apiTender.estimatedValue ?? null,
          currency: apiTender.currency || 'AED'
        };
        this.tender.set(tender);
      }
    });
  }

  private setDefaultEvaluationSubView(): void {
    if (this.canScoreTechnical()) {
      this.evaluationSubView.set('technical');
      return;
    }

    if (this.canViewComparable()) {
      this.evaluationSubView.set('comparable');
      return;
    }

    if (this.canViewTechnicalScores()) {
      this.evaluationSubView.set('technical-summary');
      return;
    }

    if (this.canViewCombined()) {
      this.evaluationSubView.set('scorecard');
    }
  }

  private calculateCountdown(deadline: Date): CountdownTime {
    const now = new Date().getTime();
    const target = deadline.getTime();
    const diff = target - now;

    if (diff <= 0) {
      return { days: 0, hours: 0, minutes: 0, seconds: 0, expired: true };
    }

    return {
      days: Math.floor(diff / (1000 * 60 * 60 * 24)),
      hours: Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
      minutes: Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60)),
      seconds: Math.floor((diff % (1000 * 60)) / 1000),
      expired: false
    };
  }

  private loadActivities(): void {
    const tenderId = this.route.snapshot.params['id'];
    if (!tenderId) return;
    this.tenderService.getActivityLog(tenderId).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (activities) => {
        this.activities.set(activities);
      }
    });
  }

  private loadEvaluationSetup(): void {
    const tenderId = this.route.snapshot.params['id'];
    if (!tenderId) return;
    this.evaluationService.getEvaluationSetup(tenderId).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (setup) => {
        this.evaluationSetup.set(setup);
      },
      error: () => {
        // Evaluation setup not configured yet - leave as null
        this.evaluationSetup.set(null);
      }
    });
  }

  private loadTenderDetails(): void {
    const tenderId = this.route.snapshot.params['id'];
    if (!tenderId) return;

    this.tenderService.getTenderById(tenderId).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (apiTender) => {
        // Map service Tender model to local view model
        const tender: Tender = {
          id: apiTender.id as number,
          title: apiTender.title,
          referenceNumber: apiTender.reference,
          description: apiTender.description,
          status: this.mapServiceStatus(apiTender.status),
          organization: apiTender.clientName || '',
          category: apiTender.type || 'open',
          publishDate: apiTender.dates?.issueDate ? new Date(String(apiTender.dates.issueDate)) : undefined,
          deadline: apiTender.dates?.submissionDeadline ? new Date(String(apiTender.dates.submissionDeadline)) : new Date(),
          budget: apiTender.estimatedValue ?? null,
          currency: apiTender.currency || 'AED'
        };
        this.tender.set(tender);
        this.updateBreadcrumb(tender);
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load tender details'
        });
      }
    });
  }

  private mapServiceStatus(status: string): Tender['status'] {
    const statusMap: Record<string, Tender['status']> = {
      'draft': 'draft',
      'active': 'open',
      'evaluation': 'evaluation',
      'awarded': 'awarded',
      'closed': 'closed',
      'cancelled': 'cancelled'
    };
    return statusMap[status] || 'draft';
  }

  private updateBreadcrumb(tender: Tender): void {
    this.breadcrumbItems = [
      { label: 'Tenders', routerLink: '/tenders' },
      { label: tender.title }
    ];
  }

  editTender(): void {
    const t = this.tender();
    if (t) {
      this.router.navigate(['/tenders', t.id, 'edit']);
    }
  }

  publishTender(): void {
    this.confirmationService.confirm({
      message: 'Are you sure you want to publish this tender? This will make it visible to invited bidders.',
      header: 'Confirm Publish',
      icon: 'pi pi-send',
      accept: () => {
        const t = this.tender();
        if (t) {
          this.tenderService.updateTenderStatus(t.id, 'active').subscribe({
            next: () => {
              this.messageService.add({
                severity: 'success',
                summary: 'Success',
                detail: 'Tender published successfully'
              });
              this.loadTenderDetails();
              this.loadActivities();
              this.loadInvitedBidders();
            },
            error: (err: any) => {
              this.messageService.add({
                severity: 'error',
                summary: 'Error',
                detail: err?.message || 'Failed to publish tender'
              });
            }
          });
        }
      }
    });
  }

  closeTender(): void {
    this.confirmationService.confirm({
      message: 'Are you sure you want to close this tender? No more bids will be accepted.',
      header: 'Confirm Close',
      icon: 'pi pi-stop-circle',
      accept: () => {
        const t = this.tender();
        if (t) {
          this.tenderService.updateTenderStatus(t.id, 'closed').subscribe({
            next: () => {
              this.messageService.add({
                severity: 'success',
                summary: 'Success',
                detail: 'Tender closed successfully'
              });
              this.loadTenderDetails();
              this.loadActivities();
            },
            error: (err: any) => {
              this.messageService.add({
                severity: 'error',
                summary: 'Error',
                detail: err?.message || 'Failed to close tender'
              });
            }
          });
        }
      }
    });
  }

  archiveTender(): void {
    this.confirmationService.confirm({
      message: 'Are you sure you want to archive this tender?',
      header: 'Confirm Archive',
      icon: 'pi pi-inbox',
      accept: () => {
        const t = this.tender();
        if (t) {
          this.tenderService.updateTenderStatus(t.id, 'cancelled').subscribe({
            next: () => {
              this.messageService.add({
                severity: 'success',
                summary: 'Success',
                detail: 'Tender archived successfully'
              });
              this.loadTenderDetails();
              this.loadActivities();
            },
            error: (err: any) => {
              this.messageService.add({
                severity: 'error',
                summary: 'Error',
                detail: err?.message || 'Failed to archive tender'
              });
            }
          });
        }
      }
    });
  }

  getActivityIcon(action: string): string {
    switch (action) {
      case 'created': return 'pi pi-plus';
      case 'updated': return 'pi pi-pencil';
      case 'published': return 'pi pi-send';
      case 'bid_received': return 'pi pi-briefcase';
      default: return 'pi pi-info-circle';
    }
  }

  getActivityIconClass(action: string): string {
    const validClasses = ['created', 'updated', 'published', 'bid_received'];
    return validClasses.includes(action) ? action : 'default';
  }

  private loadInvitedBidders(): void {
    const tenderId = this.route.snapshot.params['id'];
    if (!tenderId) return;

    this.tenderService.getInvitedBidders(tenderId).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (invitedList) => {
        // Map TenderInvitedBidder to TenderBidder for template compatibility
        const bidders: TenderBidder[] = invitedList.map(tib => ({
          id: tib.id,
          tenderId: tib.tenderId,
          bidderId: tib.bidderId,
          bidder: {
            id: tib.bidderId,
            companyNameEn: tib.bidderName,
            email: tib.bidderEmail,
            tradeSpecializations: [],
            prequalificationStatus: PrequalificationStatus.APPROVED,
            isActive: true,
            createdAt: new Date(),
            updatedAt: new Date()
          } as any,
          invitedAt: new Date(tib.invitedAt),
          invitedBy: 0,
          invitationStatus: this.mapToInvitationStatus(tib.status),
          bidSubmittedAt: tib.status === 'submitted' ? (tib.submittedAt ? new Date(String(tib.submittedAt)) : new Date()) : undefined
        }));
        this.invitedBidders.set(bidders);
      },
      error: () => {
        // No bidders or endpoint not available - show empty state
        this.invitedBidders.set([]);
      }
    });
  }

  private mapToInvitationStatus(status: string): InvitationStatus {
    switch (status) {
      case 'viewed': return InvitationStatus.VIEWED;
      case 'declined': return InvitationStatus.DECLINED;
      case 'submitted': return InvitationStatus.ACCEPTED;
      default: return InvitationStatus.SENT;
    }
  }

  getExistingBidderIds(): (number | string)[] {
    return this.invitedBidders().map(tb => tb.bidderId);
  }

  getAcceptedCount(): number {
    return this.invitedBidders().filter(
      tb => tb.invitationStatus === InvitationStatus.ACCEPTED
    ).length;
  }

  getSubmittedCount(): number {
    return this.invitedBidders().filter(
      tb => tb.bidSubmittedAt !== undefined || tb.invitationStatus === InvitationStatus.ACCEPTED
    ).length;
  }

  onInvitationsSent(bidders: Bidder[]): void {
    // Add new invitations to the list
    const newInvitations: TenderBidder[] = bidders.map((bidder, index) => ({
      id: Date.now() + index,
      tenderId: this.tender()!.id,
      bidderId: bidder.id,
      bidder,
      invitedAt: new Date(),
      invitedBy: 1, // Current user ID
      invitationStatus: InvitationStatus.SENT,
      invitationSentAt: new Date()
    }));

    this.invitedBidders.update(current => [...current, ...newInvitations]);
    this.showInviteBiddersDialog = false;

    this.messageService.add({
      severity: 'success',
      summary: 'Success',
      detail: `${bidders.length} bidder(s) invited successfully`
    });
  }

  resendInvitation(tenderBidder: TenderBidder): void {
    // In production: call bidderService.resendInvitation()
    this.messageService.add({
      severity: 'success',
      summary: 'Success',
      detail: `Invitation resent to ${tenderBidder.bidder.companyNameEn}`
    });
  }

  confirmRemoveBidder(tenderBidder: TenderBidder): void {
    this.confirmationService.confirm({
      message: `Are you sure you want to remove ${tenderBidder.bidder.companyNameEn} from this tender?`,
      header: 'Confirm Remove',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => {
        // In production: call bidderService.removeTenderBidder()
        this.invitedBidders.update(current =>
          current.filter(tb => tb.id !== tenderBidder.id)
        );
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Bidder removed from tender'
        });
      }
    });
  }

  getStatusLabel(status?: string): string {
    if (!status) return '';
    const labels: Record<string, string> = {
      'draft': 'Draft',
      'published': 'Published',
      'open': 'Open',
      'evaluation': 'Evaluation',
      'closed': 'Closed',
      'awarded': 'Awarded',
      'cancelled': 'Cancelled'
    };
    return labels[status] || status;
  }

  getStatusSeverity(status?: string): 'success' | 'secondary' | 'info' | 'warn' | 'danger' | 'contrast' | undefined {
    if (!status) return undefined;
    const severities: Record<string, 'success' | 'secondary' | 'info' | 'warn' | 'danger'> = {
      'draft': 'secondary',
      'published': 'info',
      'open': 'success',
      'evaluation': 'info',
      'closed': 'warn',
      'awarded': 'success',
      'cancelled': 'danger'
    };
    return severities[status];
  }

  getInvitationStatusLabel(status: InvitationStatus): string {
    const labels: Record<InvitationStatus, string> = {
      [InvitationStatus.PENDING]: 'Pending',
      [InvitationStatus.SENT]: 'Sent',
      [InvitationStatus.VIEWED]: 'Viewed',
      [InvitationStatus.ACCEPTED]: 'Accepted',
      [InvitationStatus.DECLINED]: 'Declined',
      [InvitationStatus.EXPIRED]: 'Expired'
    };
    return labels[status];
  }

  getInvitationStatusSeverity(status: InvitationStatus): 'success' | 'secondary' | 'info' | 'warn' | 'danger' {
    const severities: Record<InvitationStatus, 'success' | 'secondary' | 'info' | 'warn' | 'danger'> = {
      [InvitationStatus.PENDING]: 'secondary',
      [InvitationStatus.SENT]: 'info',
      [InvitationStatus.VIEWED]: 'info',
      [InvitationStatus.ACCEPTED]: 'success',
      [InvitationStatus.DECLINED]: 'danger',
      [InvitationStatus.EXPIRED]: 'warn'
    };
    return severities[status];
  }
}
