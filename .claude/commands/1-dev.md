Lance l'environnement de dev 1 (Backend port 8000 + Frontend port 3000).

## Commande

Exécute : `./1-dev.sh` (wrapper qui appelle `./scripts/dev.sh 1`)

**IMPORTANT pour Claude** : Utiliser `run_in_background: true` dans le Bash tool pour que Claude reste disponible pendant que les serveurs tournent.

## Ce que fait le script

1. Vérifie que Docker est démarré
2. Lance les conteneurs Docker si nécessaire (PostgreSQL + Redis)
3. Kill les serveurs existants sur ports 8000 et 3000 (uniquement les serveurs, pas les clients)
4. Lance le backend (uvicorn) sur port 8000 en arrière-plan
5. Lance le frontend (npm run dev) sur port 3000 en arrière-plan
6. Configure le frontend avec `NUXT_PUBLIC_DEV_ENV=1` (favicon bleu)

## URLs

- **Backend** : http://localhost:8000
- **Frontend** : http://localhost:3000
- **Favicon** : Bleu avec "1"

## Logs

Consulter les logs en temps réel :
```bash
tail -f logs/dev1-backend.log
tail -f logs/dev1-frontend.log
```

## Arrêt

Appuyer sur **Ctrl+C** dans le terminal où le script tourne.
