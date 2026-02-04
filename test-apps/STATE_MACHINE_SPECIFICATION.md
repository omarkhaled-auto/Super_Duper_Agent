# FlowForge: Workflow State Machine Engine

## Project Overview

Build a TypeScript library called **FlowForge** that provides a robust, type-safe workflow state machine engine. This library allows developers to define complex workflows with states, transitions, guards, actions, timers, parallel states, and history tracking.

**Target Use Case:** Order fulfillment, approval workflows, document lifecycles, and any business process requiring strict state management.

**Core Principle:** The state machine must be **deterministic and correct**. Invalid transitions must be impossible. Every state change must be auditable.

---

## Technical Requirements

### Stack
- **Language:** TypeScript 5.x (strict mode)
- **Runtime:** Node.js 20+ (no browser requirements)
- **Testing:** Vitest
- **Build:** tsup or esbuild
- **No external state machine libraries** (build from scratch)

### Package Structure
```
flowforge/
├── src/
│   ├── index.ts                 # Public API exports
│   ├── types.ts                 # All TypeScript types/interfaces
│   ├── StateMachine.ts          # Core state machine class
│   ├── StateNode.ts             # State node representation
│   ├── Transition.ts            # Transition logic
│   ├── Guard.ts                 # Guard condition evaluation
│   ├── Action.ts                # Action execution
│   ├── EventQueue.ts            # Event queuing system
│   ├── Timer.ts                 # Timeout/timer management
│   ├── History.ts               # History state tracking
│   ├── ParallelState.ts         # Parallel state management
│   ├── Interpreter.ts           # Runtime interpreter
│   └── errors.ts                # Custom error types
├── tests/
│   ├── basic-transitions.test.ts
│   ├── guards.test.ts
│   ├── actions.test.ts
│   ├── event-queue.test.ts
│   ├── timers.test.ts
│   ├── parallel-states.test.ts
│   ├── history-states.test.ts
│   ├── order-workflow.test.ts   # Full integration test
│   └── edge-cases.test.ts
├── examples/
│   └── order-fulfillment.ts     # Complete example workflow
├── package.json
├── tsconfig.json
├── vitest.config.ts
└── README.md
```

---

## Feature Specifications

### Feature 1: State Machine Definition (Core)

Users define state machines using a declarative configuration object.

```typescript
import { createMachine } from 'flowforge';

const orderMachine = createMachine({
  id: 'order',
  initial: 'draft',
  context: {
    orderId: '',
    items: [],
    total: 0,
    customerId: '',
    approvals: {
      manager: false,
      vp: false
    }
  },
  states: {
    draft: {
      on: {
        SUBMIT: {
          target: 'submitted',
          guard: 'hasItems',
          actions: ['logSubmission', 'notifyWarehouse']
        }
      }
    },
    submitted: {
      on: {
        APPROVE: {
          target: 'approved',
          guard: 'canApprove'
        },
        REJECT: {
          target: 'rejected',
          actions: ['notifyCustomer']
        }
      }
    },
    approved: {
      on: {
        START_PROCESSING: 'processing'
      }
    },
    processing: {
      on: {
        SHIP: 'shipped'
      }
    },
    shipped: {
      after: {
        // Auto-transition to 'lost' after 7 days (604800000ms)
        604800000: {
          target: 'lost',
          guard: 'notDelivered'
        }
      },
      on: {
        DELIVER: 'delivered',
        REPORT_LOST: 'lost'
      }
    },
    delivered: {
      type: 'final'
    },
    rejected: {
      on: {
        REVISE: 'draft'
      }
    },
    lost: {
      type: 'final'
    }
  }
});
```

**Requirements:**
- Type-safe configuration with full IntelliSense support
- Validation of configuration at creation time (catch invalid references)
- Immutable state - machine definition cannot change after creation
- `context` holds mutable workflow data that guards/actions can access

---

### Feature 2: Transitions

Transitions move the machine from one state to another.

**Requirements:**

1. **Basic Transitions**
   ```typescript
   // String shorthand
   on: { NEXT: 'nextState' }
   
   // Object form with options
   on: { 
     NEXT: { 
       target: 'nextState',
       guard: 'someGuard',
       actions: ['action1', 'action2']
     }
   }
   ```

2. **Self-Transitions**
   ```typescript
   // Re-enter same state (triggers onExit and onEntry)
   on: { RETRY: 'sameState' }
   ```

3. **Conditional Transitions (multiple targets)**
   ```typescript
   on: {
     SUBMIT: [
       { target: 'fastTrack', guard: 'isPremiumCustomer' },
       { target: 'standardQueue', guard: 'isStandardCustomer' },
       { target: 'manualReview' } // Default fallback (no guard)
     ]
   }
   ```

4. **Forbidden Transitions**
   - Attempting an undefined transition should throw `InvalidTransitionError`
   - Attempting transition when guard fails should throw `GuardFailedError`
   - Transitions from `final` states should throw `FinalStateError`

---

