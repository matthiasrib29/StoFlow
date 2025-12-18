# Stoflow Frontend

Interface web SaaS pour la gestion et publication de produits sur marketplaces (Vinted, eBay, Etsy, Facebook Marketplace).

## Stack Technique

- **Framework :** Nuxt 4.2.1 (Vue 3.5.13)
- **UI Library :** PrimeVue 4.5.1
- **Styling :** Tailwind CSS + modern-dashboard.css
- **State Management :** Pinia 2.3.0
- **Animations :** @formkit/auto-animate
- **Icons :** PrimeIcons

## Couleurs

- **Primaire :** `#facc15` (Jaune) - primary-400
- **Secondaire :** `#1a1a1a` (Noir) - secondary-900
- **Accent :** `#eab308` (Jaune foncé) - primary-500

## Quick Start

```bash
# Installation
npm install

# Développement (port 3000)
npm run dev

# Build production
npm run build

# Preview build
npm run preview
```

## Structure du Projet

```
Stoflow_FrontEnd/
├── pages/              # Routes auto (file-based routing)
│   ├── index.vue       # Page d'accueil
│   ├── login.vue       # Authentification
│   └── dashboard/      # Pages dashboard
├── components/         # Composants réutilisables
├── layouts/            # Layouts (dashboard, default)
├── stores/             # Pinia stores (state management)
├── composables/        # Fonctions réutilisables
├── plugins/            # Plugins Nuxt
├── assets/             # CSS, images
│   └── css/
│       └── modern-dashboard.css
├── public/             # Fichiers statiques
└── nuxt.config.ts      # Configuration Nuxt
```

## Configuration

### Variables d'Environnement

Créer un fichier `.env` :

```env
# API Backend
NUXT_PUBLIC_API_BASE=http://localhost:8000

# Optionnel
NUXT_PUBLIC_APP_NAME=Stoflow
```

### API Communication

Toutes les requêtes API passent par le backend FastAPI :

```typescript
// Dans un composable ou store
const config = useRuntimeConfig()
const { data } = await useFetch('/api/products', {
  baseURL: config.public.apiBase,
  headers: {
    Authorization: `Bearer ${authStore.token}`
  }
})
```

## State Management (Pinia)

**Stores disponibles :**

- `authStore` : Authentification, user, tenant
- `productsStore` : Gestion produits (CRUD)
- `publicationsStore` : Publications, activité récente
- `platformsStore` : Connexions plateformes

Exemple d'utilisation :

```vue
<script setup>
const authStore = useAuthStore()
const productsStore = useProductsStore()

onMounted(() => {
  productsStore.fetchProducts()
})
</script>
```

## Routing

**File-based routing** (auto-généré par Nuxt) :

| Fichier | Route |
|---------|-------|
| `pages/index.vue` | `/` |
| `pages/login.vue` | `/login` |
| `pages/dashboard/index.vue` | `/dashboard` |
| `pages/dashboard/products/index.vue` | `/dashboard/products` |
| `pages/dashboard/products/[id].vue` | `/dashboard/products/123` |

**Middleware :** `auth.global.ts` protège les routes `/dashboard/*`

## Styling

**Guide complet :** Voir [STYLING_GUIDE.md](./STYLING_GUIDE.md)

**Classes réutilisables :**
- `.rounded-2xl` : Border-radius standard (16px)
- `.gradient-vinted`, `.gradient-ebay`, etc. : Gradients plateformes
- `.stat-card-gradient` : Stat cards avec accent couleur

**Spacing standard :**
```vue
<div class="p-8">               <!-- Page wrapper -->
  <div class="mb-8">            <!-- Section header -->
    <h1 class="text-3xl font-bold text-secondary-900 mb-1">Titre</h1>
    <p class="text-gray-600">Sous-titre</p>
  </div>
</div>
```

## Composants Principaux

### Dashboard
- `QuickActions.vue` : Actions rapides (créer produit, connecter plateforme)
- `RecentActivity.vue` : Activité récente
- `IntegrationsStatus.vue` : État des intégrations

### Layouts
- `dashboard.vue` : Layout principal avec sidebar
- `default.vue` : Layout simple (login, etc.)

## Documentation

- **Architecture Frontend :** [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Logique Métier :** [BUSINESS.md](./BUSINESS.md)
- **Styling :** [STYLING_GUIDE.md](./STYLING_GUIDE.md)
- **Guidelines Claude :** [CLAUDE.md](./CLAUDE.md)

## Scripts Disponibles

```bash
npm run dev          # Développement avec hot-reload
npm run build        # Build production
npm run generate     # Génération statique
npm run preview      # Preview du build
npm run postinstall  # Préparation Nuxt (auto après install)
```

## Authentification

**Flow :**
1. User login via `/login`
2. Backend retourne JWT access + refresh tokens
3. Access token stocké dans `authStore` (memory)
4. Refresh token dans HttpOnly cookie
5. Middleware `auth.global.ts` vérifie token sur routes protégées

**Auto-refresh :** À implémenter (refresh automatique avant expiration)

## Intégration Backend

**Base URL :** Configurée dans `nuxt.config.ts`

```typescript
export default defineNuxtConfig({
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000'
    }
  }
})
```

**Exemple de requête :**

```typescript
// GET /api/products
const { data: products } = await useFetch('/api/products', {
  baseURL: config.public.apiBase
})

// POST /api/products
await $fetch('/api/products', {
  method: 'POST',
  baseURL: config.public.apiBase,
  body: { name: 'Mon produit', price: 29.99 }
})
```

## Bonnes Pratiques

1. **Toujours utiliser les composables** pour les appels API
2. **Pinia stores** pour l'état partagé
3. **TypeScript** pour le typage (fichiers `.ts` ou `<script setup lang="ts">`)
4. **Lazy loading** des composants lourds : `defineAsyncComponent`
5. **Auto-animate** sur les listes dynamiques : directive `v-auto-animate`

## Dépannage

**Problème :** Nuxt ne démarre pas
```bash
rm -rf .nuxt node_modules/.vite
npm install
npm run dev
```

**Problème :** Erreur CORS
- Vérifier que le backend autorise l'origine frontend
- Vérifier `NUXT_PUBLIC_API_BASE` dans `.env`

**Problème :** Token expiré
- Implémenter refresh automatique dans `authStore`
- Vérifier durée de vie des tokens côté backend

---

**Dernière mise à jour :** 2024-12-07
**Version Nuxt :** 4.2.1
**Node version recommandée :** 18.x ou 20.x
