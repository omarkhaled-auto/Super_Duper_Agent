import { Component, OnInit, OnDestroy, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute } from '@angular/router';
import { FormBuilder, FormGroup, FormArray, Validators, ReactiveFormsModule } from '@angular/forms';
import { Subject, takeUntil, switchMap, of } from 'rxjs';
import { StepsModule } from 'primeng/steps';
import { MenuItem, MessageService } from 'primeng/api';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { ToastModule } from 'primeng/toast';
import { ProgressSpinnerModule } from 'primeng/progressspinner';

import { BasicInfoStepComponent } from './basic-info-step.component';
import { DatesStepComponent } from './dates-step.component';
import { CriteriaStepComponent } from './criteria-step.component';
import { ReviewStepComponent } from './review-step.component';

import { TenderService } from '../../../core/services/tender.service';
import { CreateTenderDto, Tender, DEFAULT_EVALUATION_CRITERIA } from '../../../core/models/tender.model';

@Component({
  selector: 'app-tender-wizard',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    StepsModule,
    CardModule,
    ButtonModule,
    ToastModule,
    ProgressSpinnerModule,
    BasicInfoStepComponent,
    DatesStepComponent,
    CriteriaStepComponent,
    ReviewStepComponent
  ],
  providers: [MessageService],
  template: `
    <div class="tender-wizard">
      <p-toast></p-toast>

      <!-- Header -->
      <div class="wizard-header">
        <div class="header-content">
          <h1>{{ isEditMode() ? 'Edit Tender' : 'Create New Tender' }}</h1>
          <p>{{ isEditMode() ? 'Update tender details' : 'Follow the steps to create a new tender' }}</p>
        </div>
        <button
          pButton
          icon="pi pi-times"
          label="Cancel"
          class="p-button-text"
          (click)="onCancel()"
        ></button>
      </div>

      <!-- Steps Indicator -->
      <p-steps
        [model]="steps"
        [activeIndex]="activeStep()"
        [readonly]="false"
        (activeIndexChange)="onStepChange($event)"
        styleClass="wizard-steps"
      ></p-steps>

      <!-- Loading State -->
      @if (loading()) {
        <div class="loading-container">
          <p-progressSpinner [style]="{ width: '50px', height: '50px' }"></p-progressSpinner>
          <p>Loading tender data...</p>
        </div>
      } @else {
        <!-- Step Content -->
        <p-card styleClass="step-card">
          @switch (activeStep()) {
            @case (0) {
              <app-basic-info-step
                [form]="tenderForm"
                (clientAdded)="onClientAdded($event)"
              ></app-basic-info-step>
            }
            @case (1) {
              <app-dates-step [form]="tenderForm"></app-dates-step>
            }
            @case (2) {
              <app-criteria-step [form]="tenderForm"></app-criteria-step>
            }
            @case (3) {
              <app-review-step [form]="tenderForm"></app-review-step>
            }
          }
        </p-card>

        <!-- Navigation Buttons -->
        <div class="wizard-navigation">
          <div class="nav-left">
            @if (activeStep() > 0) {
              <button
                pButton
                icon="pi pi-arrow-left"
                label="Previous"
                class="p-button-outlined"
                data-testid="wizard-prev"
                (click)="previousStep()"
              ></button>
            }
          </div>

          <div class="nav-right">
            @if (activeStep() < steps.length - 1) {
              <button
                pButton
                icon="pi pi-arrow-right"
                iconPos="right"
                label="Next"
                data-testid="wizard-next"
                (click)="nextStep()"
                [disabled]="!isCurrentStepValid()"
              ></button>
            } @else {
              <button
                pButton
                icon="pi pi-save"
                label="Save as Draft"
                class="p-button-outlined"
                data-testid="wizard-save-draft"
                (click)="saveDraft()"
                [loading]="saving()"
              ></button>
              <button
                pButton
                icon="pi pi-check"
                label="{{ isEditMode() ? 'Update Tender' : 'Create Tender' }}"
                data-testid="wizard-create"
                (click)="createTender()"
                [loading]="saving()"
                [disabled]="!tenderForm.valid"
              ></button>
            }
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .tender-wizard {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
      max-width: 1000px;
      margin: 0 auto;
    }

    .wizard-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }

    .header-content h1 {
      margin: 0;
      font-size: 1.5rem;
      font-weight: 700;
      color: var(--bayan-slate-900, #0F172A);
    }

    .header-content p {
      margin: 0.25rem 0 0;
      color: var(--bayan-slate-500, #64748B);
    }

    :host ::ng-deep .wizard-steps {
      .p-steps-item {
        flex: 1;
      }

      .p-steps-item .p-steps-item-link,
      .p-steps-item .p-menuitem-link {
        flex-direction: column;
        gap: 0.5rem;
      }

      .p-steps-item-number,
      .p-steps-number {
        min-width: 2.5rem;
        height: 2.5rem;
        font-size: 1rem;
      }
    }

    :host ::ng-deep .step-card {
      .p-card-body {
        padding: 1.5rem;
      }

      .p-card {
        box-shadow: var(--bayan-shadow-sm, 0 1px 3px 0 rgba(0,0,0,0.1), 0 1px 2px -1px rgba(0,0,0,0.1));
        border-radius: var(--bayan-radius-lg, 0.75rem);
      }
    }

    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 4rem;
      gap: 1rem;
    }

    .loading-container p {
      color: var(--bayan-slate-500, #64748B);
    }

    .wizard-navigation {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem 0;
      margin-top: 0.5rem;
      background: var(--bayan-card, #ffffff);
      border-top: 1px solid var(--bayan-slate-200, #E2E8F0);
    }

    .nav-left, .nav-right {
      display: flex;
      gap: 0.75rem;
    }

    @media (max-width: 768px) {
      .wizard-header {
        flex-direction: column;
        gap: 1rem;
      }

      :host ::ng-deep .wizard-steps {
        .p-steps-item .p-steps-item-link,
        .p-steps-item .p-menuitem-link {
          .p-steps-item-label,
          .p-steps-title {
            display: none;
          }
        }
      }

      .wizard-navigation {
        flex-direction: column;
        gap: 1rem;
      }

      .nav-left, .nav-right {
        width: 100%;
        justify-content: center;
      }

      .nav-right {
        flex-direction: column;
      }

      .nav-right button {
        width: 100%;
      }
    }
  `]
})
export class TenderWizardComponent implements OnInit, OnDestroy {
  private readonly fb = inject(FormBuilder);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly tenderService = inject(TenderService);
  private readonly messageService = inject(MessageService);
  private readonly destroy$ = new Subject<void>();

