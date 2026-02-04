// =============================================================================
// Password Utility Functions
// =============================================================================

import bcrypt from "bcrypt";

const SALT_ROUNDS = 10;

/** Hash a plaintext password with bcrypt (10 rounds) */
export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, SALT_ROUNDS);
}

/** Compare a plaintext password against a bcrypt hash */
export async function comparePassword(
  password: string,
  hash: string,
): Promise<boolean> {
  return bcrypt.compare(password, hash);
}
