# FlowBoard -- Complete Testing Strategy (20+ Tests)

## 1. Architecture & Framework Decisions

### Tech Stack Under Test
| Layer | Technology | Test Runner | Key Libraries |
|---|---|---|---|
| Server API | Express + TypeScript | **Vitest** | `supertest`, `@prisma/client` |
| Database | PostgreSQL + Prisma ORM | **Vitest** | prisma mock / test DB |
| WebSocket | Socket.io | **Vitest** | `socket.io-client` |
| Client UI | Next.js 14 App Router + React | **Vitest** (via `@vitejs/plugin-react`) | `@testing-library/react`, `@testing-library/user-event`, `jsdom` |
| Drag-and-Drop | `@dnd-kit` (or similar) | **Vitest** | `@testing-library/react`, `fireEvent`/`pointer` |

### Why Vitest Over Jest
- Native ESM + TypeScript support (no `ts-jest` config pain)
- Same Vite pipeline the client already uses
- Compatible with `@testing-library/react`
- Significantly faster watch mode
- Single test runner for the entire monorepo

### Test Database Strategy
- **CI and local tests**: use a dedicated PostgreSQL test database via `DATABASE_URL` override in `.env.test`
- **Prisma**: run `prisma migrate reset --force` before the test suite to get a clean schema
- **Isolation**: each test file uses a transaction-based cleanup helper (begin txn, run test, rollback) OR `deleteMany` teardown per table in reverse FK order
- **No in-memory SQLite**: the schema uses PostgreSQL-specific features (`@db.Text`, enums) that SQLite cannot represent

---

## 2. Testing Infrastructure

### 2.1 Shared Test Utilities (`server/src/__tests__/helpers/`)

#### `setup.ts` -- Global Setup / Teardown
```
- beforeAll: connect Prisma to test DB, run migrations
- afterAll: disconnect Prisma
- afterEach: truncate all tables in dependency order
```

#### `factories.ts` -- Test Data Factories
```ts
createTestUser(overrides?)    -> { id, email, name, passwordHash, ... }
createTestProject(userId, overrides?)  -> { id, name, creatorId, ... }
createTestTask(projectId, creatorId, overrides?) -> { id, title, status, ... }
createTestSession(userId)     -> { token, refreshToken }
getAuthHeaders(token)         -> { Authorization: `Bearer ${token}` }
```

#### `app.ts` -- Express App Without Listening
```
Export the Express app instance (without calling .listen()) so Supertest can bind to it directly.
```

#### `socket-helpers.ts` -- WebSocket Test Client
```
createSocketClient(token) -> connected socket.io-client instance
waitForEvent(socket, eventName, timeout?) -> Promise<payload>
```

### 2.2 Client Test Utilities (`client/src/__tests__/helpers/`)

#### `render.tsx` -- Custom Render Wrapper
```
- Wraps components in required providers: ThemeProvider, AuthProvider (mocked), QueryClientProvider
- Exposes a `renderWithAuth(component, { user })` helper for authenticated views
```

#### `mocks/`
```
- api.ts: MSW (Mock Service Worker) handlers for all API routes
- socket.ts: Mock socket.io-client with emit/on stubs
- dnd.ts: Pointer-event simulation helpers for drag-and-drop
```

---

## 3. Complete Test Inventory (24 Tests)

---

### CATEGORY A: Auth API Tests (5 tests)

**File**: `server/src/__tests__/api/auth.test.ts`

---

#### TEST 1: `POST /api/auth/signup -- creates user with valid input`
| Field | Detail |
|---|---|
| **Type** | Integration |
| **Description** | Sending a valid `{ email, password, name }` payload creates a user row, returns a 201 with `{ user, token, refreshToken }` |
| **Setup** | Clean users table |
| **Teardown** | Truncate users, sessions |
| **Mocks** | None (hits real test DB) |
| **Assertions** | (1) Response status 201, (2) response body contains `user.id`, `user.email`, `user.name`, (3) `token` and `refreshToken` are non-empty strings, (4) password is NOT in response body, (5) DB contains exactly 1 user with matching email, (6) DB contains exactly 1 session for that user |

