#!/bin/bash
# cleanup-worktrees.sh
# Nettoie les worktrees dont les branches ont été mergées dans develop

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🧹 Cleaning merged worktrees...${NC}"
echo ""

cd ~/StoFlow

# List current worktrees
echo "=== Current worktrees ==="
git worktree list
echo ""

# Find merged branches (feature/* or hotfix/*)
MERGED_BRANCHES=$(git branch --merged develop | grep -E "^\s*(feature/|hotfix/)" | tr -d ' ' || true)

if [ -z "$MERGED_BRANCHES" ]; then
    echo -e "${GREEN}✅ No merged branches to clean up${NC}"
    echo ""
    # Still prune orphaned worktrees
    echo "=== Pruning orphaned worktrees ==="
    git worktree prune -v
    exit 0
fi

echo "=== Merged branches found ==="
echo "$MERGED_BRANCHES"
echo ""

# Process each merged branch
for branch in $MERGED_BRANCHES; do
    # Find worktree for this branch
    WORKTREE=$(git worktree list | grep "$branch" | awk '{print $1}' || true)

    if [ -n "$WORKTREE" ] && [ "$WORKTREE" != "$(pwd)" ]; then
        echo -e "${YELLOW}Removing worktree: $WORKTREE ($branch)${NC}"

        # Check for uncommitted changes
        if [ -n "$(git -C "$WORKTREE" status --porcelain 2>/dev/null)" ]; then
            echo -e "${RED}⚠️  Warning: $WORKTREE has uncommitted changes!${NC}"
            echo "   Skipping this worktree. Clean it manually if needed."
            continue
        fi

        # Remove worktree
        git worktree remove "$WORKTREE" 2>/dev/null || {
            echo -e "${YELLOW}   Force removing...${NC}"
            git worktree remove "$WORKTREE" --force
        }

        echo -e "${GREEN}   ✅ Worktree removed${NC}"
    fi

    # Delete the branch
    echo -e "${YELLOW}Deleting branch: $branch${NC}"
    git branch -d "$branch" 2>/dev/null || {
        echo -e "${RED}   Could not delete branch (may have unmerged changes)${NC}"
    }
    echo ""
done

# Prune orphaned worktrees
echo "=== Pruning orphaned worktrees ==="
git worktree prune -v

echo ""
echo -e "${GREEN}✅ Cleanup complete${NC}"
echo ""

# Show final state
echo "=== Final worktree state ==="
git worktree list
