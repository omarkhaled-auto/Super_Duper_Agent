import { describe, test, expect, vi, beforeEach } from 'vitest';
import { Observable } from '../../src/Observable.js';
import { Computed } from '../../src/Computed.js';
import { Store } from '../../src/Store.js';

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
    const taskId = store.getState().tasks[0]!.id;
    toggleTask(taskId);
    expect(store.getState().tasks[0]!.completed).toBe(true);
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
    const taskId = store.getState().tasks[0]!.id;

    toggleTask(taskId);
    expect(store.getState().tasks[0]!.completed).toBe(true);

    store.undo();
    expect(store.getState().tasks[0]!.completed).toBe(false);

    store.redo();
    expect(store.getState().tasks[0]!.completed).toBe(true);
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
    expect(store.getState().tasks[0]!.title).toBe('Existing Task');
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

  test('remove task decreases count and preserves others', () => {
    addTask('Task 1');
    addTask('Task 2');
    addTask('Task 3');
    const taskId = store.getState().tasks[1]!.id;

    removeTask(taskId);

    expect(store.getState().tasks.length).toBe(2);
    expect(store.getState().tasks.every(t => t.id !== taskId)).toBe(true);
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
