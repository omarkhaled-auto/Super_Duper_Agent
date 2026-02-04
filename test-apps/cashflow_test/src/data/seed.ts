import { DEFAULT_CATEGORIES } from '@/data/categories';
import { useCategoryStore } from '@/stores/use-category-store';
import { useAccountStore } from '@/stores/use-account-store';
import { useTransactionStore } from '@/stores/use-transaction-store';
import { useBudgetStore } from '@/stores/use-budget-store';
import { useGoalStore } from '@/stores/use-goal-store';
import { useRecurringStore } from '@/stores/use-recurring-store';
import type {
  Account,
  Transaction,
  Budget,
  Goal,
  RecurringTransaction,
} from '@/types';

// =============================================================================
// Seed Data Generator (TASK-017)
// Populates every store with realistic demo data.
// Called OUTSIDE of React -- accesses stores via .getState().
// All monetary amounts are INTEGER CENTS.
// =============================================================================

const SEED_TS = '2025-01-01T00:00:00.000Z';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Simple seeded PRNG (mulberry32) for deterministic "random" data. */
function createRng(seed: number) {
  let s = seed;
  return (): number => {
    s |= 0;
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const rng = createRng(42);

/** Return a random integer between min and max (inclusive), in cents. */
function randCents(minDollars: number, maxDollars: number): number {
  const minC = Math.round(minDollars * 100);
  const maxC = Math.round(maxDollars * 100);
  return Math.round(minC + rng() * (maxC - minC));
}

/** Pick a random element from an array. */
function pick<T>(arr: T[]): T {
  return arr[Math.floor(rng() * arr.length)]!;
}

/** Generate an ISO date string for a date N days ago from a reference date. */
function daysAgo(days: number, ref: Date): string {
  const d = new Date(ref);
  d.setDate(d.getDate() - days);
  return d.toISOString().split('T')[0] + 'T12:00:00.000Z';
}

/** Generate an ISO date string for a specific year/month/day. */
function isoDate(y: number, m: number, d: number): string {
  return new Date(y, m - 1, d, 12).toISOString();
}

// ---------------------------------------------------------------------------
// Account definitions
// ---------------------------------------------------------------------------

const ACCOUNTS: Account[] = [
  {
    id: 'acc-checking',
    name: 'Main Checking',
    type: 'checking',
    institution: 'Chase',
    balance: 452367,
    color: '#3B82F6',
    icon: 'Landmark',
    isActive: true,
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  },
  {
    id: 'acc-savings',
    name: 'High-Yield Savings',
    type: 'savings',
    institution: 'Marcus',
    balance: 1284000,
    color: '#10B981',
    icon: 'PiggyBank',
    isActive: true,
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  },
  {
    id: 'acc-credit',
    name: 'Everyday Card',
    type: 'credit',
    institution: 'AmEx',
    balance: -124530,
    color: '#F97316',
    icon: 'CreditCard',
    isActive: true,
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  },
  {
    id: 'acc-investment',
    name: 'Investment Portfolio',
    type: 'investment',
    institution: 'Vanguard',
    balance: 2875000,
    color: '#8B5CF6',
    icon: 'TrendingUp',
    isActive: true,
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  },
  {
    id: 'acc-cash',
    name: 'Cash',
    type: 'checking',
    institution: 'Cash',
    balance: 12000,
    color: '#64748B',
    icon: 'Banknote',
    isActive: true,
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  },
];

// ---------------------------------------------------------------------------
// Transaction generation
// ---------------------------------------------------------------------------

function generateTransactions(): Transaction[] {
  const txns: Transaction[] = [];
  let txId = 0;

  const now = new Date(2025, 6, 15); // reference point: mid-July 2025
  const sixMonthsInDays = 183;

  const ts = (id: number): string => `txn-${String(id).padStart(4, '0')}`;
  const txDate = (d: string) => d;

  // --- Recurring: Salary $4,800 biweekly on 1st and 15th ----
  for (let m = 0; m < 6; m++) {
    const month = 7 - m; // July down to February
    const year = month <= 0 ? 2024 : 2025;
    const mo = month <= 0 ? month + 12 : month;

    // 1st of month
    txns.push({
      id: ts(txId++),
      type: 'income',
      amount: 480000,
      date: isoDate(year, mo, 1),
      description: 'Payroll Direct Deposit',
      categoryId: 'cat-salary',
      accountId: 'acc-checking',
      notes: 'Biweekly salary',
      tags: ['salary', 'recurring'],
      isRecurring: true,
      recurringId: 'rec-salary',
      transferToAccountId: null,
      createdAt: SEED_TS,
      updatedAt: SEED_TS,
    });

    // 15th of month
    txns.push({
      id: ts(txId++),
      type: 'income',
      amount: 480000,
      date: isoDate(year, mo, 15),
      description: 'Payroll Direct Deposit',
      categoryId: 'cat-salary',
      accountId: 'acc-checking',
      notes: 'Biweekly salary',
      tags: ['salary', 'recurring'],
      isRecurring: true,
      recurringId: 'rec-salary',
      transferToAccountId: null,
      createdAt: SEED_TS,
      updatedAt: SEED_TS,
    });
  }

  // --- Recurring: Rent $1,850 monthly on 1st ---
  for (let m = 0; m < 6; m++) {
    const month = 7 - m;
    const year = month <= 0 ? 2024 : 2025;
    const mo = month <= 0 ? month + 12 : month;

    txns.push({
      id: ts(txId++),
      type: 'expense',
      amount: 185000,
      date: isoDate(year, mo, 1),
      description: 'Monthly Rent Payment',
      categoryId: 'cat-housing',
      accountId: 'acc-checking',
      notes: 'Apartment rent',
      tags: ['rent', 'housing', 'recurring'],
      isRecurring: true,
      recurringId: 'rec-rent',
      transferToAccountId: null,
      createdAt: SEED_TS,
      updatedAt: SEED_TS,
    });
  }

  // --- Recurring: Internet $79.99 monthly on 5th ---
  for (let m = 0; m < 6; m++) {
    const month = 7 - m;
    const year = month <= 0 ? 2024 : 2025;
    const mo = month <= 0 ? month + 12 : month;

    txns.push({
      id: ts(txId++),
      type: 'expense',
      amount: 7999,
      date: isoDate(year, mo, 5),
      description: 'Xfinity Internet',
      categoryId: 'cat-utilities',
      accountId: 'acc-credit',
      notes: 'Monthly internet bill',
      tags: ['internet', 'utilities', 'recurring'],
      isRecurring: true,
      recurringId: 'rec-internet',
      transferToAccountId: null,
      createdAt: SEED_TS,
      updatedAt: SEED_TS,
    });
  }

  // --- Recurring: Gym $49.99 monthly on 3rd ---
  for (let m = 0; m < 6; m++) {
    const month = 7 - m;
    const year = month <= 0 ? 2024 : 2025;
    const mo = month <= 0 ? month + 12 : month;

    txns.push({
      id: ts(txId++),
      type: 'expense',
      amount: 4999,
      date: isoDate(year, mo, 3),
      description: 'Equinox Gym Membership',
      categoryId: 'cat-healthcare',
      accountId: 'acc-credit',
      notes: 'Monthly gym',
      tags: ['gym', 'fitness', 'recurring'],
      isRecurring: true,
      recurringId: 'rec-gym',
      transferToAccountId: null,
      createdAt: SEED_TS,
      updatedAt: SEED_TS,
    });
  }

  // --- Recurring: Netflix $15.99 monthly on 12th ---
  for (let m = 0; m < 6; m++) {
    const month = 7 - m;
    const year = month <= 0 ? 2024 : 2025;
    const mo = month <= 0 ? month + 12 : month;

    txns.push({
      id: ts(txId++),
      type: 'expense',
      amount: 1599,
      date: isoDate(year, mo, 12),
      description: 'Netflix Premium',
      categoryId: 'cat-subscriptions',
      accountId: 'acc-credit',
      notes: 'Streaming subscription',
      tags: ['netflix', 'streaming', 'recurring'],
      isRecurring: true,
      recurringId: 'rec-netflix',
      transferToAccountId: null,
      createdAt: SEED_TS,
      updatedAt: SEED_TS,
    });
  }

  // --- Recurring: Spotify $12.99 monthly on 18th ---
  for (let m = 0; m < 6; m++) {
    const month = 7 - m;
    const year = month <= 0 ? 2024 : 2025;
    const mo = month <= 0 ? month + 12 : month;

    txns.push({
      id: ts(txId++),
      type: 'expense',
      amount: 1299,
      date: isoDate(year, mo, 18),
      description: 'Spotify Premium Family',
      categoryId: 'cat-subscriptions',
      accountId: 'acc-credit',
      notes: 'Music subscription',
      tags: ['spotify', 'music', 'recurring'],
      isRecurring: true,
      recurringId: 'rec-spotify',
      transferToAccountId: null,
      createdAt: SEED_TS,
      updatedAt: SEED_TS,
    });
  }

  // --- Variable: Groceries ---
  const groceryStores = [
    { name: 'Whole Foods Market', min: 85, max: 180 },
    { name: "Trader Joe's", min: 40, max: 90 },
    { name: 'Costco Wholesale', min: 120, max: 250 },
    { name: 'Safeway', min: 35, max: 95 },
    { name: 'Sprouts Farmers Market', min: 30, max: 75 },
  ];
  for (let d = 0; d < sixMonthsInDays; d += 3) {
    // ~every 3 days
    const store = pick(groceryStores);
    txns.push({
      id: ts(txId++),
      type: 'expense',
      amount: randCents(store.min, store.max),
      date: daysAgo(d, now),
      description: store.name,
      categoryId: 'cat-groceries',
      accountId: pick(['acc-checking', 'acc-credit']),
      notes: '',
      tags: ['groceries', 'food'],
      isRecurring: false,
      recurringId: null,
      transferToAccountId: null,
      createdAt: SEED_TS,
      updatedAt: SEED_TS,
    });
  }

  // --- Variable: Dining ---
  const restaurants = [
    { name: 'Chipotle Mexican Grill', min: 12, max: 18 },
    { name: 'Olive Garden', min: 25, max: 55 },
    { name: 'Sushi Zen', min: 35, max: 85 },
    { name: 'Thai Basil Kitchen', min: 15, max: 30 },
    { name: 'The Cheesecake Factory', min: 30, max: 65 },
    { name: 'Panera Bread', min: 10, max: 18 },
    { name: 'Five Guys Burgers', min: 12, max: 22 },
    { name: 'Starbucks', min: 5, max: 12 },
    { name: "Domino's Pizza", min: 15, max: 35 },
    { name: 'Local Brunch Spot', min: 20, max: 45 },
  ];
  for (let d = 0; d < sixMonthsInDays; d += 4) {
    const rest = pick(restaurants);
    txns.push({
      id: ts(txId++),
      type: 'expense',
      amount: randCents(rest.min, rest.max),
      date: daysAgo(d + Math.floor(rng() * 2), now),
      description: rest.name,
      categoryId: 'cat-dining',
      accountId: pick(['acc-credit', 'acc-cash']),
      notes: '',
      tags: ['dining', 'food'],
      isRecurring: false,
      recurringId: null,
      transferToAccountId: null,
      createdAt: SEED_TS,
      updatedAt: SEED_TS,
    });
  }

  // --- Variable: Gas / Transportation ---
  const gasStations = [
    { name: 'Shell Gas Station', min: 35, max: 65 },
    { name: 'Chevron', min: 38, max: 62 },
    { name: 'Costco Gas', min: 40, max: 55 },
    { name: 'BP Gas', min: 35, max: 58 },
  ];
  const transitOther = [
    { name: 'Uber Ride', min: 8, max: 35 },
    { name: 'Lyft Ride', min: 10, max: 30 },
    { name: 'Metro Card Reload', min: 50, max: 127 },
    { name: 'Parking Garage', min: 10, max: 25 },
  ];
  for (let d = 0; d < sixMonthsInDays; d += 7) {
    const gas = pick(gasStations);
    txns.push({
      id: ts(txId++),
      type: 'expense',
      amount: randCents(gas.min, gas.max),
      date: daysAgo(d, now),
      description: gas.name,
      categoryId: 'cat-transport',
      accountId: 'acc-credit',
      notes: '',
      tags: ['gas', 'transportation'],
      isRecurring: false,
      recurringId: null,
      transferToAccountId: null,
      createdAt: SEED_TS,
      updatedAt: SEED_TS,
    });
  }
  for (let d = 2; d < sixMonthsInDays; d += 12) {
    const t = pick(transitOther);
    txns.push({
      id: ts(txId++),
      type: 'expense',
      amount: randCents(t.min, t.max),
      date: daysAgo(d, now),
      description: t.name,
      categoryId: 'cat-transport',
      accountId: pick(['acc-credit', 'acc-checking']),
      notes: '',
      tags: ['transit', 'transportation'],
      isRecurring: false,
      recurringId: null,
      transferToAccountId: null,
      createdAt: SEED_TS,
      updatedAt: SEED_TS,
    });
  }

  // --- Variable: Shopping ---
  const shops = [
    { name: 'Amazon.com', min: 15, max: 200 },
    { name: 'Target', min: 20, max: 120 },
    { name: 'Best Buy', min: 30, max: 180 },
    { name: 'IKEA', min: 40, max: 200 },
    { name: 'Nike Store', min: 50, max: 160 },
    { name: 'Nordstrom', min: 35, max: 150 },
    { name: 'Home Depot', min: 20, max: 130 },
    { name: 'TJ Maxx', min: 15, max: 75 },
  ];
  for (let d = 1; d < sixMonthsInDays; d += 6) {
    const shop = pick(shops);
    txns.push({
      id: ts(txId++),
      type: 'expense',
      amount: randCents(shop.min, shop.max),
      date: daysAgo(d, now),
      description: shop.name,
      categoryId: 'cat-shopping',
      accountId: pick(['acc-credit', 'acc-checking']),
      notes: '',
      tags: ['shopping'],
      isRecurring: false,
      recurringId: null,
      transferToAccountId: null,
      createdAt: SEED_TS,
      updatedAt: SEED_TS,
    });
  }

  // --- Variable: Entertainment ---
  const entertainment = [
    { name: 'AMC Movie Theater', min: 12, max: 35 },
    { name: 'Concert Tickets - Ticketmaster', min: 50, max: 150 },
    { name: 'Dave & Busters', min: 25, max: 60 },
    { name: 'Bowling Alley', min: 15, max: 40 },
    { name: 'Steam Game Purchase', min: 10, max: 60 },
    { name: 'Apple App Store', min: 3, max: 15 },
    { name: 'Escape Room Adventure', min: 30, max: 50 },
  ];
  for (let d = 3; d < sixMonthsInDays; d += 10) {
    const ent = pick(entertainment);
    txns.push({
      id: ts(txId++),
      type: 'expense',
      amount: randCents(ent.min, ent.max),
      date: daysAgo(d, now),
      description: ent.name,
      categoryId: 'cat-entertainment',
      accountId: pick(['acc-credit', 'acc-checking', 'acc-cash']),
      notes: '',
      tags: ['entertainment', 'fun'],
      isRecurring: false,
      recurringId: null,
      transferToAccountId: null,
      createdAt: SEED_TS,
      updatedAt: SEED_TS,
    });
  }

  // --- Variable: Utilities ---
  const utilities = [
    { name: 'Electric Bill - ConEd', min: 60, max: 160 },
    { name: 'Water & Sewer', min: 30, max: 55 },
    { name: 'Gas Bill - National Grid', min: 40, max: 90 },
    { name: 'Cell Phone - T-Mobile', min: 75, max: 85 },
  ];
  for (let m = 0; m < 6; m++) {
    for (const util of utilities) {
      const month = 7 - m;
      const year = month <= 0 ? 2024 : 2025;
      const mo = month <= 0 ? month + 12 : month;

      txns.push({
        id: ts(txId++),
        type: 'expense',
        amount: randCents(util.min, util.max),
        date: isoDate(year, mo, 8 + Math.floor(rng() * 10)),
        description: util.name,
        categoryId: 'cat-utilities',
        accountId: 'acc-checking',
        notes: '',
        tags: ['utilities', 'bills'],
        isRecurring: false,
        recurringId: null,
        transferToAccountId: null,
        createdAt: SEED_TS,
        updatedAt: SEED_TS,
      });
    }
  }

  // --- Variable: Healthcare ---
  const healthcare = [
    { name: 'CVS Pharmacy', min: 10, max: 50 },
    { name: 'Dr. Smith Co-Pay', min: 25, max: 40 },
    { name: 'Dental Cleaning', min: 50, max: 120 },
    { name: 'Eye Exam & Contacts', min: 80, max: 200 },
    { name: 'Urgent Care Visit', min: 100, max: 250 },
  ];
  for (let d = 5; d < sixMonthsInDays; d += 20) {
    const hc = pick(healthcare);
    txns.push({
      id: ts(txId++),
      type: 'expense',
      amount: randCents(hc.min, hc.max),
      date: daysAgo(d, now),
      description: hc.name,
      categoryId: 'cat-healthcare',
      accountId: pick(['acc-credit', 'acc-checking']),
      notes: '',
      tags: ['health', 'medical'],
      isRecurring: false,
      recurringId: null,
      transferToAccountId: null,
      createdAt: SEED_TS,
      updatedAt: SEED_TS,
    });
  }

  // --- Variable: Insurance ---
  for (let m = 0; m < 6; m++) {
    const month = 7 - m;
    const year = month <= 0 ? 2024 : 2025;
    const mo = month <= 0 ? month + 12 : month;

    txns.push({
      id: ts(txId++),
      type: 'expense',
      amount: 18500,
      date: isoDate(year, mo, 1),
      description: 'Geico Auto Insurance',
      categoryId: 'cat-insurance',
      accountId: 'acc-checking',
      notes: 'Monthly auto insurance premium',
      tags: ['insurance', 'auto'],
      isRecurring: true,
      recurringId: 'rec-insurance',
      transferToAccountId: null,
      createdAt: SEED_TS,
      updatedAt: SEED_TS,
    });
  }

  // --- Variable: Education ---
  const education = [
    { name: 'Udemy Course - React Mastery', min: 12, max: 80 },
    { name: 'O\'Reilly Book Purchase', min: 25, max: 50 },
    { name: 'Coursera Subscription', min: 49, max: 49 },
    { name: 'Language Learning App', min: 13, max: 13 },
  ];
  for (let d = 10; d < sixMonthsInDays; d += 30) {
    const edu = pick(education);
    txns.push({
      id: ts(txId++),
      type: 'expense',
      amount: randCents(edu.min, edu.max),
      date: daysAgo(d, now),
      description: edu.name,
      categoryId: 'cat-education',
      accountId: pick(['acc-credit', 'acc-checking']),
      notes: '',
      tags: ['education', 'learning'],
      isRecurring: false,
      recurringId: null,
      transferToAccountId: null,
      createdAt: SEED_TS,
      updatedAt: SEED_TS,
    });
  }

  // --- Variable: Personal Care ---
  const personalCare = [
    { name: 'Haircut - Great Clips', min: 20, max: 45 },
    { name: 'Sephora', min: 25, max: 80 },
    { name: 'Dry Cleaning Pickup', min: 15, max: 35 },
    { name: 'Spa Treatment', min: 60, max: 120 },
  ];
  for (let d = 8; d < sixMonthsInDays; d += 18) {
    const pc = pick(personalCare);
    txns.push({
      id: ts(txId++),
      type: 'expense',
      amount: randCents(pc.min, pc.max),
      date: daysAgo(d, now),
      description: pc.name,
      categoryId: 'cat-personal',
      accountId: pick(['acc-credit', 'acc-cash']),
      notes: '',
      tags: ['personal'],
      isRecurring: false,
      recurringId: null,
      transferToAccountId: null,
      createdAt: SEED_TS,
      updatedAt: SEED_TS,
    });
  }

  // --- Variable: Travel ---
  const travel = [
    { name: 'Delta Airlines - SFO to JFK', min: 250, max: 450 },
    { name: 'Hilton Hotel - 2 Nights', min: 200, max: 400 },
    { name: 'Airbnb - Weekend Getaway', min: 150, max: 350 },
    { name: 'Hertz Car Rental', min: 80, max: 200 },
  ];
  for (let d = 15; d < sixMonthsInDays; d += 45) {
    const tr = pick(travel);
    txns.push({
      id: ts(txId++),
      type: 'expense',
      amount: randCents(tr.min, tr.max),
      date: daysAgo(d, now),
      description: tr.name,
      categoryId: 'cat-travel',
      accountId: 'acc-credit',
      notes: '',
      tags: ['travel'],
      isRecurring: false,
      recurringId: null,
      transferToAccountId: null,
      createdAt: SEED_TS,
      updatedAt: SEED_TS,
    });
  }

  // --- Variable: Gifts & Donations ---
  const gifts = [
    { name: 'Birthday Gift - Amazon', min: 25, max: 80 },
    { name: 'Charity Donation - Red Cross', min: 25, max: 100 },
    { name: 'Wedding Gift', min: 50, max: 150 },
    { name: 'GoFundMe Contribution', min: 20, max: 50 },
    { name: 'Holiday Gift - Etsy', min: 30, max: 100 },
  ];
  for (let d = 12; d < sixMonthsInDays; d += 25) {
    const g = pick(gifts);
    txns.push({
      id: ts(txId++),
      type: 'expense',
      amount: randCents(g.min, g.max),
      date: daysAgo(d, now),
      description: g.name,
      categoryId: 'cat-gifts',
      accountId: pick(['acc-credit', 'acc-checking']),
      notes: '',
      tags: ['gifts'],
      isRecurring: false,
      recurringId: null,
      transferToAccountId: null,
      createdAt: SEED_TS,
      updatedAt: SEED_TS,
    });
  }

  // --- Variable: Miscellaneous ---
  const misc = [
    { name: 'Post Office - Shipping', min: 5, max: 20 },
    { name: 'Locksmith Service', min: 50, max: 120 },
    { name: 'Car Wash', min: 10, max: 25 },
    { name: 'ATM Withdrawal', min: 40, max: 200 },
    { name: 'Pet Supplies - PetSmart', min: 20, max: 60 },
  ];
  for (let d = 7; d < sixMonthsInDays; d += 14) {
    const m = pick(misc);
    txns.push({
      id: ts(txId++),
      type: 'expense',
      amount: randCents(m.min, m.max),
      date: daysAgo(d, now),
      description: m.name,
      categoryId: 'cat-misc',
      accountId: pick(['acc-cash', 'acc-checking', 'acc-credit']),
      notes: '',
      tags: ['misc'],
      isRecurring: false,
      recurringId: null,
      transferToAccountId: null,
      createdAt: SEED_TS,
      updatedAt: SEED_TS,
    });
  }

  // --- Income: Freelance (sporadic) ---
  const freelance = [
    { name: 'Freelance Web Dev - Client A', min: 500, max: 2000 },
    { name: 'Logo Design Project', min: 200, max: 600 },
    { name: 'Consulting Session', min: 150, max: 400 },
    { name: 'Technical Writing Gig', min: 100, max: 350 },
  ];
  for (let d = 20; d < sixMonthsInDays; d += 30) {
    const fl = pick(freelance);
    txns.push({
      id: ts(txId++),
      type: 'income',
      amount: randCents(fl.min, fl.max),
      date: daysAgo(d, now),
      description: fl.name,
      categoryId: 'cat-freelance',
      accountId: 'acc-checking',
      notes: '',
      tags: ['freelance', 'income'],
      isRecurring: false,
      recurringId: null,
      transferToAccountId: null,
      createdAt: SEED_TS,
      updatedAt: SEED_TS,
    });
  }

  // --- Income: Investment dividends (quarterly) ---
  const dividends = [
    { name: 'Vanguard Quarterly Dividend', min: 150, max: 350 },
    { name: 'AAPL Dividend Payment', min: 50, max: 120 },
  ];
  for (let q = 0; q < 2; q++) {
    const div = pick(dividends);
    txns.push({
      id: ts(txId++),
      type: 'income',
      amount: randCents(div.min, div.max),
      date: daysAgo(90 * q + 30, now),
      description: div.name,
      categoryId: 'cat-investments',
      accountId: 'acc-investment',
      notes: 'Quarterly dividend',
      tags: ['investment', 'dividend'],
      isRecurring: false,
      recurringId: null,
      transferToAccountId: null,
      createdAt: SEED_TS,
      updatedAt: SEED_TS,
    });
  }

  // --- Income: Other ---
  txns.push({
    id: ts(txId++),
    type: 'income',
    amount: 15000,
    date: daysAgo(45, now),
    description: 'Facebook Marketplace Sale',
    categoryId: 'cat-other-income',
    accountId: 'acc-checking',
    notes: 'Sold old furniture',
    tags: ['sale', 'income'],
    isRecurring: false,
    recurringId: null,
    transferToAccountId: null,
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  });

  txns.push({
    id: ts(txId++),
    type: 'income',
    amount: 5000,
    date: daysAgo(80, now),
    description: 'Cash Back Reward - AmEx',
    categoryId: 'cat-other-income',
    accountId: 'acc-credit',
    notes: 'Statement credit',
    tags: ['cashback', 'reward'],
    isRecurring: false,
    recurringId: null,
    transferToAccountId: null,
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  });

  txns.push({
    id: ts(txId++),
    type: 'income',
    amount: 25000,
    date: daysAgo(120, now),
    description: 'Tax Refund - IRS',
    categoryId: 'cat-other-income',
    accountId: 'acc-checking',
    notes: '2024 federal tax refund',
    tags: ['tax', 'refund'],
    isRecurring: false,
    recurringId: null,
    transferToAccountId: null,
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  });

  return txns;
}

// ---------------------------------------------------------------------------
// Budget definitions
// ---------------------------------------------------------------------------

const BUDGETS: Budget[] = [
  {
    id: 'budget-groceries',
    name: 'Groceries',
    categoryId: 'cat-groceries',
    amount: 60000,
    period: 'monthly',
    alertThreshold: 80,
    isActive: true,
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  },
  {
    id: 'budget-dining',
    name: 'Dining Out',
    categoryId: 'cat-dining',
    amount: 30000,
    period: 'monthly',
    alertThreshold: 80,
    isActive: true,
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  },
  {
    id: 'budget-transport',
    name: 'Transportation',
    categoryId: 'cat-transport',
    amount: 25000,
    period: 'monthly',
    alertThreshold: 80,
    isActive: true,
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  },
  {
    id: 'budget-shopping',
    name: 'Shopping',
    categoryId: 'cat-shopping',
    amount: 40000,
    period: 'monthly',
    alertThreshold: 75,
    isActive: true,
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  },
  {
    id: 'budget-entertainment',
    name: 'Entertainment',
    categoryId: 'cat-entertainment',
    amount: 20000,
    period: 'monthly',
    alertThreshold: 80,
    isActive: true,
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  },
  {
    id: 'budget-subscriptions',
    name: 'Subscriptions',
    categoryId: 'cat-subscriptions',
    amount: 10000,
    period: 'monthly',
    alertThreshold: 90,
    isActive: true,
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  },
  {
    id: 'budget-personal',
    name: 'Personal Care',
    categoryId: 'cat-personal',
    amount: 8000,
    period: 'monthly',
    alertThreshold: 80,
    isActive: true,
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  },
  {
    id: 'budget-utilities',
    name: 'Utilities',
    categoryId: 'cat-utilities',
    amount: 35000,
    period: 'monthly',
    alertThreshold: 85,
    isActive: true,
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  },
];

// ---------------------------------------------------------------------------
// Goal definitions
// ---------------------------------------------------------------------------

const GOALS: Goal[] = [
  {
    id: 'goal-emergency',
    name: 'Emergency Fund',
    description: 'Build a 6-month emergency fund for financial security',
    targetAmount: 1500000,
    currentAmount: 850000,
    deadline: '2026-12-31T00:00:00.000Z',
    monthlyContribution: 50000,
    icon: 'Shield',
    color: '#22C55E',
    status: 'on-track',
    linkedAccountId: 'acc-savings',
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  },
  {
    id: 'goal-japan',
    name: 'Japan Vacation',
    description: 'Two-week trip to Tokyo, Kyoto, and Osaka',
    targetAmount: 500000,
    currentAmount: 120000,
    deadline: '2027-06-30T00:00:00.000Z',
    monthlyContribution: 30000,
    icon: 'Plane',
    color: '#3B82F6',
    status: 'on-track',
    linkedAccountId: 'acc-savings',
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  },
  {
    id: 'goal-car',
    name: 'New Car',
    description: 'Down payment for a new reliable vehicle',
    targetAmount: 1000000,
    currentAmount: 280000,
    deadline: '2027-03-31T00:00:00.000Z',
    monthlyContribution: 40000,
    icon: 'Car',
    color: '#8B5CF6',
    status: 'behind',
    linkedAccountId: 'acc-savings',
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  },
];

// ---------------------------------------------------------------------------
// Recurring transaction rules
// ---------------------------------------------------------------------------

const RECURRING_RULES: RecurringTransaction[] = [
  {
    id: 'rec-salary',
    type: 'income',
    amount: 480000,
    description: 'Payroll Direct Deposit',
    categoryId: 'cat-salary',
    accountId: 'acc-checking',
    frequency: 'biweekly',
    nextDate: '2025-08-01T00:00:00.000Z',
    endDate: null,
    isActive: true,
    transferToAccountId: null,
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  },
  {
    id: 'rec-rent',
    type: 'expense',
    amount: 185000,
    description: 'Monthly Rent Payment',
    categoryId: 'cat-housing',
    accountId: 'acc-checking',
    frequency: 'monthly',
    nextDate: '2025-08-01T00:00:00.000Z',
    endDate: null,
    isActive: true,
    transferToAccountId: null,
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  },
  {
    id: 'rec-internet',
    type: 'expense',
    amount: 7999,
    description: 'Xfinity Internet',
    categoryId: 'cat-utilities',
    accountId: 'acc-credit',
    frequency: 'monthly',
    nextDate: '2025-08-05T00:00:00.000Z',
    endDate: null,
    isActive: true,
    transferToAccountId: null,
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  },
  {
    id: 'rec-gym',
    type: 'expense',
    amount: 4999,
    description: 'Equinox Gym Membership',
    categoryId: 'cat-healthcare',
    accountId: 'acc-credit',
    frequency: 'monthly',
    nextDate: '2025-08-03T00:00:00.000Z',
    endDate: null,
    isActive: true,
    transferToAccountId: null,
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  },
  {
    id: 'rec-netflix',
    type: 'expense',
    amount: 1599,
    description: 'Netflix Premium',
    categoryId: 'cat-subscriptions',
    accountId: 'acc-credit',
    frequency: 'monthly',
    nextDate: '2025-08-12T00:00:00.000Z',
    endDate: null,
    isActive: true,
    transferToAccountId: null,
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  },
  {
    id: 'rec-spotify',
    type: 'expense',
    amount: 1299,
    description: 'Spotify Premium Family',
    categoryId: 'cat-subscriptions',
    accountId: 'acc-credit',
    frequency: 'monthly',
    nextDate: '2025-08-18T00:00:00.000Z',
    endDate: null,
    isActive: true,
    transferToAccountId: null,
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  },
  {
    id: 'rec-insurance',
    type: 'expense',
    amount: 18500,
    description: 'Geico Auto Insurance',
    categoryId: 'cat-insurance',
    accountId: 'acc-checking',
    frequency: 'monthly',
    nextDate: '2025-08-01T00:00:00.000Z',
    endDate: null,
    isActive: true,
    transferToAccountId: null,
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  },
  {
    id: 'rec-savings-transfer',
    type: 'transfer',
    amount: 50000,
    description: 'Monthly Savings Transfer',
    categoryId: 'cat-other-income',
    accountId: 'acc-checking',
    frequency: 'monthly',
    nextDate: '2025-08-01T00:00:00.000Z',
    endDate: null,
    isActive: true,
    transferToAccountId: 'acc-savings',
    createdAt: SEED_TS,
    updatedAt: SEED_TS,
  },
];

// =============================================================================
// Main seed function
// =============================================================================

export function generateSeedData(): void {
  // Seed order: categories -> accounts -> transactions -> budgets -> goals -> recurring
  useCategoryStore.getState().seedCategories(DEFAULT_CATEGORIES);
  useAccountStore.getState().seedAccounts(ACCOUNTS);
  useTransactionStore.getState().seedTransactions(generateTransactions());
  useBudgetStore.getState().seedBudgets(BUDGETS);
  useGoalStore.getState().seedGoals(GOALS);
  useRecurringStore.getState().seedRecurring(RECURRING_RULES);
}
