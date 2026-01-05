Lance l'environnement de dev :

## Ports utilisés

- **Backend** : `http://localhost:8000`
- **Frontend** : `http://localhost:3000`

## Étapes

1. **Docker** : `cd backend && docker compose up -d` (ou `docker start` si conteneurs existent)
2. **Backend** : Tuer UNIQUEMENT le serveur sur port 8000 (pas les clients), puis lancer uvicorn
3. **Frontend** : Tuer UNIQUEMENT le serveur sur port 3000, puis lancer npm run dev

## Commandes pour kill propre (IMPORTANT)

Pour tuer uniquement les SERVEURS (pas les clients connectés) :
- Backend : `lsof -ti:8000 -sTCP:LISTEN | xargs -r kill -9`
- Frontend : `lsof -ti:3000 -sTCP:LISTEN | xargs -r kill -9`

NE JAMAIS utiliser `lsof -ti:PORT | xargs kill` car ça tue aussi Firefox et autres clients connectés !

## Lancement des serveurs

- Backend : `cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000`
- Frontend : `cd frontend && npm run dev`

## Plugin

Rebuild avec `cd plugin && npm run build` si nécessaire.
