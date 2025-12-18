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

## License

Private - All rights reserved.
