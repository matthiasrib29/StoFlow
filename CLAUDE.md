# CLAUDE.md - StoFlow Monorepo

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Note**: General rules (language, security, git, debugging) are defined in `~/.claude/CLAUDE.md` (global config).
> This file contains **StoFlow-specific** rules and architecture details.

---

## 🛡️ Git Worktree - Règles StoFlow (CRITIQUE)

> **Contexte** : Règles ajoutées après perte de ~8000 lignes de code (2026-01-12).
> Les règles Git générales sont dans `~/.claude/CLAUDE.md` (commandes interdites, protection contre perte de données).

### Règle Principale

**`~/StoFlow` (repo principal) est READ-ONLY pour le développement manuel.**

Tout le travail doit se faire dans des **worktrees** (`~/StoFlow-*`).

> **Note** : Les skills `/finish` et `/sync` peuvent automatiquement modifier `~/StoFlow` (pull, merge) mais avec des vérifications de sécurité préalables.

### Workflow Obligatoire

```
1. Créer worktree    : /1-new-feature ou /2-new-feature
2. Travailler dans   : ~/StoFlow-[nom]/
3. Terminer avec     : /finish (depuis le worktree)
4. NE JAMAIS         : Committer directement sur develop dans ~/StoFlow
```

### Vérifications Automatiques (skills /finish et /sync)

Avant toute opération sur `~/StoFlow`, les skills vérifient :
1. ✅ Pas de changements non commités
2. ✅ Pas de commits locaux non poussés
3. ✅ Confirmation utilisateur si problème détecté

### 🚨 Création de PLAN.md (CRITIQUE - ajouté 2026-01-19)

> **Contexte** : Après un `/clear`, Claude perd le contexte et revient sur `~/StoFlow` (develop).
> Si le plan ne spécifie pas le worktree, l'exécution se fera sur le mauvais répertoire !

**RÈGLE OBLIGATOIRE :**

Lors de la création d'un `PLAN.md`, **TOUJOURS** commencer par indiquer le worktree :

```markdown
# Plan: [Nom de la feature]

## 🎯 Worktree de travail
**Chemin**: `~/StoFlow-[nom-feature]`
**Branche**: `feature/[nom]`

⚠️ IMPORTANT: Exécuter `cd ~/StoFlow-[nom-feature]` AVANT toute action !

## Étapes
...
```

**Pourquoi c'est critique :**
1. `/clear` efface le contexte de conversation
2. Claude revient par défaut sur `~/StoFlow` (develop)
3. Sans indication explicite du worktree, le plan s'exécute sur develop
4. Risque de commits directs sur develop = **INTERDIT**

**Checklist avant de finaliser un plan :**
- [ ] Le worktree est indiqué EN PREMIER dans le plan
- [ ] Le chemin complet est spécifié (`~/StoFlow-xxx`)
- [ ] Une instruction `cd` explicite est présente

---

## Project Overview

**StoFlow** is an e-commerce management application for multi-channel selling:
- **Backend**: FastAPI REST API with PostgreSQL multi-tenant architecture
- **Frontend**: Nuxt.js web application (Vue 3 + Composition API)
- **Plugin**: Browser extension (Firefox/Chrome) for marketplace integrations

---

## Repository Structure

```
StoFlow/
├── backend/         # FastAPI API server
├── frontend/        # Nuxt.js web application
├── plugin/          # Browser extension (Vinted integration)
├── CLAUDE.md        # This file (project guidelines)
├── README.md        # Project documentation
└── .gitignore       # Git ignore rules
```

---

## Module-Specific Guidelines

Each module has its own CLAUDE.md with detailed instructions:
- [backend/CLAUDE.md](backend/CLAUDE.md) - Backend API development
- [frontend/CLAUDE.md](frontend/CLAUDE.md) - Frontend development
- [plugin/CLAUDE.md](plugin/CLAUDE.md) - Browser extension development

---

