# BAYAN Tender - Manual Testing Guide (P0-P7)

**Date:** 2026-02-07
**For:** Omar (manual verification before production)
**Prerequisites:** All Docker services running (`docker-compose up -d`)

---

## Quick Reference

| Service | URL | Purpose |
|---------|-----|---------|
| UI (nginx prod) | http://localhost:4200 | Angular production app |
| API | http://localhost:5000 | .NET 8 backend |
| MailHog | http://localhost:8025 | Catch-all email viewer |
| MinIO Console | http://localhost:9001 | Object storage browser |
| Adminer | http://localhost:8080 | PostgreSQL database viewer |
| Redis Commander | http://localhost:8081 | Redis cache viewer |
| Swagger | http://localhost:5000/swagger | API documentation |

### Credentials (all passwords: `Bayan@2024`)

| Role | Email | Access |
|------|-------|--------|
| Admin | admin@bayan.ae | Full system access |
| Tender Manager | tendermgr@bayan.ae | Create/manage tenders |
| Analyst | analyst@bayan.ae | Evaluation, scoring |
| Panelist | panelist1@bayan.ae | Technical evaluation |
| Approver | approver@bayan.ae | Approval workflow |
| Auditor | auditor@bayan.ae | Read-only audit |
| Bidder | bidder@vendor.ae | Portal only |

---

## P0: Seed Data + Full Lifecycle Smoke Test

**Goal:** Confirm the database has usable data and the basic happy path works.

### Step 1: Verify all services are healthy

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

Expected: All containers show `healthy` or `Up`. Key ones:
- `bayan-api` - healthy
- `bayan-ui-prod` - healthy
- `bayan-db` - healthy
- `bayan-redis` - healthy
- `bayan-minio` - healthy

```bash
curl -s http://localhost:5000/api/health | jq
```

Expected: `{"status":"Healthy","checks":[{"name":"postgresql","status":"Healthy"}]}`

```bash
curl -s http://localhost:4200 | findstr "app-root"
```

Expected: HTML containing `<app-root></app-root>` (nginx serving Angular).

### Step 2: Verify seed users exist

1. Open http://localhost:4200 in Chrome (incognito for clean state)
2. You should see the **BAYAN login page**
3. Enter `admin@bayan.ae` / `Bayan@2024`
4. Click **Login**
5. **Expected:** Redirected to `/dashboard` showing KPI cards and active tenders table
6. Sidebar should show: Dashboard, Tenders, Admin (Users, Clients, Bidders, Settings, Audit Logs)

### Step 3: Check Admin data pages

1. **Admin > Users** -- Should show 7 users (admin, tendermgr, analyst, panelist1, approver, auditor, bidder)
2. **Admin > Clients** -- May have "E2E Test Ministry" from previous E2E run
3. **Admin > Bidders** -- May have "E2E Test Vendor Corp"
4. **Admin > Settings** -- Should show system settings (default_currency=AED, default_bid_validity_days=90, etc.)

### Step 4: Quick API smoke test

```bash
# Login and get token
TOKEN=$(curl -s http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@bayan.ae\",\"password\":\"Bayan@2024\",\"rememberMe\":true}" \
  | jq -r ".data.accessToken")

echo "Token: ${TOKEN:0:20}..."

# Test key endpoints (all should return {"success":true,...})
curl -s http://localhost:5000/api/dashboard/stats -H "Authorization: Bearer $TOKEN" | jq ".success"
curl -s "http://localhost:5000/api/clients?page=1&pageSize=5" -H "Authorization: Bearer $TOKEN" | jq ".success"
curl -s "http://localhost:5000/api/tenders?page=1&pageSize=5" -H "Authorization: Bearer $TOKEN" | jq ".success"
curl -s "http://localhost:5000/api/bidders?page=1&pageSize=5" -H "Authorization: Bearer $TOKEN" | jq ".success"
```

### Step 5: Login with every role

Test each user in a separate incognito window or log out between each:

| # | Email | Expected After Login |
|---|-------|---------------------|
| 1 | admin@bayan.ae | Dashboard with full sidebar |
| 2 | tendermgr@bayan.ae | Dashboard with KPIs, New Tender button |
| 3 | analyst@bayan.ae | Dashboard, access to evaluation |
| 4 | panelist1@bayan.ae | Dashboard, technical evaluation access |
| 5 | approver@bayan.ae | Dashboard, pending approvals section |
| 6 | auditor@bayan.ae | Dashboard, read-only, audit logs accessible |
| 7 | bidder@vendor.ae | **Use /portal/login** (see P2) |

