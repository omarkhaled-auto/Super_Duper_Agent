# Bayan Tender — Manual E2E Testing Handoff

**Date:** 2026-02-10 (updated)
**Session scope:** Manual walkthrough of the full tender lifecycle (admin + bidder portal)
**Status:** Steps 0-2 complete — clarification full cycle verified; bid submission verified (upload, submit, receipt, re-visit handling); evaluation, and award remain

---

## 1. What Was Tested & Confirmed Working

### Admin Side (pre-session — previously verified)
| Feature | Status |
|---------|--------|
| Tender creation (CRUD) | Working |
| BOQ import (Excel upload, validation, column mapping, force-import) | Working |
| BOQ export (template download) | Working |
| Document upload to folders (tender_documents, drawings, etc.) | Working |
| Tender publishing (Draft -> Published) | Working |
| Mock bidder seeding (2 bidders in DB) | Working |

### Admin Side (this session + previous)
| Feature | Status |
|---------|--------|
| Bidder invitation (both bidders) | Working — status shows "Sent", DB records confirmed |
| Clarifications — view submitted questions | Working — status normalization (int→string) applied |
| Clarifications — answer a question | Working — DraftAnswer flow verified |
| Clarifications — publish Q&A bulletin | Working — auto-approves DraftAnswer, generates PDF, emails bidders |

### Bidder Portal (this session + previous)
| Feature | Status |
|---------|--------|
| Portal login | Working — `bidder@vendor.ae` / `Bayan@2024` |
| Tender listing on landing page | Working — published tender appears correctly |
| Tender listing — "Bid Submitted" status | Working — shows blue "Bid Submitted" tag instead of "Qualified" after bid submission |
| Tab navigation (Documents, Clarifications, Submit Bid) | Working — after rewrite to plain routerLink |
| Back to Your Tenders link | Working — arrow icon in header navigates back to tender listing |
| Documents tab — file listing by folder | Working — grouped by folderPath with category inference |
| Documents tab — file download | Working — streams through API |
| Clarifications tab — submit question dialog | Working — BOQ sections load in dropdown |
| Clarifications tab — question submission | Working — relatedBoqSection field fixed |
| Clarifications tab — status display | Working — verified "Submitted" shows correctly |
| Clarifications tab — My Questions (persistent) | Working — new /my-questions endpoint, survives refresh |
| Clarifications tab — Q&A Bulletins | Working — bulletin with Q&A items renders correctly |
| Clarifications tab — bulletin PDF download | Working — hasPdf flag + download endpoint |
| Submit Bid — document upload | Working — all 5 categories upload correctly |
| Submit Bid — bid submission + receipt | Working — receipt number, company name, file sizes all correct |
| Submit Bid — receipt PDF download | Working — receipt PDF generates and downloads correctly |
| Submit Bid — already submitted handling | Working — shows green "Already Submitted" card with View Receipt / Back to Tender actions |

---

## 2. Bugs Found & Fixed (18 total)

### Fix 1: Bidders not qualified — documents invisible
- **Symptom:** Portal documents page showed empty list
- **Root cause:** `GetPortalDocumentsQueryHandler` requires `QualificationStatus == Qualified`, but bidders were `Pending` after invitation
- **Fix:** SQL update: `SET qualification_status = 'Qualified'` on `tender_bidders`
- **Note:** Production needs a proper qualification workflow UI

### Fix 2: Property name mismatch — portal documents
- **Symptom:** Template bindings failed silently (empty values)
- **Root cause:** Backend `PortalDocumentDto` fields (`folderPath`, `fileSizeBytes`, `contentType`, `createdAt`) didn't match frontend `TenderDocument` interface (`category`, `fileSize`, `mimeType`, `uploadedAt`)
- **Files:**
  - `frontend/src/app/core/models/portal.model.ts` — rewrote `TenderDocument` interface
  - `frontend/src/app/features/portal/documents/portal-documents.component.ts` — updated template bindings
  - `frontend/src/app/core/services/portal.service.ts` — `organizeDocumentsByCategory()` groups by `folderPath`

