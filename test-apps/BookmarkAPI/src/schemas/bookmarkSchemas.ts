import { z } from 'zod';

export const createBookmarkSchema = z.object({
  url: z.string().url(),
  title: z.string().min(1),
  collectionId: z.number().int(),
  description: z.string().optional(),
  favicon: z.string().optional(),
});

export const updateBookmarkSchema = z.object({
  url: z.string().url().optional(),
  title: z.string().min(1).optional(),
  collectionId: z.number().int().optional(),
  description: z.string().optional(),
  favicon: z.string().optional(),
});