### Feature 3: Guards

Guards are conditions that must be true for a transition to occur.

**Requirements:**

1. **Guard Definition**
   ```typescript
   const machine = createMachine({
     // ... states config
   }, {
     guards: {
       hasItems: (context) => context.items.length > 0,
       
       canApprove: (context) => {
         if (context.total < 1000) return true;
         if (context.total < 10000 && context.approvals.manager) return true;
         if (context.total >= 10000 && context.approvals.vp) return true;
         return false;
       },
       
       isPremiumCustomer: (context, event) => {
         return context.customerTier === 'premium';
       }
     }
   });
   ```

2. **Guard Parameters**
   - `context`: Current machine context
   - `event`: The event that triggered the transition (including payload)

3. **Compound Guards**
   ```typescript
   guard: { and: ['hasItems', 'hasValidAddress', 'hasPaymentMethod'] }
   guard: { or: ['isPremiumCustomer', 'hasExpressUpgrade'] }
   guard: { not: 'isBanned' }
   ```

4. **Guard Evaluation Rules**
   - Guards must be pure functions (no side effects)
   - Guards must be synchronous
   - If guard throws, treat as `false` and log error
   - Guards evaluated in order for conditional transitions; first `true` wins

---

### Feature 4: Actions

Actions are side effects executed during transitions.

**Requirements:**

1. **Action Types**
   ```typescript
   const machine = createMachine({
     states: {
       submitted: {
         entry: ['logEntry', 'startTimer'],      // Run when entering state
         exit: ['logExit', 'cleanup'],           // Run when leaving state
         on: {
           APPROVE: {
             target: 'approved',
             actions: ['logApproval', 'notifyStakeholders']  // Transition actions
           }
         }
       }
     }
   }, {
     actions: {
       logEntry: (context, event) => {
         console.log(`Entered state with event: ${event.type}`);
       },
       
       notifyStakeholders: (context, event) => {
         // Send notifications
       },
       
       updateContext: assign({
         lastUpdated: () => Date.now(),
         processedBy: (context, event) => event.userId
       })
     }
   });
   ```

2. **Action Execution Order**
   - Exit actions of source state (in order defined)
   - Transition actions (in order defined)
   - Entry actions of target state (in order defined)

3. **Context Updates with `assign`**
   ```typescript
   import { assign } from 'flowforge';
   
   actions: {
     incrementRetries: assign({
       retryCount: (context) => context.retryCount + 1
     }),
     
     setApproval: assign((context, event) => ({
       approvals: {
         ...context.approvals,
         [event.approverRole]: true
       }
     }))
   }
   ```

4. **Action Rules**
   - Actions may be async (return Promise)
   - If action throws, transition still completes but error is logged
   - Actions should not determine transition outcome (that's guards' job)

---

### Feature 5: Event Queue

Events can be queued and processed in order.

**Requirements:**

1. **Basic Event Sending**
   ```typescript
   const interpreter = interpret(machine);
   interpreter.start();
   
   interpreter.send('SUBMIT');
   interpreter.send({ type: 'APPROVE', userId: 'user123', reason: 'Looks good' });
   ```

2. **Event Queuing**
   ```typescript
   // Events sent during action execution are queued
   actions: {
     triggerFollowUp: (context, event, { send }) => {
       send('FOLLOW_UP'); // Queued, processed after current transition completes
     }
   }
   ```

3. **Event Priority**
   ```typescript
   interpreter.send({ type: 'URGENT_CANCEL', priority: 'high' });
   interpreter.send({ type: 'STATUS_UPDATE', priority: 'low' });
   
   // High priority events processed before normal/low
   ```

4. **Queue Inspection**
   ```typescript
   interpreter.getQueuedEvents(); // Returns array of pending events
   interpreter.clearQueue();       // Clear all pending events
   ```

5. **Event Processing Rules**
   - Events processed synchronously in order (respecting priority)
   - If machine is in final state, events are ignored (with warning)
   - Unknown event types are ignored (with warning)

---

### Feature 6: Timers and Delayed Transitions

States can have automatic transitions after a delay.

**Requirements:**

1. **Delayed Transitions**
   ```typescript
   states: {
     pending: {
       after: {
         30000: 'timeout',      // After 30 seconds, go to 'timeout' state
         
         60000: {               // After 60 seconds with guard
           target: 'escalated',
           guard: 'notResolved',
           actions: ['notifyManager']
         }
       }
     }
   }
   ```

2. **Timer Lifecycle**
   - Timer starts when entering state
   - Timer cancelled when leaving state (for any reason)
   - Timer reset if re-entering same state
   - Multiple timers per state allowed (all active simultaneously)

3. **Dynamic Delays**
   ```typescript
   after: {
     // Delay based on context
     timeout: {
       delay: (context) => context.isPremium ? 60000 : 30000,
       target: 'expired'
     }
   }
   ```

4. **Timer Control**
   ```typescript
   interpreter.getActiveTimers();  // Returns array of { id, remaining, target }
   interpreter.cancelTimer(id);    // Manually cancel specific timer
   ```

