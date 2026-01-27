# Rapport d'Audit - Sécurité

**Projet**: StoFlow
**Date d'analyse**: 2026-01-27
**Scope**: Backend (FastAPI), Frontend (Nuxt.js), Plugin (Browser Extension)

---

## Résumé Exécutif

**Verdict Global**: 1 vulnérabilité CRITIQUE, plusieurs HAUTES, et des problèmes MOYENS/BAS. Des améliorations importantes sont nécessaires avant un déploiement production étendu.

---

## Vulnérabilités Critiques

### CRITICAL-01: Secrets Hardcodés dans .env

**Fichier**: `backend/.env`

Le fichier `.env` contient des secrets en clair (Cloudflare R2, eBay API, Stripe, Gemini). Si ce fichier est commité dans l'historique Git, tous ces secrets sont compromis.

**Risque**: Accès non autorisé aux services cloud, facturation frauduleuse, vol de données
**Remédiation IMMÉDIATE**:
1. Révoquer TOUS les secrets exposés
2. Utiliser un gestionnaire de secrets en production (Railway env vars, AWS Secrets Manager)
3. Vérifier l'historique Git avec `git log --all --full-history -- backend/.env`

---

## Vulnérabilités Hautes

### HIGH-01: JWT Secret Faible (HS256 fallback)

**Fichier**: `backend/.env` (ligne 53)
**Problème**: `JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production-min-32-chars`
**Remédiation**: Générer un secret de 64+ caractères avec `secrets.token_urlsafe(64)`
**Note positive**: Migration vers RS256 (asymétrique) en cours

### HIGH-02: SQL Injection potentielle via SET search_path

**Fichiers**: `backend/worker/marketplace_worker.py:192`, `backend/temporal/activities/vinted_activities.py:55`

```python
# VULNÉRABLE - Interpolation directe du nom de schéma
db.execute(text(f"SET search_path TO {schema_name}, public"))
```

`validate_schema_name()` existe mais n'est pas systématiquement appelée.
**Remédiation**: Utiliser `schema_translate_map` partout, ou valider systématiquement avant SET

### HIGH-03: Absence d'ENCRYPTION_KEY configurée

Les tokens OAuth2 (eBay, Etsy) sont potentiellement stockés en clair dans la base.
**Remédiation**: Générer une clé Fernet, l'ajouter en `.env`, migrer les tokens existants

### HIGH-04: v-html XSS (frontend)

**Fichier**: `frontend/pages/docs/[category]/[slug].vue:105`
Content Markdown rendu avec `v-html` après sanitization. Si la sanitization est insuffisante, XSS possible.
**Remédiation**: Auditer la configuration DOMPurify, renforcer CSP

### HIGH-05: CSRF Token Bypassable

**Fichier**: `backend/middleware/csrf.py:93-97`
Le middleware CSRF skip si pas de cookie CSRF → endpoints avec `Authorization: Bearer` non protégés.
**Remédiation**: Exiger CSRF pour TOUS les endpoints authentifiés

---

## Vulnérabilités Moyennes

### MEDIUM-01: Dev Auth Bypass potentiellement actif en production

`DEV_AUTH_BYPASS=true` et `DEV_DEFAULT_USER_ID=2` dans `.env`
**Remédiation**: Validation stricte au démarrage avec refus de démarrer si bypass actif en production

### MEDIUM-02: Rate Limiting désactivable

`DISABLE_RATE_LIMIT=1` existe comme option (ignorée en prod, mais risque de config error)
**Remédiation**: Supprimer complètement cette fonctionnalité

### MEDIUM-03: Timing Attack sur authentification

Le délai aléatoire 100-300ms ne masque pas les différences entre "user not found" et "wrong password" (bcrypt lent).
**Remédiation**: Toujours exécuter le hash bcrypt même si l'utilisateur n'existe pas

### MEDIUM-04: Webhook eBay sans validation IP

Seule la signature HMAC est vérifiée, pas l'IP source.
**Remédiation**: Ajouter whitelist d'IPs eBay

### MEDIUM-05: Validation uploads d'images incomplète

Pas de validation de type MIME basée sur le contenu, taille, dimensions.
**Remédiation**: Utiliser `python-magic` pour MIME réel, valider dimensions avec Pillow

---

## Vulnérabilités Basses

- **LOW-01**: Password reset non implémenté (routes exemptées de CSRF mais pas de logique)
- **LOW-02**: Logs contenant potentiellement des données sensibles (à auditer)
- **LOW-03**: Plugin - permission `tabs` trop large (accès à toutes les URLs)
- **LOW-04**: Absence de `security.txt`

---

## Points Positifs

1. **JWT RS256 Migration** en cours
2. **CSRF Protection** (double-submit cookie pattern)
3. **Rate Limiting** sur endpoints auth
4. **Multi-Tenant Schema Isolation** sécurisée
5. **Password Hashing** bcrypt 12 rounds
6. **Security Headers** (HSTS, X-Frame-Options, CSP)
7. **HTTPOnly Cookies** pour tokens
8. **Account Lockout** après 5 tentatives
9. **Email Verification** tokens hashés SHA-256
10. **ORM systématique** (pas de raw SQL non paramétré)

---

## Plan d'Action

### Immédiat (Avant Production)
1. Révoquer secrets exposés dans .env
2. Configurer ENCRYPTION_KEY
3. Renforcer JWT_SECRET_KEY
4. Valider systématiquement schema names
5. Désactiver DEV_AUTH_BYPASS en production

### Court Terme (1-2 semaines)
6. Validation complète des uploads images
7. IP whitelisting webhooks eBay
8. Compléter migration JWT → RS256
9. Renforcer sanitization HTML
10. Implémenter password reset sécurisé

### Moyen Terme (1-2 mois)
11. Audit complet des logs (PII, secrets)
12. Dependency scanning (Dependabot, Snyk)
13. Tests de sécurité automatisés (SAST, DAST)
14. CSP report-only en production
15. Monitoring tentatives d'intrusion

---

**Rapport généré le**: 2026-01-27
**Auditeur**: Claude Code (Security Analyzer)
