import { defineConfig, devices } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:4200';
const API_URL = process.env.API_URL || 'http://localhost:5000/api';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { open: 'never' }],
    ['list'],
  ],
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
    extraHTTPHeaders: {
      'Accept': 'application/json',
    },
  },
  globalSetup: './global-setup.ts',

  projects: [
    // --- Auth setup dependencies (no tests, just auth) ---
    {
      name: 'setup:admin',
      testMatch: /global-setup\.ts/,
      teardown: undefined,
    },

    // --- Role-based test projects ---
    {
      name: 'unauthenticated',
      use: {
        ...devices['Desktop Chrome'],
      },
      testMatch: /auth\.spec\.ts/,
    },
    {
      name: 'admin',
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.auth/admin.json',
      },
      testMatch: /admin\.spec\.ts|rbac\.spec\.ts/,
    },
    {
      name: 'tender_manager',
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.auth/tender-manager.json',
      },
      testMatch: /dashboard\.spec\.ts|tender-list\.spec\.ts|tender-wizard\.spec\.ts|tender-details\.spec\.ts|boq\.spec\.ts|clarifications\.spec\.ts|evaluation\.spec\.ts|approval\.spec\.ts/,
    },
    {
      name: 'analyst',
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.auth/analyst.json',
      },
      testMatch: /evaluation\.spec\.ts/,
    },
    {
      name: 'approver',
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.auth/approver.json',
      },
      testMatch: /approval\.spec\.ts|rbac\.spec\.ts/,
    },
    {
      name: 'auditor',
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.auth/auditor.json',
      },
      testMatch: /admin\.spec\.ts|rbac\.spec\.ts/,
    },
    {
      name: 'bidder',
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.auth/bidder.json',
      },
      testMatch: /portal-bidder\.spec\.ts|rbac\.spec\.ts/,
    },
    {
      name: 'full_lifecycle',
      use: {
        ...devices['Desktop Chrome'],
      },
      testMatch: /full-lifecycle\.spec\.ts/,
    },

    // --- Functional Verification Projects ---
    {
      name: 'api_verification',
      use: {
        ...devices['Desktop Chrome'],
      },
      testMatch: /api-functional-verification\.spec\.ts/,
    },
    {
      name: 'ui_smoke_unauthenticated',
      use: {
        ...devices['Desktop Chrome'],
      },
      testMatch: /ui-smoke-verification\.spec\.ts/,
    },
    {
      name: 'ui_smoke_authenticated',
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.auth/tender-manager.json',
      },
      testMatch: /ui-smoke-verification\.spec\.ts/,
    },
  ],
});

export { BASE_URL, API_URL };
