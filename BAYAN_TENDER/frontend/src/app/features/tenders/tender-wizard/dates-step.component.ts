import { Component, Input, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormGroup, FormControl, ReactiveFormsModule } from '@angular/forms';
import { DatePickerModule } from 'primeng/datepicker';
import { MessageModule } from 'primeng/message';
import { TooltipModule } from 'primeng/tooltip';

@Component({
  selector: 'app-dates-step',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    DatePickerModule,
    MessageModule,
    TooltipModule
  ],
  template: `
    <div class="dates-step">
      <div class="dates-grid">
        <!-- Issue Date -->
        <div class="date-field">
          <label for="issueDate">
            <span class="date-icon" style="background-color: var(--bayan-primary-light, #EEF2FF);">
              <i class="pi pi-calendar" style="color: var(--bayan-primary, #4F46E5);"></i>
            </span>
            Issue Date *
          </label>
          <p-datepicker
            id="issueDate"
            [formControl]="issueDateControl"
            [showIcon]="true"
            [showButtonBar]="true"
            dateFormat="dd/mm/yy"
            placeholder="Select issue date"
            styleClass="w-full"
            [minDate]="today"
            (onSelect)="onDateChange()"
          ></p-datepicker>
          <small class="date-hint">When the tender will be officially issued</small>
          @if (datesGroup.get('issueDate')?.invalid && datesGroup.get('issueDate')?.touched) {
            <small class="p-error">Issue date is required</small>
          }
        </div>

        <!-- Clarification Deadline -->
        <div class="date-field">
          <label for="clarificationDeadline">
            <span class="date-icon" style="background-color: var(--bayan-warning-bg, #FFFBEB);">
              <i class="pi pi-question-circle" style="color: var(--bayan-warning, #D97706);"></i>
            </span>
            Clarification Deadline *
          </label>
          <p-datepicker
            id="clarificationDeadline"
            [formControl]="clarificationDeadlineControl"
            [showIcon]="true"
            [showButtonBar]="true"
            dateFormat="dd/mm/yy"
            placeholder="Select clarification deadline"
            styleClass="w-full"
            [minDate]="datesGroup.get('issueDate')?.value || today"
            (onSelect)="onDateChange()"
          ></p-datepicker>
          <small class="date-hint">Last date for bidders to submit questions</small>
          @if (datesGroup.get('clarificationDeadline')?.invalid && datesGroup.get('clarificationDeadline')?.touched) {
            <small class="p-error">Clarification deadline is required</small>
          }
        </div>

        <!-- Submission Deadline -->
        <div class="date-field">
          <label for="submissionDeadline">
            <span class="date-icon" style="background-color: var(--bayan-success-bg, #F0FDF4);">
              <i class="pi pi-send" style="color: var(--bayan-success, #16A34A);"></i>
            </span>
            Submission Deadline *
          </label>
          <p-datepicker
            id="submissionDeadline"
            [formControl]="submissionDeadlineControl"
            [showIcon]="true"
            [showButtonBar]="true"
            dateFormat="dd/mm/yy"
            placeholder="Select submission deadline"
            styleClass="w-full"
            [minDate]="minSubmissionDate()"
            (onSelect)="onDateChange()"
          ></p-datepicker>
          <small class="date-hint">Final deadline for bid submissions</small>
          @if (datesGroup.get('submissionDeadline')?.invalid && datesGroup.get('submissionDeadline')?.touched) {
            <small class="p-error">
              @if (datesGroup.get('submissionDeadline')?.errors?.['required']) {
                Submission deadline is required
              }
            </small>
          }
          @if (submissionDateWarning()) {
            <p-message
              severity="warn"
              [text]="submissionDateWarning()!"
              styleClass="mt-2"
            ></p-message>
          }
        </div>

        <!-- Opening Date -->
        <div class="date-field">
          <label for="openingDate">
            <span class="date-icon" style="background-color: var(--bayan-danger-bg, #FEF2F2);">
              <i class="pi pi-folder-open" style="color: var(--bayan-danger, #DC2626);"></i>
            </span>
            Opening Date *
          </label>
          <p-datepicker
            id="openingDate"
            [formControl]="openingDateControl"
            [showIcon]="true"
            [showButtonBar]="true"
            dateFormat="dd/mm/yy"
            placeholder="Select opening date"
            styleClass="w-full"
            [minDate]="datesGroup.get('submissionDeadline')?.value || today"
            (onSelect)="onDateChange()"
          ></p-datepicker>
          <small class="date-hint">When bids will be officially opened</small>
          @if (datesGroup.get('openingDate')?.invalid && datesGroup.get('openingDate')?.touched) {
            <small class="p-error">Opening date is required</small>
          }
        </div>
      </div>

      <!-- Timeline Visualization -->
      <div class="timeline-container">
        <h3>Timeline Preview</h3>
        <div class="timeline">
          @for (milestone of timelineMilestones(); track milestone.label) {
            <div class="timeline-item" [class.active]="milestone.date">
              <div class="timeline-marker" [style.background-color]="milestone.color"></div>
              <div class="timeline-content">
                <span class="timeline-label">{{ milestone.label }}</span>
                @if (milestone.date) {
                  <span class="timeline-date">{{ milestone.date | date:'mediumDate' }}</span>
                  <span class="timeline-days">{{ milestone.daysFromNow }}</span>
                } @else {
                  <span class="timeline-date not-set">Not set</span>
                }
              </div>
              @if (!$last) {
                <div class="timeline-connector" [class.has-date]="milestone.date"></div>
              }
            </div>
          }
        </div>
      </div>

      <!-- Duration Summary -->
      @if (durationSummary()) {
        <div class="duration-summary">
          <div class="duration-card">
            <i class="pi pi-clock"></i>
            <div class="duration-content">
              <span class="duration-value">{{ durationSummary()!.totalDays }} days</span>
              <span class="duration-label">Total tender duration</span>
            </div>
          </div>
          @if (durationSummary()!.clarificationPeriod) {
            <div class="duration-card">
              <i class="pi pi-comments"></i>
              <div class="duration-content">
                <span class="duration-value">{{ durationSummary()!.clarificationPeriod }} days</span>
                <span class="duration-label">Clarification period</span>
              </div>
            </div>
          }
          <div class="duration-card">
            <i class="pi pi-calendar-plus"></i>
            <div class="duration-content">
              <span class="duration-value">{{ durationSummary()!.submissionPeriod }} days</span>
              <span class="duration-label">Submission period</span>
            </div>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .dates-step {
      display: flex;
      flex-direction: column;
      gap: 2rem;
    }

    .dates-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 1.5rem;
    }

    .date-field {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .date-field label {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      font-weight: 600;
      color: var(--bayan-slate-700, #334155);
      font-size: 0.875rem;
    }

    .date-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 32px;
      height: 32px;
      border-radius: var(--bayan-radius, 0.5rem);
    }

    .date-icon i {
      font-size: 1rem;
      color: var(--bayan-slate-700, #334155);
    }

    .date-hint {
      color: var(--bayan-slate-400, #94A3B8);
      font-size: 0.75rem;
    }

    :host ::ng-deep .w-full {
      width: 100%;
    }

    .timeline-container {
      padding: 1.5rem;
      background-color: var(--bayan-primary-light, #EEF2FF);
      border-radius: var(--bayan-radius-lg, 0.75rem);
    }

    .timeline-container h3 {
      margin: 0 0 1.5rem 0;
      font-size: 1rem;
      font-weight: 600;
      color: var(--bayan-slate-900, #0F172A);
      border-bottom: 1px solid var(--bayan-slate-200, #E2E8F0);
      padding-bottom: 0.75rem;
    }

    .timeline {
      display: flex;
      justify-content: space-between;
      position: relative;
    }

    .timeline-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      flex: 1;
      position: relative;
    }

    .timeline-marker {
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background-color: var(--bayan-slate-200, #E2E8F0);
      z-index: 1;
    }

    .timeline-item.active .timeline-marker {
      box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.15);
    }

    .timeline-content {
      display: flex;
      flex-direction: column;
      align-items: center;
      margin-top: 0.75rem;
      text-align: center;
    }

    .timeline-label {
      font-weight: 600;
      color: var(--bayan-slate-900, #0F172A);
      font-size: 0.875rem;
    }

    .timeline-date {
      color: var(--bayan-slate-500, #64748B);
      font-size: 0.8rem;
      margin-top: 0.25rem;
    }

    .timeline-date.not-set {
      color: var(--bayan-slate-400, #94A3B8);
      font-style: italic;
    }

    .timeline-days {
      font-size: 0.75rem;
      color: var(--bayan-primary, #4F46E5);
      font-weight: 500;
      margin-top: 0.25rem;
    }

    .timeline-connector {
      position: absolute;
      top: 8px;
      left: 50%;
      width: 100%;
      height: 2px;
      background-color: var(--bayan-slate-200, #E2E8F0);
      z-index: 0;
    }

    .timeline-connector.has-date {
      background-color: var(--bayan-primary, #4F46E5);
    }

    .timeline-item:last-child .timeline-connector {
      display: none;
    }

    .duration-summary {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
    }

    .duration-card {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1rem;
      background-color: var(--bayan-card, #ffffff);
      border: 1px solid var(--bayan-border, #E2E8F0);
      border-radius: var(--bayan-radius-lg, 0.75rem);
      box-shadow: var(--bayan-shadow-xs, 0 1px 2px 0 rgba(0,0,0,0.05));
    }

    .duration-card i {
      font-size: 1.5rem;
      color: var(--bayan-primary, #4F46E5);
    }

    .duration-content {
      display: flex;
      flex-direction: column;
    }

    .duration-value {
      font-weight: 600;
      color: var(--bayan-slate-900, #0F172A);
      font-size: 1.1rem;
    }

    .duration-label {
      font-size: 0.8rem;
      color: var(--bayan-slate-500, #64748B);
    }

    @media (max-width: 768px) {
      .dates-grid {
        grid-template-columns: 1fr;
      }

      .timeline {
        flex-direction: column;
        gap: 1.5rem;
      }

      .timeline-item {
        flex-direction: row;
        align-items: flex-start;
      }

      .timeline-content {
        align-items: flex-start;
        margin-top: 0;
        margin-left: 1rem;
      }

      .timeline-connector {
        display: none;
      }
    }
  `]
})
export class DatesStepComponent implements OnInit {
  @Input() form!: FormGroup;

