# MISSION: CLOSE THE FINAL 3 GAPS — BAYAN TO 100% TODAY

You have 3 gaps to close. No excuses. No "code verified." No "partial pass." Every gap must end with Playwright MCP BROWSER screenshots proving it works. If something is broken, fix it. If something doesn't exist, build it. We are not stopping until this is done.

The system is running in Docker Compose:
- Frontend: http://localhost:4200
- API: http://localhost:5000
- MailHog: http://localhost:8025
- MinIO: http://localhost:9001

Accounts (all password: Bayan@2024):
- admin@bayan.ae, tendermgr@bayan.ae, bidder@vendor.ae, bidder2@vendor.ae
- approver@bayan.ae, approver2@bayan.ae, approver3@bayan.ae
- analyst@bayan.ae, auditor@bayan.ae, panelist1@bayan.ae

Existing tenders:
- TNR-2026-0003: AWARDED (complete lifecycle, 2 bids, approval done)
- TNR-2026-0002: AWARDED (previous test)
- TNR-2026-0001: ACTIVE

---

## GAP A: EXCEL BID IMPORT WIZARD (THE BIG ONE)

The bid-import-dialog component (~1,472 lines, 10-step wizard) has NEVER been opened in a browser. Last attempt tested a "quick import" API button — that is NOT the wizard. The wizard has: file upload -> column auto-detection -> data parsing -> UOM matching -> currency conversion -> fuzzy BOQ matching -> outlier flagging -> validation -> import confirmation.

### What you must do:

**Step 1: Read the component code.**
Find `bid-import-dialog.component.ts` (or similar name). Read it completely. Understand:
- How is the dialog triggered? What button opens it? What route?
- What does it expect as input (a file? what format? what columns?)
- What are the actual wizard steps?
- Does it call specific API endpoints? Which ones?

**Step 2: Create a REAL Excel test file.**
The previous test failed because mock files were 514 bytes of garbage. You need to create an actual Excel file that matches what the wizard expects. Read the component code to understand the expected format. Then:
```bash
pip install openpyxl --break-system-packages
```
Write a Python script that generates a proper Excel BOQ file with:
- Headers matching what the column auto-detection expects
- BOQ item numbers/descriptions matching the 20 items in TNR-2026-0003 (or TNR-2026-0001)
- Quantities, unit prices, totals
- Multiple items so fuzzy matching has something to work with
- Save it somewhere accessible

**Step 3: Set up the right conditions.**
The wizard probably needs a tender with BOQ items and a bid that hasn't been imported yet. Options:
- Use TNR-2026-0001 (Active) — check if it has BOQ items, add some if needed, create a bid
- OR create a brand new tender TNR-2026-0004 with BOQ items, invite a bidder, submit a bid
- The key requirement: a bid must exist that has an un-imported Excel BOQ file

**Step 4: Upload the real Excel file as a bid document.**
Submit a bid with your generated Excel file as the priced BOQ document.

**Step 5: Open the wizard through the browser.**
Navigate to the bid, find the import trigger. Open the actual multi-step wizard dialog — NOT the quick import button. If there are two different paths (quick import vs wizard), find the wizard path.

**Step 6: Walk through every step with screenshots.**
- `gapA-step01-upload.png` — file upload step
- `gapA-step02-columns.png` — column auto-detection/mapping
- `gapA-step03-parsing.png` — data parsing results
- `gapA-step04-uom.png` — UOM matching
- `gapA-step05-currency.png` — currency conversion (if applicable)
- `gapA-step06-matching.png` — fuzzy BOQ matching
- `gapA-step07-outliers.png` — outlier flagging
- `gapA-step08-validation.png` — validation results
- `gapA-step09-confirm.png` — import confirmation
- `gapA-step10-complete.png` — import success

If any step is broken, FIX IT, then screenshot the working version.

**Step 7: Verify the data landed.**
After import, go to the Evaluation > Comparable Sheet. The imported bid data should now appear in the bidder columns with actual prices. Screenshot: `gapA-comparable-with-data.png`

This gap is the #1 priority. This component is our showcase — "single component larger than most AI-generated apps." It MUST work.

---

## GAP B: APPROVAL REJECTION/RETURN FLOW

Last time this was skipped because "creating a new tender lifecycle would require 30+ minutes." That's fine. We have time. Do it.

### What you must do:

**Step 1: Create a fast-track tender for testing rejection.**
Create a new tender (TNR-2026-0004 or whatever is next). You can use the API to speed this up — create tender, add a few BOQ items, invite bidders, submit bids, close, open bids. The goal is to get a tender into a state where approval can be initiated.

Check what status the tender needs to be in for approval initiation. The previous report said "Evaluation" status is required. Figure out how to get there — it might need the tender to be closed and bids opened, or it might need evaluation scores entered.

**Step 2: Initiate approval workflow.**
Start a 3-level approval with the 3 approver accounts.

**Step 3: Login as Level 1 approver -> choose "Return for Revision".**
- Navigate to the approval tab
- Find the decision form
- Select "Return for Revision"
- Enter comment: "Evaluation methodology needs revision. Please update the technical scoring criteria weights and resubmit."
- Submit the decision
- Screenshot: `gapB-return-decision-form.png` — showing the Return for Revision option selected with comment
- Screenshot: `gapB-return-submitted.png` — showing the workflow state after return

**Step 4: Verify the returned state.**
- What does the workflow look like now? Does it show "Returned" status?
- Can the TenderManager see that it was returned?
- Screenshot: `gapB-returned-state-tm-view.png` — TenderManager's view of the returned workflow

