import { Router, Request, Response, NextFunction } from 'express';
import { bookmarkStore } from './store';
import { validateBookmark, validateBookmarkUpdate } from './validators';
import { BookmarkFilter, AppError } from './types';

const router = Router();

/**
 * GET / - List all bookmarks with optional filtering
 * Query params:
 *   - tag: Filter by tag
 *   - search: Search in title and description
 */
router.get('/', (req: Request, res: Response, next: NextFunction): void => {
  try {
    const filter: BookmarkFilter = {};

    if (typeof req.query.tag === 'string' && req.query.tag.trim()) {
      filter.tag = req.query.tag.trim();
    }

    if (typeof req.query.search === 'string' && req.query.search.trim()) {
      filter.search = req.query.search.trim();
    }

    const bookmarks = bookmarkStore.getAll(filter);
    res.status(200).json(bookmarks);
  } catch (error) {
    next(error);
  }
});

/**
 * POST / - Create a new bookmark
 * Body: { url: string, title: string, description?: string, tags?: string[] }
 */
router.post('/', validateBookmark, (req: Request, res: Response, next: NextFunction): void => {
  try {
    const bookmark = bookmarkStore.add(req.body);
    res.status(201).json(bookmark);
  } catch (error) {
    next(error);
  }
});

/**
 * GET /:id - Get a single bookmark by ID
 */
router.get('/:id', (req: Request, res: Response, next: NextFunction): void => {
  try {
    const id = req.params.id;
    const bookmark = bookmarkStore.get(id);

    if (!bookmark) {
      next(new AppError(404, 'Bookmark not found', 'NOT_FOUND'));
      return;
    }

    res.status(200).json(bookmark);
  } catch (error) {
    next(error);
  }
});

/**
 * PUT /:id - Update an existing bookmark
 * Body: { url?: string, title?: string, description?: string, tags?: string[] }
 */
router.put('/:id', validateBookmarkUpdate, (req: Request, res: Response, next: NextFunction): void => {
  try {
    const id = req.params.id;
    const updatedBookmark = bookmarkStore.update(id, req.body);

    if (!updatedBookmark) {
      next(new AppError(404, 'Bookmark not found', 'NOT_FOUND'));
      return;
    }

    res.status(200).json(updatedBookmark);
  } catch (error) {
    next(error);
  }
});

/**
 * DELETE /:id - Delete a bookmark by ID
 */
router.delete('/:id', (req: Request, res: Response, next: NextFunction): void => {
  try {
    const id = req.params.id;
    const deleted = bookmarkStore.delete(id);

    if (!deleted) {
      next(new AppError(404, 'Bookmark not found', 'NOT_FOUND'));
      return;
    }

    res.status(204).send();
  } catch (error) {
    next(error);
  }
});

export { router as bookmarkRouter };
