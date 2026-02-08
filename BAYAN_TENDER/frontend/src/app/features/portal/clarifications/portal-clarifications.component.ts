import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TabViewModule } from 'primeng/tabview';
import { AccordionModule } from 'primeng/accordion';
import { TagModule } from 'primeng/tag';
import { TableModule } from 'primeng/table';
import { TooltipModule } from 'primeng/tooltip';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageModule } from 'primeng/message';
import { DividerModule } from 'primeng/divider';
import { ToastModule } from 'primeng/toast';
import { DialogService, DynamicDialog } from 'primeng/dynamicdialog';
import { MessageService } from 'primeng/api';
import { forkJoin } from 'rxjs';
import { PortalService } from '../../../core/services/portal.service';
import { PortalClarification, PortalBulletin } from '../../../core/models/portal.model';
import { SubmitQuestionDialogComponent } from './submit-question-dialog.component';

@Component({
  selector: 'app-portal-clarifications',
  standalone: true,
  imports: [
    CommonModule,
    CardModule,
    ButtonModule,
    TabViewModule,
    AccordionModule,
    TagModule,
    TableModule,
    TooltipModule,
    ProgressSpinnerModule,
    MessageModule,
    DividerModule,
    ToastModule,
    DynamicDialog
  ],
  providers: [DialogService, MessageService],
  template: `
    <div class="portal-clarifications">
      <!-- Loading State -->
      @if (isLoading()) {
        <div class="loading-container">
          <p-progressSpinner></p-progressSpinner>
          <p>Loading clarifications...</p>
        </div>
      }

      <!-- Error State -->
      @if (error()) {
        <p-message severity="error" [text]="error()!" styleClass="w-full mb-4"></p-message>
      }

      @if (!isLoading() && !error()) {
        <!-- Header with Submit Button -->
        <div class="page-header">
          <div class="header-info">
            <h2>Clarifications & Q&A</h2>
            <p>View published Q&A bulletins and submit your questions</p>
          </div>
          <div class="header-actions">
            @if (!isClarificationDeadlinePassed()) {
              <button
                pButton
                label="Submit Question"
                icon="pi pi-plus"
                (click)="openSubmitQuestionDialog()"
              ></button>
            } @else {
              <p-tag
                severity="warn"
                value="Clarification Period Closed"
                icon="pi pi-clock"
              ></p-tag>
            }
          </div>
        </div>

        <p-tabView>
          <!-- Published Bulletins Tab -->
          <p-tabPanel header="Q&A Bulletins">
            <ng-template pTemplate="header">
              <i class="pi pi-file-pdf mr-2"></i>
              <span>Q&A Bulletins</span>
              @if (bulletins().length > 0) {
                <p-tag [value]="bulletins().length.toString()" severity="info" class="ml-2"></p-tag>
              }
            </ng-template>

            @if (bulletins().length === 0) {
              <div class="empty-state">
                <i class="pi pi-inbox"></i>
                <p>No Q&A bulletins have been published yet.</p>
                <small>Check back later for published clarifications.</small>
              </div>
            } @else {
              <p-accordion [multiple]="true" [activeIndex]="[0]">
                @for (bulletin of bulletins(); track bulletin.id) {
                  <p-accordionTab>
                    <ng-template pTemplate="header">
                      <div class="bulletin-header">
                        <div class="bulletin-info">
                          <strong>Bulletin #{{ bulletin.bulletinNumber }}</strong>
                          <span class="bulletin-date">
                            Issued: {{ bulletin.issueDate | date:'mediumDate' }}
                          </span>
                        </div>
                        <div class="bulletin-meta">
                          <p-tag
                            [value]="bulletin.clarifications.length + ' Q&A'"
                            severity="secondary"
                          ></p-tag>
                          @if (bulletin.pdfUrl) {
                            <button
                              pButton
                              icon="pi pi-download"
                              class="p-button-sm p-button-text"
                              pTooltip="Download PDF"
                              tooltipPosition="top"
                              (click)="downloadBulletinPdf(bulletin, $event)"
                            ></button>
                          }
                        </div>
                      </div>
                    </ng-template>

                    @if (bulletin.title || bulletin.introduction) {
                      <div class="bulletin-intro">
                        @if (bulletin.title) {
                          <h4>{{ bulletin.title }}</h4>
                        }
                        @if (bulletin.introduction) {
                          <p>{{ bulletin.introduction }}</p>
                        }
                      </div>
                      <p-divider></p-divider>
                    }

                    <div class="qa-list">
                      @for (qa of bulletin.clarifications; track qa.id; let i = $index) {
                        <div class="qa-item">
                          <div class="qa-number">Q{{ i + 1 }}</div>
                          <div class="qa-content">
                            <div class="qa-question">
                              <strong>{{ qa.subject }}</strong>
                              <p>{{ qa.question }}</p>
                              @if (qa.relatedBoqSectionTitle) {
                                <span class="boq-ref">
                                  <i class="pi pi-link"></i>
                                  {{ qa.relatedBoqSectionTitle }}
                                </span>
                              }
                            </div>
                            <div class="qa-answer">
                              <span class="answer-label">Answer:</span>
                              <p>{{ qa.answer }}</p>
                            </div>
                          </div>
                        </div>
                      }
                    </div>
                  </p-accordionTab>
                }
              </p-accordion>
            }
          </p-tabPanel>

          <!-- My Questions Tab -->
          <p-tabPanel header="My Questions">
            <ng-template pTemplate="header">
              <i class="pi pi-send mr-2"></i>
              <span>My Questions</span>
              @if (myClarifications().length > 0) {
                <p-tag [value]="myClarifications().length.toString()" severity="info" class="ml-2"></p-tag>
              }
            </ng-template>

            @if (myClarifications().length === 0) {
              <div class="empty-state">
                <i class="pi pi-comments"></i>
                <p>You haven't submitted any questions yet.</p>
                @if (!isClarificationDeadlinePassed()) {
                  <button
                    pButton
                    label="Submit Your First Question"
                    icon="pi pi-plus"
                    class="p-button-outlined mt-3"
                    (click)="openSubmitQuestionDialog()"
                  ></button>
                }
              </div>
            } @else {
              <p-table
                [value]="myClarifications()"
                [tableStyle]="{ 'min-width': '50rem' }"
                styleClass="p-datatable-sm"
              >
                <ng-template pTemplate="header">
                  <tr>
                    <th style="width: 15%">Reference</th>
                    <th style="width: 35%">Subject</th>
                    <th style="width: 15%">Status</th>
                    <th style="width: 20%">Submitted</th>
                    <th style="width: 15%">Actions</th>
                  </tr>
                </ng-template>
                <ng-template pTemplate="body" let-clarification>
                  <tr>
                    <td>
                      <span class="reference-code">{{ clarification.referenceNumber }}</span>
                    </td>
                    <td>
                      <span
                        class="subject-text"
                        [pTooltip]="clarification.subject"
                        tooltipPosition="top"
                      >
                        {{ clarification.subject }}
                      </span>
                    </td>
                    <td>
                      <p-tag
                        [value]="getStatusLabel(clarification.status)"
                        [severity]="getStatusSeverity(clarification.status)"
                      ></p-tag>
                    </td>
                    <td>{{ clarification.submittedAt | date:'medium' }}</td>
                    <td>
                      <button
                        pButton
                        icon="pi pi-eye"
                        pTooltip="View Details"
                        tooltipPosition="top"
                        class="p-button-sm p-button-text"
                        (click)="viewClarificationDetails(clarification)"
                      ></button>
                    </td>
                  </tr>
                </ng-template>
              </p-table>
            }
          </p-tabPanel>
        </p-tabView>
      }
    </div>

    <!-- Clarification Details Dialog (inline) -->
    @if (selectedClarification()) {
      <div class="details-overlay" (click)="closeClarificationDetails()">
        <div class="details-dialog" (click)="$event.stopPropagation()">
          <div class="details-header">
            <h3>Question Details</h3>
            <button
              pButton
              icon="pi pi-times"
              class="p-button-text p-button-rounded"
              (click)="closeClarificationDetails()"
            ></button>
          </div>
          <div class="details-content">
            <div class="detail-row">
              <span class="detail-label">Reference:</span>
              <span class="detail-value">{{ selectedClarification()!.referenceNumber }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Status:</span>
              <p-tag
                [value]="getStatusLabel(selectedClarification()!.status)"
                [severity]="getStatusSeverity(selectedClarification()!.status)"
              ></p-tag>
            </div>
            <div class="detail-row">
              <span class="detail-label">Submitted:</span>
              <span class="detail-value">{{ selectedClarification()!.submittedAt | date:'medium' }}</span>
            </div>
            @if (selectedClarification()!.relatedBoqSectionTitle) {
              <div class="detail-row">
                <span class="detail-label">Related BOQ:</span>
                <span class="detail-value">{{ selectedClarification()!.relatedBoqSectionTitle }}</span>
              </div>
            }
            <p-divider></p-divider>
            <div class="detail-section">
              <h4>Subject</h4>
              <p>{{ selectedClarification()!.subject }}</p>
            </div>
            <div class="detail-section">
              <h4>Question</h4>
              <p>{{ selectedClarification()!.question }}</p>
            </div>
            @if (selectedClarification()!.answer) {
              <div class="detail-section answer-section">
                <h4><i class="pi pi-check-circle"></i> Answer</h4>
                <p>{{ selectedClarification()!.answer }}</p>
                @if (selectedClarification()!.answeredAt) {
                  <small class="answered-date">
                    Answered on {{ selectedClarification()!.answeredAt | date:'medium' }}
                  </small>
                }
              </div>
            } @else {
              <div class="detail-section pending-section">
                <i class="pi pi-clock"></i>
                <p>Your question is being reviewed. You will be notified when an answer is published.</p>
              </div>
            }
          </div>
        </div>
      </div>
    }

    <p-toast></p-toast>
  `,
  styles: [`
    .portal-clarifications {
      animation: fadeIn 0.3s ease;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 4rem 2rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .loading-container p {
      margin-top: 1rem;
    }

    /* Page Header */
    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 1.5rem;
      padding: 1.5rem;
      background: var(--bayan-card, #ffffff);
      border-radius: var(--bayan-radius-sm, 0.375rem);
      border: 1px solid var(--bayan-border, #e4e4e7);
      box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05);
    }

    .header-info h2 {
      margin: 0 0 0.25rem 0;
      font-size: 1.5rem;
      font-weight: 600;
      color: var(--bayan-foreground, #09090b);
    }

    .header-info p {
      margin: 0;
      color: var(--bayan-muted-foreground, #71717a);
    }

    /* Empty State */
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 4rem 2rem;
      color: var(--bayan-muted-foreground, #71717a);
      text-align: center;
    }

    .empty-state i {
      font-size: 3rem;
      margin-bottom: 1rem;
    }

    .empty-state p {
      margin: 0;
      font-size: 1.125rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .empty-state small {
      margin-top: 0.5rem;
    }

    /* Bulletin Styles */
    .bulletin-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      width: 100%;
    }

    .bulletin-info {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }

    .bulletin-info strong {
      font-size: 1rem;
      color: var(--bayan-foreground, #09090b);
    }

    .bulletin-date {
      font-size: 0.8rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .bulletin-meta {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .bulletin-intro {
      padding: 1rem;
      background: var(--bayan-accent, #f4f4f5);
      border-radius: var(--bayan-radius-sm, 0.375rem);
    }

    .bulletin-intro h4 {
      margin: 0 0 0.5rem 0;
      color: var(--bayan-foreground, #09090b);
    }

    .bulletin-intro p {
      margin: 0;
      color: var(--bayan-muted-foreground, #71717a);
    }

    /* Q&A List */
    .qa-list {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .qa-item {
      display: flex;
      gap: 1rem;
      padding: 1.25rem;
      background: var(--bayan-accent, #f4f4f5);
      border-radius: var(--bayan-radius-sm, 0.375rem);
      border-left: 4px solid var(--bayan-primary, #18181b);
    }

    .qa-number {
      font-weight: 700;
      font-size: 1.25rem;
      color: var(--bayan-primary, #18181b);
      min-width: 40px;
    }

    .qa-content {
      flex: 1;
    }

    .qa-question {
      margin-bottom: 1rem;
    }

    .qa-question strong {
      display: block;
      margin-bottom: 0.5rem;
      color: var(--bayan-foreground, #09090b);
    }

    .qa-question p {
      margin: 0;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .boq-ref {
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      margin-top: 0.5rem;
      font-size: 0.8rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .qa-answer {
      padding: 1rem;
      background: var(--bayan-card, #ffffff);
      border-radius: var(--bayan-radius-sm, 0.375rem);
      border: 1px solid var(--bayan-border, #e4e4e7);
    }

    .answer-label {
      display: block;
      font-weight: 600;
      color: #16a34a;
      margin-bottom: 0.5rem;
    }

    .qa-answer p {
      margin: 0;
      color: var(--bayan-foreground, #09090b);
    }

    /* My Questions Table */
    .reference-code {
      font-family: monospace;
      font-size: 0.875rem;
      color: var(--bayan-primary, #18181b);
    }

    .subject-text {
      display: block;
      max-width: 250px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    /* Details Dialog */
    .details-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1100;
      animation: fadeIn 0.2s ease;
    }

    .details-dialog {
      background: var(--bayan-card, #ffffff);
      border-radius: var(--bayan-radius, 0.5rem);
      width: 100%;
      max-width: 600px;
      max-height: 80vh;
      overflow-y: auto;
      border: 1px solid var(--bayan-border, #e4e4e7);
      box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05);
    }

    .details-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1.25rem 1.5rem;
      border-bottom: 1px solid var(--bayan-border, #e4e4e7);
    }

    .details-header h3 {
      margin: 0;
      font-size: 1.25rem;
      color: var(--bayan-foreground, #09090b);
    }

    .details-content {
      padding: 1.5rem;
    }

    .detail-row {
      display: flex;
      align-items: center;
      gap: 1rem;
      margin-bottom: 0.75rem;
    }

    .detail-label {
      font-weight: 500;
      color: var(--bayan-muted-foreground, #71717a);
      min-width: 100px;
    }

    .detail-value {
      color: var(--bayan-foreground, #09090b);
    }

    .detail-section {
      margin-bottom: 1.5rem;
    }

    .detail-section h4 {
      margin: 0 0 0.5rem 0;
      font-size: 0.875rem;
      font-weight: 600;
      color: var(--bayan-muted-foreground, #71717a);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .detail-section p {
      margin: 0;
      color: var(--bayan-foreground, #09090b);
      line-height: 1.6;
    }

    .answer-section {
      padding: 1rem;
      background: #f0fdf4;
      border-radius: var(--bayan-radius-sm, 0.375rem);
      border-left: 4px solid #16a34a;
    }

    .answer-section h4 {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: #16a34a;
    }

    .answered-date {
      display: block;
      margin-top: 0.75rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .pending-section {
      display: flex;
      align-items: flex-start;
      gap: 0.75rem;
      padding: 1rem;
      background: #fffbeb;
      border-radius: var(--bayan-radius-sm, 0.375rem);
      color: #92400e;
    }

    .pending-section i {
      font-size: 1.25rem;
      margin-top: 2px;
    }

    .pending-section p {
      margin: 0;
      color: #92400e;
    }

    :host ::ng-deep {
      .p-tabview .p-tabview-panels {
        padding: 1.5rem 0 0 0;
      }

      .p-accordion .p-accordion-header .p-accordion-header-link {
        padding: 1rem 1.25rem;
      }

      .p-accordion .p-accordion-content {
        padding: 1.25rem;
      }
    }

    @media (max-width: 768px) {
      .page-header {
        flex-direction: column;
        gap: 1rem;
      }

      .bulletin-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
      }

      .qa-item {
        flex-direction: column;
      }

      .details-dialog {
        margin: 1rem;
        max-height: calc(100vh - 2rem);
      }
    }
  `]
})
export class PortalClarificationsComponent implements OnInit {
  private readonly portalService = inject(PortalService);
  private readonly route = inject(ActivatedRoute);
  private readonly dialogService = inject(DialogService);
  private readonly messageService = inject(MessageService);

