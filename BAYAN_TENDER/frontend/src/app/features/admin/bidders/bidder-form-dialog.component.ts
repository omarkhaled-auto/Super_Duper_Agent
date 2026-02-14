import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { DynamicDialogRef, DynamicDialogConfig } from 'primeng/dynamicdialog';
import { InputTextModule } from 'primeng/inputtext';
import { InputTextarea } from 'primeng/inputtextarea';
import { DropdownModule } from 'primeng/dropdown';
import { MultiSelectModule } from 'primeng/multiselect';
import { ButtonModule } from 'primeng/button';
import { MessageModule } from 'primeng/message';
import { DividerModule } from 'primeng/divider';
import { TabViewModule } from 'primeng/tabview';
import {
  Bidder,
  CreateBidderDto,
  UpdateBidderDto,
  PrequalificationStatus,
  TradeSpecialization
} from '../../../core/models/bidder.model';
import { BidderService } from '../../../core/services/bidder.service';

export interface BidderFormDialogData {
  bidder?: Bidder;
  mode: 'create' | 'edit' | 'view';
}

@Component({
  selector: 'app-bidder-form-dialog',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    InputTextModule,
    InputTextarea,
    DropdownModule,
    MultiSelectModule,
    ButtonModule,
    MessageModule,
    DividerModule,
    TabViewModule
  ],
  template: `
    <div class="bidder-form-dialog">
      @if (errorMessage()) {
        <p-message severity="error" [text]="errorMessage()!" styleClass="w-full mb-3"></p-message>
      }

      <form [formGroup]="bidderForm" (ngSubmit)="onSubmit()">
        <p-tabView>
          <!-- Company Information Tab -->
          <p-tabPanel header="Company Info">
            <div class="form-grid">
              <div class="form-field">
                <label for="companyNameEn">Company Name (EN) <span class="required">*</span></label>
                <input
                  pInputText
                  id="companyNameEn"
                  formControlName="companyNameEn"
                  placeholder="Enter company name in English"
                  class="w-full"
                  [class.ng-invalid]="isFieldInvalid('companyNameEn')"
                  data-testid="bidder-form-name"
                />
                @if (isFieldInvalid('companyNameEn')) {
                  <small class="p-error">Company name (English) is required</small>
                }
              </div>

              <div class="form-field">
                <label for="companyNameAr">Company Name (AR)</label>
                <input
                  pInputText
                  id="companyNameAr"
                  formControlName="companyNameAr"
                  placeholder="Enter company name in Arabic"
                  class="w-full"
                  dir="rtl"
                />
              </div>

              <div class="form-field">
                <label for="email">Email <span class="required">*</span></label>
                <input
                  pInputText
                  id="email"
                  type="email"
                  formControlName="email"
                  placeholder="Enter company email"
                  class="w-full"
                  [class.ng-invalid]="isFieldInvalid('email')"
                />
                @if (isFieldInvalid('email')) {
                  <small class="p-error">
                    @if (bidderForm.get('email')?.errors?.['required']) {
                      Email is required
                    }
                    @if (bidderForm.get('email')?.errors?.['email']) {
                      Please enter a valid email
                    }
                  </small>
                }
              </div>

              <div class="form-field">
                <label for="phone">Phone</label>
                <input
                  pInputText
                  id="phone"
                  formControlName="phone"
                  placeholder="+966 XX XXX XXXX"
                  class="w-full"
                />
              </div>

              <div class="form-field">
                <label for="crNumber">CR Number</label>
                <input
                  pInputText
                  id="crNumber"
                  formControlName="crNumber"
                  placeholder="Commercial Registration Number"
                  class="w-full"
                />
                @if (bidderForm.get('crNumber')?.errors?.['crNumberExists']) {
                  <small class="p-error">This CR Number is already registered</small>
                }
              </div>

              <div class="form-field">
                <label for="tradeSpecializations">Trade Specialization <span class="required">*</span></label>
                <p-multiSelect
                  id="tradeSpecializations"
                  [options]="tradeOptions"
                  formControlName="tradeSpecializations"
                  placeholder="Select trade specializations"
                  [showClear]="true"
                  display="chip"
                  styleClass="w-full"
                  [class.ng-invalid]="isFieldInvalid('tradeSpecializations')"
                ></p-multiSelect>
                @if (isFieldInvalid('tradeSpecializations')) {
                  <small class="p-error">At least one trade specialization is required</small>
                }
              </div>

              <div class="form-field full-width">
                <label for="address">Address</label>
                <textarea
                  pInputTextarea
                  id="address"
                  formControlName="address"
                  placeholder="Enter company address"
                  class="w-full"
                  rows="3"
                ></textarea>
              </div>
            </div>
          </p-tabPanel>

          <!-- Status & Qualification Tab -->
          <p-tabPanel header="Status">
            <div class="form-grid">
              <div class="form-field">
                <label for="prequalificationStatus">Prequalification Status <span class="required">*</span></label>
                <p-dropdown
                  id="prequalificationStatus"
                  [options]="prequalificationOptions"
                  formControlName="prequalificationStatus"
                  placeholder="Select status"
                  styleClass="w-full"
                  [class.ng-invalid]="isFieldInvalid('prequalificationStatus')"
                ></p-dropdown>
                @if (isFieldInvalid('prequalificationStatus')) {
                  <small class="p-error">Prequalification status is required</small>
                }
              </div>

            </div>
          </p-tabPanel>

          <!-- Contact Person Tab -->
          <p-tabPanel header="Contact Person">
            <div class="form-grid">
              <div class="form-field full-width">
                <label for="contactPersonName">Contact Person Name</label>
                <input
                  pInputText
                  id="contactPersonName"
                  formControlName="contactPersonName"
                  placeholder="Enter contact person name"
                  class="w-full"
                />
              </div>

              <div class="form-field">
                <label for="contactPersonEmail">Contact Person Email</label>
                <input
                  pInputText
                  id="contactPersonEmail"
                  type="email"
                  formControlName="contactPersonEmail"
                  placeholder="Enter contact person email"
                  class="w-full"
                  [class.ng-invalid]="isFieldInvalid('contactPersonEmail')"
                />
                @if (isFieldInvalid('contactPersonEmail')) {
                  <small class="p-error">Please enter a valid email</small>
                }
              </div>

              <div class="form-field">
                <label for="contactPersonPhone">Contact Person Phone</label>
                <input
                  pInputText
                  id="contactPersonPhone"
                  formControlName="contactPersonPhone"
                  placeholder="+966 XX XXX XXXX"
                  class="w-full"
                />
              </div>
            </div>
          </p-tabPanel>
        </p-tabView>

        <p-divider></p-divider>

        <div class="dialog-actions">
          @if (isViewMode()) {
            <button
              pButton
              type="button"
              label="Close"
              class="p-button-text"
              (click)="onCancel()"
            ></button>
            <button
              pButton
              type="button"
              label="Edit"
              icon="pi pi-pencil"
              (click)="switchToEdit()"
            ></button>
          } @else {
            <button
              pButton
              type="button"
              label="Cancel"
              class="p-button-text"
              (click)="onCancel()"
            ></button>
            <button
              pButton
              type="submit"
              [label]="isCreateMode() ? 'Create Bidder' : 'Update Bidder'"
              [loading]="isLoading()"
              [disabled]="bidderForm.invalid || isLoading()"
              data-testid="bidder-form-save"
            ></button>
          }
        </div>
      </form>
    </div>
  `,
  styles: [`
    .bidder-form-dialog {
      min-width: 650px;
    }

    .form-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
      padding: 1rem 0;
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
      font-weight: 600;
      color: var(--bayan-foreground, #0F172A);
    }

    .required {
      color: var(--bayan-danger, #DC2626);
    }

    .dialog-actions {
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
      margin-top: 1rem;
    }

    .p-error {
      display: block;
      margin-top: 0.25rem;
    }

    :host ::ng-deep {
      .p-inputtext,
      .p-dropdown,
      .p-multiselect,
      .p-inputtextarea {
        width: 100%;
      }

      .p-tabview-panels,
      .p-tabpanels {
        padding: 0;
      }

      .p-tabview-nav,
      .p-tablist {
        justify-content: flex-start;
      }

      .p-tabview .p-tabview-nav li.p-highlight .p-tabview-nav-link,
      .p-tab.p-tab-active {
        border-color: var(--bayan-primary, #4F46E5);
        color: var(--bayan-primary, #4F46E5);
      }
    }
  `]
})
export class BidderFormDialogComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly bidderService = inject(BidderService);
  private readonly dialogRef = inject(DynamicDialogRef);
  private readonly dialogConfig = inject(DynamicDialogConfig);

  bidderForm!: FormGroup;
  isLoading = this.bidderService.isLoading;
  errorMessage = signal<string | null>(null);

  isCreateMode = computed(() => this.dialogConfig.data?.mode === 'create');
  isViewMode = signal(false);

  tradeOptions = [
    { label: 'IT Services', value: TradeSpecialization.IT_SERVICES },
    { label: 'Construction', value: TradeSpecialization.CONSTRUCTION },
    { label: 'Consulting', value: TradeSpecialization.CONSULTING },
    { label: 'Supplies', value: TradeSpecialization.SUPPLIES },
    { label: 'Maintenance', value: TradeSpecialization.MAINTENANCE },
    { label: 'Security', value: TradeSpecialization.SECURITY },
    { label: 'Logistics', value: TradeSpecialization.LOGISTICS },
    { label: 'Healthcare', value: TradeSpecialization.HEALTHCARE },
    { label: 'Education', value: TradeSpecialization.EDUCATION },
    { label: 'Financial', value: TradeSpecialization.FINANCIAL },
    { label: 'Engineering', value: TradeSpecialization.ENGINEERING },
    { label: 'Telecommunications', value: TradeSpecialization.TELECOMMUNICATIONS },
    { label: 'Other', value: TradeSpecialization.OTHER }
  ];

  prequalificationOptions = [
    { label: 'Pending', value: PrequalificationStatus.PENDING },
    { label: 'Approved', value: PrequalificationStatus.APPROVED },
    { label: 'Rejected', value: PrequalificationStatus.REJECTED }
  ];


  ngOnInit(): void {
    this.initForm();
  }

  private initForm(): void {
    const data = this.dialogConfig.data as BidderFormDialogData | undefined;
    const bidder = data?.bidder;

    this.bidderForm = this.fb.group({
      companyNameEn: [bidder?.companyNameEn || '', Validators.required],
      companyNameAr: [bidder?.companyNameAr || ''],
      email: [bidder?.email || '', [Validators.required, Validators.email]],
      phone: [bidder?.phone || ''],
      crNumber: [bidder?.crNumber || ''],
      address: [bidder?.address || ''],
      tradeSpecializations: [bidder?.tradeSpecializations || [], Validators.required],
      prequalificationStatus: [bidder?.prequalificationStatus || PrequalificationStatus.PENDING, Validators.required],
      contactPersonName: [bidder?.contactPersonName || ''],
      contactPersonEmail: [bidder?.contactPersonEmail || '', Validators.email],
      contactPersonPhone: [bidder?.contactPersonPhone || '']
    });

    if (data?.mode === 'view') {
      this.isViewMode.set(true);
      this.bidderForm.disable();
    }
  }

  switchToEdit(): void {
    this.isViewMode.set(false);
    this.bidderForm.enable();
  }

  isFieldInvalid(field: string): boolean {
    const control = this.bidderForm.get(field);
    return !!(control && control.invalid && (control.dirty || control.touched));
  }

  onSubmit(): void {
    if (this.isViewMode()) return;
    if (this.bidderForm.invalid) {
      this.bidderForm.markAllAsTouched();
      return;
    }

    this.errorMessage.set(null);
    const formValue = this.bidderForm.value;
    const data = this.dialogConfig.data as BidderFormDialogData | undefined;

    if (this.isCreateMode()) {
      const createDto: CreateBidderDto = {
        companyNameEn: formValue.companyNameEn,
        companyNameAr: formValue.companyNameAr || undefined,
        email: formValue.email,
        phone: formValue.phone || undefined,
        crNumber: formValue.crNumber || undefined,
        address: formValue.address || undefined,
        tradeSpecializations: formValue.tradeSpecializations,
        prequalificationStatus: formValue.prequalificationStatus,
        contactPersonName: formValue.contactPersonName || undefined,
        contactPersonEmail: formValue.contactPersonEmail || undefined,
        contactPersonPhone: formValue.contactPersonPhone || undefined
      };

      this.bidderService.createBidder(createDto).subscribe({
        next: (result) => {
          this.dialogRef.close(result);
        },
        error: (err) => {
          this.errorMessage.set(err.message || 'Failed to create bidder');
        }
      });
    } else {
      const updateDto: UpdateBidderDto = {
        companyNameEn: formValue.companyNameEn,
        companyNameAr: formValue.companyNameAr || undefined,
        email: formValue.email,
        phone: formValue.phone || undefined,
        crNumber: formValue.crNumber || undefined,
        address: formValue.address || undefined,
        tradeSpecializations: formValue.tradeSpecializations,
        prequalificationStatus: formValue.prequalificationStatus,
        contactPersonName: formValue.contactPersonName || undefined,
        contactPersonEmail: formValue.contactPersonEmail || undefined,
        contactPersonPhone: formValue.contactPersonPhone || undefined
      };

      this.bidderService.updateBidder(data!.bidder!.id, updateDto).subscribe({
        next: (result) => {
          this.dialogRef.close(result);
        },
        error: (err) => {
          this.errorMessage.set(err.message || 'Failed to update bidder');
        }
      });
    }
  }

  onCancel(): void {
    this.dialogRef.close();
  }
}
