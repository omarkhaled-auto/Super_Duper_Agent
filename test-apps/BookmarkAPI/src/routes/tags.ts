import { Router, Request, Response, NextFunction } from 'express';
import { prisma } from '../lib/prisma.js';
import { validate } from '../middleware/validate.js';
import { createTagSchema } from '../schemas/tagSchemas.js';

const router = Router();

// GET / - List all tags with bookmark count
router.get('/', async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const tags = await prisma.tag.findMany({
      include: {
        _count: {
          select: {
            bookmarks: true,
          },
        },
      },
    });

    const transformedTags = tags.map(({ _count, ...rest }) => ({
      ...rest,
      bookmarkCount: _count.bookmarks,
    }));

    res.json({
      success: true,
      data: transformedTags,
    });
  } catch (error) {
    next(error);
  }
});

// POST / - Create tag
router.post('/', validate(createTagSchema), async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const tag = await prisma.tag.create({
      data: req.body,
    });

    res.status(201).json({
      success: true,
      data: tag,
    });
  } catch (error) {
    next(error);
  }
});

// DELETE /:id - Delete tag
router.delete('/:id', async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const id = Number(req.params.id);

    const existing = await prisma.tag.findUnique({
      where: { id },
    });

    if (!existing) {
      res.status(404).json({
        success: false,
        error: 'Tag not found',
      });
      return;
    }

    await prisma.tag.delete({
      where: { id },
    });

    res.json({
      success: true,
      data: { message: 'Tag deleted' },
    });
  } catch (error) {
    next(error);
  }
});

export default router;
