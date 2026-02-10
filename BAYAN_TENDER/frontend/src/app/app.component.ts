import { Component, inject, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';
import { PrimeNG } from 'primeng/config';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { ToastService } from './core/services/toast.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, ToastModule],
  providers: [MessageService],
  template: `
    <p-toast position="top-right" [life]="5000"></p-toast>
    <p-toast position="top-right" key="retryToast" [life]="10000">
      <ng-template let-message pTemplate="message">
        <div class="flex flex-column w-full">
          <div class="flex align-items-center gap-2">
            <i class="pi pi-exclamation-circle text-2xl"></i>
            <span class="font-bold">{{ message.summary }}</span>
          </div>
          <div class="mt-2">{{ message.detail }}</div>
          @if (message.data?.retryAction) {
            <div class="mt-3">
              <button
                class="p-button p-button-sm p-button-outlined"
                (click)="onRetry(message)"
              >
                <i class="pi pi-refresh mr-2"></i>
                Retry
              </button>
            </div>
          }
        </div>
      </ng-template>
    </p-toast>
    <router-outlet></router-outlet>
  `,
  styles: [`
    :host {
      display: block;
      min-height: 100vh;
    }

    :host ::ng-deep {
      .p-toast {
        z-index: 10000;
      }

      .p-toast-message-success {
        background: var(--bayan-success-bg, #f0fdf4);
        border: 1px solid var(--bayan-success, #22c55e);
        border-left-width: 4px;
        border-radius: 0.5rem;
      }

      .p-toast-message-info {
        background: var(--bayan-info-bg, #eff6ff);
        border: 1px solid var(--bayan-info, #3b82f6);
        border-left-width: 4px;
        border-radius: 0.5rem;
      }

      .p-toast-message-warn {
        background: var(--bayan-warning-bg, #fffbeb);
        border: 1px solid var(--bayan-warning, #f59e0b);
        border-left-width: 4px;
        border-radius: 0.5rem;
      }

      .p-toast-message-error {
        background: var(--bayan-danger-bg, #fef2f2);
        border: 1px solid var(--bayan-danger, #ef4444);
        border-left-width: 4px;
        border-radius: 0.5rem;
      }
    }
  `]
})
export class AppComponent implements OnInit {
  private readonly translate = inject(TranslateService);
  private readonly primeng = inject(PrimeNG);
  private readonly messageService = inject(MessageService);
  private readonly toastService = inject(ToastService);

  ngOnInit(): void {
    // Initialize toast service with the message service
    this.toastService.initialize(this.messageService);

    // Set available languages
    this.translate.addLangs(['en', 'ar']);
    this.translate.setDefaultLang('en');

    // Get saved language or use browser language
    const savedLang = localStorage.getItem('bayan_language');
    const browserLang = this.translate.getBrowserLang();
    const lang = savedLang || (browserLang?.match(/en|ar/) ? browserLang : 'en');

    this.translate.use(lang);

    // Set RTL for Arabic
    if (lang === 'ar') {
      document.documentElement.dir = 'rtl';
      document.documentElement.lang = 'ar';
    }

    // Enable ripple effect
    this.primeng.ripple.set(true);
  }

  onRetry(message: any): void {
    if (message.data?.retryAction) {
      message.data.retryAction();
      this.messageService.clear('retryToast');
    }
  }
}
