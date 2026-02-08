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
      background-color: rgba(0, 0, 0, 0.5);
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
      background: white;
      padding: 2rem;
      border-radius: var(--bayan-radius, 0.5rem);
      box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
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
      color: var(--bayan-foreground, #09090b);
      font-size: 0.875rem;
    }

    :host ::ng-deep .p-progress-spinner-circle {
      stroke: var(--bayan-primary, #18181b) !important;
    }
  `]
})
export class LoadingSpinnerComponent {
  @Input() overlay = false;
  @Input() size = 50;
  @Input() message = '';
}
