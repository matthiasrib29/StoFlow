# Business Logic - Stoflow Frontend

## Index Rapide

| Thème | Règles Clés Frontend |
|-------|---------------------|
| [UI/UX](#uiux) | Responsive, accessibilité, feedback utilisateur |
| [Validation](#validation) | Validation client AVANT envoi API |
| [Gestion Erreurs](#gestion-erreurs) | Toast notifications, retry logic |
| [Navigation](#navigation) | Protection routes, redirections |
| [Performance](#performance) | Lazy loading, pagination, cache |

---

## UI/UX

<details>
<summary><b>Design System</b></summary>

**Couleurs :**
- Primaire : `#facc15` (Jaune) ’ Actions, CTA
- Secondaire : `#1a1a1a` (Noir) ’ Textes, UI principale
- Gris : Backgrounds, bordures

**Typography :**
- Titres pages : `text-3xl font-bold text-secondary-900`
- Sous-titres : `text-gray-600`
- Espacement : `mb-1` entre titre et sous-titre

**Composants :**
- Boutons primaires : Jaune avec hover effect
- Boutons secondaires : Gris clair
- Cards : `rounded-2xl shadow-sm border border-gray-100`

**Guide :** Voir [STYLING_GUIDE.md](./STYLING_GUIDE.md)

</details>

<details>
<summary><b>Responsive</b></summary>

**Breakpoints Tailwind :**
- Mobile : < 768px
- Tablet : 768px - 1024px
- Desktop : > 1024px

**Grids adaptatifs :**
```vue
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
```

**Sidebar :**
- Desktop : Sidebar fixe 256px
- Mobile : À implémenter (menu hamburger)

</details>

<details>
<summary><b>Accessibilité</b></summary>

**Keyboard Navigation :**
- Tous les boutons/links focusables
- Focus visible : Outline jaune 2px

**ARIA Labels :**
- Images décoratives : `aria-hidden="true"`
- Actions : `aria-label` descriptif

**Contraste :**
- Texte noir sur fond blanc :  AAA
- Texte jaune sur fond blanc :   Éviter (contraste insuffisant)

</details>

<details>
<summary><b>Feedback Utilisateur</b></summary>

**Toast Notifications :**
- Succès : Fond jaune, icône check
- Erreur : Fond rouge, icône erreur
- Info : Fond bleu, icône info

```typescript
toast.add({
  severity: 'success',
  summary: 'Produit créé',
  detail: 'Le produit a été créé avec succès',
  life: 3000
})
```

**Loading States :**
- Skeleton loaders pour listes
- Spinner pour actions ponctuelles
- Désactiver boutons pendant loading

**Confirmation :**
- Dialog pour actions destructives (supprimer)
- Pas de confirmation pour actions réversibles

</details>

---

## Validation

<details>
<summary><b>Validation Formulaires</b></summary>

**Principe :** Valider côté client AVANT envoi API

**Produit :**
```typescript
// Règles validation
{
  name: {
    required: true,
    minLength: 3,
    maxLength: 200
  },
  price: {
    required: true,
    min: 0.01,
    pattern: /^\d+(\.\d{1,2})?$/  // 2 décimales max
  },
  description: {
    maxLength: 5000
  },
  images: {
    maxCount: 10,
    maxSize: 5 * 1024 * 1024,  // 5MB
    allowedTypes: ['image/jpeg', 'image/png']
  }
}
```

**Affichage erreurs :**
- Inline sous chaque champ
- Résumé en haut du formulaire si plusieurs erreurs
- Désactiver submit si invalide

</details>

<details>
<summary><b>Messages d'Erreur</b></summary>

**Français, clairs, actionnables :**

L Mauvais :
- "Invalid input"
- "Error 400"
- "Validation failed"

 Bon :
- "Le nom doit contenir au moins 3 caractères"
- "Le prix doit être supérieur à 0"
- "L'image ne doit pas dépasser 5MB"

</details>

---

## Gestion Erreurs

<details>
<summary><b>Erreurs API</b></summary>

**Codes HTTP gérés :**

| Code | Signification | Action Frontend |
|------|---------------|-----------------|
| 400 | Bad Request | Afficher message erreur spécifique |
| 401 | Unauthorized | Refresh token OU redirect login |
| 403 | Forbidden | Message "Accès refusé" |
| 404 | Not Found | Message "Ressource introuvable" |
| 409 | Conflict | Message erreur (ex: nom dupliqué) |
| 422 | Validation Error | Afficher erreurs par champ |
| 429 | Too Many Requests | Message "Trop de requêtes, réessayez" |
| 500 | Server Error | Message générique + log Sentry |

**Exemple gestion :**
```typescript
try {
  await productsStore.createProduct(data)
  toast.add({ severity: 'success', summary: 'Produit créé' })
  router.push('/dashboard/products')
} catch (error) {
  if (error.status === 409) {
    toast.add({ severity: 'error', summary: 'Un produit avec ce nom existe déjà' })
  } else if (error.status === 422) {
    // Afficher erreurs validation inline
  } else {
    toast.add({ severity: 'error', summary: 'Erreur lors de la création' })
  }
}
```

</details>

<details>
<summary><b>Retry Logic</b></summary>

**Requêtes à retry :**
- Erreurs réseau (timeout, connexion perdue)
- 500, 502, 503, 504 (erreurs serveur temporaires)

**Requêtes à NE PAS retry :**
- 400, 401, 403, 404, 409, 422 (erreurs client)

**Implémentation :**
```typescript
async function fetchWithRetry(url, options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await $fetch(url, options)
    } catch (error) {
      if (i === maxRetries - 1 || !isRetryable(error)) throw error
      await sleep(Math.pow(2, i) * 1000)  // Backoff: 1s, 2s, 4s
    }
  }
}
```

</details>

<details>
<summary><b>Offline Handling</b></summary>

**Détection :**
```typescript
window.addEventListener('offline', () => {
  toast.add({
    severity: 'warn',
    summary: 'Connexion perdue',
    detail: 'Vérifiez votre connexion internet',
    life: 0  // Permanent jusqu'à reconnexion
  })
})
```

**Comportement :**
- Désactiver actions nécessitant l'API
- Afficher banner "Mode hors ligne"
- Queue requêtes (roadmap)

</details>

---

## Navigation

<details>
<summary><b>Protection Routes</b></summary>

**Middleware :** `auth.global.ts`

**Logique :**
```typescript
// Routes publiques
if (['/login', '/'].includes(to.path)) {
  return
}

// Routes protégées /dashboard/*
if (to.path.startsWith('/dashboard')) {
  if (!authStore.isAuthenticated) {
    return navigateTo('/login')
  }
}
```

**Redirection après login :**
- Si `?redirect=/dashboard/products` ’ redirect vers produits
- Sinon ’ `/dashboard` par défaut

</details>

<details>
<summary><b>Breadcrumbs</b></summary>

**À implémenter (roadmap) :**

```
Dashboard > Produits > Mon Produit
```

**Règle :** Toujours afficher fil d'Ariane sur pages niveau 2+

</details>

---

## Performance

<details>
<summary><b>Lazy Loading</b></summary>

**Composants lourds :**
```typescript
const HeavyComponent = defineAsyncComponent(() =>
  import('./components/HeavyComponent.vue')
)
```

**Routes :**
Nuxt lazy-load automatiquement toutes les pages

**Images :**
```vue
<img loading="lazy" src="..." alt="..." />
```

</details>

<details>
<summary><b>Pagination</b></summary>

**Listes produits/publications :**
- Limite : 50 items par page par défaut
- Pagination côté serveur (API retourne `total`, `page`, `limit`)
- UI : Numéros de pages + Précédent/Suivant

**Infinite scroll :** Non (préférer pagination explicite)

</details>

<details>
<summary><b>Cache</b></summary>

**Stratégie :**
- Produits : Cache 5min dans store
- User info : Cache session entière
- Stats : Re-fetch à chaque visite dashboard

**Invalidation :**
- Création/modification/suppression ’ Clear cache immédiatement
- Refresh manuel : Bouton "Rafraîchir"

</details>

<details>
<summary><b>Optimistic UI</b></summary>

**Actions immédiates :**

**Exemple suppression produit :**
```typescript
async deleteProduct(id) {
  // 1. Optimistic update (retirer de la liste immédiatement)
  const index = this.products.findIndex(p => p.id === id)
  const removed = this.products.splice(index, 1)[0]

  try {
    // 2. Appel API
    await $fetch(`/api/products/${id}`, { method: 'DELETE' })
    toast.add({ severity: 'success', summary: 'Produit supprimé' })
  } catch (error) {
    // 3. Rollback si erreur
    this.products.splice(index, 0, removed)
    toast.add({ severity: 'error', summary: 'Erreur lors de la suppression' })
  }
}
```

**À utiliser pour :**
-  Suppression
-  Toggle status (actif/inactif)
- L Création (attendre confirmation serveur)

</details>

---

## Règles Métier Frontend

<details>
<summary><b>Produits</b></summary>

**Création :**
- Formulaire : Nom, description, prix, images
- Validation temps réel sur blur
- Images : Drag & drop + preview
- Auto-save brouillon (roadmap)

**Édition :**
- Même formulaire que création
- Bouton "Annuler" ’ Confirm dialog si modifications

**Suppression :**
- Dialog confirmation : "Êtes-vous sûr ?"
- Si publications actives ’ Bloquer avec message

**Limite :**
- Afficher compteur : "25/100 produits" (plan gratuit)
- Si limite atteinte ’ Banner upgrade

</details>

<details>
<summary><b>Publications</b></summary>

**Publication produit :**
- Sélection multi-plateformes (checkboxes)
- Aperçu description par plateforme (roadmap)
- Confirmation avant publication

**États affichés :**
- Draft : Badge gris
- Active : Badge vert
- Sold : Badge jaune
- Cancelled : Badge rouge

**Actions :**
- Republier (si cancelled)
- Marquer vendu (si active)
- Annuler (si active)

</details>

<details>
<summary><b>Plateformes</b></summary>

**Connexion :**
- Modal avec formulaire credentials
- Validation temps réel
- Test connexion avant save
- Message succès + close modal

**Déconnexion :**
- Confirm dialog
- Si publications actives ’ Avertissement

**Status :**
- Connecté : Badge vert
- Erreur : Badge rouge + message erreur
- Désactivé : Badge gris

</details>

---

## > Pour Claude

**Règles Frontend :**

1. **Toujours valider avant API** : Ne jamais envoyer données invalides
2. **Feedback immédiat** : Toast pour toutes actions importantes
3. **Gestion erreurs** : Messages clairs en français
4. **Responsive** : Tester mobile/tablet/desktop
5. **Accessibilité** : Focus, ARIA, contraste

**En cas de doute :**
- Consulter ce fichier
- Vérifier STYLING_GUIDE.md pour UI
- Si absent ’ **DEMANDER** à @maribeiro

**Source de vérité :** Ce fichier + ARCHITECTURE.md

---

*Dernière maj : 2024-12-07*
