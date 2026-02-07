import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit,
  OnDestroy,
  inject,
  signal,
  computed
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil, forkJoin } from 'rxjs';

// PrimeNG
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TableModule } from 'primeng/table';
import { MultiSelectModule } from 'primeng/multiselect';
import { DropdownModule } from 'primeng/dropdown';
import { CheckboxModule } from 'primeng/checkbox';
import { DatePickerModule } from 'primeng/datepicker';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';
import { TagModule } from 'primeng/tag';
import { DividerModule } from 'primeng/divider';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageModule } from 'primeng/message';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { MessageService, ConfirmationService } from 'primeng/api';

// Services and Models
import { EvaluationService } from '../../../../core/services/evaluation.service';
import {
  PanelMemberOption,
  EvaluationCriterion,
  EvaluationSetup,
  CreateEvaluationSetupDto,
  ScoringMethod,
  SCORING_METHOD_OPTIONS
} from '../../../../core/models/evaluation.model';

@Component({
  selector: 'app-evaluation-setup',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    ButtonModule,
    TableModule,
    MultiSelectModule,
    DropdownModule,
    CheckboxModule,
    DatePickerModule,
    ToastModule,
    TooltipModule,
    TagModule,
    DividerModule,
    ProgressSpinnerModule,
    MessageModule,
    ConfirmDialogModule
  ],
  providers: [MessageService, ConfirmationService],
  template: `
    <p-toast></p-toast>
    <p-confirmDialog></p-confirmDialog>

    <div class="evaluation-setup-container">
      <!-- Loading State -->
      @if (isLoading()) {
        <div class="loading-container">
          <p-progressSpinner
            [style]="{ width: '50px', height: '50px' }"
            strokeWidth="4"
          ></p-progressSpinner>
          <p>Loading evaluation setup...</p>
        </div>
      } @else if (existingSetup()) {
        <!-- Existing Setup View -->
        <div class="existing-setup">
          <p-message
            severity="info"
            [text]="'Evaluation is ' + existingSetup()!.status + '. Configuration cannot be changed.'"
            styleClass="w-full mb-3"
          ></p-message>

          <p-card header="Current Configuration" styleClass="config-card">
            <div class="config-grid">
              <div class="config-item">
                <label>Scoring Method</label>
                <span>{{ getScoringMethodLabel(existingSetup()!.scoringMethod) }}</span>
              </div>
              <div class="config-item">
                <label>Blind Mode</label>
                <p-tag
                  [value]="existingSetup()!.blindMode ? 'Enabled' : 'Disabled'"
                  [severity]="existingSetup()!.blindMode ? 'success' : 'secondary'"
                ></p-tag>
              </div>
              <div class="config-item">
                <label>Deadline</label>
                <span>{{ existingSetup()!.deadline | date:'medium' }}</span>
              </div>
              <div class="config-item">
                <label>Panel Members</label>
                <span>{{ existingSetup()!.panelMembers.length }} assigned</span>
              </div>
            </div>
          </p-card>

          <p-card header="Panel Members" styleClass="mt-3">
            <p-table [value]="existingSetup()!.panelMembers" styleClass="p-datatable-sm">
              <ng-template pTemplate="header">
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                </tr>
              </ng-template>
              <ng-template pTemplate="body" let-member>
                <tr>
                  <td>
                    {{ member.firstName }} {{ member.lastName }}
                    @if (member.isLead) {
                      <p-tag value="Lead" severity="warn" styleClass="ml-2"></p-tag>
                    }
                  </td>
                  <td>{{ member.email }}</td>
                  <td>{{ member.role }}</td>
                  <td>
                    <p-tag
                      [value]="member.status"
                      [severity]="getMemberStatusSeverity(member.status)"
                    ></p-tag>
                  </td>
                </tr>
              </ng-template>
            </p-table>
          </p-card>
        </div>
      } @else {
        <!-- Setup Form -->
        <div class="setup-form">
          <p-card header="Panel Members Selection" styleClass="section-card">
            <div class="panel-selection">
              <p-multiSelect
                [options]="availablePanelMembers()"
                [(ngModel)]="selectedPanelMemberIds"
                optionLabel="fullName"
                optionValue="id"
                placeholder="Select panel members (2-5 required)"
                [filter]="true"
                filterPlaceholder="Search members..."
                [showClear]="true"
                [maxSelectedLabels]="5"
                selectedItemsLabel="{0} members selected"
                styleClass="w-full"
                (onChange)="onPanelMemberChange()"
              >
                <ng-template let-member pTemplate="item">
                  <div class="member-option">
                    <div class="member-info">
                      <span class="member-name">{{ member.fullName }}</span>
                      <span class="member-dept">{{ member.department }}</span>
                    </div>
                    <span class="member-email">{{ member.email }}</span>
                  </div>
                </ng-template>
              </p-multiSelect>

              @if (panelMemberError()) {
                <small class="p-error">{{ panelMemberError() }}</small>
              }

              <div class="selection-info">
                <i class="pi pi-info-circle"></i>
                <span>Select between 2 and 5 panel members. The first selected member will be designated as the lead.</span>
              </div>
            </div>

            @if (selectedPanelMemberIds.length > 0) {
              <p-divider></p-divider>
              <h4>Selected Members</h4>
              <div class="selected-members">
                @for (memberId of selectedPanelMemberIds; track memberId; let i = $index) {
                  <div class="selected-member">
                    <span class="member-order">{{ i + 1 }}</span>
                    <span class="member-name">{{ getMemberName(memberId) }}</span>
                    @if (i === 0) {
                      <p-tag value="Lead" severity="warn"></p-tag>
                    }
                    <button
                      pButton
                      icon="pi pi-times"
                      class="p-button-text p-button-sm p-button-danger"
                      (click)="removePanelMember(memberId)"
                    ></button>
                  </div>
                }
              </div>
            }
          </p-card>

          <p-card header="Evaluation Criteria (Read-Only)" styleClass="section-card mt-3">
            <p-table [value]="criteria()" styleClass="p-datatable-sm p-datatable-striped">
              <ng-template pTemplate="header">
                <tr>
                  <th style="width: 50px">#</th>
                  <th>Criterion Name</th>
                  <th style="width: 100px">Weight (%)</th>
                  <th style="width: 100px">Max Score</th>
                  <th>Description</th>
                </tr>
              </ng-template>
              <ng-template pTemplate="body" let-criterion let-i="rowIndex">
                <tr>
                  <td>{{ i + 1 }}</td>
                  <td>
                    <strong>{{ criterion.name }}</strong>
                    @if (criterion.category === 'technical') {
                      <p-tag value="Technical" severity="info" styleClass="ml-2"></p-tag>
                    } @else {
                      <p-tag value="Commercial" severity="success" styleClass="ml-2"></p-tag>
                    }
                  </td>
                  <td class="text-center">{{ criterion.weight }}%</td>
                  <td class="text-center">{{ criterion.maxScore }}</td>
                  <td>{{ criterion.description }}</td>
                </tr>
              </ng-template>
              <ng-template pTemplate="footer">
                <tr>
                  <td colspan="2" class="text-right"><strong>Total Weight:</strong></td>
                  <td class="text-center"><strong>{{ totalWeight() }}%</strong></td>
                  <td colspan="2"></td>
                </tr>
              </ng-template>
            </p-table>

            @if (totalWeight() !== 100) {
              <p-message
                severity="warn"
                text="Total weight should equal 100%. Current total: {{ totalWeight() }}%"
                styleClass="mt-3"
              ></p-message>
            }
          </p-card>

          <p-card header="Scoring Configuration" styleClass="section-card mt-3">
            <div class="config-form">
              <div class="form-row">
                <div class="form-field">
                  <label for="scoringMethod">Scoring Method *</label>
                  <p-dropdown
                    id="scoringMethod"
                    [options]="scoringMethodOptions"
                    [(ngModel)]="scoringMethod"
                    optionLabel="label"
                    optionValue="value"
                    placeholder="Select scoring method"
                    styleClass="w-full"
                  >
                    <ng-template let-option pTemplate="item">
                      <div class="method-option">
                        <span class="method-label">{{ option.label }}</span>
                        <span class="method-desc">{{ option.description }}</span>
                      </div>
                    </ng-template>
                  </p-dropdown>
                </div>

                <div class="form-field">
                  <label for="deadline">Evaluation Deadline *</label>
                  <p-datepicker
                    id="deadline"
                    [(ngModel)]="deadline"
                    [showTime]="true"
                    [minDate]="minDeadline"
                    dateFormat="dd/mm/yy"
                    placeholder="Select deadline"
                    [showIcon]="true"
                    styleClass="w-full"
                  ></p-datepicker>
                </div>
              </div>

              <div class="form-row">
                <div class="form-field checkbox-field">
                  <p-checkbox
                    [(ngModel)]="blindMode"
                    [binary]="true"
                    inputId="blindMode"
                  ></p-checkbox>
                  <label for="blindMode" class="checkbox-label">
                    <span class="label-title">Enable Blind Mode</span>
                    <span class="label-desc">
                      Panel members will see "Bidder 001", "Bidder 002" etc. instead of actual bidder names
                    </span>
                  </label>
                </div>
              </div>
            </div>
          </p-card>

          <div class="action-bar">
            <button
              pButton
              label="Start Evaluation"
              icon="pi pi-play"
              class="p-button-success p-button-lg"
              [loading]="isSaving()"
              [disabled]="!isFormValid()"
              (click)="startEvaluation()"
            ></button>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .evaluation-setup-container {
      display: flex;
      flex-direction: column;
      gap: 1rem;
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
      color: #666;
      margin: 0;
    }

    /* Config Display */
    .config-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1.5rem;
    }

    .config-item {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .config-item label {
      font-size: 0.875rem;
      color: #666;
      font-weight: 500;
    }

    .config-item span {
      font-size: 1rem;
      color: #333;
    }

    /* Section Cards */
    :host ::ng-deep .section-card {
      .p-card-title {
        font-size: 1.125rem;
        color: #333;
      }
    }

    /* Panel Selection */
    .panel-selection {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .member-option {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
      padding: 0.25rem 0;
    }

    .member-info {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .member-name {
      font-weight: 500;
      color: #333;
    }

    .member-dept {
      font-size: 0.75rem;
      color: #666;
      background: #f0f0f0;
      padding: 0.125rem 0.5rem;
      border-radius: 4px;
    }

    .member-email {
      font-size: 0.8rem;
      color: #888;
    }

    .selection-info {
      display: flex;
      align-items: flex-start;
      gap: 0.5rem;
      padding: 0.75rem;
      background: #f8f9fa;
      border-radius: 6px;
      font-size: 0.875rem;
      color: #666;
    }

    .selection-info i {
      color: #1976D2;
      margin-top: 0.125rem;
    }

    /* Selected Members */
    .selected-members {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .selected-member {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.75rem 1rem;
      background: #f8f9fa;
      border-radius: 6px;
      border-left: 3px solid #1976D2;
    }

    .selected-member .member-order {
      width: 24px;
      height: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #1976D2;
      color: white;
      border-radius: 50%;
      font-size: 0.75rem;
      font-weight: 600;
    }

    .selected-member .member-name {
      flex: 1;
      font-weight: 500;
    }

    /* Config Form */
    .config-form {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .form-row {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 1.5rem;
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

    .checkbox-field {
      flex-direction: row;
      align-items: flex-start;
      gap: 0.75rem;
      padding: 1rem;
      background: #f8f9fa;
      border-radius: 6px;
    }

    .checkbox-label {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
      cursor: pointer;
    }

    .label-title {
      font-weight: 500;
      color: #333;
    }

    .label-desc {
      font-size: 0.85rem;
      color: #666;
    }

    .method-option {
      display: flex;
      flex-direction: column;
      gap: 0.125rem;
    }

    .method-label {
      font-weight: 500;
    }

    .method-desc {
      font-size: 0.8rem;
      color: #666;
    }

    /* Action Bar */
    .action-bar {
      display: flex;
      justify-content: flex-end;
      padding: 1.5rem 0;
      border-top: 1px solid #e0e0e0;
      margin-top: 1rem;
    }

    /* Table styles */
    :host ::ng-deep .p-datatable-sm .p-datatable-thead > tr > th {
      padding: 0.75rem 1rem;
    }

    :host ::ng-deep .p-datatable-sm .p-datatable-tbody > tr > td {
      padding: 0.75rem 1rem;
    }

    .text-center {
      text-align: center;
    }

    .text-right {
      text-align: right;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .form-row {
        grid-template-columns: 1fr;
      }

      .config-grid {
        grid-template-columns: 1fr;
      }

      .action-bar {
        justify-content: stretch;
      }

      .action-bar button {
        width: 100%;
      }
    }
  `]
})
export class EvaluationSetupComponent implements OnInit, OnDestroy {
  @Input() tenderId!: number;
  @Output() evaluationStarted = new EventEmitter<EvaluationSetup>();