  activeStep = signal<number>(0);
  loading = signal<boolean>(false);
  saving = signal<boolean>(false);
  isEditMode = signal<boolean>(false);
  tenderId = signal<string | number | null>(null);

  steps: MenuItem[] = [
    { label: 'Basic Info', icon: 'pi pi-file' },
    { label: 'Dates', icon: 'pi pi-calendar' },
    { label: 'Criteria', icon: 'pi pi-list' },
    { label: 'Review', icon: 'pi pi-check' }
  ];

  tenderForm!: FormGroup;

  ngOnInit(): void {
    this.initForm();
    this.checkEditMode();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private initForm(): void {
    this.tenderForm = this.fb.group({
      title: ['', [Validators.required, Validators.maxLength(500)]],
      reference: ['', Validators.required],
      description: [''],
      clientId: [null, Validators.required],
      type: ['open', Validators.required],
      currency: ['AED', Validators.required],
      estimatedValue: [null],
      bidValidityPeriod: [90],
      dates: this.fb.group({
        issueDate: [new Date(), Validators.required],
        clarificationDeadline: [null, Validators.required],
        submissionDeadline: [null, Validators.required],
        openingDate: [null, Validators.required]
      }),
      technicalWeight: [70, [Validators.required, Validators.min(0), Validators.max(100)]],
      commercialWeight: [30, [Validators.required, Validators.min(0), Validators.max(100)]],
      evaluationCriteria: this.fb.array([])
    });

    // Add default criteria
    this.loadDefaultCriteria();
  }

  private loadDefaultCriteria(): void {
    const criteriaArray = this.tenderForm.get('evaluationCriteria') as FormArray;
    DEFAULT_EVALUATION_CRITERIA.forEach(criterion => {
      criteriaArray.push(this.fb.group({
        name: [criterion.name, Validators.required],
        weight: [criterion.weight, [Validators.required, Validators.min(0), Validators.max(100)]],
        description: [criterion.description || '']
      }));
    });
  }

  private checkEditMode(): void {
    this.route.params.pipe(
      takeUntil(this.destroy$),
      switchMap(params => {
        if (params['id']) {
          this.isEditMode.set(true);
          this.tenderId.set(params['id']);
          this.loading.set(true);
          return this.tenderService.getTenderById(params['id']);
        }

        // Check for duplicate query param
        const duplicateId = this.route.snapshot.queryParams['duplicate'];
        if (duplicateId) {
          this.loading.set(true);
          return this.tenderService.getTenderById(duplicateId);
        }

        return of(null);
      })
    ).subscribe({
      next: (tender) => {
        if (tender) {
          this.populateForm(tender);
        }
        this.loading.set(false);
      },
      error: (error) => {
        this.loading.set(false);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load tender data'
        });
      }
    });
  }

  private populateForm(tender: Tender): void {
    // Clear existing criteria
    const criteriaArray = this.tenderForm.get('evaluationCriteria') as FormArray;
    while (criteriaArray.length) {
      criteriaArray.removeAt(0);
    }

    // If duplicating, clear the reference
    const isDuplicate = this.route.snapshot.queryParams['duplicate'];

    this.tenderForm.patchValue({
      title: isDuplicate ? `${tender.title} (Copy)` : tender.title,
      reference: isDuplicate ? '' : tender.reference,
      description: tender.description,
      clientId: { id: tender.clientId, name: tender.clientName },
      type: tender.type,
      currency: tender.currency,
      estimatedValue: tender.estimatedValue,
      bidValidityPeriod: tender.bidValidityPeriod,
      dates: {
        issueDate: isDuplicate ? new Date() : new Date(tender.dates.issueDate),
        clarificationDeadline: tender.dates.clarificationDeadline
          ? (isDuplicate ? null : new Date(tender.dates.clarificationDeadline))
          : null,
        submissionDeadline: isDuplicate ? null : new Date(tender.dates.submissionDeadline),
        openingDate: tender.dates.openingDate
          ? (isDuplicate ? null : new Date(tender.dates.openingDate))
          : null
      },
      technicalWeight: tender.technicalWeight,
      commercialWeight: tender.commercialWeight
    });

    // Add criteria
    tender.evaluationCriteria.forEach(criterion => {
      criteriaArray.push(this.fb.group({
        name: [criterion.name, Validators.required],
        weight: [criterion.weight, [Validators.required, Validators.min(0), Validators.max(100)]],
        description: [criterion.description || '']
      }));
    });
  }

  onStepChange(index: number): void {
    // Validate current step before allowing navigation forward
    if (index > this.activeStep()) {
      if (!this.isCurrentStepValid()) {
        this.messageService.add({
          severity: 'warn',
          summary: 'Validation',
          detail: 'Please complete the current step before proceeding'
        });
        return;
      }
    }
    this.activeStep.set(index);
  }

  nextStep(): void {
    if (this.isCurrentStepValid()) {
      this.activeStep.update(step => Math.min(step + 1, this.steps.length - 1));
    } else {
      this.markStepAsTouched();
      this.messageService.add({
        severity: 'warn',
        summary: 'Validation',
        detail: 'Please fill in all required fields'
      });
    }
  }

  previousStep(): void {
    this.activeStep.update(step => Math.max(step - 1, 0));
  }

  isCurrentStepValid(): boolean {
    switch (this.activeStep()) {
      case 0: // Basic Info
        return (
          this.tenderForm.get('title')?.valid &&
          this.tenderForm.get('reference')?.valid &&
          this.tenderForm.get('clientId')?.valid &&
          this.tenderForm.get('type')?.valid &&
          this.tenderForm.get('currency')?.valid
        ) ?? false;

      case 1: // Dates
        const datesGroup = this.tenderForm.get('dates') as FormGroup;
        return (
          datesGroup.get('issueDate')?.valid &&
          datesGroup.get('clarificationDeadline')?.valid &&
          datesGroup.get('submissionDeadline')?.valid &&
          datesGroup.get('openingDate')?.valid
        ) ?? false;

      case 2: // Criteria
        const technicalWeight = this.tenderForm.get('technicalWeight')?.value || 0;
        const commercialWeight = this.tenderForm.get('commercialWeight')?.value || 0;
        return technicalWeight + commercialWeight === 100;

      case 3: // Review
        return this.tenderForm.valid;

      default:
        return true;
    }
  }

  private markStepAsTouched(): void {
    switch (this.activeStep()) {
      case 0:
        this.tenderForm.get('title')?.markAsTouched();
        this.tenderForm.get('reference')?.markAsTouched();
        this.tenderForm.get('clientId')?.markAsTouched();
        this.tenderForm.get('type')?.markAsTouched();
        this.tenderForm.get('currency')?.markAsTouched();
        break;

      case 1:
        const datesGroup2 = this.tenderForm.get('dates') as FormGroup;
        datesGroup2.get('issueDate')?.markAsTouched();
        datesGroup2.get('clarificationDeadline')?.markAsTouched();
        datesGroup2.get('submissionDeadline')?.markAsTouched();
        datesGroup2.get('openingDate')?.markAsTouched();
        break;

      case 2:
        this.tenderForm.get('technicalWeight')?.markAsTouched();
        this.tenderForm.get('commercialWeight')?.markAsTouched();
        break;
    }
  }

  saveDraft(): void {
    this.saveTender('draft');
  }

  createTender(): void {
    if (!this.tenderForm.valid) {
      this.messageService.add({
        severity: 'error',
        summary: 'Validation Error',
        detail: 'Please fix all validation errors before submitting'
      });
      return;
    }
    this.saveTender('draft'); // Save as draft first, user can publish later
  }

  private saveTender(status: 'draft' | 'active'): void {
    this.saving.set(true);

    const formValue = this.tenderForm.value;
    const clientValue = formValue.clientId;

    const tenderData: CreateTenderDto = {
      title: formValue.title,
      reference: formValue.reference,
      description: formValue.description,
      clientId: typeof clientValue === 'object' ? clientValue.id : clientValue,
      type: formValue.type,
      currency: formValue.currency,
      estimatedValue: formValue.estimatedValue,
      bidValidityPeriod: formValue.bidValidityPeriod,
      dates: formValue.dates,
      technicalWeight: formValue.technicalWeight,
      commercialWeight: formValue.commercialWeight,
      evaluationCriteria: formValue.evaluationCriteria,
      status
    };

    const operation = this.isEditMode()
      ? this.tenderService.updateTender(this.tenderId()!, tenderData)
      : this.tenderService.createTender(tenderData);

    operation.pipe(takeUntil(this.destroy$)).subscribe({
      next: (tender) => {
        this.saving.set(false);
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: this.isEditMode()
            ? 'Tender updated successfully'
            : 'Tender created successfully'
        });
        setTimeout(() => {
          this.router.navigate(['/tenders', tender.id]);
        }, 1000);
      },
      error: (error) => {
        this.saving.set(false);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to save tender'
        });
      }
    });
  }

  onCancel(): void {
    this.router.navigate(['/tenders']);
  }

  onClientAdded(client: any): void {
    this.messageService.add({
      severity: 'success',
      summary: 'Success',
      detail: `Client "${client.name}" added successfully`
    });
  }
}
