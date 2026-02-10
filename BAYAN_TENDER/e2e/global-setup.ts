// ============================================================================
// BAYAN Tender E2E Global Setup
// 1. Authenticates each role via API and persists storageState
// 2. Seeds test data (client, bidder, tender, BOQ) so tests have real data
// ============================================================================

import { chromium, FullConfig } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import { USERS, SAMPLE_TENDER, SAMPLE_BOQ_SECTIONS, SAMPLE_BOQ_ITEMS, SAMPLE_CLIENT, SAMPLE_BIDDER, generateTenderDates } from './fixtures/test-data';

const API_URL = process.env.API_URL || 'http://localhost:5000/api';
const BASE_URL = process.env.BASE_URL || 'http://localhost:4200';
const SEED_FILE = path.join(__dirname, '.test-data', 'seed.json');

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AuthState {
  role: string;
  email: string;
  password: string;
  storageFile: string;
}

export interface SeedData {
  tenderId: string;
  clientId: string;
  bidderId: string;
  boqSectionIds: string[];
  boqItemIds: string[];
  seeded: boolean;
}

const AUTH_STATES: AuthState[] = [
  { role: 'admin', email: USERS.admin.email, password: USERS.admin.password, storageFile: '.auth/admin.json' },
  { role: 'tender-manager', email: USERS.tenderManager.email, password: USERS.tenderManager.password, storageFile: '.auth/tender-manager.json' },
  { role: 'analyst', email: USERS.analyst.email, password: USERS.analyst.password, storageFile: '.auth/analyst.json' },
  { role: 'panelist', email: USERS.panelist.email, password: USERS.panelist.password, storageFile: '.auth/panelist.json' },
  { role: 'approver', email: USERS.approver.email, password: USERS.approver.password, storageFile: '.auth/approver.json' },
  { role: 'auditor', email: USERS.auditor.email, password: USERS.auditor.password, storageFile: '.auth/auditor.json' },
  { role: 'bidder', email: USERS.bidder.email, password: USERS.bidder.password, storageFile: '.auth/bidder.json' },
];

// ---------------------------------------------------------------------------
// Phase 1: Authenticate all roles
// ---------------------------------------------------------------------------

async function authenticateRoles(browser: import('@playwright/test').Browser): Promise<Map<string, string>> {
  const tokens = new Map<string, string>();

  for (const auth of AUTH_STATES) {
    console.log(`  Authenticating ${auth.role} (${auth.email})...`);
    try {
      const context = await browser.newContext({ baseURL: BASE_URL });
      const page = await context.newPage();

      const response = await page.request.post(`${API_URL}/auth/login`, {
        data: { email: auth.email, password: auth.password, rememberMe: true },
      });

      if (response.ok()) {
        const body = await response.json();
        const loginData = body.data;
        tokens.set(auth.role, loginData.accessToken);

        await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });

        const isBidder = auth.role === 'bidder';
        await page.evaluate(({ data, isBidder }) => {
          if (isBidder) {
            localStorage.setItem('portal_access_token', data.accessToken);
            localStorage.setItem('portal_refresh_token', data.refreshToken);
            localStorage.setItem('portal_user', JSON.stringify(data.user));
          } else {
            localStorage.setItem('bayan_remember_me', 'true');
            localStorage.setItem('bayan_access_token', data.accessToken);
            localStorage.setItem('bayan_refresh_token', data.refreshToken);
            localStorage.setItem('bayan_user', JSON.stringify(data.user));
          }
        }, { data: loginData, isBidder });

        await context.storageState({ path: auth.storageFile });
        console.log(`    [OK] ${auth.role} authenticated`);
      } else {
        console.warn(`    [FAIL] ${auth.role} login failed (${response.status()})`);
        await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
        await context.storageState({ path: auth.storageFile });
      }

      await context.close();
    } catch (error) {
      console.warn(`    [FAIL] ${auth.role} auth error: ${error}`);
    }
  }

  return tokens;
}

// ---------------------------------------------------------------------------
// Phase 2: Seed test data
// ---------------------------------------------------------------------------