#### TEST 2: `POST /api/auth/signup -- rejects duplicate email`
| Field | Detail |
|---|---|
| **Type** | Integration |
| **Description** | Attempting to sign up with an email that already exists returns 409 Conflict |
| **Setup** | Create a user via factory with email `dup@test.com` |
| **Teardown** | Truncate users |
| **Mocks** | None |
| **Assertions** | (1) Response status 409, (2) response body contains an error message referencing "email" or "already exists", (3) DB still contains exactly 1 user with that email |

#### TEST 3: `POST /api/auth/signup -- rejects invalid input (Zod validation)`
| Field | Detail |
|---|---|
| **Type** | Integration |
| **Description** | Sending malformed payloads (missing fields, short password, invalid email format) returns 400 with structured Zod error messages |
| **Setup** | None |
| **Teardown** | None |
| **Mocks** | None |
| **Assertions** | For each invalid payload variant: (1) status 400, (2) body contains `errors` array, (3) each error identifies the offending field path. Test at least 3 variants: `{}`, `{ email: "notanemail" }`, `{ email: "a@b.com", password: "12", name: "" }` |

#### TEST 4: `POST /api/auth/login -- returns tokens for valid credentials`
| Field | Detail |
|---|---|
| **Type** | Integration |
| **Description** | Logging in with correct email/password returns 200 with `{ user, token, refreshToken }` |
| **Setup** | Create user via factory (hash password with bcrypt) |
| **Teardown** | Truncate users, sessions |
| **Mocks** | None |
| **Assertions** | (1) Status 200, (2) `user.email` matches, (3) token is a valid JWT (decode and check `sub` matches user id), (4) a new session row is created in DB |

#### TEST 5: `POST /api/auth/login -- rejects wrong password`
| Field | Detail |
|---|---|
| **Type** | Integration |
| **Description** | Logging in with incorrect password returns 401 |
| **Setup** | Create user via factory |
| **Teardown** | Truncate users |
| **Mocks** | None |
| **Assertions** | (1) Status 401, (2) body contains generic error "Invalid credentials" (not leaking which field was wrong), (3) no new session created |

---

### CATEGORY B: Protected Route Access (1 test)

**File**: `server/src/__tests__/api/auth.test.ts` (same file, separate `describe` block)

---

#### TEST 6: `GET /api/auth/me -- rejects unauthenticated and returns user when authenticated`
| Field | Detail |
|---|---|
| **Type** | Integration |
| **Description** | The `/me` endpoint returns 401 without a token and 200 with a valid token |
| **Setup** | Create user + session via factory |
| **Teardown** | Truncate users, sessions |
| **Mocks** | None |
| **Assertions** | (1) Without `Authorization` header: status 401, (2) with expired/malformed token: status 401, (3) with valid token: status 200 + body contains `user.id`, `user.email`, `user.name`, no `passwordHash` |

---

### CATEGORY C: Task CRUD API Tests (6 tests)

**File**: `server/src/__tests__/api/tasks.test.ts`

---

#### TEST 7: `POST /api/projects/:projectId/tasks -- creates a task`
| Field | Detail |
|---|---|
| **Type** | Integration |
| **Description** | Authenticated user who is a project member can create a task |
| **Setup** | Create user, project, project membership (MEMBER role), obtain auth token |
| **Teardown** | Truncate tasks, project_members, projects, sessions, users |
| **Mocks** | None |
| **Assertions** | (1) Status 201, (2) returned task has `title`, `status: "BACKLOG"` (default), `priority: "MEDIUM"` (default), `creatorId` matches auth user, `projectId` matches URL param, (3) DB contains the new task, (4) `position` is set (integer >= 0) |

#### TEST 8: `GET /api/projects/:projectId/tasks -- returns filtered task list`
| Field | Detail |
|---|---|
| **Type** | Integration |
| **Description** | Fetching tasks with query params `?status=TODO&priority=HIGH&assigneeId=...` returns only matching tasks |
| **Setup** | Create user, project, 5 tasks with varying status/priority/assignee |
| **Teardown** | Truncate all |
| **Mocks** | None |
| **Assertions** | (1) Status 200, (2) without filters: returns all 5 tasks, (3) with `?status=TODO`: returns only tasks with status TODO, (4) with `?priority=HIGH&status=TODO`: returns intersection, (5) tasks are ordered by `position` ascending |

