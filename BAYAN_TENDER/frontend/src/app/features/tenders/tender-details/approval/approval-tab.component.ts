import {
  Component,
  Input,
  OnInit,
  OnDestroy,
  inject,
  signal,
  computed
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';
import { StepsModule } from 'primeng/steps';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { TimelineModule } from 'primeng/timeline';
import { RadioButtonModule } from 'primeng/radiobutton';
import { InputTextarea } from 'primeng/inputtextarea';
import { ToastModule } from 'primeng/toast';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageModule } from 'primeng/message';
import { DividerModule } from 'primeng/divider';
import { AvatarModule } from 'primeng/avatar';
import { TooltipModule } from 'primeng/tooltip';
import { MessageService, MenuItem } from 'primeng/api';

import { ApprovalService } from '../../../../core/services/approval.service';
import { AuthService } from '../../../../core/auth/auth.service';
import {
  ApprovalWorkflow,
  ApprovalLevel,
  ApprovalLevelStatus,
  ApprovalDecision,
  ApprovalTimelineEntry,
  APPROVAL_LEVEL_STATUS_CONFIG,
  APPROVAL_WORKFLOW_STATUS_CONFIG,
  APPROVAL_DECISION_CONFIG
} from '../../../../core/models/approval.model';
import { InitiateApprovalDialogComponent } from './initiate-approval-dialog.component';

