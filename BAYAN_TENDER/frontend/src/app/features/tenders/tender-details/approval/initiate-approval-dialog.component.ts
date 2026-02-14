import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit,
  OnDestroy,
  OnChanges,
  SimpleChanges,
  inject,
  signal
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';
import { DialogModule } from 'primeng/dialog';
import { ButtonModule } from 'primeng/button';
import { DropdownModule } from 'primeng/dropdown';
import { DatePickerModule } from 'primeng/datepicker';
import { MessageModule } from 'primeng/message';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { TooltipModule } from 'primeng/tooltip';
import { InputTextarea } from 'primeng/inputtextarea';

import { ApprovalService } from '../../../../core/services/approval.service';
import {
  ApprovalWorkflow,
  ApproverOption,
  InitiateApprovalDto
} from '../../../../core/models/approval.model';

@Component({
  selector: 'app-initiate-approval-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    DialogModule,
    ButtonModule,
    DropdownModule,
    DatePickerModule,
    MessageModule,
    ProgressSpinnerModule,
    TooltipModule,
    InputTextarea
  ],
  template: `
    <p-dialog
      [header]="isReinitiation ? 'Re-initiate Approval Workflow' : 'Initiate Approval Workflow'"
      [(visible)]="visible"
      [modal]="true"
      [style]="{ width: 'min(860px, 95vw)' }"
      [breakpoints]="{ '960px': '94vw', '640px': '98vw' }"
      [contentStyle]="{ 'max-height': '72vh', overflow: 'auto' }"
      [draggable]="false"
      [resizable]="false"
      styleClass="initiate-approval-dialog"
      [closable]="!isSubmitting()"
      [closeOnEscape]="!isSubmitting()"
      (onHide)="onDialogHide()"
    >
      @if (isLoadingApprovers()) {
        <div class="loading-container">
          <p-progressSpinner
            [style]="{ width: '40px', height: '40px' }"
            strokeWidth="4"
          ></p-progressSpinner>
          <p>Loading approvers...</p>
        </div>
      } @else {
        <form [formGroup]="form" (ngSubmit)="onSubmit()" class="dialog-form">
          <p-message
            severity="info"
            text="Choose approvers in sequence. The decision route runs Level 1 -> Level 2 -> Level 3."
            styleClass="w-full"
          ></p-message>

          @if (isReinitiation && previousRouteReady()) {
            <p-message
              severity="info"
              text="This re-initiation is prefilled with the previous approver route."
              styleClass="w-full"
            ></p-message>

            <div class="reinit-controls">
              <label class="change-route-toggle">
                <input
                  type="checkbox"
                  [checked]="allowApproverChanges()"
                  (change)="toggleApproverChanges($event)"
                />
                <span>Change approvers for this re-initiation</span>
              </label>
              <small>Keep it unchecked to reuse the same 3 approvers.</small>
            </div>
          }

          @if (approvers().length < 3) {
            <p-message
              severity="warn"
              [text]="'Only ' + approvers().length + ' active approver(s) available. At least 3 are required to initiate workflow.'"
              styleClass="w-full"
            ></p-message>
          }

          <div class="workflow-preview">
            <div class="preview-title">Current Route</div>
            <div class="preview-steps">
              <div class="preview-pill" [class.unselected]="!selectedApproverName('level1ApproverId')">
                <span class="preview-level">L1</span>
                <span>{{ selectedApproverName('level1ApproverId') || 'Select Level 1 Approver' }}</span>
              </div>
              <div class="preview-pill" [class.unselected]="!selectedApproverName('level2ApproverId')">
                <span class="preview-level">L2</span>
                <span>{{ selectedApproverName('level2ApproverId') || 'Select Level 2 Approver' }}</span>
              </div>
              <div class="preview-pill" [class.unselected]="!selectedApproverName('level3ApproverId')">
                <span class="preview-level">L3</span>
                <span>{{ selectedApproverName('level3ApproverId') || 'Select Level 3 Approver' }}</span>
              </div>
            </div>
          </div>

          <div class="level-stack">
            <div class="level-section">
              <div class="level-header">
                <span class="level-badge level-1">1</span>
                <div>
                  <h4>Level 1 Approver</h4>
                  <p>Initial review and first decision checkpoint.</p>
                </div>
              </div>
              <div class="level-form">
                <div class="form-field">
                  <label for="level1Approver">Approver <span class="required">*</span></label>
                  <p-dropdown
                    id="level1Approver"
                    formControlName="level1ApproverId"
                    [options]="availableApproversLevel1()"
                    optionLabel="fullName"
                    optionValue="id"
                    placeholder="Select Level 1 Approver"
                  [disabled]="isApproverSelectionLocked()"
                  [filter]="true"
                  filterBy="fullName,email"
                  [showClear]="true"
                  [appendTo]="'body'"
                  [autoZIndex]="true"
                  [baseZIndex]="12000"
                  scrollHeight="260px"
                  styleClass="w-full"
                >
                    <ng-template let-approver pTemplate="item">
                      <div class="approver-option">
                        <span class="approver-name">{{ approver.fullName }}</span>
                        <span class="approver-email">{{ approver.email }}</span>
                      </div>
                    </ng-template>
                  </p-dropdown>
                  @if (form.get('level1ApproverId')?.invalid && form.get('level1ApproverId')?.touched) {
                    <small class="p-error">Level 1 approver is required.</small>
                  }
                </div>
                <div class="form-field deadline-field">
                  <label for="level1Deadline">Deadline</label>
                  <p-datepicker
                    id="level1Deadline"
                    formControlName="level1Deadline"
                    [minDate]="minDate"
                    [showIcon]="true"
                    [showButtonBar]="true"
                    dateFormat="dd/mm/yy"
                    placeholder="Optional"
                    styleClass="w-full"
                    pTooltip="Optional deadline for this approval level"
                  ></p-datepicker>
                  <small class="field-hint">Optional. Must be in the future.</small>
                </div>
              </div>
            </div>

            <div class="level-section">
              <div class="level-header">
                <span class="level-badge level-2">2</span>
                <div>
                  <h4>Level 2 Approver</h4>
                  <p>Secondary review after Level 1 approval.</p>
                </div>
              </div>
              <div class="level-form">
                <div class="form-field">
                  <label for="level2Approver">Approver <span class="required">*</span></label>
                  <p-dropdown
                    id="level2Approver"
                    formControlName="level2ApproverId"
                    [options]="availableApproversLevel2()"
                    optionLabel="fullName"
                    optionValue="id"
                    placeholder="Select Level 2 Approver"
                  [disabled]="isApproverSelectionLocked()"
                  [filter]="true"
                  filterBy="fullName,email"
                  [showClear]="true"
                  [appendTo]="'body'"
                  [autoZIndex]="true"
                  [baseZIndex]="12000"
                  scrollHeight="260px"
                  styleClass="w-full"
                >
                    <ng-template let-approver pTemplate="item">
                      <div class="approver-option">
                        <span class="approver-name">{{ approver.fullName }}</span>
                        <span class="approver-email">{{ approver.email }}</span>
                      </div>
                    </ng-template>
                  </p-dropdown>
                  @if (form.get('level2ApproverId')?.invalid && form.get('level2ApproverId')?.touched) {
                    <small class="p-error">Level 2 approver is required.</small>
                  }
                </div>
                <div class="form-field deadline-field">
                  <label for="level2Deadline">Deadline</label>
                  <p-datepicker
                    id="level2Deadline"
                    formControlName="level2Deadline"
                    [minDate]="getLevel2MinDate()"
                    [showIcon]="true"
                    [showButtonBar]="true"
                    dateFormat="dd/mm/yy"
                    placeholder="Optional"
                    styleClass="w-full"
                    pTooltip="Optional deadline for this approval level"
                  ></p-datepicker>
                  <small class="field-hint">Optional. Must be on/after Level 1 deadline.</small>
                </div>
              </div>
            </div>

            <div class="level-section">
              <div class="level-header">
                <span class="level-badge level-3">3</span>
                <div>
                  <h4>Level 3 Approver</h4>
                  <p>Final decision level before completion.</p>
                </div>
              </div>
              <div class="level-form">
                <div class="form-field">
                  <label for="level3Approver">Approver <span class="required">*</span></label>
                  <p-dropdown
                    id="level3Approver"
                    formControlName="level3ApproverId"
                    [options]="availableApproversLevel3()"
                    optionLabel="fullName"
                    optionValue="id"
                    placeholder="Select Level 3 Approver"
                  [disabled]="isApproverSelectionLocked()"
                  [filter]="true"
                  filterBy="fullName,email"
                  [showClear]="true"
                  [appendTo]="'body'"
                  [autoZIndex]="true"
                  [baseZIndex]="12000"
                  scrollHeight="260px"
                  styleClass="w-full"
                >
                    <ng-template let-approver pTemplate="item">
                      <div class="approver-option">
                        <span class="approver-name">{{ approver.fullName }}</span>
                        <span class="approver-email">{{ approver.email }}</span>
                      </div>
                    </ng-template>
                  </p-dropdown>
                  @if (form.get('level3ApproverId')?.invalid && form.get('level3ApproverId')?.touched) {
                    <small class="p-error">Level 3 approver is required.</small>
                  }
                </div>
                <div class="form-field deadline-field">
                  <label for="level3Deadline">Deadline</label>
                  <p-datepicker
                    id="level3Deadline"
                    formControlName="level3Deadline"
                    [minDate]="getLevel3MinDate()"
                    [showIcon]="true"
                    [showButtonBar]="true"
                    dateFormat="dd/mm/yy"
                    placeholder="Optional"
                    styleClass="w-full"
                    pTooltip="Optional deadline for this approval level"
                  ></p-datepicker>
                  <small class="field-hint">Optional. Must be on/after Level 2 deadline.</small>
                </div>
              </div>
            </div>
          </div>

          @if (showApproverChangeReason()) {
            <div class="reason-field">
              <label for="approverChangeReason">Reason for changing approvers <span class="required">*</span></label>
              <textarea
                pInputTextarea
                id="approverChangeReason"
                formControlName="approverChangeReason"
                [rows]="3"
                [autoResize]="true"
                placeholder="Explain why the approver route changed (minimum 10 characters)."
                class="w-full"
              ></textarea>
              @if (form.get('approverChangeReason')?.invalid && form.get('approverChangeReason')?.touched) {
                <small class="p-error">Reason is required and must be at least 10 characters.</small>
              }
            </div>
          }

          @if (errorMessage()) {
            <p-message
              severity="error"
              [text]="errorMessage()!"
              styleClass="mt-4 w-full"
            ></p-message>
          }
        </form>
      }

      <ng-template pTemplate="footer">
        <div class="dialog-footer">
          <div class="footer-note">
            @if (approvers().length >= 3 && !isReinitiation) {
              <span>Use 3 unique approvers to initiate this workflow.</span>
            } @else if (approvers().length >= 3) {
              <span>Route is prefilled from the previous workflow. Change approvers only if needed.</span>
            } @else {
              <span>At least 3 active approvers are required.</span>
            }
          </div>
          <div class="footer-actions">
            <button
              pButton
              type="button"
              label="Cancel"
              class="p-button-text"
              [disabled]="isSubmitting()"
              (click)="onCancel()"
            ></button>
            <button
              pButton
              type="submit"
              [label]="isReinitiation ? 'Re-initiate Workflow' : 'Initiate Workflow'"
              [icon]="isReinitiation ? 'pi pi-refresh' : 'pi pi-play'"
              data-testid="initiate-approval-submit"
              [loading]="isSubmitting()"
              [disabled]="form.invalid || isSubmitting() || isLoadingApprovers() || approvers().length < 3"
              (click)="onSubmit()"
            ></button>
          </div>
        </div>
      </ng-template>
    </p-dialog>
  `,
  styles: [`
    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 2rem;
      gap: 1rem;
    }

    .loading-container p {
      color: var(--bayan-muted-foreground, #64748B);
    }

    .dialog-form {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .reinit-controls {
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
      padding: 0.75rem 0.875rem;
      border: 1px dashed var(--bayan-border, #E2E8F0);
      border-radius: 0.75rem;
      background: var(--bayan-accent, #F1F5F9);
    }

    .change-route-toggle {
      display: flex;
      align-items: center;
      gap: 0.6rem;
      font-weight: 500;
      color: var(--bayan-foreground, #0F172A);
      cursor: pointer;
    }

    .change-route-toggle input {
      width: 16px;
      height: 16px;
      cursor: pointer;
    }

    .reinit-controls small {
      color: var(--bayan-muted-foreground, #64748B);
      font-size: 0.78rem;
    }

    .workflow-preview {
      border: 1px solid var(--bayan-border, #E2E8F0);
      background: var(--bayan-card, #ffffff);
      border-radius: 0.75rem;
      padding: 0.875rem;
    }

    .preview-title {
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--bayan-muted-foreground, #64748B);
      margin-bottom: 0.625rem;
      font-weight: 600;
    }

    .preview-steps {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 0.5rem;
    }

    .preview-pill {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.5rem 0.625rem;
      border-radius: 0.625rem;
      border: 1px solid var(--bayan-border, #E2E8F0);
      background: var(--bayan-accent, #F1F5F9);
      font-size: 0.85rem;
      color: var(--bayan-foreground, #0F172A);
      min-width: 0;
    }

    .preview-pill.unselected {
      color: var(--bayan-muted-foreground, #64748B);
      background: var(--bayan-accent, #F1F5F9);
    }

    .preview-pill span:last-child {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .preview-level {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 28px;
      height: 22px;
      border-radius: 999px;
      background: var(--bayan-primary, #4F46E5);
      color: #fff;
      font-weight: 700;
      font-size: 0.72rem;
      line-height: 1;
      padding: 0 0.4rem;
      flex-shrink: 0;
    }

    .level-stack {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .level-section {
      border: 1px solid var(--bayan-border, #E2E8F0);
      background: var(--bayan-card, #ffffff);
      border-radius: 0.75rem;
      padding: 0.875rem;
    }

    .level-header {
      display: flex;
      align-items: flex-start;
      gap: 0.75rem;
      margin-bottom: 0.875rem;
    }

    .level-badge {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 28px;
      border-radius: 50%;
      font-weight: 600;
      font-size: 0.9rem;
      color: white;
    }

    .level-badge.level-1 {
      background-color: var(--bayan-primary, #4F46E5);
    }

    .level-badge.level-2 {
      background-color: var(--bayan-success, #16A34A);
    }

    .level-badge.level-3 {
      background-color: var(--bayan-info, #2563EB);
    }

    .level-header h4 {
      margin: 0;
      color: var(--bayan-foreground, #0F172A);
      font-size: 1rem;
    }

    .level-header p {
      margin: 0.2rem 0 0;
      color: var(--bayan-muted-foreground, #64748B);
      font-size: 0.85rem;
    }

    .level-form {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(210px, 240px);
      gap: 1rem;
      padding-left: 2.7rem;
    }

    .form-field {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .form-field label {
      font-weight: 500;
      color: var(--bayan-foreground, #0F172A);
      font-size: 0.9rem;
    }

    .required {
      color: var(--bayan-danger, #DC2626);
    }

    .field-hint {
      font-size: 0.78rem;
      color: var(--bayan-muted-foreground, #64748B);
      margin-top: -0.1rem;
    }

    .reason-field {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .reason-field label {
      font-weight: 500;
      color: var(--bayan-foreground, #0F172A);
      font-size: 0.9rem;
    }

    .approver-option {
      display: flex;
      flex-direction: column;
      gap: 0.15rem;
      padding: 0.125rem 0;
    }

    .approver-name {
      font-weight: 500;
      color: var(--bayan-foreground, #0F172A);
    }

    .approver-email {
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #64748B);
    }

    .dialog-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 0.75rem;
      width: 100%;
    }

    .footer-note {
      font-size: 0.8rem;
      color: var(--bayan-muted-foreground, #64748B);
    }

    .footer-actions {
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
    }

    .w-full {
      width: 100%;
    }

    .mt-4 {
      margin-top: 1rem;
    }

    :host ::ng-deep .initiate-approval-dialog .p-dropdown:focus,
    :host ::ng-deep .initiate-approval-dialog .p-dropdown.p-focus {
      border-color: var(--bayan-primary, #4F46E5);
      box-shadow: 0 0 0 3px var(--bayan-primary-ring, rgba(79,70,229,0.15));
    }

    :host ::ng-deep .initiate-approval-dialog .p-inputtextarea:focus {
      border-color: var(--bayan-primary, #4F46E5);
      box-shadow: 0 0 0 3px var(--bayan-primary-ring, rgba(79,70,229,0.15));
    }

    @media (max-width: 960px) {
      .preview-steps {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 700px) {
      .level-form {
        grid-template-columns: 1fr;
        padding-left: 0;
      }

      .deadline-field {
        margin-top: 0.5rem;
      }

      .dialog-footer {
        flex-direction: column;
        align-items: stretch;
      }

      .footer-actions {
        width: 100%;
      }

      :host ::ng-deep .footer-actions .p-button {
        flex: 1;
      }
    }
  `]
})
export class InitiateApprovalDialogComponent implements OnInit, OnChanges, OnDestroy {
  @Input() visible = false;
  @Input() tenderId!: string | number;
  @Input() isReinitiation = false;
  @Input() existingWorkflow: ApprovalWorkflow | null = null;

