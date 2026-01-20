#!/bin/bash
# =============================================================================
# dev-all.sh - Lance tout l'environnement de dev en une commande
# =============================================================================
#
# Usage:
#   ./scripts/dev-all.sh          # Start all services
#   ./scripts/dev-all.sh build    # Rebuild and start
#   ./scripts/dev-all.sh stop     # Stop all services
#   ./scripts/dev-all.sh logs     # View all logs
#   ./scripts/dev-all.sh status   # Check status
#   ./scripts/dev-all.sh clean    # Stop and remove volumes
#
# Services lancés:
#   - PostgreSQL  (port 5433)
#   - Redis       (port 6379)
#   - Backend     (port 8000) - http://localhost:8000
#   - Worker      Celery worker
#   - Beat        Celery scheduler
#   - Flower      (port 5555) - http://localhost:5555
#
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$BACKEND_DIR/docker-compose.dev.yml"

cd "$BACKEND_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║              StoFlow Dev Environment                           ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_urls() {
    echo -e "${GREEN}"
    echo "┌────────────────────────────────────────────────────────────────┐"
    echo "│  Services disponibles:                                        │"
    echo "│                                                                │"
    echo "│  Backend API:  http://localhost:8000                          │"
    echo "│  Swagger UI:   http://localhost:8000/docs                     │"
    echo "│  Flower:       http://localhost:5555                          │"
    echo "│  PostgreSQL:   localhost:5433                                 │"
    echo "│  Redis:        localhost:6379                                 │"
    echo "└────────────────────────────────────────────────────────────────┘"
    echo -e "${NC}"
}

case "${1:-start}" in
    start)
        print_header
        echo -e "${YELLOW}Starting all services...${NC}"
        docker compose -f "$COMPOSE_FILE" up -d
        echo ""
        print_urls
        echo -e "${GREEN}All services started!${NC}"
        echo ""
        echo "View logs: ./scripts/dev-all.sh logs"
        ;;

    build)
        print_header
        echo -e "${YELLOW}Rebuilding and starting all services...${NC}"
        docker compose -f "$COMPOSE_FILE" up -d --build
        echo ""
        print_urls
        echo -e "${GREEN}All services rebuilt and started!${NC}"
        ;;

    stop)
        echo -e "${YELLOW}Stopping all services...${NC}"
        docker compose -f "$COMPOSE_FILE" down
        echo -e "${GREEN}All services stopped.${NC}"
        ;;

    logs)
        docker compose -f "$COMPOSE_FILE" logs -f "${2:-}"
        ;;

    status)
        print_header
        echo -e "${YELLOW}Service status:${NC}"
        echo ""
        docker compose -f "$COMPOSE_FILE" ps
        ;;

    clean)
        echo -e "${RED}WARNING: This will remove all containers AND volumes (data will be lost)${NC}"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker compose -f "$COMPOSE_FILE" down -v
            echo -e "${GREEN}All services and volumes removed.${NC}"
        else
            echo "Cancelled."
        fi
        ;;

    restart)
        echo -e "${YELLOW}Restarting ${2:-all services}...${NC}"
        if [ -n "$2" ]; then
            docker compose -f "$COMPOSE_FILE" restart "$2"
        else
            docker compose -f "$COMPOSE_FILE" restart
        fi
        echo -e "${GREEN}Restart complete.${NC}"
        ;;

    shell)
        # Open a shell in the backend container
        docker compose -f "$COMPOSE_FILE" exec backend /bin/bash
        ;;

    migrate)
        # Run alembic migrations
        echo -e "${YELLOW}Running migrations...${NC}"
        docker compose -f "$COMPOSE_FILE" exec backend alembic upgrade head
        echo -e "${GREEN}Migrations complete.${NC}"
        ;;

    *)
        echo "Usage: $0 {start|build|stop|logs|status|clean|restart|shell|migrate}"
        echo ""
        echo "Commands:"
        echo "  start     Start all services (default)"
        echo "  build     Rebuild and start all services"
        echo "  stop      Stop all services"
        echo "  logs      View logs (optionally specify service: logs worker)"
        echo "  status    Show service status"
        echo "  clean     Stop and remove all data (volumes)"
        echo "  restart   Restart services (optionally specify: restart worker)"
        echo "  shell     Open bash in backend container"
        echo "  migrate   Run alembic migrations"
        exit 1
        ;;
esac