5. **Timer Accuracy**
   - Timers should fire within 100ms of specified delay
   - Use `setTimeout` internally but track remaining time for pause/resume

---

### Feature 7: Parallel States

Multiple state "regions" can be active simultaneously.

**Requirements:**

1. **Parallel State Definition**
   ```typescript
   states: {
     processing: {
       type: 'parallel',
       states: {
         payment: {
           initial: 'pending',
           states: {
             pending: { on: { AUTHORIZE: 'authorized' } },
             authorized: { on: { CAPTURE: 'captured' } },
             captured: { type: 'final' }
           }
         },
         shipping: {
           initial: 'picking',
           states: {
             picking: { on: { PACK: 'packing' } },
             packing: { on: { SHIP: 'shipped' } },
             shipped: { on: { DELIVER: 'delivered' } },
             delivered: { type: 'final' }
           }
         },
         notification: {
           initial: 'queued',
           states: {
             queued: { on: { SEND: 'sent' } },
             sent: { on: { CONFIRM: 'confirmed' } },
             confirmed: { type: 'final' }
           }
         }
       },
       onDone: 'completed'  // Transition when ALL parallel states are final
     },
     completed: {
       type: 'final'
     }
   }
   ```

2. **Parallel State Behavior**
   - Each region has independent state
   - Events broadcast to all regions (each handles if relevant)
   - `onDone` triggers only when ALL regions reach final state
   - Context is shared across all regions

3. **Parallel State Access**
   ```typescript
   interpreter.getState();
   // Returns: { value: { processing: { payment: 'authorized', shipping: 'picking', notification: 'sent' } } }
   
   interpreter.matches('processing.payment.authorized'); // true
   interpreter.matches('processing.shipping.delivered'); // false
   ```

---

### Feature 8: Nested/Hierarchical States

States can contain child states.

**Requirements:**

1. **Nested State Definition**
   ```typescript
   states: {
     editing: {
       initial: 'details',
       states: {
         details: {
           on: { NEXT: 'shipping' }
         },
         shipping: {
           on: { NEXT: 'payment', BACK: 'details' }
         },
         payment: {
           on: { NEXT: 'review', BACK: 'shipping' }
         },
         review: {
           on: { SUBMIT: '#submitted', BACK: 'payment' }  // # = absolute reference
         }
       },
       on: {
         CANCEL: 'cancelled'  // Can cancel from ANY child state
       }
     },
     submitted: { /* ... */ },
     cancelled: { type: 'final' }
   }
   ```

2. **Event Bubbling**
   - Events handled by deepest matching state first
   - If not handled, bubble up to parent
   - Parent handlers can catch events from any child

3. **State Resolution**
   ```typescript
   interpreter.matches('editing');           // true if in any editing.* state
   interpreter.matches('editing.payment');   // true only if in payment specifically
   ```

---

### Feature 9: History States

Remember and restore previous child state.

**Requirements:**

1. **Shallow History**
   ```typescript
   states: {
     editing: {
       initial: 'details',
       states: {
         details: { /* ... */ },
         shipping: { /* ... */ },
         payment: { /* ... */ },
         hist: { type: 'history' }  // Shallow history pseudo-state
       }
     },
     paused: {
       on: {
         RESUME: 'editing.hist'  // Returns to last active child of 'editing'
       }
     }
   }
   ```

2. **Deep History**
   ```typescript
   states: {
     wizard: {
       initial: 'step1',
       states: {
         step1: {
           initial: 'substep1a',
           states: {
             substep1a: { /* ... */ },
             substep1b: { /* ... */ }
           }
         },
         step2: { /* ... */ },
         deepHist: { type: 'history', history: 'deep' }
       }
     },
     interrupted: {
       on: {
         RESUME: 'wizard.deepHist'  // Returns to exact nested state, e.g., step1.substep1b
       }
     }
   }
   ```

3. **History Default**
   ```typescript
   hist: { 
     type: 'history', 
     target: 'details'  // Default if no history exists yet
   }
   ```

---

### Feature 10: Interpreter & Runtime

The interpreter runs the state machine.

**Requirements:**

1. **Interpreter Lifecycle**
   ```typescript
   import { interpret } from 'flowforge';
   
   const interpreter = interpret(machine)
     .onTransition((state) => {
       console.log('New state:', state.value);
       console.log('Context:', state.context);
     })
     .onChange((context) => {
       console.log('Context changed:', context);
     })
     .onEvent((event) => {
       console.log('Event received:', event);
     })
     .onError((error) => {
       console.error('Error:', error);
     });
   
   interpreter.start();   // Enter initial state
   interpreter.send('SUBMIT');
   interpreter.stop();    // Cleanup, cancel timers
   ```

