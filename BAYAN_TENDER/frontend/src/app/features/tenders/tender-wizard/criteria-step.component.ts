import { Component, Input, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormGroup, FormArray, FormBuilder, FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { InputNumberModule } from 'primeng/inputnumber';
import { InputTextModule } from 'primeng/inputtext';
import { ButtonModule } from 'primeng/button';
import { TableModule } from 'primeng/table';
import { TooltipModule } from 'primeng/tooltip';
import { SliderModule } from 'primeng/slider';
import { MessageModule } from 'primeng/message';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ConfirmationService } from 'primeng/api';
import { InputTextarea } from 'primeng/inputtextarea';

import { EvaluationCriterion, DEFAULT_EVALUATION_CRITERIA } from '../../../core/models/tender.model';

@Component({
  selector: 'app-criteria-step',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    InputNumberModule,
    InputTextModule,
    ButtonModule,
    TableModule,
    TooltipModule,
    SliderModule,
    MessageModule,
    ConfirmDialogModule,
    InputTextarea
  ],
  providers: [ConfirmationService],
  template: `
    <div class="criteria-step">
      <!-- Weight Distribution -->
      <div class="weight-distribution">
        <h3>Evaluation Weight Distribution</h3>
        <p class="weight-description">
          Define how technical and commercial scores will be weighted in the final evaluation.
          The total must equal 100%.
        </p>

        <div class="weight-inputs">
          <div class="weight-field">
            <label for="technicalWeight">Technical Weight (%)</label>
            <div class="weight-input-group">
              <p-inputNumber
                id="technicalWeight"
                [formControl]="technicalWeightControl"
                [min]="0"
                [max]="100"
                [showButtons]="true"
                suffix="%"
                styleClass="w-full"
                (onInput)="onTechnicalWeightChange($event)"
              ></p-inputNumber>
              <p-slider
                [formControl]="technicalWeightControl"
                [min]="0"
                [max]="100"
                (onChange)="onTechnicalWeightChange($event)"
              ></p-slider>
            </div>
          </div>

          <div class="weight-divider">
            <span>+</span>
          </div>

          <div class="weight-field">
            <label for="commercialWeight">Commercial Weight (%)</label>
            <div class="weight-input-group">
              <p-inputNumber
                id="commercialWeight"
                [formControl]="commercialWeightControl"
                [min]="0"
                [max]="100"
                [showButtons]="true"
                suffix="%"
                styleClass="w-full"
                (onInput)="onCommercialWeightChange($event)"
              ></p-inputNumber>
              <p-slider
                [formControl]="commercialWeightControl"
                [min]="0"
                [max]="100"
                (onChange)="onCommercialWeightChange($event)"
              ></p-slider>
            </div>
          </div>

          <div class="weight-divider">
            <span>=</span>
          </div>

          <div class="weight-total" [class.valid]="weightTotal() === 100" [class.invalid]="weightTotal() !== 100">
            <span class="total-value">{{ weightTotal() }}%</span>
            <span class="total-label">Total</span>
          </div>
        </div>

        @if (weightTotal() !== 100) {
          <p-message
            severity="error"
            text="Technical and commercial weights must sum to 100%"
            styleClass="mt-3"
          ></p-message>
        }
      </div>

      <!-- Evaluation Criteria -->
      <div class="evaluation-criteria">
        <div class="criteria-header">
          <h3>Technical Evaluation Criteria</h3>
          <div class="criteria-actions">
            <button
              pButton
              type="button"
              label="Load Defaults"
              icon="pi pi-refresh"
              class="p-button-outlined p-button-sm"
              (click)="loadDefaultCriteria()"
              pTooltip="Load default evaluation criteria"
            ></button>
            <button
              pButton
              type="button"
              label="Add Criterion"
              icon="pi pi-plus"
              class="p-button-sm"
              (click)="addCriterion()"
            ></button>
          </div>
        </div>

        <p-table
          [value]="criteriaControls"
          styleClass="p-datatable-sm"
          [scrollable]="true"
        >
          <ng-template pTemplate="header">
            <tr>
              <th style="width: 40%">Criterion Name</th>
              <th style="width: 35%">Description</th>
              <th style="width: 15%">Weight (%)</th>
              <th style="width: 10%">Actions</th>
            </tr>
          </ng-template>
          <ng-template pTemplate="body" let-criterion let-rowIndex="rowIndex">
            <tr [formGroup]="criterion">
              <td>
                <input
                  pInputText
                  formControlName="name"
                  placeholder="Enter criterion name"
                  class="w-full"
                />
                @if (criterion.get('name')?.invalid && criterion.get('name')?.touched) {
                  <small class="p-error">Name is required</small>
                }
              </td>
              <td>
                <input
                  pInputText
                  formControlName="description"
                  placeholder="Brief description (optional)"
                  class="w-full"
                />
              </td>
              <td>
                <p-inputNumber
                  formControlName="weight"
                  [min]="0"
                  [max]="100"
                  suffix="%"
                  styleClass="w-full"
                  [inputStyle]="{ width: '100%' }"
                ></p-inputNumber>
                @if (criterion.get('weight')?.invalid && criterion.get('weight')?.touched) {
                  <small class="p-error">Required</small>
                }
              </td>
              <td>
                <button
                  pButton
                  type="button"
                  icon="pi pi-trash"
                  class="p-button-rounded p-button-danger p-button-text p-button-sm"
                  (click)="removeCriterion(rowIndex)"
                  pTooltip="Remove criterion"
                  [disabled]="criteriaArray.length <= 1"
                ></button>
              </td>
            </tr>
          </ng-template>
          <ng-template pTemplate="footer">
            <tr>
              <td colspan="2" class="text-right font-bold">Total Criteria Weight:</td>
              <td [class.text-success]="criteriaWeightTotal() === 100" [class.text-danger]="criteriaWeightTotal() !== 100">
                <strong>{{ criteriaWeightTotal() }}%</strong>
              </td>
              <td></td>
            </tr>
          </ng-template>
          <ng-template pTemplate="emptymessage">
            <tr>
              <td colspan="4" class="text-center p-4">
                <p>No evaluation criteria defined.</p>
                <button
                  pButton
                  label="Add First Criterion"
                  icon="pi pi-plus"
                  class="p-button-outlined"
                  (click)="addCriterion()"
                ></button>
              </td>
            </tr>
          </ng-template>
        </p-table>

        @if (criteriaWeightTotal() !== 100 && criteriaArray.length > 0) {
          <p-message
            severity="warn"
            text="Criteria weights should sum to 100% for proper evaluation"
            styleClass="mt-3"
          ></p-message>
        }
      </div>

      <p-confirmDialog></p-confirmDialog>
    </div>
  `,
  styles: [`
    .criteria-step {
      display: flex;
      flex-direction: column;
      gap: 2rem;
    }

    .weight-distribution {
      padding: 1.5rem;
      background-color: #f8f9fa;
      border-radius: 12px;
    }

    .weight-distribution h3 {
      margin: 0 0 0.5rem 0;
      font-size: 1.1rem;
      color: #333;
    }

    .weight-description {
      color: #666;
      font-size: 0.9rem;
      margin: 0 0 1.5rem 0;
    }

    .weight-inputs {
      display: flex;
      align-items: center;
      gap: 1.5rem;
      flex-wrap: wrap;
    }

    .weight-field {
      flex: 1;
      min-width: 200px;
    }

    .weight-field label {
      display: block;
      font-weight: 600;
      color: #333;
      margin-bottom: 0.5rem;
      font-size: 0.9rem;
    }

    .weight-input-group {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .weight-divider {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 40px;
      height: 40px;
      font-size: 1.5rem;
      color: #666;
      margin-top: 1.5rem;
    }

    .weight-total {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 1rem 1.5rem;
      border-radius: 8px;
      background-color: #fff;
      border: 2px solid #e0e0e0;
      margin-top: 1.5rem;
    }

    .weight-total.valid {
      border-color: #4caf50;
      background-color: #e8f5e9;
    }

    .weight-total.invalid {
      border-color: #f44336;
      background-color: #ffebee;
    }

    .total-value {
      font-size: 1.5rem;
      font-weight: 700;
    }

    .weight-total.valid .total-value {
      color: #2e7d32;
    }

    .weight-total.invalid .total-value {
      color: #c62828;
    }

    .total-label {
      font-size: 0.8rem;
      color: #666;
    }

    .evaluation-criteria {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .criteria-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
    }

    .criteria-header h3 {
      margin: 0;
      font-size: 1.1rem;
      color: #333;
    }

    .criteria-actions {
      display: flex;
      gap: 0.5rem;
    }

    :host ::ng-deep .w-full {
      width: 100%;
    }

    .text-right {
      text-align: right;
    }

    .text-center {
      text-align: center;
    }

    .font-bold {
      font-weight: 600;
    }

    .text-success {
      color: #2e7d32;
    }

    .text-danger {
      color: #c62828;
    }

    @media (max-width: 768px) {
      .weight-inputs {
        flex-direction: column;
        align-items: stretch;
      }

      .weight-divider {
        margin-top: 0;
        width: 100%;
      }

      .weight-total {
        margin-top: 0;
        width: 100%;
      }
    }
  `]
})
export class CriteriaStepComponent implements OnInit {
  @Input() form!: FormGroup;

