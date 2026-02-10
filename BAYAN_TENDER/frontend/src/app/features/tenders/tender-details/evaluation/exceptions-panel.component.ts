import {
  Component,
  Input,
  OnInit,
  OnDestroy,
  inject,
  signal
} from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';

// PrimeNG
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TableModule } from 'primeng/table';
import { DropdownModule } from 'primeng/dropdown';
import { InputTextModule } from 'primeng/inputtext';
import { InputTextarea } from 'primeng/inputtextarea';
import { InputNumberModule } from 'primeng/inputnumber';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';
import { TagModule } from 'primeng/tag';
import { DividerModule } from 'primeng/divider';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { PanelModule } from 'primeng/panel';
import { MessageService, ConfirmationService } from 'primeng/api';

// Services and Models
import { EvaluationService } from '../../../../core/services/evaluation.service';
import {
  BidException,
  CreateExceptionDto,
  ExceptionType,
  RiskLevel,
  BidderForScoring,
  EXCEPTION_TYPE_OPTIONS,
  RISK_LEVEL_OPTIONS
} from '../../../../core/models/evaluation.model';

interface BidderOption {
  label: string;
  value: number;
}

@Component({
  selector: 'app-exceptions-panel',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    ButtonModule,
    TableModule,
    DropdownModule,
    InputTextModule,
    InputTextarea,
    InputNumberModule,
    ToastModule,
    TooltipModule,
    TagModule,
    DividerModule,
    ProgressSpinnerModule,
    ConfirmDialogModule,
    PanelModule
  ],
  providers: [MessageService, ConfirmationService, DecimalPipe],
  template: `
    <p-toast></p-toast>
    <p-confirmDialog></p-confirmDialog>

    <div class="exceptions-panel-container" data-testid="exceptions-panel">
      <!-- Add Exception Form -->
      <p-panel header="Log New Exception" [toggleable]="true" [collapsed]="!showForm">
        <div class="exception-form">
          <div class="form-row">
            <div class="form-field">
              <label for="bidder">Bidder *</label>
              <p-dropdown
                id="bidder"
                [options]="bidderOptions()"
                [(ngModel)]="formData.bidderId"
                optionLabel="label"
                optionValue="value"
                placeholder="Select bidder"
                styleClass="w-full"
                [filter]="true"
              ></p-dropdown>
            </div>

            <div class="form-field">
              <label for="type">Exception Type *</label>
              <p-dropdown
                id="type"
                [options]="exceptionTypeOptions"
                [(ngModel)]="formData.type"
                optionLabel="label"
                optionValue="value"
                placeholder="Select type"
                styleClass="w-full"
              ></p-dropdown>
            </div>

            <div class="form-field">
              <label for="riskLevel">Risk Level *</label>
              <p-dropdown
                id="riskLevel"
                [options]="riskLevelOptions"
                [(ngModel)]="formData.riskLevel"
                optionLabel="label"
                optionValue="value"
                placeholder="Select risk level"
                styleClass="w-full"
              >
                <ng-template let-option pTemplate="item">
                  <div class="risk-option">
                    <p-tag [value]="option.label" [severity]="option.severity"></p-tag>
                  </div>
                </ng-template>
                <ng-template let-option pTemplate="selectedItem">
                  <p-tag [value]="option.label" [severity]="option.severity"></p-tag>
                </ng-template>
              </p-dropdown>
            </div>
          </div>

          <div class="form-row">
            <div class="form-field full-width">
              <label for="description">Description *</label>
              <textarea
                pInputTextarea
                id="description"
                [(ngModel)]="formData.description"
                [rows]="3"
                placeholder="Describe the exception or deviation from tender requirements..."
                styleClass="w-full"
              ></textarea>
            </div>
          </div>

          <div class="form-row">
            <div class="form-field">
              <label for="costImpact">Cost Impact (SAR)</label>
              <p-inputNumber
                id="costImpact"
                [(ngModel)]="formData.costImpact"
                mode="currency"
                currency="SAR"
                locale="en-US"
                [minFractionDigits]="0"
                placeholder="e.g., 50000"
                styleClass="w-full"
              ></p-inputNumber>
            </div>

            <div class="form-field">
              <label for="timeImpact">Time Impact</label>
              <input
                pInputText
                id="timeImpact"
                [(ngModel)]="formData.timeImpact"
                placeholder="e.g., +2 weeks, -5 days"
                styleClass="w-full"
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-field full-width">
              <label for="mitigation">Mitigation / Notes</label>
              <textarea
                pInputTextarea
                id="mitigation"
                [(ngModel)]="formData.mitigation"
                [rows]="2"
                placeholder="Describe any proposed mitigation measures or additional notes..."
                styleClass="w-full"
              ></textarea>
            </div>
          </div>

          <div class="form-actions">
            <button
              pButton
              label="Clear"
              icon="pi pi-times"
              class="p-button-text"
              (click)="clearForm()"
            ></button>
            <button
              pButton
              label="Add Exception"
              icon="pi pi-plus"
              class="p-button-warning"
              [loading]="isSaving()"
              [disabled]="!isFormValid()"
              (click)="addException()"
            ></button>
          </div>
        </div>
      </p-panel>

      <!-- Exceptions List -->
      <p-card header="Logged Exceptions" styleClass="exceptions-list-card">
        @if (isLoading()) {
          <div class="loading-container">
            <p-progressSpinner
              [style]="{ width: '40px', height: '40px' }"
              strokeWidth="4"
            ></p-progressSpinner>
            <p>Loading exceptions...</p>
          </div>
        } @else if (exceptions().length > 0) {
          <p-table
            [value]="exceptions()"
            styleClass="p-datatable-sm p-datatable-striped"
            [paginator]="exceptions().length > 10"
            [rows]="10"
          >
            <ng-template pTemplate="header">
              <tr>
                <th style="width: 150px">Bidder</th>
                <th style="width: 100px">Type</th>
                <th>Description</th>
                <th style="width: 100px">Cost Impact</th>
                <th style="width: 100px">Time Impact</th>
                <th style="width: 80px">Risk</th>
                <th style="width: 80px">Actions</th>
              </tr>
            </ng-template>
            <ng-template pTemplate="body" let-exception>
              <tr>
                <td>
                  <span class="bidder-name">{{ exception.bidderName }}</span>
                </td>
                <td>
                  <p-tag
                    [value]="getTypeLabel(exception.type)"
                    [severity]="getTypeSeverity(exception.type)"
                  ></p-tag>
                </td>
                <td>
                  <div class="description-cell">
                    <span class="description-text">{{ exception.description }}</span>
                    @if (exception.mitigation) {
                      <div class="mitigation-text">
                        <i class="pi pi-info-circle"></i>
                        {{ exception.mitigation }}
                      </div>
                    }
                  </div>
                </td>
                <td class="text-right">
                  @if (exception.costImpact) {
                    <span [class.positive]="exception.costImpact > 0" [class.negative]="exception.costImpact < 0">
                      {{ exception.costImpact | currency:'SAR':'symbol':'1.0-0' }}
                    </span>
                  } @else {
                    <span class="no-value">-</span>
                  }
                </td>
                <td class="text-center">
                  @if (exception.timeImpact) {
                    <span>{{ exception.timeImpact }}</span>
                  } @else {
                    <span class="no-value">-</span>
                  }
                </td>
                <td class="text-center">
                  <p-tag
                    [value]="getRiskLabel(exception.riskLevel)"
                    [severity]="getRiskSeverity(exception.riskLevel)"
                  ></p-tag>
                </td>
                <td class="text-center">
                  <button
                    pButton
                    icon="pi pi-trash"
                    class="p-button-text p-button-sm p-button-danger"
                    pTooltip="Delete Exception"
                    tooltipPosition="top"
                    (click)="confirmDelete(exception)"
                  ></button>
                </td>
              </tr>
            </ng-template>
            <ng-template pTemplate="emptymessage">
              <tr>
                <td colspan="7" class="text-center p-4">
                  <div class="empty-state">
                    <i class="pi pi-list" style="font-size: 2rem; color: var(--bayan-muted-foreground, #71717a); opacity: 0.5;"></i>
                    <p>No exceptions logged yet.</p>
                  </div>
                </td>
              </tr>
            </ng-template>
          </p-table>

          <!-- Summary Stats -->
          <div class="exceptions-summary">
            <div class="summary-item">
              <span class="summary-label">Total Exceptions</span>
              <span class="summary-value">{{ exceptions().length }}</span>
            </div>
            <div class="summary-divider"></div>
            <div class="summary-item">
              <span class="summary-label">High/Critical Risk</span>
              <span class="summary-value risk-high">{{ getHighRiskCount() }}</span>
            </div>
            <div class="summary-divider"></div>
            <div class="summary-item">
              <span class="summary-label">Total Cost Impact</span>
              <span class="summary-value">{{ getTotalCostImpact() | currency:'SAR':'symbol':'1.0-0' }}</span>
            </div>
            <div class="summary-divider"></div>
            <div class="summary-item">
              <span class="summary-label">Bidders Affected</span>
              <span class="summary-value">{{ getAffectedBiddersCount() }}</span>
            </div>
          </div>
        } @else {
          <div class="empty-state">
            <i class="pi pi-check-circle" style="font-size: 2.5rem; color: var(--bayan-success, #22c55e);"></i>
            <h3>No Exceptions</h3>
            <p>No exceptions or deviations have been logged for this tender.</p>
            <button
              pButton
              label="Log First Exception"
              icon="pi pi-plus"
              class="p-button-outlined p-button-warning"
              (click)="showForm = true"
            ></button>
          </div>
        }
      </p-card>
    </div>
  `,
  styles: [`
    .exceptions-panel-container {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 2rem;
      gap: 1rem;
    }

    .loading-container p {
      color: var(--bayan-muted-foreground, #71717a);
      margin: 0;
    }

    /* Form Styles */
    .exception-form {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .form-row {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
    }

    .form-field {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .form-field.full-width {
      grid-column: 1 / -1;
    }

    .form-field label {
      font-weight: 500;
      color: var(--bayan-foreground, #09090b);
      font-size: 0.9rem;
    }

    .form-field textarea {
      width: 100%;
    }

    .risk-option {
      padding: 0.25rem 0;
    }

    .form-actions {
      display: flex;
      justify-content: flex-end;
      gap: 0.75rem;
      margin-top: 0.5rem;
      padding-top: 1rem;
      border-top: 1px solid var(--bayan-border, #e4e4e7);
    }

    /* Table Styles */
    .bidder-name {
      font-weight: 500;
    }

    .description-cell {
      display: flex;
      flex-direction: column;
      gap: 0.375rem;
    }

    .description-text {
      color: var(--bayan-foreground, #09090b);
    }

    .mitigation-text {
      display: flex;
      align-items: flex-start;
      gap: 0.375rem;
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #71717a);
      padding: 0.375rem 0.5rem;
      background: var(--bayan-accent, #f4f4f5);
      border-radius: var(--bayan-radius-sm, 0.375rem);
    }

    .mitigation-text i {
      color: var(--bayan-primary, #18181b);
      margin-top: 0.125rem;
    }

    .text-right {
      text-align: right;
    }

    .text-center {
      text-align: center;
    }

    .positive {
      color: #dc2626;
    }

    .negative {
      color: #16a34a;
    }

    .no-value {
      color: var(--bayan-muted-foreground, #71717a);
    }

    /* Summary Stats */
    .exceptions-summary {
      display: flex;
      align-items: center;
      gap: 1.5rem;
      padding: 1rem;
      background: var(--bayan-accent, #f4f4f5);
      border-radius: var(--bayan-radius, 0.5rem);
      margin-top: 1rem;
      flex-wrap: wrap;
    }

    .summary-item {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }

    .summary-label {
      font-size: 0.8rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .summary-value {
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--bayan-foreground, #09090b);
    }

    .summary-value.risk-high {
      color: #dc2626;
    }

    .summary-divider {
      width: 1px;
      height: 40px;
      background: var(--bayan-border, #e4e4e7);
    }

    /* Empty State */
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 2rem;
      gap: 1rem;
      text-align: center;
    }

    .empty-state h3 {
      margin: 0;
      color: var(--bayan-foreground, #09090b);
    }

    .empty-state p {
      margin: 0;
      color: var(--bayan-muted-foreground, #71717a);
    }

    /* Responsive */
    @media (max-width: 768px) {
      .form-row {
        grid-template-columns: 1fr;
      }

      .exceptions-summary {
        flex-direction: column;
        align-items: stretch;
      }

      .summary-divider {
        display: none;
      }

      .summary-item {
        flex-direction: row;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 0;
        border-bottom: 1px solid var(--bayan-border, #e4e4e7);
      }

      .summary-item:last-child {
        border-bottom: none;
      }
    }
  `]
})
export class ExceptionsPanelComponent implements OnInit, OnDestroy {
  @Input() tenderId!: number;

