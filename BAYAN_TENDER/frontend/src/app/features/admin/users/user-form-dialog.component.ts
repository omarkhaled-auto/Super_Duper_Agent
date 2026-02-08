import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { DynamicDialogRef, DynamicDialogConfig } from 'primeng/dynamicdialog';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { DropdownModule } from 'primeng/dropdown';
import { CheckboxModule } from 'primeng/checkbox';
import { ButtonModule } from 'primeng/button';
import { MessageModule } from 'primeng/message';
import { User, UserRole } from '../../../core/models/user.model';
import { UserService, CreateUserDto, UpdateUserDto } from '../../../core/services/user.service';

export interface UserFormDialogData {
  user?: User;
  mode: 'create' | 'edit';
}

@Component({
  selector: 'app-user-form-dialog',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    InputTextModule,
    PasswordModule,
    DropdownModule,
    CheckboxModule,
    ButtonModule,
    MessageModule
  ],
  template: `
    <div class="user-form-dialog">
      @if (errorMessage()) {
        <p-message severity="error" [text]="errorMessage()!" styleClass="w-full mb-3"></p-message>
      }

      <form [formGroup]="userForm" (ngSubmit)="onSubmit()">
        <div class="form-grid">
          <div class="form-field">
            <label for="firstName">First Name <span class="required">*</span></label>
            <input
              pInputText
              id="firstName"
              formControlName="firstName"
              placeholder="Enter first name"
              class="w-full"
              [class.ng-invalid]="isFieldInvalid('firstName')"
            />
            @if (isFieldInvalid('firstName')) {
              <small class="p-error">First name is required</small>
            }
          </div>

          <div class="form-field">
            <label for="lastName">Last Name <span class="required">*</span></label>
            <input
              pInputText
              id="lastName"
              formControlName="lastName"
              placeholder="Enter last name"
              class="w-full"
              [class.ng-invalid]="isFieldInvalid('lastName')"
            />
            @if (isFieldInvalid('lastName')) {
              <small class="p-error">Last name is required</small>
            }
          </div>

          <div class="form-field full-width">
            <label for="email">Email <span class="required">*</span></label>
            <input
              pInputText
              id="email"
              type="email"
              formControlName="email"
              placeholder="Enter email address"
              class="w-full"
              [class.ng-invalid]="isFieldInvalid('email')"
              data-testid="user-form-email"
            />
            @if (isFieldInvalid('email')) {
              <small class="p-error">
                @if (userForm.get('email')?.errors?.['required']) {
                  Email is required
                }
                @if (userForm.get('email')?.errors?.['email']) {
                  Please enter a valid email
                }
              </small>
            }
          </div>

          @if (isCreateMode()) {
            <div class="form-field full-width">
              <label for="password">Password <span class="required">*</span></label>
              <p-password
                id="password"
                formControlName="password"
                placeholder="Enter password"
                [toggleMask]="true"
                [feedback]="true"
                styleClass="w-full"
                inputStyleClass="w-full"
                [class.ng-invalid]="isFieldInvalid('password')"
              ></p-password>
              @if (isFieldInvalid('password')) {
                <small class="p-error">
                  @if (userForm.get('password')?.errors?.['required']) {
                    Password is required
                  }
                  @if (userForm.get('password')?.errors?.['minlength']) {
                    Password must be at least 8 characters
                  }
                </small>
              }
            </div>
          }

          <div class="form-field">
            <label for="role">Role <span class="required">*</span></label>
            <p-dropdown
              id="role"
              [options]="roleOptions"
              formControlName="role"
              placeholder="Select role"
              styleClass="w-full"
              [class.ng-invalid]="isFieldInvalid('role')"
            ></p-dropdown>
            @if (isFieldInvalid('role')) {
              <small class="p-error">Role is required</small>
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

          <div class="form-field full-width">
            <label for="company">Company</label>
            <input
              pInputText
              id="company"
              formControlName="company"
              placeholder="Enter company name"
              class="w-full"
            />
          </div>

          <div class="form-field full-width checkbox-field">
            <p-checkbox
              formControlName="isActive"
              [binary]="true"
              inputId="isActive"
            ></p-checkbox>
            <label for="isActive">Active User</label>
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
            [label]="isCreateMode() ? 'Create User' : 'Update User'"
            [loading]="isLoading()"
            [disabled]="userForm.invalid || isLoading()"
            data-testid="user-form-save"
          ></button>
        </div>
      </form>
    </div>
  `,
  styles: [`
    .user-form-dialog {
      min-width: 500px;
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
      font-weight: 600;
      color: var(--bayan-foreground, #09090b);
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
      border-top: 1px solid var(--bayan-border, #e4e4e7);
    }

    .p-error {
      display: block;
      margin-top: 0.25rem;
    }

    :host ::ng-deep {
      .p-inputtext,
      .p-dropdown,
      .p-password {
        width: 100%;
      }
    }
  `]
})
export class UserFormDialogComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly userService = inject(UserService);
  private readonly dialogRef = inject(DynamicDialogRef);
  private readonly dialogConfig = inject(DynamicDialogConfig);

  userForm!: FormGroup;
  isLoading = this.userService.isLoading;
  errorMessage = signal<string | null>(null);

  isCreateMode = computed(() => this.dialogConfig.data?.mode === 'create');

  roleOptions = [
    { label: 'Admin', value: UserRole.ADMIN },
    { label: 'Tender Manager', value: UserRole.TENDER_MANAGER },
    { label: 'Commercial Analyst', value: UserRole.COMMERCIAL_ANALYST },
    { label: 'Technical Panelist', value: UserRole.TECHNICAL_PANELIST },
    { label: 'Approver', value: UserRole.APPROVER },
    { label: 'Auditor', value: UserRole.AUDITOR },
    { label: 'Bidder', value: UserRole.BIDDER },
    { label: 'Viewer', value: UserRole.VIEWER }
  ];

  ngOnInit(): void {
    this.initForm();
  }

  private initForm(): void {
    const data = this.dialogConfig.data as UserFormDialogData | undefined;
    const user = data?.user;

    this.userForm = this.fb.group({
      firstName: [user?.firstName || '', Validators.required],
      lastName: [user?.lastName || '', Validators.required],
      email: [user?.email || '', [Validators.required, Validators.email]],
      password: ['', this.isCreateMode() ? [Validators.required, Validators.minLength(8)] : []],
      role: [user?.role || null, Validators.required],
      phone: [user?.phone || ''],
      company: [user?.company || ''],
      isActive: [user?.isActive ?? true]
    });
  }

  isFieldInvalid(field: string): boolean {
    const control = this.userForm.get(field);
    return !!(control && control.invalid && (control.dirty || control.touched));
  }

  onSubmit(): void {
    if (this.userForm.invalid) {
      this.userForm.markAllAsTouched();
      return;
    }

    this.errorMessage.set(null);
    const formValue = this.userForm.value;
    const data = this.dialogConfig.data as UserFormDialogData | undefined;

    if (this.isCreateMode()) {
      const createDto: CreateUserDto = {
        firstName: formValue.firstName,
        lastName: formValue.lastName,
        email: formValue.email,
        password: formValue.password,
        role: formValue.role,
        phone: formValue.phone || undefined,
        company: formValue.company || undefined,
        isActive: formValue.isActive
      };

      this.userService.createUser(createDto).subscribe({
        next: (user) => {
          this.dialogRef.close(user);
        },
        error: (error) => {
          this.errorMessage.set(error.message || 'Failed to create user');
        }
      });
    } else {
      const updateDto: UpdateUserDto = {
        firstName: formValue.firstName,
        lastName: formValue.lastName,
        email: formValue.email,
        role: formValue.role,
        phone: formValue.phone || undefined,
        company: formValue.company || undefined,
        isActive: formValue.isActive
      };

      this.userService.updateUser(data!.user!.id, updateDto).subscribe({
        next: (user) => {
          this.dialogRef.close(user);
        },
        error: (error) => {
          this.errorMessage.set(error.message || 'Failed to update user');
        }
      });
    }
  }

  onCancel(): void {
    this.dialogRef.close();
  }
}