### Fix 3: Download URL missing tenderId
- **Symptom:** 404 on document download
- **Root cause:** `downloadDocument()` path was `/portal/documents/{id}/download` (missing tenderId)
- **Files:**
  - `portal.service.ts` — `downloadDocument(tenderId, documentId)` and `downloadBulletinPdf(tenderId, bulletinId)` now include tenderId
  - `portal-clarifications.component.ts` — passes tenderId to `downloadBulletinPdf()`

### Fix 4: Presigned URL unreachable from browser
- **Symptom:** Download returned MinIO URL with `minio:9000` (Docker internal hostname)
- **Root cause:** `PortalController.DownloadDocument` returned presigned URL
- **Files:**
  - `backend/Bayan.API/Controllers/PortalController.cs` — now streams file directly: `return File(stream, contentType, fileName)`

### Fix 5: `doc.url` build error
- **Symptom:** `Property 'url' does not exist on type 'TenderDocument'`
- **Root cause:** `previewDocument()` referenced removed field
- **Fix:** Changed to blob download approach in `portal-documents.component.ts`

### Fix 6: PrimeNG TabMenu navigation broken/slow
- **Symptom:** Tabs very slow, sometimes didn't navigate
- **Root cause:** PrimeNG `TabMenu` had conflicting `command` callbacks overriding `routerLink`, `[activeItem]` binding fights, `interval(1000)` countdown triggering change detection
- **Files:**
  - `portal-layout.component.ts` — complete rewrite:
    - Plain `<a routerLink>` + `routerLinkActive` (no PrimeNG)
    - `ChangeDetectionStrategy.OnPush`
    - Countdown throttled to 30s interval

### Fix 7: BOQ sections missing in clarification dialog
- **Symptom:** "Related BOQ Section" dropdown was empty
- **Root cause:** No `GET /api/portal/tenders/{tenderId}/boq-sections` endpoint
- **Files:**
  - `backend/Bayan.API/Controllers/PortalController.cs` — added `GetBoqSections` endpoint

### Fix 8: Clarification status empty after submission
- **Symptom:** Status column blank after submitting a question
- **Root cause:** Two mismatches:
  1. POST returns `BidderQuestionDto` with `statusDisplay` (string) but **no `status` field**
  2. GET returns `PortalClarificationDto` with `status` as **integer** enum (0=Submitted) — ASP.NET has no `JsonStringEnumConverter`
  3. Frontend expected lowercase string (`'submitted'`, `'answered'`, etc.)
- **Files:**
  - `portal.model.ts` — widened `status` to `string`, added `statusDisplay`, `relatedBoqSection`
  - `portal.service.ts` — added `normalizeClarification()` that maps integers/statusDisplay to lowercase strings
  - `portal-clarifications.component.ts` — `getStatusLabel()`/`getStatusSeverity()` handle all 7 enum values

### Fix 9: Questions disappear on page refresh
- **Symptom:** Bidder submits a question, sees it, refreshes — question gone
- **Root cause:** `GetPublishedClarificationsQueryHandler` only returns `Status == Published` — bidder's own submitted (unpublished) questions were excluded
- **Files:**
  - `backend/.../Portal/Clarifications/GetMyQuestionsQuery.cs` — NEW: MediatR query
  - `backend/.../Portal/Clarifications/GetMyQuestionsQueryHandler.cs` — NEW: returns bidder's own questions (any status, BidderQuestion type, with qualification check)
  - `backend/Bayan.API/Controllers/PortalController.cs` — added `GET /portal/tenders/{tenderId}/my-questions`
  - `frontend/src/app/core/services/portal.service.ts` — added `getMyQuestions()` method
  - `frontend/src/app/features/portal/clarifications/portal-clarifications.component.ts` — uses `getMyQuestions` for "My Questions" tab

### Fix 10: relatedBoqSection field name mismatch (frontend → backend)
- **Symptom:** BOQ section not saved when submitting a question
- **Root cause:** Frontend sent `relatedBoqSectionId` (number) but backend expected `relatedBoqSection` (string)
- **Files:**
  - `frontend/src/app/core/models/portal.model.ts` — `relatedBoqSectionId?: number` → `relatedBoqSection?: string`
  - `frontend/src/app/features/portal/clarifications/submit-question-dialog.component.ts` — form control renamed, dropdown `optionValue="id"` → `optionValue="title"`

