import { Component, EventEmitter, inject, Input, OnInit, Output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormGroup, FormControl, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { InputTextModule } from 'primeng/inputtext';
import { InputTextarea } from 'primeng/inputtextarea';
import { DropdownModule } from 'primeng/dropdown';
import { AutoCompleteModule, AutoCompleteCompleteEvent } from 'primeng/autocomplete';
import { RadioButtonModule } from 'primeng/radiobutton';
import { InputNumberModule } from 'primeng/inputnumber';
import { ButtonModule } from 'primeng/button';
import { EditorModule } from 'primeng/editor';
import { FloatLabelModule } from 'primeng/floatlabel';
import { DialogModule } from 'primeng/dialog';

import { ClientService } from '../../../core/services/client.service';
import { TenderService } from '../../../core/services/tender.service';
import { Client } from '../../../core/models/client.model';
import { TENDER_TYPE_OPTIONS, CURRENCY_OPTIONS } from '../../../core/models/tender.model';

@Component({
  selector: 'app-basic-info-step',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    InputTextModule,
    InputTextarea,
    DropdownModule,
    AutoCompleteModule,
    RadioButtonModule,
    InputNumberModule,
    ButtonModule,
    EditorModule,
    FloatLabelModule,
    DialogModule
  ],
  template: `
    <div class="basic-info-step">
      <div class="form-row">
        <div class="form-field full-width">
          <label for="title">Tender Title *</label>
          <div class="input-with-counter">
            <input
              pInputText
              id="title"
              [formControl]="titleControl"
              placeholder="Enter tender title"
              maxlength="500"
            />
            <span class="char-counter" [class.warning]="titleLength() > 450">
              {{ titleLength() }}/500
            </span>
          </div>
          @if (form.get('title')?.invalid && form.get('title')?.touched) {
            <small class="p-error">
              @if (form.get('title')?.errors?.['required']) {
                Tender title is required
              }
              @if (form.get('title')?.errors?.['maxlength']) {
                Title cannot exceed 500 characters
              }
            </small>
          }
        </div>
      </div>

      <div class="form-row two-columns">
        <div class="form-field">
          <label for="client">Client *</label>
          <div class="client-input">
            <p-autoComplete
              id="client"
              [formControl]="clientIdControl"
              [suggestions]="filteredClients()"
              (completeMethod)="searchClients($event)"
              field="name"
              [dropdown]="true"
              [forceSelection]="true"
              placeholder="Search or select client"
              styleClass="w-full"
              (onSelect)="onClientSelect($event)"
            >
              <ng-template let-client pTemplate="item">
                <div class="client-item">
                  <span>{{ client.name }}</span>
                  @if (client.city) {
                    <span class="client-location">{{ client.city }}</span>
                  }
                </div>
              </ng-template>
            </p-autoComplete>
            <button
              pButton
              type="button"
              icon="pi pi-plus"
              class="p-button-outlined add-client-btn"
              pTooltip="Add New Client"
              (click)="showAddClientDialog = true"
            ></button>
          </div>
          @if (form.get('clientId')?.invalid && form.get('clientId')?.touched) {
            <small class="p-error">Client is required</small>
          }
        </div>

        <div class="form-field">
          <label for="reference">Tender Reference *</label>
          <div class="reference-input">
            <input
              pInputText
              id="reference"
              [formControl]="referenceControl"
              placeholder="TND-YYYY-XXXX"
            />
            <button
              pButton
              type="button"
              icon="pi pi-sync"
              class="p-button-outlined"
              pTooltip="Auto-generate Reference"
              (click)="generateReference()"
              [loading]="generatingRef()"
            ></button>
          </div>
          @if (form.get('reference')?.invalid && form.get('reference')?.touched) {
            <small class="p-error">Reference is required</small>
          }
        </div>
      </div>

      <div class="form-row">
        <div class="form-field full-width">
          <label for="description">Description</label>
          <p-editor
            id="description"
            [formControl]="descriptionControl"
            [style]="{ height: '200px' }"
            placeholder="Enter detailed description of the tender..."
          >
            <ng-template pTemplate="header">
              <span class="ql-formats">
                <button type="button" class="ql-bold" aria-label="Bold"></button>
                <button type="button" class="ql-italic" aria-label="Italic"></button>
                <button type="button" class="ql-underline" aria-label="Underline"></button>
              </span>
              <span class="ql-formats">
                <button type="button" class="ql-list" value="ordered" aria-label="Ordered List"></button>
                <button type="button" class="ql-list" value="bullet" aria-label="Unordered List"></button>
              </span>
              <span class="ql-formats">
                <button type="button" class="ql-link" aria-label="Link"></button>
              </span>
            </ng-template>
          </p-editor>
        </div>
      </div>

      <div class="form-row">
        <div class="form-field full-width">
          <label>Tender Type *</label>
          <div class="tender-type-options">
            @for (type of tenderTypes; track type.value) {
              <div class="type-option" [class.selected]="form.get('type')?.value === type.value">
                <p-radioButton
                  [inputId]="'type-' + type.value"
                  [value]="type.value"
                  [formControl]="typeControl"
                ></p-radioButton>
                <label [for]="'type-' + type.value" class="type-label">
                  <span class="type-name">{{ type.label }}</span>
                  <span class="type-description">{{ type.description }}</span>
                </label>
              </div>
            }
          </div>
          @if (form.get('type')?.invalid && form.get('type')?.touched) {
            <small class="p-error">Tender type is required</small>
          }
        </div>
      </div>

      <div class="form-row two-columns">
        <div class="form-field">
          <label for="currency">Base Currency *</label>
          <p-dropdown
            id="currency"
            [options]="currencies"
            [formControl]="currencyControl"
            optionLabel="label"
            optionValue="value"
            placeholder="Select Currency"
            styleClass="w-full"
          >
            <ng-template let-currency pTemplate="item">
              <span>{{ currency.symbol }} - {{ currency.label }}</span>
            </ng-template>
            <ng-template let-currency pTemplate="selectedItem">
              <span>{{ currency.symbol }} - {{ currency.label }}</span>
            </ng-template>
          </p-dropdown>
          @if (form.get('currency')?.invalid && form.get('currency')?.touched) {
            <small class="p-error">Currency is required</small>
          }
        </div>

        <div class="form-field">
          <label for="bidValidity">Bid Validity Period (days)</label>
          <p-inputNumber
            id="bidValidity"
            [formControl]="bidValidityPeriodControl"
            [min]="1"
            [max]="365"
            placeholder="e.g., 90"
            styleClass="w-full"
            [showButtons]="true"
          ></p-inputNumber>
          <small class="field-hint">Number of days bids remain valid after submission deadline</small>
        </div>
      </div>

      <div class="form-row">
        <div class="form-field">
          <label for="estimatedValue">Estimated Value (optional)</label>
          <p-inputNumber
            id="estimatedValue"
            [formControl]="estimatedValueControl"
            mode="decimal"
            [minFractionDigits]="0"
            [maxFractionDigits]="2"
            placeholder="Enter estimated value"
            styleClass="w-full"
          ></p-inputNumber>
        </div>
      </div>
    </div>

    <!-- Add Client Dialog -->
    <p-dialog
      header="Add New Client"
      [(visible)]="showAddClientDialog"
      [modal]="true"
      [style]="{ width: '500px' }"
      [draggable]="false"
    >
      <div class="add-client-form">
        <div class="form-field">
          <label for="newClientName">Client Name *</label>
          <input
            pInputText
            id="newClientName"
            [(ngModel)]="newClientName"
            placeholder="Enter client name"
          />
        </div>
        <div class="form-field">
          <label for="newClientEmail">Email *</label>
          <input
            pInputText
            id="newClientEmail"
            [(ngModel)]="newClientEmail"
            type="email"
            placeholder="Enter email address"
          />
        </div>
      </div>
      <ng-template pTemplate="footer">
        <button
          pButton
          label="Cancel"
          class="p-button-text"
          (click)="showAddClientDialog = false"
        ></button>
        <button
          pButton
          label="Add Client"
          icon="pi pi-check"
          (click)="addNewClient()"
          [disabled]="!newClientName || !newClientEmail"
        ></button>
      </ng-template>
    </p-dialog>
  `,
  styles: [`
    .basic-info-step {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .form-row {
      display: flex;
      gap: 1.5rem;
    }

    .form-row.two-columns {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.5rem;
    }

    .form-field {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .form-field.full-width {
      width: 100%;
    }

    .form-field label {
      font-weight: 600;
      color: var(--bayan-foreground, #09090b);
      font-size: 0.9rem;
    }

    .input-with-counter {
      position: relative;
    }

    .input-with-counter input {
      width: 100%;
      padding-right: 70px;
    }

    .char-counter {
      position: absolute;
      right: 12px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 0.75rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .char-counter.warning {
      color: #f59e0b;
    }

    .client-input,
    .reference-input {
      display: flex;
      gap: 0.5rem;
    }

    .client-input :host ::ng-deep .p-autocomplete,
    .reference-input input {
      flex: 1;
    }

    .add-client-btn {
      flex-shrink: 0;
    }

    .client-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      width: 100%;
    }

    .client-location {
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .tender-type-options {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .type-option {
      display: flex;
      align-items: flex-start;
      gap: 0.75rem;
      padding: 1rem;
      border: 1px solid var(--bayan-border, #e4e4e7);
      border-radius: var(--bayan-radius, 0.5rem);
      cursor: pointer;
      transition: all 0.2s;
    }

    .type-option:hover {
      border-color: var(--bayan-primary, #18181b);
      background-color: var(--bayan-accent, #f4f4f5);
    }

    .type-option.selected {
      border-color: var(--bayan-primary, #18181b);
      background-color: var(--bayan-accent, #f4f4f5);
    }

    .type-label {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
      cursor: pointer;
    }

    .type-name {
      font-weight: 600;
      color: var(--bayan-foreground, #09090b);
    }

    .type-description {
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .field-hint {
      color: var(--bayan-muted-foreground, #71717a);
      font-size: 0.8rem;
    }

    :host ::ng-deep .w-full {
      width: 100%;
    }

    .add-client-form {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .add-client-form .form-field input {
      width: 100%;
    }

    @media (max-width: 768px) {
      .form-row.two-columns {
        grid-template-columns: 1fr;
      }
    }
  `]
})
export class BasicInfoStepComponent implements OnInit {
  @Input() form!: FormGroup;
  @Output() clientAdded = new EventEmitter<Client>();

