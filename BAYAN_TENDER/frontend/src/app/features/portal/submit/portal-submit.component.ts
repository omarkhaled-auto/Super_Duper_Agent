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
    </div>

    <p-confirmDialog></p-confirmDialog>
    <p-toast></p-toast>
  `,
  styles: [`
    .portal-submit {
      animation: fadeIn 0.3s ease;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* Deadline Banner */
    .deadline-banner {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1rem 1.5rem;
      background: var(--bayan-accent, #f4f4f5);
      border: 1px solid var(--bayan-border, #e4e4e7);
      border-radius: var(--bayan-radius, 0.5rem);
      margin-bottom: 1.5rem;
    }

    .deadline-banner.urgent {
      background: #fffbeb;
      border-color: #fbbf24;
    }

    .deadline-banner.critical {
      background: #fef2f2;
      border-color: #f87171;
      animation: pulse 2s infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.8; }
    }

    .banner-icon {
      font-size: 2rem;
      color: var(--bayan-foreground, #09090b);
    }

    .deadline-banner.urgent .banner-icon {
      color: #d97706;
    }

    .deadline-banner.critical .banner-icon {
      color: #dc2626;
    }

    .banner-content {
      flex: 1;
    }

    .banner-content strong {
      display: block;
      margin-bottom: 0.25rem;
      color: var(--bayan-foreground, #09090b);
    }

    .deadline-banner.urgent .banner-content strong {
      color: #92400e;
    }

    .deadline-banner.critical .banner-content strong {
      color: #991b1b;
    }

    .deadline-time {
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--bayan-foreground, #09090b);
    }

    .deadline-banner.urgent .deadline-time {
      color: #b45309;
    }

    .deadline-banner.critical .deadline-time {
      color: #dc2626;
    }

    .banner-date {
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    /* Section Cards */
    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem 1.5rem;
      border-bottom: 1px solid var(--bayan-border, #e4e4e7);
    }

    .section-header.commercial {
      background: #f0fdf4;
    }

    .section-header.technical {
      background: var(--bayan-accent, #f4f4f5);
    }

    .section-header.supporting {
      background: var(--bayan-muted, #f4f4f5);
    }

    .section-header.submit {
      background: #fffbeb;
    }

    .header-info {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .header-info i {
      font-size: 1.5rem;
    }

    .header-info h3 {
      margin: 0;
      font-size: 1.125rem;
      font-weight: 600;
      color: var(--bayan-foreground, #09090b);
    }

    /* Upload Zone */
    .upload-zone {
      padding: 1.5rem;
    }

    .section-description {
      color: var(--bayan-muted-foreground, #71717a);
      margin: 0 0 1.5rem 0;
    }

    .upload-item {
      padding: 1rem;
      border: 1px solid var(--bayan-border, #e4e4e7);
      border-radius: var(--bayan-radius-sm, 0.375rem);
      margin-bottom: 1rem;
    }

    .upload-item:last-child {
      margin-bottom: 0;
    }

    .upload-label {
      display: flex;
      align-items: flex-start;
      gap: 1rem;
      margin-bottom: 1rem;
    }

    .upload-label > i {
      font-size: 1.5rem;
      color: var(--bayan-primary, #18181b);
      margin-top: 2px;
    }

    .label-info {
      flex: 1;
    }

    .label-info strong {
      display: block;
      color: var(--bayan-foreground, #09090b);
      margin-bottom: 0.25rem;
    }

    .label-info small {
      display: block;
      color: var(--bayan-muted-foreground, #71717a);
      margin-bottom: 0.25rem;
    }

    .file-info {
      display: block;
      font-size: 0.75rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .dropzone {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      padding: 2rem;
      border: 2px dashed var(--bayan-border, #e4e4e7);
      border-radius: var(--bayan-radius-sm, 0.375rem);
      background: var(--bayan-accent, #f4f4f5);
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .dropzone:hover {
      border-color: var(--bayan-primary, #18181b);
      background: var(--bayan-muted, #f4f4f5);
    }

    .dropzone i {
      font-size: 2rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .dropzone span {
      color: var(--bayan-muted-foreground, #71717a);
    }

    .uploaded-file {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.75rem 1rem;
      background: #f0fdf4;
      border: 1px solid #86efac;
      border-radius: var(--bayan-radius-sm, 0.375rem);
    }

    .uploaded-files-list {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      margin-bottom: 1rem;
    }

    .file-details {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .file-details i {
      font-size: 1.25rem;
      color: #16a34a;
    }

    .file-name {
      font-weight: 500;
      color: var(--bayan-foreground, #09090b);
      max-width: 300px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .file-size {
      color: var(--bayan-muted-foreground, #71717a);
      font-size: 0.875rem;
    }

    .upload-progress {
      padding: 1rem;
      background: var(--bayan-accent, #f4f4f5);
      border-radius: var(--bayan-radius-sm, 0.375rem);
    }

    .upload-progress span {
      display: block;
      margin-bottom: 0.5rem;
      color: var(--bayan-muted-foreground, #71717a);
      font-size: 0.875rem;
    }

    /* Submission Form */
    .form-field {
      margin-bottom: 1.5rem;
    }

    .form-field label {
      display: block;
      margin-bottom: 0.5rem;
      font-weight: 500;
      color: var(--bayan-foreground, #09090b);
    }

    .field-hint {
      display: block;
      margin-top: 0.25rem;
      color: var(--bayan-muted-foreground, #71717a);
      font-size: 0.8rem;
    }

    .upload-summary {
      margin-bottom: 1.5rem;
    }

    .upload-summary h4 {
      margin: 0 0 1rem 0;
      font-size: 1rem;
      color: var(--bayan-foreground, #09090b);
    }

    .summary-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 0.75rem;
    }

    .summary-item {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.5rem 0.75rem;
      background: var(--bayan-accent, #f4f4f5);
      border-radius: var(--bayan-radius-sm, 0.375rem);
      color: var(--bayan-muted-foreground, #71717a);
    }

    .summary-item.complete {
      background: #f0fdf4;
      color: #16a34a;
    }

    .summary-item .pi-check-circle {
      color: #16a34a;
    }

    .required-badge {
      color: #dc2626;
      font-weight: 700;
    }

    .terms-section {
      display: flex;
      align-items: flex-start;
      gap: 1rem;
      padding: 1.5rem;
      background: var(--bayan-accent, #f4f4f5);
      border-radius: var(--bayan-radius-sm, 0.375rem);
      margin-bottom: 1.5rem;
    }

    .terms-label {
      cursor: pointer;
      color: var(--bayan-foreground, #09090b);
    }

    .terms-label ul {
      margin: 0.5rem 0 0 0;
      padding-left: 1.25rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .terms-label li {
      margin-bottom: 0.25rem;
    }

    .submit-actions {
      display: flex;
      justify-content: center;
    }

    .submit-btn {
      height: 52px;
      font-size: 1.125rem;
      padding: 0 3rem;
    }

    :host ::ng-deep {
      .section-card .p-card-body {
        padding: 0;
      }

      .submission-card .p-card-body {
        padding: 1.5rem;
      }

      .p-inputnumber {
        width: 100%;
      }
    }

    @media (max-width: 768px) {
      .deadline-banner {
        flex-direction: column;
        text-align: center;
      }

      .summary-grid {
        grid-template-columns: 1fr;
      }

      .submit-btn {
        width: 100%;
      }
    }
  `]
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

  private tenderId!: number;
  private fileInputRefs = new Map<PortalBidDocumentType, HTMLInputElement>();

  ngOnInit(): void {
    this.tenderId = parseInt(this.route.snapshot.params['tenderId'], 10);
    this.initForm();
    this.initSections();
    this.startCountdown();
    this.subscribeToProgress();
    this.loadDraftBid();
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