### Fix 11: Admin clarification statuses showing raw integers
- **Symptom:** Admin clarifications page showed "0" as status, no action buttons worked
- **Root cause:** Admin `ClarificationService` had no enum normalization (unlike portal service)
- **Files:**
  - `frontend/src/app/core/services/clarification.service.ts` — added `normalizeClarification()` with `STATUS_INT_MAP`, `STATUS_NAME_MAP`, `PRIORITY_INT_MAP`, `PRIORITY_NAME_MAP`, `SOURCE_INT_MAP`, `SOURCE_NAME_MAP`; applied to all 13 methods

### Fix 12: DraftAnswer mapped to wrong frontend status
- **Symptom:** Answered question showed Edit/Submit for Review/Delete (draft actions) instead of Edit Answer/Ready for bulletin
- **Root cause:** Backend `DraftAnswer=2` was mapped to frontend `'draft'` (draft question), but it means "answer exists in draft form"
- **Fix:** Changed mapping: `DraftAnswer(2) → 'answered'` in both `STATUS_INT_MAP` and `STATUS_NAME_MAP`

### Fix 13: "No answered clarifications available for publishing"
- **Symptom:** Publish Q&A Bulletin dialog showed no clarifications to select
- **Root cause:** Two issues:
  1. `getAnsweredClarifications()` sent `status=answered` to backend → mapped to `Answered=3` enum, but clarifications were in `DraftAnswer=2` state
  2. Backend `PublishBulletinCommandHandler` required `Answered` status (rejected `DraftAnswer`)
- **Files:**
  - `frontend/src/app/core/services/clarification.service.ts` — `getAnsweredClarifications()` now fetches all and filters client-side for `status === 'answered'`
  - `backend/.../PublishBulletin/PublishBulletinCommandHandler.cs` — auto-approves `DraftAnswer` → `Answered` before validation

### Fix 14: Portal bulletins page crash — "Cannot read properties of undefined (reading 'length')"
- **Symptom:** Repeated errors on portal load, clarifications page blank
- **Root cause:** Backend `PortalBulletinDto` only had `ClarificationCount` (int), no actual Q&A array. Frontend template accessed `bulletin.clarifications.length` → `undefined.length`
- **Files:**
  - `backend/.../Portal/DTOs/PortalBulletinDto.cs` — added `List<PortalBulletinClarificationDto> Clarifications` property + new `PortalBulletinClarificationDto` class
  - `backend/.../Portal/Clarifications/GetPublishedBulletinsQueryHandler.cs` — query now includes clarification items (ordered by reference number)
  - `frontend/src/app/core/models/portal.model.ts` — added `PortalBulletinClarification` interface, updated `PortalBulletin` to match backend (hasPdf, clarificationCount, closingNotes)
  - `frontend/src/app/features/portal/clarifications/portal-clarifications.component.ts` — updated template: `pdfUrl` → `hasPdf`, removed `bulletin.title`, `relatedBoqSectionTitle` → `relatedBoqSection`

### Fix 15: Bid receipt — company name empty, NaN file size, blank PDF
- **Symptom:** Receipt page showed empty company name, "NaN KB" for file sizes, and blank PDF
- **Root cause:** Three issues:
  1. `BidReceiptDto` had no `CompanyName` field — only `BidderName`
  2. `GetBidReceiptQueryHandler` didn't populate `CompanyName` or `SubmittedDocuments`
  3. PDF receipt generation used `bidder.ContactPerson` instead of `bidder.CompanyName`
- **Files:**
  - `backend/.../Bids/DTOs/BidReceiptDto.cs` — added `CompanyName` field
  - `backend/.../Bids/Queries/GetBidReceipt/GetBidReceiptQueryHandler.cs` — populates CompanyName + SubmittedDocuments with actual file sizes
  - `backend/.../Bids/Commands/SubmitBid/SubmitBidCommandHandler.cs` — receipt PDF uses `bidder.CompanyName`

### Fix 16: 404/500 errors when revisiting Submit Bid tab after bid already submitted
- **Symptom:** Navigating to Submit Bid for a tender that already has a submitted bid caused 404 (no draft) and 500 (upload fails) errors
- **Root cause:** Component always tried to load a draft bid and show upload UI, even when a bid was already submitted
- **Files:**
  - `backend/Bayan.API/Controllers/PortalController.cs` — added `GET /portal/tenders/{tenderId}/bid/status` endpoint
  - `frontend/src/app/core/services/portal.service.ts` — added `getBidStatus()` method
  - `frontend/src/app/features/portal/submit/portal-submit.component.ts` — added `checkBidStatus()`, shows "Already Submitted" card with View Receipt / Back to Tender links instead of upload UI

