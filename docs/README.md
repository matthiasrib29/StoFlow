# StoFlow Documentation

> Documentation centralisée du projet StoFlow - Application e-commerce multi-plateformes (Vinted, eBay, Etsy)

---

## 📚 Table des Matières

- [Documentation Projet](#-documentation-projet)
- [Documentation Backend](#-documentation-backend)
- [Documentation Frontend](#-documentation-frontend)
- [Documentation Plugin](#-documentation-plugin)

---

## 🎯 Documentation Projet

Documentation globale concernant l'ensemble du projet.

### Rapports & Audits

| Document | Description |
|----------|-------------|
| [audit-2-summary.md](project/reports/audit-2-summary.md) | Rapport d'audit complet du système (2e audit) |
| [completion-summary.md](project/reports/completion-summary.md) | Résumé des tâches complétées et état du projet |
| [fixes-summary.md](project/reports/fixes-summary.md) | Liste des correctifs appliqués au projet |

### Intégration Notion

| Document | Description |
|----------|-------------|
| [sync-report.md](project/notion/sync-report.md) | Rapport de synchronisation avec Notion |
| [helper-guide.md](project/notion/helper-guide.md) | Guide d'utilisation du helper Notion API |

### Général

| Document | Description |
|----------|-------------|
| [implementation-plan.md](project/implementation-plan.md) | Plan d'implémentation restant |
| [test-readme.md](project/test-readme.md) | Guide des tests globaux |
| [product-attributes.md](project/product-attributes.md) | Documentation des attributs produits partagés |

---

## 🔧 Documentation Backend

Documentation technique de l'API FastAPI.

### Architecture & Patterns

| Document | Description |
|----------|-------------|
| [README.md](backend/architecture/README.md) | Index de l'architecture backend |
| [architecture.md](backend/architecture/architecture.md) | Architecture globale du backend (Clean Architecture) |
| [business-logic.md](backend/architecture/business-logic.md) | Règles métier et logique business |
| [order-sync-idempotency.md](backend/architecture/order-sync-idempotency.md) | Pattern d'idempotence pour la synchronisation des commandes |
| [overview.md](backend/architecture/overview.md) | Vue d'ensemble du backend |

### Migrations & Base de Données

| Document | Description |
|----------|-------------|
| [README.md](backend/migrations/README.md) | Guide des migrations Alembic |
| [job-unification.md](backend/migrations/job-unification.md) | Migration vers le système de jobs unifié (Vinted/eBay/Etsy) |
| [websocket-migration.md](backend/migrations/websocket-migration.md) | Migration vers l'architecture WebSocket pour Vinted |
| [missing-columns.md](backend/migrations/missing-columns.md) | Documentation des colonnes manquantes détectées |

### Guides Pratiques

| Document | Description |
|----------|-------------|
| [security.md](backend/guides/security.md) | Guide de sécurité et best practices |
| [troubleshooting.md](backend/guides/troubleshooting.md) | Guide de résolution des problèmes courants |
| [marketplace-handlers.md](backend/guides/marketplace-handlers.md) | Documentation des handlers Vinted/eBay/Etsy |

### Rapports de Vérification

| Document | Description |
|----------|-------------|
| [system-verification-final.md](backend/verification/system-verification-final.md) | Rapport de vérification système final |
| [verification-complete.md](backend/verification/verification-complete.md) | Rapport de vérification complète |
| [websocket-verification.md](backend/verification/websocket-verification.md) | Vérification de l'implémentation WebSocket |

### Tests

| Document | Description |
|----------|-------------|
| [README.md](backend/testing/README.md) | Guide des tests backend (Pytest) |
| [manual-tests.md](backend/testing/manual-tests.md) | Procédures de tests manuels |

---

## 🎨 Documentation Frontend

Documentation de l'application Nuxt.js.

| Document | Description |
|----------|-------------|
| [seo-guide.md](frontend/seo-guide.md) | Guide SEO pour le frontend Nuxt.js |

---

## 🔌 Documentation Plugin

Documentation de l'extension navigateur (Firefox/Chrome).

Voir [plugin/README.md](../plugin/README.md) pour la documentation du plugin.

---

## 📝 Guides de Configuration

Documentation de configuration spécifique à chaque module :

- **Racine** : [CLAUDE.md](../CLAUDE.md) - Configuration projet globale
- **Backend** : [backend/CLAUDE.md](../backend/CLAUDE.md) - Standards et best practices backend
- **Frontend** : [frontend/CLAUDE.md](../frontend/CLAUDE.md) - Standards et best practices frontend
- **Plugin** : [plugin/CLAUDE.md](../plugin/CLAUDE.md) - Standards et best practices plugin

---

## 🔗 Liens Utiles

- [README principal](../README.md) - Documentation projet globale
- [Worktree Guide](../.claude/WORKTREE-GUIDE.md) - Guide des worktrees Git
- [Claude Automations](CLAUDE_AUTOMATIONS.md) - Automatisations Claude Code

---

*Dernière mise à jour : 2026-01-15*
