# FlowBoard -- Technical Requirements Document

> Produced by PLANNER agent from PRD analysis.
> This document is the single source of truth for all implementation agents.

---

## 1. Stack Specifications

### 1.1 Frontend (Client)

| Dependency | Version | Purpose |
|---|---|---|
| `next` | `14.2.x` | App Router framework (NOT 15 -- PRD specifies 14) |
| `react` | `^18.2.0` | UI library |
| `react-dom` | `^18.2.0` | React DOM bindings |
| `typescript` | `^5.4.0` | Language (strict mode) |
| `tailwindcss` | `^3.4.x` | Utility-first CSS (v3, not v4 -- stays compatible with Next 14 + React 18) |
| `@hello-pangea/dnd` | `^18.0.1` | Drag-and-drop for Kanban board (maintained fork of react-beautiful-dnd) |
| `recharts` | `^2.12.x` | Charts/visualizations (v2 for React 18 compatibility; v3 has React 19 deps) |
| `next-themes` | `^0.3.x` | Dark/light mode with system preference detection |
| `socket.io-client` | `^4.8.x` | WebSocket client |
| `zod` | `^3.23.x` | Schema validation (shared with server) |
| `@tanstack/react-query` | `^5.x` | Server state management, optimistic updates, cache |
| `sonner` | `^1.x` | Toast notifications (shadcn/ui recommended replacement for toast) |
| `cmdk` | `^1.x` | Command palette (Cmd/Ctrl+K) |
| `lucide-react` | `^0.x` | Icon library (shadcn/ui default) |
| `class-variance-authority` | `^0.7.x` | Component variant utility (shadcn/ui dependency) |
| `clsx` | `^2.x` | Class merging utility |
| `tailwind-merge` | `^2.x` | Tailwind class conflict resolution |
| `date-fns` | `^3.x` | Date formatting and manipulation |
| `react-markdown` or `@tiptap/react` | latest | Markdown editor for task descriptions |

### 1.2 shadcn/ui Components (Installed via CLI, not npm)

Install these components using `npx shadcn-ui@latest add <component>`:

- `button`, `input`, `label`, `textarea`, `select`
- `dialog`, `sheet` (slide-over panels), `popover`, `dropdown-menu`
- `card`, `badge`, `avatar`, `separator`
- `table`, `checkbox`, `switch`, `tabs`
- `skeleton` (loading states), `tooltip`
- `command` (command palette)
- `calendar`, `form` (react-hook-form + zod integration)
- `chart` (Recharts wrapper)

### 1.3 Backend (Server)

| Dependency | Version | Purpose |
|---|---|---|
| `express` | `^4.21.x` | HTTP framework (v4 for stability; PRD says Express, not v5) |
| `typescript` | `^5.4.0` | Language (strict mode) |
| `prisma` | `^5.x` | ORM CLI + migration tool |
| `@prisma/client` | `^5.x` | Generated database client |
| `socket.io` | `^4.8.x` | WebSocket server |
| `zod` | `^3.23.x` | API input validation (shared schemas with client) |
| `jsonwebtoken` | `^9.x` | JWT token creation and verification |
| `bcryptjs` | `^2.4.x` | Password hashing (10 salt rounds) |
| `cors` | `^2.8.x` | Cross-origin resource sharing |
| `dotenv` | `^16.x` | Environment variable loading |
| `helmet` | `^7.x` | HTTP security headers |
| `morgan` | `^1.10.x` | HTTP request logging |
| `cookie-parser` | `^1.4.x` | Cookie parsing for refresh tokens |

### 1.4 Dev Dependencies (Shared / Root)

| Dependency | Version | Purpose |
|---|---|---|
| `vitest` | `^1.x` | Test runner (faster than Jest for modern stacks) |
| `@testing-library/react` | `^14.x` | React component testing |
| `@testing-library/jest-dom` | `^6.x` | DOM matchers for tests |
| `@testing-library/user-event` | `^14.x` | User interaction simulation |
| `jsdom` | `^24.x` | DOM environment for Vitest |
| `supertest` | `^6.x` | API endpoint testing |
| `eslint` | `^8.x` | Linting |
| `prettier` | `^3.x` | Code formatting |
| `tsx` | `^4.x` | TypeScript execution for seed scripts |
| `concurrently` | `^8.x` | Run client + server simultaneously |
| `ts-node` | `^10.x` | TypeScript Node execution |
| `@types/express` | latest | Express type definitions |
| `@types/jsonwebtoken` | latest | JWT type definitions |
| `@types/bcryptjs` | latest | bcryptjs type definitions |
| `@types/cors` | latest | CORS type definitions |
| `@types/cookie-parser` | latest | Cookie parser type definitions |

### 1.5 Infrastructure

| Technology | Version | Notes |
|---|---|---|
| Node.js | `>=20.x LTS` | Runtime for both client and server |
| PostgreSQL | `15` or `16` | Database |
| npm or pnpm | latest | Package manager (pnpm preferred for monorepo) |

---

## 2. TypeScript Configuration Requirements

### 2.1 Client tsconfig.json

