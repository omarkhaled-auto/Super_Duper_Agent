/**
 * Observable - A reactive value container that notifies subscribers when changed
 */

export type Listener<T> = (newValue: T, oldValue: T) => void;
export type Unsubscribe = () => void;

export interface IObservable<T> {
  get(): T;
  set(value: T): void;
  subscribe(listener: Listener<T>): Unsubscribe;
}

/**
 * Global dependency tracking context for Computed values
 * This allows Computed to automatically track which Observables it depends on
 */
let currentTracker: Set<Observable<unknown>> | null = null;

/**
 * Internal function to get the current tracker (used by Computed)
 */
export function getCurrentTracker(): Set<Observable<unknown>> | null {
  return currentTracker;
}

/**
 * Internal function to set the current tracker (used by Computed)
 */
export function setCurrentTracker(tracker: Set<Observable<unknown>> | null): void {
  currentTracker = tracker;
}

/**
 * Observable class - the foundation of the reactive system
 */
export class Observable<T> implements IObservable<T> {
  private value: T;
  private readonly equals: (a: T, b: T) => boolean;
  private readonly listeners: Set<Listener<T>> = new Set();
  private isNotifying: boolean = false;
  private pendingUpdates: T[] = [];

  constructor(initialValue: T, equals?: (a: T, b: T) => boolean) {
    this.value = initialValue;
    this.equals = equals ?? ((a: T, b: T): boolean => a === b);
  }

  /**
   * Get the current value
   * If called during a Computed's computation, registers this Observable as a dependency
   */
  get(): T {
    // Register with current tracker if one is active (for Computed dependency tracking)
    if (currentTracker !== null) {
      currentTracker.add(this as Observable<unknown>);
    }
    return this.value;
  }

  /**
   * Set a new value
   * Notifies subscribers if the value changed (according to equality function)
   * If called during notification, queues the update for later
   */
  set(value: T): void {
    // If we're currently notifying, queue this update for later
    if (this.isNotifying) {
      this.pendingUpdates.push(value);
      return;
    }

    // Check equality - no notification if unchanged
    if (this.equals(this.value, value)) {
      return;
    }

    const oldValue = this.value;
    this.value = value;

    this.notify(value, oldValue);
    this.processPendingUpdates();
  }

  /**
   * Subscribe to value changes
   * Returns an unsubscribe function
   */
  subscribe(listener: Listener<T>): Unsubscribe {
    this.listeners.add(listener);

    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * Notify all listeners of a value change
   * Uses a snapshot of listeners to handle modifications during iteration
   */
  private notify(newValue: T, oldValue: T): void {
    this.isNotifying = true;

    // CRITICAL: Take a snapshot of listeners BEFORE iterating
    // This handles:
    // - Unsubscribe during notification (listener removed from Set but still in snapshot)
    // - Subscribe during notification (listener added to Set but not in snapshot)
    const snapshot = [...this.listeners];

    for (const listener of snapshot) {
      // Check if listener is still subscribed (may have been removed during iteration)
      if (this.listeners.has(listener)) {
        listener(newValue, oldValue);
      }
    }

    this.isNotifying = false;
  }

  /**
   * Process any updates that were queued during notification
   */
  private processPendingUpdates(): void {
    while (this.pendingUpdates.length > 0) {
      // The while guard ensures the array is non-empty, so shift() always returns a value.
      // We use `as T` because T may include undefined as a valid value type.
      const nextValue = this.pendingUpdates.shift() as T;

      // Apply equality check for queued updates too
      if (!this.equals(this.value, nextValue)) {
        const oldValue = this.value;
        this.value = nextValue;
        this.notify(nextValue, oldValue);
      }
    }
  }
}
