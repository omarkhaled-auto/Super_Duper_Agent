/**
 * Store - State container with transactions and optional history
 *
 * Key features:
 * - Immutable state (Object.freeze)
 * - Partial updates via setState
 * - Functional updates: setState(state => partial)
 * - Transaction support with rollback on error
 * - Optional undo/redo history
 * - Batched notifications during transactions
 */

import { Unsubscribe } from './Observable.js';

export interface StoreConfig<T extends object> {
  initialState: T;
  enableHistory?: boolean;
  historyLimit?: number;
}

export interface IStore<T extends object> {
  getState(): Readonly<T>;
  setState(partial: Partial<T>): void;
  setState(updater: (state: T) => Partial<T>): void;
  subscribe(listener: (state: T, prevState: T) => void): Unsubscribe;
  transaction<R>(fn: () => R): R;
}

type StateListener<T> = (state: T, prevState: T) => void;

/**
 * Store class - centralized state management with transactions and history
 */
export class Store<T extends object> implements IStore<T> {
  private state: T;
  private readonly initialState: T;
  private readonly listeners: Set<StateListener<T>> = new Set();

  // Transaction state
  private inTransaction: boolean = false;
  private transactionStartState: T | null = null;
  private pendingNotification: { newState: T; prevState: T } | null = null;

  // History
  private readonly enableHistory: boolean;
  private readonly historyLimit: number;
  private undoStack: T[] = [];
  private redoStack: T[] = [];

  constructor(config: StoreConfig<T>) {
    this.initialState = this.deepClone(config.initialState);
    this.state = this.deepClone(config.initialState);
    this.enableHistory = config.enableHistory ?? false;
    this.historyLimit = config.historyLimit ?? 100;
  }

  /**
   * Get the current state
   * Returns a frozen copy to ensure immutability
   */
  getState(): Readonly<T> {
    return Object.freeze({ ...this.state });
  }

  /**
   * Update state with a partial update or an updater function
   */
  setState(partialOrUpdater: Partial<T> | ((state: T) => Partial<T>)): void {
    const prevState = this.state;
    const partial = typeof partialOrUpdater === 'function'
      ? partialOrUpdater(this.state)
      : partialOrUpdater;

    // Merge partial into state
    const newState = { ...this.state, ...partial };

    // Save to history before updating (if enabled and not in transaction)
    if (this.enableHistory && !this.inTransaction) {
      this.undoStack.push(this.deepClone(prevState));

      // Enforce history limit
      if (this.undoStack.length > this.historyLimit) {
        this.undoStack.shift();
      }

      // Clear redo stack on new action (KILLER TEST requirement)
      this.redoStack = [];
    }

    this.state = newState;

    // Handle notification
    if (this.inTransaction) {
      // Batch notification - store for later
      this.pendingNotification = {
        newState: this.state,
        prevState: this.transactionStartState as T
      };
    } else {
      // Immediate notification
      this.notify(newState, prevState);
    }
  }

  /**
   * Subscribe to state changes
   */
  subscribe(listener: StateListener<T>): Unsubscribe {
    this.listeners.add(listener);

    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * Execute a transaction
   * - Multiple setState calls = one notification at end
   * - If error thrown, ALL changes are rolled back and NO notification is sent
   */
  transaction<R>(fn: () => R): R {
    // Save snapshot for potential rollback
    const snapshot = this.deepClone(this.state);
    const prevUndoStack = this.enableHistory ? [...this.undoStack.map(s => this.deepClone(s))] : [];
    const prevRedoStack = this.enableHistory ? [...this.redoStack.map(s => this.deepClone(s))] : [];

    this.inTransaction = true;
    this.transactionStartState = snapshot;
    this.pendingNotification = null;

    try {
      const result = fn();

      // Transaction succeeded - send batched notification if state changed
      this.inTransaction = false;

      // Use getPendingNotification() to work around TypeScript's control-flow analysis.
      // TS cannot track that fn() mutates this.pendingNotification from null,
      // so direct access narrows the type to 'never'. The method call breaks the narrowing chain.
      const pending = this.getPendingNotification();
      if (pending !== null) {
        // Save to history for successful transaction
        if (this.enableHistory) {
          this.undoStack.push(snapshot);

          if (this.undoStack.length > this.historyLimit) {
            this.undoStack.shift();
          }

          this.redoStack = [];
        }

        this.notify(pending.newState, pending.prevState);
      }

      this.transactionStartState = null;
      this.pendingNotification = null;

      return result;
    } catch (error) {
      // Transaction failed - ROLLBACK everything
      this.state = snapshot;

      // Restore history stacks
      if (this.enableHistory) {
        this.undoStack = prevUndoStack;
        this.redoStack = prevRedoStack;
      }

      this.inTransaction = false;
      this.transactionStartState = null;
      this.pendingNotification = null;

      // NO notification on rollback

      // Re-throw the original error to preserve its message for caller assertions
      throw error;
    }
  }

  /**
   * Undo the last state change
   * Returns true if undo was successful, false if nothing to undo
   */
  undo(): boolean {
    if (!this.enableHistory || this.undoStack.length === 0) {
      return false;
    }

    const prevState = this.state;

    // Push current state to redo stack
    this.redoStack.push(this.deepClone(this.state));

    // Pop from undo stack
    const previousState = this.undoStack.pop();
    if (previousState === undefined) {
      return false;
    }

    this.state = previousState;
    this.notify(this.state, prevState);

    return true;
  }

  /**
   * Redo the last undone state change
   * Returns true if redo was successful, false if nothing to redo
   */
  redo(): boolean {
    if (!this.enableHistory || this.redoStack.length === 0) {
      return false;
    }

    const prevState = this.state;

    // Push current state to undo stack
    this.undoStack.push(this.deepClone(this.state));

    // Pop from redo stack
    const nextState = this.redoStack.pop();
    if (nextState === undefined) {
      return false;
    }

    this.state = nextState;
    this.notify(this.state, prevState);

    return true;
  }

  /**
   * Check if undo is available
   */
  canUndo(): boolean {
    return this.enableHistory && this.undoStack.length > 0;
  }

  /**
   * Check if redo is available
   */
  canRedo(): boolean {
    return this.enableHistory && this.redoStack.length > 0;
  }

  /**
   * Reset state to initial value
   */
  reset(): void {
    const prevState = this.state;
    this.state = this.deepClone(this.initialState);

    if (this.enableHistory) {
      this.undoStack.push(this.deepClone(prevState));

      if (this.undoStack.length > this.historyLimit) {
        this.undoStack.shift();
      }

      this.redoStack = [];
    }

    this.notify(this.state, prevState);
  }

  /**
   * Destroy the store and clean up
   */
  destroy(): void {
    this.listeners.clear();
    this.undoStack = [];
    this.redoStack = [];
  }

  /**
   * Notify all listeners of a state change
   */
  private notify(newState: T, prevState: T): void {
    // Take snapshot of listeners
    const snapshot = [...this.listeners];

    for (const listener of snapshot) {
      if (this.listeners.has(listener)) {
        listener(newState, prevState);
      }
    }
  }

  /**
   * Get the pending notification (workaround for TypeScript control-flow narrowing)
   * TS cannot track that fn() in transaction() mutates this.pendingNotification,
   * so direct field access after fn() returns narrows to 'never'.
   */
  private getPendingNotification(): { newState: T; prevState: T } | null {
    return this.pendingNotification;
  }

  /**
   * Deep clone a state object
   */
  private deepClone(obj: T): T {
    return structuredClone(obj);
  }
}
