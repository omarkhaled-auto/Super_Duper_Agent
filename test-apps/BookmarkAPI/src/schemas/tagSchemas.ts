import { z } from 'zod';

export const createTagSchema = z.object({
  name: z.string().min(1),
});

export const updateBookmarkTagsSchema = z.object({
  tagIds: z.array(z.number().int()),
});