2. **State Inspection**
   ```typescript
   const state = interpreter.getState();
   
   state.value;           // Current state value ('submitted' or { parallel: { a: 'x', b: 'y' } })
   state.context;         // Current context
   state.matches('submitted');  // Boolean check
   state.can('APPROVE');  // Check if transition is possible (guards evaluated)
   state.nextEvents;      // Array of valid event types in current state
   state.history;         // Array of previous states
   ```

3. **Persistence & Rehydration**
   ```typescript
   // Save state
   const snapshot = interpreter.getSnapshot();
   localStorage.setItem('workflow', JSON.stringify(snapshot));
   
   // Restore state
   const saved = JSON.parse(localStorage.getItem('workflow'));
   const interpreter = interpret(machine).start(saved);
   ```

---

### Feature 11: Type Safety

Full TypeScript type inference and safety.

**Requirements:**

1. **Event Type Safety**
   ```typescript
   type OrderEvents = 
     | { type: 'SUBMIT' }
     | { type: 'APPROVE'; userId: string; reason?: string }
     | { type: 'REJECT'; userId: string; reason: string }
     | { type: 'SHIP'; trackingNumber: string };
   
   const machine = createMachine<OrderContext, OrderEvents>({ /* ... */ });
   
   interpreter.send({ type: 'APPROVE', userId: 'u1' });  // ✅ Valid
   interpreter.send({ type: 'APPROVE' });                // ❌ Error: missing userId
   interpreter.send({ type: 'UNKNOWN' });                // ❌ Error: invalid type
   ```

2. **Context Type Safety**
   ```typescript
   interface OrderContext {
     orderId: string;
     items: Array<{ sku: string; quantity: number }>;
     total: number;
   }
   
   guards: {
     hasItems: (context: OrderContext) => context.items.length > 0,
     // TypeScript knows context.items is Array<{ sku, quantity }>
   }
   ```

3. **State Type Safety**
   ```typescript
   type OrderState = 'draft' | 'submitted' | 'approved' | 'rejected';
   
   interpreter.matches('draft');     // ✅ Valid
   interpreter.matches('unknown');   // ❌ Error: invalid state
   ```

---

### Feature 12: Audit Trail

Complete history of all state changes.

**Requirements:**

1. **Transition Log**
   ```typescript
   interpreter.getHistory();
   // Returns:
   [
     {
       timestamp: 1704067200000,
       from: 'draft',
       to: 'submitted',
       event: { type: 'SUBMIT' },
       context: { /* snapshot */ },
       duration: 5  // ms to complete transition
     },
     // ...
   ]
   ```

2. **Subscribing to History**
   ```typescript
   interpreter.onTransition((state, event, meta) => {
     auditLog.write({
       workflowId: state.context.orderId,
       transition: `${meta.from} -> ${state.value}`,
       triggeredBy: event,
       timestamp: meta.timestamp
     });
   });
   ```

---

## Acceptance Tests

The following tests MUST pass. These are the exact scenarios that validate correctness.

### Test Suite 1: Basic Transitions

```typescript
describe('Basic Transitions', () => {
  const machine = createMachine({
    id: 'light',
    initial: 'green',
    states: {
      green: { on: { TIMER: 'yellow' } },
      yellow: { on: { TIMER: 'red' } },
      red: { on: { TIMER: 'green' } }
    }
  });

  test('should start in initial state', () => {
    const interpreter = interpret(machine).start();
    expect(interpreter.getState().value).toBe('green');
  });

  test('should transition on valid event', () => {
    const interpreter = interpret(machine).start();
    interpreter.send('TIMER');
    expect(interpreter.getState().value).toBe('yellow');
  });

  test('should follow transition chain', () => {
    const interpreter = interpret(machine).start();
    interpreter.send('TIMER');
    interpreter.send('TIMER');
    interpreter.send('TIMER');
    expect(interpreter.getState().value).toBe('green'); // Full cycle
  });

  test('should ignore unknown events', () => {
    const interpreter = interpret(machine).start();
    interpreter.send('UNKNOWN');
    expect(interpreter.getState().value).toBe('green'); // Unchanged
  });
});
```

### Test Suite 2: Guards

