# FlowBoard -- Complete Frontend Architecture Plan

## Table of Contents

1. [Design System Foundation](#1-design-system-foundation)
2. [Route Map](#2-route-map)
3. [Folder Structure](#3-folder-structure)
4. [Page-by-Page Specifications](#4-page-by-page-specifications)
5. [Shared Components Catalog](#5-shared-components-catalog)
6. [State Management Architecture](#6-state-management-architecture)
7. [Data Fetching Strategy](#7-data-fetching-strategy)
8. [User Interaction Flows](#8-user-interaction-flows)
9. [Server vs Client Component Boundaries](#9-server-vs-client-component-boundaries)
10. [Loading and Error States](#10-loading-and-error-states)
11. [Responsive Breakpoints](#11-responsive-breakpoints)
12. [Keyboard Shortcuts and Accessibility](#12-keyboard-shortcuts-and-accessibility)

---

## 1. Design System Foundation

Inspired by Linear's design language: monochromatic palette, bold typography, minimal color accents, LCH-derived theming, and high information density.

### Color Tokens (CSS custom properties via Tailwind)

```
--background:         light 0 0 100%   / dark 222.2 84% 4.9%
--foreground:         light 222.2 84% 4.9%  / dark 210 40% 98%
--card:               light 0 0 100%   / dark 222.2 84% 4.9%
--card-foreground:    light 222.2 84% 4.9%  / dark 210 40% 98%
--primary:            light 222.2 47.4% 11.2% / dark 210 40% 98%
--primary-foreground: light 210 40% 98% / dark 222.2 47.4% 11.2%
--muted:              light 210 40% 96.1% / dark 217.2 32.6% 17.5%
--muted-foreground:   light 215.4 16.3% 46.9% / dark 215 20.2% 65.1%
--accent:             light 210 40% 96.1% / dark 217.2 32.6% 17.5%
--destructive:        0 84.2% 60.2%  (both modes)
--border:             light 214.3 31.8% 91.4% / dark 217.2 32.6% 17.5%
--ring:               light 222.2 84% 4.9%  / dark 212.7 26.8% 83.9%

Priority colors:
--priority-urgent:    0 84% 60%        (red)
--priority-high:      25 95% 53%       (orange)
--priority-medium:    48 96% 53%       (yellow)
--priority-low:       210 40% 65%      (muted blue)
--priority-none:      215 16% 47%      (gray)

Status colors:
--status-backlog:     215 16% 47%      (gray)
--status-todo:        210 40% 65%      (blue-gray)
--status-in-progress: 221 83% 53%      (blue)
--status-in-review:   262 83% 58%      (purple)
--status-done:        142 71% 45%      (green)
```

### Typography

```
Font family:    Inter (sans-serif), fallback to system-ui
Font sizes:     text-xs(12), text-sm(14), text-base(16), text-lg(18), text-xl(20), text-2xl(24), text-3xl(30)
Font weights:   400 (body), 500 (labels/nav), 600 (headings), 700 (page titles)
Line heights:   tight(1.25), normal(1.5), relaxed(1.75)
Letter spacing: tracking-tight(-0.025em) for headings
```

### Spacing Scale

```
Tailwind default: 0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16, 20, 24
Sidebar width:    w-[240px] desktop, w-[60px] collapsed
Top bar height:   h-14 (56px)
Card padding:     p-3 to p-4
Column gap:       gap-4 (kanban), gap-2 (list)
Page padding:     px-6 py-4 desktop, px-4 py-3 mobile
```

### Border Radius

```
Buttons/Inputs:  rounded-md (6px)
Cards:           rounded-lg (8px)
Avatars:         rounded-full
Modals/Panels:   rounded-xl (12px)
```

---

## 2. Route Map

All routes use the Next.js 14 App Router file-system conventions.

```
client/
  src/
    app/
      layout.tsx                         # Root layout: font loading, ThemeProvider, Toaster
      loading.tsx                         # Global fallback skeleton
      not-found.tsx                       # Custom 404 page
      error.tsx                           # Global error boundary
      globals.css                         # Tailwind + CSS custom properties

      (auth)/                             # Route group -- public, no sidebar
        layout.tsx                        # Centered card layout, no nav
        login/
          page.tsx                        # /login
          loading.tsx
        signup/
          page.tsx                        # /signup
          loading.tsx

      (app)/                              # Route group -- protected, sidebar layout
        layout.tsx                        # Sidebar + TopBar + Mobile nav + WebSocket init
        loading.tsx                       # Dashboard-level skeleton
        page.tsx                          # / (dashboard home, redirects from root)

        projects/
          page.tsx                        # /projects (all-projects listing)
          loading.tsx
          new/
            page.tsx                      # /projects/new (create project)
          [projectId]/
            layout.tsx                    # Project-level layout (project header, sub-nav tabs)
            loading.tsx
            page.tsx                      # /projects/[projectId] (redirects to board)
            board/
              page.tsx                    # /projects/[projectId]/board (kanban)
              loading.tsx
            list/
              page.tsx                    # /projects/[projectId]/list (table)
              loading.tsx
            settings/
              page.tsx                    # /projects/[projectId]/settings
              loading.tsx

        analytics/
          page.tsx                        # /analytics
          loading.tsx

        settings/
          page.tsx                        # /settings (profile + app settings)
          loading.tsx

      api/                                # Route handlers (BFF proxy if needed)
        auth/
          [...nextauth]/
            route.ts
```

### Route Protection

```
Middleware: client/src/middleware.ts
  - Checks JWT in cookies
  - Public paths: /login, /signup
  - Protected paths: everything under (app)/
  - Redirects unauthenticated users to /login
  - Redirects authenticated users away from /login, /signup to /
```

---

## 3. Folder Structure

```
client/
  src/
    app/                    # Route segments (pages, layouts, loading, error)
    components/
      ui/                   # shadcn/ui primitives (button, input, dialog, etc.)
      layout/               # Sidebar, TopBar, MobileNav, PageWrapper
      kanban/               # Board, Column, Card, AddCardForm
      list/                 # TaskTable, TableRow, BulkActionBar, Pagination
      task-detail/          # TaskPanel, MarkdownEditor, CommentSection, SubTasks
      search/               # CommandPalette, SearchResults
      charts/               # AreaChart, DonutChart, BarChart, LineChart wrappers
      dashboard/            # ProjectCard, ActivityFeed, MyTasks, QuickAdd
      project/              # ProjectHeader, ProjectTabs, MemberList, ProjectForm
      auth/                 # LoginForm, SignupForm, SocialButtons
      common/               # Avatar, Badge, PriorityBadge, StatusBadge, EmptyState
    hooks/                  # Custom React hooks
      use-socket.ts         # WebSocket connection + event handling
      use-auth.ts           # Auth state + guards
      use-tasks.ts          # Task CRUD operations
      use-projects.ts       # Project CRUD operations
      use-keyboard.ts       # Global keyboard shortcut registration
      use-optimistic.ts     # Optimistic update helper
      use-debounce.ts
      use-media-query.ts
    stores/                 # Zustand stores (OUTSIDE app/ directory)
      auth-store.ts         # User session, tokens
      task-store.ts         # Tasks state, filters, sort
      project-store.ts      # Projects state
      ui-store.ts           # Sidebar collapsed, theme, modals, command palette open
      notification-store.ts # Toast queue
      presence-store.ts     # Online users, cursor positions
    lib/
      api.ts                # Axios/fetch wrapper with interceptors
      validators.ts         # Zod schemas shared between client validation and API
      utils.ts              # cn() helper, date formatters, etc.
      constants.ts          # Priority levels, status columns, keyboard shortcuts map
      socket.ts             # Socket.io client singleton factory
    types/
      index.ts              # Shared TypeScript interfaces
      task.ts               # Task, SubTask, Comment, Activity
      project.ts            # Project, Member, Role
      user.ts               # User, Profile
      api.ts                # API response wrappers, pagination
```

---

## 4. Page-by-Page Specifications

### 4.1 Login Page -- `/login`

**Route:** `(auth)/login/page.tsx`

**Component Hierarchy:**
```
AuthLayout (server component -- centered card wrapper)
  LoginPage (server component -- page shell)
    LoginForm (client component -- "use client")
      Input (email)
      Input (password)
      Button (submit)
      Link (to /signup)
      FormError (inline validation messages)
```

**State Management:**
- Local `useState` for form fields and validation errors
- `useTransition` for pending state during server action
- No Zustand -- form state is ephemeral

**Data Fetching:**
- Server Action: `loginAction(formData)` -- validates with Zod, calls backend `/api/auth/login`, sets HTTP-only cookie, redirects to `/`
- No server-side data fetch on page load

**Loading Skeleton:**
```
+-----------------------------+
|                             |
|      [  Logo skeleton  ]   |
|                             |
|  [=====  input  ======]    |
|  [=====  input  ======]    |
|  [=====  button ======]    |
|                             |
|      Signup link            |
+-----------------------------+
```

**Error States:**
- Inline field validation (red border + message below input)
- Toast notification for server errors (network, 500)
- "Invalid credentials" message from server displayed inline

**User Interactions:**
1. User types email/password
2. Clicks "Sign in" or presses Enter
3. Button shows loading spinner (disabled state)
4. On success: redirect to dashboard
5. On error: show inline message, focus first errored field

---

### 4.2 Signup Page -- `/signup`

**Route:** `(auth)/signup/page.tsx`

**Component Hierarchy:**
```
AuthLayout (server component)
  SignupPage (server component)
    SignupForm (client component -- "use client")
      Input (full name)
      Input (email)
      Input (password)
      Input (confirm password)
      Button (submit)
      Link (to /login)
      FormError
```

**State Management:**
- Local `useState` for form fields, password strength indicator
- `useTransition` for pending state

**Data Fetching:**
- Server Action: `signupAction(formData)` -- validates with Zod, calls backend `/api/auth/register`, auto-logs in on success, redirects to `/`

**Loading Skeleton:** Same centered card pattern as login, with 4 input skeletons.

**Error States:**
- Field-level validation: name required, email format, password min 8 chars, passwords must match
- Server errors: "Email already taken" inline, network errors as toast

**User Interactions:**
1. User fills name, email, password, confirm password
2. Real-time password strength meter updates as user types
3. Submit triggers validation then server action
4. On success: redirect to dashboard
5. On error: highlight fields, show messages

---

### 4.3 Dashboard (Home) -- `/`

**Route:** `(app)/page.tsx`

**Component Hierarchy:**
```
AppLayout (server component -- sidebar + topbar)
  DashboardPage (server component -- data fetching shell)
    Suspense boundary -> ProjectCardsSection
      ProjectCardGrid (server component -- fetches projects)
        ProjectCard (server component) x N
          CircularProgress (client component -- animated)
    Suspense boundary -> MyTasksSection
      MyTasks (server component -- fetches user tasks)
        TaskRow (client component -- clickable, opens panel)
          PriorityBadge
          DueDateBadge
          StatusBadge
    Suspense boundary -> ActivityFeedSection
      ActivityFeed (client component -- "use client" for real-time via WebSocket)
        ActivityItem x N
          Avatar
          Timestamp
    QuickAddTask (client component -- "use client")
      Input (task title)
      ProjectSelector (dropdown)
      Button (submit)
    TaskDetailPanel (client component -- slide-over, conditionally rendered)
```

**State Management:**
- `projectStore` -- list of user's projects (hydrated from server fetch, updated via WebSocket)
- `taskStore` -- user's assigned tasks (hydrated from server, filtered/sorted client-side)
- `uiStore.selectedTaskId` -- controls TaskDetailPanel visibility
- Activity feed: local component state, appended via WebSocket events

**Data Fetching:**
- Server components fetch data directly via `fetch()` to backend API with cookie forwarding
- Three parallel Suspense boundaries stream independently:
  1. `GET /api/projects` -- user's projects with task counts
  2. `GET /api/tasks?assignee=me&sort=dueDate` -- user's tasks
  3. `GET /api/activity?limit=20` -- recent activity
- After hydration, WebSocket pushes live activity updates

**Loading Skeleton:**
```
+-------+------------------------------------------+
|       |  +------+ +------+ +------+ +------+    |
| side  |  |  []  | |  []  | |  []  | |  []  |    |  <- Project card skeletons (4)
| bar   |  | ---- | | ---- | | ---- | | ---- |    |
| skel  |  | ---- | | ---- | | ---- | | ---- |    |
|       |  +------+ +------+ +------+ +------+    |
|       |                                          |
|       |  My Tasks                                |
|       |  [===== skeleton row ======]             |
|       |  [===== skeleton row ======]             |
|       |  [===== skeleton row ======]             |
|       |                                          |
|       |  Activity                                |
|       |  [O  ====== skeleton ======]             |
|       |  [O  ====== skeleton ======]             |
+-------+------------------------------------------+
```

**Error States:**
- Each Suspense section has its own error boundary (partial failure)
- If projects fail: "Could not load projects" card with retry button
- If tasks fail: "Could not load tasks" row with retry button
- If activity fails: "Could not load activity" with retry button
- Network disconnect: toast "Connection lost, reconnecting..."

**User Interactions:**
1. Click project card -> navigate to `/projects/[id]/board`
2. Click task row -> open TaskDetailPanel slide-over
3. Quick-add: type task title, select project from dropdown, press Enter or click Add
4. Activity feed scrolls automatically as new items arrive via WebSocket
5. "See all" links navigate to full project or task lists

---

### 4.4 Projects Listing -- `/projects`

**Route:** `(app)/projects/page.tsx`

**Component Hierarchy:**
```
AppLayout
  ProjectsPage (server component)
    PageHeader
      Title ("Projects")
      Button ("New Project") -> navigates to /projects/new
    Suspense boundary
      ProjectGrid (server component)
        ProjectCard (server component) x N
          ProjectIcon
          ProjectTitle
          MemberAvatarStack
          TaskProgressBar
          ArchiveBadge (if archived)
    EmptyState (if no projects)
```

**State Management:**
- Minimal -- server component fetches and renders
- `uiStore` only for modal states if needed

**Data Fetching:**
- Server component: `GET /api/projects`
- Static shell with streamed project list

**Loading Skeleton:** Grid of 6 project card skeletons (icon + 3 text lines + progress bar).

**Error States:**
- Full-page error boundary: "Failed to load projects" + retry
- Empty state: illustration + "Create your first project" CTA

---

### 4.5 Create Project -- `/projects/new`

**Route:** `(app)/projects/new/page.tsx`

**Component Hierarchy:**
```
AppLayout
  CreateProjectPage (server component)
    PageHeader ("New Project")
    ProjectForm (client component -- "use client")
      Input (name)
      Textarea (description)
      IconPicker (client component)
      ColorPicker (client component)
      Button (submit)
      Button (cancel -> router.back())
```

**State Management:**
- Local form state via `useState`
- `useTransition` for submit

**Data Fetching:**
- Server Action: `createProjectAction(formData)` -> `POST /api/projects`
- On success: `router.push(/projects/[newId]/board)`

**Error States:**
- Inline validation (name required, max length)
- Server errors as toast

---

### 4.6 Project Layout -- `/projects/[projectId]/*`

**Route:** `(app)/projects/[projectId]/layout.tsx`

**Component Hierarchy:**
```
ProjectLayout (server component -- fetches project metadata)
  ProjectHeader (server component)
    ProjectIcon
    ProjectTitle (editable inline -- client component wrapper)
    MemberAvatarStack
    Button ("Invite")
  ProjectTabs (client component -- "use client" for active state)
    TabLink ("Board"  -> /projects/[id]/board)
    TabLink ("List"   -> /projects/[id]/list)
    TabLink ("Settings" -> /projects/[id]/settings)
  {children}   <- sub-route content rendered here
```

**State Management:**
- `projectStore.currentProject` -- hydrated from server fetch
- Tab active state derived from `usePathname()`

**Data Fetching:**
- Server component fetches: `GET /api/projects/[id]` (project name, icon, members)
- Cached at layout level, shared by all sub-routes
- Revalidated on project update via `revalidatePath`

**Error States:**
- 404: project not found -> custom not-found.tsx inside `[projectId]/`
- 403: not a member -> "You don't have access" page with "Request access" button

---

### 4.7 Kanban Board -- `/projects/[projectId]/board`

**Route:** `(app)/projects/[projectId]/board/page.tsx`

**Component Hierarchy:**
```
ProjectLayout (from parent)
  KanbanPage (server component -- fetches tasks)
    BoardToolbar (client component -- "use client")
      FilterDropdown (priority, assignee, label)
      SortDropdown
      SearchInput (within-board search)
    Suspense boundary
      KanbanBoard (client component -- "use client" -- DnD requires client)
        KanbanColumn x 5 (Backlog, Todo, In Progress, In Review, Done)
          ColumnHeader
            StatusBadge
            TaskCountBadge
            AddCardButton (+)
          SortableContext (dnd-kit)
            KanbanCard x N (draggable)
              CardTitle
              PriorityBadge
              AssigneeAvatar
              DueDateBadge
              LabelDots
            AddCardForm (client component -- inline, toggled by + button)
              Input (title)
              Button (save / cancel)
        DragOverlay
          KanbanCard (preview during drag)
    TaskDetailPanel (client component -- slide-over, triggered by card click)
```

**State Management:**
- `taskStore.tasks` -- full task list for this project, keyed by status
- `taskStore.filters` -- active filter criteria
- `taskStore.sortBy` -- current sort
- Drag state managed by `@dnd-kit/core` internally
- Optimistic updates: on drag end, immediately move card in store, fire API call, rollback on failure
- WebSocket: listen for `task:updated`, `task:created`, `task:deleted` events -> update store

**Data Fetching:**
- Server component fetches initial tasks: `GET /api/projects/[id]/tasks`
- Passes data to client `KanbanBoard` as props (server-to-client serialization)
- After hydration, WebSocket provides real-time updates
- Mutations via Server Actions or direct API calls:
  - `PATCH /api/tasks/[id]` (status change on drag)
  - `POST /api/projects/[id]/tasks` (add card)

**Loading Skeleton:**
```
+-------+  +-------+  +-------+  +-------+  +-------+
|Backlog|  | Todo  |  |In Prog|  |Review |  | Done  |
|-------|  |-------|  |-------|  |-------|  |-------|
|[=====]|  |[=====]|  |[=====]|  |[=====]|  |[=====]|
|[=====]|  |[=====]|  |[=====]|  |       |  |[=====]|
|[=====]|  |       |  |[=====]|  |       |  |       |
|       |  |       |  |       |  |       |  |       |
+-------+  +-------+  +-------+  +-------+  +-------+
```
Each card skeleton: rounded-lg with shimmer animation, 3 lines of varying width.

**Error States:**
- Board fails to load: full-width error card with retry
- Single card drag fails: toast "Failed to update task status", card animates back to original column
- WebSocket disconnect: subtle banner "Live updates paused, reconnecting..."

**User Interactions:**
1. Drag card between columns -> optimistic status update -> API call -> toast on failure with rollback
2. Click card -> open TaskDetailPanel slide-over from right
3. Click "+" on column -> show inline AddCardForm at bottom of column
4. Type title in AddCardForm, press Enter -> create task in that column
5. Press Escape -> close AddCardForm
6. Use filter/sort dropdowns -> filter/sort tasks client-side (instant)
7. Inline quick-edit: double-click card title -> editable input -> Enter to save, Escape to cancel
8. Other users' changes appear in real-time (card moves, new cards appear with subtle animation)

---

### 4.8 List/Table View -- `/projects/[projectId]/list`

**Route:** `(app)/projects/[projectId]/list/page.tsx`

**Component Hierarchy:**
```
ProjectLayout (from parent)
  ListPage (server component)
    ListToolbar (client component -- "use client")
      FilterDropdown
      SearchInput
      BulkActionBar (conditionally visible when rows selected)
        Checkbox ("Select all")
        Button ("Change status")
        Button ("Assign to")
        Button ("Delete")
        SelectedCount ("3 selected")
    Suspense boundary
      TaskTable (client component -- "use client" for sorting, selection, inline edit)
        TableHeader (sortable columns)
          SortableColumnHeader ("Title")
          SortableColumnHeader ("Status")
          SortableColumnHeader ("Priority")
          SortableColumnHeader ("Assignee")
          SortableColumnHeader ("Due Date")
          SortableColumnHeader ("Created")
        TableBody
          TaskTableRow x N
            Checkbox (select)
            TitleCell (click to open panel)
            StatusCell (inline dropdown -- click to change)
            PriorityCell (inline dropdown -- click to change)
            AssigneeCell (avatar + name, inline dropdown)
            DueDateCell (date picker on click)
            CreatedCell (read-only timestamp)
        Pagination (client component)
          PageInfo ("Showing 1-25 of 142")
          ItemsPerPageSelect (10, 25, 50, 100)
          PrevButton
          PageNumbers
          NextButton
    TaskDetailPanel
```

**State Management:**
- `taskStore.tasks` -- same store as kanban (shared)
- `taskStore.selectedIds` -- Set of selected task IDs for bulk actions
- `taskStore.sortColumn`, `taskStore.sortDirection` -- current sort
- `taskStore.page`, `taskStore.pageSize` -- pagination
- Inline edits: optimistic update to store + API call

**Data Fetching:**
- Server component fetches: `GET /api/projects/[id]/tasks?page=1&limit=25&sort=createdAt&order=desc`
- Pagination triggers client-side fetches (or router.push with search params for server-side)
- Sorting can be client-side for small datasets, server-side for large ones
- WebSocket updates same as kanban

**Loading Skeleton:**
```
+--+---------------------------+--------+--------+--------+--------+--------+
|  | Title                     | Status | Prior. | Assign | Due    | Created|
+--+---------------------------+--------+--------+--------+--------+--------+
|  | [================]        | [====] | [====] | [==]   | [====] | [====] |
|  | [================]        | [====] | [====] | [==]   | [====] | [====] |
|  | [================]        | [====] | [====] | [==]   | [====] | [====] |
|  | [================]        | [====] | [====] | [==]   | [====] | [====] |
|  | [================]        | [====] | [====] | [==]   | [====] | [====] |
+--+---------------------------+--------+--------+--------+--------+--------+
```
8 skeleton rows with shimmer.

**Error States:**
- Table fails to load: error card with retry
- Inline edit fails: toast + revert cell value
- Bulk action fails: toast "Failed to update 2 of 3 tasks" with details
- Empty state: "No tasks yet" illustration + "Create a task" button

**User Interactions:**
1. Click column header -> sort ascending, click again -> descending, third click -> clear sort
2. Click checkbox on row -> add to selection, show BulkActionBar
3. Click "Select all" -> select all visible rows
4. Bulk action -> confirmation dialog for destructive actions (delete)
5. Click status/priority cell -> inline dropdown, select new value -> optimistic update
6. Click assignee cell -> member dropdown -> assign
7. Click due date cell -> date picker popover
8. Click task title -> open TaskDetailPanel
9. Click page number or next/prev -> load that page
10. Change items per page -> reload from page 1

---

### 4.9 Task Detail Panel (Slide-Over)

**Not a page -- a client component rendered in the app layout.**

**Route:** No dedicated route. Triggered by setting `uiStore.selectedTaskId`. URL does NOT change (it is a panel, not a page).

**Component Hierarchy:**
```
TaskDetailPanel (client component -- "use client", fixed right, z-50)
  PanelOverlay (click to close, opacity transition)
  PanelContainer (slide-in from right, w-[480px] desktop, full-width mobile)
    PanelHeader
      TaskIdentifier (#PRJ-123)
      Button (close X)
      Button (open full page -- future)
      DropdownMenu (more: copy link, delete)
    PanelBody (scrollable)
      TitleEditor (inline editable h2)
      FieldGrid (2-column grid)
        StatusField (dropdown)
        PriorityField (dropdown)
        AssigneeField (member dropdown with avatar)
        DueDateField (date picker)
        LabelsField (multi-select tag picker)
      Separator
      DescriptionEditor (client component -- markdown editor)
        MarkdownToolbar (bold, italic, code, link, list, heading)
        TextArea (auto-resizing)
        PreviewToggle
      Separator
      SubTasksSection
        SubTaskList
          SubTaskItem x N
            Checkbox (toggle completion)
            SubTaskTitle (inline editable)
            DeleteButton (X)
        AddSubTaskInput (inline input + Enter to add)
        ProgressBar (completed / total)
      Separator
      CommentsSection
        CommentList
          CommentItem x N
            Avatar
            AuthorName
            Timestamp
            CommentBody (markdown rendered)
            EditButton (if own comment)
            DeleteButton (if own comment)
        CommentForm
          TextArea
          Button ("Comment")
      Separator
      ActivityLog
        ActivityItem x N (status changes, assignments, etc.)
          Avatar
          Description ("John changed status to In Progress")
          Timestamp
    PanelFooter
      CreatedAt timestamp
      UpdatedAt timestamp
```

**State Management:**
- `uiStore.selectedTaskId` -- which task is open (null = closed)
- `taskStore` -- read task data from store by ID
- Local state for description editor (draft), comment form
- Optimistic updates for all field changes (status, priority, assignee, etc.)

**Data Fetching:**
- On open: fetch full task detail if not already in store: `GET /api/tasks/[id]` (includes comments, subtasks, activity)
- Comments loaded with task, paginated if > 20
- All mutations via API calls with optimistic UI:
  - `PATCH /api/tasks/[id]` (field updates)
  - `POST /api/tasks/[id]/comments` (add comment)
  - `POST /api/tasks/[id]/subtasks` (add subtask)
  - `PATCH /api/tasks/[id]/subtasks/[subId]` (toggle subtask)
  - `DELETE /api/tasks/[id]` (delete task)

**Loading State:**
- Panel slides in immediately with skeleton content
- Title skeleton: one wide line
- Fields skeleton: 2x3 grid of small rectangles
- Description skeleton: 4 lines of varying width
- Comments skeleton: 3 comment blocks (avatar circle + lines)

**Error States:**
- Task not found: "This task no longer exists" + close button
- Field update fails: toast + revert to previous value
- Comment fails to post: toast, keep comment text in form
- Network error: toast "Could not load task details" + retry button

**User Interactions:**
1. Click task (from kanban card, list row, my tasks, search) -> panel slides in from right (300ms ease)
2. Click overlay or X button or press Escape -> panel slides out
3. Click any field -> dropdown/picker opens -> select value -> instant update
4. Click title -> inline edit mode -> type -> blur or Enter to save
5. Type in description editor -> auto-save after 1s debounce
6. Toggle markdown preview
7. Click subtask checkbox -> toggle completion with animation
8. Type in "Add subtask" input -> Enter to create
9. Type comment -> click "Comment" or Cmd+Enter to submit
10. Click delete on comment -> confirmation dialog -> delete
11. Scroll within panel (panel body is independently scrollable)
12. On mobile: panel is full-screen with back button

---

### 4.10 Analytics Page -- `/analytics`

**Route:** `(app)/analytics/page.tsx`

**Component Hierarchy:**
```
AppLayout
  AnalyticsPage (server component)
    PageHeader ("Analytics")
    AnalyticsToolbar (client component -- "use client")
      ProjectFilter (dropdown -- all projects or specific)
      DateRangeSelector (last 7d, 30d, 90d, custom)
    Suspense boundary
      AnalyticsGrid (server component -- fetches analytics data)
        StatsRow (server component)
          StatCard x 4 (total tasks, completed this week, avg completion time, overdue count)
        ChartGrid (client component wrapper -- "use client" for Recharts)
          AreaChartCard ("Tasks Completed Over Time")
            AreaChartWrapper (Recharts)
          DonutChartCard ("Tasks by Status")
            DonutChartWrapper (Recharts)
          BarChartCard ("Priority Distribution")
            BarChartWrapper (Recharts)
          LineChartCard ("Team Velocity")
            LineChartWrapper (Recharts)
```

**State Management:**
- Toolbar filters stored in URL search params (sharable, bookmark-able)
- `useSearchParams()` to read filters
- Chart data: fetched server-side based on params, no client-side store needed
- Recharts components are client-only (they use DOM/SVG)

**Data Fetching:**
- Server component fetches: `GET /api/analytics?projectId=all&range=30d`
- Returns pre-aggregated data from backend
- Charts receive data as props from server component
- No real-time updates needed (analytics are point-in-time)

**Loading Skeleton:**
```
+------+ +------+ +------+ +------+
| stat | | stat | | stat | | stat |   <- 4 stat card skeletons
+------+ +------+ +------+ +------+

+-------------------+  +-------------------+
|                   |  |                   |
|   Area chart      |  |   Donut chart     |   <- chart area skeletons
|   skeleton        |  |   skeleton        |       (gray rectangles with
|                   |  |                   |        rounded shapes)
+-------------------+  +-------------------+

+-------------------+  +-------------------+
|                   |  |                   |
|   Bar chart       |  |   Line chart      |
|   skeleton        |  |   skeleton        |
|                   |  |                   |
+-------------------+  +-------------------+
```

**Error States:**
- Individual chart error boundaries: "Could not load chart" + retry per card
- Full analytics error: "Analytics unavailable" with retry
- No data: "Not enough data yet" illustration with suggestion to create tasks

**User Interactions:**
1. Select project from dropdown -> URL param updates -> server re-fetches -> charts re-render
2. Select date range -> same flow
3. Hover chart data points -> tooltip with value
4. Click chart legend items -> toggle series visibility
5. Charts animate on initial load (Recharts enter animations)

---

### 4.11 Profile / Settings -- `/settings`

**Route:** `(app)/settings/page.tsx`

**Component Hierarchy:**
```
AppLayout
  SettingsPage (server component -- fetches user profile)
    PageHeader ("Settings")
    SettingsTabs (client component -- "use client")
      Tab ("Profile")
      Tab ("Appearance")
      Tab ("Notifications") -- future
    TabContent
      ProfileSection (client component -- "use client")
        AvatarUpload (click to change, drag-drop)
        Input (full name)
        Input (email -- read only or changeable)
        Button ("Save changes")
        Separator
        DangerZone
          Button ("Delete account") -> confirmation dialog
      AppearanceSection (client component -- "use client")
        ThemeSelector
          RadioGroup (Light / Dark / System)
        Separator
        SidebarDensity (future: compact/comfortable)
```

**State Management:**
- `authStore.user` -- current user profile
- Local form state for edits
- `uiStore.theme` -- light/dark/system
- Theme persisted in localStorage + cookie (for SSR consistency)

**Data Fetching:**
- Server component fetches: `GET /api/users/me`
- Mutations: `PATCH /api/users/me` (profile update), `DELETE /api/users/me` (account deletion)
- Avatar upload: `POST /api/users/me/avatar` (multipart form data)

**Loading Skeleton:** Form fields with input skeletons, avatar circle skeleton.

**Error States:**
- Profile load fails: error card with retry
- Save fails: toast "Could not save changes"
- Avatar upload fails: toast + revert preview
- Delete account: multi-step confirmation (type "DELETE" to confirm)

**User Interactions:**
1. Edit name -> click "Save changes" -> toast "Profile updated"
2. Click avatar -> file picker -> preview -> auto-upload -> toast
3. Toggle theme -> instant switch with CSS transition (no flash)
4. Delete account -> dialog -> type confirmation -> redirect to /login

---

## 5. Shared Components Catalog

### 5.1 Layout Components

| Component | File | Type | Description |
|-----------|------|------|-------------|
| `Sidebar` | `components/layout/sidebar.tsx` | Client | Collapsible nav with project list, nav links, user menu. Uses `uiStore.sidebarCollapsed`. |
| `SidebarNavItem` | `components/layout/sidebar-nav-item.tsx` | Client | Single nav item: icon + label, active state from `usePathname()`. |
| `SidebarProjectList` | `components/layout/sidebar-project-list.tsx` | Client | Scrollable project list in sidebar with color dots. |
| `TopBar` | `components/layout/top-bar.tsx` | Client | Breadcrumbs, search trigger (Cmd+K), notifications bell, user avatar dropdown. |
| `MobileNav` | `components/layout/mobile-nav.tsx` | Client | Fixed bottom nav bar (visible < md breakpoint): Home, Projects, Search, Settings. |
| `PageWrapper` | `components/layout/page-wrapper.tsx` | Server | Consistent page padding, max-width, heading slot. |

**Sidebar Detail:**
```
Sidebar (client -- "use client")
  SidebarHeader
    Logo / App name
    CollapseToggle (hamburger icon)
  SidebarNav
    SidebarNavItem (Home / Dashboard)     icon: LayoutDashboard
    SidebarNavItem (Projects)             icon: FolderKanban
    SidebarNavItem (Analytics)            icon: BarChart3
    Separator
    SidebarProjectList
      SidebarProjectItem x N              icon: colored dot + project name
    AddProjectButton                      icon: Plus
  SidebarFooter
    ThemeToggle (sun/moon icon)
    UserMenu (avatar + dropdown: settings, logout)
```

**Responsive Behavior:**
- Desktop (>= 1024px): Sidebar always visible, 240px width. Can collapse to 60px (icons only).
- Tablet (768-1023px): Sidebar collapsed by default (60px). Expand on hover or toggle.
- Mobile (< 768px): Sidebar hidden. Bottom nav replaces it. Sidebar accessible via hamburger in TopBar (slides over as drawer).

### 5.2 Kanban Components

| Component | File | Type | Description |
|-----------|------|------|-------------|
| `KanbanBoard` | `components/kanban/board.tsx` | Client | Horizontal scrollable container, DndContext provider, manages drag state. |
| `KanbanColumn` | `components/kanban/column.tsx` | Client | Droppable zone, column header with status + count, card list, add-card slot. |
| `KanbanCard` | `components/kanban/card.tsx` | Client | Draggable card: title, priority badge, assignee avatar, due date, labels. Click opens panel. |
| `AddCardForm` | `components/kanban/add-card-form.tsx` | Client | Inline form at bottom of column: title input + save/cancel buttons. |
| `DragOverlay` | `components/kanban/drag-overlay.tsx` | Client | Ghost card shown during drag (slightly rotated, elevated shadow). |

**Drag-and-Drop Library:** `@dnd-kit/core` + `@dnd-kit/sortable`
- Chosen over `react-beautiful-dnd` (deprecated) and `react-dnd` (heavier API)
- Supports keyboard DnD for accessibility
- Smooth animations via CSS transforms

### 5.3 List/Table Components

| Component | File | Type | Description |
|-----------|------|------|-------------|
| `TaskTable` | `components/list/task-table.tsx` | Client | Full table with sortable headers, selectable rows, inline editing. |
| `SortableColumnHeader` | `components/list/sortable-column-header.tsx` | Client | Column header with sort arrows, click to cycle sort direction. |
| `TaskTableRow` | `components/list/task-table-row.tsx` | Client | Single row with checkbox, inline-editable cells. |
| `BulkActionBar` | `components/list/bulk-action-bar.tsx` | Client | Sticky bar above table when rows selected: actions + count. |
| `Pagination` | `components/list/pagination.tsx` | Client | Page numbers, prev/next, items-per-page selector. |

### 5.4 Task Detail Components

| Component | File | Type | Description |
|-----------|------|------|-------------|
| `TaskDetailPanel` | `components/task-detail/panel.tsx` | Client | Slide-over container: overlay + panel + scroll body. |
| `TitleEditor` | `components/task-detail/title-editor.tsx` | Client | Inline editable heading, blur/enter to save. |
| `FieldGrid` | `components/task-detail/field-grid.tsx` | Client | 2-column grid of task metadata fields. |
| `DescriptionEditor` | `components/task-detail/description-editor.tsx` | Client | Markdown editor with toolbar, preview toggle, auto-save. |
| `SubTasksSection` | `components/task-detail/subtasks-section.tsx` | Client | Subtask list with checkboxes, add input, progress bar. |
| `CommentsSection` | `components/task-detail/comments-section.tsx` | Client | Comment list + comment form. |
| `ActivityLog` | `components/task-detail/activity-log.tsx` | Client | Chronological list of task changes. |

**Markdown Editor Choice:** `@uiw/react-md-editor` or custom with `textarea` + `react-markdown` for preview.

### 5.5 Search / Command Palette

| Component | File | Type | Description |
|-----------|------|------|-------------|
| `CommandPalette` | `components/search/command-palette.tsx` | Client | Dialog triggered by Cmd+K. Input + result list. Uses shadcn `Command` component (built on cmdk). |
| `SearchResults` | `components/search/search-results.tsx` | Client | Grouped results: Tasks, Projects, Members. |
| `SearchResultItem` | `components/search/search-result-item.tsx` | Client | Single result row: icon + title + subtitle + action. |

**Implementation:** shadcn/ui `<Command>` component wraps `cmdk` library.

**Component Hierarchy:**
```
CommandPalette (client -- "use client", Dialog)
  CommandInput (search input, auto-focused)
  CommandList
    CommandEmpty ("No results found")
    CommandGroup ("Tasks")
      CommandItem x N (task title, project name, status badge)
    CommandGroup ("Projects")
      CommandItem x N (project name, task count)
    CommandGroup ("Members")
      CommandItem x N (avatar, name, email)
    Separator
    CommandGroup ("Actions")
      CommandItem ("Create new task"      shortcut: N)
      CommandItem ("Switch to board view" shortcut: B)
      CommandItem ("Switch to list view"  shortcut: L)
```

**Data Fetching:**
- Debounced search (300ms): `GET /api/search?q={query}`
- Results streamed as user types
- Recent searches stored in localStorage

### 5.6 Common / Primitive Components

All sourced from or built on top of shadcn/ui:

| Component | Source | Type | Notes |
|-----------|--------|------|-------|
| `Button` | shadcn/ui | Client | Variants: default, destructive, outline, secondary, ghost, link. Sizes: default, sm, lg, icon. |
| `Input` | shadcn/ui | Client | Standard text input with label and error message slots. |
| `Textarea` | shadcn/ui | Client | Auto-resizing textarea. |
| `Select` | shadcn/ui | Client | Dropdown select with search. |
| `Dialog` | shadcn/ui | Client | Modal dialog with overlay. |
| `Sheet` | shadcn/ui | Client | Slide-over panel (used for TaskDetailPanel). |
| `DropdownMenu` | shadcn/ui | Client | Context menus, action menus. |
| `Popover` | shadcn/ui | Client | Floating content (date pickers, color pickers). |
| `Tooltip` | shadcn/ui | Client | Hover tooltips. |
| `Checkbox` | shadcn/ui | Client | With label support. |
| `Badge` | shadcn/ui | Server/Client | Status and priority badges. Can be server component when non-interactive. |
| `Avatar` | shadcn/ui | Server/Client | User avatars with fallback initials. |
| `Separator` | shadcn/ui | Server | Horizontal/vertical dividers. |
| `Skeleton` | shadcn/ui | Server | Shimmer loading placeholders. |
| `Toast` / `Toaster` | shadcn/ui (sonner) | Client | Toast notifications via `sonner`. |
| `Calendar` | shadcn/ui | Client | Date picker calendar. |
| `Tabs` | shadcn/ui | Client | Tab navigation. |
| `Table` | shadcn/ui | Client | Table primitives. |
| `Card` | shadcn/ui | Server/Client | Card container. |
| `ScrollArea` | shadcn/ui | Client | Custom scrollbar areas. |
| `Form` | shadcn/ui + react-hook-form | Client | Form wrapper with Zod validation integration. |

Custom components built on primitives:

| Component | File | Type | Description |
|-----------|------|------|-------------|
| `PriorityBadge` | `components/common/priority-badge.tsx` | Server | Color-coded badge: Urgent(red), High(orange), Medium(yellow), Low(blue), None(gray). |
| `StatusBadge` | `components/common/status-badge.tsx` | Server | Color-coded badge for task status. |
| `DueDateBadge` | `components/common/due-date-badge.tsx` | Server | Shows relative date. Red if overdue, yellow if due today. |
| `AvatarStack` | `components/common/avatar-stack.tsx` | Server | Overlapping avatar circles with "+N" overflow. |
| `EmptyState` | `components/common/empty-state.tsx` | Server | Illustration + title + description + CTA button. |
| `CircularProgress` | `components/common/circular-progress.tsx` | Client | SVG ring for project completion percentage. |
| `PresenceIndicator` | `components/common/presence-indicator.tsx` | Client | Green/gray dot for online status. |

### 5.7 Chart Components

All chart components are client components (Recharts uses DOM).

| Component | File | Description |
|-----------|------|-------------|
| `AreaChartCard` | `components/charts/area-chart-card.tsx` | Card wrapper + Recharts `AreaChart`. Gradient fill, tooltip, responsive. |
| `DonutChartCard` | `components/charts/donut-chart-card.tsx` | Card wrapper + Recharts `PieChart` (donut). Legend, tooltip, label. |
| `BarChartCard` | `components/charts/bar-chart-card.tsx` | Card wrapper + Recharts `BarChart`. Grouped/stacked support. |
| `LineChartCard` | `components/charts/line-chart-card.tsx` | Card wrapper + Recharts `LineChart`. Multi-series, dot markers. |
| `ChartTooltip` | `components/charts/chart-tooltip.tsx` | Custom tooltip component for consistent styling. |
| `ChartLegend` | `components/charts/chart-legend.tsx` | Custom legend with clickable items to toggle series. |

### 5.8 Theme Toggle

```
ThemeToggle (client component -- "use client")
  Uses next-themes ThemeProvider (wraps entire app in root layout)
  Button with sun/moon icon
  Click cycles: light -> dark -> system
  Keyboard: accessible via Tab + Enter
  Transition: CSS transition on all color custom properties (150ms)
```

**Implementation:**
- `next-themes` library for SSR-safe theme detection
- `ThemeProvider` in root layout with `attribute="class"` (Tailwind dark mode)
- Cookie-based theme persistence for SSR (avoids flash)
- All colors via CSS custom properties that swap on `.dark` class

---

## 6. State Management Architecture

### Store Design (Zustand)

**Principle:** Per-request stores on the server, singleton stores on the client. Stores live in `src/stores/` (outside `app/`). All stores are client-only.

```typescript
// stores/auth-store.ts
interface AuthStore {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginInput) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
  setUser: (user: User) => void;
}

// stores/task-store.ts
interface TaskStore {
  tasks: Record<string, Task>;          // taskId -> Task (normalized)
  tasksByProject: Record<string, string[]>;  // projectId -> taskId[]
  selectedTaskId: string | null;
  filters: TaskFilters;
  sortBy: SortConfig;
  selectedIds: Set<string>;
  page: number;
  pageSize: number;

  // Actions
  setTasks: (projectId: string, tasks: Task[]) => void;
  addTask: (task: Task) => void;
  updateTask: (taskId: string, updates: Partial<Task>) => void;
  removeTask: (taskId: string) => void;
  moveTask: (taskId: string, newStatus: Status) => void;  // optimistic
  setFilters: (filters: Partial<TaskFilters>) => void;
  setSortBy: (sort: SortConfig) => void;
  toggleSelected: (taskId: string) => void;
  selectAll: (taskIds: string[]) => void;
  clearSelection: () => void;
  setSelectedTask: (taskId: string | null) => void;
}

// stores/project-store.ts
interface ProjectStore {
  projects: Record<string, Project>;
  currentProjectId: string | null;

  setProjects: (projects: Project[]) => void;
  addProject: (project: Project) => void;
  updateProject: (projectId: string, updates: Partial<Project>) => void;
  removeProject: (projectId: string) => void;
  setCurrentProject: (projectId: string) => void;
}

// stores/ui-store.ts
interface UIStore {
  sidebarCollapsed: boolean;
  commandPaletteOpen: boolean;
  theme: 'light' | 'dark' | 'system';

  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleCommandPalette: () => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
}

// stores/presence-store.ts
interface PresenceStore {
  onlineUsers: Record<string, { userId: string; name: string; avatar: string; lastSeen: Date }>;
  viewingBoard: string[];   // userIds viewing current board

  setOnlineUsers: (users: PresenceUser[]) => void;
  addOnlineUser: (user: PresenceUser) => void;
  removeOnlineUser: (userId: string) => void;
}
```

### Hydration Pattern

Server components fetch data and pass to client components as props. Client components hydrate Zustand stores on mount:

```typescript
// components/dashboard/app-initializer.tsx ("use client")
// Rendered once in (app)/layout.tsx
// Receives server-fetched user data as props
// Hydrates authStore on mount (non-blocking)
function AppInitializer({ user, projects }: { user: User; projects: Project[] }) {
  const setUser = useAuthStore((s) => s.setUser);
  const setProjects = useProjectStore((s) => s.setProjects);

  useEffect(() => {
    setUser(user);
    setProjects(projects);
  }, [user, projects]);

  return null; // renders nothing, just initializes stores
}
```

---

## 7. Data Fetching Strategy

### Decision Matrix

| What | Where | How | Cache |
|------|-------|-----|-------|
| User session | `(app)/layout.tsx` | Server component fetch with cookie | Per-request |
| Project list | `(app)/layout.tsx` (sidebar) | Server component fetch | 60s revalidate |
| Project detail | `[projectId]/layout.tsx` | Server component fetch | 60s revalidate |
| Task list (kanban/list) | `board/page.tsx`, `list/page.tsx` | Server component fetch -> pass to client | No cache (real-time) |
| Task detail | Client-side | `useEffect` fetch on panel open | Store cache |
| Analytics | `analytics/page.tsx` | Server component fetch | 5min revalidate |
| Search results | Client-side | Debounced fetch in CommandPalette | No cache |
| Activity feed | Client-side | Initial server fetch + WebSocket | No cache |
| Real-time updates | Client-side | WebSocket -> Zustand store | In-memory |

### Server Actions (Mutations)

```typescript
// All mutations go through server actions for type safety and progressive enhancement.

// app/(app)/actions/task-actions.ts
"use server"

export async function createTaskAction(formData: FormData): Promise<ActionResult<Task>> { ... }
export async function updateTaskAction(taskId: string, updates: Partial<Task>): Promise<ActionResult<Task>> { ... }
export async function deleteTaskAction(taskId: string): Promise<ActionResult<void>> { ... }
export async function moveTaskAction(taskId: string, newStatus: Status): Promise<ActionResult<Task>> { ... }
export async function bulkUpdateTasksAction(taskIds: string[], updates: Partial<Task>): Promise<ActionResult<Task[]>> { ... }

// app/(app)/actions/project-actions.ts
"use server"

export async function createProjectAction(formData: FormData): Promise<ActionResult<Project>> { ... }
export async function updateProjectAction(projectId: string, updates: Partial<Project>): Promise<ActionResult<Project>> { ... }
export async function deleteProjectAction(projectId: string): Promise<ActionResult<void>> { ... }
export async function inviteMemberAction(projectId: string, email: string, role: Role): Promise<ActionResult<void>> { ... }

// app/(app)/actions/comment-actions.ts
"use server"

export async function addCommentAction(taskId: string, content: string): Promise<ActionResult<Comment>> { ... }
export async function deleteCommentAction(commentId: string): Promise<ActionResult<void>> { ... }
```

### Optimistic Update Pattern

```typescript
// hooks/use-optimistic.ts
// Generic hook for optimistic mutations:
// 1. Immediately update Zustand store
// 2. Call server action / API
// 3. On success: confirm (no-op, store already updated)
// 4. On failure: rollback store to previous state + show error toast

function useOptimisticUpdate<T>(
  getCurrentState: () => T,
  setOptimisticState: (state: T) => void,
) {
  return async (
    optimisticState: T,
    serverAction: () => Promise<T>,
  ) => {
    const previousState = getCurrentState();
    setOptimisticState(optimisticState);
    try {
      const result = await serverAction();
      setOptimisticState(result); // server truth
    } catch (error) {
      setOptimisticState(previousState); // rollback
      toast.error("Action failed. Changes reverted.");
      throw error;
    }
  };
}
```

### WebSocket Integration

```typescript
// hooks/use-socket.ts
function useSocket() {
  // Connects to Socket.io server
  // Listens for events and updates Zustand stores:
  //
  //   "task:created"   -> taskStore.addTask(task)
  //   "task:updated"   -> taskStore.updateTask(id, updates)
  //   "task:deleted"   -> taskStore.removeTask(id)
  //   "task:moved"     -> taskStore.moveTask(id, newStatus)
  //   "project:updated"-> projectStore.updateProject(id, updates)
  //   "activity:new"   -> append to activity feed
  //   "presence:join"  -> presenceStore.addOnlineUser(user)
  //   "presence:leave" -> presenceStore.removeOnlineUser(userId)
  //
  // Emits:
  //   "presence:join"  -> on connect (with current user info)
  //   "board:viewing"  -> when user opens a board (for presence)
  //
  // Auto-reconnect with exponential backoff
  // Connection status exposed for UI indicators
}
```

---

## 8. User Interaction Flows

### Flow 1: New User Onboarding

```
/signup -> fill form -> submit -> server action validates ->
  backend creates user -> JWT set in cookie ->
  redirect to / (dashboard) -> dashboard loads empty state ->
  user sees "Create your first project" CTA ->
  clicks -> navigates to /projects/new -> fills form ->
  submit -> project created -> redirect to /projects/[id]/board ->
  sees empty kanban -> uses inline add-card to create first task
```

### Flow 2: Returning User Task Management

```
/ (dashboard) -> sees "My Tasks" with overdue highlighted ->
  clicks overdue task -> TaskDetailPanel opens ->
  changes status to "In Progress" -> optimistic update ->
  types update in comments -> submits -> comment appears ->
  closes panel -> navigates to project via sidebar ->
  /projects/[id]/board -> drags task from "In Progress" to "In Review" ->
  optimistic update -> teammate sees card move in real-time
```

### Flow 3: Bulk Task Management (List View)

```
/projects/[id]/list -> clicks column header to sort by priority ->
  table re-sorts -> selects 5 tasks via checkboxes ->
  BulkActionBar appears -> clicks "Change status" ->
  dropdown shows status options -> selects "Done" ->
  all 5 tasks update optimistically -> toast "5 tasks updated"
```

### Flow 4: Search and Navigate

```
Any page -> presses Cmd+K -> CommandPalette opens ->
  types "auth bug" -> debounced search fires ->
  results show: 2 tasks matching, 1 project ->
  uses arrow keys to navigate results -> Enter to select ->
  if task: TaskDetailPanel opens ->
  if project: navigates to /projects/[id]/board
```

### Flow 5: Real-Time Collaboration

```
User A on /projects/[id]/board -> User B opens same board ->
  User A sees User B's avatar in presence indicators ->
  User B drags "Fix auth" from "Todo" to "In Progress" ->
  WebSocket emits "task:moved" -> User A's board receives event ->
  Card animates from "Todo" column to "In Progress" column ->
  Activity feed shows "User B moved Fix auth to In Progress"
```

### Flow 6: Quick-Add from Dashboard

```
/ (dashboard) -> clicks quick-add input (or presses "N" shortcut) ->
  input focuses -> types task title -> selects project from dropdown ->
  presses Enter -> task created (POST to API) ->
  "My Tasks" section updates -> toast "Task created" ->
  optionally clicks task to open detail panel and add more info
```

### Flow 7: Analytics Review

```
Sidebar -> clicks "Analytics" -> /analytics ->
  default view: all projects, last 30 days ->
  4 stat cards load, 4 charts render with enter animations ->
  selects specific project from filter -> URL params update ->
  server re-fetches analytics -> charts animate to new data ->
  hovers on area chart -> tooltip shows date + task count ->
  notices velocity dip -> navigates to project to investigate
```

---

## 9. Server vs Client Component Boundaries

### Guiding Principles

1. **Default to server components** -- they ship zero JS to client
2. **Push "use client" to leaf nodes** -- keep the boundary as deep as possible
3. **Server components for data fetching** -- fetch in parent, pass data as props to client children
4. **Client components for interactivity** -- anything with state, effects, event handlers, or browser APIs

### Boundary Map

```
SERVER                              CLIENT ("use client")
------                              ---------------------
RootLayout                          ThemeProvider (next-themes)
  (auth)/Layout                     Toaster (sonner)
    LoginPage                       LoginForm
    SignupPage                      SignupForm
  (app)/Layout                      Sidebar
    DashboardPage                   SidebarNavItem
      ProjectCardGrid               SidebarProjectList
        ProjectCard                  TopBar
      MyTasks                        MobileNav
        TaskRow*                     AppInitializer
      ActivityFeed*                  SocketProvider
    ProjectsPage                     QuickAddTask
      ProjectGrid                    ActivityFeed (WebSocket)
    ProjectLayout                    TaskDetailPanel (entire panel)
      ProjectHeader
      ProjectTabs*                   KanbanBoard (entire board + cards)
    KanbanPage (shell)               BoardToolbar
    ListPage (shell)                 TaskTable (entire table)
      TaskTable*                     BulkActionBar
    AnalyticsPage                    Pagination
      StatsRow                       AreaChartCard (Recharts)
        StatCard                     DonutChartCard
      AnalyticsGrid (shell)          BarChartCard
    SettingsPage                     LineChartCard
      PageHeader                     AnalyticsToolbar
                                     ProfileSection
                                     AppearanceSection
                                     ThemeToggle
                                     CommandPalette (cmdk)
                                     CircularProgress

*  = These may be client components depending on interactivity needs,
     or server components that render client sub-components.
```

### Key Boundary Decisions

| Decision | Rationale |
|----------|-----------|
| `KanbanBoard` is fully client | DnD requires client-side DOM manipulation. Attempting to split columns as server components adds complexity with no benefit since all cards need to be draggable. |
| `TaskTable` is fully client | Row selection, inline editing, sorting all require state. |
| `ProjectCard` is server | It is read-only on the project grid. Click navigates via `<Link>`. No state needed. |
| `StatCard` is server | Static display of numbers. No interactivity. |
| Chart wrappers are client | Recharts uses SVG/DOM. Must be client. |
| `TaskDetailPanel` is fully client | Every element inside is interactive: editable fields, forms, markdown editor. |
| `Sidebar` is client | Collapse state, active route highlighting, click handlers. |
| `PageWrapper` is server | Just applies padding/layout. No interactivity. |
| `Badge` components are server | Pure display, no state. Can be imported by client components (they become client at that point). |

---

## 10. Loading and Error States

### Loading Strategy: Skeletons, Not Spinners

Every route segment has a `loading.tsx` that renders a skeleton matching the page layout. This provides instant visual structure while data loads.

**Skeleton Components:**

```typescript
// components/ui/skeleton.tsx (from shadcn/ui)
// Renders a div with shimmer animation:
//   bg-muted animate-pulse rounded-md

// Composed skeletons:
// components/common/skeletons/
//   project-card-skeleton.tsx    -- card shape with 3 text lines + progress bar
//   task-row-skeleton.tsx        -- table row with cells
//   kanban-card-skeleton.tsx     -- card with title + 2 badges
//   kanban-board-skeleton.tsx    -- 5 columns x 3 cards each
//   stat-card-skeleton.tsx       -- number + label
//   chart-skeleton.tsx           -- rectangular area with subtle shape
//   comment-skeleton.tsx         -- avatar + text lines
//   sidebar-skeleton.tsx         -- nav items + project list
```

**Suspense Boundaries:**

```
DashboardPage
  <Suspense fallback={<ProjectCardGridSkeleton />}>
    <ProjectCardGrid />
  </Suspense>
  <Suspense fallback={<MyTasksSkeleton />}>
    <MyTasks />
  </Suspense>
  <Suspense fallback={<ActivityFeedSkeleton />}>
    <ActivityFeed />
  </Suspense>
```

Each section loads independently -- the fastest section renders first, others stream in.

### Error Boundaries

```
// app/error.tsx -- global error boundary (client component)
// app/(app)/error.tsx -- app-level error boundary
// app/(app)/projects/[projectId]/error.tsx -- project-level error boundary

// Pattern for each error boundary:
function ErrorBoundary({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 p-8">
      <AlertCircle className="h-12 w-12 text-destructive" />
      <h2 className="text-lg font-semibold">Something went wrong</h2>
      <p className="text-muted-foreground text-sm">{error.message}</p>
      <Button onClick={reset}>Try again</Button>
    </div>
  );
}
```

**Error Granularity:**

| Scope | Boundary | Behavior |
|-------|----------|----------|
| Entire app crashes | `app/error.tsx` | Full-page error with "Go home" button |
| Auth fails | `(auth)/error.tsx` | "Authentication error" with retry |
| Dashboard section fails | Per-Suspense error boundary | Other sections still work, failed section shows retry |
| Project not found | `[projectId]/not-found.tsx` | "Project not found" page |
| Task mutation fails | Toast notification | Show error, rollback optimistic update |
| WebSocket disconnects | Banner at top of page | "Reconnecting..." with auto-retry |
| Search fails | Inline in CommandPalette | "Search unavailable" with retry |

---

## 11. Responsive Breakpoints

Following Tailwind defaults:

```
sm:  640px   -- small tablets
md:  768px   -- tablets
lg:  1024px  -- small desktops
xl:  1280px  -- desktops
2xl: 1536px  -- large desktops
```

### Layout Behavior Per Breakpoint

| Breakpoint | Sidebar | Navigation | Kanban | Table | Task Panel |
|------------|---------|------------|--------|-------|------------|
| < 768px (mobile) | Hidden (drawer) | Bottom nav bar | Single column, swipeable | Horizontal scroll or card view | Full-screen slide-up |
| 768-1023px (tablet) | Collapsed (60px, icons) | Top bar | Horizontal scroll, smaller cards | Full table, horizontal scroll | Half-screen slide-over (320px) |
| >= 1024px (desktop) | Full (240px) | Top bar | Full 5-column board | Full table | Side panel (480px) |

### Mobile-Specific Patterns

```
Mobile Kanban:
  - Single column visible at a time
  - Swipe left/right to change columns
  - Column indicator dots at top
  - Tap card to open full-screen detail
  - Long-press card for drag (or use move action in menu)

Mobile Table:
  - Switches to card-based list (not table)
  - Each card shows: title, status badge, priority badge, assignee
  - Tap to open detail
  - Swipe right to complete, swipe left to delete (with confirmation)

Mobile Navigation:
  - Bottom bar with 4 items: Home, Projects, Search, Profile
  - Each item: icon + label
  - Active item highlighted
  - Search opens full-screen command palette
```

---

## 12. Keyboard Shortcuts and Accessibility

### Global Shortcuts

| Shortcut | Action | Scope |
|----------|--------|-------|
| `Cmd/Ctrl + K` | Open command palette | Global |
| `N` | Create new task (opens quick-add) | Global (when no input focused) |
| `B` | Switch to board view | Project context |
| `L` | Switch to list view | Project context |
| `Escape` | Close panel / palette / modal | Global |
| `?` | Show keyboard shortcuts help | Global |

### Kanban Shortcuts

| Shortcut | Action |
|----------|--------|
| `Arrow keys` | Navigate between cards (when board focused) |
| `Enter` | Open selected card in detail panel |
| `Space` | Pick up / drop card (keyboard DnD) |

### Table Shortcuts

| Shortcut | Action |
|----------|--------|
| `Arrow Up/Down` | Navigate rows |
| `Space` | Toggle row selection |
| `Enter` | Open task detail |
| `Cmd/Ctrl + A` | Select all rows |
| `Delete/Backspace` | Delete selected (with confirmation) |

### Accessibility Requirements

- All interactive elements have `aria-label` or visible label
- Color is never the only indicator (badges have text, not just color)
- Focus management: focus trap in modals/panels, return focus on close
- Keyboard navigation for all DnD operations via `@dnd-kit`
- Screen reader announcements for drag operations ("Picked up task, over In Progress column")
- Skip-to-content link at top of page
- All images have alt text
- Minimum contrast ratio 4.5:1 (enforced by shadcn/ui defaults)
- Reduced motion: respect `prefers-reduced-motion` (disable animations)

---

## Summary: Component Count Estimates

| Category | Count |
|----------|-------|
| Route segments (pages) | 12 |
| Layout files | 4 |
| Loading files | 10 |
| Error boundaries | 5 |
| Layout components | 6 |
| Kanban components | 5 |
| List/Table components | 5 |
| Task Detail components | 7 |
| Search components | 3 |
| Chart components | 6 |
| Dashboard components | 5 |
| Project components | 5 |
| Auth components | 3 |
| Common/shared components | 8 |
| shadcn/ui primitives | ~20 |
| Custom hooks | 8 |
| Zustand stores | 5 |
| Skeleton components | 8+ |
| **Total unique components** | **~120** |

---

## Dependency Summary

```json
{
  "dependencies": {
    "next": "^14.x",
    "react": "^18.x",
    "typescript": "^5.x",
    "tailwindcss": "^3.x",
    "@radix-ui/*": "various (via shadcn/ui)",
    "class-variance-authority": "^0.7",
    "clsx": "^2.x",
    "tailwind-merge": "^2.x",
    "zustand": "^4.x",
    "@dnd-kit/core": "^6.x",
    "@dnd-kit/sortable": "^8.x",
    "@dnd-kit/utilities": "^3.x",
    "recharts": "^2.x",
    "react-markdown": "^9.x",
    "cmdk": "^0.2 (via shadcn Command)",
    "sonner": "^1.x (via shadcn Toaster)",
    "next-themes": "^0.3",
    "socket.io-client": "^4.x",
    "zod": "^3.x",
    "react-hook-form": "^7.x",
    "@hookform/resolvers": "^3.x",
    "date-fns": "^3.x",
    "lucide-react": "^0.x (icons)"
  }
}
```
