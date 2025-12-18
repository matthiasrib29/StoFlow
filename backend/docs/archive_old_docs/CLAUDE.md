# Stoflow Backend - Claude Code Guidelines

## 🎯 Règle Principale

**TOUJOURS POSER DES QUESTIONS avant d'implémenter de la logique métier.**

En cas de doute → STOP → DEMANDER à l'utilisateur.

## 📋 Quand Poser des Questions

### Obligatoire de demander pour :
- **Calculs métier** : prix, commissions, arrondis, frais
- **Règles de validation** : limites, contraintes, formats
- **Gestion d'erreurs** : comportement en cas d'échec, retry, fallback
- **Intégrations externes** : Vinted, eBay, Etsy (format données, mapping)
- **Limites business** : quotas, rate limiting, abonnements
- **Workflows** : états, transitions, conditions

### Pas besoin de demander pour :
- CRUD standard
- Code technique pur (utils, logging)
- Patterns établis (Repository, Service)

## 💻 Code Style

- **Python** : PEP 8, type hints obligatoires
- **Docstrings** : Format Google pour fonctions publiques
- **Naming** : snake_case pour fonctions/variables, PascalCase pour classes
- **Imports** : Groupés (stdlib, third-party, local) avec ligne vide entre

## 🏗️ Architecture

### Structure Multi-Tenant
- Schema PostgreSQL par client (`client_{tenant_id}`)
- Isolation stricte des données via `search_path`
- Tables communes dans schema `public`

### Patterns
- **Services** : Logique métier
- **Repositories** : Accès données
- **Dependencies** : FastAPI Depends pour injection
- **Middleware** : Multi-tenant, auth, CORS

## ✅ Standards de Code

### Sécurité
- Passwords hashés avec bcrypt
- JWT pour authentification
- Validation Pydantic sur toutes les entrées
- Pas de données sensibles dans logs

### Base de Données
- Migrations Alembic obligatoires
- Foreign keys avec `ondelete` défini
- Index sur colonnes fréquemment requêtées
- Timestamps (`created_at`, `updated_at`) sur toutes les tables

### API
- Routes préfixées `/api`
- Réponses JSON avec Pydantic models
- Status codes HTTP appropriés
- Documentation Swagger automatique

### Tests
- Coverage minimum 80%
- Tests unitaires pour services
- Tests intégration pour API
- Fixtures pytest pour données test

## 📚 Documentation

- Documenter décisions métier dans le code
- Référencer date et auteur pour règles business
- Mettre à jour README.md si nouveaux endpoints
- Exemples d'utilisation dans docstrings