  @Output() visibleChange = new EventEmitter<boolean>();
  @Output() initiated = new EventEmitter<ApprovalWorkflow>();

  private readonly approvalService = inject(ApprovalService);
  private readonly fb = inject(FormBuilder);
  private readonly destroy$ = new Subject<void>();

  // Data
  approvers = signal<ApproverOption[]>([]);

  // State
  isLoadingApprovers = signal(false);
  isSubmitting = signal(false);
  errorMessage = signal<string | null>(null);
  allowApproverChanges = signal(false);
  private readonly initialApproverIds = signal<(string | number | null)[]>([null, null, null]);

  // Form
  form: FormGroup;
  minDate = new Date();

  // Computed available approvers (filter out already selected)
  availableApproversLevel1 = signal<ApproverOption[]>([]);
  availableApproversLevel2 = signal<ApproverOption[]>([]);
  availableApproversLevel3 = signal<ApproverOption[]>([]);

  constructor() {
    this.form = this.fb.group({
      level1ApproverId: [null, Validators.required],
      level1Deadline: [null],
      level2ApproverId: [null, Validators.required],
      level2Deadline: [null],
      level3ApproverId: [null, Validators.required],
      level3Deadline: [null],
      approverChangeReason: [null]
    });

    // Update available approvers when selection changes
    this.form.valueChanges.subscribe(() => {
      this.updateAvailableApprovers();
      this.syncApproverChangeReasonValidation();
    });
  }