```typescript
describe('Guards', () => {
  const machine = createMachine({
    id: 'order',
    initial: 'draft',
    context: { items: [], total: 0, managerApproval: false, vpApproval: false },
    states: {
      draft: {
        on: { SUBMIT: { target: 'submitted', guard: 'hasItems' } }
      },
      submitted: {
        on: { APPROVE: { target: 'approved', guard: 'canApprove' } }
      },
      approved: { type: 'final' }
    }
  }, {
    guards: {
      hasItems: (ctx) => ctx.items.length > 0,
      canApprove: (ctx) => {
        if (ctx.total < 1000) return true;
        if (ctx.total < 10000 && ctx.managerApproval) return true;
        if (ctx.total >= 10000 && ctx.vpApproval) return true;
        return false;
      }
    }
  });

  test('should block transition when guard fails', () => {
    const interpreter = interpret(machine).start();
    expect(() => interpreter.send('SUBMIT')).toThrow('GuardFailedError');
    expect(interpreter.getState().value).toBe('draft');
  });

  test('should allow transition when guard passes', () => {
    const interpreter = interpret(machine).start();
    interpreter.getState().context.items = [{ sku: 'ABC', qty: 1 }];
    interpreter.send('SUBMIT');
    expect(interpreter.getState().value).toBe('submitted');
  });

  test('should handle complex approval logic - small order', () => {
    const interpreter = interpret(machine).start();
    interpreter.getState().context.items = [{ sku: 'ABC', qty: 1 }];
    interpreter.getState().context.total = 500;
    interpreter.send('SUBMIT');
    interpreter.send('APPROVE');
    expect(interpreter.getState().value).toBe('approved');
  });

  test('should handle complex approval logic - medium order needs manager', () => {
    const interpreter = interpret(machine).start();
    interpreter.getState().context.items = [{ sku: 'ABC', qty: 1 }];
    interpreter.getState().context.total = 5000;
    interpreter.send('SUBMIT');
    
    // Without manager approval - should fail
    expect(() => interpreter.send('APPROVE')).toThrow('GuardFailedError');
    
    // With manager approval - should pass
    interpreter.getState().context.managerApproval = true;
    interpreter.send('APPROVE');
    expect(interpreter.getState().value).toBe('approved');
  });

  test('should handle complex approval logic - large order needs VP', () => {
    const interpreter = interpret(machine).start();
    interpreter.getState().context.items = [{ sku: 'ABC', qty: 1 }];
    interpreter.getState().context.total = 50000;
    interpreter.send('SUBMIT');
    
    // With only manager approval - should fail
    interpreter.getState().context.managerApproval = true;
    expect(() => interpreter.send('APPROVE')).toThrow('GuardFailedError');
    
    // With VP approval - should pass
    interpreter.getState().context.vpApproval = true;
    interpreter.send('APPROVE');
    expect(interpreter.getState().value).toBe('approved');
  });
});
```

### Test Suite 3: Actions

```typescript
describe('Actions', () => {
  test('should execute actions in correct order', () => {
    const executionOrder: string[] = [];
    
    const machine = createMachine({
      id: 'test',
      initial: 'a',
      states: {
        a: {
          exit: ['exitA'],
          on: { GO: { target: 'b', actions: ['transitionAction'] } }
        },
        b: {
          entry: ['entryB']
        }
      }
    }, {
      actions: {
        exitA: () => executionOrder.push('exitA'),
        transitionAction: () => executionOrder.push('transition'),
        entryB: () => executionOrder.push('entryB')
      }
    });

    const interpreter = interpret(machine).start();
    interpreter.send('GO');
    
    expect(executionOrder).toEqual(['exitA', 'transition', 'entryB']);
  });

  test('should update context with assign', () => {
    const machine = createMachine({
      id: 'counter',
      initial: 'active',
      context: { count: 0 },
      states: {
        active: {
          on: { 
            INCREMENT: { 
              target: 'active', 
              actions: ['increment'] 
            } 
          }
        }
      }
    }, {
      actions: {
        increment: assign({ count: (ctx) => ctx.count + 1 })
      }
    });

    const interpreter = interpret(machine).start();
    interpreter.send('INCREMENT');
    interpreter.send('INCREMENT');
    interpreter.send('INCREMENT');
    
    expect(interpreter.getState().context.count).toBe(3);
  });
});
```

### Test Suite 4: Event Queue

```typescript
describe('Event Queue', () => {
  test('should process events in order', () => {
    const events: string[] = [];
    
    const machine = createMachine({
      id: 'queue',
      initial: 'idle',
      states: {
        idle: { 
          entry: [() => events.push('idle')],
          on: { A: 'stateA' } 
        },
        stateA: { 
          entry: [() => events.push('A')],
          on: { B: 'stateB' } 
        },
        stateB: { 
          entry: [() => events.push('B')],
          on: { C: 'stateC' } 
        },
        stateC: { 
          entry: [() => events.push('C')]
        }
      }
    });

    const interpreter = interpret(machine).start();
    
    // Queue multiple events
    interpreter.send('A');
    interpreter.send('B');
    interpreter.send('C');
    
    expect(events).toEqual(['idle', 'A', 'B', 'C']);
    expect(interpreter.getState().value).toBe('stateC');
  });

  test('should handle events queued during transition', () => {
    const machine = createMachine({
      id: 'queue',
      initial: 'a',
      context: { triggered: false },
      states: {
        a: { 
          on: { GO: { target: 'b', actions: ['queueNext'] } }
        },
        b: { 
          on: { AUTO: 'c' }
        },
        c: { type: 'final' }
      }
    }, {
      actions: {
        queueNext: (ctx, event, { send }) => {
          send('AUTO'); // Queue during transition
        }
      }
    });

    const interpreter = interpret(machine).start();
    interpreter.send('GO');
    
    // Should have processed both GO and AUTO
    expect(interpreter.getState().value).toBe('c');
  });
});
```

