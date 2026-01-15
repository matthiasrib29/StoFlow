# Backend Troubleshooting Guide

> Solutions aux erreurs communes du backend StoFlow.

---

## Alembic / Migrations

### "Target database is not up to date"

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

### "Multiple heads detected"

```bash
cd backend
alembic heads  # Voir les heads
alembic merge -m "merge heads" heads
alembic upgrade head
git add migrations/
git commit -m "chore: merge alembic heads"
```

### "Can't locate revision identified by '...'"

La révision référencée n'existe pas localement.

```bash
# Sync avec develop pour récupérer les migrations
git fetch origin develop
git merge origin/develop
alembic upgrade head
```

### "FAILED: Can't proceed with migration"

```bash
# Voir l'état actuel
alembic current

# Forcer une révision spécifique (DANGEREUX)
alembic stamp <revision>
alembic upgrade head
```

### Créer une nouvelle migration

```bash
cd backend
alembic revision --autogenerate -m "add user preferences table"
# TOUJOURS vérifier le fichier généré avant de committer
```

---

## SQLAlchemy

### "No such table" ou "relation does not exist"

Le search_path n'est pas configuré.

```python
# CORRECT
async with get_tenant_session(user_id) as session:
    result = await session.execute(select(Product))

# INCORRECT - ne pas utiliser la session globale
result = await db.execute(select(Product))
```

### "Object is already attached to session"

```python
# Utiliser merge au lieu de add pour objets existants
merged_obj = await session.merge(existing_obj)
await session.commit()
```

### "Connection pool exhausted"

```python
# Augmenter pool_size dans config
SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://..."
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=20,  # Default: 5
    max_overflow=30,  # Default: 10
)
```

### Deadlock détecté

```python
# Réduire la durée des transactions
async with get_tenant_session(user_id) as session:
    # Faire UNE chose, commit, puis autre chose
    await session.execute(...)
    await session.commit()
```

---

## FastAPI / Uvicorn

### "Address already in use"

```bash
# Trouver et tuer le processus (SEULEMENT serveur)
lsof -ti:8000 -sTCP:LISTEN | xargs -r kill -9
```

### Hot reload ne fonctionne pas

```bash
# Vérifier que uvicorn est lancé avec --reload
uvicorn main:app --reload --port 8000

# Vérifier que le fichier est dans le bon dossier
# (pas dans un sous-dossier ignoré)
```

### "422 Unprocessable Entity"

Erreur de validation Pydantic. Vérifier:
- Types des paramètres
- Champs requis manquants
- Format des données (ex: date ISO)

```python
# Voir les détails
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )
```

---

## WebSocket

### Connexion refusée

```bash
# Vérifier que le backend écoute
curl http://localhost:8000/docs

# Vérifier les CORS
# Dans main.py, s'assurer que origins inclut le client
```

### Déconnexion fréquente

```python
# Augmenter le ping interval
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Configurer ping/pong si nécessaire
```

### "WebSocket connection failed"

Vérifier:
1. URL correcte (ws:// ou wss://)
2. Port correct
3. Backend en cours d'exécution
4. Pas de proxy bloquant WebSocket

---

## JWT / Authentification

### "Token expired"

```python
# Le token a dépassé son TTL
# Client doit rafraîchir le token via /auth/refresh
```

### "Invalid token signature"

```bash
# Vérifier que SECRET_KEY est identique entre envs
echo $SECRET_KEY
```

### "User not found" après auth

```python
# L'utilisateur existe mais pas son schema
# Créer le schema tenant
await create_tenant_schema(user_id)
```

---

## Docker / PostgreSQL

### Container ne démarre pas

```bash
# Voir les logs
docker logs stoflow_postgres --tail 100

# Redémarrer
docker-compose down && docker-compose up -d
```

### "Connection refused" à PostgreSQL

```bash
# Attendre que PostgreSQL soit prêt
docker exec stoflow_postgres pg_isready -U stoflow_user

# Ou attendre manuellement
for i in {1..30}; do
  docker exec stoflow_postgres pg_isready -U stoflow_user && break
  sleep 1
done
```

### Espace disque plein (Docker)

```bash
# Nettoyer les images/containers inutilisés
docker system prune -a

# Nettoyer les volumes (ATTENTION: supprime les données!)
docker volume prune
```

---

## Performances

### Queries lentes

```python
# Activer le logging SQL
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### Memory leak

```bash
# Monitorer l'utilisation mémoire
ps aux | grep uvicorn

# Redémarrer périodiquement (dev seulement)
```

### CPU élevé

Vérifier:
- Boucles infinies
- Queries N+1
- Trop de logs en mode DEBUG

---

## Logs

### Trouver les erreurs récentes

```bash
# Dernières erreurs
grep -i error ~/StoFlow/backend/logs/*.log | tail -20

# Erreurs d'aujourd'hui
grep "$(date +%Y-%m-%d)" ~/StoFlow/backend/logs/*.log | grep -i error
```

### Logs trop volumineux

```bash
# Rotation manuelle
./rotate-logs.sh

# Ou automatique dans logrotate
```

---

## Multi-Worktree

### Schema déjà créé dans un autre worktree

Les schemas sont partagés (même DB). Si un autre worktree a créé le schema:

```bash
# Juste appliquer les migrations manquantes
alembic upgrade head
```

### Migrations en conflit

Deux worktrees ont créé des migrations avec le même parent.

```bash
# Dans le worktree problématique
git fetch origin develop
git merge origin/develop
alembic merge -m "merge heads" heads
alembic upgrade head
```

---

*Dernière mise à jour: 2026-01-13*
