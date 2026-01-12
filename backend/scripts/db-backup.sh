#!/bin/bash
# Database backup script for StoFlow
# Creates automatic backups before destructive operations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="backups"
DATABASE_HOST="localhost"
DATABASE_PORT="5433"
DATABASE_NAME="stoflow_db"
DATABASE_USER="stoflow_user"
DATABASE_PASSWORD="stoflow_dev_password_2024"
MAX_BACKUPS=10  # Keep last 10 backups

# Help message
show_help() {
    cat << EOF
${BLUE}StoFlow Database Backup Tool${NC}

Usage: $0 [options]

Options:
    -h, --help              Show this help message
    -f, --force             Skip confirmation prompt
    -o, --output <path>     Custom backup output path
    -d, --database <name>   Database name (default: stoflow_db)
    -p, --port <port>       Database port (default: 5433)

Examples:
    $0                      # Interactive backup
    $0 --force              # Automatic backup without confirmation
    $0 --output ~/my-backup.sql
    $0 --database stoflow_test --port 5434

${YELLOW}⚠️  IMPORTANT:${NC}
- This script backs up the DEVELOPMENT database (port 5433)
- For TEST database, use: $0 --database stoflow_test --port 5434
- Backups are stored in: backend/backups/
- Last $MAX_BACKUPS backups are kept (older ones are deleted)

EOF
}

# Parse arguments
FORCE=false
CUSTOM_OUTPUT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -o|--output)
            CUSTOM_OUTPUT="$2"
            shift 2
            ;;
        -d|--database)
            DATABASE_NAME="$2"
            shift 2
            ;;
        -p|--port)
            DATABASE_PORT="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🗄️  StoFlow Database Backup${NC}"
echo ""

# Check if database is accessible
echo -e "${YELLOW}Checking database connection...${NC}"
export PGPASSWORD="$DATABASE_PASSWORD"

if ! pg_isready -h "$DATABASE_HOST" -p "$DATABASE_PORT" -U "$DATABASE_USER" > /dev/null 2>&1; then
    echo -e "${RED}❌ Cannot connect to database${NC}"
    echo -e "   Host: $DATABASE_HOST:$DATABASE_PORT"
    echo -e "   Database: $DATABASE_NAME"
    echo ""
    echo -e "${YELLOW}💡 Make sure the database is running:${NC}"
    echo -e "   docker-compose up -d"
    exit 1
fi

echo -e "${GREEN}✅ Database connection OK${NC}"

# Get database size
DB_SIZE=$(PGPASSWORD="$DATABASE_PASSWORD" psql -h "$DATABASE_HOST" -p "$DATABASE_PORT" -U "$DATABASE_USER" -d "$DATABASE_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DATABASE_NAME'));" 2>/dev/null | tr -d ' ')

echo -e "${BLUE}📊 Database info:${NC}"
echo -e "   Name: $DATABASE_NAME"
echo -e "   Port: $DATABASE_PORT"
echo -e "   Size: $DB_SIZE"
echo ""

# Confirmation prompt (unless --force)
if [ "$FORCE" = false ]; then
    read -p "$(echo -e ${YELLOW}⚠️  Create backup? [y/N]: ${NC})" -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Backup cancelled${NC}"
        exit 0
    fi
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate backup filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
if [ -z "$CUSTOM_OUTPUT" ]; then
    BACKUP_FILE="$BACKUP_DIR/backup_${DATABASE_NAME}_${TIMESTAMP}.sql"
else
    BACKUP_FILE="$CUSTOM_OUTPUT"
    mkdir -p "$(dirname "$BACKUP_FILE")"
fi

# Create backup
echo -e "${YELLOW}📦 Creating backup...${NC}"
echo -e "   Output: $BACKUP_FILE"

PGPASSWORD="$DATABASE_PASSWORD" pg_dump \
    -h "$DATABASE_HOST" \
    -p "$DATABASE_PORT" \
    -U "$DATABASE_USER" \
    -d "$DATABASE_NAME" \
    --no-owner \
    --no-acl \
    -F p \
    -f "$BACKUP_FILE" 2>&1 | grep -v "^$"

if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✅ Backup created successfully${NC}"
    echo -e "   File: $BACKUP_FILE"
    echo -e "   Size: $BACKUP_SIZE"
else
    echo -e "${RED}❌ Backup failed${NC}"
    exit 1
fi

# Clean old backups (keep last MAX_BACKUPS)
if [ -z "$CUSTOM_OUTPUT" ]; then
    echo -e "${YELLOW}🧹 Cleaning old backups...${NC}"
    OLD_BACKUPS=$(ls -t "$BACKUP_DIR"/backup_*.sql 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)))

    if [ ! -z "$OLD_BACKUPS" ]; then
        echo "$OLD_BACKUPS" | while read -r old_backup; do
            echo "   Deleting: $(basename "$old_backup")"
            rm -f "$old_backup"
        done
        echo -e "${GREEN}✅ Old backups cleaned (kept last $MAX_BACKUPS)${NC}"
    else
        echo -e "   No old backups to clean"
    fi
fi

echo ""
echo -e "${GREEN}✨ Backup complete!${NC}"
echo ""
echo -e "${BLUE}📝 To restore this backup:${NC}"
echo -e "   $0 --restore $BACKUP_FILE"
echo ""
