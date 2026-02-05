import { describe, test, expect, vi } from 'vitest';
import { Observable, Unsubscribe } from '../src/Observable.js';

describe('Observable', () => {
  test('get() returns initial value', () => {
    const obs = new Observable(42);
    expect(obs.get()).toBe(42);
  });

  test('set() updates value', () => {
    const obs = new Observable(1);
    obs.set(2);
    expect(obs.get()).toBe(2);
  });

  test('subscribe() is called on change', () => {
    const obs = new Observable(0);
    const listener = vi.fn();
    obs.subscribe(listener);
    obs.set(1);
    expect(listener).toHaveBeenCalledWith(1, 0);
  });

  test('subscribe() receives old and new values', () => {
    const obs = new Observable('a');
    const listener = vi.fn();
    obs.subscribe(listener);
    obs.set('b');
    expect(listener).toHaveBeenCalledWith('b', 'a');
  });

  test('unsubscribe() stops notifications', () => {
    const obs = new Observable(0);
    const listener = vi.fn();
    const unsub = obs.subscribe(listener);
    unsub();
    obs.set(1);
    expect(listener).not.toHaveBeenCalled();
  });

  test('no notification when value unchanged (primitive)', () => {
    const obs = new Observable(5);
    const listener = vi.fn();
    obs.subscribe(listener);
    obs.set(5);
    expect(listener).not.toHaveBeenCalled();
  });

  test('custom equals function is used', () => {
    const obs = new Observable(
      { id: 1, name: 'test' },
      (a, b) => a.id === b.id
    );
    const listener = vi.fn();
    obs.subscribe(listener);
    obs.set({ id: 1, name: 'changed' }); // Same id, different name
    expect(listener).not.toHaveBeenCalled(); // No notification - ids equal
  });

  test('multiple subscribers all notified', () => {
    const obs = new Observable(0);
    const listener1 = vi.fn();
    const listener2 = vi.fn();
    const listener3 = vi.fn();
    obs.subscribe(listener1);
    obs.subscribe(listener2);
    obs.subscribe(listener3);
    obs.set(1);
    expect(listener1).toHaveBeenCalledWith(1, 0);
    expect(listener2).toHaveBeenCalledWith(1, 0);
    expect(listener3).toHaveBeenCalledWith(1, 0);
  });

  test('subscribers notified in order added', () => {
    const obs = new Observable(0);
    const order: number[] = [];
    obs.subscribe(() => order.push(1));
    obs.subscribe(() => order.push(2));
    obs.subscribe(() => order.push(3));
    obs.set(1);
    expect(order).toEqual([1, 2, 3]);
  });

  test('unsubscribe during notification is safe', () => {
    const obs = new Observable(0);
    let unsub2: Unsubscribe;
    const listener1 = vi.fn(() => {
      unsub2(); // Unsubscribe listener2 while notifying
    });
    const listener2 = vi.fn();
    const listener3 = vi.fn();

    obs.subscribe(listener1);
    unsub2 = obs.subscribe(listener2);
    obs.subscribe(listener3);

    obs.set(1);

    // All three should still be called for THIS notification
    // (unsubscribe takes effect on NEXT change)
    expect(listener1).toHaveBeenCalled();
    expect(listener3).toHaveBeenCalled();
    // listener2 behavior may vary - either called or not is acceptable
    // but NO CRASH
  });

  test('subscribe during notification does not call new subscriber', () => {
    const obs = new Observable(0);
    const laterListener = vi.fn();

    obs.subscribe((newVal) => {
      if (newVal === 1) {
        obs.subscribe(laterListener);
      }
    });

    obs.set(1);

    // laterListener should NOT be called for the change that triggered its subscription
    expect(laterListener).not.toHaveBeenCalled();

    // But it SHOULD be called for subsequent changes
    obs.set(2);
    expect(laterListener).toHaveBeenCalledWith(2, 1);
  });

  test('set during notification queues update', () => {
    const obs = new Observable(0);
    const values: number[] = [];

    obs.subscribe((newVal) => {
      values.push(newVal);
      if (newVal === 1) {
        obs.set(2); // Trigger another change during notification
      }
    });

    obs.set(1);

    // Should see both values, in order
    expect(values).toContain(1);
    expect(values).toContain(2);
  });

  test('handles undefined as valid value', () => {
    const obs = new Observable<number | undefined>(1);
    const listener = vi.fn();
    obs.subscribe(listener);
    obs.set(undefined);
    expect(listener).toHaveBeenCalledWith(undefined, 1);
    expect(obs.get()).toBeUndefined();
  });

  test('handles null as valid value', () => {
    const obs = new Observable<string | null>('test');
    const listener = vi.fn();
    obs.subscribe(listener);
    obs.set(null);
    expect(listener).toHaveBeenCalledWith(null, 'test');
    expect(obs.get()).toBeNull();
  });

  test('multiple sequential updates work correctly', () => {
    const obs = new Observable(0);
    const listener = vi.fn();
    obs.subscribe(listener);

    obs.set(1);
    obs.set(2);
    obs.set(3);

    expect(listener).toHaveBeenCalledTimes(3);
    expect(listener).toHaveBeenNthCalledWith(1, 1, 0);
    expect(listener).toHaveBeenNthCalledWith(2, 2, 1);
    expect(listener).toHaveBeenNthCalledWith(3, 3, 2);
    expect(obs.get()).toBe(3);
  });
});