@Component({
  selector: 'app-approval-tab',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    StepsModule,
    CardModule,
    ButtonModule,
    TagModule,
    TimelineModule,
    RadioButtonModule,
    InputTextarea,
    ToastModule,
    ProgressSpinnerModule,
    MessageModule,
    DividerModule,
    AvatarModule,
    TooltipModule,
    InitiateApprovalDialogComponent
  ],
  providers: [MessageService],
  template: `
    <p-toast></p-toast>

    <div class="approval-tab-container" data-testid="approval-tab">
      <!-- Loading State -->
      @if (approvalService.isLoading() && !workflow()) {
        <div class="loading-container">
          <p-progressSpinner
            [style]="{ width: '50px', height: '50px' }"
            strokeWidth="4"
          ></p-progressSpinner>
          <p>Loading approval workflow...</p>
        </div>
      } @else if (!workflow()) {
        <!-- No Workflow - Initiate Button -->
        <div class="no-workflow-state">
          <div class="empty-state-content">
            <i class="pi pi-check-circle empty-icon"></i>
            <h3>No Approval Workflow</h3>
            <p>An approval workflow has not been initiated for this tender.</p>
            <button
              pButton
              label="Initiate Approval Workflow"
              icon="pi pi-play"
              data-testid="initiate-approval-btn"
              (click)="showInitiateDialog = true"
            ></button>
          </div>
        </div>
      } @else {
        <!-- Workflow Exists -->
        <div class="workflow-container" data-testid="approval-workflow">
          <!-- Header with Overall Status -->
          <div class="workflow-header">
            <div class="header-left">
              <h3>Approval Workflow</h3>
              <p-tag
                [value]="getWorkflowStatusLabel(workflow()!.status)"
                [severity]="getWorkflowStatusSeverity(workflow()!.status)"
              ></p-tag>
            </div>
            <div class="header-right">
              @if (workflow()!.awardPackUrl) {
                <button
                  pButton
                  icon="pi pi-download"
                  label="Download Award Pack"
                  class="p-button-outlined"
                  (click)="downloadAwardPack()"
                  [loading]="isDownloading()"
                ></button>
              }
            </div>
          </div>

          <!-- Initiator Info -->
          <div class="initiator-info">
            <span class="info-label">Initiated by:</span>
            <span class="info-value">
              {{ workflow()!.initiatedBy.firstName }} {{ workflow()!.initiatedBy.lastName }}
            </span>
            <span class="info-separator">|</span>
            <span class="info-label">Date:</span>
            <span class="info-value">{{ workflow()!.initiatedAt | date:'medium' }}</span>
          </div>

          <!-- Visual Stepper -->
          <div class="stepper-container">
            <p-steps
              [model]="stepItems()"
              [activeIndex]="activeStepIndex()"
              [readonly]="true"
              styleClass="approval-steps"
            ></p-steps>
          </div>

          <!-- Approval Levels Detail -->
          <div class="levels-grid">
            @for (level of workflow()!.levels; track level.level) {
              <p-card [styleClass]="'level-card ' + getLevelCardClass(level)">
                <ng-template pTemplate="header">
                  <div class="level-header">
                    <span class="level-number">Level {{ level.level }}</span>
                    <p-tag
                      [value]="getLevelStatusLabel(level.status)"
                      [severity]="getLevelStatusSeverity(level.status)"
                      [icon]="'pi ' + getLevelStatusIcon(level.status)"
                    ></p-tag>
                  </div>
                </ng-template>

                <div class="level-content">
                  <div class="approver-info">
                    <p-avatar
                      [label]="getApproverInitials(level.approver)"
                      shape="circle"
                      size="large"
                      [style]="{ 'background-color': getAvatarColor(level.level), color: '#ffffff' }"
                    ></p-avatar>
                    <div class="approver-details">
                      <span class="approver-name">
                        {{ level.approver.firstName }} {{ level.approver.lastName }}
                      </span>
                      <span class="approver-email">{{ level.approver.email }}</span>
                    </div>
                  </div>

                  @if (level.deadline) {
                    <div class="level-deadline">
                      <i class="pi pi-calendar"></i>
                      <span>Deadline: {{ level.deadline | date:'mediumDate' }}</span>
                    </div>
                  }

                  @if (level.decidedAt) {
                    <div class="level-decision">
                      <i class="pi pi-clock"></i>
                      <span>Decided: {{ level.decidedAt | date:'medium' }}</span>
                    </div>
                  }

                  @if (level.comment) {
                    <div class="level-comment">
                      <i class="pi pi-comment"></i>
                      <span>{{ level.comment }}</span>
                    </div>
                  }
                </div>
              </p-card>
            }
          </div>

          <!-- Decision Form (if current user is active approver) -->
          @if (isCurrentUserApprover() && workflow()!.status === 'in_progress') {
            <p-divider></p-divider>

            <p-card header="Submit Your Decision" styleClass="decision-card">
              <form [formGroup]="decisionForm" (ngSubmit)="onSubmitDecision()">
                <div class="decision-options">
                  <div class="option-group">
                    @for (option of decisionOptions; track option.value) {
                      <div class="decision-option" [attr.data-testid]="option.value === 'approve' ? 'approve-btn' : option.value === 'reject' ? 'reject-btn' : null">
                        <p-radioButton
                          [inputId]="option.value"
                          [value]="option.value"
                          formControlName="decision"
                        ></p-radioButton>
                        <label [for]="option.value" class="option-label">
                          <i [class]="'pi ' + option.icon" [style.color]="option.color"></i>
                          <span>{{ option.label }}</span>
                        </label>
                      </div>
                    }
                  </div>
                </div>

                <div class="comment-section">
                  <label for="comment">
                    Comment
                    @if (requiresComment()) {
                      <span class="required">*</span>
                    }
                  </label>
                  <textarea
                    pInputTextarea
                    id="comment"
                    formControlName="comment"
                    [rows]="4"
                    [autoResize]="true"
                    placeholder="Enter your comments..."
                    class="w-full"
                  ></textarea>
                  @if (decisionForm.get('comment')?.invalid && decisionForm.get('comment')?.touched) {
                    <small class="p-error">Comment is required for Reject or Return decisions</small>
                  }
                </div>

                <div class="form-actions">
                  <button
                    pButton
                    type="submit"
                    [label]="getSubmitButtonLabel()"
                    [icon]="getSubmitButtonIcon()"
                    [class]="getSubmitButtonClass()"
                    [disabled]="decisionForm.invalid"
                    [loading]="isSubmitting()"
                  ></button>
                </div>
              </form>
            </p-card>
          }

          <!-- Decision Timeline -->
          @if (workflow()!.timeline.length > 0) {
            <p-divider></p-divider>

            <div class="timeline-section">
              <h4>Decision History</h4>
              <p-timeline [value]="workflow()!.timeline" align="left">
                <ng-template pTemplate="marker" let-event>
                  <span
                    class="timeline-marker"
                    [class.approved]="event.decision === 'approve'"
                    [class.rejected]="event.decision === 'reject'"
                    [class.returned]="event.decision === 'return'"
                  >
                    <i [class]="getDecisionIcon(event.decision)"></i>
                  </span>
                </ng-template>

                <ng-template pTemplate="content" let-event>
                  <div class="timeline-event">
                    <div class="event-header">
                      <span class="event-approver">{{ event.approverName }}</span>
                      <p-tag
                        [value]="getDecisionLabel(event.decision)"
                        [severity]="getDecisionSeverity(event.decision)"
                        size="small"
                      ></p-tag>
                    </div>
                    <div class="event-meta">
                      <span class="event-level">Level {{ event.level }}</span>
                      <span class="event-time">{{ event.timestamp | date:'medium' }}</span>
                    </div>
                    @if (event.comment) {
                      <div class="event-comment">
                        <i class="pi pi-comment"></i>
                        {{ event.comment }}
                      </div>
                    }
                  </div>
                </ng-template>
              </p-timeline>
            </div>
          }
        </div>
      }

      <!-- Initiate Dialog -->
      <app-initiate-approval-dialog
        [visible]="showInitiateDialog"
        [tenderId]="tenderId"
        (visibleChange)="showInitiateDialog = $event"
        (initiated)="onWorkflowInitiated($event)"
      ></app-initiate-approval-dialog>
    </div>
  `,
  styles: [`
    .approval-tab-container {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 3rem;
      gap: 1rem;
    }

    .loading-container p {
      color: var(--bayan-muted-foreground, #71717a);
    }

    .no-workflow-state {
      display: flex;
      justify-content: center;
      padding: 3rem;
    }

    .empty-state-content {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      gap: 1rem;
      max-width: 400px;
    }

    .empty-icon {
      font-size: 4rem;
      color: var(--bayan-muted-foreground, #71717a);
      opacity: 0.5;
    }

    .empty-state-content h3 {
      margin: 0;
      color: var(--bayan-foreground, #09090b);
    }

    .empty-state-content p {
      margin: 0;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .workflow-container {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .workflow-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
    }

    .header-left {
      display: flex;
      align-items: center;
      gap: 1rem;
    }

    .header-left h3 {
      margin: 0;
      color: var(--bayan-foreground, #09090b);
    }

    .initiator-info {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.75rem 1rem;
      background-color: var(--bayan-accent, #f4f4f5);
      border-radius: var(--bayan-radius, 0.5rem);
      font-size: 0.9rem;
      flex-wrap: wrap;
    }

    .info-label {
      color: var(--bayan-muted-foreground, #71717a);
    }

    .info-value {
      color: var(--bayan-foreground, #09090b);
      font-weight: 500;
    }

    .info-separator {
      color: var(--bayan-border, #e4e4e7);
    }

    .stepper-container {
      padding: 1rem 0;
    }

    :host ::ng-deep .approval-steps .p-steps-item {
      flex: 1;
    }

    :host ::ng-deep .approval-steps .p-steps-item .p-menuitem-link {
      flex-direction: column;
      gap: 0.5rem;
    }

    .levels-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 1rem;
    }

    :host ::ng-deep .level-card {
      border: 2px solid var(--bayan-border, #e4e4e7);
      transition: border-color 0.2s;
    }

    :host ::ng-deep .level-card.active {
      border-color: var(--bayan-primary, #18181b);
      box-shadow: 0 0 0 3px rgba(24, 24, 27, 0.1);
    }

    :host ::ng-deep .level-card.approved {
      border-color: var(--bayan-success, #22c55e);
    }

    :host ::ng-deep .level-card.rejected {
      border-color: #f44336;
    }

    :host ::ng-deep .level-card.returned {
      border-color: var(--bayan-warning, #f59e0b);
    }

    :host ::ng-deep .level-card .p-card-header {
      padding: 1rem;
      background-color: var(--bayan-accent, #f4f4f5);
      border-bottom: 1px solid var(--bayan-border, #e4e4e7);
    }

    .level-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .level-number {
      font-weight: 600;
      color: var(--bayan-foreground, #09090b);
    }

    .level-content {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .approver-info {
      display: flex;
      align-items: center;
      gap: 1rem;
    }

    .approver-details {
      display: flex;
      flex-direction: column;
    }

    .approver-name {
      font-weight: 600;
      color: var(--bayan-foreground, #09090b);
    }

    .approver-email {
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .level-deadline,
    .level-decision,
    .level-comment {
      display: flex;
      align-items: flex-start;
      gap: 0.5rem;
      font-size: 0.9rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .level-deadline i,
    .level-decision i,
    .level-comment i {
      margin-top: 2px;
    }

    .level-comment {
      background-color: var(--bayan-accent, #f4f4f5);
      padding: 0.75rem;
      border-radius: 6px;
      font-style: italic;
    }

    /* Decision Form Styles */
    :host ::ng-deep .decision-card {
      background-color: var(--bayan-accent, #f4f4f5);
      border: 2px solid var(--bayan-primary, #18181b);
    }

    .decision-options {
      margin-bottom: 1.5rem;
    }

    .option-group {
      display: flex;
      flex-wrap: wrap;
      gap: 1.5rem;
    }

    .decision-option {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .option-label {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      cursor: pointer;
      font-weight: 500;
    }

    .comment-section {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      margin-bottom: 1.5rem;
    }

    .comment-section label {
      font-weight: 500;
      color: var(--bayan-foreground, #09090b);
    }

    .required {
      color: #f44336;
    }

    .form-actions {
      display: flex;
      justify-content: flex-end;
    }

    /* Timeline Styles */
    .timeline-section {
      padding: 1rem;
    }

    .timeline-section h4 {
      margin: 0 0 1rem 0;
      color: var(--bayan-foreground, #09090b);
    }

    .timeline-marker {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background-color: var(--bayan-border, #e4e4e7);
      color: var(--bayan-muted-foreground, #71717a);
    }

    .timeline-marker.approved {
      background-color: var(--bayan-success, #22c55e);
      color: white;
    }

    .timeline-marker.rejected {
      background-color: #f44336;
      color: white;
    }

    .timeline-marker.returned {
      background-color: var(--bayan-warning, #f59e0b);
      color: white;
    }

    .timeline-event {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      padding: 0.5rem 0;
    }

    .event-header {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .event-approver {
      font-weight: 600;
      color: var(--bayan-foreground, #09090b);
    }

    .event-meta {
      display: flex;
      gap: 1rem;
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .event-comment {
      display: flex;
      align-items: flex-start;
      gap: 0.5rem;
      padding: 0.75rem;
      background-color: var(--bayan-accent, #f4f4f5);
      border-radius: 6px;
      font-size: 0.9rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .event-comment i {
      margin-top: 2px;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .w-full {
      width: 100%;
    }

    @media (max-width: 768px) {
      .workflow-header {
        flex-direction: column;
        align-items: stretch;
      }

      .header-right {
        display: flex;
        justify-content: center;
      }

      .option-group {
        flex-direction: column;
      }

      .initiator-info {
        flex-direction: column;
        align-items: flex-start;
      }

      .info-separator {
        display: none;
      }
    }
  `]
})
export class ApprovalTabComponent implements OnInit, OnDestroy {
  @Input() tenderId!: number;

