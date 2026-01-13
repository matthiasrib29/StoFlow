Arrête tous les services de dev :

## Ports fixes par environnement

| Env | Backend | Frontend |
|-----|---------|----------|
| dev1 (~/StoFlow) | 8000 | 3000 |
| dev2 | 8001 | 3001 |
| dev3 | 8002 | 3002 |
| dev4 | 8003 | 3003 |

## Détection automatique

```bash
WORKTREE_NAME=$(basename "$PWD")

# Déterminer l'environnement basé sur le worktree
case "$WORKTREE_NAME" in
  StoFlow)
    ENV_NUM=1
    ;;
  *)
    # Extraire le numéro de l'env depuis les logs ou utiliser dev1 par défaut
    # On cherche dans quel env le worktree a été lancé
    ENV_NUM=1  # Default
    for i in 1 2 3 4; do
      BACKEND_PORT=$((8000 + i - 1))
      if lsof -ti:$BACKEND_PORT -sTCP:LISTEN >/dev/null 2>&1; then
        # Vérifier si c'est le bon worktree
        ENV_NUM=$i
        break
      fi
    done
    ;;
esac

BACKEND_PORT=$((8000 + ENV_NUM - 1))
FRONTEND_PORT=$((3000 + ENV_NUM - 1))
```

## Commandes

1. **Afficher** : `echo "🛑 Stopping env $ENV_NUM | Backend: $BACKEND_PORT | Frontend: $FRONTEND_PORT"`
2. **Backend** : `lsof -ti:$BACKEND_PORT -sTCP:LISTEN | xargs -r kill -9` (tue uniquement le serveur, pas les clients)
3. **Frontend** : `lsof -ti:$FRONTEND_PORT -sTCP:LISTEN | xargs -r kill -9` (tue uniquement le serveur, pas les clients)
4. **Docker** : `cd ~/StoFlow/backend && docker compose stop` (stop, pas down - conserve les données)

## Alternative : Arrêter un environnement spécifique

Si l'utilisateur demande d'arrêter un env spécifique :
```bash
# /stop 2 → arrête env dev2
ENV_NUM=$1
BACKEND_PORT=$((8000 + ENV_NUM - 1))
FRONTEND_PORT=$((3000 + ENV_NUM - 1))
lsof -ti:$BACKEND_PORT -sTCP:LISTEN | xargs -r kill -9
lsof -ti:$FRONTEND_PORT -sTCP:LISTEN | xargs -r kill -9
```

## Note

- Utiliser `-sTCP:LISTEN` pour ne tuer que les serveurs, pas Firefox ou autres clients connectés
- Utiliser `docker compose stop` plutôt que `down` pour conserver les volumes
- Les ports sont FIXES et correspondent aux scripts `/X-dev.sh`

---

*Mis à jour : 2026-01-13*
