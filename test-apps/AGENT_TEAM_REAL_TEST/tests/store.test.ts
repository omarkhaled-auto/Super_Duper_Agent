import { describe, test, expect, vi } from 'vitest';
import { Store } from '../src/Store.js';

describe('Store', () => {
  // Basic operations
  test('getState returns initial state', () => {
    const store = new Store({ initialState: { count: 0, name: 'test' } });
    expect(store.getState()).toEqual({ count: 0, name: 'test' });
  });

  test('getState returns frozen object', () => {
    const store = new Store({ initialState: { count: 0 } });
    const state = store.getState();
    expect(() => { (state as any).count = 5; }).toThrow();
  });

  test('setState updates state partially', () => {
    const store = new Store({ initialState: { a: 1, b: 2 } });
    store.setState({ a: 10 });
    expect(store.getState()).toEqual({ a: 10, b: 2 });
  });

  test('setState with function receives current state', () => {
    const store = new Store({ initialState: { count: 5 } });
    store.setState(state => ({ count: state.count + 1 }));
    expect(store.getState().count).toBe(6);
  });

  test('subscribe notifies on state change', () => {
    const store = new Store({ initialState: { value: 0 } });
    const listener = vi.fn();
    store.subscribe(listener);
    store.setState({ value: 1 });
    expect(listener).toHaveBeenCalledWith({ value: 1 }, { value: 0 });
  });

  test('unsubscribe stops notifications', () => {
    const store = new Store({ initialState: { value: 0 } });
    const listener = vi.fn();
    const unsub = store.subscribe(listener);
    unsub();
    store.setState({ value: 1 });
    expect(listener).not.toHaveBeenCalled();
  });

  test('reset restores initial state', () => {
    const store = new Store({ initialState: { count: 0 } });
    store.setState({ count: 100 });
    store.reset();
    expect(store.getState().count).toBe(0);
  });

  // Transactions
  test('transaction batches multiple setState calls', () => {
    const store = new Store({ initialState: { a: 0, b: 0 } });
    const listener = vi.fn();
    store.subscribe(listener);

    store.transaction(() => {
      store.setState({ a: 1 });
      store.setState({ b: 2 });
      store.setState({ a: 3 });
    });

    // Listener called only ONCE with final state
    expect(listener).toHaveBeenCalledTimes(1);
    expect(listener).toHaveBeenCalledWith({ a: 3, b: 2 }, { a: 0, b: 0 });
  });

  // ═══════════════════════════════════════════════════════════
  // CRITICAL TEST: Transaction Rollback
  // ═══════════════════════════════════════════════════════════
  test('CRITICAL: transaction rolls back ALL changes on error', () => {
    const store = new Store({ initialState: { a: 1, b: 2, c: 3 } });

    expect(() => {
      store.transaction(() => {
        store.setState({ a: 10 });
        store.setState({ b: 20 });
        store.setState({ c: 30 });
        throw new Error('Simulated failure');
      });
    }).toThrow('Simulated failure');

    // State must be COMPLETELY restored
    expect(store.getState()).toEqual({ a: 1, b: 2, c: 3 });
  });

  test('CRITICAL: transaction rollback does not notify subscribers', () => {
    const store = new Store({ initialState: { value: 0 } });
    const listener = vi.fn();
    store.subscribe(listener);

    try {
      store.transaction(() => {
        store.setState({ value: 100 });
        throw new Error('Fail');
      });
    } catch {}

    // No notification should have occurred
    expect(listener).not.toHaveBeenCalled();
  });

  test('transaction returns result on success', () => {
    const store = new Store({ initialState: { count: 0 } });

    const result = store.transaction(() => {
      store.setState({ count: 5 });
      return 'success';
    });

    expect(result).toBe('success');
    expect(store.getState().count).toBe(5);
  });

  // History
  test('undo reverts to previous state', () => {
    const store = new Store({
      initialState: { value: 'A' },
      enableHistory: true
    });

    store.setState({ value: 'B' });
    store.setState({ value: 'C' });

    expect(store.undo()).toBe(true);
    expect(store.getState().value).toBe('B');

    expect(store.undo()).toBe(true);
    expect(store.getState().value).toBe('A');
  });

  test('redo restores undone state', () => {
    const store = new Store({
      initialState: { value: 'A' },
      enableHistory: true
    });

    store.setState({ value: 'B' });
    store.undo();

    expect(store.redo()).toBe(true);
    expect(store.getState().value).toBe('B');
  });

  // ═══════════════════════════════════════════════════════════
  // CRITICAL TEST: New Action Clears Redo Stack
  // ═══════════════════════════════════════════════════════════
  test('CRITICAL: new setState after undo clears redo stack', () => {
    const store = new Store({
      initialState: { value: 'A' },
      enableHistory: true
    });

    store.setState({ value: 'B' });
    store.setState({ value: 'C' });

    store.undo(); // At B
    expect(store.canRedo()).toBe(true); // Can redo to C

    store.setState({ value: 'D' }); // New action from B

    expect(store.canRedo()).toBe(false); // Redo to C is GONE
    expect(store.getState().value).toBe('D');

    store.undo();
    expect(store.getState().value).toBe('B'); // NOT C
  });

  test('history limit is enforced', () => {
    const store = new Store({
      initialState: { value: 0 },
      enableHistory: true,
      historyLimit: 3
    });

    store.setState({ value: 1 });
    store.setState({ value: 2 });
    store.setState({ value: 3 });
    store.setState({ value: 4 });
    store.setState({ value: 5 });

    // Should only be able to undo 3 times (limit)
    expect(store.undo()).toBe(true); // 5 -> 4
    expect(store.undo()).toBe(true); // 4 -> 3
    expect(store.undo()).toBe(true); // 3 -> 2

    // History limit reached
    expect(store.canUndo()).toBe(false);
  });
});
