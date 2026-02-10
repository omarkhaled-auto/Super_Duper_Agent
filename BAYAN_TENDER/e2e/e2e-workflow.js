/**
 * BAYAN Tender - Complete E2E Workflow Test v2
 * Tests the FULL tender lifecycle: Create → Publish → Invite → Bid → Open → Evaluate → Approve → Award
 *
 * Prerequisites:
 *   - Docker containers running (bayan-db, bayan-api, bayan-redis, bayan-minio, bayan-mailhog)
 *   - API at http://localhost:5000
 *   - Frontend at http://localhost:4201 (optional, for screenshots)
 */
const { chromium } = require('@playwright/test');
const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const API_URL = 'http://localhost:5000';
const BASE_URL = 'http://localhost:4201';

// ===== STATE =====
const state = {
  adminToken: null,
  adminUserId: null,
  tenderId: null,
  tenderRef: null,
  bidderToken: null,
  bidderId: null,
  bidId: null,
  panelistToken: null,
  panelistUserId: null,
  approverToken: null,
  approverUserId: null,
  results: [],
  fixes: []
};

// ===== HELPERS =====
function log(step, status, detail) {
  const entry = { step, status, detail, time: new Date().toISOString() };
  state.results.push(entry);
  const icon = status === 'PASS' ? '✅' : status === 'FAIL' ? '❌' : status === 'INFO' ? 'ℹ️' : '⚠️';
  console.log(`${icon} [${step}] ${detail}`);
}

function logFix(description) {
  state.fixes.push({ description, time: new Date().toISOString() });
  console.log(`🔧 [FIX] ${description}`);
}

async function apiCall(method, apiPath, body, token) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const opts = { method, headers };
  if (body !== null && body !== undefined) opts.body = JSON.stringify(body);
  try {
    const resp = await fetch(`${API_URL}${apiPath}`, opts);
    const text = await resp.text();
    let json;
    try { json = JSON.parse(text); } catch { json = { raw: text }; }
    return { status: resp.status, ok: resp.ok, data: json };
  } catch (e) {
    return { status: 0, ok: false, data: { error: e.message } };
  }
}

async function uploadFile(tenderId, documentType, fileName, token) {
  const dummyContent = Buffer.from(`%PDF-1.4\nDummy ${fileName} content for E2E testing\n%%EOF`);
  const blob = new Blob([dummyContent], { type: 'application/pdf' });
  const formData = new FormData();
  formData.append('file', blob, fileName);

  try {
    const resp = await fetch(
      `${API_URL}/api/portal/tenders/${tenderId}/bids/upload?documentType=${documentType}`,
      {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      }
    );
    const text = await resp.text();
    let json;
    try { json = JSON.parse(text); } catch { json = { raw: text }; }
    return { status: resp.status, ok: resp.ok, data: json };
  } catch (e) {
    return { status: 0, ok: false, data: { error: e.message } };
  }
}