**P0 Pass Criteria:** All 6 internal users can login, dashboard loads, sidebar shows correct menu items per role.

---

## P1: Tender Wizard -> Bid Submission -> Award (Full Lifecycle)

**Goal:** Walk through the complete tender lifecycle end-to-end. This is the most important test.

### Phase A: Create a Client

1. Login as `admin@bayan.ae`
2. Go to **Admin > Clients**
3. Click **New Client** (+ button)
4. Fill in:
   - Name: `Ministry of Infrastructure`
   - Contact Person: `Mohammed Al-Rashid`
   - Email: `contact@moi.ae`
   - Phone: `+971-50-111-2222`
5. Click **Save**
6. **Expected:** Client appears in the clients list
7. **If it already exists** (from E2E global-setup), skip to Phase B

### Phase B: Create a Bidder

1. Go to **Admin > Bidders**
2. Click **New Bidder** (+ button)
3. Fill in:
   - Company Name: `Gulf Construction LLC`
   - Contact Person: `Ali Khan`
   - Email: `ali@gulfcon.ae`
   - CR Number: `CR-2026-MANUAL-001`
   - Phone: `+971-50-333-4444`
4. Click **Save**
5. **Expected:** Bidder appears in the bidders list

### Phase C: Create a Tender via Wizard

1. Login as `tendermgr@bayan.ae`
2. Click **New Tender** button (dashboard or tender list)
3. **Expected:** Wizard opens at Step 1 with a stepper showing 4 steps (Basic Info, Dates, Criteria, Review)

**Step 1 - Basic Info:**
- Title: `IT Infrastructure Upgrade 2026`
- Reference: (auto-generated or type `TNR-2026-MANUAL-001`)
- Description: `Procurement of servers, networking equipment, and installation services for HQ data center`
- Client: Select `Ministry of Infrastructure` (or the client you created)
- Tender Type: `Open`
- Currency: `AED`
- Click **Next**

**Step 2 - Dates:**
- Issue Date: Tomorrow
- Clarification Deadline: 2 weeks from now
- Submission Deadline: 4 weeks from now
- Opening Date: 4 weeks + 1 day from now
- Click **Next**

**Step 3 - Evaluation Criteria:**
- Technical Weight: `70`
- Commercial Weight: `30`
- Add criteria (weights must sum to 100):
  1. Technical Approach - Weight: 40
  2. Experience & Track Record - Weight: 35
  3. Team Composition - Weight: 25
- Click **Next**

**Step 4 - Review & Submit:**
- Review all details are correct
- Click **Create Tender** (or **Save as Draft**)
- **Expected:** Tender created, redirected to tender details page
- **Note the tender ID from the URL** (e.g., `/tenders/abc-def-123`)

### Phase D: Add BOQ Items

1. On the tender details page, click the **BOQ** tab
2. Click **Add Section**:
   - Section Number: `1`
   - Title: `General Requirements`
   - Save
3. Click **Add Section** again:
   - Section Number: `2`
   - Title: `Hardware Supply`
   - Save
4. Under Section 1, click **Add Item**:
   - Item Number: `1.1`
   - Description: `Project Management`
   - UOM: `LS` (Lump Sum)
   - Quantity: `1`
   - Save
5. Under Section 1, click **Add Item**:
   - Item Number: `1.2`
   - Description: `Site Survey`
   - UOM: `nos` (Numbers)
   - Quantity: `5`
   - Save
6. Under Section 2, click **Add Item**:
   - Item Number: `2.1`
   - Description: `Server Rack 42U`
   - UOM: `nos` (Numbers)
   - Quantity: `3`
   - Save

**Expected:** BOQ tree shows 2 sections with 3 items total.

### Phase E: Invite Bidders

