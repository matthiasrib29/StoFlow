Lance l'environnement de dev :

## Calcul des ports dynamiques

Détermine les ports en fonction du worktree actuel :

```bash
WORKTREE_NAME=$(basename "$PWD")

if [ "$WORKTREE_NAME" = "StoFlow" ]; then
  PORT_OFFSET=0
else
  # Hash du nom du worktree -> offset entre 1 et 99
  PORT_OFFSET=$(echo -n "$WORKTREE_NAME" | md5sum | tr -d -c '0-9' | cut -c1-2)
  PORT_OFFSET=$((10#$PORT_OFFSET % 99 + 1))
fi

BACKEND_PORT=$((8000 + PORT_OFFSET))
FRONTEND_PORT=$((3000 + PORT_OFFSET))
```

Affiche les ports utilisés au début du lancement.

## Étapes

1. **Afficher les ports** : `echo "🚀 Worktree: $WORKTREE_NAME | Backend: $BACKEND_PORT | Frontend: $FRONTEND_PORT"`
2. **Docker** : `cd backend && docker compose up -d` (ou `docker start` si conteneurs existent)
3. **Backend** : Tuer UNIQUEMENT le serveur sur port $BACKEND_PORT (pas les clients), puis lancer uvicorn sur ce port
4. **Frontend** : Tuer UNIQUEMENT le serveur sur port $FRONTEND_PORT, puis lancer npm run dev sur ce port

## Commandes pour kill propre (IMPORTANT)

Pour tuer uniquement les SERVEURS (pas les clients connectés) :
- Backend : `lsof -ti:$BACKEND_PORT -sTCP:LISTEN | xargs -r kill -9`
- Frontend : `lsof -ti:$FRONTEND_PORT -sTCP:LISTEN | xargs -r kill -9`

NE JAMAIS utiliser `lsof -ti:PORT | xargs kill` car ça tue aussi Firefox et autres clients connectés !

## Lancement des serveurs

- Backend : `cd backend && source venv/bin/activate && uvicorn main:app --reload --port $BACKEND_PORT`
- Frontend : `cd frontend && NUXT_PORT=$FRONTEND_PORT npm run dev -- --port $FRONTEND_PORT`

## Plugin

Rebuild avec `cd plugin && npm run build` (le plugin utilise toujours localhost:8000, à adapter manuellement si besoin)
