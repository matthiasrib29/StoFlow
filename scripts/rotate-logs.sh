#!/bin/bash
# Log rotation script for StoFlow
# Cleans up old logs automatically to prevent disk space issues

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOG_RETENTION_DAYS=7
COMPRESS_AFTER_DAYS=2
MAX_BACKEND_LOG_SIZE_MB=10

echo -e "${BLUE}🔄 StoFlow Log Rotation${NC}"
echo ""

# Function to get directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Counter for cleaned files
DELETED_COUNT=0
COMPRESSED_COUNT=0
TRUNCATED_COUNT=0

# 1. Clean old dev logs (> 7 days) in main repo
echo -e "${YELLOW}📁 Cleaning logs in main repo...${NC}"
if [ -d "$PROJECT_ROOT/logs" ]; then
    OLD_LOGS=$(find "$PROJECT_ROOT/logs" -name "*.log" -type f -mtime +${LOG_RETENTION_DAYS} 2>/dev/null || true)
    if [ ! -z "$OLD_LOGS" ]; then
        echo "$OLD_LOGS" | while read -r logfile; do
            echo "  Deleting: $(basename "$logfile")"
            rm -f "$logfile"
            DELETED_COUNT=$((DELETED_COUNT + 1))
        done
    fi
fi

# 2. Clean old dev logs in all worktrees
echo -e "${YELLOW}📁 Cleaning logs in worktrees...${NC}"
for worktree_dir in "$HOME"/StoFlow-*; do
    if [ -d "$worktree_dir/logs" ]; then
        OLD_LOGS=$(find "$worktree_dir/logs" -name "*.log" -type f -mtime +${LOG_RETENTION_DAYS} 2>/dev/null || true)
        if [ ! -z "$OLD_LOGS" ]; then
            echo "$OLD_LOGS" | while read -r logfile; do
                echo "  Deleting: $(basename "$worktree_dir")/logs/$(basename "$logfile")"
                rm -f "$logfile"
                DELETED_COUNT=$((DELETED_COUNT + 1))
            done
        fi
    fi
done

# 3. Compress logs older than 2 days (but keep last 7 days)
echo -e "${YELLOW}📦 Compressing old logs...${NC}"
for logs_dir in "$PROJECT_ROOT/logs" "$HOME"/StoFlow-*/logs; do
    if [ -d "$logs_dir" ]; then
        OLD_LOGS=$(find "$logs_dir" -name "*.log" -type f -mtime +${COMPRESS_AFTER_DAYS} ! -name "*.gz" 2>/dev/null || true)
        if [ ! -z "$OLD_LOGS" ]; then
            echo "$OLD_LOGS" | while read -r logfile; do
                echo "  Compressing: $(basename "$logfile")"
                gzip -f "$logfile" 2>/dev/null || true
                COMPRESSED_COUNT=$((COMPRESSED_COUNT + 1))
            done
        fi
    fi
done

# 4. Truncate large backend logs (> 10 MB)
echo -e "${YELLOW}✂️  Truncating large backend logs...${NC}"
for backend_log in "$PROJECT_ROOT/backend/logs/stoflow.log" "$HOME"/StoFlow-*/backend/logs/stoflow.log; do
    if [ -f "$backend_log" ]; then
        LOG_SIZE_MB=$(du -m "$backend_log" | cut -f1)
        if [ "$LOG_SIZE_MB" -gt "$MAX_BACKEND_LOG_SIZE_MB" ]; then
            echo "  Truncating: $backend_log (${LOG_SIZE_MB}MB -> 0MB)"
            # Keep last 1000 lines before truncating
            tail -1000 "$backend_log" > "${backend_log}.tmp"
            mv "${backend_log}.tmp" "$backend_log"
            TRUNCATED_COUNT=$((TRUNCATED_COUNT + 1))
        fi
    fi
done

# 5. Clean compressed logs older than retention period
echo -e "${YELLOW}🗑️  Removing old compressed logs...${NC}"
for logs_dir in "$PROJECT_ROOT/logs" "$HOME"/StoFlow-*/logs; do
    if [ -d "$logs_dir" ]; then
        OLD_GZ=$(find "$logs_dir" -name "*.log.gz" -type f -mtime +${LOG_RETENTION_DAYS} 2>/dev/null || true)
        if [ ! -z "$OLD_GZ" ]; then
            echo "$OLD_GZ" | while read -r gzfile; do
                echo "  Deleting: $(basename "$gzfile")"
                rm -f "$gzfile"
                DELETED_COUNT=$((DELETED_COUNT + 1))
            done
        fi
    fi
done

# Summary
echo ""
echo -e "${GREEN}✅ Log rotation complete${NC}"
echo -e "   Files deleted: $DELETED_COUNT"
echo -e "   Files compressed: $COMPRESSED_COUNT"
echo -e "   Backend logs truncated: $TRUNCATED_COUNT"
echo ""

# Calculate total disk usage
TOTAL_LOGS_SIZE=$(du -sh "$PROJECT_ROOT/logs" 2>/dev/null | cut -f1 || echo "0")
BACKEND_LOGS_SIZE=$(du -sh "$PROJECT_ROOT/backend/logs" 2>/dev/null | cut -f1 || echo "0")
echo -e "${BLUE}📊 Current log sizes:${NC}"
echo -e "   Dev logs:     $TOTAL_LOGS_SIZE"
echo -e "   Backend logs: $BACKEND_LOGS_SIZE"
