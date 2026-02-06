import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { ReactiveFormsModule, FormArray } from '@angular/forms';
import { MessageService } from 'primeng/api';
import { of, throwError, Subject, BehaviorSubject } from 'rxjs';

import { TenderWizardComponent } from './tender-wizard.component';
import { TenderService } from '../../../core/services/tender.service';
import { Tender, DEFAULT_EVALUATION_CRITERIA } from '../../../core/models/tender.model';

describe('TenderWizardComponent', () => {
  let component: TenderWizardComponent;
  let fixture: ComponentFixture<TenderWizardComponent>;
  let tenderServiceSpy: jasmine.SpyObj<TenderService>;
  let routerSpy: jasmine.SpyObj<Router>;
  let messageServiceSpy: jasmine.SpyObj<MessageService>;
  let paramsSubject: BehaviorSubject<Record<string, string>>;

  const mockTender: Tender = {
    id: 42,
    title: 'IT Infrastructure Upgrade',
    reference: 'TND-2026-0001',
    description: 'Full infrastructure modernization',
    clientId: 1,
    clientName: 'Ministry of Finance',
    type: 'open',
    status: 'draft',
    currency: 'AED',
    estimatedValue: 2500000,
    bidValidityPeriod: 90,
    dates: {
      issueDate: new Date('2026-01-15'),
      clarificationDeadline: new Date('2026-02-10'),
      submissionDeadline: new Date('2026-02-28'),
      openingDate: new Date('2026-03-01')
    },
    technicalWeight: 70,
    commercialWeight: 30,
    evaluationCriteria: [
      { id: 1, name: 'Compliance', weight: 20, description: 'Compliance check' },
      { id: 2, name: 'Methodology', weight: 25, description: 'Technical approach' },
      { id: 3, name: 'Team CVs', weight: 15, description: 'Team qualifications' },
      { id: 4, name: 'Program', weight: 15, description: 'Work schedule' },
      { id: 5, name: 'QA/QC', weight: 15, description: 'Quality assurance' },
      { id: 6, name: 'HSE', weight: 10, description: 'Health safety' }
    ],
    invitedBiddersCount: 12,
    submittedBidsCount: 5,
    createdAt: new Date('2026-01-10'),
    updatedAt: new Date('2026-01-15'),
    createdBy: 1,
    createdByName: 'Admin User'
  };

  beforeEach(async () => {
    tenderServiceSpy = jasmine.createSpyObj('TenderService', [
      'createTender',
      'updateTender',
      'getTenderById'
    ]);
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);
    messageServiceSpy = jasmine.createSpyObj('MessageService', ['add']);
    paramsSubject = new BehaviorSubject<Record<string, string>>({});

    await TestBed.configureTestingModule({
      imports: [TenderWizardComponent, ReactiveFormsModule],
      schemas: [NO_ERRORS_SCHEMA],
      providers: [
        { provide: TenderService, useValue: tenderServiceSpy },
        { provide: Router, useValue: routerSpy },
        { provide: MessageService, useValue: messageServiceSpy },
        {
          provide: ActivatedRoute,
          useValue: {
            params: paramsSubject.asObservable(),
            snapshot: { queryParams: {} }
          }
        }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(TenderWizardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  // ─────────────────────── Creation & Initialization ───────────────────────

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with step 0', () => {
    expect(component.activeStep()).toBe(0);
  });

  it('should initialize form with default values', () => {
    expect(component.tenderForm).toBeTruthy();
    expect(component.tenderForm.get('title')).toBeTruthy();
    expect(component.tenderForm.get('reference')).toBeTruthy();
    expect(component.tenderForm.get('clientId')).toBeTruthy();
    expect(component.tenderForm.get('type')?.value).toBe('open');
    expect(component.tenderForm.get('currency')?.value).toBe('AED');
    expect(component.tenderForm.get('technicalWeight')?.value).toBe(70);
    expect(component.tenderForm.get('commercialWeight')?.value).toBe(30);
  });

  it('should load default evaluation criteria', () => {
    const criteriaArray = component.tenderForm.get('evaluationCriteria') as FormArray;
    expect(criteriaArray.length).toBe(DEFAULT_EVALUATION_CRITERIA.length);
    expect(criteriaArray.at(0).get('name')?.value).toBe('Compliance');
  });

  // ─────────────────────── Step 1 Validation ───────────────────────

  it('should validate required fields on step 1', () => {
    // Form starts empty except defaults, so step 1 required fields are invalid
    expect(component.isCurrentStepValid()).toBeFalse();

    // Fill required fields for step 1
    component.tenderForm.patchValue({
      title: 'Test Tender',
      reference: 'TND-TEST-001',
      clientId: 1,
      type: 'open',
      currency: 'AED'
    });

    expect(component.isCurrentStepValid()).toBeTrue();
  });

  // ─────────────────────── Navigation ───────────────────────

  it('should navigate to next step when step 1 is valid', () => {
    // Fill step 1 required fields
    component.tenderForm.patchValue({
      title: 'Test Tender',
      reference: 'TND-TEST-001',
      clientId: 1,
      type: 'open',
      currency: 'AED'
    });

    component.nextStep();

    expect(component.activeStep()).toBe(1);
  });

  it('should not navigate to next step when current step is invalid', () => {
    // Step 1 fields are empty (invalid)
    component.nextStep();

    expect(component.activeStep()).toBe(0);
    expect(messageServiceSpy.add).toHaveBeenCalledWith(
      jasmine.objectContaining({
        severity: 'warn',
        summary: 'Validation'
      })
    );
  });

  it('should navigate back to previous step', () => {
    // Move to step 1 first
    component.activeStep.set(1);
    expect(component.activeStep()).toBe(1);

    component.previousStep();

    expect(component.activeStep()).toBe(0);
  });

  it('should not navigate past the last step', () => {
    // Fill all required fields to make all steps valid
    fillValidForm();
    component.activeStep.set(3); // Last step (index 3 = step 4 of 4)

    component.nextStep();

    // activeStep should be clamped at steps.length - 1 = 3
    expect(component.activeStep()).toBe(3);
  });

  it('should not navigate before step 0', () => {
    component.activeStep.set(0);

    component.previousStep();

    expect(component.activeStep()).toBe(0);
  });

  // ─────────────────────── Form Submission: Create ───────────────────────

  it('should call TenderService.createTender on submit', fakeAsync(() => {
    const createdTender = { ...mockTender, id: 99 };
    tenderServiceSpy.createTender.and.returnValue(of(createdTender));
    fillValidForm();

    component.createTender();
    tick();

    expect(tenderServiceSpy.createTender).toHaveBeenCalled();
    const callArg = tenderServiceSpy.createTender.calls.mostRecent().args[0];
    expect(callArg.title).toBe('Test Tender');
    expect(callArg.reference).toBe('TND-TEST-001');
  }));

  it('should navigate to tender details after successful create', fakeAsync(() => {
    const createdTender = { ...mockTender, id: 99 };
    tenderServiceSpy.createTender.and.returnValue(of(createdTender));
    fillValidForm();

    component.createTender();
    tick();

    expect(messageServiceSpy.add).toHaveBeenCalledWith(
      jasmine.objectContaining({
        severity: 'success',
        summary: 'Success'
      })
    );

    // The component uses setTimeout(1000) before navigating
    tick(1000);

    expect(routerSpy.navigate).toHaveBeenCalledWith(['/tenders', 99]);
  }));

  it('should handle API error on submit', fakeAsync(() => {
    tenderServiceSpy.createTender.and.returnValue(
      throwError(() => ({ message: 'Server validation failed' }))
    );
    fillValidForm();

    component.createTender();
    tick();

    expect(component.saving()).toBeFalse();
    expect(messageServiceSpy.add).toHaveBeenCalledWith(
      jasmine.objectContaining({
        severity: 'error',
        summary: 'Error'
      })
    );
  }));

  it('should display validation errors when form is invalid on submit', () => {
    // Leave form invalid
    component.createTender();

    expect(tenderServiceSpy.createTender).not.toHaveBeenCalled();
    expect(messageServiceSpy.add).toHaveBeenCalledWith(
      jasmine.objectContaining({
        severity: 'error',
        summary: 'Validation Error'
      })
    );
  });

  // ─────────────────────── Cancel ───────────────────────

  it('should navigate to tender list on cancel', () => {
    component.onCancel();

    expect(routerSpy.navigate).toHaveBeenCalledWith(['/tenders']);
  });

  // ─────────────────────── Edit Mode ───────────────────────

  it('should populate form when editing existing tender', fakeAsync(() => {
    tenderServiceSpy.getTenderById.and.returnValue(of(mockTender));

    // Simulate route params with an ID to trigger edit mode
    paramsSubject.next({ id: '42' });
    tick();

    expect(component.isEditMode()).toBeTrue();
    expect(component.tenderId()).toBe(42);
    expect(component.tenderForm.get('title')?.value).toBe('IT Infrastructure Upgrade');
    expect(component.tenderForm.get('reference')?.value).toBe('TND-2026-0001');

    const criteriaArray = component.tenderForm.get('evaluationCriteria') as FormArray;
    expect(criteriaArray.length).toBe(mockTender.evaluationCriteria.length);
  }));

  it('should call TenderService.updateTender when editing', fakeAsync(() => {
    tenderServiceSpy.getTenderById.and.returnValue(of(mockTender));
    const updatedTender = { ...mockTender, title: 'Updated Tender' };
    tenderServiceSpy.updateTender.and.returnValue(of(updatedTender));

    // Enter edit mode
    paramsSubject.next({ id: '42' });
    tick();

    // Ensure form is valid and submit
    // The form was already populated from mockTender; ensure dates are valid
    const datesGroup = component.tenderForm.get('dates');
    if (!datesGroup?.get('submissionDeadline')?.value) {
      datesGroup?.patchValue({ submissionDeadline: new Date('2026-02-28') });
    }

    component.createTender();
    tick();

    expect(tenderServiceSpy.updateTender).toHaveBeenCalledWith(
      42,
      jasmine.objectContaining({ title: 'IT Infrastructure Upgrade' })
    );
    expect(tenderServiceSpy.createTender).not.toHaveBeenCalled();
  }));

  // ─────────────────────── Helpers ───────────────────────

  /**
   * Fills the form with valid data across all steps so the form passes
   * full validation and can be submitted.
   */
  function fillValidForm(): void {
    component.tenderForm.patchValue({
      title: 'Test Tender',
      reference: 'TND-TEST-001',
      clientId: 1,
      type: 'open',
      currency: 'AED',
      estimatedValue: 100000,
      bidValidityPeriod: 90,
      dates: {
        issueDate: new Date('2026-01-15'),
        submissionDeadline: new Date('2026-02-28')
      },
      technicalWeight: 70,
      commercialWeight: 30
    });
  }
});