#### TEST 9: `PATCH /api/tasks/:taskId -- updates task fields`
| Field | Detail |
|---|---|
| **Type** | Integration |
| **Description** | Updating a task's title, status, priority, and assignee works correctly |
| **Setup** | Create user, project, task, second user (potential assignee) |
| **Teardown** | Truncate all |
| **Mocks** | None |
| **Assertions** | (1) Status 200, (2) returned task reflects updated fields, (3) DB row matches, (4) `updatedAt` changed, (5) an activity log entry with action `TASK_UPDATED` is created |

#### TEST 10: `PATCH /api/tasks/:taskId -- moves task (status + position change for drag-and-drop)`
| Field | Detail |
|---|---|
| **Type** | Integration |
| **Description** | Changing a task's `status` and `position` (simulating a Kanban drag) correctly reorders sibling tasks |
| **Setup** | Create project with 3 tasks in TODO (positions 0, 1, 2) and 2 tasks in IN_PROGRESS (positions 0, 1) |
| **Teardown** | Truncate all |
| **Mocks** | None |
| **Assertions** | Move task at TODO/pos=1 to IN_PROGRESS/pos=1: (1) Status 200, (2) moved task now has `status: IN_PROGRESS`, `position: 1`, (3) the task that was previously at IN_PROGRESS/pos=1 is now at pos=2, (4) remaining TODO tasks positions are recalculated (gap-free), (5) activity log entry with action `TASK_MOVED` including `metadata: { oldStatus, newStatus }` |

#### TEST 11: `DELETE /api/tasks/:taskId -- deletes a task`
| Field | Detail |
|---|---|
| **Type** | Integration |
| **Description** | Deleting a task removes it and its associated subtasks, comments, and labels |
| **Setup** | Create task with 2 subtasks, 1 comment, and 1 label association |
| **Teardown** | Truncate all |
| **Mocks** | None |
| **Assertions** | (1) Status 200 or 204, (2) task no longer in DB, (3) subtasks no longer in DB (cascade), (4) comments no longer in DB (cascade), (5) task_labels junction rows deleted (cascade), (6) the label itself still exists (not cascade-deleted), (7) activity log entry with `TASK_DELETED` |

#### TEST 12: `PATCH /api/tasks/bulk -- bulk status update`
| Field | Detail |
|---|---|
| **Type** | Integration |
| **Description** | Sending `{ taskIds: [...], updates: { status: "DONE" } }` updates multiple tasks at once |
| **Setup** | Create 4 tasks in various statuses |
| **Teardown** | Truncate all |
| **Mocks** | None |
| **Assertions** | (1) Status 200, (2) all specified tasks now have `status: DONE`, (3) tasks NOT in the list are unchanged, (4) `updatedAt` changed on all affected tasks |

---

### CATEGORY D: Project API Tests (3 tests)

**File**: `server/src/__tests__/api/projects.test.ts`

---

#### TEST 13: `POST /api/projects -- creates project and adds creator as ADMIN member`
| Field | Detail |
|---|---|
| **Type** | Integration |
| **Description** | Creating a project automatically creates a `ProjectMember` row with role ADMIN for the creator |
| **Setup** | Create authenticated user |
| **Teardown** | Truncate projects, project_members, sessions, users |
| **Mocks** | None |
| **Assertions** | (1) Status 201, (2) project has correct `name`, `description`, `creatorId`, (3) `project_members` table has exactly 1 row for this project, (4) that row has `role: ADMIN` and `userId` matching the creator, (5) activity log entry with `PROJECT_CREATED` |

#### TEST 14: `POST /api/projects/:projectId/members -- invite member by email`
| Field | Detail |
|---|---|
| **Type** | Integration |
| **Description** | Project admin can add a new member by providing their email and desired role |
| **Setup** | Create admin user + project + membership, create second user |
| **Teardown** | Truncate all |
| **Mocks** | None |
| **Assertions** | (1) Status 201, (2) new `ProjectMember` row with correct `userId`, `projectId`, `role`, (3) non-admin member attempting the same gets 403, (4) adding non-existent email returns 404, (5) adding already-member returns 409 |

#### TEST 15: `PATCH /api/projects/:projectId -- update project settings`
| Field | Detail |
|---|---|
| **Type** | Integration |
| **Description** | Admin can update project name, description, icon, color, and archived status |
| **Setup** | Create admin user + project |
| **Teardown** | Truncate all |
| **Mocks** | None |
| **Assertions** | (1) Status 200, (2) returned project reflects new values, (3) VIEWER role user gets 403 when attempting update, (4) `updatedAt` changed |