### Test Suite 5: Timers

```typescript
describe('Timers', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  test('should transition after delay', () => {
    const machine = createMachine({
      id: 'timer',
      initial: 'pending',
      states: {
        pending: {
          after: {
            1000: 'timeout'
          }
        },
        timeout: { type: 'final' }
      }
    });

    const interpreter = interpret(machine).start();
    expect(interpreter.getState().value).toBe('pending');
    
    vi.advanceTimersByTime(999);
    expect(interpreter.getState().value).toBe('pending');
    
    vi.advanceTimersByTime(1);
    expect(interpreter.getState().value).toBe('timeout');
  });

  test('should cancel timer on state exit', () => {
    const machine = createMachine({
      id: 'timer',
      initial: 'pending',
      states: {
        pending: {
          after: { 1000: 'timeout' },
          on: { CANCEL: 'cancelled' }
        },
        timeout: { type: 'final' },
        cancelled: { type: 'final' }
      }
    });

    const interpreter = interpret(machine).start();
    
    vi.advanceTimersByTime(500);
    interpreter.send('CANCEL');
    
    vi.advanceTimersByTime(1000); // Timer should NOT fire
    expect(interpreter.getState().value).toBe('cancelled');
  });

  test('should reset timer on re-entry', () => {
    const machine = createMachine({
      id: 'timer',
      initial: 'active',
      context: { attempts: 0 },
      states: {
        active: {
          after: { 1000: 'timeout' },
          on: { RETRY: { target: 'active', actions: ['incrementAttempts'] } }
        },
        timeout: { type: 'final' }
      }
    }, {
      actions: {
        incrementAttempts: assign({ attempts: (ctx) => ctx.attempts + 1 })
      }
    });

    const interpreter = interpret(machine).start();
    
    vi.advanceTimersByTime(800);
    interpreter.send('RETRY'); // Timer resets
    
    vi.advanceTimersByTime(800);
    expect(interpreter.getState().value).toBe('active'); // Still active!
    
    vi.advanceTimersByTime(200);
    expect(interpreter.getState().value).toBe('timeout'); // Now times out
    expect(interpreter.getState().context.attempts).toBe(1);
  });
});
```

### Test Suite 6: Parallel States

```typescript
describe('Parallel States', () => {
  const machine = createMachine({
    id: 'order',
    initial: 'processing',
    states: {
      processing: {
        type: 'parallel',
        states: {
          payment: {
            initial: 'pending',
            states: {
              pending: { on: { PAY: 'paid' } },
              paid: { type: 'final' }
            }
          },
          shipping: {
            initial: 'preparing',
            states: {
              preparing: { on: { SHIP: 'shipped' } },
              shipped: { on: { DELIVER: 'delivered' } },
              delivered: { type: 'final' }
            }
          }
        },
        onDone: 'completed'
      },
      completed: { type: 'final' }
    }
  });

  test('should have multiple active states', () => {
    const interpreter = interpret(machine).start();
    const state = interpreter.getState();
    
    expect(state.value).toEqual({
      processing: {
        payment: 'pending',
        shipping: 'preparing'
      }
    });
  });

  test('should handle events in parallel regions independently', () => {
    const interpreter = interpret(machine).start();
    
    interpreter.send('PAY');
    expect(interpreter.getState().value).toEqual({
      processing: {
        payment: 'paid',
        shipping: 'preparing'
      }
    });
    
    interpreter.send('SHIP');
    expect(interpreter.getState().value).toEqual({
      processing: {
        payment: 'paid',
        shipping: 'shipped'
      }
    });
  });

  test('should complete only when all regions are final', () => {
    const interpreter = interpret(machine).start();
    
    interpreter.send('PAY');
    expect(interpreter.getState().matches('processing')).toBe(true);
    
    interpreter.send('SHIP');
    expect(interpreter.getState().matches('processing')).toBe(true);
    
    interpreter.send('DELIVER');
    expect(interpreter.getState().value).toBe('completed');
  });

  test('should match nested parallel states', () => {
    const interpreter = interpret(machine).start();
    
    expect(interpreter.getState().matches('processing')).toBe(true);
    expect(interpreter.getState().matches('processing.payment')).toBe(true);
    expect(interpreter.getState().matches('processing.payment.pending')).toBe(true);
    expect(interpreter.getState().matches('processing.shipping.shipped')).toBe(false);
  });
});
```

### Test Suite 7: History States