```jsonc
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,                          // MANDATORY per PRD
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

### 2.2 Server tsconfig.json

```jsonc
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,                          // MANDATORY per PRD
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

### 2.3 Strict Mode Sub-Flags (all enabled via `"strict": true`)

- `strictNullChecks` -- No implicit null/undefined
- `strictBindCallApply` -- Type-safe call/bind/apply
- `strictFunctionTypes` -- Contravariant function parameter types
- `strictPropertyInitialization` -- Class properties must be initialized
- `noImplicitAny` -- No implicit any types
- `noImplicitThis` -- No implicit this types
- `alwaysStrict` -- Emit "use strict" in every file

### 2.4 Additional Constraints

- **No `any` types** except in explicitly justified escape hatches (must use `// eslint-disable-next-line @typescript-eslint/no-explicit-any` with comment explaining why)
- **No `@ts-ignore`** -- use `@ts-expect-error` with explanation if absolutely necessary
- All API response types must be explicitly defined (no inferred `any` from fetch calls)
- All event handler types must be explicit
- Shared types between client/server go in a `shared/` directory or are duplicated with identical definitions

---

## 3. Build System Requirements

### 3.1 Monorepo Root package.json Scripts

```jsonc
{
  "scripts": {
    "dev": "concurrently \"npm run dev:client\" \"npm run dev:server\"",
    "dev:client": "cd client && npm run dev",
    "dev:server": "cd server && npm run dev",
    "build": "npm run build:client && npm run build:server",
    "build:client": "cd client && npm run build",
    "build:server": "cd server && npm run build",
    "test": "npm run test:client && npm run test:server",
    "test:client": "cd client && npm run test",
    "test:server": "cd server && npm run test",
    "db:migrate": "cd server && npx prisma migrate dev",
    "db:seed": "cd server && npx prisma db seed",
    "db:studio": "cd server && npx prisma studio",
    "lint": "npm run lint:client && npm run lint:server",
    "lint:client": "cd client && npm run lint",
    "lint:server": "cd server && npm run lint"
  }
}
```

### 3.2 Client Build

