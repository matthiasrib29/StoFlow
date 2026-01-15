#!/bin/bash
# Quick test script for alembic-utils.sh
# This script tests the basic functionality of auto_copy_missing_migrations

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🧪 Test Alembic Utils - Auto-Copy Migrations               ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the utilities
echo -e "${YELLOW}📦 Chargement de alembic-utils.sh...${NC}"
source "${SCRIPT_DIR}/alembic-utils.sh"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ alembic-utils.sh chargé avec succès${NC}"
else
    echo -e "${RED}❌ Échec du chargement${NC}"
    exit 1
fi

echo ""

# Test 1: Check if functions are defined
echo -e "${BLUE}Test 1: Vérification des fonctions${NC}"
if type auto_copy_missing_migrations &>/dev/null; then
    echo -e "${GREEN}✅ auto_copy_missing_migrations définie${NC}"
else
    echo -e "${RED}❌ auto_copy_missing_migrations non définie${NC}"
    exit 1
fi

if type find_migration_in_worktrees &>/dev/null; then
    echo -e "${GREEN}✅ find_migration_in_worktrees définie${NC}"
else
    echo -e "${RED}❌ find_migration_in_worktrees non définie${NC}"
    exit 1
fi

if type list_all_migrations &>/dev/null; then
    echo -e "${GREEN}✅ list_all_migrations définie${NC}"
else
    echo -e "${RED}❌ list_all_migrations non définie${NC}"
    exit 1
fi

echo ""

# Test 2: List all migrations
echo -e "${BLUE}Test 2: Liste des migrations disponibles${NC}"
list_all_migrations

echo ""

# Test 3: Check if backend directory exists
echo -e "${BLUE}Test 3: Vérification du répertoire backend${NC}"
if [ -d "${SCRIPT_DIR}/../backend/migrations/versions" ]; then
    MIGRATION_COUNT=$(find "${SCRIPT_DIR}/../backend/migrations/versions" -name "*.py" ! -name "__*" | wc -l)
    echo -e "${GREEN}✅ Répertoire migrations trouvé (${MIGRATION_COUNT} fichiers)${NC}"
else
    echo -e "${YELLOW}⚠️  Répertoire migrations non trouvé (peut-être dans un worktree)${NC}"
fi

echo ""

# Test 4: Check worktrees
echo -e "${BLUE}Test 4: Détection des worktrees${NC}"
WORKTREE_COUNT=$(ls -1d ~/StoFlow-* 2>/dev/null | wc -l)
if [ "$WORKTREE_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ ${WORKTREE_COUNT} worktree(s) détecté(s)${NC}"
    ls -1d ~/StoFlow-* 2>/dev/null | sed 's|.*/||' | sed 's/^/   - /'
else
    echo -e "${YELLOW}⚠️  Aucun worktree détecté (~/StoFlow-*)${NC}"
fi

echo ""

# Test 5: Syntax validation
echo -e "${BLUE}Test 5: Validation de la syntaxe bash${NC}"
if bash -n "${SCRIPT_DIR}/alembic-utils.sh" 2>/dev/null; then
    echo -e "${GREEN}✅ Syntaxe bash correcte${NC}"
else
    echo -e "${RED}❌ Erreurs de syntaxe détectées${NC}"
    bash -n "${SCRIPT_DIR}/alembic-utils.sh"
    exit 1
fi

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ TOUS LES TESTS RÉUSSIS                                   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}💡 Pour tester l'auto-copy en situation réelle:${NC}"
echo -e "   1. Créer un worktree: /1-new-feature \"test-auto-copy\""
echo -e "   2. Lancer les serveurs: /1-dev"
echo -e "   3. Observer l'auto-copy dans les logs"
echo ""
