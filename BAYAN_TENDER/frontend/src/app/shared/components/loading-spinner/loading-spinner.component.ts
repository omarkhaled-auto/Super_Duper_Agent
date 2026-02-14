import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ProgressSpinnerModule } from 'primeng/progressspinner';

@Component({
  selector: 'app-loading-spinner',
  standalone: true,
  imports: [CommonModule, ProgressSpinnerModule],
  template: `
    @if (overlay) {
      <div class="loading-overlay">
        <div class="spinner-container">
          <p-progressSpinner
            [style]="{ width: size + 'px', height: size + 'px' }"
            strokeWidth="4"
            animationDuration=".5s"
          />
          @if (message) {
            <p class="loading-message">{{ message }}</p>
          }
        </div>
      </div>
    } @else {
      <div class="spinner-inline">
        <p-progressSpinner
          [style]="{ width: size + 'px', height: size + 'px' }"
          strokeWidth="4"
          animationDuration=".5s"
        />
        @if (message) {
          <p class="loading-message">{{ message }}</p>
        }
      </div>
    }
  `,
  styles: [`
    .loading-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background-color: rgba(15, 23, 42, 0.6);
      backdrop-filter: blur(4px);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 9999;
    }

    .spinner-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1rem;
      background: var(--bayan-card, #ffffff);
      padding: 2rem;
      border-radius: var(--bayan-radius-lg, 0.75rem);
      border: 1px solid var(--bayan-border, #E2E8F0);
      box-shadow: var(--bayan-shadow-lg, 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -4px rgba(0,0,0,0.1));
    }

    .spinner-inline {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.5rem;
      padding: 1rem;
    }

    .loading-message {
      margin: 0;
      color: var(--bayan-slate-500, #64748B);
      font-size: 0.875rem;
    }

    .spinner-inline ::ng-deep .p-progress-spinner-svg circle {
      stroke: var(--bayan-slate-200, #E2E8F0);
    }

    :host ::ng-deep .p-progress-spinner-circle {
      stroke: var(--bayan-primary, #4F46E5) !important;
    }
  `]
})
export class LoadingSpinnerComponent {
  @Input() overlay = false;
  @Input() size = 50;
  @Input() message = '';
}
