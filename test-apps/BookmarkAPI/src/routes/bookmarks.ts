import { Router, Request, Response, NextFunction } from 'express';
import { prisma } from '../lib/prisma.js';
import { validate } from '../middleware/validate.js';
import { createBookmarkSchema, updateBookmarkSchema } from '../schemas/bookmarkSchemas.js';
import { updateBookmarkTagsSchema } from '../schemas/tagSchemas.js';

const router = Router();

// Helper to transform bookmark tags from join table format to simple { id, name }
function transformBookmarkTags(bookmark: any) {
  return {
    ...bookmark,
    tags: bookmark.tags?.map((bt: any) => ({
      id: bt.tag.id,
      name: bt.tag.name,
    })) || [],
  };
}

// GET / - List all bookmarks with tags and collection
router.get('/', async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const bookmarks = await prisma.bookmark.findMany({
      include: {
        collection: true,
        tags: {
          include: {
            tag: true,
          },
        },
      },
    });

    const transformedBookmarks = bookmarks.map(transformBookmarkTags);

    res.json({
      success: true,
      data: transformedBookmarks,
    });
  } catch (error) {
    next(error);
  }
});

// POST / - Create bookmark
router.post('/', validate(createBookmarkSchema), async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const { url, title, collectionId, description, favicon } = req.body;

    // Check if collection exists
    const collection = await prisma.collection.findUnique({
      where: { id: collectionId },
    });

    if (!collection) {
      res.status(404).json({
        success: false,
        error: 'Collection not found',
      });
      return;
    }

    const bookmark = await prisma.bookmark.create({
      data: { url, title, collectionId, description, favicon },
      include: {
        collection: true,
        tags: {
          include: {
            tag: true,
          },
        },
      },
    });

    res.status(201).json({
      success: true,
      data: transformBookmarkTags(bookmark),
    });
  } catch (error) {
    next(error);
  }
});

// GET /:id - Get single bookmark
router.get('/:id', async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const id = Number(req.params.id);

    const bookmark = await prisma.bookmark.findUnique({
      where: { id },
      include: {
        collection: true,
        tags: {
          include: {
            tag: true,
          },
        },
      },
    });

    if (!bookmark) {
      res.status(404).json({
        success: false,
        error: 'Bookmark not found',
      });
      return;
    }

    res.json({
      success: true,
      data: transformBookmarkTags(bookmark),
    });
  } catch (error) {
    next(error);
  }
});

// PUT /:id - Update bookmark (partial)
router.put('/:id', validate(updateBookmarkSchema), async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const id = Number(req.params.id);

    const existing = await prisma.bookmark.findUnique({
      where: { id },
    });

    if (!existing) {
      res.status(404).json({
        success: false,
        error: 'Bookmark not found',
      });
      return;
    }

    const bookmark = await prisma.bookmark.update({
      where: { id },
      data: req.body,
      include: {
        collection: true,
        tags: {
          include: {
            tag: true,
          },
        },
      },
    });

    res.json({
      success: true,
      data: transformBookmarkTags(bookmark),
    });
  } catch (error) {
    next(error);
  }
});

// DELETE /:id - Delete bookmark
router.delete('/:id', async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const id = Number(req.params.id);

    const existing = await prisma.bookmark.findUnique({
      where: { id },
    });

    if (!existing) {
      res.status(404).json({
        success: false,
        error: 'Bookmark not found',
      });
      return;
    }

    await prisma.bookmark.delete({
      where: { id },
    });

    res.json({
      success: true,
      data: { message: 'Bookmark deleted' },
    });
  } catch (error) {
    next(error);
  }
});

// PUT /:id/tags - Replace tag associations for a bookmark
router.put('/:id/tags', validate(updateBookmarkTagsSchema), async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const id = Number(req.params.id);
    const { tagIds } = req.body;

    const existing = await prisma.bookmark.findUnique({
      where: { id },
    });

    if (!existing) {
      res.status(404).json({
        success: false,
        error: 'Bookmark not found',
      });
      return;
    }

    // Delete all existing tag associations
    await prisma.bookmarkTag.deleteMany({
      where: { bookmarkId: id },
    });

    // Create new tag associations
    if (tagIds && tagIds.length > 0) {
      await prisma.bookmarkTag.createMany({
        data: tagIds.map((tagId: number) => ({
          bookmarkId: id,
          tagId,
        })),
      });
    }

    // Fetch and return updated bookmark with tags
    const bookmark = await prisma.bookmark.findUnique({
      where: { id },
      include: {
        collection: true,
        tags: {
          include: {
            tag: true,
          },
        },
      },
    });

    res.json({
      success: true,
      data: transformBookmarkTags(bookmark),
    });
  } catch (error) {
    next(error);
  }
});

export default router;