**Step 5: Re-initiate or continue, then test rejection.**
If the workflow can be re-initiated after return:
- Start a new approval round
- Login as Level 1 approver -> Approve
- Login as Level 2 approver -> choose "Reject"
- Enter comment: "Technical compliance review failed. Bidder documentation does not meet DCD requirements."
- Submit rejection
- Screenshot: `gapB-reject-decision-form.png` — showing Reject selected
- Screenshot: `gapB-rejected-state.png` — showing rejected workflow state
- Screenshot: `gapB-tender-status-after-reject.png` — what status is the tender in now?

If rejection at Level 2 means the whole workflow fails, that's a valid business outcome — document it with screenshots.

**Step 6: Verify emails.**
Check MailHog for rejection/return notification emails.
- Screenshot: `gapB-return-email.png`
- Screenshot: `gapB-reject-email.png`

---

## GAP C: DOCUMENTS TAB IMPLEMENTATION

The admin-side Documents tab is a placeholder div saying "Document management will be implemented in a future milestone." The backend DocumentsController exists. MinIO is running. This needs to be built.

### What you must do:

**Step 1: Investigate what exists.**
- Read `DocumentsController.cs` — what endpoints are available?
- Read the documents service/repository — what operations are supported?
- Check MinIO setup — how are files stored? What bucket?
- Read how the bidder portal handles document upload (it works there) — reuse that pattern

**Step 2: Build the Documents Tab component.**
The Documents tab needs:
1. **List documents** — show all documents uploaded to a tender in a table (name, type/category, size, uploaded by, uploaded date, actions)
2. **Upload document** — button that opens a file upload dialog with category selection (Technical Specifications, Drawings, Terms & Conditions, General, etc.)
3. **Download document** — click to download any document
4. **Delete document** — with confirmation dialog
5. **Document categories** — dropdown or tags for organization

This should follow the exact same patterns used elsewhere in the app — PrimeNG p-table, same dialog patterns, same service patterns. Look at how the BOQ tab or Bidders tab is structured and follow that pattern exactly.

**Step 3: After implementation, rebuild the frontend Docker container.**
```bash
docker compose up -d --build frontend
```

**Step 4: Verify through Playwright MCP browser.**
- Navigate to any tender > Documents tab
- Screenshot: `gapC-documents-tab-empty.png` — shows real component (not placeholder), empty state with upload button
- Upload a document (any PDF or Excel file)
- Screenshot: `gapC-upload-dialog.png` — upload dialog with category selection
- Screenshot: `gapC-document-uploaded.png` — document appears in the table
- Download the document
- Screenshot: `gapC-download-working.png` — download triggered
- Delete the document (with confirmation)
- Screenshot: `gapC-delete-confirmation.png` — confirmation dialog
- Screenshot: `gapC-document-deleted.png` — document removed from table

---

## BONUS FIX: SENSITIVITY ANALYSIS — 5 vs 7 SCENARIOS

The evidence brief claims "7 weight splits (30/70 through 70/30)." Every E2E test shows 5 scenarios. Fix the discrepancy:

**Option A:** If the code supports 7 but only 5 are showing, fix it to show 7.
**Option B:** If the code only does 5, update it to do 7 (30/70, 35/65, 40/60, 45/55, 50/50, 55/45, 60/40, 65/35, 70/30 — that's actually 9, but at minimum do 7).
**Option C:** If 5 is the correct design, note that the evidence brief needs to be updated from 7 to 5.

Read the sensitivity analysis handler/component code, determine what's correct, fix if needed, and screenshot the final result:
- Screenshot: `bonus-sensitivity-scenarios.png` — showing the actual number of scenarios

---

## BONUS FIX: COMPARABLE SHEET WITH REAL BID DATA

The comparable sheet on TNR-2026-0003 shows "0 bidders" because BOQ prices were never imported. If you successfully complete Gap A (Excel import), the comparable sheet should populate with real data. Navigate to it and screenshot:
- Screenshot: `bonus-comparable-with-bid-prices.png` — showing actual prices in bidder columns, section subtotals, outlier highlighting

If Gap A is done on a different tender, that's fine — prove the comparable sheet works with real data on whatever tender has imported bids.

---

## EXECUTION ORDER

1. **Gap A first** (Excel Import Wizard) — this is the hardest and most impressive. Start with code reading, then create the Excel file, then set up test conditions, then walk through the wizard.

2. **Gap B second** (Rejection/Return) — create a new tender lifecycle and test both return and reject paths.

3. **Gap C third** (Documents Tab) — write spec, implement, rebuild, verify.

4. **Bonuses last** — sensitivity fix and comparable sheet data verification.

---

## OUTPUT REQUIREMENTS

Save all screenshots to `final-100-screenshots/`

When ALL gaps are closed, produce `VERIFIED-100-PERCENT-REPORT.md` with full results table, code changes summary, regression check, and final verdict.

## ABSOLUTE RULES

1. NO "code verified" — if you can't click it in the browser, it's not verified
2. NO "partial pass" — either it works end-to-end or it doesn't
3. NO skipping because "it would take too long" — we have all day
4. FIX what's broken, BUILD what's missing, PROVE everything with screenshots
5. Every screenshot must show REAL DATA, not empty states or placeholders
6. After all changes, verify TNR-2026-0003 still works (regression check)
7. Git commit after each gap is closed with clear messages
8. If something genuinely cannot work (architectural impossibility), explain WHY in detail — don't just skip it
9. The bar is: could an investor click through this system and see every feature work? That's 100%.

## TECHNOLOGY STACK
- Frontend: Angular 18 with PrimeNG, standalone components
- Backend: .NET 8, Clean Architecture (CQRS/MediatR), EF Core
- Database: PostgreSQL 16
- Storage: MinIO (S3-compatible)
- Cache: Redis
- Email: SMTP + MailHog (dev)
- Auth: JWT with 7 RBAC roles
- Docker Compose for all services
