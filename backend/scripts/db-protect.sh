#!/bin/bash
# Database protection script
# Prevents accidental destructive operations on development database

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Protection configuration
PROTECTED_DATABASES=("stoflow_db" "stoflow_dev")
PROTECTED_PORT="5433"
TEST_DATABASE="stoflow_test"
TEST_PORT="5434"

show_help() {
    cat << EOF
${BLUE}StoFlow Database Protection${NC}

This script helps prevent accidental data loss by:
- Checking if you're targeting the correct database
- Creating automatic backups before destructive operations
- Providing clear warnings for dangerous operations

Usage:
    $0 <command>

Commands:
    check-migration         Check if migration is safe
    pre-downgrade          Create backup before downgrade
    pre-drop              Create backup before DROP operation
    verify-test-db         Verify test database is being used

Examples:
    # Before running alembic downgrade
    $0 pre-downgrade && alembic downgrade -1

    # Verify you're using test database in tests
    $0 verify-test-db

${YELLOW}⚠️  CRITICAL RULES:${NC}

1. ${RED}NEVER${NC} run destructive operations on ${GREEN}development database${NC} (port $PROTECTED_PORT)
   without explicit confirmation and backup

2. ${GREEN}ALWAYS${NC} use ${BLUE}test database${NC} (port $TEST_PORT) for tests

3. ${GREEN}ALWAYS${NC} create a backup before:
   - alembic downgrade
   - Manual SQL with DROP/TRUNCATE/DELETE
   - Schema modifications

4. ${RED}NEVER${NC} run migrations with --sql or --autogenerate without review

${BLUE}📋 Quick Reference:${NC}

Safe operations (no backup needed):
  ✅ alembic upgrade head
  ✅ alembic history
  ✅ alembic current
  ✅ SELECT queries
  ✅ pytest (uses test DB)

Dangerous operations (backup required):
  ⚠️  alembic downgrade
  ⚠️  DROP TABLE/SCHEMA/DATABASE
  ⚠️  TRUNCATE
  ⚠️  DELETE FROM (without WHERE or WHERE 1=1)
  ⚠️  ALTER TABLE DROP COLUMN

EOF
}

# Check if we're targeting development database
check_dev_database() {
    local db_url="${DATABASE_URL:-}"

    if [[ "$db_url" == *"$PROTECTED_PORT"* ]]; then
        for protected_db in "${PROTECTED_DATABASES[@]}"; do
            if [[ "$db_url" == *"$protected_db"* ]]; then
                return 0  # Yes, it's dev database
            fi
        done
    fi
    return 1  # Not dev database
}

# Check if we're targeting test database
check_test_database() {
    local db_url="${DATABASE_URL:-}"
    local test_db_url="${TEST_DATABASE_URL:-}"

    if [[ "$db_url" == *"$TEST_PORT"* ]] || [[ "$db_url" == *"$TEST_DATABASE"* ]]; then
        return 0  # Yes, it's test database
    fi

    if [[ "$test_db_url" == *"$TEST_PORT"* ]] || [[ "$test_db_url" == *"$TEST_DATABASE"* ]]; then
        return 0  # Yes, TEST_DATABASE_URL is set correctly
    fi

    return 1  # Not test database
}

# Create backup before destructive operation
create_safety_backup() {
    local operation="$1"

    echo -e "${YELLOW}🛡️  Safety Backup (before $operation)${NC}"
    echo ""

    # Create backup
    if ./scripts/db-backup.sh --force --output "backups/safety_backup_$(date +%Y%m%d_%H%M%S).sql"; then
        echo -e "${GREEN}✅ Safety backup created${NC}"
        return 0
    else
        echo -e "${RED}❌ Backup failed - operation CANCELLED${NC}"
        return 1
    fi
}

# Main command handling
case "${1:-}" in
    -h|--help|help)
        show_help
        exit 0
        ;;

    check-migration)
        echo -e "${BLUE}🔍 Checking migration safety...${NC}"

        if check_dev_database; then
            echo -e "${YELLOW}⚠️  Targeting DEVELOPMENT database${NC}"
            echo -e "   This is OK for 'alembic upgrade'"
            echo -e "   For downgrades, run: $0 pre-downgrade first"
        elif check_test_database; then
            echo -e "${GREEN}✅ Targeting TEST database - safe${NC}"
        else
            echo -e "${BLUE}ℹ️  Unknown database target${NC}"
            echo -e "   DATABASE_URL: ${DATABASE_URL:-not set}"
        fi
        ;;

    pre-downgrade)
        echo -e "${RED}⚠️  DOWNGRADE OPERATION DETECTED${NC}"
        echo ""

        if ! check_dev_database; then
            echo -e "${GREEN}✅ Not targeting dev database - no backup needed${NC}"
            exit 0
        fi

        echo -e "${YELLOW}You are about to downgrade the DEVELOPMENT database${NC}"
        echo -e "${YELLOW}This operation can cause DATA LOSS${NC}"
        echo ""
        echo -e "${BLUE}Creating safety backup first...${NC}"
        echo ""

        if create_safety_backup "alembic downgrade"; then
            echo ""
            echo -e "${GREEN}✅ Backup complete - you can proceed with downgrade${NC}"
            exit 0
        else
            echo -e "${RED}❌ Cannot proceed without backup${NC}"
            exit 1
        fi
        ;;

    pre-drop)
        echo -e "${RED}⚠️  DROP OPERATION DETECTED${NC}"
        echo ""

        if ! check_dev_database; then
            echo -e "${GREEN}✅ Not targeting dev database - no backup needed${NC}"
            exit 0
        fi

        echo -e "${YELLOW}You are about to execute a DROP statement${NC}"
        echo -e "${YELLOW}This will PERMANENTLY DELETE data${NC}"
        echo ""
        read -p "$(echo -e ${RED}Are you ABSOLUTELY sure? Type 'DROP' to confirm: ${NC})" -r
        echo

        if [[ "$REPLY" != "DROP" ]]; then
            echo -e "${YELLOW}Operation cancelled${NC}"
            exit 1
        fi

        echo -e "${BLUE}Creating safety backup first...${NC}"
        echo ""

        if create_safety_backup "DROP"; then
            echo ""
            echo -e "${GREEN}✅ Backup complete - you can proceed with DROP${NC}"
            exit 0
        else
            echo -e "${RED}❌ Cannot proceed without backup${NC}"
            exit 1
        fi
        ;;

    verify-test-db)
        echo -e "${BLUE}🔍 Verifying test database configuration...${NC}"
        echo ""

        if check_test_database; then
            echo -e "${GREEN}✅ TEST database is configured correctly${NC}"
            echo -e "   Tests will use: port $TEST_PORT"
            exit 0
        else
            echo -e "${RED}❌ TEST database is NOT configured correctly${NC}"
            echo ""
            echo -e "${YELLOW}Current configuration:${NC}"
            echo -e "   DATABASE_URL: ${DATABASE_URL:-not set}"
            echo -e "   TEST_DATABASE_URL: ${TEST_DATABASE_URL:-not set}"
            echo ""
            echo -e "${YELLOW}Expected for tests:${NC}"
            echo -e "   Port: $TEST_PORT"
            echo -e "   Database: $TEST_DATABASE"
            echo ""
            echo -e "${RED}⚠️  Tests might be using DEVELOPMENT database!${NC}"
            exit 1
        fi
        ;;

    *)
        echo -e "${RED}Unknown command: ${1:-none}${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
