#!/bin/bash
# Start Celery worker for StoFlow
#
# Usage:
#   ./scripts/start_celery_worker.sh           # Default: all queues
#   ./scripts/start_celery_worker.sh marketplace  # Only marketplace queue
#   ./scripts/start_celery_worker.sh cleanup notifications  # Multiple queues

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

# Default queues
QUEUES="${@:-default,marketplace,cleanup,notifications}"

# Log level from env or default to info
LOG_LEVEL="${CELERY_LOG_LEVEL:-info}"

# Concurrency from env or default to 4
CONCURRENCY="${CELERY_WORKER_CONCURRENCY:-4}"

echo "Starting Celery worker..."
echo "  Queues: $QUEUES"
echo "  Concurrency: $CONCURRENCY"
echo "  Log level: $LOG_LEVEL"

exec celery -A celery_app worker \
    --queues="$QUEUES" \
    --loglevel="$LOG_LEVEL" \
    --concurrency="$CONCURRENCY" \
    --hostname="worker@%h"