### Fix 17: No "Back to Your Tenders" navigation from inside a tender
- **Symptom:** Once inside a tender, no way to go back to the tender listing page
- **Files:**
  - `frontend/src/app/features/portal/layout/portal-layout.component.ts` — added back-arrow link in header pointing to `/portal/tenders`

### Fix 18: Tender card still shows "Qualified" after bid submission
- **Symptom:** After submitting a bid, the tender listing page still showed "Qualified" status instead of reflecting the submission
- **Root cause:** Login response didn't include bid submission info
- **Files:**
  - `backend/.../Portal/DTOs/BidderLoginResponseDto.cs` — added `HasSubmittedBid` field to `BidderTenderAccessDto`
  - `backend/.../Portal/Auth/BidderLoginCommandHandler.cs` — queries `BidSubmissions` to populate `HasSubmittedBid`
  - `frontend/src/app/features/portal/tenders/portal-tenders.component.ts` — template shows "Bid Submitted" tag (blue/info) when `hasSubmittedBid` is true

---

## 3. Uncommitted Changes

All changes sit on top of commit `fbc6021`. **Build succeeds** (Angular `ng build` passes, API builds clean with 0 errors, 14 pre-existing warnings).

### Backend (new files)
| File | Description |
|------|-------------|
| `Features/Portal/Clarifications/GetMyQuestionsQuery.cs` | NEW — MediatR query for bidder's own questions |
| `Features/Portal/Clarifications/GetMyQuestionsQueryHandler.cs` | NEW — handler returning bidder's questions (any status) |

### Backend (modified files)
| File | Changes |
|------|---------|
| `Controllers/PortalController.cs` | +`GetBoqSections`, +`GetMyQuestions`, +`GetBidStatus`, `DownloadDocument` streams directly |
| `Features/Portal/DTOs/PortalBulletinDto.cs` | +`Clarifications` list, +`PortalBulletinClarificationDto` class |
| `Features/Portal/DTOs/BidderLoginResponseDto.cs` | +`HasSubmittedBid` on `BidderTenderAccessDto` |
| `Features/Portal/Auth/BidderLoginCommandHandler.cs` | Queries BidSubmissions, populates `HasSubmittedBid` in tender access |
| `Features/Portal/Clarifications/GetPublishedBulletinsQueryHandler.cs` | Query includes clarification items |
| `Features/Clarifications/Commands/PublishBulletin/PublishBulletinCommandHandler.cs` | Auto-approves DraftAnswer before validation |
| `Features/Bids/DTOs/BidReceiptDto.cs` | +`CompanyName` field |
| `Features/Bids/Queries/GetBidReceipt/GetBidReceiptQueryHandler.cs` | Populates CompanyName + SubmittedDocuments |
| `Features/Bids/Commands/SubmitBid/SubmitBidCommandHandler.cs` | Receipt PDF uses `bidder.CompanyName` |
| `Dockerfile` | Updated for production builds |

### Frontend (modified files)
| File | Changes |
|------|---------|
| `core/models/portal.model.ts` | `TenderDocument` + `PortalClarification` rewritten, +`PortalBulletinClarification`, `PortalBulletin` updated, `SubmitQuestionDto.relatedBoqSection` fixed |
| `core/services/portal.service.ts` | +`normalizeClarification()`, +`getMyQuestions()`, +`getBidStatus()`, +`folderPathToCategory()`, fixed download URLs |
| `core/services/clarification.service.ts` | +`normalizeClarification()` with enum maps, applied to all methods, `getAnsweredClarifications()` client-side filter |
| `features/portal/layout/portal-layout.component.ts` | Complete rewrite — plain routerLink, OnPush, 30s countdown, +back-to-tenders arrow link |
| `features/portal/tenders/portal-tenders.component.ts` | Shows "Bid Submitted" tag when `hasSubmittedBid` is true |
| `features/portal/submit/portal-submit.component.ts` | +`checkBidStatus()`, "Already Submitted" card UI, `goToReceipt()`/`goToTender()` navigation |
| `features/portal/documents/portal-documents.component.ts` | Template bindings updated, preview uses blob download |
| `features/portal/clarifications/portal-clarifications.component.ts` | +`PortalBulletinClarification` import, template fixed for backend DTO shape |
| `features/portal/clarifications/submit-question-dialog.component.ts` | `relatedBoqSectionId` → `relatedBoqSection`, dropdown optionValue fixed |