  private readonly evaluationService = inject(EvaluationService);
  private readonly messageService = inject(MessageService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly decimalPipe = inject(DecimalPipe);
  private readonly destroy$ = new Subject<void>();

  // State signals
  exceptions = signal<BidException[]>([]);
  bidders = signal<BidderForScoring[]>([]);
  isLoading = signal<boolean>(true);
  isSaving = signal<boolean>(false);

  // Form state
  showForm = false;
  formData: Partial<CreateExceptionDto> = this.getEmptyFormData();

  // Options
  exceptionTypeOptions = EXCEPTION_TYPE_OPTIONS;
  riskLevelOptions = RISK_LEVEL_OPTIONS;

  // Computed
  bidderOptions = signal<BidderOption[]>([]);

  ngOnInit(): void {
    this.loadData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadData(): void {
    this.isLoading.set(true);

    // Load exceptions
    this.evaluationService.getExceptions(this.tenderId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (exceptions) => {
          this.exceptions.set(exceptions);
          this.isLoading.set(false);
        },
        error: (error) => {
          this.isLoading.set(false);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: error.message || 'Failed to load exceptions'
          });
        }
      });

    // Load bidders for dropdown
    this.evaluationService.getBiddersForScoring(this.tenderId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (bidders) => {
          this.bidders.set(bidders);
          this.bidderOptions.set(
            bidders.map(b => ({ label: b.bidderName, value: b.bidderId }))
          );
        }
      });
  }

  private getEmptyFormData(): Partial<CreateExceptionDto> {
    return {
      bidderId: undefined,
      type: undefined,
      description: '',
      costImpact: undefined,
      timeImpact: '',
      riskLevel: undefined,
      mitigation: ''
    };
  }

  isFormValid(): boolean {
    return !!(
      this.formData.bidderId &&
      this.formData.type &&
      this.formData.description?.trim() &&
      this.formData.riskLevel
    );
  }

  clearForm(): void {
    this.formData = this.getEmptyFormData();
  }

  addException(): void {
    if (!this.isFormValid()) return;

    this.isSaving.set(true);

    const dto: CreateExceptionDto = {
      tenderId: this.tenderId,
      bidderId: this.formData.bidderId!,
      type: this.formData.type!,
      description: this.formData.description!.trim(),
      costImpact: this.formData.costImpact,
      timeImpact: this.formData.timeImpact?.trim() || undefined,
      riskLevel: this.formData.riskLevel!,
      mitigation: this.formData.mitigation?.trim() || undefined
    };

    this.evaluationService.addException(dto)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (exception) => {
          this.isSaving.set(false);
          this.exceptions.update(list => [...list, exception]);
          this.clearForm();
          this.showForm = false;
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Exception logged successfully'
          });
        },
        error: (error) => {
          this.isSaving.set(false);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: error.message || 'Failed to add exception'
          });
        }
      });
  }

  confirmDelete(exception: BidException): void {
    this.confirmationService.confirm({
      message: `Are you sure you want to delete this exception for ${exception.bidderName}?`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => {
        this.deleteException(exception.id);
      }
    });
  }

  private deleteException(exceptionId: number): void {
    this.evaluationService.deleteException(this.tenderId, exceptionId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.exceptions.update(list => list.filter(e => e.id !== exceptionId));
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Exception deleted successfully'
          });
        },
        error: (error) => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: error.message || 'Failed to delete exception'
          });
        }
      });
  }

  getTypeLabel(type: ExceptionType): string {
    const option = this.exceptionTypeOptions.find(o => o.value === type);
    return option?.label || type;
  }

  getTypeSeverity(type: ExceptionType): 'info' | 'success' | 'warn' {
    switch (type) {
      case 'technical': return 'info';
      case 'commercial': return 'success';
      case 'contractual': return 'warn';
      default: return 'info';
    }
  }

  getRiskLabel(level: RiskLevel): string {
    const option = this.riskLevelOptions.find(o => o.value === level);
    return option?.label || level;
  }

  getRiskSeverity(level: RiskLevel): 'success' | 'info' | 'warn' | 'danger' {
    const option = this.riskLevelOptions.find(o => o.value === level);
    return option?.severity || 'info';
  }

  getHighRiskCount(): number {
    return this.exceptions().filter(e => e.riskLevel === 'high' || e.riskLevel === 'critical').length;
  }

  getTotalCostImpact(): number {
    return this.exceptions().reduce((sum, e) => sum + (e.costImpact || 0), 0);
  }

  getAffectedBiddersCount(): number {
    const uniqueBidders = new Set(this.exceptions().map(e => e.bidderId));
    return uniqueBidders.size;
  }
}