  today = new Date();

  get datesGroup(): FormGroup {
    return this.form.get('dates') as FormGroup;
  }

  get issueDateControl(): FormControl {
    return this.datesGroup.get('issueDate') as FormControl;
  }

  get clarificationDeadlineControl(): FormControl {
    return this.datesGroup.get('clarificationDeadline') as FormControl;
  }

  get submissionDeadlineControl(): FormControl {
    return this.datesGroup.get('submissionDeadline') as FormControl;
  }

  get openingDateControl(): FormControl {
    return this.datesGroup.get('openingDate') as FormControl;
  }

  minSubmissionDate = computed(() => {
    const clarificationDate = this.datesGroup.get('clarificationDeadline')?.value;
    if (clarificationDate) {
      const minDate = new Date(clarificationDate);
      minDate.setDate(minDate.getDate() + 3);
      return minDate;
    }
    return this.datesGroup.get('issueDate')?.value || this.today;
  });

  submissionDateWarning = signal<string | null>(null);

  timelineMilestones = computed(() => {
    const issueDate = this.datesGroup.get('issueDate')?.value;
    const clarificationDeadline = this.datesGroup.get('clarificationDeadline')?.value;
    const submissionDeadline = this.datesGroup.get('submissionDeadline')?.value;
    const openingDate = this.datesGroup.get('openingDate')?.value;

    return [
      {
        label: 'Issue',
        date: issueDate,
        color: '#4F46E5',
        daysFromNow: issueDate ? this.getDaysFromNow(issueDate) : null
      },
      {
        label: 'Clarification',
        date: clarificationDeadline,
        color: '#D97706',
        daysFromNow: clarificationDeadline ? this.getDaysFromNow(clarificationDeadline) : null
      },
      {
        label: 'Submission',
        date: submissionDeadline,
        color: '#16A34A',
        daysFromNow: submissionDeadline ? this.getDaysFromNow(submissionDeadline) : null
      },
      {
        label: 'Opening',
        date: openingDate,
        color: '#DC2626',
        daysFromNow: openingDate ? this.getDaysFromNow(openingDate) : null
      }
    ];
  });

