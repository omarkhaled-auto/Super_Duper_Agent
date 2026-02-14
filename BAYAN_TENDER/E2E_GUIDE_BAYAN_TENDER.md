# Bayan Tender Management System - Complete E2E Guide

> **Project**: The Joud Tower | **Value**: AED 800,000,000 | **Client**: Cubic Engineering Consultancy
> **Date**: February 14, 2026
> **Environment**: Angular 18+ frontend (localhost:4200) + ASP.NET Core backend (localhost:5000) + PostgreSQL (Docker: bayan-db)

---

## Table of Contents

1. [Prerequisites & Environment](#1-prerequisites--environment)
2. [Task 1: Account Creation](#2-task-1-account-creation)
3. [Task 2: Tender Creation](#3-task-2-tender-creation)
4. [Task 3: BOQ Creation](#4-task-3-boq-creation)
5. [Task 4: Bidder Submissions](#5-task-4-bidder-submissions)
6. [Task 5: Bid Opening, Evaluation & Award](#6-task-5-bid-opening-evaluation--award)
7. [Key Gotchas & Lessons Learned](#7-key-gotchas--lessons-learned)
8. [Database Reference](#8-database-reference)
9. [API Reference](#9-api-reference)

---

## 1. Prerequisites & Environment

### Infrastructure

| Service | Address | Notes |
|---------|---------|-------|
| Frontend (Angular) | `http://localhost:4200` | Angular 18+ with Material |
| Backend (ASP.NET Core) | `http://localhost:5000` | MediatR + CQRS pattern |
| PostgreSQL | `localhost:5432` | Docker container: `bayan-db` |
| MinIO (Object Storage) | `localhost:9000` | For document uploads |
| Redis | `localhost:6379` | Caching layer |

### Database Connection

```bash
docker exec -it bayan-db psql -U bayan_user -d bayan
```

### Default Credentials

- **All user passwords**: `Bayan@2024`
- **Admin account**: `admin@bayan.ae` / `Bayan@2024`
- **DB**: user=`bayan_user`, password=`BayanSecure123!`, database=`bayan`

### Critical Technical Notes

- **All enum columns are VARCHAR** storing STRING names (e.g., `"Submitted"`, `"Active"`, `"Awarded"`), NOT integer values. EF Core uses `HasConversion<string>()`.
- **User table**: Uses `first_name` + `last_name` columns (NOT `full_name`)
- **Tender reference column**: Just `reference` (NOT `reference_number` or `tender_reference`)
- **API responses** are wrapped in `ApiResponse<T>` with `{ success, data, message }` structure

---

## 2. Task 1: Account Creation

### Goal
Create 7 project-specific accounts with "joud" naming convention for all required roles.

### Step 1.1: Login as Admin

**Method**: Playwright MCP browser automation

1. Navigate to `http://localhost:4200/auth/login`
2. Fill email: `admin@bayan.ae`
3. Fill password: `Bayan@2024`
4. Click "Sign In"
5. Verify redirect to dashboard

```
Browser Actions:
- browser_navigate → http://localhost:4200/auth/login
- browser_snapshot → verify login form visible
- browser_fill_form → email + password fields
- browser_click → Sign In button
- browser_snapshot → verify dashboard loaded
```

### Step 1.2: Navigate to User Management

1. Click "Admin" in sidebar to expand submenu
2. Click "Users" submenu item
3. Verify user list page loads

### Step 1.3: Create Each User Account

For each of the 7 users, repeat this process:

1. Click "Add User" button
2. Fill the user form dialog:
   - First Name
   - Last Name
   - Email
   - Password: `Bayan@2024`
   - Role (from dropdown)
3. Click "Save" / "Create"
4. Verify success toast notification
5. Wait for toast to dismiss before next action

### Users Created

| # | Email | First Name | Last Name | Role | Purpose |
|---|-------|------------|-----------|------|---------|
| 1 | `joudtendermanager@bayan.ae` | Mansour | Al-Joud | TenderManager | Manages tender lifecycle |
| 2 | `joudanalyst@bayan.ae` | Layla | Al-Joud | CommercialAnalyst | Commercial evaluation |
| 3 | `joudpanelist@bayan.ae` | Saeed | Al-Joud | TechnicalPanelist | Technical scoring |
| 4 | `joudapprover1@bayan.ae` | Sultan | Al-Joud | Approver | Level 3 approver |
| 5 | `joudapprover2@bayan.ae` | Hessa | Al-Joud | Approver | Level 2 approver |
| 6 | `joudapprover3@bayan.ae` | Rashid | Al-Joud | Approver | Level 1 approver |
| 7 | `joudauditor@bayan.ae` | Mariam | Al-Joud | Auditor | Audit trail access |

### Step 1.4: Create Bidder Accounts (Admin → Bidders)

Navigate to Admin → Bidders and create 3 bidder companies:

| # | Company Name | Contact Email | CR Number |
|---|-------------|---------------|-----------|
| 1 | Joud Al Khaleej Construction LLC | alkhaleej@joud.ae | CR-JK-2024-001 |
| 2 | Joud Desert Star Contracting | desertstar@joud.ae | CR-DS-2024-002 |
| 3 | Joud Emirates Build LLC | emiratesbuild@joud.ae | CR-EB-2024-003 |

### Step 1.5: Create Client

Navigate to Admin → Clients and create:

| Field | Value |
|-------|-------|
| Company Name | Cubic Engineering Consultancy |
| Contact Person | Omar Al-Joud |
| Email | cubic@joud.ae |
| Phone | +971-4-555-0100 |

### Verification

```sql
-- Verify all users created
SELECT email, first_name, last_name, role, is_active
FROM users
WHERE email LIKE '%joud%'
ORDER BY role, email;

-- Verify bidders
SELECT company_name, contact_email, cr_number
FROM bidders
WHERE company_name LIKE '%Joud%';

-- Verify client
SELECT company_name, contact_person_name
FROM clients
WHERE company_name LIKE '%Cubic%';
```

---

## 3. Task 2: Tender Creation

### Goal
Create "The Joud Tower" tender with full details via the Tender Wizard.

### Step 2.1: Login as Tender Manager

1. Logout from admin
2. Login as `joudtendermanager@bayan.ae` / `Bayan@2024`

### Step 2.2: Launch Tender Wizard

1. Navigate to Tenders page
2. Click "Create Tender" button
3. The wizard has 4 steps: Basic Info → Criteria → Dates → Review

### Step 2.3: Basic Info Step

| Field | Value |
|-------|-------|
| Tender Title | The Joud Tower – Main Construction Contract |
| Description | Main construction contract for The Joud Tower, a 45-storey mixed-use development in Dubai, UAE. Scope includes substructure, superstructure, MEP, facade, interior finishes, landscaping, vertical transportation, fire & life safety systems, and IT/smart building infrastructure. Estimated project value: AED 800,000,000. |
| Client | Cubic Engineering Consultancy (select from dropdown) |
| Tender Type | Open |
| Evaluation Method | Lowest Price |
| Currency | AED |
| Estimated Budget | 800000000 |

Click "Next" to proceed.

### Step 2.4: Criteria Step

The system pre-populates default evaluation criteria. For this tender:

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Relevant Experience | 25% | Past projects of similar scale/type |
| Technical Approach & Methodology | 30% | Construction methodology and approach |
| Project Team Qualifications | 20% | Key personnel qualifications |
| Schedule & Programme | 15% | Project timeline and milestones |
| HSE Plan | 10% | Health, Safety & Environment plan |

**Total: 100%**

Click "Next" to proceed.

### Step 2.5: Dates Step

| Field | Value |
|-------|-------|
| Submission Deadline | 2026-02-28T17:00 |
| Opening Date | 2026-03-01T10:00 |
| Estimated Completion | 2026-05-31 |

Click "Next" to proceed.

### Step 2.6: Review & Submit

1. Review all entered information on the summary page
2. Click "Create Tender" / "Submit"
3. Verify success notification
4. Note the generated reference number: **TNR-2026-0005**

### Step 2.7: Publish the Tender

After creation, the tender is in "Draft" status. To make it available to bidders:

1. Navigate to Tender Details page
2. Click "Publish" button
3. Confirm the action
4. Verify status changes to "Published"

### Step 2.8: Invite Bidders

1. Go to "Invite Bidders" tab on Tender Details
2. Select all 3 Joud bidders from the bidder list
3. Click "Send Invitations"
4. Verify invitations sent

### Verification

```sql
-- Verify tender created
SELECT id, reference, title, status, tender_type, evaluation_method, currency, estimated_budget
FROM tenders
WHERE title LIKE '%Joud Tower%';

-- Expected: status = 'Published', tender_type = 'Open', evaluation_method = 'LowestPrice'
```

**Tender ID**: `a4a62672-9152-45c7-9864-3594a7265aec`

---

## 4. Task 3: BOQ Creation

### Goal
Create a Bill of Quantities with 10 sections and 43 items covering all construction disciplines.

### Step 3.1: Navigate to BOQ Tab

1. Open tender details for "The Joud Tower"
2. Click the "BOQ" tab

### Step 3.2: Create Sections and Items

The BOQ was created section by section. For each section:
1. Click "Add Section"
2. Enter section name and description
3. For each item in the section:
   - Click "Add Item" within the section
   - Fill: Description, Unit, Quantity, Unit Price (if applicable)

### Complete BOQ Structure

#### Section 1: Preliminaries & General Requirements (4 items)
| # | Description | Unit | Quantity |
|---|-------------|------|----------|
| 1.1 | Site establishment and temporary facilities | LS | 1 |
| 1.2 | Construction insurance (CAR policy) | LS | 1 |
| 1.3 | Performance bond & advance payment guarantee | LS | 1 |
| 1.4 | Health, safety & environmental management | Month | 36 |

#### Section 2: Substructure Works (4 items)
| # | Description | Unit | Quantity |
|---|-------------|------|----------|
| 2.1 | Piling works – bored cast-in-situ (1200mm dia.) | LM | 12000 |
| 2.2 | Pile caps and ground beams | M3 | 3500 |
| 2.3 | Raft foundation (2.5m thick) | M3 | 8000 |
| 2.4 | Basement retaining walls & waterproofing | M2 | 15000 |

#### Section 3: Superstructure – Concrete Frame (5 items)
| # | Description | Unit | Quantity |
|---|-------------|------|----------|
| 3.1 | Reinforced concrete columns (Grade C60) | M3 | 6000 |
| 3.2 | Reinforced concrete core walls | M3 | 9000 |
| 3.3 | Post-tensioned flat slabs (250mm) | M2 | 180000 |
| 3.4 | Reinforced concrete transfer beams | M3 | 1200 |
| 3.5 | Concrete staircase flights & landings | Nr | 90 |

#### Section 4: MEP – Mechanical, Electrical & Plumbing (6 items)
| # | Description | Unit | Quantity |
|---|-------------|------|----------|
| 4.1 | HVAC – chilled water system (central plant) | LS | 1 |
| 4.2 | Electrical MV/LV distribution & emergency power | LS | 1 |
| 4.3 | Plumbing & drainage (including water tanks) | LS | 1 |
| 4.4 | Fire fighting systems (wet riser, sprinklers) | LS | 1 |
| 4.5 | BMS – Building Management System | LS | 1 |
| 4.6 | ELV systems (CCTV, access control, intercom) | LS | 1 |

#### Section 5: Facade & Envelope (4 items)
| # | Description | Unit | Quantity |
|---|-------------|------|----------|
| 5.1 | Unitized curtain wall system (DGU, low-e) | M2 | 42000 |
| 5.2 | Aluminum composite panel cladding | M2 | 8000 |
| 5.3 | Stone cladding – podium levels | M2 | 5000 |
| 5.4 | Structural glazing & feature fins | M2 | 3000 |

#### Section 6: Interior Finishes (5 items)
| # | Description | Unit | Quantity |
|---|-------------|------|----------|
| 6.1 | Internal partitions (drywall & block) | M2 | 95000 |
| 6.2 | Raised access flooring – office levels | M2 | 45000 |
| 6.3 | Ceramic & porcelain tiling | M2 | 60000 |
| 6.4 | Painting & wall coverings | M2 | 200000 |
| 6.5 | Suspended ceilings (mineral fibre & GRG) | M2 | 150000 |

#### Section 7: External Works & Landscaping (4 items)
| # | Description | Unit | Quantity |
|---|-------------|------|----------|
| 7.1 | Hard landscaping (pavers, granite kerbs) | M2 | 12000 |
| 7.2 | Soft landscaping (irrigation, planting, turf) | M2 | 8000 |
| 7.3 | Swimming pool & water features | LS | 1 |
| 7.4 | External lighting & street furniture | LS | 1 |

#### Section 8: Vertical Transportation (3 items)
| # | Description | Unit | Quantity |
|---|-------------|------|----------|
| 8.1 | High-speed passenger lifts (floors 1-45) | Nr | 8 |
| 8.2 | Service & freight lifts | Nr | 3 |
| 8.3 | Escalators – podium levels | Nr | 6 |

#### Section 9: Fire & Life Safety (4 items)
| # | Description | Unit | Quantity |
|---|-------------|------|----------|
| 9.1 | Fire alarm & detection system | LS | 1 |
| 9.2 | Emergency voice communication (EVAC) | LS | 1 |
| 9.3 | Smoke management & pressurisation | LS | 1 |
| 9.4 | Fire-rated doors & penetration sealing | Nr | 850 |

#### Section 10: IT & Smart Building Infrastructure (4 items)
| # | Description | Unit | Quantity |
|---|-------------|------|----------|
| 10.1 | Structured cabling (Cat6A + fibre backbone) | LS | 1 |
| 10.2 | Server room & network infrastructure | LS | 1 |
| 10.3 | Smart home/office automation per floor | Nr | 45 |
| 10.4 | Visitor management & digital signage | LS | 1 |

**Total: 10 sections, 43 items**

### Verification

```sql
-- Verify BOQ sections
SELECT s.name, s.sort_order, COUNT(i.id) as item_count
FROM boq_sections s
LEFT JOIN boq_items i ON s.id = i.section_id
WHERE s.tender_id = 'a4a62672-9152-45c7-9864-3594a7265aec'
GROUP BY s.name, s.sort_order
ORDER BY s.sort_order;

-- Verify total items
SELECT COUNT(*) as total_items
FROM boq_items i
JOIN boq_sections s ON i.section_id = s.id
WHERE s.tender_id = 'a4a62672-9152-45c7-9864-3594a7265aec';
-- Expected: 43
```

---

## 5. Task 4: Bidder Submissions

### Goal
Submit 3 differently-priced BOQs with deliberate outliers to test the system's comparable sheet and analysis features.

### Pricing Strategy

| Section | Bidder 1 (Al Khaleej) | Bidder 2 (Desert Star) | Bidder 3 (Emirates Build) |
|---------|----------------------|----------------------|--------------------------|
| Preliminaries | Market rate | +5% | +3% |
| Substructure | -5% | +10% | Market rate |
| Superstructure | Market rate | +5% | -3% |
| **MEP** | Market rate | **+25% OUTLIER** | +8% |
| **Facade** | **-30% OUTLIER** | Market rate | +5% |
| Interior Finishes | +3% | -5% | Market rate |
| **Landscaping** | Market rate | +10% | **+40% OUTLIER** |
| Vertical Transport | -8% | Market rate | +5% |
| Fire & Life Safety | Market rate | +15% | -5% |
| IT & Smart Building | +5% | Market rate | +10% |

### Step 4.1: Generate Priced BOQ Files

A Python script (`generate_priced_boq.py`) was used to generate Excel files with realistic pricing for each bidder. The script:

1. Reads the BOQ structure from the database
2. Applies the pricing strategy (market rate + adjustments)
3. Generates `.xlsx` files with proper formatting

### Step 4.2: Submit Bids via API

For each bidder, the submission was done via direct API calls (more reliable than portal UI for bulk pricing):

**API Endpoint**: `POST /api/portal/tenders/{tenderId}/submit`

Each submission included:
- Bidder authentication (portal login)
- Commercial BOQ pricing (all 43 line items)
- Technical documents (placeholder PDF)

### Step 4.3: Alternative - Submit via Bidder Portal

If using the portal UI:

1. Navigate to `http://localhost:4200/portal/login`
2. Login with bidder portal credentials
3. Go to active tenders → The Joud Tower
4. Navigate to "Submit Bid" section
5. Upload priced BOQ Excel file
6. Upload technical proposal PDF
7. Click "Submit Bid"
8. Confirm submission

### Step 4.4: Import Bids (Admin Side)

As the Tender Manager, import each bid:

1. Go to Tender Details → Bids tab
2. Click "Import Bid"
3. Select bidder from dropdown
4. Upload the priced BOQ file
5. Map columns if needed
6. Click "Import"
7. Verify bid appears in list

### Final Bid Totals

| Bidder | Total Bid (AED) | Notable Outliers |
|--------|----------------|------------------|
| Joud Al Khaleej Construction LLC | **743,605,000** | Facade -30% below avg |
| Joud Desert Star Contracting | **843,315,000** | MEP +25% above avg |
| Joud Emirates Build LLC | **818,770,000** | Landscaping +40% above avg |

### Verification

```sql
-- Verify all bids submitted
SELECT b.id, bi.company_name as bidder, b.status, b.total_amount, b.is_late, b.submission_time
FROM bids b
JOIN bidders bi ON b.bidder_id = bi.id
WHERE b.tender_id = 'a4a62672-9152-45c7-9864-3594a7265aec'
ORDER BY b.total_amount;
```

**Bidder IDs**:
- Joud Al Khaleej: `8b29c03f-ea0c-45c0-a3b7-10e7bca23f1f`
- Joud Desert Star: `a8d3815f-ab2e-4893-a29d-782f82af26e7`
- Joud Emirates Build: `b32b7aa2-3bf3-40ea-956e-1c9b52e93065`

---

## 6. Task 5: Bid Opening, Evaluation & Award

This is the most complex task, involving multiple user roles and a strict sequence of operations.

### Phase 1: Bid Opening

#### Step 5.1: Open Bids

**User**: Tender Manager (`joudtendermanager@bayan.ae`)

**Method**: Playwright MCP (UI)

1. Navigate to Tender Details → Bids tab
2. Click "Open Bids" button
3. Confirm the **IRREVERSIBLE** action in the dialog
4. Verify all bids status changes to "Opened"
5. Bid amounts are now visible

**Alternative via API**:
```http
POST http://localhost:5000/api/tenders/{tenderId}/bids/open
Authorization: Bearer {tenderManagerToken}
```

**Response**: `OpenBidsResultDto` with list of opened bids and their amounts.

> **WARNING**: Bid opening is IRREVERSIBLE. Once opened, all bid amounts are permanently revealed.

#### Step 5.2: Verify Comparable Sheet

After opening bids:
1. Navigate to Evaluation tab → Comparable Sheet
2. Verify all 3 bidders visible with their pricing
3. Check outlier indicators (7 outliers detected based on pricing strategy)

### Phase 2: Technical Evaluation

#### Step 5.3: Set Up Technical Evaluation

**User**: Tender Manager (`joudtendermanager@bayan.ae`)

**Method**: API call (more efficient for programmatic setup)

```http
POST http://localhost:5000/api/tenders/{tenderId}/evaluation/setup
Authorization: Bearer {tenderManagerToken}
Content-Type: application/json

{
  "scoringMethod": 0,
  "blindMode": true,
  "technicalEvaluationDeadline": "2026-02-28T23:59:59Z",
  "panelistUserIds": ["0107f2fc-xxxx-xxxx-xxxx-xxxxxxxxxxxx"],
  "sendNotificationEmails": false
}
```

**Parameters explained**:
| Parameter | Value | Notes |
|-----------|-------|-------|
| `scoringMethod` | `0` | Numeric (0-10 scale) |
| `blindMode` | `true` | Hides bidder identity from panelists |
| `technicalEvaluationDeadline` | ISO datetime | When scoring must be completed |
| `panelistUserIds` | Array of GUIDs | Panelist user IDs (Saeed Al-Joud) |
| `sendNotificationEmails` | `false` | Skip emails in test environment |

**Response**:
```json
{
  "success": true,
  "data": {
    "evaluationStateId": "...",
    "panelistsAssigned": 1,
    "criteriaCount": 5,
    "success": true
  }
}
```

#### Step 5.4: Retrieve Required IDs

Before scoring, we need bidder IDs and criterion IDs.

**Get Evaluation Criteria**:
```sql
SELECT id, name, weight, sort_order
FROM evaluation_criteria
WHERE tender_id = 'a4a62672-9152-45c7-9864-3594a7265aec'
ORDER BY sort_order;
```

| Criterion | ID | Weight |
|-----------|----|--------|
| Relevant Experience | `{criterion1_id}` | 25% |
| Technical Approach & Methodology | `{criterion2_id}` | 30% |
| Project Team Qualifications | `{criterion3_id}` | 20% |
| Schedule & Programme | `{criterion4_id}` | 15% |
| HSE Plan | `{criterion5_id}` | 10% |

#### Step 5.5: Submit Technical Scores

**User**: Technical Panelist (`joudpanelist@bayan.ae`)

First, login as the panelist to get their auth token:

```http
POST http://localhost:5000/api/auth/login
Content-Type: application/json

{
  "email": "joudpanelist@bayan.ae",
  "password": "Bayan@2024"
}
```

Then submit all 15 scores (3 bidders x 5 criteria) in one batch:

```http
POST http://localhost:5000/api/tenders/{tenderId}/evaluation/scores
Authorization: Bearer {panelistToken}
Content-Type: application/json

{
  "scores": [
    // Bidder 1: Joud Al Khaleej Construction (strong commercial, decent technical)
    { "bidderId": "8b29c03f-...", "criterionId": "{criterion1_id}", "score": 7.0, "comment": "Good portfolio of tower projects in UAE" },
    { "bidderId": "8b29c03f-...", "criterionId": "{criterion2_id}", "score": 7.0, "comment": "Solid methodology, standard approach" },
    { "bidderId": "8b29c03f-...", "criterionId": "{criterion3_id}", "score": 8.0, "comment": "Strong project team with relevant experience" },
    { "bidderId": "8b29c03f-...", "criterionId": "{criterion4_id}", "score": 7.0, "comment": "Realistic schedule with adequate float" },
    { "bidderId": "8b29c03f-...", "criterionId": "{criterion5_id}", "score": 7.0, "comment": "Comprehensive HSE plan" },

    // Bidder 2: Joud Desert Star Contracting (weaker technical)
    { "bidderId": "a8d3815f-...", "criterionId": "{criterion1_id}", "score": 6.0, "comment": "Limited high-rise experience" },
    { "bidderId": "a8d3815f-...", "criterionId": "{criterion2_id}", "score": 6.0, "comment": "Generic methodology, lacks specificity" },
    { "bidderId": "a8d3815f-...", "criterionId": "{criterion3_id}", "score": 5.0, "comment": "Key personnel lack tower experience" },
    { "bidderId": "a8d3815f-...", "criterionId": "{criterion4_id}", "score": 6.0, "comment": "Aggressive schedule, limited float" },
    { "bidderId": "a8d3815f-...", "criterionId": "{criterion5_id}", "score": 6.0, "comment": "Adequate HSE plan" },

    // Bidder 3: Joud Emirates Build (strongest technical)
    { "bidderId": "b32b7aa2-...", "criterionId": "{criterion1_id}", "score": 9.0, "comment": "Exceptional portfolio, 3 similar towers completed" },
    { "bidderId": "b32b7aa2-...", "criterionId": "{criterion2_id}", "score": 8.0, "comment": "Innovative methodology with BIM integration" },
    { "bidderId": "b32b7aa2-...", "criterionId": "{criterion3_id}", "score": 8.0, "comment": "Highly qualified team, strong CVs" },
    { "bidderId": "b32b7aa2-...", "criterionId": "{criterion4_id}", "score": 7.0, "comment": "Well-structured programme" },
    { "bidderId": "b32b7aa2-...", "criterionId": "{criterion5_id}", "score": 8.0, "comment": "Award-winning HSE track record" }
  ],
  "isFinalSubmission": true
}
```

**Score ranges** (0-10 scale):
- **9-10**: Exceptional, exceeds requirements
- **7-8**: Good, meets requirements well
- **5-6**: Adequate, meets minimum requirements
- **3-4**: Below average, some concerns
- **1-2**: Poor, significant deficiencies (requires mandatory comment)

**Response**:
```json
{
  "success": true,
  "data": {
    "savedCount": 15,
    "success": true
  }
}
```

#### Step 5.6: Lock Technical Scores

**User**: Tender Manager (`joudtendermanager@bayan.ae`)

> **WARNING**: This is IRREVERSIBLE. Once locked, no further score modifications are possible.

```http
POST http://localhost:5000/api/tenders/{tenderId}/evaluation/lock-scores
Authorization: Bearer {tenderManagerToken}
Content-Type: application/json

{
  "confirm": true
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "lockedAt": "2026-02-14T...",
    "lockedBy": "Mansour Al-Joud",
    "incompletePanelists": 0,
    "success": true
  }
}
```

### Phase 3: Commercial Evaluation

#### Step 5.7: Calculate Commercial Scores

**User**: Tender Manager

```http
POST http://localhost:5000/api/tenders/{tenderId}/evaluation/calculate-commercial-scores
Authorization: Bearer {tenderManagerToken}
```

**Formula**: `(Lowest Total Price / Bidder's Total Price) x 100`

**Results**:

| Bidder | Total Price (AED) | Commercial Score | Rank |
|--------|-------------------|-----------------|------|
| Joud Al Khaleej | 743,605,000 | **100.00** | #1 |
| Joud Emirates Build | 818,770,000 | **90.81** | #2 |
| Joud Desert Star | 843,315,000 | **88.18** | #3 |

### Phase 4: Combined Evaluation

#### Step 5.8: Calculate Combined Scores

**User**: Tender Manager

```http
POST http://localhost:5000/api/tenders/{tenderId}/evaluation/calculate-combined-scores
Authorization: Bearer {tenderManagerToken}
Content-Type: application/json

{
  "technicalWeight": 40,
  "commercialWeight": 60
}
```

**Formula**: `(TechWeight/100 x TechScore) + (CommWeight/100 x CommScore)`

**Results**:

| Final Rank | Bidder | Tech Score | Tech Rank | Comm Score | Comm Rank | **Combined** | Recommended |
|-----------|--------|-----------|-----------|------------|-----------|-------------|-------------|
| **#1** | **Joud Al Khaleej** | 7.20 | #2 | 100.00 | #1 | **62.88** | **YES** |
| #2 | Joud Emirates Build | 8.00 | #1 | 90.81 | #2 | 57.69 | No |
| #3 | Joud Desert Star | 5.80 | #3 | 88.18 | #3 | 55.23 | No |

**Key Insight**: The technically strongest bidder (#1 in tech) did NOT win because the commercial weight (60%) favored the lowest-priced bidder. This is realistic for a "Lowest Price" evaluation method where technical only serves as qualification.

### Phase 5: Approval Workflow

#### Step 5.9: Initiate Approval

**Method**: Playwright MCP (UI)

1. Navigate to Tender Details → Combined Scorecard tab
2. Click "Start Approval" button
3. Confirmation dialog: "Start the approval workflow?"
4. Click "Confirm"
5. Success toast: "Approval workflow started successfully"

**What happens behind the scenes**:
- Creates `approval_workflows` record (status: InProgress)
- Creates 3 `approval_levels` records (sequential)
- Level 1 activated, others waiting
- Email notification sent to Level 1 approver

**Alternative via API**:
```http
POST http://localhost:5000/api/tenders/{tenderId}/approval/initiate
Authorization: Bearer {tenderManagerToken}
Content-Type: application/json

{
  "awardPackPdfPath": null,
  "approverUserIds": [
    "6d20bd29-...",  // Rashid (Level 1)
    "3bc07563-...",  // Hessa (Level 2)
    "8d489c11-..."   // Sultan (Level 3)
  ],
  "levelDeadlines": null,
  "approverChangeReason": null
}
```

**Rules**:
- Must provide exactly 3 approver user IDs
- Approvers are assigned sequentially (Level 1, 2, 3)
- Only users with "Approver" role can be assigned

#### Step 5.10: Level 1 Approval (Rashid)

**User**: Approver 1 (`joudapprover3@bayan.ae` - Rashid Al-Joud)

```http
# First, login as Rashid
POST http://localhost:5000/api/auth/login
Content-Type: application/json
{ "email": "joudapprover3@bayan.ae", "password": "Bayan@2024" }

# Submit approval decision
POST http://localhost:5000/api/tenders/{tenderId}/approval/decide
Authorization: Bearer {rashidToken}
Content-Type: application/json

{
  "decision": 0,
  "comment": "Level 1 approved. Evaluation process properly followed. Commercial analysis aligns with technical assessment. Recommending progression to Level 2."
}
```

**Decision enum values**:
- `0` = Approve
- `1` = Reject
- `2` = ReturnForRevision

**Response**:
```json
{
  "success": true,
  "data": {
    "levelNumber": 1,
    "decision": "Approved",
    "isWorkflowComplete": false,
    "message": "Approval recorded. Progressing to next level."
  }
}
```

#### Step 5.11: Level 2 Approval (Hessa)

**User**: Approver 2 (`joudapprover2@bayan.ae` - Hessa Al-Joud)

```http
# Login as Hessa
POST http://localhost:5000/api/auth/login
Content-Type: application/json
{ "email": "joudapprover2@bayan.ae", "password": "Bayan@2024" }

# Submit approval
POST http://localhost:5000/api/tenders/{tenderId}/approval/decide
Authorization: Bearer {hessaToken}
Content-Type: application/json

{
  "decision": 0,
  "comment": "Level 2 approved. Award recommendation to Joud Al Khaleej Construction is sound. Best value for money considering 40/60 technical/commercial split."
}
```

#### Step 5.12: Level 3 Approval (Sultan) - FINAL

**User**: Approver 3 (`joudapprover1@bayan.ae` - Sultan Al-Joud)

```http
# Login as Sultan
POST http://localhost:5000/api/auth/login
Content-Type: application/json
{ "email": "joudapprover1@bayan.ae", "password": "Bayan@2024" }

# Submit final approval
POST http://localhost:5000/api/tenders/{tenderId}/approval/decide
Authorization: Bearer {sultanToken}
Content-Type: application/json

{
  "decision": 0,
  "comment": "Final approval granted. Award to Joud Al Khaleej Construction LLC at AED 743,605,000. All evaluation procedures were conducted in accordance with procurement policy."
}
```

**Response** (Final Level):
```json
{
  "success": true,
  "data": {
    "levelNumber": 3,
    "decision": "Approved",
    "isWorkflowComplete": true,
    "message": "Final approval granted. Tender has been awarded."
  }
}
```

> **CRITICAL**: When the final (Level 3) approval is granted, the system **automatically** sets the tender status to **"Awarded"**.

### Phase 6: Final Verification

#### Step 5.13: Verify Award in Database

```sql
-- Check tender status
SELECT reference, title, status
FROM tenders
WHERE id = 'a4a62672-9152-45c7-9864-3594a7265aec';
-- Expected: status = 'Awarded'

-- Check approval workflow
SELECT aw.status as workflow_status,
       al.level_number, al.status as level_status,
       u.first_name || ' ' || u.last_name as approver,
       al.decision, al.decided_at
FROM approval_workflows aw
JOIN approval_levels al ON aw.id = al.workflow_id
JOIN users u ON al.approver_user_id = u.id
WHERE aw.tender_id = 'a4a62672-9152-45c7-9864-3594a7265aec'
ORDER BY al.level_number;
```

#### Step 5.14: Verify in UI

1. Navigate to tender details in browser
2. Verify status badge shows "Awarded" (green)
3. Check activity log shows "Tender was awarded"
4. Take final screenshot for documentation

---

## 7. Key Gotchas & Lessons Learned

### Database Schema Gotchas

| Issue | Wrong | Correct |
|-------|-------|---------|
| User name field | `full_name` | `first_name` + `last_name` |
| Tender reference | `reference_number` | `reference` |
| Enum storage | Integer values | VARCHAR strings (`"Submitted"`, `"Active"`, etc.) |
| Enum in API | String names | Integer values (`0`, `1`, `2`) |

### UI Gotchas

| Issue | Solution |
|-------|----------|
| Toast notifications block clicks on elements behind them | Wait for toast to auto-dismiss (~3-5 seconds) before clicking |
| Approval tab shows "No Approval Workflow" after initiating via Combined Scorecard button | Frontend display issue; the workflow exists in DB. Use API for approval decisions. |
| Dropdown panels overlap with other elements | Take a fresh snapshot after each interaction |
| Long forms require scrolling in dialogs | Use `browser_evaluate` with `scrollIntoView()` if needed |

### API Gotchas

| Issue | Solution |
|-------|----------|
| ScoringMethod is an integer in API | `0` = Numeric, `1` = PassFail, `2` = Letter |
| Decision is an integer in API | `0` = Approve, `1` = Reject, `2` = ReturnForRevision |
| Approval requires exactly 3 approvers | Must provide exactly 3 GUIDs in `approverUserIds` array |
| Scores require comments for edge values | Comment required if score < 3 or > 8 |
| Technical scores must be locked before commercial calculation | Enforced by backend |

### Process Order (STRICT)

```
1. Create Tender (Draft)
2. Create BOQ
3. Publish Tender
4. Invite Bidders
5. Bidders Submit Bids
6. Open Bids (IRREVERSIBLE)
7. Setup Technical Evaluation (assign panelists)
8. Panelists Submit Scores
9. Lock Technical Scores (IRREVERSIBLE)
10. Calculate Commercial Scores
11. Calculate Combined Scores
12. Initiate Approval Workflow
13. Level 1 → Level 2 → Level 3 Approval (sequential)
14. Tender Awarded (automatic on final approval)
```

> **IMPORTANT**: Steps 6, 9 are irreversible. Steps must be followed in order — the backend enforces state transitions.

---

## 8. Database Reference

### Key Tables

```sql
-- Core tables
users                    -- All system users
tenders                  -- Tender records
bidders                  -- Bidder companies
clients                  -- Client companies
bids                     -- Bid submissions
boq_sections             -- BOQ sections
boq_items                -- BOQ line items
bid_items                -- Priced BOQ items per bid

-- Evaluation tables
evaluation_criteria      -- Tender evaluation criteria
evaluation_state         -- Evaluation configuration (scoring method, blind mode)
evaluation_panels        -- Panelist assignments
technical_scores         -- Individual panelist scores
commercial_scores        -- Calculated commercial scores
combined_scorecards      -- Final combined rankings

-- Approval tables
approval_workflows       -- Workflow records
approval_levels          -- Individual approval levels (3 per workflow)

-- Supporting tables
documents                -- Uploaded documents
notifications            -- System notifications
audit_logs               -- Audit trail
```

### Useful Queries

```sql
-- Full tender status overview
SELECT t.reference, t.title, t.status,
       COUNT(DISTINCT b.id) as bid_count,
       aw.status as approval_status
FROM tenders t
LEFT JOIN bids b ON t.id = b.tender_id
LEFT JOIN approval_workflows aw ON t.id = aw.tender_id
WHERE t.id = '{tenderId}'
GROUP BY t.reference, t.title, t.status, aw.status;

-- Complete evaluation results
SELECT cs.final_rank, bi.company_name,
       cs.tech_score_avg, cs.commercial_score, cs.combined_score,
       cs.is_recommended
FROM combined_scorecards cs
JOIN bidders bi ON cs.bidder_id = bi.id
WHERE cs.tender_id = '{tenderId}'
ORDER BY cs.final_rank;

-- Approval trail
SELECT al.level_number, u.first_name || ' ' || u.last_name as approver,
       al.status, al.decision, al.comment, al.decided_at
FROM approval_levels al
JOIN approval_workflows aw ON al.workflow_id = aw.id
JOIN users u ON al.approver_user_id = u.id
WHERE aw.tender_id = '{tenderId}'
ORDER BY al.level_number;
```

---

## 9. API Reference

### Authentication

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@bayan.ae",
  "password": "Bayan@2024"
}

# Response: { "success": true, "data": { "token": "eyJ...", "refreshToken": "..." } }
# Use token in all subsequent requests:
# Authorization: Bearer {token}
```

### Tender Endpoints

| Method | Endpoint | Description | Role Required |
|--------|----------|-------------|---------------|
| GET | `/api/tenders` | List tenders | InternalUsers |
| POST | `/api/tenders` | Create tender | TenderManager |
| GET | `/api/tenders/{id}` | Get tender details | InternalUsers |
| POST | `/api/tenders/{id}/publish` | Publish tender | TenderManager |

### BOQ Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tenders/{id}/boq` | Get BOQ |
| POST | `/api/tenders/{id}/boq/sections` | Add section |
| POST | `/api/tenders/{id}/boq/sections/{sectionId}/items` | Add item |
| POST | `/api/tenders/{id}/boq/import` | Import BOQ from Excel |
| GET | `/api/tenders/{id}/boq/export` | Export BOQ to Excel |

### Bid Endpoints

| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| GET | `/api/tenders/{id}/bids` | List bids | BidImporters |
| GET | `/api/tenders/{id}/bids/{bidId}` | Bid details | BidImporters |
| POST | `/api/tenders/{id}/bids/open` | Open all bids (IRREVERSIBLE) | BidImporters |
| POST | `/api/tenders/{id}/bids/{bidId}/accept-late` | Accept late bid | BidImporters |
| POST | `/api/tenders/{id}/bids/{bidId}/reject-late` | Reject late bid | BidImporters |
| POST | `/api/tenders/{id}/bids/{bidId}/disqualify` | Disqualify bid | BidImporters |
| GET | `/api/tenders/{id}/bids/download-all` | Download all bids ZIP | BidImporters |

### Technical Evaluation Endpoints

| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| GET | `/api/tenders/{id}/evaluation/setup` | Get setup | TechnicalScoresViewers |
| POST | `/api/tenders/{id}/evaluation/setup` | Configure setup | TechnicalEvaluationSetup |
| GET | `/api/tenders/{id}/evaluation/panelists` | List panelists | TechnicalScoresViewers |
| GET | `/api/tenders/{id}/evaluation/my-assignments` | Panelist assignments | TechnicalScorers |
| GET | `/api/tenders/{id}/evaluation/bidders/{bidderId}/documents` | Bidder docs | TechnicalScorers |
| GET | `/api/tenders/{id}/evaluation/scores/{bidderId}` | Get scores | TechnicalScorers |
| POST | `/api/tenders/{id}/evaluation/scores` | Save scores | TechnicalScorers |
| GET | `/api/tenders/{id}/evaluation/summary` | Scores summary | TechnicalScoresViewers |
| POST | `/api/tenders/{id}/evaluation/lock-scores` | Lock scores (IRREVERSIBLE) | TechnicalScoresLockers |

### Commercial & Combined Evaluation Endpoints

| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| POST | `/api/tenders/{id}/evaluation/calculate-commercial-scores` | Calculate commercial | TenderManager |
| POST | `/api/tenders/{id}/evaluation/calculate-combined-scores` | Calculate combined | TenderManager |
| GET | `/api/tenders/{id}/evaluation/comparable-sheet` | Comparable sheet data | InternalUsers |
| GET | `/api/tenders/{id}/evaluation/combined-scorecard` | Combined scorecard | InternalUsers |

### Approval Endpoints

| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| GET | `/api/tenders/{id}/approval` | Approval status | InternalUsers |
| POST | `/api/tenders/{id}/approval/initiate` | Start approval | ApprovalInitiators |
| POST | `/api/tenders/{id}/approval/decide` | Submit decision | ApprovalDeciders |
| GET | `/api/tenders/{id}/approval/history` | Approval history | InternalUsers |
| GET | `/api/approvals/pending` | My pending approvals | ApprovalDeciders |
| GET | `/api/approvers` | List approver users | ApprovalInitiators |

### Role Mappings

| BayanRoles Constant | Includes Roles |
|---------------------|----------------|
| `InternalUsers` | Admin, TenderManager, CommercialAnalyst, TechnicalPanelist, Approver, Auditor |
| `BidImporters` | Admin, TenderManager |
| `TechnicalScoresViewers` | Admin, TenderManager, CommercialAnalyst, Auditor |
| `TechnicalScorers` | TechnicalPanelist |
| `TechnicalEvaluationSetup` | Admin, TenderManager |
| `TechnicalScoresLockers` | Admin, TenderManager |
| `ApprovalInitiators` | Admin, TenderManager |
| `ApprovalDeciders` | Approver |

---

## Appendix: Complete Entity Relationship Flow

```
Client (Cubic Engineering)
  └── Tender (The Joud Tower)
       ├── BOQ
       │    ├── Section 1: Preliminaries (4 items)
       │    ├── Section 2: Substructure (4 items)
       │    ├── ...
       │    └── Section 10: IT & Smart Building (4 items)
       │
       ├── Invited Bidders
       │    ├── Joud Al Khaleej Construction (Bidder 1)
       │    ├── Joud Desert Star Contracting (Bidder 2)
       │    └── Joud Emirates Build LLC (Bidder 3)
       │
       ├── Bids (after submission)
       │    ├── Bid 1: AED 743,605,000 (Al Khaleej)
       │    ├── Bid 2: AED 843,315,000 (Desert Star)
       │    └── Bid 3: AED 818,770,000 (Emirates Build)
       │
       ├── Evaluation
       │    ├── Criteria (5 weighted)
       │    ├── Technical Scores (15 entries: 3 bidders x 5 criteria)
       │    ├── Commercial Scores (3 entries)
       │    └── Combined Scorecards (3 entries, ranked)
       │
       └── Approval Workflow
            ├── Level 1: Rashid → APPROVED
            ├── Level 2: Hessa → APPROVED
            └── Level 3: Sultan → APPROVED (FINAL → Tender Awarded)
```

---

*Generated from end-to-end testing of the Bayan Tender Management System on February 14, 2026.*
*All operations performed using Playwright MCP browser automation and direct API calls.*
