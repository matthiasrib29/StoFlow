# Claude Code Guidelines - Stoflow Frontend

> Pour les règles globales (commits, sécurité, multi-tenant, etc.), voir [CLAUDE.md](../CLAUDE.md)

---

# 📦 Stack Technologique Frontend

| Technologie | Version | Rôle |
|-------------|---------|------|
| Nuxt.js | 4.2.1 | Framework fullstack Vue |
| Vue.js | 3.5.25 | Framework UI réactif |
| TypeScript | 5.9.3 | Typage statique |
| Tailwind CSS | 6.14.0 | Framework CSS utility-first |
| PrimeVue | 4.5.1 | Librairie composants UI |
| Pinia | 0.11.3 | State management |
| VueUse | 14.1.0 | Composables utilitaires |
| Vitest | 4.0.16 | Framework de tests |
| ESLint | 9.39.2 | Linting |
| Chart.js + vue-chartjs | 4.5.1 / 5.3.3 | Graphiques |

---

# 🟢 Nuxt 4 (v4.2.1)

## ✅ Bonnes pratiques

- **Nouvelle structure `app/`** : Placer le code dans `app/` pour une meilleure organisation et performance IDE
- **Auto-imports** : Utiliser les auto-imports natifs pour composants, composables et utils
- **Data Fetching** : Utiliser `useAsyncData` et `useFetch` avec leurs options de cache intégrées
- **TypeScript** : Activer le support TypeScript natif pour un typage fort
- **SSR/SSG** : Configurer le mode de rendu approprié selon les besoins (universal, spa, static)
- **Modules officiels** : Préférer `@pinia/nuxt`, `@vueuse/nuxt`, `@nuxtjs/tailwindcss`
- **Runtime Config** : Utiliser `runtimeConfig` pour les variables d'environnement

## ❌ Mauvaises pratiques

- **Imports manuels de composants** : Ne pas importer manuellement les composants locaux (Nuxt auto-importe)
- **Logique dans les pages** : Éviter la logique métier complexe dans les fichiers `pages/` - extraire dans des composables
- **Ignorer le cache** : Ne pas ignorer les options de cache de `useFetch`/`useAsyncData`
- **Mixing SSR/Client** : Ne pas accéder à `window`/`document` sans vérification côté client
- **Configuration legacy** : Ne pas utiliser les anciennes configurations Nuxt 3 dépréciées

## ⚠️ Pièges courants

- **Hydration mismatch** : Contenu différent entre serveur et client (vérifier avec `<ClientOnly>`)
- **useAsyncData dans onMounted** : Doit être appelé dans le setup, pas dans les lifecycle hooks
- **Refresh sans key** : `useFetch` sans `key` unique peut causer des conflits de cache
- **Conflit fichier/dossier routes** : Si `pages/foo.vue` ET `pages/foo/[id].vue` existent, utiliser `pages/foo/index.vue` au lieu de `pages/foo.vue` pour éviter les conflits de routing

### 🔀 Structure de Routes avec Paramètres Dynamiques

**❌ Mauvaise structure (conflit possible) :**
```
pages/
├── orders.vue           # /orders
└── orders/
    └── [id].vue         # /orders/:id  ← Peut ne pas fonctionner !
```

**✅ Bonne structure :**
```
pages/
└── orders/
    ├── index.vue        # /orders
    └── [id].vue         # /orders/:id  ← Fonctionne correctement
```

