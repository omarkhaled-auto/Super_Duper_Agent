import { v4 as uuidv4 } from 'uuid';
import { Bookmark, CreateBookmarkDTO, UpdateBookmarkDTO, BookmarkFilter, IBookmarkStore } from './types';

export class BookmarkStore implements IBookmarkStore {
  private bookmarks: Map<string, Bookmark> = new Map();

  add(dto: CreateBookmarkDTO): Bookmark {
    const id = uuidv4();
    const created_at = new Date();
    const bookmark: Bookmark = {
      id,
      url: dto.url,
      title: dto.title,
      tags: dto.tags ?? [],
      created_at,
    };
    this.bookmarks.set(id, bookmark);
    return bookmark;
  }

  get(id: string): Bookmark | undefined {
    return this.bookmarks.get(id);
  }

  getAll(filter?: BookmarkFilter): Bookmark[] {
    let results = Array.from(this.bookmarks.values());

    if (filter?.tag) {
      const tagLower = filter.tag.toLowerCase();
      results = results.filter((bookmark) =>
        bookmark.tags.some((t) => t.toLowerCase() === tagLower)
      );
    }

    if (filter?.search) {
      const searchLower = filter.search.toLowerCase();
      results = results.filter((bookmark) =>
        bookmark.title.toLowerCase().includes(searchLower)
      );
    }

    return results;
  }

  update(id: string, dto: UpdateBookmarkDTO): Bookmark | undefined {
    const existing = this.bookmarks.get(id);
    if (!existing) {
      return undefined;
    }

    const updated: Bookmark = {
      ...existing,
      ...(dto.url !== undefined && { url: dto.url }),
      ...(dto.title !== undefined && { title: dto.title }),
      ...(dto.tags !== undefined && { tags: dto.tags }),
      id: existing.id,
      created_at: existing.created_at,
    };

    this.bookmarks.set(id, updated);
    return updated;
  }

  delete(id: string): boolean {
    return this.bookmarks.delete(id);
  }

  clear(): void {
    this.bookmarks.clear();
  }
}

export const bookmarkStore = new BookmarkStore();
