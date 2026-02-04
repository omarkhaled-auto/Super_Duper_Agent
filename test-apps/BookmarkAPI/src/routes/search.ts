import { Router, Request, Response, NextFunction } from 'express';
import { prisma } from '../lib/prisma.js';

const router = Router();

router.get('/', async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const query = req.query.q as string | undefined;

    if (!query) {
      res.status(400).json({
        success: false,
        error: "Query parameter 'q' is required",
      });
      return;
    }

    const bookmarks = await prisma.bookmark.findMany({
      where: {
        OR: [
          { title: { contains: query } },
          { url: { contains: query } },
          { description: { contains: query } },
        ],
      },
      include: {
        collection: true,
        tags: {
          include: {
            tag: true,
          },
        },
      },
    });

    const transformedBookmarks = bookmarks.map((bookmark) => ({
      ...bookmark,
      tags: bookmark.tags.map((bt) => ({
        id: bt.tag.id,
        name: bt.tag.name,
      })),
    }));

    res.json({
      success: true,
      data: transformedBookmarks,
    });
  } catch (error) {
    next(error);
  }
});

export default router;
