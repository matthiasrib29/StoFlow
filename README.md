# StoFlow

E-commerce management application for multi-channel selling.

## Overview

StoFlow helps sellers manage their products across multiple marketplaces (Vinted, eBay, Etsy) from a single interface.

## Architecture

| Module | Technology | Description |
|--------|------------|-------------|
| **Backend** | FastAPI + PostgreSQL | REST API with multi-tenant architecture |
| **Frontend** | Nuxt.js (Vue 3) | Web application with Composition API |
| **Plugin** | Browser Extension | Vinted integration via browser |

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
docker-compose up -d          # PostgreSQL + Redis
alembic upgrade head          # Apply migrations
uvicorn main:app --reload     # http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                   # http://localhost:3000
```

### Plugin
```bash
cd plugin
npm install
npm run dev                   # Build with watch
# Load dist/ folder in browser
```

## Project Structure

```
StoFlow/
├── backend/           # FastAPI API
│   ├── api/           # Route handlers
│   ├── services/      # Business logic
│   ├── models/        # SQLAlchemy models
│   └── schemas/       # Pydantic schemas
├── frontend/          # Nuxt.js app
│   ├── components/    # Vue components
│   ├── pages/         # Application pages
│   └── stores/        # Pinia stores
├── plugin/            # Browser extension
│   ├── src/           # Source code
│   └── dist/          # Build output
└── CLAUDE.md          # AI assistant guidelines
```

## Development

See individual module READMEs for detailed development instructions:
- [Backend Development](backend/README.md)
- [Frontend Development](frontend/README.md)
- [Plugin Development](plugin/README.md)

## 📋 Project Management

### Structure du projet

Le projet StoFlow est organisé avec une structure GitHub complète pour un suivi optimal des tâches :

**Labels** : Organisés par catégorie technique, priorité et type
- **Catégories** : `frontend`, `backend`, `extension`, `infrastructure`, `ebay`, `vinted`, `stripe`, `api`, `tests`, `docs`, `security`, `ui-ux`, `database`
- **Priorités** : `priority: high`, `priority: medium`, `priority: low`
- **Types** : `feature`, `bug`, `enhancement`, `documentation`

**Milestones** : Roadmap en 3 phases avec dates claires
- 🚀 **MVP 1 - Lancement Beta** (31 mars 2025) : Fonctionnalités essentielles (auth, dashboard, eBay publish)
- 📈 **MVP 2 - Croissance** (30 juin 2025) : Ajout Vinted, Stripe, optimisations, analytics
- 🌟 **MVP 3 - Scale** (30 sept 2025) : Features avancées, IA, multi-marketplaces, performance

**Project Board** : Vue Kanban pour le suivi des tâches
- [Accéder au board](https://github.com/matthiasrib29/StoFlow/projects)

### Workflow de développement

```
📥 Backlog → 📋 À faire → 🔄 En cours → 🧪 En test → ✅ Terminé
```

1. **Nouvelles issues** : Créées dans le Backlog avec les labels appropriés
2. **Sprint planning** : Issues priorisées et déplacées dans "À faire"
3. **Développement** : Maximum 5 tâches simultanées dans "En cours"
4. **Testing** : Code review et tests dans "En test"
5. **Merge** : PR mergée → tâche déplacée dans "Terminé"

### Templates d'issues

Trois templates sont disponibles pour créer de nouvelles issues :
- 🎯 **Feature Request** : Proposer une nouvelle fonctionnalité
- 🐛 **Bug Report** : Signaler un bug
- ✅ **Task** : Tâche de développement

## Deployment

### Infrastructure

| Service | Plateforme | Description |
|---------|------------|-------------|
| **Frontend** | Vercel | Application Nuxt.js |
| **Backend** | Railway | API FastAPI |
| **Database** | Railway | PostgreSQL (même projet) |
| **Images** | Cloudflare R2 | Stockage des images produits |

### Stockage des images

Les images produits sont stockées sur **Cloudflare R2** (compatible S3) :

- **URL publique** : `https://cdn.stoflow.io/{user_id}/products/{product_id}/{image}.jpg`
- **Optimisation automatique** : redimensionnement max 2000px, compression JPEG 90%
- **Egress gratuit** : pas de frais de bande passante

```
Upload → Validation → Optimisation → R2 → cdn.stoflow.io
```

### Branches

| Branche | Environnement | Déploiement |
|---------|---------------|-------------|
| `develop` | Développement | Local uniquement |
| `prod` | Production | Auto (Railway + Vercel) |

### Workflow

```
feature/xxx → develop → prod
                         ↓
              Vercel (front) + Railway (back)
```

### Déployer en production

```bash
# Via commande Claude
/deploy

# Ou manuellement
git checkout prod
git merge develop
git push origin prod
```

Railway et Vercel détectent automatiquement le push sur `prod` et déploient.

## License

Private - All rights reserved.
