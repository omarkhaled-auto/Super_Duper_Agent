# ReactiveStore Lite — Production-Grade Builder Test

## Purpose

This specification is designed to **definitively determine**:
1. Is this AI builder production-grade?
2. Can it handle genuinely hard problems?
3. Does it produce code that works correctly under edge cases?

**Philosophy:** "Any builder can generate code. A GOAT builder generates code that actually works."

---

## What This Tests

| Capability | How It's Tested | Why It Matters |
|------------|-----------------|----------------|
| **Basic competence** | Simple features work | Baseline |
| **Complex logic** | Diamond dependency, transaction rollback | Separates good from great |
| **Edge case handling** | Circular deps, empty states, concurrent ops | Production reality |
| **Error handling** | Graceful failures, meaningful errors | Real-world robustness |
| **Type safety** | Strict TypeScript, no `any` | Code quality |
| **Test quality** | Tests that actually test things | Verification |

---

## Technical Requirements

- **Language:** TypeScript 5.x with `strict: true`
- **Runtime:** Node.js 20+
- **Testing:** Vitest
- **Dependencies:** ZERO runtime dependencies
- **Structure:** `src/` for source, `tests/` for tests

### tsconfig.json (MUST use these exact settings)

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "lib": ["ES2022"],
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "tests"]
}
```

---

## Feature 1: Observable (Foundation)

### File: `src/Observable.ts`

A reactive value container that notifies subscribers when changed.

### Type Definitions

```typescript
export type Listener<T> = (newValue: T, oldValue: T) => void;
export type Unsubscribe = () => void;

export interface IObservable<T> {
  get(): T;
  set(value: T): void;
  subscribe(listener: Listener<T>): Unsubscribe;
}
```

### Implementation Requirements

```typescript
export class Observable<T> implements IObservable<T> {
  constructor(initialValue: T, equals?: (a: T, b: T) => boolean);
  
  get(): T;
  set(value: T): void;
  subscribe(listener: Listener<T>): Unsubscribe;
}
```

### Behavior Specification

1. **get()** — Returns current value
2. **set(value)** — Updates value and notifies subscribers IF value changed
3. **subscribe(listener)** — Adds listener, returns unsubscribe function
4. **Equality check** — Uses custom `equals` or `===` by default
5. **No notification on equal value** — If `equals(old, new)` is true, no notification
6. **Multiple subscribers** — All subscribers notified in order added
7. **Unsubscribe safety** — Unsubscribing during notification is safe
8. **Subscribe during notification** — New subscriber NOT called for current change

### Tests: `tests/observable.test.ts` (15 tests)

```typescript
// Basic operations
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
});
```

---

## Feature 2: Computed (Derived Values) — THE HARD ONE

### File: `src/Computed.ts`

Computed values that automatically track dependencies and recompute when needed.

### Type Definitions

```typescript
export interface IComputed<T> {
  get(): T;
  subscribe(listener: Listener<T>): Unsubscribe;
}

// Dependency tracking context (internal)
export interface DependencyTracker {
  track(observable: Observable<any>): void;
  getCaptured(): Set<Observable<any>>;
}
```

### Implementation Requirements

```typescript
export class Computed<T> implements IComputed<T> {
  constructor(
    computation: () => T,
    equals?: (a: T, b: T) => boolean
  );
  
  get(): T;
  subscribe(listener: Listener<T>): Unsubscribe;
  
  // For testing/debugging
  getDependencies(): Observable<any>[];
  getRecomputeCount(): number;
}

// Global dependency tracking (needed for auto-tracking)
export function trackDependencies<T>(fn: () => T): { result: T; dependencies: Set<Observable<any>> };
```

### Behavior Specification

1. **Lazy evaluation** — Computation only runs on first `get()` or after invalidation
2. **Automatic dependency tracking** — During computation, all `Observable.get()` calls are recorded
3. **Auto-invalidation** — When ANY dependency changes, computed is marked stale
4. **Memoization** — Returns cached value if dependencies haven't changed
5. **Glitch-free** — Never exposes inconsistent intermediate states
6. **Diamond dependency handling** — See critical test below

### ⚠️ CRITICAL: Diamond Dependency

```
     A (Observable)
    / \
   B   C  (both Computed, depend on A)
    \ /
     D    (Computed, depends on B and C)

