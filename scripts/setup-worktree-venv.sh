#!/bin/bash
# scripts/setup-worktree-venv.sh
# Creates a dedicated venv for the current worktree

set -e

cd "$(dirname "$0")/.."

echo "🔧 Configuration du venv dédié pour ce worktree..."

# Remove symlink if present
if [ -L "backend/.venv" ] || [ -L "backend/venv" ]; then
    echo "⚠️  Symlink détecté, suppression..."
    rm -f backend/.venv backend/venv
fi

# Create venv if necessary
if [ -d "backend/.venv" ]; then
    echo "✅ Venv déjà existant"
else
    echo "📦 Création du venv..."
    cd backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✅ Venv créé et dépendances installées"
fi
