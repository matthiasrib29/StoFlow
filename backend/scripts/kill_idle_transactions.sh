#!/bin/bash
#
# Kill Idle PostgreSQL Transactions
#
# Tue toutes les transactions "idle in transaction" de plus de 5 minutes
# pour éviter les deadlocks et les transactions bloquées.
#
# Usage:
#   ./scripts/kill_idle_transactions.sh
#
# Requirements:
#   - Docker avec container stoflow_postgres
#   - PostgreSQL accessible
#

set -e

echo "🔍 Recherche des transactions idle..."

# Compte les transactions idle > 5 minutes
IDLE_COUNT=$(docker exec stoflow_postgres psql -U stoflow_user -d stoflow_db -t -c "
SELECT COUNT(*)
FROM pg_stat_activity
WHERE datname = 'stoflow_db'
  AND state = 'idle in transaction'
  AND state_change < NOW() - INTERVAL '5 minutes';
" | tr -d ' ')

if [ "$IDLE_COUNT" -eq 0 ]; then
    echo "✅ Aucune transaction idle trouvée"
    exit 0
fi

echo "⚠️  $IDLE_COUNT transaction(s) idle détectée(s)"

# Liste les transactions avant de les tuer
echo ""
echo "Transactions qui seront tuées:"
echo "=============================="
docker exec stoflow_postgres psql -U stoflow_user -d stoflow_db -c "
SELECT pid, usename, state, state_change, query
FROM pg_stat_activity
WHERE datname = 'stoflow_db'
  AND state = 'idle in transaction'
  AND state_change < NOW() - INTERVAL '5 minutes'
ORDER BY state_change;
"

# Demande confirmation
read -p "Voulez-vous tuer ces transactions? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Opération annulée"
    exit 1
fi

# Tue les transactions
echo ""
echo "🔨 Arrêt des transactions idle..."
docker exec stoflow_postgres psql -U stoflow_user -d stoflow_db -c "
SELECT pg_terminate_backend(pid), pid, usename
FROM pg_stat_activity
WHERE datname = 'stoflow_db'
  AND state = 'idle in transaction'
  AND state_change < NOW() - INTERVAL '5 minutes';
"

echo ""
echo "✅ Terminé. $IDLE_COUNT transaction(s) arrêtée(s)"