  private readonly clientService = inject(ClientService);
  private readonly tenderService = inject(TenderService);

  clients = signal<Client[]>([]);
  filteredClients = signal<Client[]>([]);
  generatingRef = signal<boolean>(false);

  tenderTypes = TENDER_TYPE_OPTIONS;
  currencies = CURRENCY_OPTIONS;

  showAddClientDialog = false;
  newClientName = '';
  newClientEmail = '';

  titleLength = signal<number>(0);

  get titleControl(): FormControl { return this.form.get('title') as FormControl; }
  get clientIdControl(): FormControl { return this.form.get('clientId') as FormControl; }
  get referenceControl(): FormControl { return this.form.get('reference') as FormControl; }
  get descriptionControl(): FormControl { return this.form.get('description') as FormControl; }
  get typeControl(): FormControl { return this.form.get('type') as FormControl; }
  get currencyControl(): FormControl { return this.form.get('currency') as FormControl; }
  get bidValidityPeriodControl(): FormControl { return this.form.get('bidValidityPeriod') as FormControl; }
  get estimatedValueControl(): FormControl { return this.form.get('estimatedValue') as FormControl; }

  ngOnInit(): void {
    this.loadClients();
    this.setupTitleCounter();
  }

  private loadClients(): void {
    this.clientService.getClients({ pageSize: 100, isActive: true }).subscribe({
      next: (response) => {
        this.clients.set(response.items);
        this.filteredClients.set(response.items);
      }
    });
  }