1. On the tender details page, find the bidder invitation section
2. Click **Invite Bidder**
3. Search for and select `Gulf Construction LLC` (the bidder you created)
4. Also invite the seeded bidder if available (`E2E Test Vendor Corp` or `ABC Construction LLC`)
5. Click **Send Invitation**
6. **Expected:** Bidders appear in the invited list
7. **Check MailHog** (http://localhost:8025): Invitation emails should appear

### Phase F: Publish the Tender

1. On the tender details page, click the **Publish** button
2. Confirm in the dialog
3. **Expected:** Tender status changes from `Draft` to `Published`/`Active`
4. Tender should now be visible on the bidder portal

### Phase G: Bidder Views Tender on Portal

(See P2 below for detailed portal testing)
1. Open new incognito window
2. Go to http://localhost:4200/portal/login
3. Login as `bidder@vendor.ae` / `Bayan@2024`
4. Find and click on the published tender
5. Browse Documents, BOQ, Clarifications tabs

### Phase H: Clarification Q&A

**As Bidder (portal):**
1. On the tender in the portal, go to Clarifications
2. Click **Ask Question**
3. Subject: `Server Specifications`
4. Question: `What are the minimum server specifications for the proposed solution?`
5. Submit

**As Tender Manager:**
1. Switch back to tendermgr window
2. Go to tender details > **Clarifications** tab
3. Find the question
4. Click to view, write answer: `Minimum: 2x Intel Xeon Gold, 256GB RAM, 4TB NVMe SSD`
5. Click **Answer** or **Approve Answer**
6. Optionally: **Publish Bulletin** to notify all bidders
7. Check MailHog for bulletin emails

### Phase I: Bid Opening & Evaluation

1. As Tender Manager, go to **Bids** tab
2. If bids were submitted via portal, click **Open Bids** (irreversible)
3. Go to **Evaluation** tab
4. Check **Comparable Sheet** -- shows bid data in grid
5. Check **Combined Scorecard** -- shows weighted scores

### Phase J: Approval Workflow

1. As Tender Manager, go to **Approval** tab
2. Click **Initiate Approval**
3. Select approver(s) from the dropdown
4. Set deadlines if prompted
5. Click **Submit**
6. **Check MailHog** for approval request email

**As Approver:**
1. Login as `approver@bayan.ae`
2. Go to Dashboard or navigate to the tender
3. Click **Approval** tab
4. Add comment: `Approved - meets all criteria`
5. Click **Approve**
6. **Expected:** Workflow progresses (or completes if single level)

**P1 Pass Criteria:** You can walk through Create Tender -> Add BOQ -> Invite Bidders -> Publish -> Clarification Q&A -> (Bid) -> Evaluation -> Approval without any 500 errors or blank screens.

---

## P2: Portal Problem Investigation

**Goal:** Confirm the bidder portal works. The portal uses a different auth endpoint and lazy-loaded Angular module.

### Step 1: Portal Login Page

1. Open Chrome **incognito**
2. Go to http://localhost:4200/portal/login
3. **Wait 10-15 seconds** -- the portal module lazy-loads and may take time on first visit
4. **Expected:** Portal login form appears (different from admin login)
5. If blank: Open DevTools (F12) > Console tab, look for errors
6. If redirected to `/auth/login`: The portal route guard may not recognize the path

### Step 2: Portal Login

1. Enter `bidder@vendor.ae` / `Bayan@2024`
2. Click **Login**
3. **Expected:** Redirected to portal dashboard/tender list

**If login fails, check:**
- DevTools > Network tab: Look at the login request
- Portal login hits `POST /api/portal/auth/login` (NOT `/api/auth/login`)
- The response should contain `accessToken` and `refreshToken`

### Step 3: Test Portal API Directly

```bash
# Test portal login endpoint
curl -s http://localhost:5000/api/portal/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"bidder@vendor.ae\",\"password\":\"Bayan@2024\",\"rememberMe\":true}" | jq

# Get portal token
PORTAL_TOKEN=$(curl -s http://localhost:5000/api/portal/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"bidder@vendor.ae\",\"password\":\"Bayan@2024\",\"rememberMe\":true}" \
  | jq -r ".data.accessToken")

# List available tenders on portal
curl -s "http://localhost:5000/api/portal/tenders?page=1&pageSize=10" \
  -H "Authorization: Bearer $PORTAL_TOKEN" | jq
```

If the API works but the UI doesn't, the problem is in the Angular portal module (lazy-loading or routing).

### Step 4: Portal Tender View

1. After logging in, click on a tender
2. **Expected:** Tender details with tabs: Documents, BOQ, Clarifications
3. Check each tab loads without errors

### Step 5: Portal Bid Submission

1. On the tender page, look for **Submit Bid** section
2. Upload a test PDF (any PDF, <100MB):
   - Select document type: `Priced BOQ`
   - Click Upload
3. Upload another file as `Methodology`
4. Click **Submit Bid**
5. **Expected:** Bid receipt generated, confirmation shown
6. Download the receipt PDF if available

**Known Issues:**
- Portal module lazy-loads -- first visit can take 5-15 seconds
- Portal uses `portal_*` localStorage keys (not `bayan_*`)
- Portal login uses `/api/portal/auth/login` (not `/api/auth/login`)

**P2 Pass Criteria:** Bidder can login to portal, view tender details, and see all tabs.

---

## P3: File Upload/Download (MinIO)

**Goal:** Verify document upload, MinIO storage, and download with pre-signed URLs.

### Step 1: Verify MinIO

1. Open http://localhost:9001
2. Login: `minioadmin` / `minioadmin`
3. **Expected:** MinIO console opens showing buckets
4. Look for a `bayan` or `documents` bucket

### Step 2: Upload via UI

1. Login as `tendermgr@bayan.ae` at http://localhost:4200
2. Navigate to a tender's details page
3. Look for **Documents** tab
4. Click **Upload Document**
5. Select a test file (PDF, DOCX, or XLSX, <100MB)
6. Click Upload
7. **Expected:** File appears in documents list with name, size, date

### Step 3: Verify in MinIO

1. Go back to MinIO console
2. Browse into the bucket
3. **Expected:** Uploaded file visible with correct size

### Step 4: Download

1. In BAYAN UI, find the uploaded document
2. Click **Download** icon
3. **Expected:** Browser downloads the file
4. **Verify:** File opens correctly and matches what you uploaded

### Step 5: Upload via API (if UI upload has issues)

```bash
# Get tender manager token
TOKEN=$(curl -s http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"tendermgr@bayan.ae\",\"password\":\"Bayan@2024\",\"rememberMe\":true}" \
  | jq -r ".data.accessToken")

# Replace TENDER_ID with an actual tender ID (from the URL when viewing a tender)
TENDER_ID="paste-tender-id-here"

# Upload a file (replace /path/to/file.pdf with a real file path)
curl -v -X POST "http://localhost:5000/api/tenders/${TENDER_ID}/documents/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@C:/path/to/test-file.pdf" \
  -F "folderPath=general"

# List documents for the tender
curl -s "http://localhost:5000/api/tenders/${TENDER_ID}/documents?page=1&pageSize=10" \
  -H "Authorization: Bearer $TOKEN" | jq
```

**P3 Pass Criteria:** Upload succeeds, file visible in MinIO, download returns correct file.

---

## P4: Email Notifications (MailHog)

**Goal:** Verify emails are sent for key business events.

### Step 1: Open MailHog

1. Open http://localhost:8025
2. **Expected:** MailHog inbox (may be empty or have previous test emails)

### Step 2: Trigger email events

Do each action, then immediately check MailHog:

**Event 1: Bidder Invitation**
1. As Tender Manager, invite a new bidder to a tender (Phase E of P1)
2. Check MailHog
3. **Expected:** Email to bidder with tender details and portal link

**Event 2: Clarification Bulletin**
1. As Tender Manager, answer a clarification and click **Publish Bulletin**
2. Check MailHog
3. **Expected:** Bulletin email to all invited bidders (may include PDF attachment)

**Event 3: Approval Request**
1. As Tender Manager, initiate approval workflow
2. Check MailHog
3. **Expected:** Email to Level 1 approver requesting review

**Event 4: Addendum Notification**
1. As Tender Manager, create and issue an addendum on a tender
2. Check MailHog
3. **Expected:** Email to all qualified bidders about the addendum

### Step 3: Verify email content

For each email in MailHog:
1. Click to open
2. Check: sender, subject line, recipient are correct
3. Check HTML body renders properly
4. Check any links point to valid URLs (they'll be localhost URLs)

**P4 Pass Criteria:** At least 1-2 of the above events produce emails in MailHog. If NONE arrive, the SMTP configuration may be wrong.

**If no emails arrive, check:**
```bash
# Verify MailHog SMTP is configured in the API
docker exec bayan-api cat /app/appsettings.Development.json | jq ".Email // .Smtp // .MailSettings // empty"
```

The API should be configured to use `mailhog:1025` as SMTP host.

---

## P5: Rate Limiting Verification

**Goal:** Confirm rate limiting is active and not too aggressive for normal use.

### Step 1: Check rate limit headers

```bash
curl -si http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@bayan.ae\",\"password\":\"Bayan@2024\",\"rememberMe\":true}" 2>&1 | findstr -i "ratelimit\|retry-after\|x-rate"
```

Look for headers like `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`.

### Step 2: Find the rate limit threshold

```bash
# Rapid-fire requests until you hit 429
for /L %i in (1,1,25) do @curl -s -o nul -w "Request %i: HTTP %%{http_code}\n" http://localhost:5000/api/auth/login -H "Content-Type: application/json" -d "{\"email\":\"admin@bayan.ae\",\"password\":\"Bayan@2024\",\"rememberMe\":true}"
```

Or in PowerShell:
```powershell
1..25 | ForEach-Object {
  $r = Invoke-WebRequest -Uri "http://localhost:5000/api/auth/login" -Method POST -ContentType "application/json" -Body '{"email":"admin@bayan.ae","password":"Bayan@2024","rememberMe":true}' -SkipHttpErrorCheck
  Write-Host "Request $_`: HTTP $($r.StatusCode)"
}
```

**Expected:** First N requests return 200, then 429 starts appearing.
**Record:** What N was? If N < 10, rate limiting may be too aggressive for dev/testing.

### Step 3: Check rate limit config

```bash
docker exec bayan-api cat /app/appsettings.Development.json
```

Look for `RateLimiting` or `RateLimit` section. Note the values.

**P5 Pass Criteria:** Rate limiting headers are present. Threshold is reasonable (>10 for login, >50 for general API).

---

## P6: E2E Timeout Fixes (Developer Reference)

**Goal:** Understand and plan fixes for the 44 E2E test timeouts.

### Step 1: Run the E2E suite

```bash
cd BAYAN_TENDER/e2e
npx playwright test --reporter=list 2>&1 | tee e2e-results.txt
```

### Step 2: Review results

The failures fall into 3 categories:

| Category | ~Count | Symptom | Root Cause |
|----------|--------|---------|------------|
| Element visibility timeout | 28 | `expect(el).toBeVisible()` exceeds 30s | UI element conditionally rendered (no data) |
| Navigation timeout | 10 | `waitForURL()` exceeds timeout | Angular lazy-loading in production mode |
| Portal lazy-load | 6 | Portal page never renders | Portal module takes >15s first load |

### Step 3: Quick fixes to try

**Option A: Increase global timeout** (in `playwright.config.ts`)
```
timeout: 30000  -->  60000
expect.timeout: 10000  -->  20000
```

**Option B: Seed more complete data** (in `global-setup.ts`)
The biggest fix is to seed complete lifecycle data:
1. Create a tender + BOQ + publish it
2. Submit a bid as the bidder
3. Open bids
4. Initiate approval workflow

Then tests checking for approval buttons, bid data, evaluation scores will find actual content instead of timing out on empty states.

**Option C: Fix portal lazy-load**
The portal module takes too long to initialize. Options:
- Add preload hint in `index.html`
- Increase portal-specific timeouts to 30s
- Check if the portal module bundle is too large

### Step 4: Re-run and compare

```bash
npx playwright test --reporter=list 2>&1 | tee e2e-results-after.txt
# Compare pass counts
```

**P6 Pass Criteria:** After fixes, target 0 failures (all remaining issues should gracefully skip, not fail).

---

## P7: Production Hardening Checklist

**Goal:** Review items that must change before deploying to a real domain.

### 7.1 Security Headers

```bash
curl -sI http://localhost:4200 | findstr -i "x-frame\|x-content\|x-xss\|security-policy\|referrer"
```

**Expected (all present):**
- `X-Frame-Options: SAMEORIGIN`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy: default-src 'self'; ...`
- `Referrer-Policy: strict-origin-when-cross-origin`

### 7.2 Authentication Security

```bash
# Unauthenticated access should return 401
curl -s -o nul -w "No token: HTTP %{http_code}\n" http://localhost:5000/api/tenders

# Wrong role should return 403
BIDDER_TOKEN=$(curl -s http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"bidder@vendor.ae\",\"password\":\"Bayan@2024\",\"rememberMe\":true}" \
  | jq -r ".data.accessToken")

curl -s -o nul -w "Bidder creating tender: HTTP %{http_code}\n" \
  http://localhost:5000/api/tenders \
  -H "Authorization: Bearer $BIDDER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Unauthorized\"}"
```

Expected: 401 for no token, 403 for wrong role.

### 7.3 Environment Variables to Change for Production

| Variable | Dev Value | Must Change To |
|----------|-----------|---------------|
| JWT Secret | Hardcoded in appsettings | Random 256-bit secret via secrets manager |
| DB Connection | `Host=db;Password=BayanSecure123!` | Real PostgreSQL (RDS/CloudSQL) |
| CORS Origins | `localhost:4200,4201` | Your real domain(s) |
| MinIO Endpoint | `minio:9000` | Real S3 or MinIO endpoint |
| SMTP Host | `mailhog:1025` | Real SMTP (SendGrid, SES, etc.) |
| ASPNETCORE_ENVIRONMENT | `Development` | `Production` |

### 7.4 Database Check

1. Open Adminer: http://localhost:8080
   - System: PostgreSQL
   - Server: `db` (or `localhost:5432`)
   - Username: `bayan_user`
   - Password: `BayanSecure123!`
   - Database: `bayan`
2. Verify:
   - Users table: all passwords are bcrypt hashed (start with `$2a$12$`)
   - No plain text secrets in any table
   - Key tables have indexes (check `tenders`, `bid_submissions`, `users`)

### 7.5 Services to Remove for Production

These are dev-only tools that should NOT be exposed in production:
- MailHog (port 8025) -- replace with real SMTP
- Adminer (port 8080) -- use direct DB access instead
- Redis Commander (port 8081) -- remove or restrict access
- MinIO Console (port 9001) -- restrict to admin VPN only

### 7.6 SSL/TLS

The nginx config currently only listens on port 80. For production:
1. Get SSL certificate (Let's Encrypt or your CA)
2. Add HTTPS listener on port 443 in nginx
3. Redirect HTTP -> HTTPS
4. Update `Content-Security-Policy` `connect-src` to use `https://`

### 7.7 Quick Performance Check

```bash
TOKEN=$(curl -s http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@bayan.ae\",\"password\":\"Bayan@2024\",\"rememberMe\":true}" \
  | jq -r ".data.accessToken")

# Time a dashboard stats request
curl -w "\nTime: %{time_total}s\n" -s -o nul \
  http://localhost:5000/api/dashboard/stats \
  -H "Authorization: Bearer $TOKEN"
```

Expected: < 500ms. If slower, check DB indexes and Redis caching.

**P7 Pass Criteria:** Security headers present, auth returns correct status codes, no plain-text secrets.

---

## Summary Checklist

| Priority | Test | Pass? |
|----------|------|-------|
| **P0** | All 8 Docker services healthy | [ ] |
| **P0** | curl health check returns Healthy | [ ] |
| **P0** | nginx serves Angular HTML at :4200 | [ ] |
| **P0** | Admin login works, dashboard loads | [ ] |
| **P0** | All 6 internal roles can login | [ ] |
| **P0** | API endpoints return success | [ ] |
| **P1** | Create client via Admin | [ ] |
| **P1** | Create bidder via Admin | [ ] |
| **P1** | Create tender via 4-step wizard | [ ] |
| **P1** | Add BOQ sections and items | [ ] |
| **P1** | Invite bidder to tender | [ ] |
| **P1** | Publish tender (Draft -> Active) | [ ] |
| **P1** | Submit clarification + answer it | [ ] |
| **P1** | View evaluation tabs | [ ] |
| **P1** | Initiate approval workflow | [ ] |
| **P1** | Approver approves the tender | [ ] |
| **P2** | Portal login page renders at /portal/login | [ ] |
| **P2** | Bidder login succeeds | [ ] |
| **P2** | Portal API works (curl test) | [ ] |
| **P2** | Portal tender details + tabs load | [ ] |
| **P2** | Bid submission from portal | [ ] |
| **P3** | MinIO console accessible | [ ] |
| **P3** | Upload document via UI | [ ] |
| **P3** | File visible in MinIO bucket | [ ] |
| **P3** | Download document works | [ ] |
| **P4** | MailHog accessible | [ ] |
| **P4** | Bidder invitation email received | [ ] |
| **P4** | Approval request email received | [ ] |
| **P5** | Rate limit headers present | [ ] |
| **P5** | Rate limit triggers at reasonable threshold | [ ] |
| **P6** | E2E suite runs, results captured | [ ] |
| **P6** | Timeout failures categorized | [ ] |
| **P7** | Security headers on nginx | [ ] |
| **P7** | 401 for unauthenticated | [ ] |
| **P7** | 403 for wrong role | [ ] |
| **P7** | No plain-text secrets in DB | [ ] |

---

*Guide prepared for manual verification of BAYAN Tender Management System - 2026-02-07*