## Quick Start Commands

### Backend (FastAPI)
```bash
cd backend
source .venv/bin/activate        # Activate virtual env
docker-compose up -d             # Start PostgreSQL + Redis
alembic upgrade head             # Apply migrations
uvicorn main:app --reload        # Start dev server (port 8000)
```

### Frontend (Nuxt.js)
```bash
cd frontend
npm install                      # Install dependencies
npm run dev                      # Start dev server (port 3000)
```

### Plugin (Browser Extension)
```bash
cd plugin
npm install                      # Install dependencies
npm run dev                      # Start dev build with watch
npm run build                    # Production build
```

---

## 🔄 Serveurs de Dev - Hot Reload (IMPORTANT)

> **Règle ajoutée 2026-01-13** : Éviter les processus dupliqués

### Principe

Les serveurs lancés par `/X-dev` sont en **mode hot-reload** :
- **Backend (uvicorn)** : `--reload` → redémarre automatiquement après modification `.py`
- **Frontend (Nuxt)** : hot-reload natif → met à jour automatiquement après modification

### ⛔ INTERDIT après lancement de `/X-dev`

| Action | Pourquoi c'est interdit |
|--------|------------------------|
| Relancer `uvicorn` manuellement | Crée un processus dupliqué, conflit de port |
| Relancer `npm run dev` manuellement | Crée un processus dupliqué, conflit de port |
| Lancer le backend "pour voir les logs" | Utiliser `tail -f logs/devX-backend.log` à la place |
| Lancer le frontend "pour voir les erreurs" | Utiliser `tail -f logs/devX-frontend.log` à la place |

### ✅ Comportement attendu

```
Après /X-dev lancé :
1. Modifier le code → Le serveur se recharge AUTOMATIQUEMENT
2. Besoin des logs → tail -f logs/devX-backend.log
3. Besoin de redémarrer complètement → /stop puis /X-dev
```

### Si erreur de syntaxe bloque le serveur

Le hot-reload peut échouer si le code a une erreur de syntaxe. Dans ce cas :
1. **Corriger l'erreur** dans le code
2. **Sauvegarder** → le serveur redémarre automatiquement
3. **NE PAS** relancer manuellement uvicorn/npm

### Si vraiment besoin de redémarrer

```bash
# Option 1 : Utiliser /stop
/stop  # puis /X-dev

# Option 2 : Kill manuel du port spécifique
lsof -ti:8000 -sTCP:LISTEN | xargs -r kill -9  # Backend
lsof -ti:3000 -sTCP:LISTEN | xargs -r kill -9  # Frontend
# Puis /X-dev
```

---

## 💻 Stack Technique

### Backend (Python)
- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Database**: PostgreSQL
- **Migrations**: Alembic
- **Tests**: Pytest (unit + integration)
- **Architecture**: Clean Architecture (Services, Repositories, Entities)

### Frontend (JavaScript/TypeScript)
- **Framework**: Vue.js / Nuxt.js
- **Style**: Composition API (`setup()`, `ref()`, `computed()`)
- **CSS**: Tailwind CSS
- **Package manager**: npm
- **Structure**: By type (`components/`, `services/`, `stores/`)

### Plugin (Browser Extension)
- **Framework**: Vue.js (Composition API)
- **Build**: Vite
- **Target**: Firefox & Chrome (Manifest V3)

---

## 📝 Standards de Code Python

### Naming Conventions
```python
# Variables et fonctions : snake_case
user_name = "John"
def get_user_by_id(user_id: int): ...

# Classes : PascalCase
class UserService: ...
class ProductRepository: ...

# Constantes : UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
```

### Type Hints
- **Flexible**: Use when it helps understanding
- Required on public service functions
- Optional on simple internal functions

### Docstrings (Google Style)
```python
def create_user(name: str, email: str) -> User:
    """
    Creates a new user in the database.

    Args:
        name: The user's full name.
        email: The user's email address.

    Returns:
        The newly created User object.

    Raises:
        ValidationError: If email format is invalid.
        DuplicateError: If email already exists.
    """
```