  private fb = new FormBuilder();
  private confirmationService = new ConfirmationService();

  get criteriaArray(): FormArray {
    return this.form.get('evaluationCriteria') as FormArray;
  }

  get criteriaControls(): FormGroup[] {
    return this.criteriaArray.controls as FormGroup[];
  }

  get technicalWeightControl(): FormControl {
    return this.form.get('technicalWeight') as FormControl;
  }

  get commercialWeightControl(): FormControl {
    return this.form.get('commercialWeight') as FormControl;
  }

  weightTotal = computed(() => {
    const technical = this.form.get('technicalWeight')?.value || 0;
    const commercial = this.form.get('commercialWeight')?.value || 0;
    return technical + commercial;
  });

  criteriaWeightTotal = signal<number>(0);

  ngOnInit(): void {
    this.calculateCriteriaTotal();
    this.criteriaArray.valueChanges.subscribe(() => {
      this.calculateCriteriaTotal();
    });
  }

  private calculateCriteriaTotal(): void {
    const total = this.criteriaArray.controls.reduce((sum, control) => {
      return sum + (control.get('weight')?.value || 0);
    }, 0);
    this.criteriaWeightTotal.set(total);
  }

  onTechnicalWeightChange(event: any): void {
    const technical = event.value ?? this.form.get('technicalWeight')?.value ?? 0;
    const commercial = 100 - technical;
    if (commercial >= 0 && commercial <= 100) {
      this.form.patchValue({ commercialWeight: commercial }, { emitEvent: false });
    }
  }

  onCommercialWeightChange(event: any): void {
    const commercial = event.value ?? this.form.get('commercialWeight')?.value ?? 0;
    const technical = 100 - commercial;
    if (technical >= 0 && technical <= 100) {
      this.form.patchValue({ technicalWeight: technical }, { emitEvent: false });
    }
  }

  addCriterion(): void {
    const newCriterion = this.fb.group({
      name: ['', Validators.required],
      weight: [0, [Validators.required, Validators.min(0), Validators.max(100)]],
      description: ['']
    });
    this.criteriaArray.push(newCriterion);
  }

  removeCriterion(index: number): void {
    if (this.criteriaArray.length > 1) {
      this.criteriaArray.removeAt(index);
    }
  }

  loadDefaultCriteria(): void {
    // Clear existing criteria
    while (this.criteriaArray.length) {
      this.criteriaArray.removeAt(0);
    }

    // Add default criteria
    DEFAULT_EVALUATION_CRITERIA.forEach(criterion => {
      const criterionGroup = this.fb.group({
        name: [criterion.name, Validators.required],
        weight: [criterion.weight, [Validators.required, Validators.min(0), Validators.max(100)]],
        description: [criterion.description || '']
      });
      this.criteriaArray.push(criterionGroup);
    });
  }
}