When A changes:
- B and C both need to recompute
- D depends on BOTH B and C
- D must recompute exactly ONCE, not twice
- D must see consistent values (both B and C updated)
```

### ⚠️ CRITICAL: Circular Dependency Detection

```typescript
// This MUST throw an error, NOT infinite loop:
const a = new Computed(() => b.get() + 1);
const b = new Computed(() => a.get() + 1);
a.get(); // Should throw CircularDependencyError
```

### Tests: `tests/computed.test.ts` (20 tests)

```typescript
import { Observable } from '../src/Observable';
import { Computed, CircularDependencyError } from '../src/Computed';

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
    const b = new Computed(() => a.get() * 2);  // 4
    const c = new Computed(() => b.get() + 1);  // 5
    
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
});
```

---

## Feature 3: Store (State Container)

### File: `src/Store.ts`

A central store that holds state and manages updates.

### Type Definitions

```typescript
export interface StoreConfig<T extends object> {
  initialState: T;
  enableHistory?: boolean;
  historyLimit?: number;
}

export interface IStore<T extends object> {
  getState(): Readonly<T>;
  setState(partial: Partial<T>): void;
  subscribe(listener: (state: T, prevState: T) => void): Unsubscribe;
  transaction<R>(fn: () => R): R;
}
```

### Implementation Requirements

```typescript
export class Store<T extends object> implements IStore<T> {
  constructor(config: StoreConfig<T>);
  
  getState(): Readonly<T>;
  setState(partial: Partial<T>): void;
  setState(updater: (state: T) => Partial<T>): void;
  
  subscribe(listener: (state: T, prevState: T) => void): Unsubscribe;
  
  // Transactions
  transaction<R>(fn: () => R): R;
  
  // History (if enabled)
  undo(): boolean;
  redo(): boolean;
  canUndo(): boolean;
  canRedo(): boolean;
  
  // Utilities
  reset(): void;
  destroy(): void;
}
```

### Behavior Specification

1. **Immutable state** — `getState()` returns frozen object
2. **Partial updates** — `setState({ key: value })` merges, doesn't replace
3. **Functional updates** — `setState(state => ({ count: state.count + 1 }))`
4. **Batched notifications** — Multiple setState in sequence = one notification
5. **Transaction support** — Multiple setState = one notification at end
6. **Transaction rollback** — If error thrown, revert ALL changes
7. **History** — Undo/redo when enabled

### Tests: `tests/store.test.ts` (15 tests)

```typescript
import { Store } from '../src/Store';

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
});
```

---

## Feature 4: Integration Test — Task Manager

### File: `tests/integration/task-manager.test.ts`

A complete integration test proving all systems work together.

### Test Scenario

Build a reactive task manager with:
- Observable task list
- Computed: total count, completed count, pending count, completion percentage
- Store with history
- Transactions for bulk operations

```typescript
import { Observable } from '../../src/Observable';
import { Computed } from '../../src/Computed';
import { Store } from '../../src/Store';

interface Task {
  id: string;
  title: string;
  completed: boolean;
}

interface TaskManagerState {
  tasks: Task[];
  filter: 'all' | 'completed' | 'pending';
}

