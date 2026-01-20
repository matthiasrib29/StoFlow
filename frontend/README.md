# StoFlow Frontend

Interface web SaaS pour la gestion et publication de produits sur marketplaces (Vinted, eBay, Etsy).

## Stack Technique

| Technologie | Version | Rôle |
|-------------|---------|------|
| **Nuxt.js** | 4.2.1 | Framework fullstack Vue |
| **Vue.js** | 3.5.25 | Framework UI réactif |
| **TypeScript** | 5.9.3 | Typage statique |
| **Tailwind CSS** | 6.14.0 | Framework CSS utility-first |
| **PrimeVue** | 4.5.1 | Librairie composants UI |
| **Pinia** | 0.11.3 | State management |
| **VueUse** | 14.1.0 | Composables utilitaires |
| **Chart.js** | 4.5.1 | Graphiques et analytics |
| **Socket.io-client** | 4.8.3 | Communication WebSocket |
| **Vitest** | 4.0.16 | Framework de tests |
| **ESLint** | 9.39.2 | Linting |

## Fonctionnalités Implémentées

### Authentification
- ✅ Login / Register avec validation
- ✅ JWT tokens (access + refresh)
- ✅ Middleware de protection des routes
- ✅ Auto-refresh des tokens

### Dashboard
- ✅ Vue globale avec statistiques
- ✅ Actions rapides
- ✅ Activité récente
- ✅ État des intégrations marketplaces

### Produits
- ✅ Liste avec filtres et recherche
- ✅ Création / édition / suppression
- ✅ Upload et gestion des images
- ✅ Génération de texte IA (titre, description)
- ✅ Gestion des statuts (draft, published, sold, archived)
- ✅ Publication multi-marketplace

### Intégrations Marketplaces
- ✅ **Vinted** : Connexion via plugin, sync bidirectionnelle, messages
- ✅ **eBay** : OAuth2, publication, sync commandes, retours
- ✅ **Etsy** : OAuth2, publication, sync commandes

### Abonnements
- ✅ Plans et pricing
- ✅ Paiement Stripe
- ✅ Gestion des quotas

### Administration (Admin uniquement)
- ✅ Gestion utilisateurs
- ✅ Gestion des attributs (catégories, marques, couleurs...)
- ✅ Statistiques globales

## Quick Start

```bash
npm install          # Installation
npm run dev          # Développement (port 3000)
npm run build        # Build production
npm run preview      # Preview du build
```

## Structure du Projet

```
frontend/
├── pages/              # Routes auto (file-based routing)
│   ├── index.vue       # Landing page
│   ├── login.vue       # Authentification
│   ├── register.vue    # Inscription
│   └── dashboard/      # Pages dashboard
│       ├── index.vue           # Dashboard home
│       ├── products/           # Gestion produits
│       ├── platforms/          # Vinted, eBay, Etsy
│       ├── publications/       # Suivi publications
│       ├── subscription/       # Abonnements
│       ├── settings/           # Paramètres
│       └── admin/              # Admin panel
├── components/         # Composants réutilisables
├── layouts/            # Layouts (dashboard, default)
├── stores/             # Pinia stores
├── composables/        # Fonctions réutilisables
├── services/           # Services API
├── types/              # Types TypeScript
└── tests/              # Tests Vitest
```

## Configuration

### Variables d'Environnement

```env
NUXT_PUBLIC_API_BASE=http://localhost:8000
NUXT_PUBLIC_APP_NAME=StoFlow
```

## State Management (Pinia)

| Store | Description |
|-------|-------------|
| `auth` | Authentification, user, tokens |
| `products` | CRUD produits, filtres |
| `publications` | Publications, activité |
| `ebay` | État connexion eBay |
| `etsy` | État connexion Etsy |
| `vintedMessages` | Messages Vinted |
| `locale` | Internationalisation |

## Communication Backend

- **REST API** : FastAPI sur `/api/*`
- **WebSocket** : Socket.IO pour temps réel (Vinted plugin)
- **Auth** : Bearer token JWT

## Scripts

```bash
npm run dev          # Dev avec hot-reload
npm run build        # Build production
npm run lint         # Linting ESLint
npm run lint:fix     # Fix auto ESLint
npm run test         # Tests Vitest
npm run test:run     # Tests en CI
npm run test:coverage # Couverture de code
```

## Dépannage

**Nuxt ne démarre pas**
```bash
rm -rf .nuxt node_modules/.vite && npm install && npm run dev
```

**Erreur CORS** : Vérifier `NUXT_PUBLIC_API_BASE` dans `.env`

**WebSocket déconnecté** : Vérifier que le backend est lancé

---

**Dernière mise à jour :** 2026-01-20
**Node version recommandée :** 20.x
