# Intégration de l'Authentification - Stoflow Frontend

## Vue d'ensemble

L'authentification a été intégrée avec le backend FastAPI. Le frontend utilise JWT tokens stockés dans `localStorage` avec auto-refresh transparent.

## Architecture

### 1. Store Pinia (`stores/auth.ts`)

Le store gère toute la logique d'authentification :

**État:**
- `user`: Informations de l'utilisateur connecté
- `token`: Access token JWT (valide 1 heure)
- `refreshToken`: Refresh token JWT (valide 7 jours)
- `isAuthenticated`: Boolean indiquant si l'utilisateur est connecté
- `isLoading`: Indicateur de chargement
- `error`: Message d'erreur éventuel

**Actions:**
- `login(email, password)`: Connexion via POST /api/auth/login
- `register(email, password, fullName)`: Inscription via POST /api/auth/register
- `logout()`: Déconnexion (nettoie le localStorage)
- `loadFromStorage()`: Restaure la session depuis localStorage
- `refreshAccessToken()`: Rafraîchit le token via POST /api/auth/refresh

### 2. Composable `useApi` (`composables/useApi.ts`)

Gère les appels API avec authentication automatique :

**Fonctionnalités:**
- Ajout automatique du header `Authorization: Bearer {token}`
- Intercepteur pour auto-refresh en cas de 401
- Méthodes `get`, `post`, `put`, `patch`, `delete`
- Gestion des tokens dans localStorage

**Exemple d'utilisation:**
```typescript
const api = useApi()

// Appel API protégé
const products = await api.get('/api/products')

// Le token sera automatiquement ajouté au header
// Si le token expire (401), il sera automatiquement rafraîchi
```

### 3. Plugin Auth (`plugins/auth.client.ts`)

Plugin client-side qui s'exécute au démarrage de l'app :

**Fonctionnalité:**
- Charge automatiquement la session depuis localStorage
- Restaure l'état de l'utilisateur au refresh de la page

### 4. Middleware (`middleware/auth.ts`)

Protège les routes qui nécessitent une authentification :

**Comportement:**
- Redirige vers `/login` si l'utilisateur n'est pas connecté et accède à `/dashboard/*`
- Redirige vers `/dashboard` si l'utilisateur est déjà connecté et accède à `/login` ou `/register`

**Usage dans une page:**
```typescript
definePageMeta({
  middleware: 'auth'
})
```

### 5. Composant AuthModal (`components/auth/AuthModal.vue`)

Modal réutilisable pour login/register :

**Props:**
- `visible`: Boolean pour afficher/masquer le modal
- `mode`: 'login' | 'register' (mode par défaut)

**Events:**
- `update:visible`: Émis quand le modal se ferme
- `success`: Émis quand l'authentification réussit

**Fonctionnalités:**
- Formulaire de connexion ET d'inscription dans un seul composant
- Validation côté client (email, password complexity)
- Affichage des erreurs backend
- Basculement entre login/register
- Intégré avec PrimeVue Dialog

**Exemple d'utilisation:**
```vue
<template>
  <AuthModal
    v-model:visible="showAuth"
    :mode="authMode"
    @success="handleSuccess"
  />
</template>

<script setup>
const showAuth = ref(false)
const authMode = ref('login')

const handleSuccess = () => {
  console.log('User authenticated!')
}
</script>
```

## Backend API Endpoints

### POST /api/auth/register
**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Response (201 CREATED):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user_id": 1,
  "role": "user",
  "subscription_tier": "starter"
}
```

**Règles de validation (backend):**
- Email unique globalement
- Password min 12 caractères avec:
  - 1 majuscule (A-Z)
  - 1 minuscule (a-z)
  - 1 chiffre (0-9)
  - 1 caractère spécial (!@#$%^&*)
- Full_name min 1 caractère, max 255

**Erreurs possibles:**
- 400: Email déjà utilisé
- 400: Password ne respecte pas la complexité requise

### POST /api/auth/login?source=web
**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user_id": 1,
  "role": "user",
  "subscription_tier": "starter"
}
```

**Règles de sécurité (backend):**
- Rate limiting: 10 tentatives / 5 minutes par IP
- Timing attack protection: délai aléatoire 100-300ms
- Password min 8 caractères (au login, 12 au register)

**Erreurs possibles:**
- 401: Email ou mot de passe incorrect
- 401: Compte inactif
- 429: Trop de tentatives (rate limiting)

### POST /api/auth/refresh
**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**Règles:**
- Access token valide 1 heure
- Refresh token valide 7 jours
- Vérifie que l'utilisateur est toujours actif

**Erreurs possibles:**
- 401: Refresh token invalide ou expiré
- 401: Utilisateur inactif

## Flux d'authentification complet

### 1. Connexion
```
1. User remplit le formulaire login
2. Frontend: authStore.login(email, password)
3. POST /api/auth/login?source=web
4. Backend valide, génère access_token (1h) + refresh_token (7j)
5. Frontend stocke tokens + user dans localStorage
6. Redirection vers /dashboard
```

### 2. Appel API protégé
```
1. useApi().get('/api/products')
2. Ajoute header: Authorization: Bearer {access_token}
3. Si 401 (token expiré):
   a. POST /api/auth/refresh avec refresh_token
   b. Récupère nouveau access_token
   c. Retry la requête avec nouveau token
4. Si refresh échoue → logout + redirect /login
```

