#!/bin/bash
# scripts/new-hotfix.sh
# Creates a new hotfix worktree with dedicated venv and dev environment
# Usage: ./scripts/new-hotfix.sh <env_num> <hotfix_name>
# Example: ./scripts/new-hotfix.sh 1 fix-login

set -e
trap 'echo "❌ Script arrêté à la ligne $LINENO"' ERR

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parameters
ENV_NUM=$1
NAME=$2

# Validation
if [ -z "$ENV_NUM" ] || [ -z "$NAME" ]; then
    echo -e "${RED}❌ ERREUR: Paramètres manquants${NC}"
    echo "Usage: $0 <env_num> <name>"
    echo "Exemple: $0 1 fix-login"
    exit 1
fi

if ! [[ "$ENV_NUM" =~ ^[1-4]$ ]]; then
    echo -e "${RED}❌ ERREUR: env_num doit être 1, 2, 3, ou 4${NC}"
    exit 1
fi

# Calculate ports
BACKEND_PORT=$((8000 + ENV_NUM - 1))
FRONTEND_PORT=$((3000 + ENV_NUM - 1))

WORKTREE_DIR="$HOME/StoFlow-$NAME"
BRANCH_NAME="hotfix/$NAME"

echo -e "${RED}🚨 Création du worktree HOTFIX: $NAME${NC}"
echo -e "${BLUE}📍 Environnement: $ENV_NUM (ports $BACKEND_PORT/$FRONTEND_PORT)${NC}"
echo ""

# ============================================================================
# PROTECTION: Vérifier changements dans ~/StoFlow
# ============================================================================

echo -e "${YELLOW}🔍 Vérification de ~/StoFlow...${NC}"
cd ~/StoFlow || {
    echo -e "${RED}❌ ERREUR: Impossible d'accéder à ~/StoFlow${NC}"
    exit 1
}

# Vérifier changements non commités
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  Changements non commités détectés dans ~/StoFlow :${NC}"
    echo ""
    git status --short
    echo ""
    echo -e "${YELLOW}📝 Je vais committer automatiquement avec le message:${NC}"
    echo -e "    ${BLUE}'wip: auto-commit before creating worktree $NAME'${NC}"
    echo ""
    read -p "Continuer ? (o/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Oo]$ ]]; then
        echo -e "${RED}❌ Annulé par l'utilisateur${NC}"
        exit 1
    fi

    echo -e "${GREEN}💾 Commit en cours...${NC}"
    git add -A
    git commit -m "wip: auto-commit before creating worktree $NAME"
    git push
    echo -e "${GREEN}✅ Changements committés et pushés${NC}"
    echo ""
fi

# Vérifier commits locaux non poussés
CURRENT_BRANCH=$(git branch --show-current)
LOCAL_COMMITS=$(git log origin/$CURRENT_BRANCH..$CURRENT_BRANCH --oneline 2>/dev/null || echo "")
if [ -n "$LOCAL_COMMITS" ]; then
    echo -e "${YELLOW}⚠️  Commits locaux NON POUSSÉS sur $CURRENT_BRANCH :${NC}"
    echo "$LOCAL_COMMITS"
    echo ""
    read -p "Pousser automatiquement ? (o/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Oo]$ ]]; then
        git push
        echo -e "${GREEN}✅ Commits poussés${NC}"
    else
        echo -e "${YELLOW}⚠️  Attention: commits locaux non poussés${NC}"
    fi
    echo ""
fi

# ============================================================================
# CRÉATION DU WORKTREE
# ============================================================================

echo -e "${GREEN}📦 Mise à jour de develop...${NC}"
git checkout develop || exit 1
git pull || exit 1

echo -e "${GREEN}🌿 Création du worktree...${NC}"
if [ -d "$WORKTREE_DIR" ]; then
    echo -e "${RED}❌ ERREUR: Le dossier $WORKTREE_DIR existe déjà${NC}"
    echo "💡 Solutions:"
    echo "  1. Supprimer le dossier: rm -rf $WORKTREE_DIR"
    echo "  2. Utiliser un autre nom"
    exit 1
fi

git worktree add "$WORKTREE_DIR" -b "$BRANCH_NAME" || {
    echo -e "${RED}❌ ERREUR: Échec création worktree${NC}"
    exit 1
}

echo -e "${GREEN}✅ Worktree créé: $WORKTREE_DIR${NC}"
echo ""

# ============================================================================
# CONFIGURATION DU WORKTREE
# ============================================================================

cd "$WORKTREE_DIR" || exit 1

echo -e "${YELLOW}📋 Copie des fichiers de configuration...${NC}"
cp ~/StoFlow/backend/.env backend/.env || {
    echo -e "${RED}❌ ERREUR: Échec copie backend/.env${NC}"
    exit 1
}
cp ~/StoFlow/frontend/.env frontend/.env || {
    echo -e "${RED}❌ ERREUR: Échec copie frontend/.env${NC}"
    exit 1
}

echo -e "${YELLOW}🔧 Configuration du venv dédié...${NC}"
./scripts/setup-worktree-venv.sh || {
    echo -e "${RED}❌ ERREUR: Échec configuration venv${NC}"
    exit 1
}

echo -e "${YELLOW}🔑 Copie des clés API...${NC}"
cp -r ~/StoFlow/backend/keys backend/ || {
    echo -e "${RED}❌ ERREUR: Échec copie keys${NC}"
    exit 1
}

echo -e "${YELLOW}📂 Création du dossier logs...${NC}"
mkdir -p logs

echo -e "${YELLOW}📦 Installation des dépendances frontend...${NC}"
cd frontend
npm install || {
    echo -e "${RED}❌ ERREUR: Échec npm install${NC}"
    exit 1
}
cd ..

# ============================================================================
# LANCEMENT DE L'ENVIRONNEMENT DE DEV
# ============================================================================

echo -e "${GREEN}🚀 Lancement de l'environnement de dev $ENV_NUM...${NC}"
./scripts/dev.sh $ENV_NUM &
DEV_PID=$!
echo ""

# ============================================================================
# MESSAGE DE SUCCÈS
# ============================================================================

echo ""
echo -e "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║  🚨 HOTFIX WORKTREE CREE + DEV $ENV_NUM LANCE                       ║${NC}"
echo -e "${RED}╠══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${RED}║                                                              ║${NC}"
echo -e "${RED}║  📁 Dossier : $WORKTREE_DIR"
printf "${RED}║  🌿 Branche : $BRANCH_NAME"
printf "\n${RED}║  🚀 Env dev : $ENV_NUM (Backend $BACKEND_PORT + Frontend $FRONTEND_PORT)"
printf "\n${RED}║                                                              ║${NC}"
echo -e "${RED}╠══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${RED}║  ⚠️  A PARTIR DE MAINTENANT :                                ║${NC}"
echo -e "${RED}║                                                              ║${NC}"
echo -e "${RED}║  TOUTES les modifications doivent etre faites dans :         ║${NC}"
echo -e "${RED}║  $WORKTREE_DIR/"
printf "\n${RED}║                                                              ║${NC}"
echo -e "${RED}║  URLs :                                                      ║${NC}"
echo -e "${RED}║  • Backend  : http://localhost:$BACKEND_PORT"
printf "\n${RED}║  • Frontend : http://localhost:$FRONTEND_PORT"
printf "\n${RED}║                                                              ║${NC}"
echo -e "${RED}║  ❌ NE PAS modifier ~/StoFlow/ (c'est develop)               ║${NC}"
echo -e "${RED}║                                                              ║${NC}"
echo -e "${RED}║  Quand fini : /finish                                        ║${NC}"
echo -e "${RED}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

exit 0
