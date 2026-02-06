# =============================================================================
# Bayan Tender Management System - Docker Development Script (PowerShell)
# =============================================================================

param(
    [Parameter(Position=0)]
    [string]$Command = "help",

    [Parameter(Position=1)]
    [string]$Arg1
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

function Write-Header {
    Write-Host "================================================" -ForegroundColor Blue
    Write-Host "  Bayan Tender Management System - Docker" -ForegroundColor Blue
    Write-Host "================================================" -ForegroundColor Blue
}

function Write-Success { param([string]$Message) Write-Host "[SUCCESS] $Message" -ForegroundColor Green }
function Write-Warning { param([string]$Message) Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Error { param([string]$Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }
function Write-Info { param([string]$Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }

function Test-Docker {
    try {
        docker info | Out-Null
        Write-Success "Docker is running"
        return $true
    } catch {
        Write-Error "Docker is not running. Please start Docker and try again."
        return $false
    }
}

function Initialize-Env {
    $envFile = Join-Path $ProjectDir ".env"
    $envExample = Join-Path $ProjectDir ".env.example"

    if (-not (Test-Path $envFile)) {
        Write-Info "Creating .env file from .env.example..."
        Copy-Item $envExample $envFile
        Write-Success ".env file created"
    } else {
        Write-Info ".env file already exists"
    }
}

function Start-Services {
    Write-Header
    if (-not (Test-Docker)) { return }
    Initialize-Env

    Write-Info "Starting all services..."
    Push-Location $ProjectDir
    docker-compose up -d
    Pop-Location

    Write-Success "Services started successfully!"
    Write-Host ""
    Write-Host "Access points:"
    Write-Host "  - UI:         http://localhost:4200"
    Write-Host "  - API:        http://localhost:5000"
    Write-Host "  - API Docs:   http://localhost:5000/swagger"
    Write-Host "  - MailHog:    http://localhost:8025"
    Write-Host "  - MinIO:      http://localhost:9001"
    Write-Host "  - Adminer:    http://localhost:8080"
    Write-Host "  - Redis Cmd:  http://localhost:8081"
}

function Stop-Services {
    Write-Header
    Write-Info "Stopping all services..."
    Push-Location $ProjectDir
    docker-compose down
    Pop-Location
    Write-Success "Services stopped"
}

function Restart-Services {
    Stop-Services
    Start-Services
}

function Show-Logs {
    param([string]$Service)

    Push-Location $ProjectDir
    if ($Service) {
        docker-compose logs -f $Service
    } else {
        docker-compose logs -f
    }
    Pop-Location
}

function Build-Services {
    Write-Header
    if (-not (Test-Docker)) { return }

    Write-Info "Building all services..."
    Push-Location $ProjectDir
    docker-compose build --no-cache
    Pop-Location
    Write-Success "Build completed"
}

function Clear-All {
    Write-Header
    Write-Warning "This will remove all containers, volumes, and images for this project."
    $confirm = Read-Host "Are you sure? (y/N)"

    if ($confirm -eq "y" -or $confirm -eq "Y") {
        Push-Location $ProjectDir
        docker-compose down -v --rmi all --remove-orphans
        Pop-Location
        Write-Success "Cleanup completed"
    } else {
        Write-Info "Cleanup cancelled"
    }
}

function Show-Status {
    Write-Header
    Push-Location $ProjectDir
    docker-compose ps
    Pop-Location
}

function Run-Migration {
    Write-Header
    Write-Info "Running database migrations..."
    Push-Location $ProjectDir
    docker-compose exec api dotnet ef database update --project Bayan.Infrastructure --startup-project Bayan.API
    Pop-Location
    Write-Success "Migrations completed"
}

function Enter-Shell {
    param([string]$Service)

    if (-not $Service) {
        Write-Error "Please specify a service name (api, ui, db, redis, minio)"
        return
    }

    Push-Location $ProjectDir
    switch ($Service) {
        "db" { docker-compose exec db psql -U bayan_user -d bayan }
        "redis" { docker-compose exec redis redis-cli }
        default { docker-compose exec $Service sh }
    }
    Pop-Location
}

function Backup-Database {
    Write-Header
    $backupFile = "bayan_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"
    Write-Info "Creating database backup: $backupFile"

    $backupDir = Join-Path $ProjectDir "docker\backups"
    if (-not (Test-Path $backupDir)) {
        New-Item -ItemType Directory -Path $backupDir | Out-Null
    }

    Push-Location $ProjectDir
    docker-compose exec -T db pg_dump -U bayan_user bayan > "$backupDir\$backupFile"
    Pop-Location
    Write-Success "Backup created: docker\backups\$backupFile"
}

function Restore-Database {
    param([string]$BackupFile)

    if (-not $BackupFile) {
        Write-Error "Please specify a backup file"
        return
    }

    Write-Header
    Write-Warning "This will overwrite the current database."
    $confirm = Read-Host "Are you sure? (y/N)"

    if ($confirm -eq "y" -or $confirm -eq "Y") {
        Push-Location $ProjectDir
        Get-Content $BackupFile | docker-compose exec -T db psql -U bayan_user -d bayan
        Pop-Location
        Write-Success "Database restored from $BackupFile"
    }
}

function Show-Help {
    Write-Header
    Write-Host ""
    Write-Host "Usage: .\docker-dev.ps1 <command> [options]"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  start       Start all services"
    Write-Host "  stop        Stop all services"
    Write-Host "  restart     Restart all services"
    Write-Host "  build       Build all service images"
    Write-Host "  logs [svc]  View logs (optionally for specific service)"
    Write-Host "  status      Show service status"
    Write-Host "  shell <svc> Open shell in container (api, ui, db, redis, minio)"
    Write-Host "  migrate     Run database migrations"
    Write-Host "  backup      Create database backup"
    Write-Host "  restore <f> Restore database from backup file"
    Write-Host "  clean       Remove all containers, volumes, and images"
    Write-Host "  help        Show this help message"
    Write-Host ""
}

# Main
switch ($Command.ToLower()) {
    "start"     { Start-Services }
    "stop"      { Stop-Services }
    "restart"   { Restart-Services }
    "build"     { Build-Services }
    "logs"      { Show-Logs -Service $Arg1 }
    "status"    { Show-Status }
    "shell"     { Enter-Shell -Service $Arg1 }
    "migrate"   { Run-Migration }
    "backup"    { Backup-Database }
    "restore"   { Restore-Database -BackupFile $Arg1 }
    "clean"     { Clear-All }
    "help"      { Show-Help }
    default     {
        Write-Error "Unknown command: $Command"
        Show-Help
    }
}
