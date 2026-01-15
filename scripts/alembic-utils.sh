#!/bin/bash
# Alembic utilities for multi-worktree setup
# Automatically finds and copies missing migration files from other worktrees

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Find and copy missing Alembic migrations from other worktrees
# Usage: auto_copy_missing_migrations
# Returns: 0 if successful, 1 if failed
auto_copy_missing_migrations() {
    local backend_dir="${1:-backend}"
    local max_attempts=3
    local attempt=0

    echo -e "${BLUE}🔍 Checking for missing Alembic migrations...${NC}"

    while [ $attempt -lt $max_attempts ]; do
        # Try to get current head and detect missing revisions
        local alembic_output=$(alembic current 2>&1)
        local upgrade_output=$(alembic upgrade head 2>&1)

        # Check for "Can't locate revision" error
        if echo "$upgrade_output" | grep -q "Can't locate revision"; then
            # Extract the missing revision ID
            local missing_rev=$(echo "$upgrade_output" | grep -oP "Can't locate revision identified by '\K[a-f0-9]+")

            if [ -z "$missing_rev" ]; then
                echo -e "${RED}❌ Erreur détectée mais impossible d'extraire l'ID de révision${NC}"
                echo -e "${YELLOW}Message d'erreur:${NC}"
                echo "$upgrade_output"
                return 1
            fi

            echo -e "${YELLOW}⚠️  Migration manquante détectée: ${missing_rev}${NC}"
            echo -e "${BLUE}🔎 Recherche dans les autres worktrees...${NC}"

            # Search for the migration file in other worktrees
            local found_file=""
            local found_worktree=""

            # Get list of all StoFlow worktrees
            for worktree_path in ~/StoFlow-*; do
                if [ -d "$worktree_path" ]; then
                    local migration_dir="$worktree_path/backend/migrations/versions"
                    if [ -d "$migration_dir" ]; then
                        # Search for migration file starting with missing_rev
                        local found=$(find "$migration_dir" -name "${missing_rev}_*.py" 2>/dev/null | head -1)
                        if [ -n "$found" ]; then
                            found_file="$found"
                            found_worktree=$(basename "$worktree_path")
                            break
                        fi
                    fi
                fi
            done

            # Also check main repo
            if [ -z "$found_file" ]; then
                local main_migration_dir="$HOME/StoFlow/backend/migrations/versions"
                if [ -d "$main_migration_dir" ]; then
                    local found=$(find "$main_migration_dir" -name "${missing_rev}_*.py" 2>/dev/null | head -1)
                    if [ -n "$found" ]; then
                        found_file="$found"
                        found_worktree="StoFlow (main repo)"
                    fi
                fi
            fi

            if [ -z "$found_file" ]; then
                echo -e "${RED}❌ Migration ${missing_rev} introuvable dans les worktrees${NC}"
                echo -e "${YELLOW}Worktrees vérifiés:${NC}"
                ls -1d ~/StoFlow-* 2>/dev/null | sed 's|.*/||' || echo "  Aucun worktree trouvé"
                echo -e "${YELLOW}Suggestions:${NC}"
                echo "  1. Exécuter /sync pour récupérer les migrations depuis develop"
                echo "  2. Vérifier dans ~/StoFlow: cd ~/StoFlow && git pull origin develop"
                echo "  3. Créer manuellement la migration manquante"
                return 1
            fi

            # Copy the migration file
            local target_dir="$backend_dir/migrations/versions"
            local filename=$(basename "$found_file")
            local target_path="$target_dir/$filename"

            echo -e "${GREEN}✅ Migration trouvée dans: ${found_worktree}${NC}"
            echo -e "${BLUE}📋 Copie de: $filename${NC}"

            # Copy file
            cp "$found_file" "$target_path"

            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ Migration copiée avec succès${NC}"
                attempt=$((attempt + 1))
                echo -e "${BLUE}🔄 Tentative d'upgrade (#$attempt/$max_attempts)...${NC}"
            else
                echo -e "${RED}❌ Échec de la copie${NC}"
                return 1
            fi
        else
            # Check if upgrade was successful
            if echo "$upgrade_output" | grep -q "ERROR"; then
                echo -e "${RED}❌ Erreur Alembic (non liée à une migration manquante)${NC}"
                echo "$upgrade_output"
                return 1
            else
                # Success
                echo -e "${GREEN}✅ Base de données à jour${NC}"
                return 0
            fi
        fi
    done

    # Max attempts reached
    echo -e "${RED}❌ Nombre maximum de tentatives atteint ($max_attempts)${NC}"
    echo -e "${YELLOW}Il semble y avoir plusieurs migrations manquantes.${NC}"
    echo -e "${YELLOW}Recommandation: Synchroniser avec develop (/sync)${NC}"
    return 1
}

# Check if a migration file exists in any worktree
# Usage: find_migration_in_worktrees <revision_id>
# Returns: path to migration file or empty string
find_migration_in_worktrees() {
    local revision_id="$1"

    # Search in all worktrees
    for worktree_path in ~/StoFlow-* ~/StoFlow; do
        if [ -d "$worktree_path" ]; then
            local migration_dir="$worktree_path/backend/migrations/versions"
            if [ -d "$migration_dir" ]; then
                local found=$(find "$migration_dir" -name "${revision_id}_*.py" 2>/dev/null | head -1)
                if [ -n "$found" ]; then
                    echo "$found"
                    return 0
                fi
            fi
        fi
    done

    return 1
}

# List all available migrations across all worktrees
# Usage: list_all_migrations
list_all_migrations() {
    echo -e "${BLUE}📋 Migrations disponibles dans tous les worktrees:${NC}"
    echo ""

    for worktree_path in ~/StoFlow-* ~/StoFlow; do
        if [ -d "$worktree_path" ]; then
            local worktree_name=$(basename "$worktree_path")
            local migration_dir="$worktree_path/backend/migrations/versions"

            if [ -d "$migration_dir" ]; then
                local count=$(find "$migration_dir" -name "*.py" ! -name "__*" 2>/dev/null | wc -l)
                if [ $count -gt 0 ]; then
                    echo -e "${GREEN}${worktree_name}${NC} (${count} migrations)"
                    find "$migration_dir" -name "*.py" ! -name "__*" -exec basename {} \; 2>/dev/null | sort | sed 's/^/  /'
                    echo ""
                fi
            fi
        fi
    done
}

# Export functions for use in other scripts
export -f auto_copy_missing_migrations
export -f find_migration_in_worktrees
export -f list_all_migrations