---

### CATEGORY E: Client Component Tests (5 tests)

**File**: `client/src/__tests__/components/`

---

#### TEST 16: `LoginForm -- renders and submits` (`login-form.test.tsx`)
| Field | Detail |
|---|---|
| **Type** | Unit (component) |
| **Description** | The login form renders email and password fields, validates input client-side, and calls the auth API on submit |
| **Setup** | Render `<LoginForm />` inside test providers |
| **Teardown** | `cleanup()` from RTL |
| **Mocks** | MSW handler for `POST /api/auth/login` returning `{ user, token, refreshToken }` |
| **Assertions** | (1) Email and password inputs are rendered, (2) submit button is present, (3) submitting empty form shows validation errors, (4) submitting with valid data calls the API, (5) on success: calls the router push to dashboard, (6) on API error (401): displays error toast/message |

#### TEST 17: `TaskCard -- renders task data correctly` (`task-card.test.tsx`)
| Field | Detail |
|---|---|
| **Type** | Unit (component) |
| **Description** | A task card displays title, priority badge with correct color, assignee avatar, and due date |
| **Setup** | Render `<TaskCard task={mockTask} />` |
| **Teardown** | `cleanup()` |
| **Mocks** | None (pure presentational) |
| **Assertions** | (1) Title text is displayed, (2) priority badge renders with correct label ("Urgent" / "High" / etc.) and correct color class, (3) assignee avatar is rendered when assignee exists, (4) "Unassigned" placeholder when no assignee, (5) due date formatted correctly, (6) overdue tasks show a visual warning indicator |

#### TEST 18: `KanbanBoard -- groups tasks by status columns` (`kanban-board.test.tsx`)
| Field | Detail |
|---|---|
| **Type** | Integration (component) |
| **Description** | The Kanban board component fetches tasks and renders them in the correct status columns |
| **Setup** | Render `<KanbanBoard projectId="..." />` inside providers |
| **Teardown** | `cleanup()` |
| **Mocks** | MSW handler for `GET /api/projects/:id/tasks` returning 10 mock tasks across 5 statuses |
| **Assertions** | (1) 5 column headers rendered (Backlog, Todo, In Progress, In Review, Done), (2) each column shows correct task count badge, (3) tasks appear in the correct column based on status, (4) tasks within each column are ordered by `position`, (5) loading skeleton appears before data loads |

#### TEST 19: `SearchDialog -- opens with Cmd+K and filters results` (`search-dialog.test.tsx`)
| Field | Detail |
|---|---|
| **Type** | Integration (component) |
| **Description** | The global search dialog opens on Cmd/Ctrl+K, accepts input, and displays filtered results |
| **Setup** | Render `<SearchDialog />` inside providers with keyboard event listener |
| **Teardown** | `cleanup()` |
| **Mocks** | MSW handler for `GET /api/search?q=...` returning mock tasks and projects |
| **Assertions** | (1) Dialog not visible initially, (2) pressing Ctrl+K opens the dialog, (3) typing filters results via debounced API call, (4) results show matching tasks and projects, (5) pressing Escape closes dialog, (6) clicking a result navigates to the correct route |

#### TEST 20: `ThemeToggle -- switches between dark and light mode` (`theme-toggle.test.tsx`)
| Field | Detail |
|---|---|
| **Type** | Unit (component) |
| **Description** | The theme toggle button switches themes and persists the choice |
| **Setup** | Render `<ThemeToggle />` inside ThemeProvider |
| **Teardown** | `cleanup()`, clear localStorage |
| **Mocks** | Mock `window.matchMedia` for system preference detection |
| **Assertions** | (1) Renders with system-default theme initially, (2) clicking toggle switches `document.documentElement` class from `light` to `dark` (or vice versa), (3) preference saved to localStorage, (4) on remount reads localStorage preference |

---

### CATEGORY F: Drag-and-Drop State Tests (3 tests)

**File**: `client/src/__tests__/features/drag-and-drop.test.tsx`

---

