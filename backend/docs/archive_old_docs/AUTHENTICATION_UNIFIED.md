# Unification des Endpoints d'Authentification

**Date:** 2025-12-07
**Auteur:** Claude
**Validé par:** @maribeiro

## 🎯 Changements

### ❌ Ancien Système (Supprimé)

Deux endpoints distincts pour l'authentification :

- `POST /api/auth/login` - Pour l'application web
- `POST /api/plugin/auth` - Pour le plugin navigateur

**Problèmes :**
- Duplication de code
- Gestion séparée des endpoints
- Format de réponse différent (PluginAuthResponse vs TokenResponse)

### ✅ Nouveau Système (Unifié)

Un seul endpoint avec paramètre optionnel `source` :

```http
POST /api/auth/login?source=web      # Par défaut (application web)
POST /api/auth/login?source=plugin   # Pour le plugin
POST /api/auth/login?source=mobile   # Pour une future app mobile
```

**Avantages :**
- ✅ Code unique à maintenir
- ✅ Tracking des sources de connexion
- ✅ Format de réponse unifié (TokenResponse avec refresh_token)
- ✅ Évolutif (mobile, desktop, etc.)

## 📋 Migration Guide

### Pour le Plugin Navigateur

**Avant :**
```javascript
// Ancien endpoint
const response = await fetch('http://localhost:8000/api/plugin/auth', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});

// Format de réponse ancien
{
  "success": true,
  "access_token": "eyJ...",
  "user": { "id": 1, "email": "...", "tenant_id": 1 },
  "error": null
}
```

**Après :**
```javascript
// Nouveau endpoint unifié
const response = await fetch('http://localhost:8000/api/auth/login?source=plugin', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});

// Format de réponse standard
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user_id": 1,
  "tenant_id": 1,
  "role": "admin"
}
```

### Pour l'Application Web

**Aucun changement requis !** Le endpoint `/api/auth/login` fonctionne exactement comme avant (source par défaut = "web").

## 🔍 Tracking des Connexions

Le paramètre `source` permet de tracker d'où viennent les connexions :

**Logs générés :**
```
[AUTH] Login attempt: email=user@example.com, password=**********, source=plugin
[AUTH] User authenticated: user_id=1, tenant_id=1, source=plugin
```

Ces logs permettent :
- 📊 Analytics des sources de connexion (web vs plugin vs mobile)
- 🔒 Détection d'activités suspectes
- 📈 Monitoring de l'utilisation par plateforme

## 🧪 Tests

Nouveaux tests ajoutés dans `tests/test_auth.py` :

```python
def test_login_with_source_parameter(self, client: TestClient, test_user):
    """Test de login avec paramètre source (plugin, mobile, etc)."""
    response = client.post(
        "/api/auth/login?source=plugin",
        json={"email": user.email, "password": password}
    )
    assert response.status_code == 200

def test_login_with_mobile_source(self, client: TestClient, test_user):
    """Test de login avec source=mobile."""
    response = client.post(
        "/api/auth/login?source=mobile",
        json={"email": user.email, "password": password}
    )
    assert response.status_code == 200
```

## 📝 Modifications Techniques

### 1. `/api/auth/login` (auth.py)

**Signature mise à jour :**
```python
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
    source: str = "web",  # ← Nouveau paramètre
) -> TokenResponse:
```

**Business Rules (Updated: 2025-12-07):**
- Supporte le paramètre optionnel 'source' pour tracking (web, plugin, mobile)
- Logs enrichis avec la source de connexion

### 2. `AuthService.authenticate_user()` (services/auth_service.py)

**Signature mise à jour :**
```python
@staticmethod
def authenticate_user(
    db: Session,
    email: str,
    password: str,
    source: str = "web"  # ← Nouveau paramètre
) -> Optional[User]:
```

**Log ajouté :**
```python
print(f"[AUTH] User authenticated: user_id={user.id}, tenant_id={user.tenant_id}, source={source}")
```

### 3. `/api/plugin/auth` (plugin.py)

**Supprimé complètement :**
- ❌ Endpoint `/api/plugin/auth` supprimé
- ❌ Schema `PluginAuthRequest` supprimé
- ❌ Schema `PluginAuthResponse` supprimé

**Note ajoutée :**
```python
# Note: Plugin authentication now uses the unified /api/auth/login endpoint with source=plugin
```

### 4. Tests (tests/test_auth.py)

**Ajout de 2 nouveaux tests :**
- `test_login_with_source_parameter()` - Test avec source=plugin
- `test_login_with_mobile_source()` - Test avec source=mobile

**Tests existants :** Aucune modification nécessaire (backward compatible)

## 🚀 Valeurs Possibles pour `source`

| Source | Usage | Description |
|--------|-------|-------------|
| `web` | Application web (défaut) | Dashboard principal Stoflow |
| `plugin` | Extension navigateur | Plugin Chrome/Firefox pour Vinted |
| `mobile` | App mobile (future) | Future application mobile |
| `desktop` | App desktop (future) | Future application Electron |

## ⚠️ Breaking Changes

### Pour le Plugin

Le plugin **doit** être mis à jour pour utiliser le nouvel endpoint :

**Migration requise :**
1. Changer l'URL : `/api/plugin/auth` → `/api/auth/login?source=plugin`
2. Adapter le format de réponse :
   - `success` → vérifier `response.status === 200`
   - `user.id` → `user_id`
   - `user.tenant_id` → `tenant_id`
   - Nouveau : `refresh_token` disponible

## 📊 Impact

### Fichiers Modifiés
- `api/auth.py` - Ajout paramètre `source`
- `services/auth_service.py` - Ajout paramètre `source` + log
- `api/plugin.py` - Suppression endpoint `/auth`
- `tests/test_auth.py` - Ajout 2 tests

### Fichiers Non Modifiés
- `schemas/auth_schemas.py` - Aucune modification (source est un query param)
- `models/` - Aucune modification
- `api/dependencies/` - Aucune modification

## 🔐 Sécurité

**Aucun impact sur la sécurité :**
- ✅ Même logique d'authentification
- ✅ Mêmes validations (email, password, tenant actif, user actif)
- ✅ Même protection timing attack (100-300ms random delay)
- ✅ Même hashage bcrypt
- ✅ Mêmes tokens JWT (1h access, 7 jours refresh)

**Amélioration :**
- ✅ Meilleur tracking des sources de connexion dans les logs

## 📚 Références

- Issue/Ticket : N/A (refactoring technique)
- Validé avec : @maribeiro (2025-12-07)
- Tests : Tous les tests passent ✅

---

**Version :** 1.0
**Status :** ✅ Implémenté et testé
