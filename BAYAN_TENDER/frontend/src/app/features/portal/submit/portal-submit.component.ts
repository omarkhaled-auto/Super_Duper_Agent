import { Component, inject, OnInit, OnDestroy, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute } from '@angular/router';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { interval, Subscription } from 'rxjs';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { FileUploadModule, FileUpload } from 'primeng/fileupload';
import { ProgressBarModule } from 'primeng/progressbar';
import { InputNumberModule } from 'primeng/inputnumber';
import { CheckboxModule } from 'primeng/checkbox';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import { MessageModule } from 'primeng/message';
import { DividerModule } from 'primeng/divider';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ToastModule } from 'primeng/toast';
import { ConfirmationService, MessageService } from 'primeng/api';
import { PortalService } from '../../../core/services/portal.service';
import {
  PortalBidDocument,
  PortalBidDocumentType,
  PortalBidUploadProgress,
  PORTAL_BID_DOCUMENT_TYPE_CONFIG
} from '../../../core/models/portal.model';

interface UploadSection {
  type: PortalBidDocumentType;
  config: typeof PORTAL_BID_DOCUMENT_TYPE_CONFIG[PortalBidDocumentType];
  uploadedFiles: PortalBidDocument[];
  uploadProgress: PortalBidUploadProgress | null;
}

