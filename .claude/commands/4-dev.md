Lance l'environnement de dev 4 (Backend port 8003 + Frontend port 3003).

## Commande

Exécute : `./4-dev.sh` (wrapper qui appelle `./scripts/dev.sh 4`)

**IMPORTANT pour Claude** : Utiliser `run_in_background: true` dans le Bash tool pour que Claude reste disponible pendant que les serveurs tournent.

## Ce que fait le script

1. Vérifie que Docker est démarré
2. Lance les conteneurs Docker si nécessaire (PostgreSQL + Redis)
3. Kill les serveurs existants sur ports 8003 et 3003 (uniquement les serveurs, pas les clients)
4. Lance le backend (uvicorn) sur port 8003 en arrière-plan
5. Lance le frontend (npm run dev) sur port 3003 en arrière-plan
6. Configure le frontend avec `NUXT_PUBLIC_DEV_ENV=4` (favicon violet)

## URLs

- **Backend** : http://localhost:8003
- **Frontend** : http://localhost:3003
- **Favicon** : Violet avec "4"

## Logs

Consulter les logs en temps réel :
```bash
tail -f logs/dev4-backend.log
tail -f logs/dev4-frontend.log
```

## Arrêt

Appuyer sur **Ctrl+C** dans le terminal où le script tourne.
