Arrête tous les services de dev :

## Calcul des ports dynamiques

Même logique que `/dev` :

```bash
WORKTREE_NAME=$(basename "$PWD")

if [ "$WORKTREE_NAME" = "StoFlow" ]; then
  PORT_OFFSET=0
else
  PORT_OFFSET=$(echo -n "$WORKTREE_NAME" | md5sum | tr -d -c '0-9' | cut -c1-2)
  PORT_OFFSET=$((10#$PORT_OFFSET % 99 + 1))
fi

BACKEND_PORT=$((8000 + PORT_OFFSET))
FRONTEND_PORT=$((3000 + PORT_OFFSET))
```

## Commandes (dans l'ordre)

1. **Afficher** : `echo "🛑 Stopping worktree: $WORKTREE_NAME | Backend: $BACKEND_PORT | Frontend: $FRONTEND_PORT"`
2. **Backend** : `lsof -ti:$BACKEND_PORT -sTCP:LISTEN | xargs -r kill -9` (tue uniquement le serveur, pas les clients)
3. **Frontend** : `lsof -ti:$FRONTEND_PORT -sTCP:LISTEN | xargs -r kill -9` (tue uniquement le serveur, pas les clients)
4. **Docker** : `cd backend && docker compose stop` (stop, pas down - conserve les données)

## Note

- Utiliser `-sTCP:LISTEN` pour ne tuer que les serveurs, pas Firefox ou autres clients connectés
- Utiliser `docker compose stop` plutôt que `down` pour conserver les volumes
