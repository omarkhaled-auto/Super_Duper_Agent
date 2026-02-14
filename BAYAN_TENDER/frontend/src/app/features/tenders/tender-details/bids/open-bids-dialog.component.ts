import {
  Component,
  Input,
  Output,
  EventEmitter
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DialogModule } from 'primeng/dialog';
import { ButtonModule } from 'primeng/button';
import { CheckboxModule } from 'primeng/checkbox';
import { MessageModule } from 'primeng/message';

@Component({
  selector: 'app-open-bids-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    DialogModule,
    ButtonModule,
    CheckboxModule,
    MessageModule
  ],
  template: `
    <p-dialog
      header="Open Bids"
      [(visible)]="visible"
      (visibleChange)="visibleChange.emit($event)"
      [modal]="true"
      [style]="{ width: '500px' }"
      [draggable]="false"
      [resizable]="false"
      [closable]="true"
    >
      <div class="dialog-content">
        <!-- Warning Message -->
        <p-message
          severity="warn"
          styleClass="w-full mb-3"
        >
          <ng-template pTemplate="content">
            <div class="warning-content">
              <i class="pi pi-exclamation-triangle"></i>
              <span>
                <strong>This action is IRREVERSIBLE.</strong><br>
                All bid amounts will be revealed and cannot be hidden again.
              </span>
            </div>
          </ng-template>
        </p-message>

        <!-- Info Section -->
        <div class="info-section">
          <p>You are about to open <strong>{{ bidsCount }}</strong> bid(s).</p>
          <p>Once opened:</p>
          <ul>
            <li>All bid amounts will become visible to authorized users</li>
            <li>The opening timestamp will be recorded</li>
            <li>This action will be logged in the audit trail</li>
            <li>You cannot undo this action</li>
          </ul>
        </div>

        <!-- Confirmation Checkbox -->
        <div class="confirmation-checkbox">
          <p-checkbox
            [(ngModel)]="confirmationChecked"
            [binary]="true"
            inputId="confirmOpen"
          ></p-checkbox>
          <label for="confirmOpen" class="confirmation-label">
            I understand this action cannot be undone
          </label>
        </div>
      </div>

      <!-- Dialog Footer -->
      <ng-template pTemplate="footer">
        <div class="dialog-footer">
          <button
            pButton
            label="Cancel"
            class="p-button-text"
            (click)="onCancel()"
          ></button>
          <button
            pButton
            label="Confirm Open Bids"
            icon="pi pi-lock-open"
            class="p-button-primary"
            data-testid="confirm-open-bids-btn"
            [disabled]="!confirmationChecked"
            (click)="onConfirm()"
          ></button>
        </div>
      </ng-template>
    </p-dialog>
  `,
  styles: [`
    .dialog-content {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .warning-content {
      display: flex;
      align-items: flex-start;
      gap: 0.75rem;
    }

    .warning-content i {
      font-size: 3rem;
      color: var(--bayan-warning, #D97706);
      flex-shrink: 0;
    }

    .warning-content span {
      line-height: 1.5;
      color: var(--bayan-slate-700, #334155);
    }

    .info-section {
      padding: 1rem;
      background-color: var(--bayan-slate-50, #F8FAFC);
      border-radius: var(--bayan-radius, 0.5rem);
      border: 1px solid var(--bayan-slate-200, #E2E8F0);
    }

    .info-section p {
      margin: 0 0 0.5rem;
      color: var(--bayan-slate-700, #334155);
    }

    .info-section ul {
      margin: 0;
      padding-left: 1.5rem;
      color: var(--bayan-slate-500, #64748B);
    }

    .info-section li {
      margin-bottom: 0.25rem;
    }

    .confirmation-checkbox {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 1rem;
      background-color: #FFFBEB;
      border: 1px solid var(--bayan-warning, #D97706);
      border-radius: var(--bayan-radius, 0.5rem);
    }

    .confirmation-label {
      font-weight: 500;
      color: var(--bayan-slate-900, #0F172A);
      cursor: pointer;
    }

    .dialog-footer {
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
    }
  `]
})
export class OpenBidsDialogComponent {
  @Input() visible = false;
  @Input() bidsCount = 0;

  @Output() visibleChange = new EventEmitter<boolean>();
  @Output() confirmed = new EventEmitter<void>();

  confirmationChecked = false;

  onCancel(): void {
    this.confirmationChecked = false;
    this.visibleChange.emit(false);
  }

  onConfirm(): void {
    if (this.confirmationChecked) {
      this.confirmed.emit();
      this.confirmationChecked = false;
    }
  }
}