#### TEST 21: `DnD -- reorders tasks within the same column`
| Field | Detail |
|---|---|
| **Type** | Integration (component + state) |
| **Description** | Dragging a task card from position 0 to position 2 within the same column updates local state and fires an API call |
| **Setup** | Render KanbanBoard with 3 tasks in the TODO column |
| **Teardown** | `cleanup()` |
| **Mocks** | MSW handler for `PATCH /api/tasks/:id` (capture request body), mock the DnD sensor events |
| **Assertions** | (1) Before drag: tasks in order [A, B, C], (2) simulate drag A to position after C, (3) after drop: DOM order is [B, C, A], (4) API called with `{ position: 2, status: "TODO" }`, (5) optimistic update reflected immediately (no loading state) |

#### TEST 22: `DnD -- moves task across columns (status change)`
| Field | Detail |
|---|---|
| **Type** | Integration (component + state) |
| **Description** | Dragging a task from the TODO column to the IN_PROGRESS column updates status and position |
| **Setup** | Render KanbanBoard with tasks in multiple columns |
| **Teardown** | `cleanup()` |
| **Mocks** | MSW handler for `PATCH /api/tasks/:id` |
| **Assertions** | (1) Task starts in TODO column, (2) simulate cross-column drag to IN_PROGRESS, (3) task now renders in IN_PROGRESS column, (4) task no longer in TODO column, (5) API called with `{ status: "IN_PROGRESS", position: <number> }`, (6) column count badges update (TODO decrements, IN_PROGRESS increments) |

#### TEST 23: `DnD -- rolls back on API failure (optimistic update rollback)`
| Field | Detail |
|---|---|
| **Type** | Integration (component + state) |
| **Description** | If the API call fails after a drag, the UI reverts to the previous state |
| **Setup** | Render KanbanBoard with tasks |
| **Teardown** | `cleanup()` |
| **Mocks** | MSW handler for `PATCH /api/tasks/:id` returning 500 error |
| **Assertions** | (1) Simulate drag from TODO to DONE, (2) task momentarily appears in DONE (optimistic), (3) after API rejection: task reappears in TODO (rollback), (4) error toast/notification is shown, (5) column counts revert to original values |

---

### CATEGORY G: WebSocket Real-Time Tests (3 tests)

**File**: `server/src/__tests__/ws/websocket.test.ts`

---

#### TEST 24: `WebSocket -- authenticates and joins project room`
| Field | Detail |
|---|---|
| **Type** | Integration |
| **Description** | A socket.io client connecting with a valid JWT auth token is accepted and can join a project room |
| **Setup** | Start the server on a random port, create user + session + project |
| **Teardown** | Disconnect all sockets, close server |
| **Mocks** | None (real socket.io server) |
| **Assertions** | (1) Client connects successfully (no error event), (2) `connection` event fires on server, (3) emitting `join:project` with valid projectId succeeds, (4) connecting without token or with invalid token triggers `connect_error` |

#### TEST 25: `WebSocket -- broadcasts task:moved event to other clients`
| Field | Detail |
|---|---|
| **Type** | Integration |
| **Description** | When one client moves a task, all other clients in the same project room receive the `task:moved` event |
| **Setup** | Start server, create 2 authenticated socket clients, both join the same project room |
| **Teardown** | Disconnect all, close server |
| **Mocks** | None |
| **Assertions** | (1) Client A emits `task:move` with `{ taskId, newStatus, newPosition }`, (2) Client B receives `task:moved` event with matching payload including the updated task, (3) Client A does NOT receive its own broadcast (or receives it, depending on design decision -- assert whichever is implemented), (4) a client in a DIFFERENT project room does NOT receive the event |

#### TEST 26: `WebSocket -- handles disconnection and reconnection`
| Field | Detail |
|---|---|
| **Type** | Integration |
| **Description** | When a client disconnects and reconnects, it re-joins rooms and resumes receiving events |
| **Setup** | Start server, create authenticated socket client, join project room |
| **Teardown** | Disconnect all, close server |
| **Mocks** | None |
| **Assertions** | (1) Client connected and in room, (2) force-disconnect the client, (3) server `disconnect` event fires, (4) reconnect client (new socket with same token), (5) re-join project room, (6) client receives events broadcast after reconnection |

---

## 4. Test File Structure

