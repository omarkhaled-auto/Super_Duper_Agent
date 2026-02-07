import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit,
  OnDestroy,
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
import { DividerModule } from 'primeng/divider';
import { MessageModule } from 'primeng/message';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { TooltipModule } from 'primeng/tooltip';

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
    DividerModule,
    MessageModule,
    ProgressSpinnerModule,
    TooltipModule
  ],
  template: `
    <p-dialog
      header="Initiate Approval Workflow"
      [(visible)]="visible"
      [modal]="true"
      [style]="{ width: '600px' }"
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
        <form [formGroup]="form" (ngSubmit)="onSubmit()">
          <p-message
            severity="info"
            text="Select three approvers for the workflow. Each approver will review and decide in sequence."
            styleClass="mb-4 w-full"
          ></p-message>

          <!-- Level 1 -->
          <div class="level-section">
            <div class="level-header">
              <span class="level-badge level-1">1</span>
              <h4>Level 1 Approver</h4>
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
                  [filter]="true"
                  filterBy="fullName,email"
                  [showClear]="true"
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
                  <small class="p-error">Level 1 approver is required</small>
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
                  placeholder="Select deadline"
                  styleClass="w-full"
                  pTooltip="Optional deadline for this approval level"
                ></p-datepicker>
              </div>
            </div>
          </div>

          <p-divider></p-divider>

          <!-- Level 2 -->
          <div class="level-section">
            <div class="level-header">
              <span class="level-badge level-2">2</span>
              <h4>Level 2 Approver</h4>
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
                  [filter]="true"
                  filterBy="fullName,email"
                  [showClear]="true"
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
                  <small class="p-error">Level 2 approver is required</small>
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
                  placeholder="Select deadline"
                  styleClass="w-full"
                  pTooltip="Optional deadline for this approval level"
                ></p-datepicker>
              </div>
            </div>
          </div>

          <p-divider></p-divider>

          <!-- Level 3 -->
          <div class="level-section">
            <div class="level-header">
              <span class="level-badge level-3">3</span>
              <h4>Level 3 Approver</h4>
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
                  [filter]="true"
                  filterBy="fullName,email"
                  [showClear]="true"
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
                  <small class="p-error">Level 3 approver is required</small>
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
                  placeholder="Select deadline"
                  styleClass="w-full"
                  pTooltip="Optional deadline for this approval level"
                ></p-datepicker>
              </div>
            </div>
          </div>

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
            label="Initiate Workflow"
            icon="pi pi-play"
            data-testid="initiate-approval-submit"
            [loading]="isSubmitting()"
            [disabled]="form.invalid || isSubmitting() || isLoadingApprovers()"
            (click)="onSubmit()"
          ></button>
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
      color: #666;
    }

    .level-section {
      padding: 0.5rem 0;
    }

    .level-header {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 1rem;
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
      background-color: #1976D2;
    }

    .level-badge.level-2 {
      background-color: #388E3C;
    }

    .level-badge.level-3 {
      background-color: #7B1FA2;
    }

    .level-header h4 {
      margin: 0;
      color: #333;
      font-size: 1rem;
    }

    .level-form {
      display: grid;
      grid-template-columns: 1fr 200px;
      gap: 1rem;
      padding-left: 2.75rem;
    }

    .form-field {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .form-field label {
      font-weight: 500;
      color: #333;
      font-size: 0.9rem;
    }

    .required {
      color: #f44336;
    }

    .approver-option {
      display: flex;
      flex-direction: column;
    }

    .approver-name {
      font-weight: 500;
      color: #333;
    }

    .approver-email {
      font-size: 0.85rem;
      color: #666;
    }

    .dialog-footer {
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
    }

    .w-full {
      width: 100%;
    }

    .mb-4 {
      margin-bottom: 1rem;
    }

    .mt-4 {
      margin-top: 1rem;
    }

    @media (max-width: 600px) {
      .level-form {
        grid-template-columns: 1fr;
        padding-left: 0;
      }

      .deadline-field {
        margin-top: 0.5rem;
      }
    }
  `]
})
export class InitiateApprovalDialogComponent implements OnInit, OnDestroy {
  @Input() visible = false;
  @Input() tenderId!: number;

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
      level3Deadline: [null]
    });

    // Update available approvers when selection changes
    this.form.valueChanges.subscribe(() => {
      this.updateAvailableApprovers();
    });
  }

  ngOnInit(): void {
    this.loadApprovers();
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
          this.isLoadingApprovers.set(false);
        },
        error: (error) => {
          this.isLoadingApprovers.set(false);
          this.errorMessage.set(error.message || 'Failed to load approvers');
        }
      });
  }

  private updateAvailableApprovers(): void {
    const allApprovers = this.approvers();
    const selected1 = this.form.get('level1ApproverId')?.value;
    const selected2 = this.form.get('level2ApproverId')?.value;
    const selected3 = this.form.get('level3ApproverId')?.value;

    // Level 1: All approvers available
    this.availableApproversLevel1.set(allApprovers);

    // Level 2: Exclude level 1 selection
    this.availableApproversLevel2.set(
      allApprovers.filter(a => a.id !== selected1)
    );

    // Level 3: Exclude level 1 and 2 selections
    this.availableApproversLevel3.set(
      allApprovers.filter(a => a.id !== selected1 && a.id !== selected2)
    );
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
      level3Deadline: formValue.level3Deadline?.toISOString()
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
    this.form.reset();
    this.errorMessage.set(null);
  }
}