@Component({
  selector: 'app-portal-submit',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    CardModule,
    ButtonModule,
    FileUploadModule,
    ProgressBarModule,
    InputNumberModule,
    CheckboxModule,
    TagModule,
    TooltipModule,
    MessageModule,
    DividerModule,
    ConfirmDialogModule,
    ToastModule
  ],
  providers: [ConfirmationService, MessageService],
  template: `
    <div class="portal-submit">
      <!-- Already Submitted State -->
      @if (existingBid()) {
        <div class="already-submitted" data-testid="already-submitted">
          <div class="submitted-icon">
            <i class="pi pi-check-circle"></i>
          </div>
          <h2>Bid Already Submitted</h2>
          <p class="submitted-message">
            You have already submitted a bid for this tender.
          </p>
          <div class="submitted-details">
            <div class="detail-row">
              <span class="detail-label">Receipt Number</span>
              <span class="detail-value">{{ existingBid()!.receiptNumber }}</span>
            </div>
            @if (existingBid()!.submittedAt) {
              <div class="detail-row">
                <span class="detail-label">Submitted On</span>
                <span class="detail-value">{{ existingBid()!.submittedAt | date:'EEEE, MMMM d, y - h:mm a' }}</span>
              </div>
            }
          </div>
          <div class="submitted-actions">
            <button
              pButton
              label="View Receipt"
              icon="pi pi-file"
              class="view-receipt-btn"
              (click)="goToReceipt()"
            ></button>
            <button
              pButton
              label="Back to Tender"
              icon="pi pi-arrow-left"
              class="p-button-outlined back-btn"
              (click)="goToTender()"
            ></button>
          </div>
        </div>
      } @else {
      <!-- Deadline Warning Banner -->
      @if (!countdown().isExpired) {
        <div
          class="deadline-banner"
          [class.urgent]="countdown().totalSeconds < 86400"
          [class.critical]="countdown().totalSeconds < 3600"
          data-testid="deadline-banner"
        >
          <div class="banner-icon">
            <i class="pi pi-clock"></i>
          </div>
          <div class="banner-content">
            <strong>Submission Deadline:</strong>
            <span class="deadline-time">
              {{ countdown().days }}d {{ countdown().hours }}h {{ countdown().minutes }}m {{ countdown().seconds }}s remaining
            </span>
          </div>
          <div class="banner-date">
            {{ tender()?.submissionDeadline | date:'EEEE, MMMM d, y - h:mm a' }}
          </div>
        </div>
      } @else {
        <p-message
          severity="error"
          [text]="'The submission deadline has passed. Late submissions may not be accepted.'"
          styleClass="w-full mb-4"
        ></p-message>
      }

      <!-- Upload Sections -->
      <div class="upload-sections">
        <!-- Commercial Bid Section -->
        <p-card styleClass="section-card mb-4">
          <ng-template pTemplate="header">
            <div class="section-header commercial" data-testid="commercial-bid-section">
              <div class="header-info">
                <i class="pi pi-dollar"></i>
                <h3>Commercial Bid</h3>
              </div>
              <p-tag value="Required" severity="danger"></p-tag>
            </div>
          </ng-template>

          <div class="upload-zone" *ngIf="getUploadSection('priced_boq') as section">
            <div class="upload-item">
              <div class="upload-label">
                <i class="pi {{ section.config.icon }}"></i>
                <div class="label-info">
                  <strong>{{ section.config.label }} *</strong>
                  <small>{{ section.config.description }}</small>
                  <span class="file-info">
                    Accepted: {{ section.config.acceptedFormats.join(', ') }} |
                    Max: {{ section.config.maxSize }}MB
                  </span>
                </div>
              </div>

              @if (section.uploadedFiles.length > 0) {
                <div class="uploaded-file">
                  <div class="file-details">
                    <i class="pi pi-file-excel"></i>
                    <span class="file-name">{{ section.uploadedFiles[0].fileName }}</span>
                    <span class="file-size">{{ formatFileSize(section.uploadedFiles[0].fileSize) }}</span>
                  </div>
                  <button
                    pButton
                    icon="pi pi-times"
                    class="p-button-text p-button-danger p-button-sm"
                    pTooltip="Remove file"
                    (click)="removeFile(section.uploadedFiles[0])"
                  ></button>
                </div>
              } @else if (section.uploadProgress?.status === 'uploading') {
                <div class="upload-progress">
                  <span>{{ section.uploadProgress?.fileName }}</span>
                  <p-progressBar [value]="section.uploadProgress?.progress ?? 0"></p-progressBar>
                </div>
              } @else {
                <div class="dropzone" (click)="fileInput1.click()">
                  <i class="pi pi-cloud-upload"></i>
                  <span>Drag & drop or click to upload</span>
                  <input
                    #fileInput1
                    type="file"
                    [accept]="section.config.acceptedFormats.join(',')"
                    (change)="onFileSelect($event, section.type)"
                    hidden
                  />
                </div>
              }
            </div>
          </div>
        </p-card>

        <!-- Technical Bid Section -->
        <p-card styleClass="section-card mb-4">
          <ng-template pTemplate="header">
            <div class="section-header technical" data-testid="technical-bid-section">
              <div class="header-info">
                <i class="pi pi-file"></i>
                <h3>Technical Bid</h3>
              </div>
              <p-tag value="Required" severity="danger"></p-tag>
            </div>
          </ng-template>

          <div class="upload-zone">
            @for (docType of technicalDocTypes; track docType) {
              <div class="upload-item" *ngIf="getUploadSection(docType) as section">
                <div class="upload-label">
                  <i class="pi {{ section.config.icon }}"></i>
                  <div class="label-info">
                    <strong>{{ section.config.label }} {{ section.config.isRequired ? '*' : '' }}</strong>
                    <small>{{ section.config.description }}</small>
                    <span class="file-info">
                      Accepted: {{ section.config.acceptedFormats.join(', ') }} |
                      Max: {{ section.config.maxSize }}MB
                    </span>
                  </div>
                </div>

                @if (section.uploadedFiles.length > 0) {
                  <div class="uploaded-file">
                    <div class="file-details">
                      <i class="pi pi-file-pdf"></i>
                      <span class="file-name">{{ section.uploadedFiles[0].fileName }}</span>
                      <span class="file-size">{{ formatFileSize(section.uploadedFiles[0].fileSize) }}</span>
                    </div>
                    <button
                      pButton
                      icon="pi pi-times"
                      class="p-button-text p-button-danger p-button-sm"
                      pTooltip="Remove file"
                      (click)="removeFile(section.uploadedFiles[0])"
                    ></button>
                  </div>
                } @else if (section.uploadProgress?.status === 'uploading') {
                  <div class="upload-progress">
                    <span>{{ section.uploadProgress?.fileName }}</span>
                    <p-progressBar [value]="section.uploadProgress?.progress ?? 0"></p-progressBar>
                  </div>
                } @else {
                  <div class="dropzone" (click)="getInputRef(docType).click()">
                    <i class="pi pi-cloud-upload"></i>
                    <span>Drag & drop or click to upload</span>
                    <input
                      #dynamicInput
                      [attr.data-type]="docType"
                      type="file"
                      [accept]="section.config.acceptedFormats.join(',')"
                      (change)="onFileSelect($event, docType)"
                      hidden
                    />
                  </div>
                }
              </div>
            }
          </div>
        </p-card>

        <!-- Supporting Documents Section -->
        <p-card styleClass="section-card mb-4">
          <ng-template pTemplate="header">
            <div class="section-header supporting" data-testid="supporting-docs-section">
              <div class="header-info">
                <i class="pi pi-paperclip"></i>
                <h3>Supporting Documents</h3>
              </div>
              <p-tag value="Optional" severity="secondary"></p-tag>
            </div>
          </ng-template>

          <div class="upload-zone" *ngIf="getUploadSection('supporting_documents') as section">
            <p class="section-description">
              Upload any additional documents that support your bid (company profile, certifications, references, etc.)
            </p>

            @if (section.uploadedFiles.length > 0) {
              <div class="uploaded-files-list">
                @for (file of section.uploadedFiles; track file.id) {
                  <div class="uploaded-file">
                    <div class="file-details">
                      <i class="pi pi-file"></i>
                      <span class="file-name">{{ file.fileName }}</span>
                      <span class="file-size">{{ formatFileSize(file.fileSize) }}</span>
                    </div>
                    <button
                      pButton
                      icon="pi pi-times"
                      class="p-button-text p-button-danger p-button-sm"
                      (click)="removeFile(file)"
                    ></button>
                  </div>
                }
              </div>
            }

            @if (section.uploadProgress?.status === 'uploading') {
              <div class="upload-progress">
                <span>{{ section.uploadProgress?.fileName }}</span>
                <p-progressBar [value]="section.uploadProgress?.progress ?? 0"></p-progressBar>
              </div>
            }

            <div class="dropzone" (click)="fileInputSupporting.click()">
              <i class="pi pi-cloud-upload"></i>
              <span>Drag & drop or click to add more files</span>
              <input
                #fileInputSupporting
                type="file"
                [accept]="section.config.acceptedFormats.join(',')"
                (change)="onFileSelect($event, 'supporting_documents')"
                multiple
                hidden
              />
            </div>
          </div>
        </p-card>

        <!-- Submission Form -->
        <p-card styleClass="section-card submission-card">
          <ng-template pTemplate="header">
            <div class="section-header submit">
              <div class="header-info">
                <i class="pi pi-send"></i>
                <h3>Submit Your Bid</h3>
              </div>
            </div>
          </ng-template>

          <form [formGroup]="submissionForm">
            <!-- Bid Validity -->
            <div class="form-field">
              <label for="bidValidity">Bid Validity Period (Days) *</label>
              <p-inputNumber
                id="bidValidity"
                formControlName="bidValidityDays"
                [min]="30"
                [max]="365"
                suffix=" days"
                styleClass="w-full"
              ></p-inputNumber>
              <small class="field-hint">
                Minimum: 30 days | Recommended: {{ tender()?.bidValidityPeriod || 90 }} days
              </small>
            </div>

            <!-- Upload Summary -->
            <div class="upload-summary">
              <h4>Upload Summary</h4>
              <div class="summary-grid">
                @for (section of allSections; track section.type) {
                  <div class="summary-item" [class.complete]="isSectionComplete(section.type)">
                    <i class="pi" [class.pi-check-circle]="isSectionComplete(section.type)" [class.pi-circle]="!isSectionComplete(section.type)"></i>
                    <span>{{ section.config.label }}</span>
                    @if (section.config.isRequired) {
                      <span class="required-badge">*</span>
                    }
                  </div>
                }
              </div>
            </div>

            <p-divider></p-divider>

            <!-- Terms Acceptance -->
            <div class="terms-section">
              <p-checkbox
                formControlName="termsAccepted"
                [binary]="true"
                inputId="terms"
                data-testid="terms-checkbox"
              ></p-checkbox>
              <label for="terms" class="terms-label">
                I confirm that:
                <ul>
                  <li>All information provided is accurate and complete</li>
                  <li>I am authorized to submit this bid on behalf of my company</li>
                  <li>I have read and accept the tender terms and conditions</li>
                  <li>I acknowledge that this bid is binding once submitted</li>
                </ul>
              </label>
            </div>

            <!-- Submit Button -->
            <div class="submit-actions">
              <button
                pButton
                label="Submit Bid"
                icon="pi pi-send"
                class="submit-btn"
                data-testid="submit-bid-btn"
                [loading]="isSubmitting()"
                [disabled]="!canSubmit()"
                (click)="onSubmit()"
              ></button>
            </div>

            @if (!canSubmit()) {
              <p-message
                severity="warn"
                [text]="getSubmitBlockReason()"
                styleClass="w-full mt-3"
              ></p-message>
            }
          </form>
        </p-card>
      </div>
      }
    </div>

    <p-confirmDialog></p-confirmDialog>
    <p-toast></p-toast>
  `,
  styleUrl: './portal-submit.component.scss'
})
export class PortalSubmitComponent implements OnInit, OnDestroy {
  private readonly portalService = inject(PortalService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly fb = inject(FormBuilder);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly messageService = inject(MessageService);

  private countdownSubscription?: Subscription;
  private progressSubscription?: Subscription;

  tender = this.portalService.currentTender;
  isSubmitting = signal(false);
  existingBid = signal<{ bidId: string; receiptNumber: string; submittedAt?: string } | null>(null);

  countdown = signal({
    days: 0,
    hours: 0,
    minutes: 0,
    seconds: 0,
    isExpired: false,
    totalSeconds: 0
  });

  uploadedDocuments = signal<PortalBidDocument[]>([]);
  uploadProgress = signal<Map<PortalBidDocumentType, PortalBidUploadProgress>>(new Map());

  submissionForm!: FormGroup;

  technicalDocTypes: PortalBidDocumentType[] = ['methodology', 'team_cvs', 'program', 'hse_plan'];

  allSections: UploadSection[] = [];

  private tenderId!: string | number;
  private fileInputRefs = new Map<PortalBidDocumentType, HTMLInputElement>();

  ngOnInit(): void {
    this.tenderId = this.route.parent?.snapshot.params['tenderId'] || this.route.snapshot.params['tenderId'];
    this.initForm();
    this.initSections();
    this.checkBidStatus();
  }

  private checkBidStatus(): void {
    this.portalService.getBidStatus(this.tenderId).subscribe({
      next: (status) => {
        if (status.hasSubmitted && status.bidId) {
          this.existingBid.set({
            bidId: status.bidId,
            receiptNumber: status.receiptNumber || '',
            submittedAt: status.submittedAt
          });
        } else {
          // No existing bid — proceed with normal flow
          this.startCountdown();
          this.subscribeToProgress();
          this.loadDraftBid();
        }
      },
      error: () => {
        // If status check fails, proceed with normal flow
        this.startCountdown();
        this.subscribeToProgress();
        this.loadDraftBid();
      }
    });
  }

  ngOnDestroy(): void {
    this.countdownSubscription?.unsubscribe();
    this.progressSubscription?.unsubscribe();
    this.portalService.clearUploadProgress();
  }

  private initForm(): void {
    const defaultValidity = this.tender()?.bidValidityPeriod || 90;
    this.submissionForm = this.fb.group({
      bidValidityDays: [defaultValidity, [Validators.required, Validators.min(30), Validators.max(365)]],
      termsAccepted: [false, [Validators.requiredTrue]]
    });
  }

  private initSections(): void {
    const allTypes: PortalBidDocumentType[] = [
      'priced_boq',
      'methodology',
      'team_cvs',
      'program',
      'hse_plan',
      'qa_qc_plan',
      'supporting_documents'
    ];

    this.allSections = allTypes.map(type => ({
      type,
      config: PORTAL_BID_DOCUMENT_TYPE_CONFIG[type],
      uploadedFiles: [],
      uploadProgress: null
    }));
  }

  private startCountdown(): void {
    this.countdownSubscription = interval(1000).subscribe(() => {
      const tender = this.tender();
      if (tender?.submissionDeadline) {
        this.countdown.set(
          this.portalService.getDeadlineCountdown(tender.submissionDeadline)
        );
      }
    });

    // Initial calculation
    const tender = this.tender();
    if (tender?.submissionDeadline) {
      this.countdown.set(
        this.portalService.getDeadlineCountdown(tender.submissionDeadline)
      );
    }
  }

  private subscribeToProgress(): void {
    this.progressSubscription = this.portalService.uploadProgress$.subscribe(progress => {
      this.uploadProgress.set(progress);
    });
  }

  private loadDraftBid(): void {
    this.portalService.getDraftBid(this.tenderId).subscribe({
      next: (draft) => {
        if (draft) {
          this.uploadedDocuments.set(draft.documents);
          if (draft.bidValidityDays) {
            this.submissionForm.patchValue({ bidValidityDays: draft.bidValidityDays });
          }
        }
      }
    });
  }

  getUploadSection(type: PortalBidDocumentType): UploadSection {
    const section = this.allSections.find(s => s.type === type)!;
    section.uploadedFiles = this.uploadedDocuments().filter(d => d.documentType === type);
    section.uploadProgress = this.uploadProgress().get(type) || null;
    return section;
  }

  getInputRef(type: PortalBidDocumentType): HTMLInputElement {
    let ref = this.fileInputRefs.get(type);
    if (!ref) {
      ref = document.querySelector(`input[data-type="${type}"]`) as HTMLInputElement;
      if (ref) {
        this.fileInputRefs.set(type, ref);
      }
    }
    return ref;
  }

  onFileSelect(event: Event, documentType: PortalBidDocumentType): void {
    const input = event.target as HTMLInputElement;
    const files = input.files;
    if (!files || files.length === 0) return;

    const config = PORTAL_BID_DOCUMENT_TYPE_CONFIG[documentType];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];

      // Validate file size
      if (file.size > config.maxSize * 1024 * 1024) {
        this.messageService.add({
          severity: 'error',
          summary: 'File Too Large',
          detail: `${file.name} exceeds the maximum size of ${config.maxSize}MB`
        });
        continue;
      }

      // Validate file type
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!config.acceptedFormats.includes(ext)) {
        this.messageService.add({
          severity: 'error',
          summary: 'Invalid File Type',
          detail: `${file.name} is not an accepted format. Please use: ${config.acceptedFormats.join(', ')}`
        });
        continue;
      }