```
FlowBoard/
  server/
    src/
      __tests__/
        helpers/
          setup.ts              # Global beforeAll/afterAll/afterEach hooks
          factories.ts          # Test data factory functions
          app.ts                # Express app export for supertest
          socket-helpers.ts     # Socket.io client helpers
        api/
          auth.test.ts          # Tests 1-6
          tasks.test.ts         # Tests 7-12
          projects.test.ts      # Tests 13-15
        ws/
          websocket.test.ts     # Tests 24-26
    vitest.config.ts            # Server Vitest config
  client/
    src/
      __tests__/
        helpers/
          render.tsx            # Custom RTL render with providers
          mocks/
            handlers.ts         # MSW request handlers
            server.ts           # MSW setupServer instance
            socket.ts           # Socket.io mock
        components/
          login-form.test.tsx   # Test 16
          task-card.test.tsx    # Test 17
          kanban-board.test.tsx # Test 18
          search-dialog.test.tsx# Test 19
          theme-toggle.test.tsx # Test 20
        features/
          drag-and-drop.test.tsx# Tests 21-23
    vitest.config.ts            # Client Vitest config
```

---

## 5. Configuration Files

### `server/vitest.config.ts`
```ts
import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    setupFiles: ['./src/__tests__/helpers/setup.ts'],
    include: ['./src/__tests__/**/*.test.ts'],
    testTimeout: 15000,          // WebSocket tests need more time
    hookTimeout: 30000,          // DB migrations in beforeAll
    pool: 'forks',               // Isolate test files (DB state)
    poolOptions: {
      forks: { singleFork: true } // Run sequentially to avoid DB race conditions
    },
    coverage: {
      provider: 'v8',
      include: ['src/**/*.ts'],
      exclude: ['src/__tests__/**'],
    },
  },
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
});
```

### `client/vitest.config.ts`
```ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/__tests__/helpers/render.tsx'],
    include: ['./src/__tests__/**/*.test.tsx'],
    css: false,                   // Skip CSS parsing in tests
    coverage: {
      provider: 'v8',
      include: ['src/**/*.{ts,tsx}'],
      exclude: ['src/__tests__/**'],
    },
  },
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
});
```

---

## 6. Mock Strategies

### 6.1 MSW (Mock Service Worker) for Client Tests
All client component tests use MSW to intercept HTTP requests at the network level rather than mocking `fetch` directly. This tests the actual request/response flow the component uses.

```ts
// client/src/__tests__/helpers/mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.post('/api/auth/login', async ({ request }) => {
    const body = await request.json();
    if (body.email === 'test@test.com' && body.password === 'password123') {
      return HttpResponse.json({
        user: { id: 'u1', email: 'test@test.com', name: 'Test User' },
        token: 'mock-jwt-token',
        refreshToken: 'mock-refresh-token',
      });
    }
    return HttpResponse.json({ error: 'Invalid credentials' }, { status: 401 });
  }),

  http.get('/api/projects/:projectId/tasks', ({ params, request }) => {
    const url = new URL(request.url);
    const status = url.searchParams.get('status');
    // Return filtered mock tasks...
    return HttpResponse.json({ tasks: mockTasks });
  }),

  http.patch('/api/tasks/:taskId', async ({ params, request }) => {
    const body = await request.json();
    return HttpResponse.json({ task: { id: params.taskId, ...body } });
  }),

  // ... more handlers
];
```

### 6.2 Socket.io Mock for Client Tests
```ts
// client/src/__tests__/helpers/mocks/socket.ts
import { vi } from 'vitest';

export function createMockSocket() {
  const listeners = new Map<string, Function[]>();
  return {
    on: vi.fn((event: string, cb: Function) => {
      if (!listeners.has(event)) listeners.set(event, []);
      listeners.get(event)!.push(cb);
    }),
    emit: vi.fn(),
    off: vi.fn(),
    disconnect: vi.fn(),
    connected: true,
    // Helper to simulate server-side events in tests:
    __simulateEvent: (event: string, data: unknown) => {
      listeners.get(event)?.forEach(cb => cb(data));
    },
  };
}
```

### 6.3 Database -- No Mocking on Server
Server API tests hit the real PostgreSQL test database. This ensures Prisma queries, transactions, cascades, and constraints are tested against the real engine. The `.env.test` overrides `DATABASE_URL` to point to a separate `flowboard_test` database.

---

## 7. CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]