  readonly approvalService = inject(ApprovalService);
  private readonly authService = inject(AuthService);
  private readonly messageService = inject(MessageService);
  private readonly fb = inject(FormBuilder);
  private readonly destroy$ = new Subject<void>();

  // Data
  workflow = signal<ApprovalWorkflow | null>(null);

  // UI State
  showInitiateDialog = false;
  isDownloading = signal(false);
  isSubmitting = signal(false);

  // Decision form
  decisionForm: FormGroup;

  decisionOptions = [
    { value: 'approve', label: 'Approve', icon: 'pi-check', color: '#22c55e' },
    { value: 'reject', label: 'Reject', icon: 'pi-times', color: '#f44336' },
    { value: 'return', label: 'Return for Revision', icon: 'pi-replay', color: '#f59e0b' }
  ];

  // Computed
  stepItems = computed<MenuItem[]>(() => {
    const wf = this.workflow();
    if (!wf) return [];

    return wf.levels.map(level => ({
      label: `Level ${level.level}`,
      command: () => {}
    }));
  });

  activeStepIndex = computed(() => {
    const wf = this.workflow();
    if (!wf) return 0;
    return wf.currentLevel - 1;
  });

  constructor() {
    this.decisionForm = this.fb.group({
      decision: ['approve', Validators.required],
      comment: ['']
    });

    // Add dynamic validation for comment
    this.decisionForm.get('decision')?.valueChanges.subscribe(decision => {
      const commentControl = this.decisionForm.get('comment');
      if (decision === 'reject' || decision === 'return') {
        commentControl?.setValidators([Validators.required, Validators.minLength(10)]);
      } else {
        commentControl?.clearValidators();
      }
      commentControl?.updateValueAndValidity();
    });
  }

