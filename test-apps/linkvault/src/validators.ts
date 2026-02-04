/**
 * LinkVault Validators
 * URL validation, bookmark validation middleware, and tags validation
 */

import { Request, Response, NextFunction, RequestHandler } from 'express';
import { ValidationResult, AppError } from './types';

// =============================================================================
// URL Validation
// =============================================================================

/**
 * Validates a URL string
 * @param url - The URL to validate
 * @returns ValidationResult indicating success or failure with error message
 */
export function validateUrl(url: string): ValidationResult {
  // Check if url is a non-empty string
  if (typeof url !== 'string' || url.trim() === '') {
    return { valid: false, error: 'URL must be a non-empty string' };
  }

  try {
    const parsedUrl = new URL(url);

    // Check protocol is http or https
    if (parsedUrl.protocol !== 'http:' && parsedUrl.protocol !== 'https:') {
      return { valid: false, error: 'URL must use http or https protocol' };
    }

    return { valid: true };
  } catch {
    return { valid: false, error: 'Invalid URL format' };
  }
}

// =============================================================================
// Tags Validation
// =============================================================================

/**
 * Validates tags array
 * @param tags - The tags to validate (unknown type for runtime checking)
 * @returns ValidationResult indicating success or failure with error message
 */
export function validateTags(tags: unknown): ValidationResult {
  // Check if tags is an array
  if (!Array.isArray(tags)) {
    return { valid: false, error: 'Tags must be an array' };
  }

  // Check each element
  for (let i = 0; i < tags.length; i++) {
    const tag = tags[i];

    // Check if element is a string
    if (typeof tag !== 'string') {
      return { valid: false, error: `Tag at index ${i} must be a string` };
    }

    // Check if string is non-empty after trim
    if (tag.trim() === '') {
      return { valid: false, error: `Tag at index ${i} must be a non-empty string` };
    }
  }

  return { valid: true };
}

/**
 * Sanitizes tags array by trimming whitespace and filtering empty strings
 * @param tags - Array of tags to sanitize
 * @returns Cleaned array of tags
 */
export function sanitizeTags(tags: string[]): string[] {
  return tags
    .map(tag => tag.trim())
    .filter(tag => tag !== '');
}

// =============================================================================
// Bookmark Validation Middleware
// =============================================================================

/**
 * Middleware to validate bookmark creation requests (POST)
 * Validates title, url, and optional tags
 */
export const validateBookmark: RequestHandler = (
  req: Request,
  res: Response,
  next: NextFunction
): void => {
  const { title, url, tags } = req.body;

  // Validate title: required, non-empty string after trim
  if (typeof title !== 'string' || title.trim() === '') {
    next(new AppError(400, 'Title is required and must be a non-empty string', 'VALIDATION_ERROR'));
    return;
  }

  // Validate url: required, valid URL
  if (url === undefined || url === null) {
    next(new AppError(400, 'URL is required', 'VALIDATION_ERROR'));
    return;
  }

  const urlValidation = validateUrl(url);
  if (!urlValidation.valid) {
    next(new AppError(400, urlValidation.error!, 'VALIDATION_ERROR'));
    return;
  }

  // Validate tags: optional, if present must pass validateTags
  if (tags !== undefined) {
    const tagsValidation = validateTags(tags);
    if (!tagsValidation.valid) {
      next(new AppError(400, tagsValidation.error!, 'VALIDATION_ERROR'));
      return;
    }
    // Sanitize tags
    req.body.tags = sanitizeTags(tags);
  } else {
    // Default tags to empty array if not provided
    req.body.tags = [];
  }

  // Sanitize title
  req.body.title = title.trim();

  next();
};

/**
 * Middleware to validate bookmark update requests (PUT)
 * All fields optional but at least one must be present
 */
export const validateBookmarkUpdate: RequestHandler = (
  req: Request,
  res: Response,
  next: NextFunction
): void => {
  const { title, url, tags } = req.body;

  // Check that at least one field is provided
  const hasTitle = title !== undefined;
  const hasUrl = url !== undefined;
  const hasTags = tags !== undefined;

  if (!hasTitle && !hasUrl && !hasTags) {
    next(new AppError(400, 'At least one field (title, url, or tags) must be provided', 'VALIDATION_ERROR'));
    return;
  }

  // Validate title if provided: must be non-empty string
  if (hasTitle) {
    if (typeof title !== 'string' || title.trim() === '') {
      next(new AppError(400, 'Title must be a non-empty string', 'VALIDATION_ERROR'));
      return;
    }
    // Sanitize title
    req.body.title = title.trim();
  }

  // Validate url if provided: must be valid URL
  if (hasUrl) {
    const urlValidation = validateUrl(url);
    if (!urlValidation.valid) {
      next(new AppError(400, urlValidation.error!, 'VALIDATION_ERROR'));
      return;
    }
  }

  // Validate tags if provided: must pass validateTags
  if (hasTags) {
    const tagsValidation = validateTags(tags);
    if (!tagsValidation.valid) {
      next(new AppError(400, tagsValidation.error!, 'VALIDATION_ERROR'));
      return;
    }
    // Sanitize tags
    req.body.tags = sanitizeTags(tags);
  }

  next();
};