async function seedTestData(browser: import('@playwright/test').Browser, tokens: Map<string, string>): Promise<SeedData> {
  const seed: SeedData = {
    tenderId: '',
    clientId: '',
    bidderId: '',
    boqSectionIds: [],
    boqItemIds: [],
    seeded: false,
  };

  const tmToken = tokens.get('tender-manager');
  if (!tmToken) {
    console.warn('  [SKIP] No tender-manager token — cannot seed data');
    return seed;
  }

  const context = await browser.newContext();
  const request = context.request;

  try {
    // --- Step 1: Create client ---
    console.log('  Creating client...');
    const clientRes = await request.post(`${API_URL}/clients`, {
      headers: { Authorization: `Bearer ${tmToken}` },
      data: {
        name: SAMPLE_CLIENT.name,
        contactPerson: SAMPLE_CLIENT.contactPerson,
        email: SAMPLE_CLIENT.email,
        phone: SAMPLE_CLIENT.phone,
      },
    });

    if (clientRes.ok()) {
      const clientBody = await clientRes.json();
      seed.clientId = clientBody.data?.id ?? '';
      console.log(`    [OK] Client created: ${seed.clientId}`);
    } else {
      // Client may already exist — try to list and find it
      console.log(`    [WARN] Create client returned ${clientRes.status()}, trying to find existing...`);
      const listRes = await request.get(`${API_URL}/clients?search=${encodeURIComponent(SAMPLE_CLIENT.name)}&page=1&pageSize=5`, {
        headers: { Authorization: `Bearer ${tmToken}` },
      });
      if (listRes.ok()) {
        const listBody = await listRes.json();
        const items = listBody.data?.items ?? listBody.data ?? [];
        if (Array.isArray(items) && items.length > 0) {
          seed.clientId = items[0].id;
          console.log(`    [OK] Found existing client: ${seed.clientId}`);
        }
      }
    }

    if (!seed.clientId) {
      console.warn('  [FAIL] Could not create or find client — skipping tender creation');
      return seed;
    }

    // --- Step 2: Create bidder ---
    console.log('  Creating bidder...');
    const bidderRes = await request.post(`${API_URL}/bidders`, {
      headers: { Authorization: `Bearer ${tmToken}` },
      data: {
        companyName: SAMPLE_BIDDER.companyNameEn,
        contactPerson: 'E2E Test Contact',
        email: SAMPLE_BIDDER.email,
        crNumber: SAMPLE_BIDDER.crNumber,
        phone: SAMPLE_BIDDER.phone,
      },
    });

    if (bidderRes.ok()) {
      const bidderBody = await bidderRes.json();
      seed.bidderId = bidderBody.data?.id ?? '';
      console.log(`    [OK] Bidder created: ${seed.bidderId}`);
    } else {
      console.log(`    [WARN] Create bidder returned ${bidderRes.status()}, trying to find existing...`);
      const listRes = await request.get(`${API_URL}/bidders?search=${encodeURIComponent(SAMPLE_BIDDER.companyNameEn)}&page=1&pageSize=5`, {
        headers: { Authorization: `Bearer ${tmToken}` },
      });
      if (listRes.ok()) {
        const listBody = await listRes.json();
        const items = listBody.data?.items ?? listBody.data ?? [];
        if (Array.isArray(items) && items.length > 0) {
          seed.bidderId = items[0].id;
          console.log(`    [OK] Found existing bidder: ${seed.bidderId}`);
        }
      }
    }

    // --- Step 3: Create tender ---
    console.log('  Creating tender...');
    const dates = generateTenderDates();
    const tenderRes = await request.post(`${API_URL}/tenders`, {
      headers: { Authorization: `Bearer ${tmToken}` },
      data: {
        title: SAMPLE_TENDER.title,
        description: SAMPLE_TENDER.description,
        clientId: seed.clientId,
        tenderType: 0, // Open (numeric enum)
        baseCurrency: SAMPLE_TENDER.baseCurrency,
        bidValidityDays: SAMPLE_TENDER.bidValidityDays,
        issueDate: dates.issueDate,
        clarificationDeadline: dates.clarificationDeadline,
        submissionDeadline: dates.submissionDeadline,
        openingDate: dates.openingDate,
        technicalWeight: SAMPLE_TENDER.technicalWeight,
        commercialWeight: SAMPLE_TENDER.commercialWeight,
        evaluationCriteria: SAMPLE_TENDER.evaluationCriteria.map((c, i) => ({
          name: c.name,
          weightPercentage: c.weight,
          guidanceNotes: c.description,
          sortOrder: i + 1,
        })),
      },
    });

    if (!tenderRes.ok()) {
      const text = await tenderRes.text().catch(() => '');
      console.warn(`  [FAIL] Create tender returned ${tenderRes.status()}: ${text}`);
      return seed;
    }

    const tenderBody = await tenderRes.json();
    seed.tenderId = tenderBody.data?.id ?? '';
    console.log(`    [OK] Tender created: ${seed.tenderId}`);

    if (!seed.tenderId) return seed;

    // --- Step 4: Create BOQ sections ---
    console.log('  Creating BOQ sections...');
    for (let i = 0; i < SAMPLE_BOQ_SECTIONS.length; i++) {
      const section = SAMPLE_BOQ_SECTIONS[i];
      const secRes = await request.post(`${API_URL}/tenders/${seed.tenderId}/boq/sections`, {
        headers: { Authorization: `Bearer ${tmToken}` },
        data: {
          sectionNumber: section.number,
          title: section.title,
          sortOrder: i + 1,
        },
      });

      if (secRes.ok()) {
        const secBody = await secRes.json();
        const sectionId = secBody.data?.id ?? '';
        seed.boqSectionIds.push(sectionId);
        console.log(`    [OK] Section "${section.title}" created: ${sectionId}`);
      } else {
        console.warn(`    [WARN] Section "${section.title}" failed: ${secRes.status()}`);
      }
    }

    // --- Step 5: Create BOQ items ---
    if (seed.boqSectionIds.length > 0) {
      console.log('  Creating BOQ items...');
      for (let i = 0; i < SAMPLE_BOQ_ITEMS.length; i++) {
        const item = SAMPLE_BOQ_ITEMS[i];
        // Map section number to section ID
        const sectionIndex = SAMPLE_BOQ_SECTIONS.findIndex(s => s.number === item.sectionNumber);
        const sectionId = sectionIndex >= 0 ? seed.boqSectionIds[sectionIndex] : seed.boqSectionIds[0];

        if (!sectionId) continue;

        const itemRes = await request.post(`${API_URL}/tenders/${seed.tenderId}/boq/items`, {
          headers: { Authorization: `Bearer ${tmToken}` },
          data: {
            sectionId,
            itemNumber: item.number,
            description: item.description,
            quantity: item.quantity,
            uom: item.uom,
            itemType: 0, // Base
            sortOrder: i + 1,
          },
        });

        if (itemRes.ok()) {
          const itemBody = await itemRes.json();
          seed.boqItemIds.push(itemBody.data?.id ?? '');
          console.log(`    [OK] Item "${item.description}" created`);
        } else {
          console.warn(`    [WARN] Item "${item.description}" failed: ${itemRes.status()}`);
        }
      }
    }

    // --- Step 6: Invite bidder (if we have one) ---
    if (seed.bidderId) {
      console.log('  Inviting bidder...');
      const inviteRes = await request.post(`${API_URL}/tenders/${seed.tenderId}/invite`, {
        headers: { Authorization: `Bearer ${tmToken}` },
        data: [seed.bidderId],
      });
      if (inviteRes.ok()) {
        console.log('    [OK] Bidder invited');
      } else {
        console.warn(`    [WARN] Invite returned ${inviteRes.status()}`);
      }
    }

    seed.seeded = true;
  } catch (error) {
    console.error(`  [ERROR] Seed failed: ${error}`);
  } finally {
    await context.close();
  }

  return seed;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function globalSetup(config: FullConfig) {
  console.log('=== BAYAN E2E Global Setup ===');

  // Ensure directories exist
  fs.mkdirSync(path.join(__dirname, '.auth'), { recursive: true });
  fs.mkdirSync(path.join(__dirname, '.test-data'), { recursive: true });

  const browser = await chromium.launch();

  // Phase 1: Authenticate
  console.log('\nPhase 1: Authenticating roles...');
  const tokens = await authenticateRoles(browser);

  // Phase 2: Seed data
  console.log('\nPhase 2: Seeding test data...');
  const seed = await seedTestData(browser, tokens);

  // Write seed data for tests to consume
  fs.writeFileSync(SEED_FILE, JSON.stringify(seed, null, 2));
  console.log(`\nSeed data written to ${SEED_FILE}`);
  console.log(`  tenderId:  ${seed.tenderId || '(none)'}`);
  console.log(`  clientId:  ${seed.clientId || '(none)'}`);
  console.log(`  bidderId:  ${seed.bidderId || '(none)'}`);
  console.log(`  sections:  ${seed.boqSectionIds.length}`);
  console.log(`  items:     ${seed.boqItemIds.length}`);
  console.log(`  seeded:    ${seed.seeded}`);

  await browser.close();
  console.log('\n=== Setup complete ===\n');
}

export default globalSetup;
