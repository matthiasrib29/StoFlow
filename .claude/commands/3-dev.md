Lance l'environnement de dev 3 (Backend port 8002 + Frontend port 3002).

## Commande

Exécute : `./dev3.sh`

**IMPORTANT pour Claude** : Utiliser `run_in_background: true` dans le Bash tool pour que Claude reste disponible pendant que les serveurs tournent.

## Ce que fait le script

1. Vérifie que Docker est démarré
2. Lance les conteneurs Docker si nécessaire (PostgreSQL + Redis)
3. Kill les serveurs existants sur ports 8002 et 3002 (uniquement les serveurs, pas les clients)
4. Lance le backend (uvicorn) sur port 8002 en arrière-plan
5. Lance le frontend (npm run dev) sur port 3002 en arrière-plan
6. Configure le frontend avec `NUXT_PUBLIC_DEV_ENV=3` (favicon orange)

## URLs

- **Backend** : http://localhost:8002
- **Frontend** : http://localhost:3002
- **Favicon** : Orange avec "3"

## Logs

Consulter les logs en temps réel :
```bash
tail -f logs/dev3-backend.log
tail -f logs/dev3-frontend.log
```

## Arrêt

Appuyer sur **Ctrl+C** dans le terminal où le script tourne.
