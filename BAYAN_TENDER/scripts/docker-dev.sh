#!/bin/bash
# =============================================================================
# Bayan Tender Management System - Docker Development Script
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  Bayan Tender Management System - Docker${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Create .env file if it doesn't exist
setup_env() {
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        print_info "Creating .env file from .env.example..."
        cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
        print_success ".env file created"
    else
        print_info ".env file already exists"
    fi
}

# Start services
start() {
    print_header
    check_docker
    setup_env

    print_info "Starting all services..."
    cd "$PROJECT_DIR"
    docker-compose up -d

    print_success "Services started successfully!"
    echo ""
    echo "Access points:"
    echo "  - UI:         http://localhost:4200"
    echo "  - API:        http://localhost:5000"
    echo "  - API Docs:   http://localhost:5000/swagger"
    echo "  - MailHog:    http://localhost:8025"
    echo "  - MinIO:      http://localhost:9001"
    echo "  - Adminer:    http://localhost:8080"
    echo "  - Redis Cmd:  http://localhost:8081"
}

# Stop services
stop() {
    print_header
    print_info "Stopping all services..."
    cd "$PROJECT_DIR"
    docker-compose down
    print_success "Services stopped"
}

# Restart services
restart() {
    stop
    start
}

# View logs
logs() {
    cd "$PROJECT_DIR"
    if [ -n "$2" ]; then
        docker-compose logs -f "$2"
    else
        docker-compose logs -f
    fi
}

# Build services
build() {
    print_header
    check_docker

    print_info "Building all services..."
    cd "$PROJECT_DIR"
    docker-compose build --no-cache
    print_success "Build completed"
}

# Clean up
clean() {
    print_header
    print_warning "This will remove all containers, volumes, and images for this project."
    read -p "Are you sure? (y/N) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$PROJECT_DIR"
        docker-compose down -v --rmi all --remove-orphans
        print_success "Cleanup completed"
    else
        print_info "Cleanup cancelled"
    fi
}

# Show status
status() {
    print_header
    cd "$PROJECT_DIR"
    docker-compose ps
}

# Run database migrations
migrate() {
    print_header
    print_info "Running database migrations..."
    cd "$PROJECT_DIR"
    docker-compose exec api dotnet ef database update --project Bayan.Infrastructure --startup-project Bayan.API
    print_success "Migrations completed"
}

# Shell into a container
shell() {
    if [ -z "$2" ]; then
        print_error "Please specify a service name (api, ui, db, redis, minio)"
        exit 1
    fi

    cd "$PROJECT_DIR"
    case "$2" in
        db)
            docker-compose exec db psql -U bayan_user -d bayan
            ;;
        redis)
            docker-compose exec redis redis-cli
            ;;
        *)
            docker-compose exec "$2" sh
            ;;
    esac
}

# Backup database
backup() {
    print_header
    BACKUP_FILE="bayan_backup_$(date +%Y%m%d_%H%M%S).sql"
    print_info "Creating database backup: $BACKUP_FILE"

    cd "$PROJECT_DIR"
    docker-compose exec -T db pg_dump -U bayan_user bayan > "./docker/backups/$BACKUP_FILE"
    print_success "Backup created: ./docker/backups/$BACKUP_FILE"
}

# Restore database
restore() {
    if [ -z "$2" ]; then
        print_error "Please specify a backup file"
        exit 1
    fi

    print_header
    print_warning "This will overwrite the current database."
    read -p "Are you sure? (y/N) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$PROJECT_DIR"
        docker-compose exec -T db psql -U bayan_user -d bayan < "$2"
        print_success "Database restored from $2"
    fi
}

# Help
help() {
    print_header
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  start       Start all services"
    echo "  stop        Stop all services"
    echo "  restart     Restart all services"
    echo "  build       Build all service images"
    echo "  logs [svc]  View logs (optionally for specific service)"
    echo "  status      Show service status"
    echo "  shell <svc> Open shell in container (api, ui, db, redis, minio)"
    echo "  migrate     Run database migrations"
    echo "  backup      Create database backup"
    echo "  restore <f> Restore database from backup file"
    echo "  clean       Remove all containers, volumes, and images"
    echo "  help        Show this help message"
    echo ""
}

# Main
case "$1" in
    start)      start ;;
    stop)       stop ;;
    restart)    restart ;;
    build)      build ;;
    logs)       logs "$@" ;;
    status)     status ;;
    shell)      shell "$@" ;;
    migrate)    migrate ;;
    backup)     backup ;;
    restore)    restore "$@" ;;
    clean)      clean ;;
    help|--help|-h|"")
                help ;;
    *)
        print_error "Unknown command: $1"
        help
        exit 1
        ;;
esac