## 🔗 Sources
- [Nuxt 4 Performance Best Practices](https://nuxt.com/docs/4.x/guide/best-practices/performance)
- [Nuxt 4 Introduction](https://nuxt.com/docs)
- [Migration Guide Nuxt 4](https://epicmax.co/post/nuxt4-migration)

## 📚 Contexte projet
- Configuration dans `nuxt.config.ts`
- Modules : `@pinia/nuxt`, `@nuxtjs/tailwindcss`, `@vueuse/nuxt`, `@nuxt/eslint`
- Runtime config pour API URLs (`apiUrl`, `apiBaseUrl`)
- CSP headers configurés pour la production
- Port dev : 3000

---

# 🟢 Vue 3 Composition API (v3.5.25)

## ✅ Bonnes pratiques

- **`<script setup>`** : Toujours utiliser `<script setup>` pour les composants (moins de boilerplate)
- **Reactivity primitives** :
  - `ref()` pour primitives (string, number, boolean)
  - `reactive()` pour objets/arrays
  - `computed()` pour valeurs dérivées
- **Props/Emits typés** : Utiliser `defineProps<T>()` et `defineEmits<T>()` avec TypeScript
- **Composables** : Extraire la logique réutilisable dans des composables (`use*`)
- **toRefs()** : Utiliser `toRefs()` pour destructurer un objet reactif sans perdre la réactivité
- **watchEffect vs watch** : `watchEffect` pour effets automatiques, `watch` pour contrôle précis

## ❌ Mauvaises pratiques

- **Destructuring reactive** : `const { x } = reactive({x: 1})` perd la réactivité → utiliser `toRefs()`
- **reactive pour primitives** : `reactive('string')` ne fonctionne pas → utiliser `ref()`
- **Oublier `.value`** : En JS, `ref` nécessite `.value` (pas dans les templates)
- **Options API dans script setup** : Ne pas mélanger `name`, `components` etc. dans `<script setup>`
- **Mutations directes de props** : Ne jamais modifier les props directement → émettre un event
- **Logique dans templates** : Éviter les expressions complexes dans les templates → utiliser `computed`

## ⚠️ Pièges courants

- **Ref unwrapping** : Les refs sont auto-unwrapped dans les templates mais pas en JS
- **Async setup** : `<script setup>` avec `await` au top-level nécessite `<Suspense>`
- **Shallow vs Deep reactivity** : `shallowRef`/`shallowReactive` n'observe pas les propriétés imbriquées
- **Lost reactivity** : Réassigner un objet reactive (`state = newState`) perd la réactivité

## 🔗 Sources
- [Vue 3 Composition API FAQ](https://vuejs.org/guide/extras/composition-api-faq.html)
- [Vue 3 Best Practices 2025](https://medium.com/@ignatovich.dm/vue-3-best-practices-cb0a6e281ef4)
- [Vue Composition API Tips](https://learnvue.co/articles/vue-composition-api-tips)

## 📚 Contexte projet
- Tous les composants utilisent `<script setup lang="ts">`
- Composables dans `composables/`
- Organisation par domaine : `components/vinted/`, `components/ebay/`, etc.

---

# 🟢 TypeScript 5 (v5.9.3)

## ✅ Bonnes pratiques

- **Strict mode** : Toujours `"strict": true` dans tsconfig.json
- **`unknown` vs `any`** : Préférer `unknown` à `any` pour un typage plus sûr
- **Types explicites** : Typer les paramètres de fonctions et retours publics
- **Interfaces vs Types** : `interface` pour les objets extensibles, `type` pour les unions/intersections
- **Null checks** : Utiliser optional chaining (`?.`) et nullish coalescing (`??`)
- **Enums** : Préférer `as const` aux enums pour de meilleures performances
- **Generic constraints** : Utiliser `extends` pour contraindre les génériques

## ❌ Mauvaises pratiques

- **`any` partout** : Éviter `any` - utiliser `unknown` ou typer correctement
- **Type assertions abusives** : Éviter `as Type` quand un type guard est possible
- **Ignorer les erreurs** : Ne pas utiliser `// @ts-ignore` sans justification
- **Non-null assertion** : Éviter `!` (non-null assertion) - préférer les guards
- **Implicit any** : Ne pas laisser de paramètres sans type

## ⚠️ Pièges courants

- **Catch variables** : En strict mode, catch donne `unknown`, pas `any` → vérifier avant d'utiliser
- **Array methods** : `find()` retourne `T | undefined`, pas `T`
- **Object.keys()** : Retourne `string[]`, pas `(keyof T)[]` → utiliser un type guard
- **Vue props** : Les props avec default values nécessitent `withDefaults()`

## 🔗 Sources
- [TypeScript Best Practices 2025](https://dev.to/mitu_mariam/typescript-best-practices-in-2025-57hb)
- [TypeScript Strict Mode Guide](https://medium.com/@AlexanderObregon/getting-strict-mode-right-in-typescript-b41f6ac95431)
- [Mastering TypeScript 2025](https://www.bacancytechnology.com/blog/typescript-best-practices)

## 📚 Contexte projet
- Configuration TypeScript gérée par Nuxt (`.nuxt/tsconfig.*.json`)
- Strict mode activé par défaut
- Types générés automatiquement pour les composants et composables

---

# 🟢 Tailwind CSS (v6.14.0 via @nuxtjs/tailwindcss)

## ✅ Bonnes pratiques

- **Classes complètes** : Toujours utiliser des classes complètes (`bg-blue-500`), jamais dynamiques
- **Design tokens** : Définir les couleurs/espacements dans `tailwind.config.js`
- **Composants réutilisables** : Extraire les patterns répétés dans des composants Vue
- **@apply modéré** : Utiliser `@apply` uniquement pour les styles vraiment réutilisés
- **Responsive** : Utiliser les breakpoints (`sm:`, `md:`, `lg:`) mobile-first
- **Safelist** : Ajouter les classes dynamiques au safelist pour éviter la purge
- **Container centré** : Configurer le container avec `mx-auto` et padding consistant

## ❌ Mauvaises pratiques

- **Classes dynamiques** : `bg-${color}-500` ne fonctionne pas (purge les classes)
- **Class soup illisible** : Éviter 20+ classes sur un élément → extraire en composant
- **@apply excessif** : Recréer du CSS traditionnel avec `@apply` partout
- **Ignorer le purge** : Ne pas configurer correctement `content` = CSS énorme en prod
- **!important** : Éviter les `!important` - restructurer la cascade
- **Styles inline** : Ne pas mélanger `style=""` avec Tailwind

## ⚠️ Pièges courants

- **Classes purgées en prod** : Vérifier que `content` couvre tous les fichiers
- **PrimeVue conflicts** : Utiliser `tailwindcss-primeui` pour la compatibilité
- **Dark mode** : Nécessite configuration spécifique (`class` ou `media`)
- **Tailwind v4 ESLint** : Le plugin ESLint Tailwind n'est pas compatible avec v4 (juin 2025)

## 🔗 Sources
- [Tailwind CSS Official Docs](https://tailwindcss.com/)
- [Tailwind CSS v4 Best Practices](https://medium.com/@sureshdotariya/tailwind-css-4-best-practices-for-enterprise-scale-projects-2025-playbook-bf2910402581)
- [Debugging Tailwind CSS 4](https://medium.com/@sureshdotariya/debugging-tailwind-css-4-in-2025-common-mistakes-and-how-to-fix-them-b022e6cb0a63)

## 📚 Contexte projet
- Configuration dans `tailwind.config.js`
- Couleurs custom : `primary` (jaune), `secondary` (noir), `success`, `warning`, `error`, `info`
- Couleurs plateformes : `platform-vinted`, `platform-ebay`, `platform-etsy`
- Plugin : `tailwindcss-primeui` pour compatibilité PrimeVue
- Safelist configuré pour les classes dynamiques

---

# 🟢 PrimeVue 4 (v4.5.1)

## ✅ Bonnes pratiques

- **Import sélectif** : Importer uniquement les composants utilisés pour réduire le bundle
- **Theming CSS variables** : Utiliser les CSS variables pour la personnalisation
- **Pass-through props** : Utiliser `pt` pour personnaliser les éléments internes
- **Unstyled mode** : Possible d'utiliser le mode unstyled avec Tailwind presets
- **Accessibilité** : Les composants sont WCAG compliant - ne pas casser l'accessibilité
- **Slots** : Utiliser les slots pour personnaliser le contenu des composants
- **Forms** : Utiliser les composants de formulaire avec validation intégrée

## ❌ Mauvaises pratiques

- **Override CSS direct** : Éviter les `!important` sur les styles PrimeVue
- **Recréer des composants** : Ne pas recréer ce que PrimeVue fournit déjà
- **Ignorer les props** : Lire la doc - beaucoup de comportements configurables via props
- **Mélanger themes** : Ne pas mélanger styled et unstyled dans le même projet

## ⚠️ Pièges courants

- **Z-index modals** : Les modals/dialogs ont des z-index élevés - attention aux conflits
- **DataTable performance** : Pour de gros datasets, activer virtual scrolling
- **CSS Layers** : PrimeVue 4 utilise CSS layers - peut affecter la cascade

## 🔗 Sources
- [PrimeVue Official Documentation](https://primevue.org/)
- [PrimeVue GitHub](https://github.com/primefaces/primevue)
- [Vue School PrimeVue Tutorial](https://vueschool.io/articles/vuejs-tutorials/crafting-stunning-uis-with-prime-vue/)

## 📚 Contexte projet
- Transpilé via `build.transpile: ['primevue']`
- Icônes via `primeicons`
- Intégré avec Tailwind via `tailwindcss-primeui`
- CSS importé globalement dans `nuxt.config.ts`

---

# 🟢 Pinia (v0.11.3 via @pinia/nuxt)

## ✅ Bonnes pratiques

- **Stores modulaires** : Un store par domaine (auth, products, cart) - pas de store monolithique
- **Composition API stores** : Préférer `defineStore` avec setup function pour TypeScript
- **Getters pour dérivés** : Utiliser `computed` (getters) pour les valeurs dérivées
- **Actions pour mutations** : Encapsuler les mutations dans des actions avec logique
- **storeToRefs()** : Utiliser `storeToRefs()` pour destructurer en gardant la réactivité
- **Plugins** : Utiliser les plugins pour la persistance, logging, etc.
- **DevTools** : Profiter de l'intégration Vue DevTools pour débugger

## ❌ Mauvaises pratiques

- **Store global unique** : Ne pas mettre tout l'état dans un seul store
- **Mutations directes sans actions** : Éviter de modifier l'état directement depuis les composants
- **State dans composants** : Ne pas dupliquer l'état du store dans les composants
- **Oublier storeToRefs** : `const { count } = useStore()` perd la réactivité → `storeToRefs()`
- **Circular dependencies** : Éviter les dépendances circulaires entre stores

## ⚠️ Pièges courants

- **SSR state** : En SSR, l'état est partagé entre requêtes - utiliser `useState` de Nuxt si nécessaire
- **Hydration** : L'état initial doit correspondre entre serveur et client
- **Persistence** : Pour persister, utiliser `pinia-plugin-persistedstate`

## 🔗 Sources
- [Pinia Official Documentation](https://pinia.vuejs.org/introduction.html)
- [Pinia Best Practices](https://masteringpinia.com/blog/5-best-practices-for-scalable-vuejs-state-management-with-pinia)
- [Vue 3 + Pinia Complete Guide 2025](https://medium.com/@dedikusniadi/vue-3-pinia-the-complete-guide-to-state-management-in-2025-712cc3cd691c)

## 📚 Contexte projet
- Module Nuxt : `@pinia/nuxt`
- Stores dans `stores/`
- Pattern : setup function avec TypeScript

---

# 🟢 VueUse (v14.1.0)

## ✅ Bonnes pratiques

- **Naming `use*`** : Tous les composables commencent par `use`
- **TypeScript** : Écrire les composables en TypeScript pour l'autocomplétion
- **MaybeRefOrGetter** : Accepter `ref`, `getter`, ou valeur brute pour la flexibilité
- **Cleanup** : Toujours nettoyer les side effects (event listeners, intervals) dans `onUnmounted`
- **SSR safe** : Vérifier `typeof window !== 'undefined'` pour le code browser-only
- **Retourner des refs** : Retourner un objet avec des refs pour permettre la destructuration

## ❌ Mauvaises pratiques

- **Appel hors setup** : Ne pas appeler les composables en dehors de `setup()` ou `<script setup>`
- **Async au top-level** : Éviter `await` au top-level d'un composable sans gestion appropriée
- **State global** : Ne pas utiliser de state global dans un composable (sauf si intentionnel)
- **Réinventer** : Vérifier si VueUse n'a pas déjà le composable avant de l'écrire

## ⚠️ Pièges courants

- **Lifecycle hooks** : Les hooks comme `onMounted` dans un composable nécessitent un contexte Vue
- **Reactive unwrap** : Les refs dans un reactive sont auto-unwrapped - peut être confus
- **Memory leaks** : Oublier de cleanup = memory leaks dans les SPA

## 🔗 Sources
- [Vue.js Composables Guide](https://vuejs.org/guide/reusability/composables.html)
- [VueUse Style Guide](https://alexop.dev/posts/vueuse_composables_style_guide/)
- [Coding Better Composables](https://www.vuemastery.com/blog/coding-better-composables-1-of-5/)

## 📚 Contexte projet
- Module Nuxt : `@vueuse/nuxt`
- Composables auto-importés
- Utilisation courante : `useStorage`, `useFetch`, `onClickOutside`, etc.

---

# 🟢 Vitest (v4.0.16)

## ✅ Bonnes pratiques

- **Test user behavior** : Tester ce que l'utilisateur voit/fait, pas l'état interne
- **Accessible selectors** : Utiliser `getByRole`, `getByLabelText` plutôt que `getByTestId`
- **Mock APIs** : Toujours mocker les appels API pour des tests isolés et rapides
- **Async/await** : Utiliser `await` pour les interactions et requêtes
- **Factory pattern** : Créer des factories pour les données de test
- **Browser mode** : Préférer Vitest Browser Mode à JSDOM pour les tests d'intégration
- **Test early** : Écrire les tests tôt - plus on attend, plus c'est difficile

## ❌ Mauvaises pratiques

- **Tester l'implémentation** : Ne pas tester les détails d'implémentation (refs, data internes)
- **Tests fragiles** : Éviter les sélecteurs basés sur la structure DOM
- **Tests lents** : Ne pas faire de vrais appels API dans les tests unitaires
- **Copier-coller** : Éviter la duplication - utiliser des helpers et fixtures
- **Ignorer les warnings** : Les warnings Vue dans les tests sont souvent de vrais problèmes

## ⚠️ Pièges courants

- **Composables avec lifecycle** : Tester un composable avec `onMounted` nécessite un wrapper component
- **Async updates** : Utiliser `await nextTick()` ou `await flushPromises()` après les mutations
- **Happy-dom vs jsdom** : happy-dom est plus rapide mais peut avoir des différences subtiles

## 🔗 Sources
- [Vue.js Testing Guide](https://vuejs.org/guide/scaling-up/testing)
- [Vitest Browser Mode Vue 3](https://alexop.dev/posts/vue3_testing_pyramid_vitest_browser_mode/)
- [Vue School Vitest Guide](https://vueschool.io/articles/vuejs-tutorials/start-testing-with-vitest-beginners-guide/)

## 📚 Contexte projet
- Configuration : `vitest` dans package.json scripts
- DOM : `happy-dom`
- Test utils : `@vue/test-utils`
- Commandes : `npm test`, `npm run test:run`, `npm run test:coverage`

---

# 🟢 ESLint 9 (v9.39.2)

## ✅ Bonnes pratiques

- **Flat config** : Utiliser le nouveau format `eslint.config.js` (flat config)
- **Vue plugin** : Utiliser `eslint-plugin-vue` avec les presets recommandés
- **TypeScript config** : Utiliser `@vue/eslint-config-typescript` pour Vue + TS
- **Spread configs** : Les configs flat sont des arrays - utiliser le spread (`...`)
- **Lint before commit** : Intégrer ESLint dans les hooks pre-commit

## ❌ Mauvaises pratiques

- **Ignorer les warnings** : Ne pas désactiver les règles sans bonne raison
- **eslintrc legacy** : Ne plus utiliser `.eslintrc.*` - migrer vers flat config
- **Disable global** : Éviter `/* eslint-disable */` global - cibler les lignes spécifiques
- **Configs obsolètes** : Ne pas utiliser de configs non maintenues

## ⚠️ Pièges courants

- **ESLint 10** : `.eslintrc` sera supprimé - migrer maintenant vers flat config
- **Plugin compatibility** : Certains plugins ne supportent pas encore flat config
- **Vue SFC parsing** : S'assurer que le parser Vue est correctement configuré

## 🔗 Sources
- [eslint-plugin-vue User Guide](https://eslint.vuejs.org/user-guide/)
- [Vue ESLint Config TypeScript](https://github.com/vuejs/eslint-config-typescript)
- [ESLint 9 Flat Config Tutorial](https://dev.to/aolyang/eslint-9-flat-config-tutorial-2bm5)

## 📚 Contexte projet
- Module Nuxt : `@nuxt/eslint`
- Commandes : `npm run lint`, `npm run lint:fix`
- Config flat gérée par le module Nuxt

---

# 🟢 Chart.js + vue-chartjs (v4.5.1 / v5.3.3)

## ✅ Bonnes pratiques

- **Destroy on unmount** : Toujours détruire l'instance chart dans `onUnmounted`
- **Prepared data** : Fournir les données au format interne Chart.js avec `parsing: false`
- **Disable animations** : Pour updates fréquentes, désactiver les animations
- **Responsive** : Utiliser des dimensions en pourcentage et gérer le resize
- **Lazy loading** : Charger Chart.js dynamiquement si non critique au first paint
- **Accessibility** : Ajouter des descriptions ARIA pour les graphiques

## ❌ Mauvaises pratiques

- **Gros datasets** : Chart.js n'est pas optimal pour de très gros datasets (>10k points)
- **Oublier cleanup** : Ne pas détruire le chart = memory leak
- **Recreate on update** : Mettre à jour les données plutôt que recréer le chart

## ⚠️ Pièges courants

- **Canvas resize** : Le canvas peut ne pas resize automatiquement - gérer manuellement
- **SSR** : Chart.js nécessite `<ClientOnly>` en SSR (utilise canvas)
- **Multiple charts** : Chaque chart doit avoir un canvas unique

## 🔗 Sources
- [Chart.js Performance Guide](https://www.chartjs.org/docs/latest/general/performance.html)
- [vue-chartjs Documentation](https://vue-chartjs.org/)
- [Vue Chart Libraries Guide 2025](https://www.luzmo.com/blog/vue-chart-libraries)

## 📚 Contexte projet
- Wrapper : `vue-chartjs`
- Usage : Dashboard stats, analytics Vinted
- Toujours wrapper dans `<ClientOnly>` pour le SSR

---

# 🏗️ Architecture Frontend Stoflow

## Convention de Nommage des Composants (Nuxt Auto-Import)

Le projet utilise l'auto-import Nuxt avec `pathPrefix: true` (par défaut).
Les composants sont nommés automatiquement en combinant le chemin du dossier + nom du fichier.

**Règle : `components/<folder>/<File>.vue` → `<FolderFile>`**

### Exemples :
| Fichier | Composant auto-importé |
|---------|------------------------|
| `components/sidebar/MenuItem.vue` | `<SidebarMenuItem>` |
| `components/vinted/StatsCards.vue` | `<VintedStatsCards>` |
| `components/layout/DashboardSidebar.vue` | `<LayoutDashboardSidebar>` |
| `components/ui/InfoBox.vue` | `<UiInfoBox>` |
| `components/platform/HeaderActions.vue` | `<PlatformHeaderActions>` |

### Règles importantes :
- **Ne pas répéter** le préfixe dans le nom du fichier (éviter `vinted/VintedStatsCards.vue`)
- **Ne pas utiliser d'imports explicites** pour les composants locaux - laisser Nuxt auto-importer
- **Organiser par domaine** : `vinted/`, `ebay/`, `etsy/`, `sidebar/`, `ui/`, etc.

## Structure du Projet

```
frontend/
├── app.vue              # Point d'entrée
├── nuxt.config.ts       # Configuration Nuxt
├── tailwind.config.js   # Configuration Tailwind
├── assets/
│   └── css/            # Styles globaux (design-system, dashboard)
├── components/
│   ├── layout/         # Headers, Sidebars, Footers
│   ├── ui/             # Composants génériques (buttons, cards, modals)
│   ├── vinted/         # Composants spécifiques Vinted
│   ├── ebay/           # Composants spécifiques eBay
│   ├── etsy/           # Composants spécifiques Etsy
│   └── products/       # Composants produits
├── composables/        # Composables (useAuth, useApi, etc.)
├── layouts/            # Layouts Nuxt (default, dashboard)
├── pages/              # Pages/routes auto-générées
├── stores/             # Stores Pinia
├── services/           # Services API
├── types/              # Types TypeScript
└── tests/              # Tests Vitest
```

## API Communication

- Backend : FastAPI REST API sur `/api/*`
- Frontend : Appels API via composables/services
- Authentification : Bearer token JWT
- Runtime config : `apiUrl` et `apiBaseUrl` configurés dans `nuxt.config.ts`

---

# 🎨 Frontend Aesthetics Guidelines (Anti "AI Slop")

> **Objectif** : Éviter le design générique "AI slop" (Inter, dégradés violets, layouts prévisibles).
> Cette section guide Claude pour créer des interfaces distinctives et mémorables.

## Principes Fondamentaux

Avant de coder une interface, choisir une **direction esthétique claire** :
- **Purpose** : Quel problème cette interface résout ? Pour qui ?
- **Tone** : Choisir un style marqué (minimal raffiné, maximalist, retro-futuriste, brutalist, etc.)
- **Differentiation** : Qu'est-ce qui rend cette interface mémorable ?

## Typography

### 🎨 Fonts StoFlow (Configurées)

| Usage | Font | Classe Tailwind |
|-------|------|-----------------|
| **Headings** | Plus Jakarta Sans | `font-display` |
| **Body text** | IBM Plex Sans | `font-body` ou `font-sans` |
| **Code/SKUs** | JetBrains Mono | `font-mono` |

### Utilisation

```html
<!-- Headings (automatique sur h1-h6) -->
<h1 class="font-display text-3xl font-bold">Dashboard</h1>

<!-- Body text (par défaut) -->
<p>Texte normal utilise IBM Plex Sans automatiquement</p>

<!-- Code/SKU -->
<span class="font-mono">SKU-2026-0142</span>
```

### ❌ Polices INTERDITES
- Inter, Roboto, Open Sans, Lato, Arial, system fonts

### Règles
- **Headings** : Toujours utiliser `font-display` (Plus Jakarta Sans)
- **Body** : Par défaut `font-body` (IBM Plex Sans)
- **Code/Références** : Utiliser `font-mono` ou classe `.sku` / `.reference`
- **Weights** : Utiliser 600-800 pour les titres, 400-500 pour le body

## Color & Theme

- **CSS variables** pour la cohérence
- **Couleur dominante + accents vifs** (pas de palettes tièdes/équilibrées)
- S'inspirer des **thèmes IDE** : Dracula, Nord, Catppuccin, Tokyo Night, Gruvbox
- **ÉVITER** : dégradés violets sur fond blanc, palettes "safe"

## Motion & Animations

- **Un page load orchestré** > micro-interactions éparpillées
- Utiliser `animation-delay` pour les reveals progressifs (stagger effect)
- **CSS-first**, JavaScript si vraiment nécessaire
- Focus sur les moments à fort impact (entrée de page, hover states surprenants)

## Backgrounds & Effets

- **Créer de l'atmosphère** : ne pas se contenter de couleurs solides
- Techniques : gradients CSS en couches, patterns géométriques, textures noise
- Effets contextuels qui matchent l'esthétique globale
- Ombres dramatiques, overlays, grain

## Spatial Composition

- Layouts **inattendus** : asymétrie, overlap, flux diagonal
- Éléments qui **brisent la grille** intentionnellement
- Espacement généreux OU densité contrôlée (pas de between tiède)

## ⚠️ À ÉVITER (Generic AI Aesthetics)

| Pattern générique | Alternative distinctive |
|-------------------|------------------------|
| Inter/Roboto partout | Fonts caractéristiques par contexte |
| Dégradé violet/bleu sur blanc | Palette cohérente inspirée d'un thème |
| Cards identiques en grille | Layouts asymétriques, overlaps |
| Hover = scale 1.05 | Hover states surprenants (color shift, reveal) |
| Tous les éléments centrés | Mix d'alignements, tension visuelle |

## Application pour StoFlow

Pour StoFlow (e-commerce multi-plateforme), privilégier :
- **Ton** : Professionnel mais moderne, pas corporate fade
- **Palette** : Utiliser les couleurs de marque définies + accents vifs
- **Différenciation par plateforme** : Vinted (teal), eBay (multi), Etsy (orange) avec identité propre
- **Dashboard** : Dense en information mais hiérarchie claire, pas flat/boring

---

# 🚫 Règles Spécifiques Frontend

## ❌ Ne JAMAIS :
- Utiliser `any` sans justification
- Modifier les props directement
- Oublier de cleanup les side effects (`onUnmounted`)
- Accéder à `window`/`document` sans vérifier le contexte SSR
- Utiliser des classes Tailwind dynamiques (`bg-${color}-500`)

## ✅ TOUJOURS :
- Utiliser `<script setup lang="ts">`
- Nettoyer les event listeners dans `onUnmounted`
- Utiliser les composables VueUse existants avant d'en créer
- Wrapper les composants canvas (Chart.js) dans `<ClientOnly>`
- Utiliser `storeToRefs()` pour destructurer les stores Pinia

---

**Version :** 2.2
**Dernière mise à jour :** 2026-01-13
**Applicable à :** Frontend Vue/Nuxt uniquement
