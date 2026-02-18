# Bayan Tender - Full E2E Demo Guide

> Step-by-step. No steps skipped. Short and simple.

---

## PHASE 1: ADMIN SETUP

### Step 1 - Login as Admin
- Open `http://localhost:4200`
- Email: `admin@bayan.ae`
- Password: `Bayan@2024`
- You land on the **Admin Dashboard**.

### Step 2 - Verify Users Exist
- Go to **Admin > Users** in the sidebar.
- Confirm these users exist (they come from seed data):
  - **Fatima Al Mazrouei** - Tender Manager
  - **Ahmed Al Hashimi** - Procurement Analyst
  - **Sara Al Dhaheri** - Approver (Level 1)
  - **Khalid Al Nuaimi** - Approver (Level 2)
  - **Tariq Al Mansoori** - Approver (Level 3)
- If any are missing, click **Add User** and create them.

### Step 3 - Verify Bidders Exist
- Go to **Admin > Bidders** in the sidebar.
- Confirm these bidder companies exist:
  - **ABC Construction LLC** (bidder@vendor.ae)
  - **Gulf MEP Services** (bidder2@vendor.ae)
  - **Omar Contracting** (omar@contracting.ae)
- If missing, click **Add Bidder** and create them.
- All bidder passwords: `Bayan@2024`

---

## PHASE 2: CREATE THE TENDER

### Step 4 - Start New Tender
- Log in as **Fatima Al Mazrouei** (Tender Manager).
- Click **Create New Tender** button on the dashboard.

### Step 5 - Wizard Step 1: Basic Info
- **Tender Title**: Dubai Marina Commercial Tower - Main Construction Works
- **Tender Number**: Leave auto-generated (TNR-2026-XXXX)
- **Client**: Select or type a client name
- **Category**: Construction
- **Estimated Budget**: 20,000,000 AED
- **Currency**: AED
- **Description**: Use text from `06_Tender_Details.md` in the starter pack.
- Click **Next**.

### Step 6 - Wizard Step 2: Dates
- **Issue Date**: Today
- **Submission Deadline**: 2 weeks from today
- **Clarification Deadline**: 1 week from today
- **Bid Validity Period**: 90 days
- Click **Next**.

### Step 7 - Wizard Step 3: Evaluation Criteria
- Add criteria from `04_Evaluation_Criteria.xlsx`:
  - Technical Approach & Methodology - 25%
  - Team Qualifications & Experience - 20%
  - Past Project Experience - 15%
  - Project Schedule & Program - 15%
  - HSE Plan & Compliance - 10%
  - Financial Capacity - 15%
- Total must equal 100%.
- Click **Next**.

### Step 8 - Wizard Step 4: Review & Create
- Review all details on the summary page.
- Click **Create Tender**.
- Tender is now in **Draft** status.

---

## PHASE 3: UPLOAD MASTER BOQ

### Step 9 - Go to BOQ Tab
- Open the tender you just created.
- Click the **BOQ** tab.

### Step 10 - Upload Master BOQ
- Click **Upload BOQ** or **Import BOQ**.
- Select file: `02_BOQ_Master_No_Prices.xlsx` from the starter pack.
- Bayan auto-detects columns: Item No., Description, Qty, Unit.
- All 4 columns should show **95% confidence**.

### Step 11 - Confirm Import
- Review the preview: 19 sections, 90 items.
- Click **Import** or **Confirm**.
- BOQ tab now shows the full tree-table with all items.
- **0 errors, 0 warnings** expected.

---

## PHASE 4: PUBLISH & INVITE BIDDERS

### Step 12 - Publish Tender
- Click the **Publish** button on the tender overview.
- Confirm the publish action.
- Tender status changes to **Open**.

### Step 13 - Invite Bidders
- Click **Invite Bidders** button.
- Select all 3 bidders:
  - ABC Construction LLC
  - Gulf MEP Services
  - Omar Contracting
- Click **Send Invitations**.
- Each bidder receives an email notification (check Mailhog at `http://localhost:8025`).

---

## PHASE 5: BIDDER SUBMISSIONS (repeat for each bidder)

### Step 14 - Bidder A Logs In
- Open a new browser / incognito window.
- Go to `http://localhost:4200/portal`
- Email: `bidder@vendor.ae`
- Password: `Bayan@2024`

### Step 15 - View Tender
- Bidder sees the tender in their **My Tenders** list.
- Click on it to see tender details, documents, BOQ.

### Step 16 - Upload Priced BOQ
- Go to **Submit Bid** page.
- Upload: `03_Priced_BOQ_Bidder_A_Al_Futtaim_Construction_LLC.xlsx`
- Document type: **Priced BOQ**

