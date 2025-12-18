#!/bin/bash

################################################################################
# Script de démarrage du service de polling Etsy
#
# Ce script démarre le service de polling Etsy en arrière-plan.
# Il peut être utilisé:
# - Manuellement: ./scripts/start_etsy_polling.sh
# - Via systemd: systemctl start etsy-polling
# - Au démarrage du serveur (systemd autostart)
#
# Author: Claude
# Date: 2025-12-10
################################################################################

set -e

# Couleurs pour logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Starting Etsy Polling Service${NC}"
echo -e "${GREEN}========================================${NC}"

# Déterminer le répertoire du projet
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${YELLOW}📂 Project directory: $PROJECT_DIR${NC}"

# Se placer dans le répertoire du projet
cd "$PROJECT_DIR"

# Vérifier que l'environnement virtuel existe
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo -e "${YELLOW}Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt${NC}"
    exit 1
fi

# Activer l'environnement virtuel
echo -e "${YELLOW}🔄 Activating virtual environment...${NC}"
source venv/bin/activate

# Vérifier que APScheduler est installé
if ! python -c "import apscheduler" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  APScheduler not installed. Installing...${NC}"
    pip install apscheduler
fi

# Créer répertoire de logs si n'existe pas
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

# Nom du fichier de log
LOG_FILE="$LOG_DIR/etsy_polling.log"
PID_FILE="$LOG_DIR/etsy_polling.pid"

# Vérifier si le service est déjà en cours
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Etsy polling service is already running (PID: $OLD_PID)${NC}"
        echo -e "${YELLOW}To stop it, run: kill $OLD_PID${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠️  Found stale PID file. Removing...${NC}"
        rm "$PID_FILE"
    fi
fi

# Démarrer le service de polling
echo -e "${YELLOW}🚀 Starting Etsy polling service...${NC}"

# Option 1: Démarrer en arrière-plan (production)
if [ "$1" = "--daemon" ] || [ "$1" = "-d" ]; then
    nohup python -m services.etsy_polling_cron >> "$LOG_FILE" 2>&1 &
    PID=$!
    echo $PID > "$PID_FILE"

    echo -e "${GREEN}✅ Etsy polling service started in background${NC}"
    echo -e "${GREEN}   PID: $PID${NC}"
    echo -e "${GREEN}   Log file: $LOG_FILE${NC}"
    echo -e "${YELLOW}To view logs: tail -f $LOG_FILE${NC}"
    echo -e "${YELLOW}To stop: kill $PID${NC}"

# Option 2: Démarrer en foreground (développement)
else
    echo -e "${YELLOW}Running in foreground mode (Ctrl+C to stop)${NC}"
    echo -e "${YELLOW}For background mode, use: $0 --daemon${NC}"
    python -m services.etsy_polling_cron
fi

echo -e "${GREEN}========================================${NC}"
