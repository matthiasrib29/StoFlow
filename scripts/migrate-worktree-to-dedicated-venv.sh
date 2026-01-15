#!/bin/bash
# scripts/migrate-worktree-to-dedicated-venv.sh
# Migrates an existing worktree from symlinked venv to dedicated venv

set -e

WORKTREE_DIR="$1"

if [ -z "$WORKTREE_DIR" ]; then
    echo "Usage: ./scripts/migrate-worktree-to-dedicated-venv.sh ~/StoFlow-[nom]"
    exit 1
fi

if [ ! -d "$WORKTREE_DIR" ]; then
    echo "❌ Dossier inexistant : $WORKTREE_DIR"
    exit 1
fi

cd "$WORKTREE_DIR"
./scripts/setup-worktree-venv.sh

echo ""
echo "✅ Migration complète pour $WORKTREE_DIR"
echo "⚠️  Pensez à redémarrer les serveurs (/stop puis /X-dev)"
