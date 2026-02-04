/**
 * LinkVault Core Types and Interfaces
 * Foundation module - NO imports allowed
 */

// =============================================================================
// Core Entity
// =============================================================================

/**
 * Represents a bookmark entity in the system
 */
export interface Bookmark {
  id: string;
  title: string;
  url: string;
  tags: string[];
  created_at: Date;
}

// =============================================================================
// Data Transfer Objects (DTOs)
// =============================================================================

/**
 * DTO for creating a new bookmark
 */
export interface CreateBookmarkDTO {
  title: string;
  url: string;
  tags?: string[];
}

/**
 * DTO for updating an existing bookmark
 */
export interface UpdateBookmarkDTO {
  title?: string;
  url?: string;
  tags?: string[];
}

// =============================================================================
// Filters and Queries
// =============================================================================

/**
 * Filter options for querying bookmarks
 */
export interface BookmarkFilter {
  tag?: string;
  search?: string;
}

// =============================================================================
// Validation
// =============================================================================

/**
 * Result of a validation operation
 */
export interface ValidationResult {
  valid: boolean;
  error?: string;
}

// =============================================================================
// Error Handling
// =============================================================================

/**
 * Custom application error with status code and error code
 */
export class AppError extends Error {
  public readonly statusCode: number;
  public readonly code: string;

  constructor(statusCode: number, message: string, code: string) {
    super(message);
    this.statusCode = statusCode;
    this.code = code;

    // Restore prototype chain (required for extending built-in classes)
    Object.setPrototypeOf(this, AppError.prototype);
  }
}

// =============================================================================
// Store Interface
// =============================================================================

/**
 * Interface for bookmark storage operations
 */
export interface IBookmarkStore {
  add(dto: CreateBookmarkDTO): Bookmark;
  get(id: string): Bookmark | undefined;
  getAll(filter?: BookmarkFilter): Bookmark[];
  update(id: string, dto: UpdateBookmarkDTO): Bookmark | undefined;
  delete(id: string): boolean;
  clear(): void;
}
