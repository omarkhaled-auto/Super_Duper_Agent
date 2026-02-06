export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  errors?: ApiError[];
  meta?: ResponseMeta;
}

export interface ApiError {
  field?: string;
  code: string;
  message: string;
}

export interface ResponseMeta {
  timestamp: string;
  requestId?: string;
  version?: string;
}

export interface ValidationError {
  [field: string]: string[];
}

export interface ErrorResponse {
  success: false;
  message: string;
  errors?: ApiError[];
  statusCode: number;
}