### Function Length
- **Flexible** depending on context
- Split if function becomes hard to understand
- Favor readability over artificial brevity

---

## 🧪 Tests

### Backend (Pytest)
- **Unit tests**: For services and isolated functions
- **Integration tests**: For API endpoints
- Use PostgreSQL Docker container for tests

### Frontend (Vitest)
- Unit tests for components and composables
- E2E tests with Playwright (optional)

### Conventions
```python
# Files: test_*.py
# Functions: test_*
# Classes: Test*

def test_create_user_with_valid_data():
    ...

def test_create_user_raises_error_on_duplicate_email():
    ...
```

---

## 🛠️ Gestion des Erreurs (StoFlow)

### Exception Hierarchy
```python
# Use custom exceptions inheriting from StoflowError
class ServiceError(StoflowError): ...
class ValidationError(StoflowError): ...
class MarketplaceError(StoflowError): ...
class VintedError(MarketplaceError): ...
class EbayError(MarketplaceError): ...
```

### Logging
- Use `logger` (never `print()`)
- Levels: DEBUG for dev, INFO for prod, ERROR for exceptions
- Include context (user_id, product_id, etc.)

---

## 🗄️ Base de Données (PostgreSQL)

### Multi-Tenant Architecture (Schemas)
- `public` schema: shared data (users, categories, brands, colors, etc.)
- `user_X` schema: user-specific data (products, orders, listings)
- Isolation via `SET search_path` per request

### Migrations (Alembic)
- Claude can create migration files
- Claude can help execute them
- Always verify content before `upgrade`

### 🚨 Protection des Migrations (CRITIQUE - ajouté 2026-01-13)

> **Contexte** : Claude Code supprime parfois des fichiers de migration par erreur.

**RÈGLES STRICTES :**

| Action | Règle |
|--------|-------|
| Supprimer un fichier `migrations/versions/*.py` | ⛔ **INTERDIT** sans confirmation explicite |
| Modifier un fichier de migration existant | ⚠️ **DEMANDER** avant (sauf typos/commentaires) |
| Créer une nouvelle migration | ✅ OK (utiliser `alembic revision`) |
| Exécuter `alembic downgrade` | ⚠️ **DEMANDER** avant (peut perdre des données) |

**Avant toute suppression de migration :**
```
⛔ ATTENTION: Tu vas supprimer une migration Alembic!

Fichier: migrations/versions/xxxx_nom.py

Cette action est IRRÉVERSIBLE et peut casser la base de données.

Confirmes-tu vouloir supprimer ce fichier? (oui/non)
```

**En cas de "multiple heads" Alembic :**
- Utiliser `alembic merge heads` pour fusionner (pas supprimer)
- Le skill `/finish` gère automatiquement ce cas

### 🔀 Migrations en Multi-Worktree (IMPORTANT - ajouté 2026-01-13)

> **Contexte** : Tous les worktrees partagent la même base PostgreSQL (Docker).
> Cela peut causer des problèmes de synchronisation des migrations.

#### 🤖 RÈGLE POUR CLAUDE (CRITIQUE)

**Quand Claude rencontre une erreur Alembic de type `Can't locate revision`, il DOIT automatiquement :**

1. **Identifier la révision manquante** dans le message d'erreur
2. **Chercher le fichier** dans les autres worktrees avec :
   ```bash
   grep -rl "revision.*=.*'REVISION_ID'" ~/StoFlow*/backend/migrations/versions/
   ```
3. **Copier le fichier** vers le worktree actuel
4. **Réessayer** `alembic upgrade head`

**OU utiliser le script automatique :**
```bash
cd [worktree]/backend
source .venv/bin/activate
source ../scripts/alembic-utils.sh
auto_copy_missing_migrations "."
```

