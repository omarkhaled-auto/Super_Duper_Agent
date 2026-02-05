import { describe, test, expect } from 'vitest';
import {
  ReactiveStoreError,
  CircularDependencyError,
  TransactionError
} from '../src/errors.js';

describe('Errors', () => {
  test('ReactiveStoreError has correct name', () => {
    const error = new ReactiveStoreError('test');
    expect(error.name).toBe('ReactiveStoreError');
    expect(error.message).toBe('test');
  });

  test('CircularDependencyError includes chain', () => {
    const error = new CircularDependencyError(['A', 'B', 'C', 'A']);
    expect(error.chain).toEqual(['A', 'B', 'C', 'A']);
    expect(error.message).toContain('A → B → C → A');
  });

  test('CircularDependencyError works without chain', () => {
    const error = new CircularDependencyError();
    expect(error.chain).toEqual([]);
  });

  test('TransactionError includes cause', () => {
    const cause = new Error('Original');
    const error = new TransactionError('Transaction failed', cause);
    expect(error.cause).toBe(cause);
  });

  test('All errors extend ReactiveStoreError', () => {
    expect(new CircularDependencyError()).toBeInstanceOf(ReactiveStoreError);
    expect(new TransactionError('test')).toBeInstanceOf(ReactiveStoreError);
  });
});