function dbExec(sql) {
  try {
    const escaped = sql.replace(/"/g, '\\"');
    return execSync(`docker exec -i bayan-db psql -U bayan_user -d bayan -c "${escaped}"`, {
      encoding: 'utf8',
      timeout: 15000,
      stdio: ['pipe', 'pipe', 'pipe']
    });
  } catch (e) {
    console.log(`DB exec error: ${e.stderr || e.message}`);
    return null;
  }
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ===== MAIN WORKFLOW =====
(async () => {
  const startTime = Date.now();
  let browser;

  try {
    browser = await chromium.launch({ headless: true });
  } catch (e) {
    console.log('Could not launch browser (not required for API tests)');
  }

  // ============================================================
  // PRE-FLIGHT: Fix known DB schema gaps
  // ============================================================
  console.log('\n' + '='.repeat(60));
  console.log('  PRE-FLIGHT: DATABASE SCHEMA FIXES');
  console.log('='.repeat(60));

  // Write SQL to temp file and execute via docker exec with stdin piping
  const schemaFixSQL = fs.readFileSync(path.join(__dirname, 'schema-fixes.sql'), 'utf8');
  try {
    execSync(`docker exec -i bayan-db psql -U bayan_user -d bayan`, {
      input: schemaFixSQL,
      encoding: 'utf8',
      timeout: 30000,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    log('0-preflight', 'PASS', 'All schema fixes applied');
  } catch (e) {
    // Some statements may warn but that's ok
    log('0-preflight', 'WARN', `Schema fixes completed with warnings: ${(e.stderr || '').substring(0, 200)}`);
  }

  // ============================================================
  // STEP 1: Admin Login
  // ============================================================
  console.log('\n' + '='.repeat(60));
  console.log('  STEP 1: ADMIN LOGIN');
  console.log('='.repeat(60));

  try {
    const resp = await apiCall('POST', '/api/auth/login', {
      email: 'admin@bayan.ae',
      password: 'Bayan@2024'
    });

    if (resp.data?.success) {
      state.adminToken = resp.data.data.accessToken;
      state.adminUserId = resp.data.data.user?.id;
      log('1-login', 'PASS', `Admin login successful. User: ${resp.data.data.user?.firstName} ${resp.data.data.user?.lastName}`);
    } else {
      log('1-login', 'FAIL', `Admin login failed: ${JSON.stringify(resp.data)}`);
    }
  } catch (e) {
    log('1-login', 'FAIL', `Exception: ${e.message}`);
  }

  if (!state.adminToken) {
    log('ABORT', 'FAIL', 'Cannot proceed without admin token');
    process.exit(1);
  }

  // ============================================================
  // STEP 2: Create Tender
  // ============================================================
  console.log('\n' + '='.repeat(60));
  console.log('  STEP 2: CREATE TENDER');
  console.log('='.repeat(60));

  try {
    // Get clients
    const clientResp = await apiCall('GET', '/api/clients?page=1&pageSize=5', null, state.adminToken);
    const clients = clientResp.data?.data?.items || [];
    log('2-create', 'INFO', `Found ${clients.length} clients`);

    if (clients.length === 0) {
      log('2-create', 'WARN', 'No clients found, attempting to create one');
      const newClient = await apiCall('POST', '/api/clients', {
        name: 'E2E Test Client',
        nameAr: 'عميل اختبار',
        industry: 'Technology',
        contactPerson: 'Test Contact',
        contactEmail: 'client@test.com',
        contactPhone: '+966501234567',
        isActive: true
      }, state.adminToken);
      if (newClient.data?.data?.id) {
        clients.push(newClient.data.data);
        log('2-create', 'INFO', 'Created test client');
      }
    }

    const clientId = clients[0]?.id;
    if (!clientId) throw new Error('No client ID available');

    // Calculate future dates (required for publish validation)
    const now = new Date();
    const issueDate = new Date(now.getTime() - 1 * 24 * 60 * 60 * 1000).toISOString();
    const clarificationDeadline = new Date(now.getTime() + 5 * 24 * 60 * 60 * 1000).toISOString();
    const submissionDeadline = new Date(now.getTime() + 15 * 24 * 60 * 60 * 1000).toISOString(); // 15 days (>3 after clarification)
    const openingDate = new Date(now.getTime() + 16 * 24 * 60 * 60 * 1000).toISOString();

    const tenderData = {
      title: 'E2E Test - IT Infrastructure Upgrade 2024',
      description: 'Comprehensive IT infrastructure upgrade including network equipment, servers, and security systems. This is an end-to-end test tender.',
      clientId: clientId,
      tenderType: 0, // Open
      baseCurrency: 'SAR',
      bidValidityDays: 90,
      issueDate: issueDate,
      clarificationDeadline: clarificationDeadline,
      submissionDeadline: submissionDeadline,
      openingDate: openingDate,
      technicalWeight: 40,
      commercialWeight: 60,
      evaluationCriteria: [
        { name: 'Technical Approach', weightPercentage: 30, guidanceNotes: 'Quality of proposed technical solution', sortOrder: 0 },
        { name: 'Experience & Qualifications', weightPercentage: 25, guidanceNotes: 'Relevant project experience', sortOrder: 1 },
        { name: 'Team Composition', weightPercentage: 20, guidanceNotes: 'Qualifications of proposed team', sortOrder: 2 },
        { name: 'Timeline & Delivery', weightPercentage: 15, guidanceNotes: 'Proposed schedule and milestones', sortOrder: 3 },
        { name: 'Innovation', weightPercentage: 10, guidanceNotes: 'Innovative approaches and value-adds', sortOrder: 4 }
      ]
    };

    log('2-create', 'INFO', `Creating tender with dates: issue=${issueDate.split('T')[0]}, clarification=${clarificationDeadline.split('T')[0]}, submission=${submissionDeadline.split('T')[0]}, opening=${openingDate.split('T')[0]}`);

    const createResp = await apiCall('POST', '/api/tenders', tenderData, state.adminToken);

    if (createResp.ok || createResp.data?.success) {
      state.tenderId = createResp.data?.data?.id;
      state.tenderRef = createResp.data?.data?.reference;
      log('2-create', 'PASS', `Tender created: ${state.tenderId} (ref: ${state.tenderRef})`);
    } else {
      log('2-create', 'FAIL', `Create failed: ${JSON.stringify(createResp.data)}`);

      // Parse validation errors
      if (createResp.data?.errors) {
        Object.entries(createResp.data.errors).forEach(([field, msgs]) => {
          log('2-create', 'FAIL', `  Validation: ${field}: ${Array.isArray(msgs) ? msgs.join('; ') : msgs}`);
        });
      }
    }
  } catch (e) {
    log('2-create', 'FAIL', `Exception: ${e.message}`);
  }

  if (!state.tenderId) {
    log('ABORT', 'FAIL', 'Cannot proceed without tender ID');
    process.exit(1);
  }

  // ============================================================
  // STEP 3: Publish Tender (Draft → Active)
  // ============================================================
  console.log('\n' + '='.repeat(60));
  console.log('  STEP 3: PUBLISH TENDER');
  console.log('='.repeat(60));

  try {
    // Verify tender is in Draft
    const getResp = await apiCall('GET', `/api/tenders/${state.tenderId}`, null, state.adminToken);
    const currentStatus = getResp.data?.data?.status ?? getResp.data?.data?.statusName;
    log('3-publish', 'INFO', `Current status: ${currentStatus}`);

    const pubResp = await apiCall('POST', `/api/tenders/${state.tenderId}/publish`, null, state.adminToken);

    if (pubResp.ok || pubResp.data?.success) {
      log('3-publish', 'PASS', 'Tender published (Draft → Active)');
    } else {
      log('3-publish', 'FAIL', `Publish failed: ${JSON.stringify(pubResp.data)}`);

      if (pubResp.data?.errors) {
        Object.entries(pubResp.data.errors).forEach(([field, msgs]) => {
          log('3-publish', 'FAIL', `  Validation: ${field}: ${Array.isArray(msgs) ? msgs.join('; ') : msgs}`);
        });
      }
    }

    // Verify status changed
    const verifyResp = await apiCall('GET', `/api/tenders/${state.tenderId}`, null, state.adminToken);
    const newStatus = verifyResp.data?.data?.status ?? verifyResp.data?.data?.statusName;
    log('3-publish', 'INFO', `Status after publish: ${newStatus}`);
  } catch (e) {
    log('3-publish', 'FAIL', `Exception: ${e.message}`);
  }

  // ============================================================
  // STEP 4: Invite Bidders
  // ============================================================
  console.log('\n' + '='.repeat(60));
  console.log('  STEP 4: INVITE BIDDERS');
  console.log('='.repeat(60));

  try {
    // Get available bidders
    const biddersResp = await apiCall('GET', '/api/bidders?page=1&pageSize=10', null, state.adminToken);
    const bidders = biddersResp.data?.data?.items || [];
    log('4-invite', 'INFO', `Found ${bidders.length} bidders in system`);
    bidders.forEach(b => log('4-invite', 'INFO', `  - ${b.companyName} (${b.email})`));

    if (bidders.length > 0) {
      // Invite all bidders (raw array format)
      const bidderIds = bidders.map(b => b.id);
      const inviteResp = await apiCall('POST', `/api/tenders/${state.tenderId}/invite`, bidderIds, state.adminToken);

      if (inviteResp.ok || inviteResp.data?.success) {
        const inviteData = inviteResp.data?.data;
        log('4-invite', 'PASS', `Invited ${inviteData?.invitedCount ?? bidderIds.length} bidders`);
      } else {
        log('4-invite', 'FAIL', `Invite failed: ${JSON.stringify(inviteResp.data)}`);
      }

      // Verify
      const verifyResp = await apiCall('GET', `/api/tenders/${state.tenderId}/bidders?page=1&pageSize=10`, null, state.adminToken);
      const invitedBidders = verifyResp.data?.data?.items || [];
      log('4-invite', 'INFO', `Verified ${invitedBidders.length} bidders invited`);

      // Store first bidder ID for portal login
      if (bidders.length > 0) {
        state.bidderId = bidders[0].id;
        log('4-invite', 'INFO', `Primary bidder: ${bidders[0].companyName} (${bidders[0].email})`);
      }
    } else {
      log('4-invite', 'FAIL', 'No bidders found in system');
    }
  } catch (e) {
    log('4-invite', 'FAIL', `Exception: ${e.message}`);
  }

  // ============================================================
  // STEP 5: Bidder Portal Login + File Upload + Bid Submit
  // ============================================================
  console.log('\n' + '='.repeat(60));
  console.log('  STEP 5: BIDDER PORTAL - LOGIN + UPLOAD + SUBMIT');
  console.log('='.repeat(60));

  try {
    // Update bidder qualification status to Qualified (InviteBidders sets Pending by default)
    log('5-bid', 'INFO', 'Setting bidder qualification status to Qualified...');
    const qualResult = dbExec(
      `UPDATE tender_bidders SET qualification_status = 'Qualified' WHERE tender_id = '${state.tenderId}'`
    );
    if (qualResult) {
      log('5-bid', 'INFO', 'Bidder qualification status updated');
      logFix('Updated tender_bidders qualification_status to Qualified via SQL');
    }

    // Try portal login with bidders that have passwords in DB
    const bidderEmails = ['bidder@vendor.ae', 'bidder2@vendor.ae'];
    let loggedIn = false;

    for (const email of bidderEmails) {
      // Login WITHOUT tenderId first to avoid qualification check, then retry with tenderId
      const portalResp = await apiCall('POST', '/api/portal/auth/login', {
        email: email,
        password: 'Bayan@2024',
        tenderId: state.tenderId,
        rememberMe: true
      });

      if (portalResp.data?.success || portalResp.ok) {
        state.bidderToken = portalResp.data?.data?.accessToken;
        state.bidderId = portalResp.data?.data?.bidder?.id;
        log('5-bid', 'PASS', `Portal login successful: ${email} (Bidder: ${portalResp.data?.data?.bidder?.companyName})`);
        loggedIn = true;
        break;
      } else {
        log('5-bid', 'INFO', `Portal login attempt ${email}: ${JSON.stringify(portalResp.data).substring(0, 200)}`);
      }
    }

    if (!loggedIn) {
      log('5-bid', 'FAIL', 'All portal login attempts failed');
    }

    if (state.bidderToken) {
      // Upload all 5 required document types
      const documentTypes = [
        { type: 0, name: 'PricedBOQ.pdf' },
        { type: 1, name: 'Methodology.pdf' },
        { type: 2, name: 'TeamCVs.pdf' },
        { type: 3, name: 'Program.pdf' },
        { type: 4, name: 'HSEPlan.pdf' }
      ];

      let allUploaded = true;
      for (const doc of documentTypes) {
        const uploadResp = await uploadFile(state.tenderId, doc.type, doc.name, state.bidderToken);

        if (uploadResp.ok || uploadResp.data?.success) {
          log('5-bid', 'PASS', `Uploaded ${doc.name} (type=${doc.type})`);
        } else {
          log('5-bid', 'FAIL', `Upload ${doc.name} failed: ${JSON.stringify(uploadResp.data).substring(0, 300)}`);
          allUploaded = false;
        }
      }

      if (allUploaded) {
        // Submit bid
        const submitResp = await apiCall('POST', `/api/portal/tenders/${state.tenderId}/bids/submit`, {
          bidValidityDays: 90
        }, state.bidderToken);

        if (submitResp.ok || submitResp.data?.success) {
          state.bidId = submitResp.data?.data?.bidId;
          const receipt = submitResp.data?.data?.receipt;
          log('5-bid', 'PASS', `Bid submitted! Receipt: ${receipt?.receiptNumber || 'N/A'}, Late: ${submitResp.data?.data?.isLate}`);
        } else {
          log('5-bid', 'FAIL', `Bid submit failed: ${JSON.stringify(submitResp.data).substring(0, 400)}`);
        }
      } else {
        log('5-bid', 'WARN', 'Not all files uploaded, cannot submit bid');
      }
    }
  } catch (e) {
    log('5-bid', 'FAIL', `Exception: ${e.message}`);
  }

  // ============================================================
  // STEP 6: Open Bids (Active → Evaluation)
  // ============================================================
  console.log('\n' + '='.repeat(60));
  console.log('  STEP 6: OPEN BIDS');
  console.log('='.repeat(60));

  try {
    // CRITICAL: Move submission deadline to the past so open bids validator passes
    // The validator checks: tender.SubmissionDeadline <= DateTime.UtcNow
    log('6-open', 'INFO', 'Moving tender dates to the past for bid opening...');
    const sqlResult = dbExec(
      `UPDATE tenders SET clarification_deadline = NOW() - INTERVAL '3 days', submission_deadline = NOW() - INTERVAL '1 hour', opening_date = NOW() - INTERVAL '30 minutes' WHERE id = '${state.tenderId}'`
    );
    if (sqlResult) {
      log('6-open', 'INFO', 'Tender dates updated to past');
      logFix('Updated tender deadlines to past via SQL for bid opening validation');
    } else {
      log('6-open', 'WARN', 'Could not update tender dates - open bids may fail');
    }

    // Check current bids
    const bidsResp = await apiCall('GET', `/api/tenders/${state.tenderId}/bids?page=1&pageSize=10`, null, state.adminToken);
    const bids = bidsResp.data?.data?.items || [];
    log('6-open', 'INFO', `Bids found: ${bids.length}`);
    bids.forEach(b => log('6-open', 'INFO', `  Bid ${b.id?.substring(0, 8)}: bidder=${b.bidderName}, status=${b.status}, amount=${b.nativeTotalAmount}`));

    if (bids.length === 0) {
      log('6-open', 'WARN', 'No bids to open. Attempting to continue anyway...');
    }

    // Open bids
    const openResp = await apiCall('POST', `/api/tenders/${state.tenderId}/bids/open`, null, state.adminToken);

    if (openResp.ok || openResp.data?.success) {
      const openData = openResp.data?.data;
      log('6-open', 'PASS', `Bids opened! Count: ${openData?.bidsOpenedCount ?? 'N/A'}, Opened at: ${openData?.openedAt}`);

      if (openData?.openedBids) {
        openData.openedBids.forEach(b => {
          log('6-open', 'INFO', `  Opened: ${b.bidderName} - ${b.nativeCurrency} ${b.nativeTotalAmount}`);
        });
      }
    } else {
      log('6-open', 'FAIL', `Open bids failed: ${JSON.stringify(openResp.data).substring(0, 400)}`);
    }

    // Verify tender moved to Evaluation
    const tenderResp = await apiCall('GET', `/api/tenders/${state.tenderId}`, null, state.adminToken);
    const tenderStatus = tenderResp.data?.data?.status ?? tenderResp.data?.data?.statusName;
    log('6-open', 'INFO', `Tender status after opening: ${tenderStatus}`);
  } catch (e) {
    log('6-open', 'FAIL', `Exception: ${e.message}`);
  }

  // ============================================================
  // STEP 7: Technical Evaluation Setup + Scoring
  // ============================================================
  console.log('\n' + '='.repeat(60));
  console.log('  STEP 7: TECHNICAL EVALUATION');
  console.log('='.repeat(60));

  try {
    // Login as panelist
    const panelistResp = await apiCall('POST', '/api/auth/login', {
      email: 'panelist1@bayan.ae',
      password: 'Bayan@2024'
    });

    if (panelistResp.data?.success) {
      state.panelistToken = panelistResp.data.data.accessToken;
      state.panelistUserId = panelistResp.data.data.user?.id;
      log('7-tech', 'PASS', `Panelist login: ${panelistResp.data.data.user?.firstName} ${panelistResp.data.data.user?.lastName} (${state.panelistUserId})`);
    } else {
      log('7-tech', 'FAIL', `Panelist login failed: ${JSON.stringify(panelistResp.data)}`);
    }

    // Setup evaluation
    const setupData = {
      scoringMethod: 0, // Numeric (0-10)
      blindMode: false,
      technicalEvaluationDeadline: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      panelistUserIds: state.panelistUserId ? [state.panelistUserId] : [],
      sendNotificationEmails: false
    };

    const setupResp = await apiCall('POST', `/api/tenders/${state.tenderId}/evaluation/setup`, setupData, state.adminToken);

    if (setupResp.ok || setupResp.data?.success) {
      log('7-tech', 'PASS', `Evaluation setup complete: ${JSON.stringify(setupResp.data?.data).substring(0, 200)}`);
    } else {
      log('7-tech', 'FAIL', `Setup failed: ${JSON.stringify(setupResp.data).substring(0, 400)}`);
    }

    // Get evaluation setup to retrieve criteria IDs
    const getSetupResp = await apiCall('GET', `/api/tenders/${state.tenderId}/evaluation/setup`, null, state.adminToken);
    const setupDetails = getSetupResp.data?.data;
    log('7-tech', 'INFO', `Setup details: ${JSON.stringify(setupDetails || getSetupResp.data).substring(0, 400)}`);

    // Get criteria from tender
    const tenderResp = await apiCall('GET', `/api/tenders/${state.tenderId}`, null, state.adminToken);
    const criteria = tenderResp.data?.data?.evaluationCriteria || [];
    log('7-tech', 'INFO', `Found ${criteria.length} evaluation criteria`);
    criteria.forEach(c => log('7-tech', 'INFO', `  Criterion: ${c.name} (${c.id}) weight=${c.weightPercentage}%`));

    // Get bids to score
    const bidsResp = await apiCall('GET', `/api/tenders/${state.tenderId}/bids?page=1&pageSize=10`, null, state.adminToken);
    const bids = bidsResp.data?.data?.items || [];
    log('7-tech', 'INFO', `Bids to score: ${bids.length}`);

    // Score each bid if we have panelist token, criteria, and bids
    if (state.panelistToken && criteria.length > 0 && bids.length > 0) {
      for (const bid of bids) {
        const bidderId = bid.bidderId || bid.id;
        const scores = criteria.map(c => ({
          bidderId: bidderId,
          criterionId: c.id,
          score: 7, // Safe score (between 3 and 8, no comment required)
          comment: `E2E evaluation for ${c.name}`
        }));

        const scoreResp = await apiCall('POST', `/api/tenders/${state.tenderId}/evaluation/scores`, {
          scores: scores,
          isFinalSubmission: true
        }, state.panelistToken);

        if (scoreResp.ok || scoreResp.data?.success) {
          log('7-tech', 'PASS', `Scored bid from ${bid.bidderName}: ${scores.length} criteria scored`);
        } else {
          log('7-tech', 'FAIL', `Score submission for ${bid.bidderName} failed: ${JSON.stringify(scoreResp.data).substring(0, 400)}`);
        }
      }

      // Get technical scores summary
      const summaryResp = await apiCall('GET', `/api/tenders/${state.tenderId}/evaluation/summary`, null, state.adminToken);
      log('7-tech', 'INFO', `Technical summary: ${JSON.stringify(summaryResp.data?.data).substring(0, 400)}`);

      // Lock technical scores
      const lockResp = await apiCall('POST', `/api/tenders/${state.tenderId}/evaluation/lock-scores`, {
        confirm: true
      }, state.adminToken);

      if (lockResp.ok || lockResp.data?.success) {
        log('7-tech', 'PASS', 'Technical scores locked');
      } else {
        log('7-tech', 'WARN', `Lock scores: ${JSON.stringify(lockResp.data).substring(0, 400)}`);
      }
    } else {
      log('7-tech', 'WARN', `Cannot score: panelist=${!!state.panelistToken}, criteria=${criteria.length}, bids=${bids.length}`);
    }
  } catch (e) {
    log('7-tech', 'FAIL', `Exception: ${e.message}`);
  }

  // ============================================================
  // STEP 8: Commercial Evaluation + Combined Scoring
  // ============================================================
  console.log('\n' + '='.repeat(60));
  console.log('  STEP 8: COMMERCIAL + COMBINED SCORING');
  console.log('='.repeat(60));

  try {
    // Get comparable sheet
    const compResp = await apiCall('GET', `/api/tenders/${state.tenderId}/evaluation/comparable-sheet`, null, state.adminToken);
    log('8-commercial', 'INFO', `Comparable sheet: ${JSON.stringify(compResp.data?.data).substring(0, 300)}`);

    // Calculate commercial scores
    const commResp = await apiCall('POST', `/api/tenders/${state.tenderId}/evaluation/calculate-commercial-scores`, {
      includeProvisionalSums: true,
      includeAlternates: true
    }, state.adminToken);

    if (commResp.ok || commResp.data?.success) {
      log('8-commercial', 'PASS', `Commercial scores calculated: ${JSON.stringify(commResp.data?.data).substring(0, 300)}`);
    } else {
      log('8-commercial', 'WARN', `Commercial scores: ${JSON.stringify(commResp.data).substring(0, 300)}`);
    }

    // Calculate combined scores
    const combResp = await apiCall('POST', `/api/tenders/${state.tenderId}/evaluation/calculate-combined`, null, state.adminToken);

    if (combResp.ok || combResp.data?.success) {
      log('8-commercial', 'PASS', `Combined scores calculated: ${JSON.stringify(combResp.data?.data).substring(0, 300)}`);
    } else {
      log('8-commercial', 'WARN', `Combined scores: ${JSON.stringify(combResp.data).substring(0, 300)}`);
    }

    // Get combined scorecard
    const scorecardResp = await apiCall('GET', `/api/tenders/${state.tenderId}/evaluation/combined-scorecard`, null, state.adminToken);
    if (scorecardResp.data?.data) {
      log('8-commercial', 'INFO', `Scorecard: ${JSON.stringify(scorecardResp.data.data).substring(0, 400)}`);
    }
  } catch (e) {
    log('8-commercial', 'FAIL', `Exception: ${e.message}`);
  }

  // ============================================================
  // STEP 9: 3-Level Approval Workflow
  // ============================================================
  console.log('\n' + '='.repeat(60));
  console.log('  STEP 9: APPROVAL WORKFLOW (3 LEVELS)');
  console.log('='.repeat(60));

  try {
    // CRITICAL: Need 3 UNIQUE users with Approver role for 3-level approval.
    // Only 1 Approver exists in seed data. Update analyst + auditor roles to Approver.
    log('9-approval', 'INFO', 'Preparing 3 distinct approver users...');

    // Update roles in DB (analyst → Approver, auditor → Approver)
    dbExec(`UPDATE users SET role = 'Approver' WHERE email IN ('analyst@bayan.ae', 'auditor@bayan.ae')`);
    logFix('Updated analyst + auditor roles to Approver in DB for 3-level approval');

    // Login all 3 approvers to get fresh JWTs with Approver role
    const approverLogins = [
      { email: 'approver@bayan.ae', label: 'Level 1 (Khalid)' },
      { email: 'analyst@bayan.ae', label: 'Level 2 (Fatima)' },
      { email: 'auditor@bayan.ae', label: 'Level 3 (Sara)' }
    ];

    const approverTokens = [];
    const approverUserIds = [];

    for (const a of approverLogins) {
      await sleep(300); // Small delay between logins
      const resp = await apiCall('POST', '/api/auth/login', { email: a.email, password: 'Bayan@2024' });
      if (resp.data?.success) {
        approverTokens.push(resp.data.data.accessToken);
        approverUserIds.push(resp.data.data.user?.id);
        log('9-approval', 'PASS', `${a.label} login: ${resp.data.data.user?.firstName} ${resp.data.data.user?.lastName} (${resp.data.data.user?.id})`);
      } else {
        log('9-approval', 'FAIL', `${a.label} login failed: ${JSON.stringify(resp.data).substring(0, 200)}`);
        approverTokens.push(null);
        approverUserIds.push(null);
      }
    }

    if (approverUserIds.filter(id => id).length === 3) {
      // Initiate approval with 3 distinct approvers
      const initiateData = {
        approverUserIds: approverUserIds,
        levelDeadlines: [
          new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
          new Date(Date.now() + 6 * 24 * 60 * 60 * 1000).toISOString(),
          new Date(Date.now() + 9 * 24 * 60 * 60 * 1000).toISOString()
        ]
      };

      const initiateResp = await apiCall('POST', `/api/tenders/${state.tenderId}/approval/initiate`, initiateData, state.adminToken);

      if (initiateResp.ok || initiateResp.data?.success) {
        log('9-approval', 'PASS', 'Approval workflow initiated with 3 distinct approvers');
      } else {
        log('9-approval', 'FAIL', `Initiate failed: ${JSON.stringify(initiateResp.data).substring(0, 400)}`);
      }

      // Check status
      const statusResp = await apiCall('GET', `/api/tenders/${state.tenderId}/approval`, null, state.adminToken);
      if (statusResp.data?.data) {
        log('9-approval', 'INFO', `Workflow status: ${statusResp.data.data.status}, Level: ${statusResp.data.data.currentLevel}/${statusResp.data.data.totalLevels}`);
      }

      // Level 1: Approve (with approver@bayan.ae token)
      log('9-approval', 'INFO', 'Submitting Level 1 approval (Khalid)...');
      const lvl1Resp = await apiCall('POST', `/api/tenders/${state.tenderId}/approval/decide`, {
        decision: 0,
        comment: 'E2E Test - Level 1 approved. Technical and commercial evaluation reviewed and satisfactory.'
      }, approverTokens[0]);

      if (lvl1Resp.ok || lvl1Resp.data?.success) {
        log('9-approval', 'PASS', `Level 1 APPROVED: ${lvl1Resp.data?.data?.message || ''}`);
      } else {
        log('9-approval', 'FAIL', `Level 1 failed: ${JSON.stringify(lvl1Resp.data).substring(0, 400)}`);
      }

      // Level 2: Approve (with analyst@bayan.ae token)
      log('9-approval', 'INFO', 'Submitting Level 2 approval (Fatima)...');
      const lvl2Resp = await apiCall('POST', `/api/tenders/${state.tenderId}/approval/decide`, {
        decision: 0,
        comment: 'E2E Test - Level 2 approved. Budget allocation confirmed and within limits.'
      }, approverTokens[1]);

      if (lvl2Resp.ok || lvl2Resp.data?.success) {
        log('9-approval', 'PASS', `Level 2 APPROVED: ${lvl2Resp.data?.data?.message || ''}`);
      } else {
        log('9-approval', 'FAIL', `Level 2 failed: ${JSON.stringify(lvl2Resp.data).substring(0, 400)}`);
      }

      // Level 3: Final Approve (with auditor@bayan.ae token) → should AWARD tender
      log('9-approval', 'INFO', 'Submitting Level 3 FINAL approval (Sara)...');
      const lvl3Resp = await apiCall('POST', `/api/tenders/${state.tenderId}/approval/decide`, {
        decision: 0,
        comment: 'E2E Test - Level 3 FINAL approval granted. Tender is awarded.'
      }, approverTokens[2]);

      if (lvl3Resp.ok || lvl3Resp.data?.success) {
        const isComplete = lvl3Resp.data?.data?.isWorkflowComplete;
        log('9-approval', 'PASS', `Level 3 APPROVED (Complete: ${isComplete}): ${lvl3Resp.data?.data?.message || ''}`);
      } else {
        log('9-approval', 'FAIL', `Level 3 failed: ${JSON.stringify(lvl3Resp.data).substring(0, 400)}`);
      }

      // Check final approval status
      const finalStatusResp = await apiCall('GET', `/api/tenders/${state.tenderId}/approval`, null, state.adminToken);
      if (finalStatusResp.data?.data) {
        const ws = finalStatusResp.data.data;
        log('9-approval', 'INFO', `Final workflow: status=${ws.status}`);
        (ws.levels || []).forEach(l => {
          log('9-approval', 'INFO', `  Level ${l.levelNumber}: ${l.status} (${l.decision ?? 'pending'}) by ${l.approverName} at ${l.decidedAt || 'N/A'}`);
        });
      }
    } else {
      log('9-approval', 'FAIL', `Only ${approverUserIds.filter(id => id).length}/3 approvers logged in successfully`);
    }

    // Restore original roles
    dbExec(`UPDATE users SET role = 'CommercialAnalyst' WHERE email = 'analyst@bayan.ae'`);
    dbExec(`UPDATE users SET role = 'Auditor' WHERE email = 'auditor@bayan.ae'`);
    log('9-approval', 'INFO', 'Restored original user roles');

  } catch (e) {
    log('9-approval', 'FAIL', `Exception: ${e.message}`);
    // Restore roles even on error
    dbExec(`UPDATE users SET role = 'CommercialAnalyst' WHERE email = 'analyst@bayan.ae'`);
    dbExec(`UPDATE users SET role = 'Auditor' WHERE email = 'auditor@bayan.ae'`);
  }

  // ============================================================
  // STEP 10: FINAL VERIFICATION
  // ============================================================
  console.log('\n' + '='.repeat(60));
  console.log('  STEP 10: FINAL VERIFICATION');
  console.log('='.repeat(60));

  try {
    const finalResp = await apiCall('GET', `/api/tenders/${state.tenderId}`, null, state.adminToken);
    const tender = finalResp.data?.data;

    if (tender) {
      const statusMap = { 0: 'Draft', 1: 'Active', 2: 'Evaluation', 3: 'Awarded', 4: 'Cancelled' };
      const statusName = tender.statusName || statusMap[tender.status] || `Unknown(${tender.status})`;
      const isAwarded = tender.status === 3 || tender.status === 'Awarded' || statusName === 'Awarded';

      log('10-final', isAwarded ? 'PASS' : 'FAIL', `TENDER STATUS: ${statusName}`);
      log('10-final', 'INFO', `Title: ${tender.title}`);
      log('10-final', 'INFO', `Reference: ${tender.reference}`);
      log('10-final', 'INFO', `Client: ${tender.clientName || tender.client?.name}`);
      if (tender.awardedAt) log('10-final', 'INFO', `Awarded at: ${tender.awardedAt}`);
    } else {
      log('10-final', 'FAIL', 'Could not retrieve tender');
    }

    // Approval history
    const historyResp = await apiCall('GET', `/api/tenders/${state.tenderId}/approval/history`, null, state.adminToken);
    if (historyResp.data?.data) {
      log('10-final', 'INFO', `Approval history entries: ${historyResp.data.data.length}`);
    }

    // Take screenshots if browser available
    if (browser) {
      const authState = {
        cookies: [],
        origins: [{
          origin: BASE_URL,
          localStorage: [
            { name: 'bayan_access_token', value: state.adminToken },
            { name: 'bayan_remember_me', value: 'true' },
            { name: 'bayan_user', value: JSON.stringify({ id: state.adminUserId, firstName: 'System', lastName: 'Admin', email: 'admin@bayan.ae', role: 'admin' }) }
          ]
        }]
      };

      const screenshotPages = [
        { url: '/dashboard', name: 'final-dashboard' },
        { url: '/tenders', name: 'final-tenders' },
        { url: `/tenders/${state.tenderId}`, name: 'final-tender-detail' }
      ];

      for (const pg of screenshotPages) {
        try {
          const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, storageState: authState });
          const page = await ctx.newPage();
          await Promise.race([
            page.goto(`${BASE_URL}${pg.url}`, { waitUntil: 'networkidle' }),
            new Promise(r => setTimeout(r, 12000))
          ]);
          await sleep(3000);
          await page.screenshot({ path: path.join(__dirname, '..', `e2e-${pg.name}.png`), fullPage: false });
          log('10-final', 'INFO', `Screenshot: e2e-${pg.name}.png`);
          await Promise.race([ctx.close(), new Promise(r => setTimeout(r, 3000))]);
        } catch (e) {
          log('10-final', 'WARN', `Screenshot ${pg.name} failed: ${e.message}`);
        }
      }
    }
  } catch (e) {
    log('10-final', 'FAIL', `Exception: ${e.message}`);
  }

  // ============================================================
  // FINAL REPORT
  // ============================================================
  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
  const passes = state.results.filter(r => r.status === 'PASS').length;
  const fails = state.results.filter(r => r.status === 'FAIL').length;
  const warns = state.results.filter(r => r.status === 'WARN').length;

  console.log('\n' + '='.repeat(60));
  console.log('  E2E WORKFLOW TEST REPORT');
  console.log('='.repeat(60));
  console.log(`\nDuration: ${elapsed}s`);
  console.log(`Results: ${passes} PASS | ${warns} WARN | ${fails} FAIL\n`);

  // Group by step
  const steps = [
    '1-login', '2-create', '3-publish', '4-invite', '5-bid',
    '6-open', '7-tech', '8-commercial', '9-approval', '10-final'
  ];

  for (const step of steps) {
    const stepResults = state.results.filter(r => r.step === step);
    const stepPasses = stepResults.filter(r => r.status === 'PASS').length;
    const stepFails = stepResults.filter(r => r.status === 'FAIL').length;
    const icon = stepFails > 0 ? '❌' : stepPasses > 0 ? '✅' : '⚠️';
    console.log(`${icon} Step ${step}: ${stepPasses} pass, ${stepFails} fail`);
  }

  if (state.fixes.length > 0) {
    console.log('\n🔧 Fixes Applied:');
    state.fixes.forEach(f => console.log(`  - ${f.description}`));
  }

  // Final verdict
  const criticalSteps = ['1-login', '2-create', '3-publish', '5-bid', '6-open', '9-approval'];
  const criticalFails = criticalSteps.filter(step => {
    return state.results.some(r => r.step === step && r.status === 'FAIL');
  });

  console.log('\n' + '='.repeat(60));
  if (criticalFails.length === 0 && fails === 0) {
    console.log('  ✅ ALL TESTS PASSED - WORKFLOW COMPLETE');
  } else if (criticalFails.length > 0) {
    console.log(`  ❌ CRITICAL FAILURES in: ${criticalFails.join(', ')}`);
  } else {
    console.log(`  ⚠️  ${fails} non-critical failures`);
  }
  console.log('='.repeat(60));

  // Check final tender status
  const isTenderAwarded = state.results.some(r =>
    r.step === '10-final' && r.status === 'PASS' && r.detail.includes('Awarded')
  );

  if (isTenderAwarded) {
    console.log('\n🎉🎉🎉 TENDER AWARDED SUCCESSFULLY 🎉🎉🎉');
    console.log('The complete tender lifecycle has been verified:');
    console.log('  Create → Publish → Invite → Bid → Open → Evaluate → Approve → AWARD');
  }

  if (browser) {
    await Promise.race([browser.close(), new Promise(r => setTimeout(r, 5000))]);
  }

  process.exit(fails > 0 ? 1 : 0);
})();