describe('Integration: Task Manager', () => {
  let store: Store<TaskManagerState>;
  
  beforeEach(() => {
    store = new Store({
      initialState: {
        tasks: [],
        filter: 'all'
      },
      enableHistory: true,
      historyLimit: 50
    });
  });

  // Helper functions
  const addTask = (title: string) => {
    const tasks = store.getState().tasks;
    store.setState({
      tasks: [...tasks, { id: crypto.randomUUID(), title, completed: false }]
    });
  };

  const toggleTask = (id: string) => {
    const tasks = store.getState().tasks;
    store.setState({
      tasks: tasks.map(t => t.id === id ? { ...t, completed: !t.completed } : t)
    });
  };

  const removeTask = (id: string) => {
    const tasks = store.getState().tasks;
    store.setState({
      tasks: tasks.filter(t => t.id !== id)
    });
  };

  // Tests
  test('add task increases count', () => {
    addTask('Task 1');
    addTask('Task 2');
    expect(store.getState().tasks.length).toBe(2);
  });

  test('toggle task updates completed status', () => {
    addTask('Task 1');
    const taskId = store.getState().tasks[0].id;
    toggleTask(taskId);
    expect(store.getState().tasks[0].completed).toBe(true);
  });

  test('computed values update reactively', () => {
    const tasks = new Observable<Task[]>([]);
    
    const totalCount = new Computed(() => tasks.get().length);
    const completedCount = new Computed(() => 
      tasks.get().filter(t => t.completed).length
    );
    const pendingCount = new Computed(() => 
      totalCount.get() - completedCount.get()
    );
    const completionPercent = new Computed(() => {
      const total = totalCount.get();
      return total === 0 ? 0 : Math.round((completedCount.get() / total) * 100);
    });

    expect(totalCount.get()).toBe(0);
    expect(completionPercent.get()).toBe(0);

    tasks.set([
      { id: '1', title: 'Task 1', completed: false },
      { id: '2', title: 'Task 2', completed: false },
    ]);

    expect(totalCount.get()).toBe(2);
    expect(completedCount.get()).toBe(0);
    expect(pendingCount.get()).toBe(2);
    expect(completionPercent.get()).toBe(0);

    tasks.set([
      { id: '1', title: 'Task 1', completed: true },
      { id: '2', title: 'Task 2', completed: false },
    ]);

    expect(completedCount.get()).toBe(1);
    expect(pendingCount.get()).toBe(1);
    expect(completionPercent.get()).toBe(50);
  });

  test('undo/redo task operations', () => {
    addTask('Task 1');
    const taskId = store.getState().tasks[0].id;
    
    toggleTask(taskId);
    expect(store.getState().tasks[0].completed).toBe(true);
    
    store.undo();
    expect(store.getState().tasks[0].completed).toBe(false);
    
    store.redo();
    expect(store.getState().tasks[0].completed).toBe(true);
  });

  test('transaction: bulk add with rollback on error', () => {
    addTask('Existing Task');
    
    expect(() => {
      store.transaction(() => {
        addTask('Bulk 1');
        addTask('Bulk 2');
        addTask('Bulk 3');
        throw new Error('Oops!');
      });
    }).toThrow('Oops!');
    
    // Only original task should remain
    expect(store.getState().tasks.length).toBe(1);
    expect(store.getState().tasks[0].title).toBe('Existing Task');
  });

  test('transaction: bulk toggle succeeds', () => {
    addTask('Task 1');
    addTask('Task 2');
    addTask('Task 3');
    
    const listener = vi.fn();
    store.subscribe(listener);
    
    store.transaction(() => {
      const tasks = store.getState().tasks;
      tasks.forEach(t => toggleTask(t.id));
    });
    
    // All tasks completed
    expect(store.getState().tasks.every(t => t.completed)).toBe(true);
    
    // Only one notification
    expect(listener).toHaveBeenCalledTimes(1);
  });

  // ═══════════════════════════════════════════════════════════
  // CRITICAL: Full workflow with computed + history + transactions
  // ═══════════════════════════════════════════════════════════
  test('CRITICAL: full workflow integration', () => {
    const tasks = new Observable<Task[]>([]);
    const completedCount = new Computed(() => 
      tasks.get().filter(t => t.completed).length
    );
    const pendingCount = new Computed(() => 
      tasks.get().filter(t => !t.completed).length
    );
    
    // Add tasks
    tasks.set([
      { id: '1', title: 'Task 1', completed: false },
      { id: '2', title: 'Task 2', completed: false },
      { id: '3', title: 'Task 3', completed: false },
    ]);
    
    expect(pendingCount.get()).toBe(3);
    expect(completedCount.get()).toBe(0);
    
    // Complete task 1
    tasks.set(tasks.get().map(t => 
      t.id === '1' ? { ...t, completed: true } : t
    ));
    
    expect(pendingCount.get()).toBe(2);
    expect(completedCount.get()).toBe(1);
    
    // Complete tasks 2 and 3
    tasks.set(tasks.get().map(t => 
      t.id === '2' || t.id === '3' ? { ...t, completed: true } : t
    ));
    
    expect(pendingCount.get()).toBe(0);
    expect(completedCount.get()).toBe(3);
  });

  test('computed diamond with tasks', () => {
    const tasks = new Observable<Task[]>([
      { id: '1', title: 'A', completed: false },
      { id: '2', title: 'B', completed: true },
    ]);
    
    const completed = new Computed(() => tasks.get().filter(t => t.completed));
    const pending = new Computed(() => tasks.get().filter(t => !t.completed));
    
    let summaryComputeCount = 0;
    const summary = new Computed(() => {
      summaryComputeCount++;
      return {
        completed: completed.get().length,
        pending: pending.get().length,
        total: completed.get().length + pending.get().length
      };
    });
    
    // Initial
    expect(summary.get()).toEqual({ completed: 1, pending: 1, total: 2 });
    summaryComputeCount = 0;
    
    // Change tasks - summary should recompute only ONCE
    tasks.set([
      { id: '1', title: 'A', completed: true },
      { id: '2', title: 'B', completed: true },
    ]);
    
    summary.get();
    expect(summaryComputeCount).toBe(1);
  });

  test('handles rapid updates correctly', () => {
    for (let i = 0; i < 100; i++) {
      addTask(`Task ${i}`);
    }
    
    expect(store.getState().tasks.length).toBe(100);
    
    // Toggle all
    store.transaction(() => {
      store.getState().tasks.forEach(t => toggleTask(t.id));
    });
    
    expect(store.getState().tasks.every(t => t.completed)).toBe(true);
  });
});
```

---

## Feature 5: Error Classes

### File: `src/errors.ts`

Custom error classes for clear error handling.

```typescript
export class ReactiveStoreError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ReactiveStoreError';
  }
}

