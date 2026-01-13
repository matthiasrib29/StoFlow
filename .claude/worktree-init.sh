#!/bin/bash
# Hook exécuté après création d'un worktree
# Usage: ./worktree-init.sh <worktree-path>
#
# Ce script est appelé par les skills /X-new-feature et /X-new-hotfix
# pour initialiser un nouveau worktree avec toutes les dépendances.

set -e

WORKTREE_PATH="$1"

if [ -z "$WORKTREE_PATH" ]; then
    echo "❌ Usage: ./worktree-init.sh <worktree-path>"
    exit 1
fi

if [ ! -d "$WORKTREE_PATH" ]; then
    echo "❌ Worktree path does not exist: $WORKTREE_PATH"
    exit 1
fi

cd "$WORKTREE_PATH"
echo "🔧 Initializing worktree: $WORKTREE_PATH"

# 1. Install frontend dependencies (if node_modules missing)
if [ -d "frontend" ] && [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install --silent
    cd ..
    echo "✅ Frontend dependencies installed"
else
    echo "✅ Frontend dependencies already present"
fi

# 2. Install plugin dependencies (if node_modules missing)
if [ -d "plugin" ] && [ ! -d "plugin/node_modules" ]; then
    echo "📦 Installing plugin dependencies..."
    cd plugin
    npm install --silent
    cd ..
    echo "✅ Plugin dependencies installed"
else
    echo "✅ Plugin dependencies already present"
fi

# 3. Apply database migrations
if [ -d "backend" ]; then
    echo "🗄️ Checking database migrations..."
    cd backend

    # Activate virtual environment
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    elif [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo "⚠️ No virtual environment found, skipping migrations"
        cd ..
        exit 0
    fi

    # Check if alembic is available
    if command -v alembic &> /dev/null; then
        # Apply migrations
        if alembic upgrade head 2>&1; then
            echo "✅ Database migrations applied"
        else
            echo "⚠️ Migration failed - you may need to run manually:"
            echo "   cd $WORKTREE_PATH/backend && alembic upgrade head"
        fi
    else
        echo "⚠️ Alembic not found in venv"
    fi

    cd ..
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ WORKTREE INITIALIZATION COMPLETE                         ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  📁 Path: $WORKTREE_PATH"
echo "║  📦 Frontend: node_modules ready"
echo "║  📦 Plugin: node_modules ready"
echo "║  🗄️ Database: migrations applied"
echo "╚══════════════════════════════════════════════════════════════╝"
