import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnChanges,
  SimpleChanges
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DialogModule } from 'primeng/dialog';
import { ButtonModule } from 'primeng/button';
import { InputTextarea } from 'primeng/inputtextarea';
import { MessageModule } from 'primeng/message';

@Component({
  selector: 'app-late-bid-rejection-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    DialogModule,
    ButtonModule,
    InputTextarea,
    MessageModule
  ],
  template: `
    <p-dialog
      header="Reject Late Bid"
      [(visible)]="visible"
      (visibleChange)="onVisibleChange($event)"
      [modal]="true"
      [style]="{ width: '500px' }"
      [draggable]="false"
      [resizable]="false"
      [closable]="true"
    >
      <div class="dialog-content">
        <!-- Info Message -->
        <p-message
          severity="warn"
          styleClass="w-full mb-3"
        >
          <ng-template pTemplate="content">
            <div class="warning-content">
              <i class="pi pi-exclamation-triangle"></i>
              <span>
                You are about to reject the late bid from <strong>{{ bidderName }}</strong>.
                This action cannot be undone.
              </span>
            </div>
          </ng-template>
        </p-message>

        <!-- Reason Textarea -->
        <div class="form-field">
          <label for="rejectionReason">
            Reason for Rejection <span class="required">*</span>
          </label>
          <textarea
            pInputTextarea
            id="rejectionReason"
            [(ngModel)]="reason"
            [rows]="4"
            [autoResize]="true"
            class="w-full"
            placeholder="Enter the reason for rejecting this late bid..."
          ></textarea>
          @if (showError && !reason.trim()) {
            <small class="p-error">Reason is required</small>
          }
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
            label="Reject Bid"
            icon="pi pi-times"
            class="p-button-danger"
            [disabled]="!reason.trim()"
            (click)="onReject()"
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
      font-size: 1.25rem;
      color: #ef6c00;
      flex-shrink: 0;
    }

    .warning-content span {
      line-height: 1.5;
    }

    .form-field {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .form-field label {
      font-weight: 500;
      color: #333;
    }

    .required {
      color: #ef4444;
    }

    .dialog-footer {
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
    }
  `]
})
export class LateBidRejectionDialogComponent implements OnChanges {
  @Input() visible = false;
  @Input() bidderName = '';

  @Output() visibleChange = new EventEmitter<boolean>();
  @Output() rejected = new EventEmitter<string>();

  reason = '';
  showError = false;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['visible'] && this.visible) {
      // Reset form when dialog opens
      this.reason = '';
      this.showError = false;
    }
  }

  onVisibleChange(visible: boolean): void {
    if (!visible) {
      this.reason = '';
      this.showError = false;
    }
    this.visibleChange.emit(visible);
  }

  onCancel(): void {
    this.reason = '';
    this.showError = false;
    this.visibleChange.emit(false);
  }

  onReject(): void {
    if (!this.reason.trim()) {
      this.showError = true;
      return;
    }

    this.rejected.emit(this.reason.trim());
  }
}
