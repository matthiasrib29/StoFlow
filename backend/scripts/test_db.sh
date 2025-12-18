#!/bin/bash

# Script pour gérer la base de données de test PostgreSQL (Docker)
# Usage: ./scripts/test_db.sh [start|stop|restart|status|logs|shell]

set -e

COMPOSE_FILE="docker-compose.test.yml"
SERVICE_NAME="test_db"

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher des messages colorés
info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

success() {
    echo -e "${GREEN}✅${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

error() {
    echo -e "${RED}❌${NC} $1"
}

# Fonction pour démarrer la DB
start_db() {
    info "Starting test database..."
    docker-compose -f "$COMPOSE_FILE" up -d

    info "Waiting for database to be ready..."
    MAX_TRIES=30
    TRIES=0

    until docker-compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" pg_isready -U stoflow_test -d stoflow_test > /dev/null 2>&1; do
        TRIES=$((TRIES + 1))
        if [ $TRIES -ge $MAX_TRIES ]; then
            error "Database failed to start after ${MAX_TRIES} seconds"
            exit 1
        fi
        printf "."
        sleep 1
    done

    echo ""
    success "Test database is ready!"
    info "Connection string: postgresql://stoflow_test:test_password_123@localhost:5433/stoflow_test"
}

# Fonction pour arrêter la DB
stop_db() {
    info "Stopping test database..."
    docker-compose -f "$COMPOSE_FILE" down -v
    success "Test database stopped"
}

# Fonction pour redémarrer la DB
restart_db() {
    stop_db
    start_db
}

# Fonction pour afficher le status
status_db() {
    info "Checking test database status..."
    docker-compose -f "$COMPOSE_FILE" ps

    if docker-compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" pg_isready -U stoflow_test > /dev/null 2>&1; then
        success "Database is running and accepting connections"
    else
        warning "Database is not ready or not running"
    fi
}

# Fonction pour afficher les logs
logs_db() {
    info "Showing database logs (Ctrl+C to exit)..."
    docker-compose -f "$COMPOSE_FILE" logs -f "$SERVICE_NAME"
}

# Fonction pour ouvrir un shell psql
shell_db() {
    info "Opening PostgreSQL shell..."
    docker-compose -f "$COMPOSE_FILE" exec "$SERVICE_NAME" psql -U stoflow_test -d stoflow_test
}

# Fonction pour afficher l'aide
show_help() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start    Start the test database (Docker)"
    echo "  stop     Stop the test database and remove containers"
    echo "  restart  Restart the test database"
    echo "  status   Show database status"
    echo "  logs     Show database logs (follow mode)"
    echo "  shell    Open PostgreSQL shell"
    echo "  help     Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start              # Start the test database"
    echo "  $0 status             # Check if database is running"
    echo "  $0 shell              # Open psql shell"
}

# Main
case "${1:-help}" in
    start)
        start_db
        ;;
    stop)
        stop_db
        ;;
    restart)
        restart_db
        ;;
    status)
        status_db
        ;;
    logs)
        logs_db
        ;;
    shell)
        shell_db
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