  ngOnInit(): void {
    this.loadApprovers();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if ((changes['visible'] || changes['isReinitiation'] || changes['existingWorkflow']) && this.visible) {
      this.initializeFormState();
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadApprovers(): void {
    this.isLoadingApprovers.set(true);

    this.approvalService.getApprovers()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (approvers) => {
          this.approvers.set(approvers);
          this.updateAvailableApprovers();
          this.initializeFormState();
          this.isLoadingApprovers.set(false);
        },
        error: (error) => {
          this.isLoadingApprovers.set(false);
          this.errorMessage.set(error.message || 'Failed to load approvers');
        }
      });
  }

  private initializeFormState(): void {
    if (!this.visible) return;

    if (this.isReinitiation && this.existingWorkflow?.levels?.length === 3) {
      this.applyPreviousWorkflowDefaults(this.existingWorkflow);
      this.allowApproverChanges.set(false);
    } else {
      this.resetForm();
      this.allowApproverChanges.set(false);
      this.initialApproverIds.set([null, null, null]);
      this.updateAvailableApprovers();
      this.syncApproverChangeReasonValidation();
    }
  }

  private applyPreviousWorkflowDefaults(workflow: ApprovalWorkflow): void {
    this.ensureApproversContainPrevious(workflow);

    const orderedLevels = [...workflow.levels].sort((a, b) => a.level - b.level);
    const [level1, level2, level3] = orderedLevels;
    const previousIds: (string | number | null)[] = [
      this.normalizeApproverId(level1?.approver?.id ?? null),
      this.normalizeApproverId(level2?.approver?.id ?? null),
      this.normalizeApproverId(level3?.approver?.id ?? null)
    ];

    this.initialApproverIds.set(previousIds);

    this.form.patchValue({
      level1ApproverId: previousIds[0],
      level1Deadline: this.toValidDeadlineOrNull(level1?.deadline),
      level2ApproverId: previousIds[1],
      level2Deadline: this.toValidDeadlineOrNull(level2?.deadline),
      level3ApproverId: previousIds[2],
      level3Deadline: this.toValidDeadlineOrNull(level3?.deadline),
      approverChangeReason: null
    }, { emitEvent: false });

    this.updateAvailableApprovers();
    this.syncApproverChangeReasonValidation();
  }

