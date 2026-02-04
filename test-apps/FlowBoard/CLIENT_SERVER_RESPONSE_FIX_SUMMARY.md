# Client-Server Response Mismatch Fix Summary

## Problem
Client hooks expected API responses wrapped in `res.data` but the server returns data with different field names and no wrapper.

## Server Response Formats (Actual)

### Task Routes
- `POST /api/projects/:projectId/tasks` → `Task` (direct)
- `GET /api/projects/:projectId/tasks` → `{ tasks, total, page, limit, totalPages }`
- `GET /api/tasks/:id` → `Task` (direct)
- `PUT /api/tasks/:id` → `Task` (direct)
- `DELETE /api/tasks/:id` → `{ deleted: true }`
- `PUT /api/tasks/:id/reorder` → `Task` (direct)
- `POST /api/tasks/:id/subtasks` → `SubTask` (direct)
- `POST /api/tasks/:id/comments` → `Comment` (direct)
- `GET /api/tasks/:id/comments` → `Comment[]` (direct)
- `GET /api/tasks/:id/activity` → `ActivityEvent[]` (direct)

### Project Routes
- `POST /api/projects` → `Project` (direct)
- `GET /api/projects` → `Project[]` (direct)
- `GET /api/projects/:id` → `Project` (direct)
- `PUT /api/projects/:id` → `Project` (direct)
- `GET /api/projects/:id/members` → `ProjectMember[]` (direct)
- `POST /api/projects/:id/members` → `ProjectMember` (direct)
- `PUT /api/projects/:id/members/:userId` → `ProjectMember` (direct)
- `GET /api/projects/:id/labels` → `Label[]` (direct)
- `POST /api/projects/:id/labels` → `Label` (direct)

### Activity Routes
- `GET /api/activity/me` → `ActivityEvent[]` (direct)
- `GET /api/activity/tasks/:id` → `ActivityEvent[]` (direct)
- `GET /api/activity/projects/:id` → `ActivityEvent[]` (direct)

## Files Fixed

### 1. client/src/hooks/use-tasks.ts
- Changed `TasksResponse` interface from `{ data, meta }` to `{ tasks, total, page, limit, totalPages }`
- Changed `res.data` → `res.tasks`
- Changed `res.meta?.total` → `res.total`

### 2. client/src/hooks/use-task-detail.ts
- Changed `api.get<{ data: Task }>` → `api.get<Task>`
- Changed `res.data` → `res` (7 occurrences)
- Fixed: fetchTask, fetchComments, fetchActivities, fetchProjectLabels, updateField, addComment, addSubTask, createLabel

### 3. client/src/hooks/use-table-tasks.ts
- Changed `TasksResponse` interface from `{ data, meta }` to `{ tasks, total, page, limit, totalPages }`
- Changed `res.data` → `res.tasks`
- Changed `res.meta?.total` → `res.total`

### 4. client/src/hooks/use-members.ts
- Changed `api.get<{ data: ProjectMember[] }>` → `api.get<ProjectMember[]>`
- Changed `api.post<{ data: ProjectMember }>` → `api.post<ProjectMember>`
- Changed `api.patch<{ data: ProjectMember }>` → `api.patch<ProjectMember>`
- Changed `res.data` → `res` (3 occurrences)

### 5. client/src/hooks/use-project.ts
- Changed `api.get<{ data: Project }>` → `api.get<Project>`
- Changed `res.data` → `res`

### 6. client/src/hooks/use-board.ts
- Changed `TasksResponse` interface from `{ data, meta }` to `{ tasks, total, page, limit, totalPages }`
- Changed `res.data` → `res.tasks`

### 7. client/src/hooks/use-projects.ts
- Removed `ProjectsResponse` interface wrapper
- Changed `api.get<ProjectsResponse>` → `api.get<Project[]>`
- Changed `res.data` → `res`

### 8. client/src/hooks/use-search.ts
- Removed `SearchResponse` interface wrapper
- Changed `api.get<SearchResponse>` → `api.get<SearchResults>`
- Changed `res.data` → `res`

### 9. client/src/hooks/use-analytics.ts
- Removed `AnalyticsResponse` interface wrapper
- Changed `api.get<AnalyticsResponse>` → `api.get<AnalyticsData>`
- Changed `res.data` → `res`

### 10. client/src/contexts/project-context.tsx
- Changed `api.get<{ data: Project; member: ProjectMember }>` → `api.get<Project>`
- Changed `res.data` → `res`
- Added TODO for determining current member from response

### 11. client/src/app/(dashboard)/projects/[projectId]/settings/page.tsx
- Changed `api.patch<{ data: Project }>` → `api.patch<Project>`
- Changed `res.data` → `res`

### 12. client/src/components/board/add-task-inline.tsx
- Removed `CreateTaskResponse` interface wrapper
- Changed `api.post<CreateTaskResponse>` → `api.post<Task>`
- Changed `res.data` → `res`

## Pattern Summary

### Before (Incorrect):
```typescript
const res = await api.get<{ data: Task[] }>("/endpoint");
setTasks(res.data);
```

### After (Correct):
```typescript
const res = await api.get<Task[]>("/endpoint");
setTasks(res);
```

### Special Case - Paginated Lists:
```typescript
// Before
interface Response { data: Task[]; meta: { total, page, limit } }

// After
interface Response { tasks: Task[]; total: number; page: number; limit: number; totalPages: number }
```

## Testing Checklist
- [ ] Task list loading
- [ ] Task detail view
- [ ] Task creation
- [ ] Task editing
- [ ] Comments loading/creation
- [ ] Activity log
- [ ] Project list
- [ ] Project detail
- [ ] Project settings
- [ ] Members management
- [ ] Labels management
- [ ] Search functionality
- [ ] Analytics page
- [ ] Board view
- [ ] Table view

## Known Issues
- `project-context.tsx` needs logic to determine current member from the Project response (members array)
