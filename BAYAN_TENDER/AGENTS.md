# Repository Guidelines

## Project Structure & Module Organization
- `backend/`: .NET 8 solution (`Bayan.sln`) with layered projects: `Bayan.API`, `Bayan.Application`, `Bayan.Domain`, `Bayan.Infrastructure`, and `Bayan.Tests`.
- `frontend/`: Angular 18 app (`src/app/core`, `src/app/features`, `src/app/shared`, `src/app/layout`).
- `e2e/`: Playwright end-to-end suite (`tests/`, `fixtures/`, `global-setup.ts`).
- `docker/`: nginx and DB init assets used by local/prod compose files.
- `scripts/`: helper automation (Docker utilities, data setup, verification scripts).

## Build, Test, and Development Commands
- `powershell ./scripts/docker-dev.ps1 start`: start full stack (API `:5000`, UI `:4200` via `ui-prod`, UI dev `:4201` via `ui`).
- `powershell ./scripts/docker-dev.ps1 logs [service]`: tail logs (e.g., `api`, `ui`, `ui-prod`, `db`).
- `powershell ./scripts/docker-dev.ps1 stop`: stop the stack.
- `cd backend && dotnet restore && dotnet build Bayan.sln`: restore and compile backend.
- `cd backend && dotnet watch --project Bayan.API/Bayan.API.csproj run`: run API with hot reload.
- `cd backend && dotnet test Bayan.Tests/Bayan.Tests.csproj`: run backend unit/integration tests.
- `cd frontend && npm install && npm start`: run Angular dev server (`http://localhost:4200` is the docker `ui-prod` build).
- `cd frontend && npm run build`: production frontend build.
- `cd frontend && npm test -- --watch=false --code-coverage`: frontend unit tests with coverage.
- `cd e2e && npm test`: execute Playwright suite.

## Coding Style & Naming Conventions
- Frontend follows `frontend/.editorconfig`: UTF-8, spaces, 2-space indent, trailing whitespace trimmed, single quotes in `*.ts`.
- Use Angular naming conventions: `feature-name.component.ts`, `*.service.ts`, `*.guard.ts`, and colocated `*.spec.ts`.
- Backend uses C# conventions: PascalCase for types/methods, camelCase for locals/parameters, and nullable reference safety (`<Nullable>enable</Nullable>`).
- Keep business logic in `Bayan.Application/Features/*`; keep controllers thin in `Bayan.API/Controllers`.

## Testing Guidelines
- Backend: xUnit + FluentAssertions + Moq under `backend/Bayan.Tests` with `*Tests.cs` naming.
- Frontend: Jasmine/Karma specs named `*.spec.ts` next to source where practical.
- E2E: Playwright specs in `e2e/tests` (role-based projects configured in `playwright.config.ts`).
- No enforced global coverage gate is defined; maintain or improve coverage for touched code and add regression tests for bug fixes.

## Commit & Pull Request Guidelines
- Follow the repository's observed Conventional Commit style: `feat:`, `fix:`, `docs:`, `revert:` (optional scope encouraged, e.g., `fix(portal): ...`).
- Keep commits focused and descriptive of behavior changes.
- PRs should include: a concise summary, linked issue/ticket (if any), validation steps/command results, and screenshots for UI changes.
- Highlight schema or seed changes explicitly when touching `backend/Bayan.Infrastructure/Data/Migrations` or startup data.

