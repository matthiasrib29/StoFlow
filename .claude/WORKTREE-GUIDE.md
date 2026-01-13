# Guide Worktree StoFlow

> Guide complet pour le développement multi-worktree avec Claude Code.

---

## Commandes rapides

| Action | Commande |
|--------|----------|
| Nouvelle feature (dev 1) | `/1-new-feature` |
| Nouvelle feature (dev 2) | `/2-new-feature` |
| Nouvelle feature (dev 3) | `/3-new-feature` |
| Nouvelle feature (dev 4) | `/4-new-feature` |
| Nouveau hotfix (dev 1) | `/1-new-hotfix` |
| Nouveau hotfix (dev 2) | `/2-new-hotfix` |
| Nouveau hotfix (dev 3) | `/3-new-hotfix` |
| Nouveau hotfix (dev 4) | `/4-new-hotfix` |
| Sync avec develop | `/sync` |
| Terminer et merger | `/finish` |
| Voir état complet | `/status` |
| Arrêter tous les services | `/stop` |

---

## Architecture

```
~/StoFlow/              <- Repo principal (READ-ONLY pour dev)
├── develop             <- Branche principale
│
~/StoFlow-feature-x/    <- Worktree 1 (feature/feature-x)
├── Env dev 1: ports 8000/3000
│
~/StoFlow-feature-y/    <- Worktree 2 (feature/feature-y)
├── Env dev 2: ports 8001/3001
│
~/StoFlow-hotfix-z/     <- Worktree 3 (hotfix/hotfix-z)
├── Env dev 3: ports 8002/3002
│
~/StoFlow-feature-w/    <- Worktree 4 (feature/feature-w)
├── Env dev 4: ports 8003/3003
│
└── Tous partagent:
    └── Docker PostgreSQL (port 5433)
    └── Docker Redis (port 6379)
```

---

## Mapping des ports

| Environnement | Backend | Frontend | Script |
|---------------|---------|----------|--------|
| Dev 1 | 8000 | 3000 | `1-dev.sh` |
| Dev 2 | 8001 | 3001 | `2-dev.sh` |
| Dev 3 | 8002 | 3002 | `3-dev.sh` |
| Dev 4 | 8003 | 3003 | `4-dev.sh` |

---

## Troubleshooting

### "Target database is not up to date"

```bash
cd backend && alembic upgrade head
```

### "Multiple heads detected"

```bash
cd backend
alembic merge -m "merge heads" heads
alembic upgrade head
git add migrations/
git commit -m "chore: merge alembic heads"
```

### "Can't locate revision"

```bash
# Synchroniser avec develop
git fetch origin develop
git merge origin/develop
cd backend && alembic upgrade head
```

### Worktree corrompu

```bash
# Supprimer et recréer
git worktree remove ~/StoFlow-[nom] --force
git branch -D feature/[nom]
# Puis relancer /X-new-feature
```

### Conflit de port

```bash
# Vérifier qui utilise le port (SEULEMENT les serveurs)
lsof -ti:8000 -sTCP:LISTEN

# Tuer le processus serveur
lsof -ti:8000 -sTCP:LISTEN | xargs -r kill -9
```

> **Important**: Toujours utiliser `-sTCP:LISTEN` pour ne pas tuer les clients (Firefox, etc.)

### npm install bloqué ou échoue

```bash
# Nettoyer le cache npm
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

### Backend ne démarre pas

```bash
# Vérifier que PostgreSQL est prêt
docker exec stoflow_postgres pg_isready -U stoflow_user

# Vérifier les logs Docker
docker logs stoflow_postgres --tail 50

# Redémarrer les containers
docker-compose restart
```

### WebSocket ne se connecte pas

```bash
# Vérifier que le backend écoute
curl http://localhost:8000/docs

# Vérifier les logs backend pour erreurs WebSocket
tail -f ~/StoFlow-[nom]/backend/logs/*.log
```

---

## Workflow typique

### 1. Nouvelle feature

```bash
# 1. Lancer /1-new-feature (ou /2, /3, /4)
# 2. Donner un nom (ex: add-analytics)
# 3. Attendre initialisation (npm install, migrations)
# 4. Travailler dans ~/StoFlow-add-analytics/
# 5. Tester sur http://localhost:8000 et :3000
# 6. Quand fini: /finish
```

### 2. Hotfix urgent

```bash
# 1. Lancer /1-new-hotfix
# 2. Donner un nom (ex: fix-login)
# 3. Corriger le bug dans ~/StoFlow-fix-login/
# 4. Tester rapidement
# 5. /finish pour merger
```

### 3. Sync avec develop (long feature)

```bash
# Dans le worktree de la feature
/sync
# Cela fait:
# - Backup automatique
# - git fetch + rebase
# - alembic upgrade head
```

---

## Règles importantes

1. **Ne JAMAIS modifier ~/StoFlow** directement
2. **Toujours travailler dans ~/StoFlow-[nom]/**
3. **Un worktree = une branche = un environnement**
4. **Ne pas lancer 2 devs sur les mêmes ports**
5. **Utiliser /status pour voir l'état global**

---

## Fichiers copiés automatiquement

Lors de la création d'un worktree, ces fichiers sont copiés depuis ~/StoFlow:

- `backend/.env` - Configuration backend
- `frontend/.env` - Configuration frontend
- `backend/keys/` - Clés de chiffrement

Ces fichiers sont définis dans `.worktreeinclude`.

---

## Scripts automatiques

### worktree-init.sh

Exécuté automatiquement après création du worktree:
1. `npm install` dans frontend (si node_modules manquant)
2. `npm install` dans plugin (si node_modules manquant)
3. `alembic upgrade head` dans backend

### X-dev.sh

Exécuté pour lancer l'environnement:
1. `docker-compose up -d` (PostgreSQL + Redis)
2. Attendre que PostgreSQL soit prêt (30s timeout)
3. `alembic upgrade head` (migrations)
4. Lancer `uvicorn` (backend, hot-reload)
5. Lancer `npm run dev` (frontend, HMR)

---

*Dernière mise à jour: 2026-01-13*