  ngOnInit(): void {
    this.loadWorkflow();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadWorkflow(): void {
    this.approvalService.getApprovalWorkflow(this.tenderId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (workflow) => {
          this.workflow.set(workflow);
        },
        error: (error) => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: error.message || 'Failed to load approval workflow'
          });
        }
      });
  }

  isCurrentUserApprover(): boolean {
    const wf = this.workflow();
    const currentUser = this.authService.currentUser();
    if (!wf || !currentUser) return false;

    return this.approvalService.isCurrentUserActiveApprover(wf, currentUser.id);
  }

  requiresComment(): boolean {
    const decision = this.decisionForm.get('decision')?.value;
    return decision === 'reject' || decision === 'return';
  }

  onSubmitDecision(): void {
    if (this.decisionForm.invalid) return;

    this.isSubmitting.set(true);
    const formValue = this.decisionForm.value;

    this.approvalService.submitDecision(this.tenderId, {
      decision: formValue.decision,
      comment: formValue.comment || undefined
    }).pipe(takeUntil(this.destroy$)).subscribe({
      next: (updatedWorkflow) => {
        this.isSubmitting.set(false);
        this.workflow.set(updatedWorkflow);
        this.decisionForm.reset({ decision: 'approve', comment: '' });

        const decisionLabel = this.getDecisionLabel(formValue.decision);
        this.messageService.add({
          severity: 'success',
          summary: 'Decision Submitted',
          detail: `Your decision "${decisionLabel}" has been recorded.`
        });
      },
      error: (error) => {
        this.isSubmitting.set(false);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to submit decision'
        });
      }
    });
  }

  downloadAwardPack(): void {
    this.isDownloading.set(true);

    this.approvalService.downloadAwardPack(this.tenderId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (blob) => {
          this.isDownloading.set(false);
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `tender_${this.tenderId}_award_pack.pdf`;
          a.click();
          window.URL.revokeObjectURL(url);

          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Award pack downloaded successfully'
          });
        },
        error: (error) => {
          this.isDownloading.set(false);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: error.message || 'Failed to download award pack'
          });
        }
      });
  }

  onWorkflowInitiated(workflow: ApprovalWorkflow): void {
    this.workflow.set(workflow);
    this.showInitiateDialog = false;
    this.messageService.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Approval workflow initiated successfully'
    });
  }

  // Helper methods
  getApproverInitials(approver: { firstName: string; lastName: string }): string {
    return `${approver.firstName[0]}${approver.lastName[0]}`.toUpperCase();
  }

  getAvatarColor(level: number): string {
    const colors = ['#18181b', '#71717a', '#a1a1aa'];
    return colors[(level - 1) % colors.length];
  }

  getLevelCardClass(level: ApprovalLevel): string {
    switch (level.status) {
      case 'active': return 'active';
      case 'approved': return 'approved';
      case 'rejected': return 'rejected';
      case 'returned': return 'returned';
      default: return '';
    }
  }

  getWorkflowStatusLabel(status: string): string {
    return APPROVAL_WORKFLOW_STATUS_CONFIG[status as keyof typeof APPROVAL_WORKFLOW_STATUS_CONFIG]?.label || status;
  }

  getWorkflowStatusSeverity(status: string): 'secondary' | 'success' | 'info' | 'warn' | 'danger' | 'contrast' {
    return APPROVAL_WORKFLOW_STATUS_CONFIG[status as keyof typeof APPROVAL_WORKFLOW_STATUS_CONFIG]?.severity || 'secondary';
  }

  getLevelStatusLabel(status: ApprovalLevelStatus): string {
    return APPROVAL_LEVEL_STATUS_CONFIG[status]?.label || status;
  }

  getLevelStatusSeverity(status: ApprovalLevelStatus): 'secondary' | 'success' | 'info' | 'warn' | 'danger' | 'contrast' {
    return APPROVAL_LEVEL_STATUS_CONFIG[status]?.severity || 'secondary';
  }

  getLevelStatusIcon(status: ApprovalLevelStatus): string {
    return APPROVAL_LEVEL_STATUS_CONFIG[status]?.icon || 'pi-circle';
  }

  getDecisionLabel(decision: ApprovalDecision): string {
    return APPROVAL_DECISION_CONFIG[decision]?.label || decision;
  }

  getDecisionSeverity(decision: ApprovalDecision): 'secondary' | 'success' | 'info' | 'warn' | 'danger' | 'contrast' {
    return APPROVAL_DECISION_CONFIG[decision]?.severity || 'secondary';
  }

  getDecisionIcon(decision: ApprovalDecision): string {
    return 'pi ' + (APPROVAL_DECISION_CONFIG[decision]?.icon || 'pi-circle');
  }

  getSubmitButtonLabel(): string {
    const decision = this.decisionForm.get('decision')?.value as ApprovalDecision;
    return this.getDecisionLabel(decision);
  }

  getSubmitButtonIcon(): string {
    const decision = this.decisionForm.get('decision')?.value as ApprovalDecision;
    return 'pi ' + (APPROVAL_DECISION_CONFIG[decision]?.icon || 'pi-check');
  }

  getSubmitButtonClass(): string {
    const decision = this.decisionForm.get('decision')?.value;
    switch (decision) {
      case 'approve': return 'p-button-success';
      case 'reject': return 'p-button-danger';
      case 'return': return 'p-button-warning';
      default: return '';
    }
  }
}