  private ensureApproversContainPrevious(workflow: ApprovalWorkflow): void {
    const existing = this.approvers();
    const merged = [...existing];
    let changed = false;

    for (const level of workflow.levels) {
      const levelApprover = level.approver;
      const exists = merged.some(a => this.toIdKey(a.id) === this.toIdKey(levelApprover.id));
      if (exists) continue;

      changed = true;
      merged.push({
        id: levelApprover.id,
        firstName: levelApprover.firstName,
        lastName: levelApprover.lastName,
        email: levelApprover.email,
        fullName: `${levelApprover.firstName} ${levelApprover.lastName} (Inactive)`
      });
    }

    if (changed) {
      this.approvers.set(merged);
    }
  }

  private toValidDeadlineOrNull(value: Date | string | undefined): Date | null {
    if (!value) return null;
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return null;
    return parsed > new Date() ? parsed : null;
  }

  private updateAvailableApprovers(): void {
    const allApprovers = this.approvers();
    const selected1 = this.form.get('level1ApproverId')?.value;
    const selected2 = this.form.get('level2ApproverId')?.value;
    const selected1Key = this.toIdKey(selected1);
    const selected2Key = this.toIdKey(selected2);

    // Level 1: All approvers available
    this.availableApproversLevel1.set(allApprovers);

    // Level 2: Exclude level 1 selection
    this.availableApproversLevel2.set(
      allApprovers.filter(a => this.toIdKey(a.id) !== selected1Key)
    );

    // Level 3: Exclude level 1 and 2 selections
    this.availableApproversLevel3.set(
      allApprovers.filter(a =>
        this.toIdKey(a.id) !== selected1Key &&
        this.toIdKey(a.id) !== selected2Key
      )
    );
  }