      // Upload the file
      this.portalService.uploadBidDocument(this.tenderId, documentType, file).subscribe({
        next: (doc) => {
          if (doc) {
            // Normalize documentType to frontend format (backend returns PascalCase e.g. "PricedBOQ")
            doc.documentType = documentType;
            const current = this.uploadedDocuments();
            // For non-supporting docs, replace existing
            if (documentType !== 'supporting_documents') {
              const filtered = current.filter(d => d.documentType !== documentType);
              this.uploadedDocuments.set([...filtered, doc]);
            } else {
              this.uploadedDocuments.set([...current, doc]);
            }
            this.messageService.add({
              severity: 'success',
              summary: 'Upload Complete',
              detail: `${file.name} uploaded successfully`
            });
          }
        },
        error: (err) => {
          this.messageService.add({
            severity: 'error',
            summary: 'Upload Failed',
            detail: err.message || 'Failed to upload file'
          });
        }
      });
    }

    // Reset the input
    input.value = '';
  }

  removeFile(doc: PortalBidDocument): void {
    this.confirmationService.confirm({
      message: `Are you sure you want to remove ${doc.fileName}?`,
      header: 'Confirm Removal',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.portalService.deleteBidDocument(this.tenderId, doc.id).subscribe({
          next: () => {
            const current = this.uploadedDocuments();
            this.uploadedDocuments.set(current.filter(d => d.id !== doc.id));
            this.messageService.add({
              severity: 'success',
              summary: 'Removed',
              detail: `${doc.fileName} has been removed`
            });
          },
          error: () => {
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: 'Failed to remove file'
            });
          }
        });
      }
    });
  }

  isSectionComplete(type: PortalBidDocumentType): boolean {
    return this.uploadedDocuments().some(d => d.documentType === type);
  }

  formatFileSize(bytes: number): string {
    return this.portalService.formatFileSize(bytes);
  }

  canSubmit(): boolean {
    // Check all required documents are uploaded
    const requiredTypes: PortalBidDocumentType[] = ['priced_boq', 'methodology', 'team_cvs', 'program', 'hse_plan'];
    const hasAllRequired = requiredTypes.every(type =>
      this.uploadedDocuments().some(d => d.documentType === type)
    );

    // Check form validity
    const formValid = this.submissionForm.valid;

    return hasAllRequired && formValid;
  }

  getSubmitBlockReason(): string {
    const requiredTypes: PortalBidDocumentType[] = ['priced_boq', 'methodology', 'team_cvs', 'program', 'hse_plan'];
    const missing = requiredTypes.filter(type =>
      !this.uploadedDocuments().some(d => d.documentType === type)
    );

    if (missing.length > 0) {
      const labels = missing.map(t => PORTAL_BID_DOCUMENT_TYPE_CONFIG[t].label);
      return `Missing required documents: ${labels.join(', ')}`;
    }

    if (!this.submissionForm.get('termsAccepted')?.value) {
      return 'Please accept the terms and conditions';
    }

    return '';
  }

  goToReceipt(): void {
    const bid = this.existingBid();
    if (bid) {
      this.router.navigate(['/portal/bids', bid.bidId, 'receipt']);
    }
  }

  goToTender(): void {
    this.router.navigate(['/portal/tenders', this.tenderId, 'documents']);
  }

  onSubmit(): void {
    if (!this.canSubmit()) return;

    this.confirmationService.confirm({
      message: 'Are you sure you want to submit your bid? This action cannot be undone.',
      header: 'Confirm Submission',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.isSubmitting.set(true);

        const dto = {
          tenderId: this.tenderId,
          bidValidityDays: this.submissionForm.value.bidValidityDays,
          termsAccepted: this.submissionForm.value.termsAccepted,
          documentIds: this.uploadedDocuments().map(d => d.id)
        };

        this.portalService.submitBid(dto).subscribe({
          next: (receipt) => {
            this.isSubmitting.set(false);
            this.router.navigate(['/portal/bids', receipt.id, 'receipt']);
          },
          error: (err) => {
            this.isSubmitting.set(false);
            this.messageService.add({
              severity: 'error',
              summary: 'Submission Failed',
              detail: err.message || 'Failed to submit bid. Please try again.'
            });
          }
        });
      }
    });
  }
}
