Lance l'environnement de dev 2 (Backend port 8001 + Frontend port 3001).

## Commande

Exécute : `./2-dev.sh`

**IMPORTANT pour Claude** : Utiliser `run_in_background: true` dans le Bash tool pour que Claude reste disponible pendant que les serveurs tournent.

## Ce que fait le script

1. Vérifie que Docker est démarré
2. Lance les conteneurs Docker si nécessaire (PostgreSQL + Redis)
3. Kill les serveurs existants sur ports 8001 et 3001 (uniquement les serveurs, pas les clients)
4. Lance le backend (uvicorn) sur port 8001 en arrière-plan
5. Lance le frontend (npm run dev) sur port 3001 en arrière-plan
6. Configure le frontend avec `NUXT_PUBLIC_DEV_ENV=2` (favicon vert)

## URLs

- **Backend** : http://localhost:8001
- **Frontend** : http://localhost:3001
- **Favicon** : Vert avec "2"

## Logs

Consulter les logs en temps réel :
```bash
tail -f logs/dev2-backend.log
tail -f logs/dev2-frontend.log
```

## Arrêt

Appuyer sur **Ctrl+C** dans le terminal où le script tourne.
