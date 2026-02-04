import { Request, Response, NextFunction, RequestHandler, ErrorRequestHandler } from 'express';
import { AppError } from './types';

/**
 * Request logger middleware
 * Logs request details after response completes
 */
export const requestLogger: RequestHandler = (req: Request, res: Response, next: NextFunction): void => {
  const startTime = Date.now();

  res.on('finish', () => {
    const duration = Date.now() - startTime;
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] ${req.method} ${req.path} ${res.statusCode} ${duration}ms`);
  });

  next();
};

/**
 * CORS middleware
 * Sets Cross-Origin Resource Sharing headers
 */
export const corsMiddleware: RequestHandler = (req: Request, res: Response, next: NextFunction): void => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    res.status(204).end();
    return;
  }

  next();
};

/**
 * Error handler middleware
 * Handles errors and sends appropriate JSON responses
 */
export const errorHandler: ErrorRequestHandler = (
  err: Error,
  _req: Request,
  res: Response,
  _next: NextFunction
): void => {
  let statusCode: number;
  let message: string;
  let code: string | undefined;

  if (err instanceof AppError) {
    statusCode = err.statusCode;
    message = err.message;
    code = err.code;
  } else {
    statusCode = 500;
    message = 'Internal Server Error';
  }

  console.log(`[ERROR] ${message}`);

  res.status(statusCode);

  if (code) {
    res.json({
      error: {
        message,
        statusCode,
        code
      }
    });
  } else {
    res.json({
      error: {
        message,
        statusCode
      }
    });
  }
};