**Claude ne doit PAS :**
- Demander à l'utilisateur quoi faire (sauf si la migration est introuvable)
- Proposer de supprimer des migrations
- Proposer de downgrade la DB

#### ✨ Script Auto-Copy (`scripts/alembic-utils.sh`)

**Fonctions disponibles :**

| Fonction | Description |
|----------|-------------|
| `auto_copy_missing_migrations "."` | Détecte, copie et applique les migrations manquantes (max 3 tentatives) |
| `find_migration_in_worktrees "abc123"` | Cherche une révision dans tous les worktrees, retourne le chemin |
| `list_all_migrations` | Liste toutes les migrations de tous les worktrees |

**Comment ça marche** :
1. Détecte l'erreur `Can't locate revision XXXXX`
2. Cherche le fichier de migration **par contenu** (grep `revision = 'xxx'`) dans tous les worktrees
3. Copie automatiquement le fichier trouvé dans le worktree actuel
4. Réessaye `alembic upgrade head`
5. Maximum 3 tentatives (pour gérer plusieurs migrations manquantes en chaîne)

**Utilisation manuelle** (si besoin) :
```bash
cd ~/StoFlow-[nom]/backend
source .venv/bin/activate
source ../scripts/alembic-utils.sh

# Auto-copy et upgrade
auto_copy_missing_migrations "."

# Lister toutes les migrations disponibles dans tous les worktrees
list_all_migrations

# Chercher une migration spécifique
find_migration_in_worktrees "a1b2c3d4"
```

#### Le Problème

```
Worktree A (feature/add-ebay)     Worktree B (feature/add-etsy)
         │                                  │
         │ crée migration_001               │
         │ alembic upgrade head             │
         │                                  │
         │         DB = migration_001       │
         │                                  │
         │                                  │ ❌ N'a PAS migration_001
         │                                  │ ❌ DB "ahead" du code
         │                                  │ ❌ Erreurs possibles
```

#### Symptômes Courants

| Symptôme | Cause probable |
|----------|----------------|
| `Target database is not up to date` | La DB a des migrations que le worktree n'a pas |
| `Can't locate revision` | Le worktree référence une migration qui n'existe pas dans ses fichiers |
| `Multiple heads` | Deux worktrees ont créé des migrations en parallèle |
| Erreur de colonne manquante | La DB a été migrée par un autre worktree |

#### Solutions

**1. Avant de créer une migration dans un worktree :**
```bash
# Synchroniser avec develop pour avoir toutes les migrations récentes
cd ~/StoFlow-[nom]
git fetch origin develop
git merge origin/develop  # ou /sync

# Les migrations manquantes seront auto-copiées lors du prochain /X-dev
# Ou manuellement :
cd backend
source .venv/bin/activate
source ../scripts/alembic-utils.sh
auto_copy_missing_migrations "."
```

**2. Si erreur "Target database is not up to date" :**
```bash
# Option A : Synchroniser le worktree avec develop
/sync  # Récupère les nouvelles migrations ET les auto-copie

# Option B : Auto-copy manuel depuis autres worktrees
cd backend
source .venv/bin/activate
source ../scripts/alembic-utils.sh
auto_copy_missing_migrations "."

# Option C : Vérifier l'état actuel de la DB
cd backend
alembic current          # Montre la révision actuelle de la DB
alembic heads            # Montre les heads disponibles dans le code
alembic history --verbose  # Historique complet
```

**3. Si "Multiple heads" après /finish :**
```bash
# Le skill /finish gère automatiquement, mais si manuel :
cd ~/StoFlow/backend
alembic merge -m "merge: unify migration heads" heads
alembic upgrade head
git add migrations/
git commit -m "chore: merge alembic heads"
git push
```