  bulletins = signal<PortalBulletin[]>([]);
  myClarifications = signal<PortalClarification[]>([]);
  isLoading = signal(true);
  error = signal<string | null>(null);
  selectedClarification = signal<PortalClarification | null>(null);

  private tenderId!: number;

  ngOnInit(): void {
    this.tenderId = parseInt(this.route.snapshot.params['tenderId'], 10);
    this.loadData();
  }

  private loadData(): void {
    this.isLoading.set(true);
    this.error.set(null);

    forkJoin({
      bulletins: this.portalService.getBulletins(this.tenderId),
      clarifications: this.portalService.getClarifications(this.tenderId)
    }).subscribe({
      next: (result) => {
        this.bulletins.set(result.bulletins);
        this.myClarifications.set(result.clarifications);
        this.isLoading.set(false);
      },
      error: (err) => {
        this.error.set(err.message || 'Failed to load clarifications');
        this.isLoading.set(false);
      }
    });
  }

  isClarificationDeadlinePassed(): boolean {
    const tender = this.portalService.currentTender();
    if (!tender?.clarificationDeadline) return false;
    return new Date(tender.clarificationDeadline) < new Date();
  }

  openSubmitQuestionDialog(): void {
    const tender = this.portalService.currentTender();

    const ref = this.dialogService.open(SubmitQuestionDialogComponent, {
      header: 'Submit a Question',
      width: '550px',
      data: {
        tenderId: this.tenderId,
        clarificationDeadline: tender?.clarificationDeadline
      }
    });

    ref.onClose.subscribe((clarification: PortalClarification) => {
      if (clarification) {
        this.myClarifications.set([clarification, ...this.myClarifications()]);
        this.messageService.add({
          severity: 'success',
          summary: 'Question Submitted',
          detail: `Your question has been submitted. Reference: ${clarification.referenceNumber}`
        });
      }
    });
  }

  downloadBulletinPdf(bulletin: PortalBulletin, event: Event): void {
    event.stopPropagation();

    this.portalService.downloadBulletinPdf(bulletin.id).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `QA_Bulletin_${bulletin.bulletinNumber}.pdf`;
        link.click();
        window.URL.revokeObjectURL(url);
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Download Failed',
          detail: 'Failed to download bulletin PDF. Please try again.'
        });
      }
    });
  }

  viewClarificationDetails(clarification: PortalClarification): void {
    this.selectedClarification.set(clarification);
  }

  closeClarificationDetails(): void {
    this.selectedClarification.set(null);
  }

  getStatusLabel(status: string): string {
    const labels: Record<string, string> = {
      submitted: 'Submitted',
      answered: 'Answered',
      published: 'Published'
    };
    return labels[status] || status;
  }

  getStatusSeverity(status: string): 'secondary' | 'success' | 'info' | 'warn' | 'danger' | 'contrast' {
    const severities: Record<string, 'secondary' | 'success' | 'info' | 'warn' | 'danger' | 'contrast'> = {
      submitted: 'info',
      answered: 'success',
      published: 'contrast'
    };
    return severities[status] || 'secondary';
  }
}