jobs:
  test-server:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: flowboard_test
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: flowboard_test
        ports: ['5432:5432']
        options: >-
          --health-cmd="pg_isready"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5
    env:
      DATABASE_URL: postgresql://flowboard_test:testpass@localhost:5432/flowboard_test
      JWT_SECRET: test-jwt-secret-key
      NODE_ENV: test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm ci
      - run: npx prisma migrate deploy --schema=server/prisma/schema.prisma
      - run: npm run test --workspace=server -- --reporter=junit --outputFile=server-results.xml
      - uses: actions/upload-artifact@v4
        if: always()
        with: { name: server-test-results, path: server-results.xml }

  test-client:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm ci
      - run: npm run test --workspace=client -- --reporter=junit --outputFile=client-results.xml
      - uses: actions/upload-artifact@v4
        if: always()
        with: { name: client-test-results, path: client-results.xml }
```

---

## 8. Test Summary Matrix

| # | Test Name | Category | Type | File |
|---|---|---|---|---|
| 1 | Signup creates user with valid input | Auth API | Integration | `auth.test.ts` |
| 2 | Signup rejects duplicate email | Auth API | Integration | `auth.test.ts` |
| 3 | Signup rejects invalid input (Zod) | Auth API | Integration | `auth.test.ts` |
| 4 | Login returns tokens for valid credentials | Auth API | Integration | `auth.test.ts` |
| 5 | Login rejects wrong password | Auth API | Integration | `auth.test.ts` |
| 6 | Protected route /me - auth enforcement | Auth API | Integration | `auth.test.ts` |
| 7 | Create task in project | Task CRUD | Integration | `tasks.test.ts` |
| 8 | Get tasks with filters | Task CRUD | Integration | `tasks.test.ts` |
| 9 | Update task fields | Task CRUD | Integration | `tasks.test.ts` |
| 10 | Move task (drag-and-drop backend) | Task CRUD | Integration | `tasks.test.ts` |
| 11 | Delete task with cascades | Task CRUD | Integration | `tasks.test.ts` |
| 12 | Bulk status update | Task CRUD | Integration | `tasks.test.ts` |
| 13 | Create project + auto-admin membership | Project API | Integration | `projects.test.ts` |
| 14 | Invite member by email | Project API | Integration | `projects.test.ts` |
| 15 | Update project settings | Project API | Integration | `projects.test.ts` |
| 16 | LoginForm renders and submits | Client UI | Unit | `login-form.test.tsx` |
| 17 | TaskCard renders task data | Client UI | Unit | `task-card.test.tsx` |
| 18 | KanbanBoard groups tasks by columns | Client UI | Integration | `kanban-board.test.tsx` |
| 19 | SearchDialog opens and filters | Client UI | Integration | `search-dialog.test.tsx` |
| 20 | ThemeToggle switches modes | Client UI | Unit | `theme-toggle.test.tsx` |
| 21 | DnD reorder within column | Drag-and-Drop | Integration | `drag-and-drop.test.tsx` |
| 22 | DnD cross-column move | Drag-and-Drop | Integration | `drag-and-drop.test.tsx` |
| 23 | DnD optimistic rollback on failure | Drag-and-Drop | Integration | `drag-and-drop.test.tsx` |
| 24 | WebSocket auth + room join | WebSocket | Integration | `websocket.test.ts` |
| 25 | WebSocket broadcasts task:moved | WebSocket | Integration | `websocket.test.ts` |
| 26 | WebSocket disconnect/reconnect | WebSocket | Integration | `websocket.test.ts` |

**Total: 26 tests across 7 categories**

### Coverage Distribution
- Server-side (API + WebSocket): **18 tests** (69%)
- Client-side (UI + DnD): **8 tests** (31%)
- Integration tests: **23 tests** (88%)
- Unit tests: **3 tests** (12%)

---

## 9. Dependencies to Install

### Server
```
npm install -D --workspace=server vitest supertest @types/supertest
```

### Client
```
npm install -D --workspace=client vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/user-event @testing-library/jest-dom msw
```

### Root package.json script entries
```json
{
  "scripts": {
    "test": "npm run test --workspace=server && npm run test --workspace=client",
    "test:server": "npm run test --workspace=server",
    "test:client": "npm run test --workspace=client",
    "test:coverage": "npm run test --workspace=server -- --coverage && npm run test --workspace=client -- --coverage"
  }
}
```
