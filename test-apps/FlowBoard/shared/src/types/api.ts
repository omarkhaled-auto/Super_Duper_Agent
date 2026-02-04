// =============================================================================
// API Response Wrappers
// =============================================================================

/** Standard successful API response */
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

/** Paginated API response with cursor-based pagination */
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  pageInfo: {
    hasNextPage: boolean;
    hasPreviousPage: boolean;
    endCursor: string | null;
    startCursor: string | null;
  };
}

/** Standard error response */
export interface ApiError {
  message: string;
  errors?: Array<{
    field: string;
    message: string;
  }>;
}