- Next.js built-in build system (`next build`)
- Turbopack for dev mode (`next dev --turbo`)
- Output: `.next/` directory
- Environment variables: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_WS_URL`

### 3.3 Server Build

- TypeScript compiled via `tsc` to `dist/`
- Dev mode: `tsx watch src/index.ts` for hot-reload
- Production: `node dist/index.js`
- Environment variables: `DATABASE_URL`, `JWT_SECRET`, `JWT_REFRESH_SECRET`, `PORT`, `CLIENT_URL`

### 3.4 Database

- Prisma schema in `server/prisma/schema.prisma`
- Migrations via `prisma migrate dev` (development) and `prisma migrate deploy` (production)
- Seed script registered in `server/package.json` under `prisma.seed`

---

## 4. Code Quality Requirements

### 4.1 ESLint Configuration

- Extends: `eslint:recommended`, `plugin:@typescript-eslint/recommended`
- Client additionally extends: `next/core-web-vitals`
- Rules enforced:
  - `@typescript-eslint/no-explicit-any`: error
  - `@typescript-eslint/no-unused-vars`: error (with `_` prefix exception)
  - `no-console`: warn (except `console.error`)
  - `prefer-const`: error
  - `no-var`: error

### 4.2 Prettier Configuration

```jsonc
{
  "semi": true,
  "trailingComma": "all",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "bracketSpacing": true,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

### 4.3 Code Organization Rules

- One component per file (named exports, not default exports -- except page.tsx/layout.tsx)
- Co-locate component-specific types in the same file or adjacent `.types.ts` file
- All API calls abstracted into service/hook files (no raw `fetch` in components)
- Custom hooks prefixed with `use`
- Utility functions in `lib/` or `utils/` directories
- Constants in `constants/` directory

---

## 5. Performance Requirements

### 5.1 Optimistic Updates (MANDATORY per PRD)

Every mutation must use optimistic updates. Implementation pattern with TanStack Query:

```typescript
// Required pattern for ALL mutations
useMutation({
  mutationFn: updateTask,
  onMutate: async (newData) => {
    // 1. Cancel outgoing refetches
    await queryClient.cancelQueries({ queryKey: ['tasks'] });
    // 2. Snapshot previous value
    const previous = queryClient.getQueryData(['tasks']);
    // 3. Optimistically update cache
    queryClient.setQueryData(['tasks'], (old) => /* apply optimistic update */);
    // 4. Return rollback context
    return { previous };
  },
  onError: (err, newData, context) => {
    // 5. Rollback on error
    queryClient.setQueryData(['tasks'], context?.previous);
    // 6. Show error toast
    toast.error('Failed to update task');
  },
  onSettled: () => {
    // 7. Refetch to ensure consistency
    queryClient.invalidateQueries({ queryKey: ['tasks'] });
  },
});
```

Mutations requiring optimistic updates:
- Task create / update / delete
- Task status change (drag-and-drop)
- Task priority change
- Task assignment change
- Project create / update / archive
- Comment create / update / delete
- Sub-task toggle completion
- Bulk actions (status change, assign, delete)

### 5.2 Loading Skeletons (MANDATORY per PRD -- NOT spinners)

Every data-fetching state must show skeletons. Required skeleton implementations:

| View | Skeleton Description |
|---|---|
| Dashboard project cards | Card-shaped skeleton with pulsing lines for title, progress bar, stats |
| Dashboard activity feed | List of skeleton items with avatar circle + text lines |
| Kanban board | Column headers + 3-4 card-shaped skeletons per column |
| Kanban card | Rectangle with lines for title, badge shapes for priority/assignee |
| List/table view | Table rows with skeleton cells matching column widths |
| Task detail panel | Full slide-over skeleton with field placeholders |
| Analytics charts | Chart-area-shaped skeletons (rectangle with axis lines) |
| Sidebar navigation | Navigation item skeletons with icon circles + text lines |
| User avatar/profile | Circular skeleton for avatar, lines for name/email |
| Search results | List of skeleton items with title + description lines |

Use shadcn/ui `<Skeleton>` component with appropriate dimensions and layout matching the real content.

### 5.3 Other Performance Requirements

- **Smooth drag-and-drop animations**: @hello-pangea/dnd provides these by default; do NOT disable them
- **Smooth theme transitions**: CSS transitions on color properties (300ms ease)
- **No layout shift**: Skeletons must match real content dimensions
- **Debounced search**: Global search input debounced to 300ms
- **Pagination**: List view must paginate (not infinite scroll) with items-per-page selector
- **Image optimization**: Use Next.js `<Image>` component for all images/avatars

---

## 6. Testing Requirements

### 6.1 Minimum: 20+ Tests Covering Critical Paths

The PRD mandates **20+ tests** covering these critical paths:

#### Authentication Flow (minimum 5 tests)
1. Successful user registration with valid data
2. Registration rejection with invalid/duplicate email
3. Successful login returns valid JWT tokens
4. Login rejection with wrong credentials
5. Protected route redirects unauthenticated users

#### Task CRUD (minimum 5 tests)
6. Create task with all required fields
7. Read/fetch tasks for a project (returns correct data)
8. Update task fields (title, description, priority, status, assignee, due date)
9. Delete task removes it from database
10. Task validation rejects invalid input (missing title, invalid priority)

#### Drag-and-Drop State (minimum 3 tests)
11. Moving task between columns updates status correctly
12. Reordering tasks within a column persists order
13. Optimistic update rolls back on server error

#### API Endpoint Tests (minimum 5 tests)
14. `POST /api/auth/register` -- validates input and creates user
15. `POST /api/auth/login` -- returns access + refresh tokens
16. `GET /api/projects/:id/tasks` -- returns tasks for project (authenticated)
17. `PATCH /api/tasks/:id` -- updates task (authenticated, authorized)
18. `DELETE /api/tasks/:id` -- deletes task (authenticated, authorized)

#### Additional Tests (minimum 4 tests to reach 22+)
19. Zod schema validation rejects malformed API payloads
20. JWT middleware rejects expired/invalid tokens
21. WebSocket connection authenticates and joins project room
22. Seed script creates expected number of records (3 projects, 30+ tasks, 3 users)

### 6.2 Testing Stack

- **Unit + Integration Tests**: Vitest + React Testing Library + jsdom
- **API Tests**: Vitest + supertest
- **Test file naming**: `*.test.ts` or `*.test.tsx` co-located with source files or in `__tests__/` directories
- **Test configuration**: `vitest.config.ts` in both `/client` and `/server`

### 6.3 Test Commands

```bash
# Run all tests
npm run test

# Run with coverage
npm run test -- --coverage

# Run specific test file
npm run test -- path/to/file.test.ts

# Watch mode
npm run test -- --watch
```

---

## 7. Data Seeding Requirements

### 7.1 Seed Script Location

`server/prisma/seed.ts`

### 7.2 Seed Data Specifications

#### Users (3 users)

| Field | User 1 | User 2 | User 3 |
|---|---|---|---|
| name | Alice Johnson | Bob Smith | Carol Williams |
| email | alice@flowboard.demo | bob@flowboard.demo | carol@flowboard.demo |
| password | `demo123` (hashed with bcryptjs) | `demo123` (hashed) | `demo123` (hashed) |
| avatar | Generated initials or placeholder URL | Same | Same |
| role | admin | member | member |

#### Projects (3 projects)

| Field | Project 1 | Project 2 | Project 3 |
|---|---|---|---|
| name | FlowBoard Development | Marketing Campaign Q1 | Mobile App Redesign |
| description | Building the next-gen project management tool | Q1 2024 marketing initiatives and campaigns | Complete redesign of the mobile application |
| icon | code | megaphone | smartphone |
| color | #6366f1 (indigo) | #f59e0b (amber) | #10b981 (emerald) |
| owner | Alice | Bob | Carol |
| members | All 3 users | Alice + Bob | Bob + Carol |

#### Tasks (30+ tasks distributed across projects)

Distribution:
- Project 1: 12+ tasks
- Project 2: 10+ tasks
- Project 3: 10+ tasks

Each task must have:
- **title**: Realistic task names (e.g., "Implement authentication flow", "Design landing page hero section")
- **description**: 1-3 sentences of markdown content
- **status**: Distributed across all 5 statuses (Backlog, Todo, In Progress, In Review, Done)
- **priority**: Mix of Urgent, High, Medium, Low
- **assignee**: One of the 3 users
- **due_date**: Mix of past (overdue), today, this week, next week, next month
- **labels**: At least 5 distinct labels used across tasks (e.g., "bug", "feature", "design", "backend", "frontend")
- **sub_tasks**: At least 5 tasks should have 2-3 sub-tasks each
- **comments**: At least 10 tasks should have 1-2 comments from different users
- **created_at**: Staggered over the past 30 days (for realistic activity feed and analytics)
- **order**: Explicit ordering within each column for Kanban view

#### Activity Log Entries

Seed at least 20 activity entries showing:
- Task creations
- Status changes
- Assignment changes
- Comments added
- Spread over the past 14 days

### 7.3 Seed Script Requirements

```typescript
// server/prisma/seed.ts
// Must be idempotent -- safe to run multiple times
// Must clear existing data before seeding (upsert or deleteMany + create)
// Must use transactions for data integrity
// Must hash passwords with bcryptjs (10 rounds)
// Must output progress to console (e.g., "Seeded 3 users... Seeded 3 projects... Seeded 32 tasks...")
```

Register in `server/package.json`:
```jsonc
{
  "prisma": {
    "seed": "tsx prisma/seed.ts"
  }
}
```

---

## 8. Project Structure Requirements

### 8.1 Monorepo Root

```
FlowBoard/
  package.json              # Root scripts (dev, build, test, lint)
  .gitignore
  .env.example              # Template for environment variables
  README.md                 # Setup instructions (only if requested)
  client/                   # Next.js frontend
  server/                   # Express backend
```

### 8.2 Client Directory Structure

```
client/
  package.json
  next.config.js
  tailwind.config.ts
  tsconfig.json
  postcss.config.js
  components.json           # shadcn/ui configuration
  .env.local                # NEXT_PUBLIC_API_URL, NEXT_PUBLIC_WS_URL
  public/
    favicon.ico
  src/
    app/                    # Next.js App Router pages
      layout.tsx            # Root layout (ThemeProvider, QueryClientProvider)
      page.tsx              # Redirect to /dashboard or /login
      (auth)/               # Auth route group (no sidebar layout)
        login/page.tsx
        register/page.tsx
      (dashboard)/          # Dashboard route group (with sidebar layout)
        layout.tsx          # Sidebar + main content layout
        dashboard/page.tsx  # Home dashboard
        projects/
          page.tsx          # All projects
          [id]/
            page.tsx        # Project detail (redirects to board)
            board/page.tsx  # Kanban board view
            list/page.tsx   # Table/list view
            analytics/page.tsx
            settings/page.tsx
        settings/page.tsx   # User profile settings
    components/
      ui/                   # shadcn/ui components (auto-generated)
      layout/               # Sidebar, Header, MobileNav
      dashboard/            # Dashboard-specific components
      kanban/               # Board, Column, Card, AddCard
      task/                 # TaskDetailPanel, TaskForm, SubTasks
      project/              # ProjectCard, ProjectForm
      analytics/            # Chart components (wrapped in 'use client')
      auth/                 # LoginForm, RegisterForm
      shared/               # SearchCommand, ThemeToggle, UserAvatar, SkeletonLoaders
    hooks/                  # Custom React hooks
      use-tasks.ts          # TanStack Query hooks for tasks
      use-projects.ts       # TanStack Query hooks for projects
      use-auth.ts           # Authentication hooks
      use-socket.ts         # WebSocket connection hook
      use-keyboard-shortcuts.ts
      use-optimistic-update.ts
    lib/
      api.ts                # Axios/fetch instance with auth interceptor
      utils.ts              # cn() helper, formatters
      validations.ts        # Shared Zod schemas (client-side)
      constants.ts          # Status labels, priority colors, etc.
      query-client.ts       # TanStack Query client configuration
    providers/
      query-provider.tsx    # TanStack Query provider
      theme-provider.tsx    # next-themes provider
      socket-provider.tsx   # Socket.io context provider
      auth-provider.tsx     # Auth context provider
    types/
      index.ts              # Shared TypeScript types/interfaces
```

### 8.3 Server Directory Structure

```
server/
  package.json
  tsconfig.json
  .env                      # DATABASE_URL, JWT_SECRET, etc.
  prisma/
    schema.prisma           # Database schema
    migrations/             # Prisma migrations (auto-generated)
    seed.ts                 # Seed script
  src/
    index.ts                # Entry point (Express + Socket.io server)
    app.ts                  # Express app configuration (middleware, routes)
    config/
      env.ts                # Environment variable validation with Zod
      database.ts           # Prisma client singleton
    routes/
      auth.routes.ts        # /api/auth/*
      project.routes.ts     # /api/projects/*
      task.routes.ts        # /api/tasks/*
      user.routes.ts        # /api/users/*
    controllers/
      auth.controller.ts
      project.controller.ts
      task.controller.ts
      user.controller.ts
    middleware/
      auth.middleware.ts    # JWT verification
      validate.middleware.ts # Zod validation middleware
      error.middleware.ts   # Global error handler
    services/
      auth.service.ts       # Business logic for auth
      project.service.ts
      task.service.ts
      user.service.ts
    socket/
      index.ts              # Socket.io server setup
      handlers/
        task.handler.ts     # Task-related socket events
        project.handler.ts  # Project-related socket events
        presence.handler.ts # Online presence tracking
    validations/
      auth.schema.ts        # Zod schemas for auth endpoints
      project.schema.ts
      task.schema.ts
      user.schema.ts
    types/
      index.ts              # Server-specific types
      express.d.ts          # Express Request augmentation (req.user)
    utils/
      jwt.ts                # Token generation/verification helpers
      errors.ts             # Custom error classes (AppError, ValidationError, etc.)
```

---

## 9. API Design Requirements

### 9.1 Zod Validation Middleware (MANDATORY per PRD)

Every API endpoint must validate its input using Zod schemas before reaching the controller.

#### Validation Middleware Pattern

```typescript
// server/src/middleware/validate.middleware.ts
import { Request, Response, NextFunction } from 'express';
import { AnyZodObject, ZodError } from 'zod';

export const validate = (schema: AnyZodObject) => {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      await schema.parseAsync({
        body: req.body,
        query: req.query,
        params: req.params,
      });
      next();
    } catch (error) {
      if (error instanceof ZodError) {
        return res.status(400).json({
          status: 'error',
          message: 'Validation failed',
          errors: error.errors.map((e) => ({
            field: e.path.join('.'),
            message: e.message,
          })),
        });
      }
      next(error);
    }
  };
};
```

### 9.2 API Endpoints

#### Authentication

| Method | Path | Body | Response | Auth |
|---|---|---|---|---|
| POST | `/api/auth/register` | `{ name, email, password }` | `{ user, accessToken, refreshToken }` | No |
| POST | `/api/auth/login` | `{ email, password }` | `{ user, accessToken, refreshToken }` | No |
| POST | `/api/auth/refresh` | `{ refreshToken }` | `{ accessToken, refreshToken }` | No |
| POST | `/api/auth/logout` | -- | `{ message }` | Yes |
| GET | `/api/auth/me` | -- | `{ user }` | Yes |

#### Projects

| Method | Path | Body/Query | Response | Auth |
|---|---|---|---|---|
| GET | `/api/projects` | -- | `{ projects[] }` | Yes |
| POST | `/api/projects` | `{ name, description, icon, color }` | `{ project }` | Yes |
| GET | `/api/projects/:id` | -- | `{ project }` | Yes |
| PATCH | `/api/projects/:id` | `{ name?, description?, icon?, color? }` | `{ project }` | Yes |
| DELETE | `/api/projects/:id` | -- | `{ message }` | Yes (admin) |
| POST | `/api/projects/:id/members` | `{ email, role }` | `{ member }` | Yes (admin) |
| DELETE | `/api/projects/:id/members/:userId` | -- | `{ message }` | Yes (admin) |

#### Tasks

| Method | Path | Body/Query | Response | Auth |
|---|---|---|---|---|
| GET | `/api/projects/:projectId/tasks` | `?status, ?priority, ?assignee, ?search, ?sort, ?page, ?limit` | `{ tasks[], total, page, limit }` | Yes |
| POST | `/api/projects/:projectId/tasks` | `{ title, description?, status, priority, assigneeId?, dueDate?, labels? }` | `{ task }` | Yes |
| GET | `/api/tasks/:id` | -- | `{ task }` (with subtasks, comments, activity) | Yes |
| PATCH | `/api/tasks/:id` | `{ title?, description?, status?, priority?, assigneeId?, dueDate?, labels?, order? }` | `{ task }` | Yes |
| DELETE | `/api/tasks/:id` | -- | `{ message }` | Yes |
| PATCH | `/api/tasks/:id/order` | `{ status, order }` | `{ task }` | Yes |
| POST | `/api/tasks/:id/subtasks` | `{ title }` | `{ subtask }` | Yes |
| PATCH | `/api/subtasks/:id` | `{ title?, completed? }` | `{ subtask }` | Yes |
| POST | `/api/tasks/:id/comments` | `{ content }` | `{ comment }` | Yes |

#### Users

| Method | Path | Body | Response | Auth |
|---|---|---|---|---|
| GET | `/api/users` | `?search` | `{ users[] }` | Yes |
| GET | `/api/users/:id` | -- | `{ user }` | Yes |
| PATCH | `/api/users/me` | `{ name?, avatar? }` | `{ user }` | Yes |

#### Search

| Method | Path | Query | Response | Auth |
|---|---|---|---|---|
| GET | `/api/search` | `?q` | `{ tasks[], projects[], users[] }` | Yes |

#### Analytics

| Method | Path | Query | Response | Auth |
|---|---|---|---|---|
| GET | `/api/projects/:id/analytics` | `?range` (7d, 30d, 90d) | `{ tasksOverTime[], tasksByStatus[], tasksByPriority[], velocity[] }` | Yes |

### 9.3 Zod Schema Examples

```typescript
// server/src/validations/task.schema.ts
import { z } from 'zod';

export const TaskStatus = z.enum(['BACKLOG', 'TODO', 'IN_PROGRESS', 'IN_REVIEW', 'DONE']);
export const TaskPriority = z.enum(['URGENT', 'HIGH', 'MEDIUM', 'LOW']);

export const createTaskSchema = z.object({
  body: z.object({
    title: z.string().min(1, 'Title is required').max(200),
    description: z.string().max(5000).optional(),
    status: TaskStatus.default('TODO'),
    priority: TaskPriority.default('MEDIUM'),
    assigneeId: z.string().uuid().optional(),
    dueDate: z.string().datetime().optional(),
    labels: z.array(z.string().max(50)).max(10).optional(),
  }),
  params: z.object({
    projectId: z.string().uuid(),
  }),
});

export const updateTaskSchema = z.object({
  body: z.object({
    title: z.string().min(1).max(200).optional(),
    description: z.string().max(5000).optional(),
    status: TaskStatus.optional(),
    priority: TaskPriority.optional(),
    assigneeId: z.string().uuid().nullable().optional(),
    dueDate: z.string().datetime().nullable().optional(),
    labels: z.array(z.string().max(50)).max(10).optional(),
    order: z.number().int().min(0).optional(),
  }),
  params: z.object({
    id: z.string().uuid(),
  }),
});
```

### 9.4 API Response Format

All API responses must follow a consistent format:

```typescript
// Success
{ status: 'success', data: { ... } }

// Error
{ status: 'error', message: 'Human-readable error', errors?: [{ field, message }] }

// Paginated
{ status: 'success', data: { items: [...], total: number, page: number, limit: number } }
```

### 9.5 HTTP Status Codes

| Code | Usage |
|---|---|
| 200 | Successful GET, PATCH |
| 201 | Successful POST (resource created) |
| 204 | Successful DELETE |
| 400 | Validation error (Zod) |
| 401 | Missing or invalid authentication |
| 403 | Insufficient permissions |
| 404 | Resource not found |
| 409 | Conflict (e.g., duplicate email) |
| 500 | Internal server error |

---

## 10. Real-Time Requirements (Socket.io)

### 10.1 Socket.io Server Configuration

```typescript
// server/src/socket/index.ts
const io = new Server(httpServer, {
  cors: {
    origin: process.env.CLIENT_URL,
    methods: ['GET', 'POST'],
    credentials: true,
  },
  transports: ['websocket', 'polling'],
});
```

### 10.2 Authentication

- Socket connections must be authenticated using JWT tokens
- Token passed via `auth` option in client handshake
- Server validates token in Socket.io middleware before allowing connection

```typescript
// Server middleware
io.use(async (socket, next) => {
  const token = socket.handshake.auth.token;
  if (!token) return next(new Error('Authentication required'));
  try {
    const decoded = verifyAccessToken(token);
    socket.data.user = decoded;
    next();
  } catch {
    next(new Error('Invalid token'));
  }
});
```

### 10.3 Room Structure

- Each project has a room: `project:{projectId}`
- Users join/leave project rooms as they navigate
- Events are broadcast to the room (not globally)

### 10.4 Socket Events

#### Client -> Server

| Event | Payload | Description |
|---|---|---|
| `project:join` | `{ projectId }` | Join a project room |
| `project:leave` | `{ projectId }` | Leave a project room |
| `task:move` | `{ taskId, newStatus, newOrder }` | Task moved on Kanban board |

#### Server -> Client

| Event | Payload | Description |
|---|---|---|
| `task:created` | `{ task }` | New task created in project |
| `task:updated` | `{ task }` | Task was updated |
| `task:deleted` | `{ taskId }` | Task was deleted |
| `task:moved` | `{ taskId, newStatus, newOrder, movedBy }` | Task moved on board |
| `comment:created` | `{ comment }` | New comment on a task |
| `presence:update` | `{ users[] }` | Updated list of online users in room |
| `project:updated` | `{ project }` | Project details changed |

### 10.5 Client Socket Hook

```typescript
// client/src/hooks/use-socket.ts
// Must provide:
// - Connection management (connect/disconnect on auth state change)
// - Auto-reconnection
// - Room join/leave on project navigation
// - Event listeners that invalidate TanStack Query cache
// - Presence tracking
```

### 10.6 Integration with Optimistic Updates

When a user performs a mutation:
1. Optimistic update applied locally via TanStack Query
2. API call sent to server
3. Server processes and broadcasts Socket.io event to room (excluding sender)
4. Other clients receive event and update their cache
5. If API call fails, sender's optimistic update rolls back

---

## 11. Authentication Requirements (JWT)

### 11.1 Token Strategy

| Token | Type | Expiration | Storage |
|---|---|---|---|
| Access Token | JWT | 15 minutes | Memory (React state / context) |
| Refresh Token | JWT | 7 days | HttpOnly Secure cookie |

### 11.2 JWT Payload

```typescript
// Access Token Payload
{
  userId: string;
  email: string;
  name: string;
  iat: number;
  exp: number;
}

// Refresh Token Payload
{
  userId: string;
  iat: number;
  exp: number;
}
```

### 11.3 Password Security

- Hash with `bcryptjs`, 10 salt rounds
- Minimum password length: 8 characters
- Password never returned in API responses
- Password never stored in JWT payload

### 11.4 Auth Middleware

```typescript
// server/src/middleware/auth.middleware.ts
// Must:
// 1. Extract token from Authorization header (Bearer scheme)
// 2. Verify token signature and expiration
// 3. Attach user data to req.user
// 4. Return 401 if token missing/invalid/expired
```

### 11.5 Client Auth Flow

1. On app load, check for refresh token (cookie)
2. If refresh token exists, call `/api/auth/refresh` to get new access token
3. Store access token in memory (NOT localStorage)
4. Attach access token to all API requests via interceptor
5. On 401 response, attempt token refresh; if refresh fails, redirect to login
6. On logout, clear access token from memory and call `/api/auth/logout` (which clears refresh cookie)

### 11.6 Protected Routes

- All routes except `/login` and `/register` are protected
- Next.js middleware (`middleware.ts`) checks for auth state
- Redirect unauthenticated users to `/login`
- Redirect authenticated users away from `/login` and `/register` to `/dashboard`

---

## 12. Theme System Requirements

### 12.1 Implementation

- Use `next-themes` library with `ThemeProvider`
- Tailwind CSS `darkMode: "class"` configuration
- Three modes: `light`, `dark`, `system`
- Default: `system` (matches OS preference via `prefers-color-scheme`)

### 12.2 Root Layout Configuration

```tsx
// client/src/app/layout.tsx
<html lang="en" suppressHydrationWarning>
  <body>
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange={false}>
      {children}
    </ThemeProvider>
  </body>
</html>
```

### 12.3 CSS Variables (shadcn/ui Theme)

Define in `globals.css` with both `:root` (light) and `.dark` (dark) variants:

```css
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 240 10% 3.9%;
    --card: 0 0% 100%;
    --card-foreground: 240 10% 3.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 240 10% 3.9%;
    --primary: 240 5.9% 10%;
    --primary-foreground: 0 0% 98%;
    --secondary: 240 4.8% 95.9%;
    --secondary-foreground: 240 5.9% 10%;
    --muted: 240 4.8% 95.9%;
    --muted-foreground: 240 3.8% 46.1%;
    --accent: 240 4.8% 95.9%;
    --accent-foreground: 240 5.9% 10%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 0 0% 98%;
    --border: 240 5.9% 90%;
    --input: 240 5.9% 90%;
    --ring: 240 5.9% 10%;
    --radius: 0.5rem;
    /* Chart colors */
    --chart-1: 12 76% 61%;
    --chart-2: 173 58% 39%;
    --chart-3: 197 37% 24%;
    --chart-4: 43 74% 66%;
    --chart-5: 27 87% 67%;
  }

  .dark {
    --background: 240 10% 3.9%;
    --foreground: 0 0% 98%;
    /* ... all dark variants ... */
  }
}
```

### 12.4 Design Language (Linear-Inspired)

Since the PRD references Linear as the design inspiration:

- **Color palette**: Neutral grays for backgrounds, vibrant accents for actions
- **Typography**: Clean sans-serif (Inter or system font stack)
- **Spacing**: Generous whitespace, 4px grid system
- **Borders**: Subtle, thin borders (1px, low opacity)
- **Shadows**: Minimal, used sparingly for elevation
- **Animations**: Smooth, subtle transitions (150-300ms)
- **Components**: Clean minimalism, no unnecessary decoration

### 12.5 Theme Toggle Component

- Located in sidebar footer or header
- Three-state toggle: Light / Dark / System
- Uses `useTheme` hook from `next-themes`
- Shows current resolved theme (not "system" label when system is selected; show actual resolved value in icon)
- Smooth CSS transition on theme change (300ms)

### 12.6 Both Themes Must Be Polished

Per PRD: "Both themes must look equally polished." This means:
- All charts must be readable in both themes (axis labels, legends, colors)
- All priority badges must be visible in both themes
- All skeleton loaders must be visible in both themes
- Form inputs must have visible borders in both themes
- Focus rings must be visible in both themes
- Avatar initials must be readable against background in both themes
- Drag-and-drop placeholder must be visible in both themes

---

## 13. Database Schema (Prisma)

```prisma
// server/prisma/schema.prisma

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id            String    @id @default(uuid())
  name          String
  email         String    @unique
  passwordHash  String
  avatar        String?
  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt

  ownedProjects  Project[]       @relation("ProjectOwner")
  memberships    ProjectMember[]
  assignedTasks  Task[]          @relation("TaskAssignee")
  comments       Comment[]
  activities     Activity[]
}

model Project {
  id          String    @id @default(uuid())
  name        String
  description String?
  icon        String?
  color       String?
  archived    Boolean   @default(false)
  createdAt   DateTime  @default(now())
  updatedAt   DateTime  @updatedAt

  ownerId     String
  owner       User             @relation("ProjectOwner", fields: [ownerId], references: [id])
  members     ProjectMember[]
  tasks       Task[]
  activities  Activity[]
}

model ProjectMember {
  id        String   @id @default(uuid())
  role      Role     @default(MEMBER)
  joinedAt  DateTime @default(now())

  userId    String
  user      User    @relation(fields: [userId], references: [id], onDelete: Cascade)
  projectId String
  project   Project @relation(fields: [projectId], references: [id], onDelete: Cascade)

  @@unique([userId, projectId])
}

enum Role {
  ADMIN
  MEMBER
  VIEWER
}

model Task {
  id          String       @id @default(uuid())
  title       String
  description String?
  status      TaskStatus   @default(TODO)
  priority    TaskPriority @default(MEDIUM)
  order       Int          @default(0)
  dueDate     DateTime?
  labels      String[]     @default([])
  createdAt   DateTime     @default(now())
  updatedAt   DateTime     @updatedAt

  projectId   String
  project     Project   @relation(fields: [projectId], references: [id], onDelete: Cascade)
  assigneeId  String?
  assignee    User?     @relation("TaskAssignee", fields: [assigneeId], references: [id], onDelete: SetNull)

  subTasks    SubTask[]
  comments    Comment[]
  activities  Activity[]
}

enum TaskStatus {
  BACKLOG
  TODO
  IN_PROGRESS
  IN_REVIEW
  DONE
}

enum TaskPriority {
  URGENT
  HIGH
  MEDIUM
  LOW
}

model SubTask {
  id        String   @id @default(uuid())
  title     String
  completed Boolean  @default(false)
  order     Int      @default(0)
  createdAt DateTime @default(now())

  taskId    String
  task      Task     @relation(fields: [taskId], references: [id], onDelete: Cascade)
}

model Comment {
  id        String   @id @default(uuid())
  content   String
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  taskId    String
  task      Task     @relation(fields: [taskId], references: [id], onDelete: Cascade)
  authorId  String
  author    User     @relation(fields: [authorId], references: [id], onDelete: Cascade)
}

model Activity {
  id          String       @id @default(uuid())
  action      String       // e.g., "created", "updated_status", "assigned", "commented"
  details     Json?        // Additional context (e.g., { from: "TODO", to: "IN_PROGRESS" })
  createdAt   DateTime     @default(now())

  userId      String
  user        User         @relation(fields: [userId], references: [id], onDelete: Cascade)
  projectId   String
  project     Project      @relation(fields: [projectId], references: [id], onDelete: Cascade)
  taskId      String?
  task        Task?        @relation(fields: [taskId], references: [id], onDelete: SetNull)
}
```

---

## 14. Environment Variables

### 14.1 Server `.env`

```env
DATABASE_URL="postgresql://postgres:password@localhost:5432/flowboard"
JWT_SECRET="<random-64-char-string>"
JWT_REFRESH_SECRET="<different-random-64-char-string>"
PORT=3001
CLIENT_URL="http://localhost:3000"
NODE_ENV="development"
```

### 14.2 Client `.env.local`

```env
NEXT_PUBLIC_API_URL="http://localhost:3001/api"
NEXT_PUBLIC_WS_URL="http://localhost:3001"
```

### 14.3 Validation

Server environment variables must be validated at startup using Zod:

```typescript
// server/src/config/env.ts
import { z } from 'zod';

const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  JWT_SECRET: z.string().min(32),
  JWT_REFRESH_SECRET: z.string().min(32),
  PORT: z.coerce.number().default(3001),
  CLIENT_URL: z.string().url(),
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
});

export const env = envSchema.parse(process.env);
```

---

## 15. Responsive Design Requirements

| Breakpoint | Layout Changes |
|---|---|
| Desktop (>= 1024px) | Full sidebar, all columns visible, side-by-side panels |
| Tablet (768px - 1023px) | Collapsible sidebar (hamburger toggle), reduced padding |
| Mobile (< 768px) | Bottom navigation bar, swipeable kanban columns, stacked layout |

### Specific Requirements

- Sidebar: Persistent on desktop, collapsible on tablet, hidden on mobile (bottom nav instead)
- Kanban: All columns visible on desktop, horizontally scrollable with snap on mobile
- Task detail: Full slide-over on desktop/tablet, full-screen modal on mobile
- Table: Horizontally scrollable on mobile with sticky first column
- Analytics charts: Responsive with proper labels at all breakpoints

---

## Summary of Hard Constraints from PRD

These are non-negotiable requirements that must be verified:

1. TypeScript `"strict": true` in BOTH client and server tsconfig
2. Zod validation on EVERY API endpoint (no unvalidated input reaches controllers)
3. Loading skeletons (NOT spinners) for ALL data-fetching states
4. Optimistic updates for ALL mutations
5. 20+ tests covering auth, task CRUD, drag-and-drop state, and API endpoints
6. Seed script creates 3 projects, 30+ tasks, 3 users
7. Monorepo with `/client` and `/server` directories
8. JWT authentication with protected routes
9. Socket.io real-time updates (multi-user live sync)
10. Recharts for all analytics visualizations
11. Dark/light mode with system preference detection
12. Both themes must look equally polished
13. Next.js 14 App Router (not Pages Router, not Next.js 15)
14. shadcn/ui component library
15. Clean minimalist design inspired by Linear
