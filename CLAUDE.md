# CLAUDE.md - StoFlow Monorepo

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**StoFlow** is an e-commerce management application for multi-channel selling:
- **Backend**: FastAPI REST API with PostgreSQL multi-tenant architecture
- **Frontend**: Nuxt.js web application (Vue 3 + Composition API)
- **Plugin**: Browser extension (Firefox/Chrome) for marketplace integrations

## Repository Structure

```
StoFlow/
├── backend/         # FastAPI API server
├── frontend/        # Nuxt.js web application
├── plugin/          # Browser extension (Vinted integration)
├── CLAUDE.md        # This file (global guidelines)
├── README.md        # Project documentation
└── .gitignore       # Git ignore rules
```

## Module-Specific Guidelines

Each module has its own CLAUDE.md with detailed instructions:
- [backend/CLAUDE.md](backend/CLAUDE.md) - Backend API development
- [frontend/CLAUDE.md](frontend/CLAUDE.md) - Frontend development
- [plugin/CLAUDE.md](plugin/CLAUDE.md) - Browser extension development

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

## Development Rules

### Main Rule
**ALWAYS ASK QUESTIONS before implementing business logic.**

When in doubt -> STOP -> ASK the user.

### Commit Guidelines
- **Language**: English for all commit messages
- **Format**: Conventional Commits (`feat:`, `fix:`, `docs:`, etc.)
- **Scope**: Max 3 files per commit when possible
- **Mode**: Assume POC/prototype unless explicitly stated otherwise

### Code Quality
- Python: PEP 8, type hints, Google-style docstrings
- TypeScript/Vue: Composition API, TypeScript strict mode
- Max 500 lines per file (propose refactoring if exceeded)
- Never commit secrets or credentials

### Testing
- Backend: pytest with PostgreSQL Docker container
- Frontend: Vitest for unit tests
- Always test before committing

## Architecture Overview

### Multi-Tenant (PostgreSQL Schemas)
- `public` schema: shared data (users, categories, brands)
- `user_X` schema: user-specific data (products, orders)
- Isolation via `SET search_path` per request

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

## Security Rules (STRICT)

- Never hardcode secrets in code
- Never log credentials or sensitive data
- Always validate user input (Pydantic/Zod)
- Use parameterized queries (SQLAlchemy)
- JWT for authentication

## File Operations

- Always ask before modifying, creating, or deleting files
- Prefer editing existing files over creating new ones
- No auto-generated documentation files

---

*Last updated: 2024-12-18*
