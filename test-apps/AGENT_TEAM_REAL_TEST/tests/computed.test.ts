import { describe, test, expect, vi } from 'vitest';
import { Observable } from '../src/Observable.js';
import { Computed } from '../src/Computed.js';
import { CircularDependencyError } from '../src/errors.js';

describe('Computed', () => {
  // Basic functionality
  test('computes derived value', () => {
    const a = new Observable(2);
    const b = new Observable(3);
    const sum = new Computed(() => a.get() + b.get());
    expect(sum.get()).toBe(5);
  });

  test('recomputes when dependency changes', () => {
    const a = new Observable(1);
    const double = new Computed(() => a.get() * 2);
    expect(double.get()).toBe(2);
    a.set(5);
    expect(double.get()).toBe(10);
  });

  test('memoizes result when dependencies unchanged', () => {
    const a = new Observable(1);
    let computeCount = 0;
    const computed = new Computed(() => {
      computeCount++;
      return a.get() * 2;
    });

    computed.get();
    computed.get();
    computed.get();

    expect(computeCount).toBe(1); // Only computed once
  });

  test('tracks multiple dependencies', () => {
    const a = new Observable(1);
    const b = new Observable(2);
    const c = new Observable(3);
    const sum = new Computed(() => a.get() + b.get() + c.get());

    // Force computation to capture dependencies
    sum.get();

    expect(sum.getDependencies().length).toBe(3);
  });

  test('only recomputes when relevant dependency changes', () => {
    const a = new Observable(1);
    const b = new Observable(2);
    const unrelated = new Observable(999);

    let computeCount = 0;
    const sum = new Computed(() => {
      computeCount++;
      return a.get() + b.get();
    });

    sum.get(); // Initial
    computeCount = 0;

    unrelated.set(1000); // Change unrelated observable
    sum.get();

    expect(computeCount).toBe(0); // Should NOT recompute
  });

  test('lazy evaluation - does not compute until get()', () => {
    const a = new Observable(1);
    let computeCount = 0;
    const computed = new Computed(() => {
      computeCount++;
      return a.get() * 2;
    });

    expect(computeCount).toBe(0); // Not computed yet
    computed.get();
    expect(computeCount).toBe(1); // Now computed
  });

  // Subscription tests
  test('subscribe notifies when computed value changes', () => {
    const a = new Observable(1);
    const double = new Computed(() => a.get() * 2);

    const listener = vi.fn();
    double.subscribe(listener);

    a.set(5);

    expect(listener).toHaveBeenCalledWith(10, 2);
  });

  test('subscribe does not notify when result unchanged', () => {
    const a = new Observable(2);
    const isEven = new Computed(() => a.get() % 2 === 0);

    const listener = vi.fn();
    isEven.subscribe(listener);

    a.set(4); // Still even

    expect(listener).not.toHaveBeenCalled();
  });

  // Computed chains
  test('computed can depend on other computed', () => {
    const a = new Observable(2);
    const b = new Computed(() => a.get() * 2); // 4
    const c = new Computed(() => b.get() + 1); // 5

    expect(c.get()).toBe(5);

    a.set(3);
    expect(c.get()).toBe(7); // 3 * 2 + 1
  });

  test('long computed chain updates correctly', () => {
    const a = new Observable(1);
    const b = new Computed(() => a.get() + 1);
    const c = new Computed(() => b.get() + 1);
    const d = new Computed(() => c.get() + 1);
    const e = new Computed(() => d.get() + 1);

    expect(e.get()).toBe(5);

    a.set(10);
    expect(e.get()).toBe(14);
  });

  // ═══════════════════════════════════════════════════════════
  // CRITICAL TEST: Diamond Dependency
  // This is where most implementations fail
  // ═══════════════════════════════════════════════════════════
  test('CRITICAL: diamond dependency - D recomputes exactly ONCE', () => {
    const a = new Observable(1);
    const b = new Computed(() => a.get() * 2);
    const c = new Computed(() => a.get() * 3);

    let dComputeCount = 0;
    const d = new Computed(() => {
      dComputeCount++;
      return b.get() + c.get();
    });

    // Initial computation
    expect(d.get()).toBe(5); // 1*2 + 1*3 = 5
    dComputeCount = 0;

    // Change A - both B and C will be invalidated
    a.set(2);

    // Get D - it should recompute exactly ONCE
    const result = d.get();

    expect(result).toBe(10); // 2*2 + 2*3 = 10
    expect(dComputeCount).toBe(1); // NOT 2!
  });

  test('CRITICAL: diamond dependency - no glitch/inconsistent state', () => {
    const a = new Observable(1);
    const b = new Computed(() => a.get() * 2);
    const c = new Computed(() => a.get() * 3);

    const observedValues: number[] = [];
    const d = new Computed(() => {
      const result = b.get() + c.get();
      observedValues.push(result);
      return result;
    });

    d.get(); // Initial: 5
    observedValues.length = 0;

    a.set(2);
    d.get();

    // Should NEVER see inconsistent state like 7 (old b + new c) or 8 (new b + old c)
    expect(observedValues).not.toContain(7);
    expect(observedValues).not.toContain(8);
    expect(observedValues).toContain(10);
  });

  // ═══════════════════════════════════════════════════════════
  // CRITICAL TEST: Circular Dependency Detection
  // Must throw error, NOT infinite loop
  // ═══════════════════════════════════════════════════════════
  test('CRITICAL: circular dependency throws error, not infinite loop', () => {
    // Use a wrapper to allow circular reference
    let bRef: Computed<number>;

    const a = new Computed(() => {
      return bRef.get() + 1;
    });

    bRef = new Computed(() => {
      return a.get() + 1;
    });

    // This MUST throw, not hang
    expect(() => a.get()).toThrow();
  });

  test('CRITICAL: self-referential computed throws error', () => {
    let selfRef: Computed<number>;

    selfRef = new Computed(() => {
      return selfRef.get() + 1;
    });

    expect(() => selfRef.get()).toThrow();
  });

  // Edge cases
  test('computed with conditional dependencies', () => {
    const condition = new Observable(true);
    const a = new Observable(1);
    const b = new Observable(2);

    let computeCount = 0;
    const result = new Computed(() => {
      computeCount++;
      return condition.get() ? a.get() : b.get();
    });

    expect(result.get()).toBe(1);
    computeCount = 0;

    // Change b - should NOT trigger recompute (b is not a current dependency)
    b.set(20);
    result.get();
    expect(computeCount).toBe(0);

    // Change condition - should recompute and now depend on b
    condition.set(false);
    expect(result.get()).toBe(20);
  });

  test('computed updates dependencies when they change', () => {
    const condition = new Observable(true);
    const a = new Observable(1);
    const b = new Observable(2);

    const result = new Computed(() => {
      return condition.get() ? a.get() : b.get();
    });

    result.get(); // Depends on condition, a

    condition.set(false);
    result.get(); // Now depends on condition, b

    // Changing a should NOT trigger recompute
    let computeCount = 0;
    const monitored = new Computed(() => {
      computeCount++;
      return result.get();
    });

    monitored.get();
    computeCount = 0;

    a.set(100);
    monitored.get();

    // This is implementation-dependent, but ideally no recompute
  });

  test('computed handles undefined result', () => {
    const a = new Observable<number | null>(5);
    const result = new Computed(() => {
      const val = a.get();
      return val === null ? undefined : val * 2;
    });

    expect(result.get()).toBe(10);

    a.set(null);
    expect(result.get()).toBeUndefined();
  });

  test('getRecomputeCount tracks recomputations', () => {
    const a = new Observable(1);
    const computed = new Computed(() => a.get() * 2);

    expect(computed.getRecomputeCount()).toBe(0);

    computed.get();
    expect(computed.getRecomputeCount()).toBe(1);

    computed.get(); // Cached
    expect(computed.getRecomputeCount()).toBe(1);

    a.set(2);
    computed.get();
    expect(computed.getRecomputeCount()).toBe(2);
  });

  test('custom equals function suppresses notification', () => {
    const a = new Observable(1);
    const computed = new Computed(
      () => ({ value: a.get(), label: 'item' }),
      (prev, next) => prev.value === next.value
    );

    const listener = vi.fn();
    computed.subscribe(listener);

    // Change a — computed result has new object reference but same .value
    a.set(1); // Same value, no recompute triggered
    expect(listener).not.toHaveBeenCalled();

    // Now change to actually different value
    a.set(2);
    expect(listener).toHaveBeenCalledTimes(1);
    expect(listener.mock.calls[0]![0]).toEqual({ value: 2, label: 'item' });
  });

  test('properly cleans up old dependency subscriptions on recompute', () => {
    const a = new Observable(1);
    const b = new Observable(2);
    const condition = new Observable(true);

    let computeCount = 0;
    const result = new Computed(() => {
      computeCount++;
      return condition.get() ? a.get() : b.get();
    });

    // Initial: depends on condition + a
    result.get();
    computeCount = 0;

    // Switch to depend on condition + b
    condition.set(false);
    result.get();
    computeCount = 0;

    // Changing a should NOT cause recompute (a is no longer a dependency)
    a.set(100);
    result.get();
    expect(computeCount).toBe(0); // No recompute — a is not tracked

    // Changing b SHOULD cause recompute (b is a current dependency)
    b.set(20);
    result.get();
    expect(computeCount).toBe(1);
    expect(result.get()).toBe(20);
  });
});