**4. Si la DB est "ahead" du code (migrations appliquées mais fichiers manquants) :**
```bash
# ⚠️ ATTENTION : Ces commandes peuvent perdre des données !

# Option A (recommandée) : Synchroniser le code
git fetch origin develop
git merge origin/develop

# Option B (dangereux) : Réinitialiser la DB
# ⛔ DEMANDER confirmation avant !
cd backend
alembic downgrade base  # Supprime toutes les tables !
alembic upgrade head    # Recrée avec les migrations du worktree
```

#### Bonnes Pratiques

| Pratique | Pourquoi |
|----------|----------|
| `/sync` régulièrement | Récupère les nouvelles migrations de develop |
| `alembic upgrade head` après `/sync` | Applique les nouvelles migrations |
| Une seule feature avec migrations à la fois | Évite les conflits de heads |
| Créer migrations en fin de feature | Réduit les risques de conflits |

#### Au Lancement d'un Worktree

Le script `/X-new-feature` ne fait PAS automatiquement `alembic upgrade head` car :
- La DB est peut-être déjà à jour
- Un autre worktree peut avoir des migrations non encore mergées

**Si erreur au démarrage du backend** → Exécuter :
```bash
cd ~/StoFlow-[nom]/backend
source .venv/bin/activate
alembic upgrade head
```

### Conventions
- Tables in plural: `users`, `products`, `orders`
- Foreign keys with `ondelete` defined
- Timestamps on all tables (`created_at`, `updated_at`)
- Indexes on frequently queried columns

---

## 🏗️ Architecture Backend (Clean Architecture)

```
backend/
├── api/              # FastAPI routes
├── services/         # Business logic
├── repositories/     # Data access
├── models/           # SQLAlchemy entities
├── schemas/          # Pydantic schemas
├── shared/           # Utils, config, exceptions
└── tests/
    ├── unit/
    └── integration/
```

### Principles
- **Services**: Business logic
- **Repositories**: Database access
- **Schemas**: Input/output validation
- **Models**: SQLAlchemy entities

---

## 🎨 Frontend (Vue.js/Nuxt)

### Structure
```
frontend/
├── components/       # Reusable components
├── pages/           # Pages/routes
├── stores/          # Pinia stores
├── services/        # API calls
├── composables/     # Composition functions
└── assets/          # CSS, images
```

### Style
- Composition API with `<script setup>`
- Tailwind CSS for styling
- Pinia for state management

---

## 🏛️ Architecture Overview

### Marketplace Integration Flow
```
User -> Frontend -> Backend API -> Plugin -> Marketplace (Vinted)
                              -> Direct API (eBay, Etsy)
```

### Product Status Flow
```
DRAFT -> PUBLISHED -> SOLD -> ARCHIVED
             |
             v
         ARCHIVED
```

---

## 🔌 Intégrations Marketplaces (Vinted, eBay, Etsy)

### RÈGLE CRITIQUE

> **JAMAIS tester les APIs externes avec curl ou requêtes directes.**

### Comportement Attendu
1. **Toujours** passer par les fonctions du code (services, clients)
2. **Jamais** de `curl` vers les APIs Vinted/eBay/Etsy
3. Laisser l'utilisateur faire les tests d'intégration manuels
4. En cas de doute sur un endpoint → **DEMANDER**

### Structure des Clients
```python
# Use existing clients
from services.vinted import VintedAdapter
from services.ebay import EbayBaseClient
from services.etsy import EtsyBaseClient
```

### Vinted Integration
- Done via **Browser Extension Plugin** (not direct API)
- Plugin intercepts Vinted API calls in browser
- Backend communicates with plugin via WebSocket/HTTP

### eBay Integration
- Direct API access via OAuth 2.0
- Use `EbayBaseClient` for all API calls

### Etsy Integration
- Direct API access via OAuth 2.0
- Use `EtsyBaseClient` for all API calls

---

## 📋 Development Mode

**Assume POC/prototype mode** unless explicitly stated otherwise:
- Max 3 files per commit when possible
- Prioritize working functionality over perfect code
- Refactor later when requirements are stable

---

*Last updated: 2026-01-22*