export class CircularDependencyError extends ReactiveStoreError {
  constructor(public readonly chain: string[] = []) {
    super(`Circular dependency detected${chain.length ? `: ${chain.join(' → ')}` : ''}`);
    this.name = 'CircularDependencyError';
  }
}

export class TransactionError extends ReactiveStoreError {
  constructor(message: string, public readonly cause?: Error) {
    super(message);
    this.name = 'TransactionError';
  }
}
```

### Tests: `tests/errors.test.ts` (5 tests)

```typescript
import { 
  ReactiveStoreError, 
  CircularDependencyError, 
  TransactionError 
} from '../src/errors';

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
```

---

## Feature 6: Library Exports

### File: `src/index.ts`

```typescript
// Core classes
export { Observable } from './Observable';
export type { Listener, Unsubscribe, IObservable } from './Observable';

export { Computed } from './Computed';
export type { IComputed } from './Computed';

export { Store } from './Store';
export type { StoreConfig, IStore } from './Store';

// Errors
export { 
  ReactiveStoreError,
  CircularDependencyError,
  TransactionError
} from './errors';
```

---

## Package Configuration

### `package.json`

```json
{
  "name": "reactive-store-lite",
  "version": "1.0.0",
  "description": "A lightweight reactive state management library",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "type": "module",
  "scripts": {
    "build": "tsc",
    "test": "vitest run",
    "test:watch": "vitest",
    "typecheck": "tsc --noEmit"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "vitest": "^1.0.0",
    "@types/node": "^20.0.0"
  },
  "engines": {
    "node": ">=20.0.0"
  }
}
```

### `vitest.config.ts`

```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['tests/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
  },
});
```

---

## Summary

### Files Required

| File | Purpose |
|------|---------|
| `src/Observable.ts` | Reactive value container |
| `src/Computed.ts` | Derived values with auto-tracking |
| `src/Store.ts` | State container with history |
| `src/errors.ts` | Custom error classes |
| `src/index.ts` | Public exports |
| `tests/observable.test.ts` | 15 tests |
| `tests/computed.test.ts` | 20 tests |
| `tests/store.test.ts` | 15 tests |
| `tests/errors.test.ts` | 5 tests |
| `tests/integration/task-manager.test.ts` | 10 tests |
| `package.json` | Package config |
| `tsconfig.json` | TypeScript config |
| `vitest.config.ts` | Test config |

### Test Count

| Suite | Tests |
|-------|-------|
| Observable | 15 |
| Computed | 20 |
| Store | 15 |
| Errors | 5 |
| Integration | 10 |
| **TOTAL** | **65** |

### Estimated Time

| Phase | Time |
|-------|------|
| Planning | 2-3 min |
| Implementation | 20-30 min |
| Testing | 10-15 min |
| Debugging | 10-15 min |
| **TOTAL** | **45-60 min** |

---

## Killer Tests (The Deciders)

These 5 tests will separate production-grade builders from pretenders:

| Test | What It Catches | Points |
|------|-----------------|--------|
| **Diamond dependency** | Computed recomputes ONCE | 15 |
| **Circular dependency detection** | Throws error, not infinite loop | 10 |
| **Transaction rollback** | ALL state reverts | 15 |
| **Redo stack clearing** | New action clears redo | 10 |
| **Subscription safety** | No crash on unsubscribe during notify | 5 |

**Total killer test points: 55/100**

A builder that fails these is NOT production-grade. Period.

---

## Grading Criteria

### Production-Grade Threshold: 80/100

| Score | Grade | Verdict |
|-------|-------|---------|
| 90-100 | **A** | Elite / GOAT candidate |
| 80-89 | **B** | Production-grade |
| 70-79 | **C** | Capable, needs oversight |
| 60-69 | **D** | Limited, significant gaps |
| <60 | **F** | Not production-ready |

### GOAT Status Requirements

To earn GOAT status, a builder MUST:
1. Score 90+/100
2. Pass ALL killer tests
3. Zero TypeScript errors
4. Zero `any` types in source
5. All tests actually test something (no empty tests)

---

## What This Test Reveals

| If Builder... | It Means... |
|---------------|-------------|
| Fails diamond dependency | Can't handle complex reactive systems |
| Fails circular detection | Code will hang in production |
| Fails transaction rollback | Data corruption risk |
| Fails redo clearing | History system is broken |
| Has TypeScript errors | Basic quality control missing |
| Has `any` types | Type safety is fake |
| Has empty tests | Test count is padded |

---

*End of Specification*