---

## 4. What to Do Next

### Step 2: Bid Submission (bidder portal) — COMPLETE
- All bid submission features verified: upload, submit, receipt, PDF download, already-submitted handling, back navigation, bid status display on tender card

### Step 3: Bid Evaluation (admin side) — NEXT
1. Login as admin: http://localhost:4201/login (admin@bayan.ae / Bayan@2024)
2. Navigate to the active tender → Bids tab
3. Verify submitted bid appears with correct bidder name and status
4. Open bid for technical evaluation
5. Test technical scoring against evaluation criteria
6. Test comparable sheet generation
7. Test financial evaluation
8. **Likely issues:** Evaluation workflow state transitions may need testing

### Step 4: Approval & Award
1. Test approval workflow (route tender for approval)
2. Login as approver (approver@bayan.ae / Bayan@2024) and test approver dashboard
3. Test approve/reject actions
4. Test tender award to winning bidder
5. Verify bidder notification (check MailHog at :8025)

### Step 5: Commit & cleanup
1. Commit all E2E fixes: `git add` the specific changed files (not agent-team changes)
2. Suggested commit message: `fix: portal E2E bugs — documents, navigation, clarifications, bulletins, bid submission`

---

## 5. Test Credentials

| Role | URL | Email | Password |
|------|-----|-------|----------|
| Admin | http://localhost:4201/login | admin@bayan.ae | Bayan@2024 |
| Tender Manager | http://localhost:4201/login | tendermgr@bayan.ae | Bayan@2024 |
| Approver | http://localhost:4201/login | approver@bayan.ae | Bayan@2024 |
| Bidder 1 | http://localhost:4201/portal/login | bidder@vendor.ae | Bayan@2024 |
| Bidder 2 | http://localhost:4201/portal/login | bidder2@vendor.ae | Bayan@2024 |

**Active Tender ID:** `7d9ba792-fa69-4b53-be01-52148f9ec6c1`

**Service URLs:**
| Service | URL |
|---------|-----|
| Frontend (dev) | http://localhost:4201 |
| API | http://localhost:5000 |
| Adminer (DB) | http://localhost:8080 |
| MinIO Console | http://localhost:9001 |
| MailHog | http://localhost:8025 |
| Redis Commander | http://localhost:8081 |

---

## 6. Known Issues / Technical Debt

1. **No `JsonStringEnumConverter`:** ASP.NET serializes all enums as integers. Frontend `normalizeClarification()` handles it in both admin and portal services, but adding the converter globally in `Program.cs` would be cleaner and prevent similar issues in bid submission/evaluation.

2. **Qualification workflow gap:** Bidders must be manually set to `Qualified` in DB. A proper admin UI flow (review documents → qualify bidder) is needed for production.

3. **MinIO presigned URLs:** Both admin and portal controllers now stream files directly through the API. For production with exposed MinIO, presigned URLs would be more performant.

4. **Property naming pattern:** Backend C# uses PascalCase DTOs, serialized to camelCase by ASP.NET. But enum values serialize as integers, and different DTOs for the same entity (e.g., `BidderQuestionDto` vs `PortalClarificationDto`) have different field names. Frontend service layer normalizes — expect similar issues in bid submission flow.

5. **Style budget warnings:** 7 components exceed 4.1KB inline style limit. Non-blocking.

6. **DB schema drift:** Some columns were added via raw SQL (not EF migrations). If DB container is recreated, run the SQL from `E2E_HANDOFF.md` Section 4.

7. **DraftAnswer vs Answered:** Backend has a 2-step flow (DraftAnswer → Answered) but frontend collapses both to `'answered'`. The PublishBulletin auto-approve workaround handles this, but a proper "Approve Answer" button in the admin UI would be better for production.
