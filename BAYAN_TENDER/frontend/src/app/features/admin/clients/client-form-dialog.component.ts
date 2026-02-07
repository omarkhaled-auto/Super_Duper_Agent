import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { DynamicDialogRef, DynamicDialogConfig } from 'primeng/dynamicdialog';
import { InputTextModule } from 'primeng/inputtext';
import { InputTextarea } from 'primeng/inputtextarea';
import { CheckboxModule } from 'primeng/checkbox';
import { ButtonModule } from 'primeng/button';
import { MessageModule } from 'primeng/message';
import { DividerModule } from 'primeng/divider';
import { Client, CreateClientDto, UpdateClientDto } from '../../../core/models/client.model';
import { ClientService } from '../../../core/services/client.service';

export interface ClientFormDialogData {
  client?: Client;
  mode: 'create' | 'edit';
}

@Component({
  selector: 'app-client-form-dialog',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    InputTextModule,
    InputTextarea,
    CheckboxModule,
    ButtonModule,
    MessageModule,
    DividerModule
  ],
  template: `
    <div class="client-form-dialog">
      @if (errorMessage()) {
        <p-message severity="error" [text]="errorMessage()!" styleClass="w-full mb-3"></p-message>
      }

      <form [formGroup]="clientForm" (ngSubmit)="onSubmit()">
        <h4>Basic Information</h4>
        <div class="form-grid">
          <div class="form-field">
            <label for="name">Company Name (English) <span class="required">*</span></label>
            <input
              pInputText
              id="name"
              formControlName="name"
              placeholder="Enter company name"
              class="w-full"
              [class.ng-invalid]="isFieldInvalid('name')"
              data-testid="client-form-name"
            />
            @if (isFieldInvalid('name')) {
              <small class="p-error">Company name is required</small>
            }
          </div>

          <div class="form-field">
            <label for="nameAr">Company Name (Arabic)</label>
            <input
              pInputText
              id="nameAr"
              formControlName="nameAr"
              placeholder="Enter Arabic name"
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
              placeholder="Enter email address"
              class="w-full"
              [class.ng-invalid]="isFieldInvalid('email')"
            />
            @if (isFieldInvalid('email')) {
              <small class="p-error">
                @if (clientForm.get('email')?.errors?.['required']) {
                  Email is required
                }
                @if (clientForm.get('email')?.errors?.['email']) {
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
              placeholder="Enter phone number"
              class="w-full"
            />
          </div>
        </div>

        <p-divider></p-divider>

        <h4>Registration Details</h4>
        <div class="form-grid">
          <div class="form-field">
            <label for="crNumber">CR Number</label>
            <input
              pInputText
              id="crNumber"
              formControlName="crNumber"
              placeholder="Commercial Registration Number"
              class="w-full"
            />
          </div>

          <div class="form-field">
            <label for="vatNumber">VAT Number</label>
            <input
              pInputText
              id="vatNumber"
              formControlName="vatNumber"
              placeholder="VAT Registration Number"
              class="w-full"
            />
          </div>
        </div>

        <p-divider></p-divider>

        <h4>Address</h4>
        <div class="form-grid">
          <div class="form-field full-width">
            <label for="address">Address</label>
            <textarea
              pInputTextarea
              id="address"
              formControlName="address"
              placeholder="Enter full address"
              rows="2"
              class="w-full"
            ></textarea>
          </div>

          <div class="form-field">
            <label for="city">City</label>
            <input
              pInputText
              id="city"
              formControlName="city"
              placeholder="Enter city"
              class="w-full"
            />
          </div>

          <div class="form-field">
            <label for="country">Country</label>
            <input
              pInputText
              id="country"
              formControlName="country"
              placeholder="Enter country"
              class="w-full"
            />
          </div>
        </div>

        <p-divider></p-divider>

        <h4>Contact Person</h4>
        <div class="form-grid">
          <div class="form-field">
            <label for="contactPerson">Contact Name</label>
            <input
              pInputText
              id="contactPerson"
              formControlName="contactPerson"
              placeholder="Enter contact person name"
              class="w-full"
            />
          </div>

          <div class="form-field">
            <label for="contactEmail">Contact Email</label>
            <input
              pInputText
              id="contactEmail"
              type="email"
              formControlName="contactEmail"
              placeholder="Enter contact email"
              class="w-full"
            />
          </div>

          <div class="form-field">
            <label for="contactPhone">Contact Phone</label>
            <input
              pInputText
              id="contactPhone"
              formControlName="contactPhone"
              placeholder="Enter contact phone"
              class="w-full"
            />
          </div>

          <div class="form-field checkbox-field">
            <p-checkbox
              formControlName="isActive"
              [binary]="true"
              inputId="isActive"
            ></p-checkbox>
            <label for="isActive">Active Client</label>
          </div>
        </div>

        <div class="dialog-actions">
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
            [label]="isCreateMode() ? 'Create Client' : 'Update Client'"
            [loading]="isLoading()"
            [disabled]="clientForm.invalid || isLoading()"
            data-testid="client-form-save"
          ></button>
        </div>
      </form>
    </div>
  `,
  styles: [`
    .client-form-dialog {
      min-width: 600px;
      max-height: 70vh;
      overflow-y: auto;
    }

    h4 {
      margin: 0 0 1rem;
      font-size: 1rem;
      color: #333;
      font-weight: 600;
    }

    .form-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
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
      color: #333;
    }

    .required {
      color: #ef4444;
    }

    .checkbox-field {
      flex-direction: row;
      align-items: center;
    }

    .checkbox-field label {
      margin-left: 0.5rem;
      cursor: pointer;
    }

    .dialog-actions {
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
      margin-top: 1.5rem;
      padding-top: 1rem;
      border-top: 1px solid #e0e0e0;
    }

    .p-error {
      display: block;
      margin-top: 0.25rem;
    }

    :host ::ng-deep {
      .p-inputtext,
      .p-inputtextarea {
        width: 100%;
      }

      .p-divider {
        margin: 1rem 0;
      }
    }
  `]
})
export class ClientFormDialogComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly clientService = inject(ClientService);
  private readonly dialogRef = inject(DynamicDialogRef);
  private readonly dialogConfig = inject(DynamicDialogConfig);

  clientForm!: FormGroup;
  isLoading = this.clientService.isLoading;
  errorMessage = signal<string | null>(null);

  isCreateMode = computed(() => this.dialogConfig.data?.mode === 'create');

  ngOnInit(): void {
    this.initForm();
  }

  private initForm(): void {
    const data = this.dialogConfig.data as ClientFormDialogData | undefined;
    const client = data?.client;

    this.clientForm = this.fb.group({
      name: [client?.name || '', Validators.required],
      nameAr: [client?.nameAr || ''],
      email: [client?.email || '', [Validators.required, Validators.email]],
      phone: [client?.phone || ''],
      crNumber: [client?.crNumber || ''],
      vatNumber: [client?.vatNumber || ''],
      address: [client?.address || ''],
      city: [client?.city || ''],
      country: [client?.country || 'Saudi Arabia'],
      contactPerson: [client?.contactPerson || ''],
      contactEmail: [client?.contactEmail || ''],
      contactPhone: [client?.contactPhone || ''],
      isActive: [client?.isActive ?? true]
    });
  }

  isFieldInvalid(field: string): boolean {
    const control = this.clientForm.get(field);
    return !!(control && control.invalid && (control.dirty || control.touched));
  }

  onSubmit(): void {
    if (this.clientForm.invalid) {
      this.clientForm.markAllAsTouched();
      return;
    }

    this.errorMessage.set(null);
    const formValue = this.clientForm.value;
    const data = this.dialogConfig.data as ClientFormDialogData | undefined;

    if (this.isCreateMode()) {
      const createDto: CreateClientDto = {
        name: formValue.name,
        nameAr: formValue.nameAr || undefined,
        email: formValue.email,
        phone: formValue.phone || undefined,
        crNumber: formValue.crNumber || undefined,
        vatNumber: formValue.vatNumber || undefined,
        address: formValue.address || undefined,
        city: formValue.city || undefined,
        country: formValue.country || undefined,
        contactPerson: formValue.contactPerson || undefined,
        contactEmail: formValue.contactEmail || undefined,
        contactPhone: formValue.contactPhone || undefined
      };

      this.clientService.createClient(createDto).subscribe({
        next: (client) => {
          this.dialogRef.close(client);
        },
        error: (error) => {
          this.errorMessage.set(error.message || 'Failed to create client');
        }
      });
    } else {
      const updateDto: UpdateClientDto = {
        name: formValue.name,
        nameAr: formValue.nameAr || undefined,
        email: formValue.email,
        phone: formValue.phone || undefined,
        crNumber: formValue.crNumber || undefined,
        vatNumber: formValue.vatNumber || undefined,
        address: formValue.address || undefined,
        city: formValue.city || undefined,
        country: formValue.country || undefined,
        contactPerson: formValue.contactPerson || undefined,
        contactEmail: formValue.contactEmail || undefined,
        contactPhone: formValue.contactPhone || undefined,
        isActive: formValue.isActive
      };

      this.clientService.updateClient(data!.client!.id, updateDto).subscribe({
        next: (client) => {
          this.dialogRef.close(client);
        },
        error: (error) => {
          this.errorMessage.set(error.message || 'Failed to update client');
        }
      });
    }
  }

  onCancel(): void {
    this.dialogRef.close();
  }
}
