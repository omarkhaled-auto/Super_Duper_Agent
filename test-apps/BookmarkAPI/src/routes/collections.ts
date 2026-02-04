import { Router, Request, Response, NextFunction } from 'express';
import { prisma } from '../lib/prisma.js';
import { validate } from '../middleware/validate.js';
import { createCollectionSchema, updateCollectionSchema } from '../schemas/collectionSchemas.js';

const router = Router();

// Helper function to transform bookmark tags
function transformBookmarkTags(bookmark: any) {
  return {
    ...bookmark,
    tags: bookmark.tags?.map((bt: any) => ({
      id: bt.tag.id,
      name: bt.tag.name,
    })) || [],
  };
}

// GET / - Get all collections with bookmark count
router.get('/', async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const collections = await prisma.collection.findMany({
      include: {
        _count: {
          select: {
            bookmarks: true,
          },
        },
      },
    });

    const transformedCollections = collections.map(({ _count, ...rest }) => ({
      ...rest,
      bookmarkCount: _count.bookmarks,
    }));

    res.json({
      success: true,
      data: transformedCollections,
    });
  } catch (error) {
    next(error);
  }
});

// POST / - Create collection
router.post('/', validate(createCollectionSchema), async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const collection = await prisma.collection.create({
      data: req.body,
    });

    res.status(201).json({
      success: true,
      data: collection,
    });
  } catch (error) {
    next(error);
  }
});

// GET /:id - Get single collection
router.get('/:id', async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const id = Number(req.params.id);

    const collection = await prisma.collection.findUnique({
      where: { id },
      include: {
        _count: {
          select: {
            bookmarks: true,
          },
        },
      },
    });

    if (!collection) {
      res.status(404).json({
        success: false,
        error: 'Collection not found',
      });
      return;
    }

    const { _count, ...rest } = collection;
    const transformedCollection = {
      ...rest,
      bookmarkCount: _count.bookmarks,
    };

    res.json({
      success: true,
      data: transformedCollection,
    });
  } catch (error) {
    next(error);
  }
});

// PUT /:id - Update collection
router.put('/:id', validate(updateCollectionSchema), async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const id = Number(req.params.id);

    const existingCollection = await prisma.collection.findUnique({
      where: { id },
    });

    if (!existingCollection) {
      res.status(404).json({
        success: false,
        error: 'Collection not found',
      });
      return;
    }

    const collection = await prisma.collection.update({
      where: { id },
      data: req.body,
      include: {
        _count: {
          select: {
            bookmarks: true,
          },
        },
      },
    });

    const { _count: updateCount, ...updateRest } = collection;
    const transformedCollection = {
      ...updateRest,
      bookmarkCount: updateCount.bookmarks,
    };

    res.json({
      success: true,
      data: transformedCollection,
    });
  } catch (error) {
    next(error);
  }
});

// DELETE /:id - Delete collection (cascade deletes bookmarks)
router.delete('/:id', async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const id = Number(req.params.id);

    const existingCollection = await prisma.collection.findUnique({
      where: { id },
    });

    if (!existingCollection) {
      res.status(404).json({
        success: false,
        error: 'Collection not found',
      });
      return;
    }

    await prisma.collection.delete({
      where: { id },
    });

    res.json({
      success: true,
      data: { message: 'Collection deleted' },
    });
  } catch (error) {
    next(error);
  }
});

// GET /:id/bookmarks - Get all bookmarks in collection
router.get('/:id/bookmarks', async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const id = Number(req.params.id);

    const existingCollection = await prisma.collection.findUnique({
      where: { id },
    });

    if (!existingCollection) {
      res.status(404).json({
        success: false,
        error: 'Collection not found',
      });
      return;
    }

    const bookmarks = await prisma.bookmark.findMany({
      where: { collectionId: id },
      include: {
        tags: {
          include: {
            tag: true,
          },
        },
        collection: true,
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

export default router;
