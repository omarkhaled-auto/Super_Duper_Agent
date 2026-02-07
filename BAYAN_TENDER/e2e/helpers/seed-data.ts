// ============================================================================
// Reads seed data written by global-setup.ts
// Tests import this to get the actual tender/client/bidder IDs
// ============================================================================

import * as fs from 'fs';
import * as path from 'path';

export interface SeedData {
  tenderId: string;
  clientId: string;
  bidderId: string;
  boqSectionIds: string[];
  boqItemIds: string[];
  seeded: boolean;
}

const SEED_FILE = path.join(__dirname, '..', '.test-data', 'seed.json');

let _cached: SeedData | null = null;

export function getSeedData(): SeedData {
  if (_cached) return _cached;

  const fallback: SeedData = {
    tenderId: '',
    clientId: '',
    bidderId: '',
    boqSectionIds: [],
    boqItemIds: [],
    seeded: false,
  };

  try {
    if (!fs.existsSync(SEED_FILE)) return fallback;
    const raw = fs.readFileSync(SEED_FILE, 'utf-8');
    _cached = JSON.parse(raw) as SeedData;
    return _cached;
  } catch {
    return fallback;
  }
}