### 3. Refresh de page
```
1. Plugin auth.client.ts s'exécute
2. authStore.loadFromStorage()
3. Lit token + user depuis localStorage
4. Restaure l'état dans le store
5. L'utilisateur reste connecté
```

### 4. Déconnexion
```
1. authStore.logout()
2. Nettoie user, token, refreshToken du state
3. Supprime localStorage (token, refresh_token, user)
4. Redirection vers /login
```

## Sécurité

### Tokens
- **Access token:** JWT valide 1 heure, stocké dans localStorage
- **Refresh token:** JWT valide 7 jours, stocké dans localStorage
- **Transmission:** Via header `Authorization: Bearer {token}`
- **Pas de cookies httpOnly** (tokens gérés client-side)

### Vulnérabilités connues
- **XSS:** localStorage est vulnérable au XSS
  - Mitigation: PrimeVue sanitize automatiquement les inputs
  - Pas de `v-html` avec données user
  - CSP headers configurés dans le backend

- **CSRF:** Non applicable (pas de cookies de session)

### Bonnes pratiques
- Tokens courts (1h) pour limiter l'exposition
- Refresh tokens permettent de révoquer l'accès
- Rate limiting côté backend
- Validation stricte des passwords

## Configuration

### Variables d'environnement
Configuré dans `nuxt.config.ts`:

```typescript
runtimeConfig: {
  public: {
    apiUrl: process.env.NUXT_PUBLIC_API_URL || 'http://localhost:8000'
  }
}
```

**Pour changer l'URL du backend:**
```bash
# .env
NUXT_PUBLIC_API_URL=https://api.stoflow.com
```

## Pages

### `/login`
Page dédiée à la connexion avec formulaire classique.

### `/register`
Page dédiée à l'inscription avec formulaire classique.

### `/dashboard/*`
Routes protégées par le middleware `auth`.

## Fichiers créés/modifiés

### Créés:
- ✅ `components/auth/AuthModal.vue` - Composant modal auth réutilisable
- ✅ `plugins/auth.client.ts` - Plugin de chargement de session

### Modifiés:
- ✅ `stores/auth.ts` - Connexion aux vraies APIs backend (remplace les mocks)
- ✅ `middleware/auth.ts` - Protection des routes (déjà existant)
- ✅ `composables/useApi.ts` - Intercepteur avec auto-refresh (déjà existant)

### Inchangés (déjà fonctionnels):
- ✅ `pages/login.vue` - Page de connexion
- ✅ `pages/register.vue` - Page d'inscription
- ✅ `nuxt.config.ts` - Configuration API URL

## Utilisation

### Dans un composant

#### Vérifier si l'utilisateur est connecté
```vue
<template>
  <div v-if="authStore.isAuthenticated">
    <p>Bienvenue {{ authStore.user?.full_name }}</p>
    <Button @click="authStore.logout()">Déconnexion</Button>
  </div>
</template>

<script setup>
const authStore = useAuthStore()
</script>
```

#### Appeler une API protégée
```typescript
const api = useApi()

// L'auth est gérée automatiquement
const response = await api.get('/api/products')
```

#### Afficher le modal d'auth
```vue
<template>
  <Button @click="showLogin = true">Se connecter</Button>

  <AuthModal
    v-model:visible="showLogin"
    mode="login"
    @success="handleLoginSuccess"
  />
</template>

<script setup>
const showLogin = ref(false)

const handleLoginSuccess = () => {
  console.log('User logged in!')
  navigateTo('/dashboard')
}
</script>
```

## Prochaines étapes (optionnel)

### 1. Endpoint `/me` pour récupérer le profil complet
Actuellement, le backend ne retourne pas `email` ni `full_name` dans `TokenResponse`.

**Solution:** Créer un endpoint GET /api/users/me
```python
@router.get("/users/me")
def get_current_user(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "subscription_tier": current_user.subscription_tier
    }
```

Puis appeler cet endpoint après login pour récupérer le profil complet.

### 2. Révocation de refresh tokens
Stocker les refresh tokens dans une table PostgreSQL pour pouvoir les révoquer.

### 3. MFA (Multi-Factor Authentication)
Ajouter une couche de sécurité supplémentaire avec TOTP.

### 4. OAuth Social Login
Permettre login via Google, Facebook, etc.

## Troubleshooting

### "Session expirée, veuillez vous reconnecter"
- Le refresh token a expiré (7 jours)
- L'utilisateur a été désactivé dans le backend
- Solution: Se reconnecter

### "CORS error"
- Vérifier que `http://localhost:3000` est dans `CORS_ORIGINS` du backend
- Vérifier que le backend est bien lancé sur `localhost:8000`

### "429 Too Many Requests"
- Rate limiting activé (10 tentatives / 5 min)
- Attendre 5 minutes ou changer d'IP

### Le refresh de page déconnecte l'utilisateur
- Le plugin `auth.client.ts` ne s'exécute pas
- Vérifier que le fichier est bien nommé `auth.client.ts`
- Vérifier que localStorage n'est pas désactivé

## Support

Pour toute question ou bug, consulter:
- Documentation backend: `http://localhost:8000/docs`
- Code source backend: `/home/maribeiro/Stoflow/Stoflow_BackEnd`
- Guidelines du projet: `CLAUDE.md`

---

**Dernière mise à jour:** 2024-12-07
**Version:** 1.0
**Auteur:** Claude Code Assistant