```typescript
describe('History States', () => {
  const machine = createMachine({
    id: 'editor',
    initial: 'editing',
    states: {
      editing: {
        initial: 'step1',
        states: {
          step1: { on: { NEXT: 'step2' } },
          step2: { on: { NEXT: 'step3', BACK: 'step1' } },
          step3: { on: { BACK: 'step2' } },
          hist: { type: 'history' }
        },
        on: {
          PAUSE: 'paused'
        }
      },
      paused: {
        on: {
          RESUME: 'editing.hist'
        }
      }
    }
  });

  test('should remember last child state', () => {
    const interpreter = interpret(machine).start();
    
    interpreter.send('NEXT'); // step1 -> step2
    interpreter.send('NEXT'); // step2 -> step3
    interpreter.send('PAUSE');
    
    expect(interpreter.getState().value).toBe('paused');
    
    interpreter.send('RESUME');
    expect(interpreter.getState().value).toEqual({ editing: 'step3' });
  });

  test('should use default if no history', () => {
    const machineWithDefault = createMachine({
      id: 'editor',
      initial: 'paused',
      states: {
        editing: {
          initial: 'step1',
          states: {
            step1: {},
            step2: {},
            hist: { type: 'history', target: 'step2' } // Default to step2
          }
        },
        paused: {
          on: { RESUME: 'editing.hist' }
        }
      }
    });

    const interpreter = interpret(machineWithDefault).start();
    interpreter.send('RESUME');
    
    // Should go to default (step2), not initial (step1)
    expect(interpreter.getState().value).toEqual({ editing: 'step2' });
  });
});
```

### Test Suite 8: Final State Behavior

```typescript
describe('Final States', () => {
  const machine = createMachine({
    id: 'workflow',
    initial: 'active',
    states: {
      active: {
        on: { COMPLETE: 'done', CANCEL: 'cancelled' }
      },
      done: { type: 'final' },
      cancelled: { type: 'final' }
    }
  });

  test('should not allow transitions from final state', () => {
    const interpreter = interpret(machine).start();
    interpreter.send('COMPLETE');
    
    expect(interpreter.getState().value).toBe('done');
    expect(() => interpreter.send('CANCEL')).toThrow('FinalStateError');
    expect(interpreter.getState().value).toBe('done'); // Unchanged
  });

  test('should report no valid events in final state', () => {
    const interpreter = interpret(machine).start();
    interpreter.send('COMPLETE');
    
    expect(interpreter.getState().nextEvents).toEqual([]);
  });
});
```

### Test Suite 9: Integration - Order Workflow

```typescript
describe('Order Workflow Integration', () => {
  // This is the full order workflow from the spec
  const orderMachine = createMachine({
    id: 'order',
    initial: 'draft',
    context: {
      orderId: 'ORD-001',
      items: [],
      total: 0,
      approvals: { manager: false, vp: false },
      shipmentTracking: null,
      history: []
    },
    states: {
      draft: {
        on: {
          ADD_ITEM: { actions: ['addItem'] },
          SUBMIT: { target: 'submitted', guard: 'hasItems', actions: ['recordSubmission'] }
        }
      },
      submitted: {
        on: {
          APPROVE: { target: 'approved', guard: 'canApprove', actions: ['recordApproval'] },
          REJECT: { target: 'rejected', actions: ['recordRejection'] },
          REQUEST_MANAGER_APPROVAL: { actions: ['setManagerApproval'] },
          REQUEST_VP_APPROVAL: { actions: ['setVPApproval'] }
        }
      },
      approved: {
        on: {
          START_PROCESSING: 'processing'
        }
      },
      processing: {
        on: {
          SHIP: { target: 'shipped', actions: ['setTracking'] }
        }
      },
      shipped: {
        after: {
          604800000: { target: 'lost', guard: 'notDelivered' } // 7 days
        },
        on: {
          DELIVER: 'delivered',
          REPORT_LOST: 'lost'
        }
      },
      delivered: { type: 'final' },
      rejected: {
        on: {
          REVISE: 'draft'
        }
      },
      lost: { type: 'final' }
    }
  }, {
    guards: {
      hasItems: (ctx) => ctx.items.length > 0,
      canApprove: (ctx) => {
        if (ctx.total < 1000) return true;
        if (ctx.total < 10000 && ctx.approvals.manager) return true;
        if (ctx.total >= 10000 && ctx.approvals.vp) return true;
        return false;
      },
      notDelivered: (ctx) => true // Simplified for test
    },
    actions: {
      addItem: assign({
        items: (ctx, event) => [...ctx.items, event.item],
        total: (ctx, event) => ctx.total + event.item.price * event.item.quantity
      }),
      recordSubmission: assign({
        history: (ctx) => [...ctx.history, { action: 'submitted', timestamp: Date.now() }]
      }),
      recordApproval: assign({
        history: (ctx, event) => [...ctx.history, { action: 'approved', by: event.approver, timestamp: Date.now() }]
      }),
      recordRejection: assign({
        history: (ctx, event) => [...ctx.history, { action: 'rejected', reason: event.reason, timestamp: Date.now() }]
      }),
      setManagerApproval: assign({
        approvals: (ctx) => ({ ...ctx.approvals, manager: true })
      }),
      setVPApproval: assign({
        approvals: (ctx) => ({ ...ctx.approvals, vp: true })
      }),
      setTracking: assign({
        shipmentTracking: (ctx, event) => event.trackingNumber
      })
    }
  });

  test('complete order flow - small order', () => {
    const interpreter = interpret(orderMachine).start();
    
    // Add item
    interpreter.send({ type: 'ADD_ITEM', item: { sku: 'WIDGET', price: 50, quantity: 2 } });
    expect(interpreter.getState().context.total).toBe(100);
    
    // Submit
    interpreter.send('SUBMIT');
    expect(interpreter.getState().value).toBe('submitted');
    
    // Approve (no manager needed for <$1000)
    interpreter.send({ type: 'APPROVE', approver: 'auto' });
    expect(interpreter.getState().value).toBe('approved');
    
    // Process and ship
    interpreter.send('START_PROCESSING');
    interpreter.send({ type: 'SHIP', trackingNumber: 'TRK123' });
    expect(interpreter.getState().value).toBe('shipped');
    expect(interpreter.getState().context.shipmentTracking).toBe('TRK123');
    
    // Deliver
    interpreter.send('DELIVER');
    expect(interpreter.getState().value).toBe('delivered');
  });

  test('complete order flow - large order requiring VP', () => {
    const interpreter = interpret(orderMachine).start();
    
    // Add expensive item
    interpreter.send({ type: 'ADD_ITEM', item: { sku: 'SERVER', price: 15000, quantity: 1 } });
    interpreter.send('SUBMIT');
    
    // Try approve without VP - should fail
    expect(() => interpreter.send({ type: 'APPROVE', approver: 'manager' })).toThrow();
    
    // Get manager approval - still not enough
    interpreter.send('REQUEST_MANAGER_APPROVAL');
    expect(() => interpreter.send({ type: 'APPROVE', approver: 'manager' })).toThrow();
    
    // Get VP approval - now it works
    interpreter.send('REQUEST_VP_APPROVAL');
    interpreter.send({ type: 'APPROVE', approver: 'vp' });
    expect(interpreter.getState().value).toBe('approved');
  });

  test('rejection and revision flow', () => {
    const interpreter = interpret(orderMachine).start();
    
    interpreter.send({ type: 'ADD_ITEM', item: { sku: 'TEST', price: 10, quantity: 1 } });
    interpreter.send('SUBMIT');
    interpreter.send({ type: 'REJECT', reason: 'Invalid SKU' });
    
    expect(interpreter.getState().value).toBe('rejected');
    
    // Revise and resubmit
    interpreter.send('REVISE');
    expect(interpreter.getState().value).toBe('draft');
    
    interpreter.send('SUBMIT');
    expect(interpreter.getState().value).toBe('submitted');
  });
});
```

