Lance l'environnement de dev (Backend + Frontend) sur un des 4 environnements disponibles.

**IMPORTANT pour Claude** : Utiliser `run_in_background: true` dans le Bash tool pour que Claude reste disponible pendant que les serveurs tournent.

## Workflow

1. **Demander à l'utilisateur quel environnement lancer** avec AskUserQuestion:
   - Header: "Env de dev"
   - Question: "Quel environnement de dev veux-tu lancer ?"
   - Options:
     - "Env 1 (ports 8000/3000)" → description: "Backend sur 8000, Frontend sur 3000, favicon bleu"
     - "Env 2 (ports 8001/3001)" → description: "Backend sur 8001, Frontend sur 3001, favicon vert"
     - "Env 3 (ports 8002/3002)" → description: "Backend sur 8002, Frontend sur 3002, favicon orange"
     - "Env 4 (ports 8003/3003)" → description: "Backend sur 8003, Frontend sur 3003, favicon rouge"

2. **Exécuter le script** avec Bash:
   ```bash
   cd ~/StoFlow && ./scripts/dev.sh [1-4]
   ```

## Ce que fait le script

1. Vérifie que Docker est démarré
2. Lance les conteneurs Docker si nécessaire (PostgreSQL + Redis)
3. Kill les serveurs existants sur les ports (uniquement les serveurs, pas les clients)
4. Lance le backend (uvicorn) en arrière-plan
5. Lance le frontend (npm run dev) en arrière-plan
6. Configure le frontend avec `NUXT_PUBLIC_DEV_ENV=X` (favicon couleur)

## Logs

Consulter les logs en temps réel selon l'env choisi :
```bash
tail -f logs/dev1-backend.log logs/dev1-frontend.log   # Env 1
tail -f logs/dev2-backend.log logs/dev2-frontend.log   # Env 2
tail -f logs/dev3-backend.log logs/dev3-frontend.log   # Env 3
tail -f logs/dev4-backend.log logs/dev4-frontend.log   # Env 4
```

## Arrêt

Utiliser `/stop` ou appuyer sur **Ctrl+C** dans le terminal où le script tourne.
