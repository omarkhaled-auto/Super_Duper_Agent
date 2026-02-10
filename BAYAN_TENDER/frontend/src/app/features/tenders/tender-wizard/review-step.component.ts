import { Component, Input, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormGroup } from '@angular/forms';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { DividerModule } from 'primeng/divider';

import {
  TENDER_TYPE_OPTIONS,
  CURRENCY_OPTIONS,
  TenderType,
  Currency
} from '../../../core/models/tender.model';

@Component({
  selector: 'app-review-step',
  standalone: true,
  imports: [
    CommonModule,
    CardModule,
    TagModule,
    DividerModule
  ],
  template: `
    <div class="review-step">
      <div class="review-header">
        <h3>Review Your Tender</h3>
        <p>Please review all the information before creating the tender.</p>
      </div>

      <div class="review-grid">
        <!-- Basic Information -->
        <p-card header="Basic Information" styleClass="review-card">
          <div class="review-section">
            <div class="review-item">
              <span class="item-label">Title</span>
              <span class="item-value">{{ form.get('title')?.value || '-' }}</span>
            </div>
            <div class="review-item">
              <span class="item-label">Reference</span>
              <span class="item-value reference">{{ form.get('reference')?.value || '-' }}</span>
            </div>
            <div class="review-item">
              <span class="item-label">Client</span>
              <span class="item-value">{{ clientName() }}</span>
            </div>
            <div class="review-item">
              <span class="item-label">Tender Type</span>
              <span class="item-value">
                <p-tag [value]="getTenderTypeLabel()" severity="info"></p-tag>
              </span>
            </div>
            <div class="review-item">
              <span class="item-label">Currency</span>
              <span class="item-value">{{ getCurrencyLabel() }}</span>
            </div>
            @if (form.get('estimatedValue')?.value) {
              <div class="review-item">
                <span class="item-label">Estimated Value</span>
                <span class="item-value">
                  {{ form.get('currency')?.value }} {{ form.get('estimatedValue')?.value | number:'1.0-0' }}
                </span>
              </div>
            }
            @if (form.get('bidValidityPeriod')?.value) {
              <div class="review-item">
                <span class="item-label">Bid Validity</span>
                <span class="item-value">{{ form.get('bidValidityPeriod')?.value }} days</span>
              </div>
            }
          </div>
        </p-card>

        <!-- Key Dates -->
        <p-card header="Key Dates" styleClass="review-card">
          <div class="review-section">
            <div class="review-item">
              <span class="item-label">Issue Date</span>
              <span class="item-value">
                {{ datesGroup.get('issueDate')?.value | date:'fullDate' }}
              </span>
            </div>
            @if (datesGroup.get('clarificationDeadline')?.value) {
              <div class="review-item">
                <span class="item-label">Clarification Deadline</span>
                <span class="item-value">
                  {{ datesGroup.get('clarificationDeadline')?.value | date:'fullDate' }}
                </span>
              </div>
            }
            <div class="review-item">
              <span class="item-label">Submission Deadline</span>
              <span class="item-value highlight">
                {{ datesGroup.get('submissionDeadline')?.value | date:'fullDate' }}
              </span>
            </div>
            @if (datesGroup.get('openingDate')?.value) {
              <div class="review-item">
                <span class="item-label">Opening Date</span>
                <span class="item-value">
                  {{ datesGroup.get('openingDate')?.value | date:'fullDate' }}
                </span>
              </div>
            }
          </div>
        </p-card>

        <!-- Evaluation Weights -->
        <p-card header="Evaluation Weights" styleClass="review-card">
          <div class="weights-visualization">
            <div class="weight-bar">
              <div
                class="weight-segment technical"
                [style.width.%]="form.get('technicalWeight')?.value || 0"
              >
                <span>Technical: {{ form.get('technicalWeight')?.value }}%</span>
              </div>
              <div
                class="weight-segment commercial"
                [style.width.%]="form.get('commercialWeight')?.value || 0"
              >
                <span>Commercial: {{ form.get('commercialWeight')?.value }}%</span>
              </div>
            </div>
          </div>
        </p-card>

        <!-- Evaluation Criteria -->
        <p-card header="Evaluation Criteria" styleClass="review-card full-width">
          <div class="criteria-list">
            @for (criterion of criteriaList(); track criterion.name) {
              <div class="criterion-item">
                <div class="criterion-info">
                  <span class="criterion-name">{{ criterion.name }}</span>
                  @if (criterion.description) {
                    <span class="criterion-description">{{ criterion.description }}</span>
                  }
                </div>
                <div class="criterion-weight">
                  <span class="weight-value">{{ criterion.weight }}%</span>
                  <div class="weight-bar-small">
                    <div class="weight-fill" [style.width.%]="criterion.weight"></div>
                  </div>
                </div>
              </div>
            }
            @if (criteriaList().length === 0) {
              <p class="no-criteria">No evaluation criteria defined</p>
            }
          </div>
          <p-divider></p-divider>
          <div class="criteria-total">
            <span>Total Weight:</span>
            <strong [class.valid]="criteriaTotal() === 100" [class.invalid]="criteriaTotal() !== 100">
              {{ criteriaTotal() }}%
            </strong>
          </div>
        </p-card>

        <!-- Description Preview -->
        @if (form.get('description')?.value) {
          <p-card header="Description" styleClass="review-card full-width">
            <div class="description-preview" [innerHTML]="form.get('description')?.value"></div>
          </p-card>
        }
      </div>

      <!-- Validation Summary -->
      @if (validationErrors().length > 0) {
        <div class="validation-summary">
          <h4><i class="pi pi-exclamation-triangle"></i> Please fix the following issues:</h4>
          <ul>
            @for (error of validationErrors(); track error) {
              <li>{{ error }}</li>
            }
          </ul>
        </div>
      }
    </div>
  `,
  styles: [`
    .review-step {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .review-header h3 {
      margin: 0 0 0.25rem 0;
      font-size: 1.25rem;
      color: var(--bayan-foreground, #09090b);
    }

    .review-header p {
      margin: 0;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .review-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 1.5rem;
    }

    :host ::ng-deep .review-card {
      height: 100%;

      .p-card-body {
        height: 100%;
      }

      .p-card-content {
        padding: 0;
      }
    }

    :host ::ng-deep .review-card.full-width {
      grid-column: 1 / -1;
    }

    .review-section {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .review-item {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      padding: 0.5rem 0;
      border-bottom: 1px solid var(--bayan-border, #e4e4e7);
    }

    .review-item:last-child {
      border-bottom: none;
    }

    .item-label {
      color: var(--bayan-muted-foreground, #71717a);
      font-size: 0.9rem;
    }

    .item-value {
      font-weight: 500;
      color: var(--bayan-foreground, #09090b);
      text-align: right;
      max-width: 60%;
    }

    .item-value.reference {
      font-family: monospace;
      background-color: var(--bayan-muted, #f4f4f5);
      padding: 0.25rem 0.5rem;
      border-radius: var(--bayan-radius-sm, 0.375rem);
    }

    .item-value.highlight {
      color: var(--bayan-primary, #18181b);
      font-weight: 600;
    }

    .weights-visualization {
      padding: 1rem 0;
    }

    .weight-bar {
      display: flex;
      height: 40px;
      border-radius: var(--bayan-radius, 0.5rem);
      overflow: hidden;
    }

    .weight-segment {
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-weight: 600;
      font-size: 0.875rem;
    }

    .weight-segment.technical {
      background-color: var(--bayan-primary, #18181b);
    }

    .weight-segment.commercial {
      background-color: #16a34a;
    }

    .criteria-list {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .criterion-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.75rem;
      background-color: var(--bayan-accent, #f4f4f5);
      border-radius: var(--bayan-radius, 0.5rem);
    }

    .criterion-info {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }

    .criterion-name {
      font-weight: 600;
      color: var(--bayan-foreground, #09090b);
    }

    .criterion-description {
      font-size: 0.8rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .criterion-weight {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 0.25rem;
      min-width: 80px;
    }

    .weight-value {
      font-weight: 600;
      color: var(--bayan-primary, #18181b);
    }

    .weight-bar-small {
      width: 80px;
      height: 4px;
      background-color: var(--bayan-border, #e4e4e7);
      border-radius: 2px;
      overflow: hidden;
    }

    .weight-fill {
      height: 100%;
      background-color: var(--bayan-primary, #18181b);
      transition: width 0.3s ease;
    }

    .no-criteria {
      color: var(--bayan-muted-foreground, #71717a);
      font-style: italic;
      text-align: center;
      padding: 1rem;
    }

    .criteria-total {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 0.5rem;
      font-size: 1rem;
    }

    .criteria-total .valid {
      color: #16a34a;
    }

    .criteria-total .invalid {
      color: #dc2626;
    }

    .description-preview {
      padding: 1rem;
      background-color: var(--bayan-accent, #f4f4f5);
      border-radius: var(--bayan-radius, 0.5rem);
      max-height: 200px;
      overflow-y: auto;
    }

    .description-preview :host ::ng-deep {
      p { margin: 0 0 0.5rem 0; }
      ul, ol { margin: 0.5rem 0; padding-left: 1.5rem; }
    }

    .validation-summary {
      background-color: #fff7ed;
      border: 1px solid #fb923c;
      border-radius: var(--bayan-radius, 0.5rem);
      padding: 1rem;
    }

    .validation-summary h4 {
      margin: 0 0 0.5rem 0;
      color: #e65100;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .validation-summary ul {
      margin: 0;
      padding-left: 1.5rem;
      color: var(--bayan-foreground, #09090b);
    }

    .validation-summary li {
      margin-bottom: 0.25rem;
    }

    @media (max-width: 768px) {
      .review-grid {
        grid-template-columns: 1fr;
      }

      .review-item {
        flex-direction: column;
        gap: 0.25rem;
      }

      .item-value {
        text-align: left;
        max-width: 100%;
      }
    }
  `]
})
export class ReviewStepComponent {
  @Input() form!: FormGroup;