  toggleApproverChanges(event: Event): void {
    const checked = (event.target as HTMLInputElement).checked;
    this.allowApproverChanges.set(checked);

    if (!checked && this.isReinitiation && this.existingWorkflow) {
      this.applyPreviousWorkflowDefaults(this.existingWorkflow);
      return;
    }

    this.syncApproverChangeReasonValidation();
  }

  isApproverSelectionLocked(): boolean {
    return this.isReinitiation && this.previousRouteReady() && !this.allowApproverChanges();
  }

  previousRouteReady(): boolean {
    return this.initialApproverIds().every(id => id !== null);
  }

  private approverSelectionChanged(): boolean {
    if (!this.isReinitiation || !this.previousRouteReady()) return false;

    const currentIds = [
      this.form.get('level1ApproverId')?.value ?? null,
      this.form.get('level2ApproverId')?.value ?? null,
      this.form.get('level3ApproverId')?.value ?? null
    ];

    const initialIds = this.initialApproverIds();
    return currentIds.some((id, index) => this.toIdKey(id) !== this.toIdKey(initialIds[index]));
  }

  showApproverChangeReason(): boolean {
    return this.isReinitiation && this.approverSelectionChanged();
  }

  private syncApproverChangeReasonValidation(): void {
    const reasonControl = this.form.get('approverChangeReason');
    if (!reasonControl) return;

    if (this.showApproverChangeReason()) {
      reasonControl.setValidators([Validators.required, Validators.minLength(10)]);
    } else {
      reasonControl.clearValidators();
      reasonControl.setValue(null, { emitEvent: false });
    }

    reasonControl.updateValueAndValidity({ emitEvent: false });
  }