  private setupTitleCounter(): void {
    const titleControl = this.form.get('title');
    if (titleControl) {
      this.titleLength.set(titleControl.value?.length || 0);
      titleControl.valueChanges.subscribe(value => {
        this.titleLength.set(value?.length || 0);
      });
    }
  }

  searchClients(event: AutoCompleteCompleteEvent): void {
    const query = event.query.toLowerCase();
    const filtered = this.clients().filter(client =>
      client.name.toLowerCase().includes(query) ||
      client.city?.toLowerCase().includes(query)
    );
    this.filteredClients.set(filtered);
  }

  onClientSelect(event: any): void {
    // The autocomplete returns the full client object
    // We need to set just the ID in the form
    if (event.value?.id) {
      this.form.patchValue({ clientId: event.value });
    }
  }

  generateReference(): void {
    this.generatingRef.set(true);
    this.tenderService.generateReference().subscribe({
      next: (reference) => {
        this.form.patchValue({ reference });
        this.generatingRef.set(false);
      },
      error: () => {
        this.generatingRef.set(false);
      }
    });
  }

  addNewClient(): void {
    if (!this.newClientName || !this.newClientEmail) return;

    this.clientService.createClient({
      name: this.newClientName,
      email: this.newClientEmail
    }).subscribe({
      next: (client) => {
        this.clients.update(clients => [...clients, client]);
        this.form.patchValue({ clientId: client });
        this.clientAdded.emit(client);
        this.showAddClientDialog = false;
        this.newClientName = '';
        this.newClientEmail = '';
      }
    });
  }
}
