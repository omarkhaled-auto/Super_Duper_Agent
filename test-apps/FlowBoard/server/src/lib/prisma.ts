// =============================================================================
// Prisma Client Singleton
//
// Prevents multiple PrismaClient instances during hot-reload in development.
// In production a single instance is created and reused.
// =============================================================================

import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

export const prisma = globalForPrisma.prisma ?? new PrismaClient();

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma;

export default prisma;