  private readonly evaluationService = inject(EvaluationService);
  private readonly messageService = inject(MessageService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly destroy$ = new Subject<void>();

  // State signals
  availablePanelMembers = signal<PanelMemberOption[]>([]);
  criteria = signal<EvaluationCriterion[]>([]);
  existingSetup = signal<EvaluationSetup | null>(null);
  isLoading = signal<boolean>(true);
  isSaving = signal<boolean>(false);
  panelMemberError = signal<string | null>(null);

  // Form state
  selectedPanelMemberIds: number[] = [];
  scoringMethod: ScoringMethod = 'numeric';
  blindMode = true;
  deadline: Date | null = null;
  minDeadline = new Date();

  // Options
  scoringMethodOptions = SCORING_METHOD_OPTIONS;

  // Computed
  totalWeight = computed(() => {
    return this.criteria().reduce((sum, c) => sum + c.weight, 0);
  });

  ngOnInit(): void {
    this.loadData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadData(): void {
    this.isLoading.set(true);

    forkJoin({
      panelMembers: this.evaluationService.getAvailablePanelMembers(this.tenderId),
      criteria: this.evaluationService.getEvaluationCriteria(this.tenderId),
      setup: this.evaluationService.getEvaluationSetup(this.tenderId)
    }).pipe(takeUntil(this.destroy$))
      .subscribe({
        next: ({ panelMembers, criteria, setup }) => {
          this.availablePanelMembers.set(panelMembers);
          this.criteria.set(criteria);
          this.existingSetup.set(setup);

          // Set default deadline to 7 days from now
          const defaultDeadline = new Date();
          defaultDeadline.setDate(defaultDeadline.getDate() + 7);
          this.deadline = defaultDeadline;

          this.isLoading.set(false);
        },
        error: (error) => {
          this.isLoading.set(false);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: error.message || 'Failed to load evaluation data'
          });
        }
      });
  }