  durationSummary = computed(() => {
    const issueDate = this.datesGroup.get('issueDate')?.value;
    const clarificationDeadline = this.datesGroup.get('clarificationDeadline')?.value;
    const submissionDeadline = this.datesGroup.get('submissionDeadline')?.value;

    if (!issueDate || !submissionDeadline) return null;

    const totalDays = this.daysBetween(issueDate, submissionDeadline);
    const clarificationPeriod = clarificationDeadline
      ? this.daysBetween(issueDate, clarificationDeadline)
      : null;
    const submissionPeriod = clarificationDeadline
      ? this.daysBetween(clarificationDeadline, submissionDeadline)
      : totalDays;

    return {
      totalDays,
      clarificationPeriod,
      submissionPeriod
    };
  });

  ngOnInit(): void {
    // Set default issue date to today if not set
    if (!this.datesGroup.get('issueDate')?.value) {
      this.datesGroup.patchValue({ issueDate: this.today });
    }
  }

  onDateChange(): void {
    this.validateDates();
  }

  private validateDates(): void {
    const clarificationDate = this.datesGroup.get('clarificationDeadline')?.value;
    const submissionDate = this.datesGroup.get('submissionDeadline')?.value;

    if (clarificationDate && submissionDate) {
      const daysDiff = this.daysBetween(clarificationDate, submissionDate);
      if (daysDiff < 3) {
        this.submissionDateWarning.set(
          'Submission deadline should be at least 3 days after clarification deadline to allow bidders time to incorporate clarifications.'
        );
      } else {
        this.submissionDateWarning.set(null);
      }
    } else {
      this.submissionDateWarning.set(null);
    }
  }

  private getDaysFromNow(date: Date): string {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const targetDate = new Date(date);
    targetDate.setHours(0, 0, 0, 0);

    const diff = Math.ceil((targetDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

    if (diff === 0) return 'Today';
    if (diff === 1) return 'Tomorrow';
    if (diff < 0) return `${Math.abs(diff)} days ago`;
    return `In ${diff} days`;
  }

  private daysBetween(date1: Date, date2: Date): number {
    const d1 = new Date(date1);
    const d2 = new Date(date2);
    d1.setHours(0, 0, 0, 0);
    d2.setHours(0, 0, 0, 0);
    return Math.ceil((d2.getTime() - d1.getTime()) / (1000 * 60 * 60 * 24));
  }
}