  get datesGroup(): FormGroup {
    return this.form.get('dates') as FormGroup;
  }

  clientName = computed(() => {
    const clientValue = this.form.get('clientId')?.value;
    if (typeof clientValue === 'object' && clientValue?.name) {
      return clientValue.name;
    }
    return 'Not selected';
  });

  criteriaList = computed(() => {
    const criteria = this.form.get('evaluationCriteria')?.value || [];
    return criteria.map((c: any) => ({
      name: c.name || 'Unnamed',
      weight: c.weight || 0,
      description: c.description
    }));
  });

  criteriaTotal = computed(() => {
    const criteria = this.form.get('evaluationCriteria')?.value || [];
    return criteria.reduce((sum: number, c: any) => sum + (c.weight || 0), 0);
  });

  validationErrors = computed(() => {
    const errors: string[] = [];

    if (!this.form.get('title')?.value) {
      errors.push('Tender title is required');
    }
    if (!this.form.get('reference')?.value) {
      errors.push('Tender reference is required');
    }
    if (!this.form.get('clientId')?.value) {
      errors.push('Client is required');
    }
    if (!this.form.get('type')?.value) {
      errors.push('Tender type is required');
    }
    if (!this.form.get('currency')?.value) {
      errors.push('Currency is required');
    }
    if (!this.datesGroup.get('issueDate')?.value) {
      errors.push('Issue date is required');
    }
    if (!this.datesGroup.get('submissionDeadline')?.value) {
      errors.push('Submission deadline is required');
    }

    const technicalWeight = this.form.get('technicalWeight')?.value || 0;
    const commercialWeight = this.form.get('commercialWeight')?.value || 0;
    if (technicalWeight + commercialWeight !== 100) {
      errors.push('Technical and commercial weights must sum to 100%');
    }

    if (this.criteriaTotal() !== 100 && this.criteriaList().length > 0) {
      errors.push('Criteria weights should sum to 100%');
    }

    return errors;
  });

  getTenderTypeLabel(): string {
    const type = this.form.get('type')?.value as TenderType;
    return TENDER_TYPE_OPTIONS.find(t => t.value === type)?.label || type || '-';
  }

  getCurrencyLabel(): string {
    const currency = this.form.get('currency')?.value as Currency;
    const option = CURRENCY_OPTIONS.find(c => c.value === currency);
    return option ? `${option.symbol} (${option.value})` : currency || '-';
  }
}