  onPanelMemberChange(): void {
    this.validatePanelMembers();
  }

  private validatePanelMembers(): boolean {
    if (this.selectedPanelMemberIds.length < 2) {
      this.panelMemberError.set('At least 2 panel members are required');
      return false;
    }
    if (this.selectedPanelMemberIds.length > 5) {
      this.panelMemberError.set('Maximum 5 panel members allowed');
      return false;
    }
    this.panelMemberError.set(null);
    return true;
  }

  removePanelMember(memberId: number): void {
    this.selectedPanelMemberIds = this.selectedPanelMemberIds.filter(id => id !== memberId);
    this.validatePanelMembers();
  }

  getMemberName(memberId: number): string {
    const member = this.availablePanelMembers().find(m => m.id === memberId);
    return member?.fullName || 'Unknown';
  }

  getMemberStatusSeverity(status: string): 'success' | 'info' | 'warn' | 'secondary' {
    switch (status) {
      case 'completed': return 'success';
      case 'in_progress': return 'info';
      case 'pending': return 'warn';
      default: return 'secondary';
    }
  }

  getScoringMethodLabel(method: ScoringMethod): string {
    const option = SCORING_METHOD_OPTIONS.find(o => o.value === method);
    return option?.label || method;
  }

  isFormValid(): boolean {
    return (
      this.selectedPanelMemberIds.length >= 2 &&
      this.selectedPanelMemberIds.length <= 5 &&
      this.scoringMethod !== null &&
      this.deadline !== null &&
      this.deadline > new Date()
    );
  }