### Step 17 - Upload Supporting Documents
- Upload these (use PDFs from `sample_documents/Bidder_A/`):
  - **Methodology Statement** - Methodology_Statement.pdf
  - **Team CVs** - Team_CVs.pdf
  - **Construction Program** - Construction_Program.pdf
  - **HSE Plan** - HSE_Plan.pdf

### Step 18 - Submit Bid
- Click **Submit Bid**.
- Bidder receives a **Bid Receipt** with a unique receipt number.
- Save or screenshot the receipt page.

### Step 19 - Repeat for Bidder B
- Login: `bidder2@vendor.ae` / `Bayan@2024`
- Upload: `03_Priced_BOQ_Bidder_B_Emirates_Building_Systems_Co.xlsx`
- Upload supporting docs from `sample_documents/Bidder_B/`
- Submit bid.

### Step 20 - Repeat for Bidder C
- Login: `omar@contracting.ae` / `Bayan@2024`
- Upload: `03_Priced_BOQ_Bidder_C_Gulf_Contracting_Company_WLL.xlsx`
- Upload supporting docs from `sample_documents/Bidder_C/`
- Submit bid.

---

## PHASE 6: CLOSE & OPEN BIDS

### Step 21 - Close Tender
- Go back to admin view (Fatima / Tender Manager).
- The tender auto-closes when the submission deadline passes.
- Or manually close it if deadline is set to past.
- Status changes to **Closed**.

### Step 22 - Open Bids
- Go to the **Bids** tab.
- Click **Open Bids**.
- Confirm the bid opening.
- All 3 bids become visible with their details.
- Status changes to **Evaluation**.

---

## PHASE 7: IMPORT PRICED BOQs (repeat for each bidder)

### Step 23 - Start Bid Import for Bidder A
- In the **Bids** tab, click on **ABC Construction LLC**.
- Click **Import BOQ** button.

### Step 24 - Step 1: Parse
- Bayan parses the uploaded priced BOQ file.
- Shows detected columns: Item No., Description, Qty, Unit, Unit Rate, Amount.
- All 6 columns detected automatically.
- Click **Next**.

### Step 25 - Step 2: Map Columns
- Verify the column mappings are correct:
  - Item No. -> Item Number
  - Description -> Description
  - Qty -> Quantity
  - Unit -> UOM
  - Unit Rate -> Unit Rate
  - Amount -> Amount
- Click **Next**.

### Step 26 - Step 3: Match to BOQ
- Bayan matches bid items to the master BOQ.
- 90/90 items matched (100% match rate).
- Review any fuzzy matches if shown.
- Click **Next**.

### Step 27 - Step 4: Normalize
- FX Rate: 1.0 (same currency AED).
- UOM conversions: none needed (all UOMs match).
- Click **Next**.

### Step 28 - Step 5: Validate
- Formula check: Amount = Qty x Rate (within 1% tolerance).
- **0 errors, 0 warnings** expected.
- Coverage: 100%.
- Click **Next**.

### Step 29 - Step 6: Execute Import
- Click **Import** or **Execute**.
- Import completes successfully.
- 90 items imported.
- Total: **AED 17,494,400** (Bidder A).

### Step 30 - Import Bidder B
- Repeat Steps 23-29 for Gulf MEP Services.
- Total: **AED 18,583,690**.

### Step 31 - Import Bidder C
- Repeat Steps 23-29 for Omar Contracting.
- Total: **AED 16,519,300** (lowest bidder).

---

## PHASE 8: EVALUATION

### Step 32 - View Comparable Sheet
- Go to the **Evaluation** tab.
- Click **Comparable Sheet**.
- All 3 bidders' prices shown side-by-side for every BOQ item.
- Lowest price per item highlighted in green.
- Highest price highlighted in red.
- Grand totals at the bottom.

### Step 33 - Review Outliers
- Outlier items are flagged (deviation > 30% from average).
- Click on any flagged item to see the details.

### Step 34 - Technical Scoring
- Go to **Technical Scoring** sub-tab.
- A panel member scores each bidder on each criterion (1-100).
- Fill in scores for all 3 bidders across all 6 criteria.
- Click **Submit Scores**.

### Step 35 - View Combined Scorecard
- Go to **Combined Scorecard** sub-tab.
- Shows both technical and commercial scores.
- Commercial score is auto-calculated (lowest bidder gets highest score).
- Weighted formula: (Technical x Weight) + (Commercial x Weight) = Final Score.

### Step 36 - Run Sensitivity Analysis
- Click **Sensitivity Analysis** button.
- Choose different weight splits (e.g., 40/60, 50/50, 60/40).
- See how changing weights affects the ranking.
- Up to 9 different scenarios shown side-by-side.

---

## PHASE 9: APPROVAL WORKFLOW