---

## Error Handling Specification

### Custom Error Types

```typescript
// All errors should extend FlowForgeError
class FlowForgeError extends Error {
  constructor(message: string, public code: string) {
    super(message);
    this.name = 'FlowForgeError';
  }
}

class InvalidTransitionError extends FlowForgeError {
  constructor(
    public currentState: string,
    public event: string
  ) {
    super(
      `Cannot transition from "${currentState}" on event "${event}"`,
      'INVALID_TRANSITION'
    );
  }
}

class GuardFailedError extends FlowForgeError {
  constructor(
    public guardName: string,
    public transition: { from: string; to: string; event: string }
  ) {
    super(
      `Guard "${guardName}" failed for transition ${transition.from} -> ${transition.to}`,
      'GUARD_FAILED'
    );
  }
}

class FinalStateError extends FlowForgeError {
  constructor(public state: string) {
    super(
      `Cannot transition from final state "${state}"`,
      'FINAL_STATE'
    );
  }
}

class InvalidConfigError extends FlowForgeError {
  constructor(message: string) {
    super(message, 'INVALID_CONFIG');
  }
}
```

---

## Performance Requirements

1. **State transitions** should complete in < 1ms (excluding async actions)
2. **Guard evaluation** should complete in < 0.5ms per guard
3. **Memory usage** should not exceed 10KB per machine instance (excluding context)
4. **Event queue** should handle 1000 events/second without blocking

---

## Documentation Requirements

### README.md Must Include:
1. Installation instructions
2. Quick start example
3. API reference for all public functions
4. Examples for each feature (guards, actions, timers, parallel, history)
5. TypeScript usage guide
6. Migration guide from XState (conceptual mapping)

---

## Deliverables Checklist

- [ ] All source files in `src/`
- [ ] All test files in `tests/` with 100% of specified tests passing
- [ ] `package.json` with correct dependencies and scripts
- [ ] `tsconfig.json` with strict mode enabled
- [ ] `vitest.config.ts` configured
- [ ] `README.md` with complete documentation
- [ ] `examples/order-fulfillment.ts` with runnable example
- [ ] Zero TypeScript errors in strict mode
- [ ] Zero ESLint errors

---

## Success Criteria

| Metric | Target |
|--------|--------|
| All specified tests pass | 100% |
| TypeScript strict mode | Zero errors |
| ESLint | Zero errors |
| Test coverage | > 90% |
| Documentation complete | All sections |
| Example runs successfully | Yes |
