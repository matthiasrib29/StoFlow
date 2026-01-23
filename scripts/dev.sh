#!/bin/bash
# Unified dev environment script
# Usage: ./scripts/dev.sh <env_num>
# Example: ./scripts/dev.sh 1  (Backend: 8000, Frontend: 3000)

set -e

# Source Alembic utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/alembic-utils.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Validate parameter
ENV_NUM=$1
if [ -z "$ENV_NUM" ]; then
    echo -e "${RED}❌ ERREUR: Paramètre manquant${NC}"
    echo "Usage: $0 <env_num>"
    echo "Exemple: $0 1"
    exit 1
fi

if ! [[ "$ENV_NUM" =~ ^[1-4]$ ]]; then
    echo -e "${RED}❌ ERREUR: env_num doit être 1, 2, 3, ou 4${NC}"
    exit 1
fi

# Calculate ports based on env number
BACKEND_PORT=$((8000 + ENV_NUM - 1))
FRONTEND_PORT=$((3000 + ENV_NUM - 1))
ENV_NAME="dev${ENV_NUM}"

echo -e "${BLUE}🚀 Starting StoFlow Dev Environment ${ENV_NUM}${NC}"
echo -e "${BLUE}   Backend: http://localhost:${BACKEND_PORT}${NC}"
echo -e "${BLUE}   Frontend: http://localhost:${FRONTEND_PORT}${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Rotate logs (clean old logs automatically)
if [ -f "scripts/rotate-logs.sh" ]; then
    ./scripts/rotate-logs.sh > /dev/null 2>&1 || true
fi

# Check if PostgreSQL container is running
if ! docker ps | grep -q stoflow.*postgres; then
    echo -e "${YELLOW}⚠️  PostgreSQL container not running. Starting...${NC}"
    cd backend
    docker-compose up -d
    cd ..
fi

# Wait for PostgreSQL to be ready
echo -e "${YELLOW}⏳ Waiting for PostgreSQL...${NC}"
for i in {1..30}; do
    if docker exec stoflow_postgres pg_isready -U stoflow_user >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PostgreSQL ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ PostgreSQL not ready after 30s${NC}"
        exit 1
    fi
    sleep 1
done

# Kill any existing processes on our ports (only servers, not clients)
echo -e "${YELLOW}🧹 Cleaning up ports ${BACKEND_PORT} and ${FRONTEND_PORT}...${NC}"
lsof -ti:${BACKEND_PORT} -sTCP:LISTEN 2>/dev/null | xargs -r kill -9 2>/dev/null || true
lsof -ti:${FRONTEND_PORT} -sTCP:LISTEN 2>/dev/null | xargs -r kill -9 2>/dev/null || true
sleep 1

# PIDs to track
BACKEND_PID=""
FRONTEND_PID=""

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🛑 Stopping dev environment ${ENV_NUM}...${NC}"

    if [ ! -z "$BACKEND_PID" ]; then
        echo -e "${YELLOW}Stopping backend (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID 2>/dev/null || true
    fi

    if [ ! -z "$FRONTEND_PID" ]; then
        echo -e "${YELLOW}Stopping frontend (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID 2>/dev/null || true
    fi

    # Kill any remaining processes on our ports
    lsof -ti:${BACKEND_PORT} -sTCP:LISTEN 2>/dev/null | xargs -r kill -9 2>/dev/null || true
    lsof -ti:${FRONTEND_PORT} -sTCP:LISTEN 2>/dev/null | xargs -r kill -9 2>/dev/null || true

    echo -e "${GREEN}✅ Dev environment ${ENV_NUM} stopped${NC}"
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM EXIT

# Start Backend
echo -e "${GREEN}🔧 Starting Backend on port ${BACKEND_PORT}...${NC}"
cd backend

# Check if venv exists (.venv or venv)
if [ -d ".venv" ]; then
    VENV_DIR=".venv"
elif [ -d "venv" ]; then
    VENV_DIR="venv"
else
    echo -e "${RED}❌ Virtual environment not found. Please run: python -m venv .venv${NC}"
    exit 1
fi

# Activate venv
source ${VENV_DIR}/bin/activate

# Apply database migrations with auto-copy from other worktrees
echo -e "${YELLOW}📦 Checking database migrations...${NC}"
if auto_copy_missing_migrations "."; then
    echo -e "${GREEN}✅ Database up to date${NC}"
else
    echo -e "${RED}❌ Migration failed! Check alembic logs.${NC}"
    echo -e "${YELLOW}   Suggestions:${NC}"
    echo -e "${YELLOW}   1. Run: cd backend && alembic upgrade head${NC}"
    echo -e "${YELLOW}   2. Sync with develop: /sync${NC}"
    echo -e "${YELLOW}   3. Check migration status: cd backend && alembic current${NC}"
    exit 1
fi

# Start uvicorn in background with isolated Temporal task queue
export TEMPORAL_TASK_QUEUE="stoflow-sync-queue-dev${ENV_NUM}"
echo -e "${YELLOW}   Temporal queue: ${TEMPORAL_TASK_QUEUE}${NC}"
uvicorn main:socket_app --reload --host 0.0.0.0 --port ${BACKEND_PORT} > ../logs/${ENV_NAME}-backend.log 2>&1 &
BACKEND_PID=$!
cd ..

echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
sleep 2

# Start Frontend
echo -e "${GREEN}🎨 Starting Frontend on port ${FRONTEND_PORT}...${NC}"
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  node_modules not found. Running npm install...${NC}"
    npm install
fi

# Start Nuxt dev server in background with proper env vars
NUXT_PORT=${FRONTEND_PORT} NUXT_PUBLIC_API_URL=http://localhost:${BACKEND_PORT} NUXT_PUBLIC_API_BASE_URL=http://localhost:${BACKEND_PORT}/api NUXT_PUBLIC_DEV_ENV=${ENV_NUM} npm run dev > ../logs/${ENV_NAME}-frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ Dev Environment ${ENV_NUM} is ready!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📝 Logs:${NC}"
echo -e "   Backend:  tail -f logs/${ENV_NAME}-backend.log"
echo -e "   Frontend: tail -f logs/${ENV_NAME}-frontend.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Create logs directory if it doesn't exist
mkdir -p logs

# Follow logs (both backend and frontend)
tail -f logs/${ENV_NAME}-backend.log -f logs/${ENV_NAME}-frontend.log