  getLevel2MinDate(): Date {
    const level1Deadline = this.form.get('level1Deadline')?.value;
    if (level1Deadline) {
      const nextDay = new Date(level1Deadline);
      nextDay.setDate(nextDay.getDate() + 1);
      return nextDay;
    }
    return this.minDate;
  }

  getLevel3MinDate(): Date {
    const level2Deadline = this.form.get('level2Deadline')?.value;
    if (level2Deadline) {
      const nextDay = new Date(level2Deadline);
      nextDay.setDate(nextDay.getDate() + 1);
      return nextDay;
    }
    return this.getLevel2MinDate();
  }

  selectedApproverName(controlName: 'level1ApproverId' | 'level2ApproverId' | 'level3ApproverId'): string | null {
    const selectedId = this.form.get(controlName)?.value;
    if (!selectedId) return null;

    const selectedKey = this.toIdKey(selectedId);
    const approver = this.approvers().find(a => this.toIdKey(a.id) === selectedKey);
    if (approver?.fullName) return approver.fullName;

    if (!this.isReinitiation || !this.existingWorkflow) return null;

    const levelNumber = controlName === 'level1ApproverId'
      ? 1
      : controlName === 'level2ApproverId'
        ? 2
        : 3;

    const previousLevel = this.existingWorkflow.levels.find(l => l.level === levelNumber);
    if (!previousLevel) return null;

    return `${previousLevel.approver.firstName} ${previousLevel.approver.lastName}`.trim();
  }

