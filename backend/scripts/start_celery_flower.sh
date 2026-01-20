#!/bin/bash
# Start Celery Flower monitoring UI for StoFlow
#
# Flower provides a real-time web interface for monitoring Celery tasks.
#
# Usage:
#   ./scripts/start_celery_flower.sh
#
# Access: http://localhost:5555

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

cd "$BACKEND_DIR"

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Flower port from env or default
FLOWER_PORT="${FLOWER_PORT:-5555}"

# Basic auth (optional, recommended for production)
FLOWER_AUTH="${FLOWER_BASIC_AUTH:-}"

echo "Starting Celery Flower..."
echo "  Port: $FLOWER_PORT"
echo "  URL: http://localhost:$FLOWER_PORT"

FLOWER_ARGS=(
    "-A" "celery_app"
    "flower"
    "--port=$FLOWER_PORT"
    "--persistent=true"
    "--db=/tmp/flower.db"
)

# Add basic auth if configured
if [ -n "$FLOWER_AUTH" ]; then
    FLOWER_ARGS+=("--basic_auth=$FLOWER_AUTH")
    echo "  Auth: enabled"
fi

exec celery "${FLOWER_ARGS[@]}"
