/**
 * Computed - Derived reactive values with automatic dependency tracking
 *
 * This is the most complex component of the reactive system.
 * Key features:
 * - Lazy evaluation (only computes on first get() or after invalidation)
 * - Automatic dependency tracking
 * - Memoization (caches results)
 * - Glitch-free updates (diamond dependency handled correctly)
 * - Circular dependency detection
 *
 * Implementation uses PULL-BASED lazy evaluation:
 * - Each Computed tracks both Observable and other Computed dependencies
 * - When marked stale, it marks itself stale without immediate recompute
 * - On get(), if stale, it recomputes by pulling fresh values from all deps
 * - This naturally solves diamond dependency: D.get() pulls from B and C,
 *   which pull from A, so everything is fresh before D computes
 */

import { Observable, Listener, Unsubscribe, getCurrentTracker, setCurrentTracker } from './Observable.js';
import { CircularDependencyError } from './errors.js';

export interface IComputed<T> {
  get(): T;
  subscribe(listener: Listener<T>): Unsubscribe;
}

/**
 * Global stack for tracking which Computed is currently being evaluated
 * Used for circular dependency detection
 */
const computingStack: Set<Computed<unknown>> = new Set();

/**
 * Global tracker for Computed dependencies (separate from Observable tracker)
 * When a Computed's get() is called during another Computed's computation,
 * the outer Computed needs to track the inner one as a dependency
 */
let currentComputedTracker: Set<Computed<unknown>> | null = null;

/**
 * Track dependencies during a function execution
 */
export function trackDependencies<T>(fn: () => T): { result: T; dependencies: Set<Observable<unknown>> } {
  const deps = new Set<Observable<unknown>>();
  const previousTracker = getCurrentTracker();
  setCurrentTracker(deps);

  try {
    const result = fn();
    return { result, dependencies: deps };
  } finally {
    setCurrentTracker(previousTracker);
  }
}

/**
 * Computed class - derived values with automatic dependency tracking
 */
export class Computed<T> implements IComputed<T> {
  private cachedValue: T | undefined;
  private hasValue: boolean = false;
  private isStale: boolean = true;
  private recomputeCount: number = 0;
  private readonly equals: (a: T, b: T) => boolean;
  private readonly computation: () => T;

  // Observable dependencies
  private observableDeps: Set<Observable<unknown>> = new Set();
  private observableSubscriptions: Unsubscribe[] = [];

  // Computed dependencies
  private computedDeps: Set<Computed<unknown>> = new Set();
  private computedSubscriptions: Unsubscribe[] = [];

  // Subscribers to this Computed (other Computeds or external listeners)
  private readonly listeners: Set<Listener<T>> = new Set();

  constructor(computation: () => T, equals?: (a: T, b: T) => boolean) {
    this.computation = computation;
    this.equals = equals ?? ((a: T, b: T): boolean => a === b);
  }

  /**
   * Get the computed value
   * - Uses pull-based lazy evaluation
   * - Detects circular dependencies
   * - Handles diamond dependency correctly (D computes once)
   */
  get(): T {
    // Circular dependency check - if we're already computing this, it's circular
    if (computingStack.has(this as Computed<unknown>)) {
      const chain = [...computingStack].map((_, i) => `Computed${i}`) as string[];
      chain.push('Computed');
      throw new CircularDependencyError(chain);
    }

    // Register with current Computed tracker if one is active
    // This allows outer Computed to track this Computed as a dependency
    if (currentComputedTracker !== null) {
      currentComputedTracker.add(this as Computed<unknown>);
    }

    // If stale or never computed, recompute
    if (this.isStale || !this.hasValue) {
      this.recompute();
    }

    return this.cachedValue as T;
  }