  private toIdKey(value: unknown): string {
    return String(value ?? '').trim().toLowerCase();
  }

  private normalizeApproverId(rawId: string | number | null): string | number | null {
    if (rawId == null) return null;
    const key = this.toIdKey(rawId);
    const matched = this.approvers().find(a => this.toIdKey(a.id) === key);
    return matched?.id ?? rawId;
  }

  onSubmit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.isSubmitting.set(true);
    this.errorMessage.set(null);

    const formValue = this.form.value;
    const dto: InitiateApprovalDto = {
      level1ApproverId: formValue.level1ApproverId,
      level1Deadline: formValue.level1Deadline?.toISOString(),
      level2ApproverId: formValue.level2ApproverId,
      level2Deadline: formValue.level2Deadline?.toISOString(),
      level3ApproverId: formValue.level3ApproverId,
      level3Deadline: formValue.level3Deadline?.toISOString(),
      approverChangeReason: this.showApproverChangeReason()
        ? formValue.approverChangeReason?.trim()
        : undefined
    };

    this.approvalService.initiateApproval(this.tenderId, dto)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (workflow) => {
          this.isSubmitting.set(false);
          this.initiated.emit(workflow);
          this.close();
        },
        error: (error) => {
          this.isSubmitting.set(false);
          this.errorMessage.set(error.message || 'Failed to initiate approval workflow');
        }
      });
  }

  onCancel(): void {
    this.close();
  }

  onDialogHide(): void {
    this.visibleChange.emit(false);
    this.resetForm();
  }

  private close(): void {
    this.visible = false;
    this.visibleChange.emit(false);
    this.resetForm();
  }

  private resetForm(): void {
    this.form.reset({
      level1ApproverId: null,
      level1Deadline: null,
      level2ApproverId: null,
      level2Deadline: null,
      level3ApproverId: null,
      level3Deadline: null,
      approverChangeReason: null
    }, { emitEvent: false });
    this.allowApproverChanges.set(false);
    this.updateAvailableApprovers();
    this.syncApproverChangeReasonValidation();
    this.errorMessage.set(null);
  }
}
