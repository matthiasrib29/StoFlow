#!/bin/bash
# Start marketplace job worker for a specific user
#
# Usage:
#   ./start_job_worker.sh <user_id> [workers] [marketplace]
#
# Examples:
#   ./start_job_worker.sh 1              # User 1, 4 workers, all marketplaces
#   ./start_job_worker.sh 1 8            # User 1, 8 workers, all marketplaces
#   ./start_job_worker.sh 1 4 ebay       # User 1, 4 workers, eBay only

set -e

USER_ID=${1:-1}
WORKERS=${2:-4}
MARKETPLACE=${3:-""}

# Navigate to backend directory
cd "$(dirname "$0")/.."

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "Starting marketplace job worker..."
echo "  User ID: $USER_ID"
echo "  Workers: $WORKERS"
echo "  Marketplace: ${MARKETPLACE:-all}"

# Start the worker
exec python -m worker.marketplace_worker \
    --user-id=$USER_ID \
    --workers=$WORKERS \
    ${MARKETPLACE:+--marketplace=$MARKETPLACE} \
    --log-level=INFO
