# Bayan Tender — Manual E2E Testing Handoff

**Date:** 2026-02-09
**Session scope:** Manual walkthrough of the full tender lifecycle (admin + bidder portal)
**Status:** Partially complete — tested through clarifications; bid submission, evaluation, and award remain

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

### Admin Side (this session)
| Feature | Status |
|---------|--------|
| Bidder invitation (both bidders) | Working — status shows "Sent", DB records confirmed |

### Bidder Portal (this session)
| Feature | Status |
|---------|--------|
| Portal login | Working — `bidder@vendor.ae` / `Bayan@2024` |
| Tender listing on landing page | Working — published tender appears correctly |
| Tab navigation (Documents, Clarifications, Submit Bid) | Working — after rewrite to plain routerLink |
| Documents tab — file listing by folder | Working — grouped by folderPath with category inference |
| Documents tab — file download | Working — streams through API |
| Clarifications tab — submit question dialog | Working — BOQ sections load in dropdown |
| Clarifications tab — question submission | Working |
| Clarifications tab — status display | Fixed but NOT yet verified in browser (Docker was down) |

---

## 2. Bugs Found & Fixed (8 total)

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

---

## 3. Uncommitted Changes

All changes sit on top of commit `fbc6021`. **Build succeeds** (Angular `ng build` passes).

### Backend
| File | Changes |
|------|---------|
| `Controllers/PortalController.cs` | +`GetBoqSections` endpoint, `DownloadDocument` streams directly |

### Frontend
| File | Changes |
|------|---------|
| `core/models/portal.model.ts` | `TenderDocument` + `PortalClarification` interfaces rewritten to match backend DTOs |
| `core/services/portal.service.ts` | +`normalizeClarification()`, +`folderPathToCategory()`, fixed `organizeDocumentsByCategory()`, fixed download URLs |
| `features/portal/layout/portal-layout.component.ts` | Complete rewrite — plain routerLink, OnPush, 30s countdown |
| `features/portal/documents/portal-documents.component.ts` | Template bindings updated, preview uses blob download |
| `features/portal/clarifications/portal-clarifications.component.ts` | Status handling for all 7 ClarificationStatus enum values |

---

## 4. What to Do Next Session

### Step 0: Start up & verify Fix 8
1. Start Docker Desktop, wait until it's fully running
2. `docker compose up -d` from `BAYAN_TENDER/`
3. Wait for all services to be healthy (API on :5000, UI on :4201)
4. Open `http://localhost:4201/portal/login`
5. Login as `bidder@vendor.ae` / `Bayan@2024`
6. Navigate to tender → Clarifications → "My Questions" tab
7. **Verify** the previously submitted question shows "Submitted" status tag
8. Submit a new question and **verify** status appears immediately

### Step 1: Admin answers clarification
1. Login to admin: `http://localhost:4201/login` (admin@bayan.ae / Bayan@2024)
2. Navigate to tender → Clarifications tab
3. Find the bidder's submitted question
4. Draft and publish an answer (or create a Q&A Bulletin)
5. Switch back to bidder portal → verify answer appears in "Q&A Bulletins" tab

### Step 2: Bid Submission (bidder portal)
1. Navigate to "Submit Bid" tab
2. Upload required documents:
   - Priced BOQ (.xlsx)
   - Technical Methodology (.pdf)
   - Team CVs (.pdf)
   - Work Program (.pdf/.xlsx)
   - HSE Plan (.pdf)
3. Accept terms and submit bid
4. Verify bid receipt with receipt number
5. Test receipt PDF download
6. **Likely issues:** Similar DTO mismatch patterns may occur — watch for empty fields, 404s, or incorrect URLs

### Step 3: Bid Evaluation (admin side)
1. Navigate to tender → Bids tab
2. Verify submitted bid appears with correct bidder name and status
3. Open bid for technical evaluation
4. Test technical scoring against evaluation criteria
5. Test comparable sheet generation
6. Test financial evaluation
7. **Likely issues:** Evaluation workflow state transitions may need testing

### Step 4: Approval & Award
1. Test approval workflow (route tender for approval)
2. Login as approver (approver@bayan.ae / Bayan@2024) and test approver dashboard
3. Test approve/reject actions
4. Test tender award to winning bidder
5. Verify bidder notification (check MailHog at :8025)

### Step 5: Commit & cleanup
1. Commit all E2E fixes: `git add` the specific changed files (not agent-team changes)
2. Suggested commit message: `fix: portal E2E bugs — documents, navigation, clarifications, download streaming`

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

1. **No `JsonStringEnumConverter`:** ASP.NET serializes all enums as integers. Frontend `normalizeClarification()` handles it, but adding the converter globally in `Program.cs` would be cleaner and prevent similar issues in bid submission/evaluation.

2. **Qualification workflow gap:** Bidders must be manually set to `Qualified` in DB. A proper admin UI flow (review documents → qualify bidder) is needed for production.

3. **MinIO presigned URLs:** Both admin and portal controllers now stream files directly through the API. For production with exposed MinIO, presigned URLs would be more performant.

4. **Property naming pattern:** Backend C# uses PascalCase DTOs, serialized to camelCase by ASP.NET. But enum values serialize as integers, and different DTOs for the same entity (e.g., `BidderQuestionDto` vs `PortalClarificationDto`) have different field names. Frontend service layer normalizes — expect similar issues in bid submission flow.

5. **Style budget warnings:** 7 components exceed 4.1KB inline style limit. Non-blocking.

6. **DB schema drift:** Some columns were added via raw SQL (not EF migrations). If DB container is recreated, run the SQL from `E2E_HANDOFF.md` Section 4.