  /**
   * Subscribe to changes in the computed value
   * When a dependency changes, the subscriber will be notified with the new value
   */
  subscribe(listener: Listener<T>): Unsubscribe {
    // Force initial computation if not yet computed
    if (!this.hasValue) {
      this.get();
    }

    this.listeners.add(listener);

    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * Get the list of Observable dependencies (for testing/debugging)
   */
  getDependencies(): Observable<unknown>[] {
    // Force computation to capture dependencies
    if (!this.hasValue) {
      this.get();
    }
    return [...this.observableDeps];
  }

  /**
   * Get the number of times this computed has been recomputed (for testing/debugging)
   */
  getRecomputeCount(): number {
    return this.recomputeCount;
  }

  /**
   * Recompute the value
   * - Tracks both Observable and Computed dependencies during computation
   * - Updates cache
   * - Notifies listeners if value changed
   */
  private recompute(): void {
    // Add to computing stack for circular dependency detection
    computingStack.add(this as Computed<unknown>);

    // Clean up old subscriptions
    this.cleanupSubscriptions();

    // Set up trackers for both Observable and Computed dependencies
    const newObservableDeps = new Set<Observable<unknown>>();
    const newComputedDeps = new Set<Computed<unknown>>();

    const previousObservableTracker = getCurrentTracker();
    const previousComputedTracker = currentComputedTracker;

    setCurrentTracker(newObservableDeps);
    currentComputedTracker = newComputedDeps;

    let newValue: T;
    let oldValue: T | undefined;
    let hadValue: boolean;
    let shouldNotify = false;

    try {
      // Run the computation
      // During computation:
      // - Observable.get() adds to newObservableDeps
      // - Computed.get() adds to newComputedDeps
      newValue = this.computation();

      // Store dependencies
      this.observableDeps = newObservableDeps;
      this.computedDeps = newComputedDeps;

      // Subscribe to all dependencies for invalidation
      this.subscribeToDepencies();

      // Update cache
      oldValue = this.cachedValue;
      hadValue = this.hasValue;

      this.cachedValue = newValue;
      this.hasValue = true;
      this.isStale = false;
      this.recomputeCount++;

      // Check if we need to notify (but don't notify yet - we're still in computingStack)
      shouldNotify = hadValue && !this.equals(oldValue as T, newValue);
    } finally {
      setCurrentTracker(previousObservableTracker);
      currentComputedTracker = previousComputedTracker;
      computingStack.delete(this as Computed<unknown>);
    }

    // Notify AFTER removing from computingStack to avoid false circular detection
    if (shouldNotify) {
      this.notifyListeners(newValue!, oldValue as T);
    }
  }

  /**
   * Subscribe to all dependencies for invalidation notifications
   * Key: We ONLY mark as stale, letting the pull-based approach work
   */
  private subscribeToDepencies(): void {
    // Subscribe to Observable dependencies
    for (const dep of this.observableDeps) {
      const unsub = dep.subscribe(() => {
        this.markStale();
      });
      this.observableSubscriptions.push(unsub);
    }

    // Subscribe to Computed dependencies
    for (const dep of this.computedDeps) {
      const unsub = dep.subscribe(() => {
        this.markStale();
      });
      this.computedSubscriptions.push(unsub);
    }
  }

  /**
   * Clean up subscriptions to old dependencies
   */
  private cleanupSubscriptions(): void {
    for (const unsub of this.observableSubscriptions) {
      unsub();
    }
    this.observableSubscriptions = [];
    this.observableDeps.clear();

    for (const unsub of this.computedSubscriptions) {
      unsub();
    }
    this.computedSubscriptions = [];
    this.computedDeps.clear();
  }

  /**
   * Mark this computed as stale and propagate to listeners
   */
  private markStale(): void {
    const wasStale = this.isStale;
    this.isStale = true;

    // If we have subscribers and weren't already stale, notify them
    if (!wasStale && this.listeners.size > 0 && this.hasValue) {
      const oldValue = this.cachedValue as T;

      // Recompute to get new value (for subscribers)
      if (!computingStack.has(this as Computed<unknown>)) {
        this.recompute();
        // Notification happens inside recompute() if value changed
      }
    }
  }

  /**
   * Notify all listeners of a value change
   */
  private notifyListeners(newValue: T, oldValue: T): void {
    // Take snapshot to handle modifications during iteration
    const snapshot = [...this.listeners];

    for (const listener of snapshot) {
      if (this.listeners.has(listener)) {
        listener(newValue, oldValue);
      }
    }
  }
}