### Step 37 - Setup Approval Workflow
- Go to the **Approval** tab.
- Click **Start Approval Workflow**.
- Add 3 approval levels:
  - **Level 1**: Sara Al Dhaheri
  - **Level 2**: Khalid Al Nuaimi
  - **Level 3**: Tariq Al Mansoori
- Click **Initiate Workflow**.

### Step 38 - Level 1 Approval
- Log in as **Sara Al Dhaheri**.
- She sees the pending approval on her dashboard.
- Click on it, review the evaluation.
- Select **Approve** and add a comment.
- Click **Submit Decision**.
- Level 1 turns green. Level 2 becomes active.

### Step 39 - Level 2 Approval
- Log in as **Khalid Al Nuaimi**.
- Review and **Approve**.
- Level 2 turns green. Level 3 becomes active.

### Step 40 - Level 3 Approval (Final)
- Log in as **Tariq Al Mansoori**.
- Review and **Approve**.
- All 3 levels turn green.
- Workflow status: **Complete**.

---

## PHASE 10: AWARD

### Step 41 - Tender Awarded
- Tender status automatically changes to **Awarded**.
- The winning bidder is shown on the tender overview.
- Award notification emails sent to all bidders (check Mailhog).

### Step 42 - Generate Award Pack (if available)
- Go to the **Evaluation** tab.
- Click **Generate Award Pack**.
- Downloads a summary document with:
  - Comparable sheet
  - Scorecard
  - Approval history
  - Recommendation

### Step 43 - Verify on Portal
- Log in as the winning bidder on the portal.
- They can see the award status on their tender.

---

## PHASE 11: OPTIONAL DEMO FEATURES

### Rejection Flow
- Instead of approving at any level, select **Reject**.
- Add rejection reason.
- The workflow stops. Tender Manager can start a new workflow.

### Late Bid Handling
- If a bid arrives after the deadline, it shows as a **Late Bid**.
- Admin can choose to **Accept** or **Reject** the late bid.
- Rejected late bids are excluded from evaluation.

### Clarifications
- Bidders can submit questions through the portal.
- Admin responds with answers or bulletins.
- All bidders see published bulletins.

### Documents Tab
- Upload additional tender documents (drawings, specs, addenda).
- Bidders can download them from the portal.

### Vendor Pricing Dashboard
- View historical pricing across tenders.
- Search by vendor, item, or category.
- Compare rates across multiple bids.

### Audit Logs
- Go to **Admin > Audit Logs**.
- Every action is logged: who did what, when.
- Filter by user, action type, or date range.

---

## QUICK REFERENCE: STARTER PACK FILES

| File | Used In | Step |
|------|---------|------|
| `02_BOQ_Master_No_Prices.xlsx` | Upload master BOQ | Step 10 |
| `03_Priced_BOQ_Bidder_A_*.xlsx` | Bidder A submission | Step 16 |
| `03_Priced_BOQ_Bidder_B_*.xlsx` | Bidder B submission | Step 19 |
| `03_Priced_BOQ_Bidder_C_*.xlsx` | Bidder C submission | Step 20 |
| `04_Evaluation_Criteria.xlsx` | Reference for criteria setup | Step 7 |
| `05_Bidder_List.xlsx` | Reference for bidder details | Step 3 |
| `06_Tender_Details.md` | Reference for tender fields | Step 5 |
| `07_UOM_Reference.xlsx` | Reference for valid UOM codes | - |
| `sample_documents/Bidder_*/` | Supporting bid documents | Steps 17, 19, 20 |

---

## EXPECTED RESULTS

| Bidder | Total (AED) | Rank |
|--------|------------|------|
| Omar Contracting | 16,519,300 | 1 (Lowest) |
| ABC Construction LLC | 17,494,400 | 2 |
| Gulf MEP Services | 18,583,690 | 3 (Highest) |

**All 3 bids**: 90 items, 0 errors, 0 warnings, 100% BOQ coverage.

---

## LOGIN CHEAT SHEET

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@bayan.ae | Bayan@2024 |
| Tender Manager | fatima@bayan.ae | Bayan@2024 |
| Analyst | ahmed@bayan.ae | Bayan@2024 |
| Approver L1 | sara@bayan.ae | Bayan@2024 |
| Approver L2 | khalid@bayan.ae | Bayan@2024 |
| Approver L3 | tariq@bayan.ae | Bayan@2024 |
| Bidder A | bidder@vendor.ae | Bayan@2024 |
| Bidder B | bidder2@vendor.ae | Bayan@2024 |
| Bidder C | omar@contracting.ae | Bayan@2024 |

**Admin URL**: http://localhost:4200
**Portal URL**: http://localhost:4200/portal
**Mailhog**: http://localhost:8025