  startEvaluation(): void {
    if (!this.isFormValid()) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Validation Error',
        detail: 'Please complete all required fields'
      });
      return;
    }

    this.confirmationService.confirm({
      message: 'Are you sure you want to start the evaluation? This will notify all panel members and they will begin scoring.',
      header: 'Start Evaluation',
      icon: 'pi pi-play',
      acceptLabel: 'Start Evaluation',
      rejectLabel: 'Cancel',
      accept: () => {
        this.isSaving.set(true);

        const dto: CreateEvaluationSetupDto = {
          tenderId: this.tenderId,
          panelMemberIds: this.selectedPanelMemberIds,
          scoringMethod: this.scoringMethod,
          blindMode: this.blindMode,
          deadline: this.deadline!
        };

        this.evaluationService.startEvaluation(dto)
          .pipe(takeUntil(this.destroy$))
          .subscribe({
            next: (setup) => {
              this.isSaving.set(false);
              this.existingSetup.set(setup);
              this.messageService.add({
                severity: 'success',
                summary: 'Success',
                detail: 'Evaluation started successfully. Panel members have been notified.'
              });
              this.evaluationStarted.emit(setup);
            },
            error: (error) => {
              this.isSaving.set(false);
              this.messageService.add({
                severity: 'error',
                summary: 'Error',
                detail: error.message || 'Failed to start evaluation'
              });
            }
          });
      }
    });
  }
}
