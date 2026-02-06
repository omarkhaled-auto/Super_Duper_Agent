# Bayan Tender Management System

A comprehensive tender management platform for end-to-end procurement lifecycle management — from tender creation and bidder qualification through commercial/technical evaluation to award approval.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | .NET 8, ASP.NET Core Web API, Entity Framework Core 8 |
| Frontend | Angular 18, PrimeNG, AG Grid, Tailwind CSS |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Object Storage | MinIO (S3-compatible) |
| Background Jobs | Hangfire |
| Email | SMTP (MailHog for development) |
| Auth | JWT with refresh tokens |

## Quick Start (Docker)

```bash
# Clone the repository
git clone <repo-url> && cd BAYAN_TENDER

# Start all services
docker compose up -d

# Services will be available at:
# Frontend:  http://localhost:4200
# API:       http://localhost:5000
# Swagger:   http://localhost:5000/swagger
# MailHog:   http://localhost:8025
# MinIO:     http://localhost:9001
```

The database is automatically migrated and seeded on first startup in Development mode.

## Local Development

### Prerequisites

- .NET 8 SDK
- Node.js 20+
- PostgreSQL 16
- Redis 7

### Backend

```bash
cd backend
dotnet restore
dotnet build

# Run with hot-reload
dotnet watch run --project Bayan.API
```

### Frontend

```bash
cd frontend
npm install
ng serve
```

## Project Structure

```
BAYAN_TENDER/
├── backend/
│   ├── Bayan.API/              # Controllers, middleware, Program.cs
│   ├── Bayan.Application/      # CQRS commands/queries, DTOs, validators
│   ├── Bayan.Domain/           # Entities, enums, value objects
│   ├── Bayan.Infrastructure/   # EF Core, external services, identity
│   └── Bayan.Tests/            # Unit and integration tests
├── frontend/
│   └── src/app/
│       ├── core/               # Auth, guards, interceptors, models, services
│       ├── features/           # Feature modules (tenders, dashboard, admin)
│       ├── shared/             # Shared components, pipes, directives
│       └── layout/             # App layout, sidebar, header
├── docker-compose.yml
└── README.md
```

## Demo Users

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@bayan.ae | Admin@123 |
| Tender Manager | manager@bayan.ae | Manager@123 |
| Commercial Analyst | analyst@bayan.ae | Analyst@123 |
| Approver | approver@bayan.ae | Approver@123 |
| Auditor | auditor@bayan.ae | Auditor@123 |
| Technical Panelist | panelist@bayan.ae | Panelist@123 |

## Running Tests

### Backend Tests

```bash
cd backend
dotnet test Bayan.Tests
```

### Frontend Tests

```bash
cd frontend
ng test --no-watch --code-coverage
```

## API Documentation

Swagger UI is available at `/swagger` when running in Development mode. The API follows RESTful conventions with consistent `ApiResponse<T>` envelope:

```json
{
  "success": true,
  "data": { ... },
  "message": null,
  "errors": []
}
```

## Key Features

- **Tender Lifecycle**: Draft → Published → Active → Evaluation → Awarded
- **BOQ Management**: Hierarchical sections/items with Excel import/export
- **Bid Management**: Multi-step import (parse → map → match → normalize → validate → execute)
- **Clarification Workflow**: Q&A with bulletin publishing and PDF generation
- **Evaluation Engine**: Commercial scoring, technical panels, combined scorecards, sensitivity analysis
- **Approval Workflow**: Multi-level approval chains with delegation
- **Audit Trail**: Full audit logging via MediatR pipeline behavior
- **Role-Based Access**: 7 roles with granular permissions per endpoint
- **Bilingual**: Arabic/English support throughout
