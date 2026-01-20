#!/bin/bash
# Start Celery beat scheduler for StoFlow
#
# Beat is responsible for scheduling periodic tasks.
# Only ONE beat instance should run at a time!
#
# Usage:
#   ./scripts/start_celery_beat.sh

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

# Log level from env or default to info
LOG_LEVEL="${CELERY_LOG_LEVEL:-info}"

# Beat schedule file location
SCHEDULE_FILE="${CELERY_BEAT_SCHEDULE_FILE:-/tmp/celerybeat-schedule}"

echo "Starting Celery beat scheduler..."
echo "  Schedule file: $SCHEDULE_FILE"
echo "  Log level: $LOG_LEVEL"

exec celery -A celery_app beat \
    --loglevel="$LOG_LEVEL" \
    --schedule="$SCHEDULE_FILE"
