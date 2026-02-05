/**
 * Base error class for all ReactiveStore errors
 */
export class ReactiveStoreError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ReactiveStoreError';
    // Maintains proper stack trace for where our error was thrown (only available on V8)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, this.constructor);
    }
  }
}

/**
 * Error thrown when a circular dependency is detected in computed values
 */
export class CircularDependencyError extends ReactiveStoreError {
  public readonly chain: string[];

  constructor(chain: string[] = []) {
    const message = chain.length > 0
      ? `Circular dependency detected: ${chain.join(' → ')}`
      : 'Circular dependency detected';
    super(message);
    this.name = 'CircularDependencyError';
    this.chain = chain;
  }
}

/**
 * Error thrown when a transaction fails
 */
export class TransactionError extends ReactiveStoreError {
  public readonly cause?: Error;

  constructor(message: string, cause?: Error) {
    super(message);
    this.name = 'TransactionError';
    this.cause = cause;
  }
}
