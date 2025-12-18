# Utilisation des Attributs - Frontend

## Vue d'ensemble

Le système d'attributs dans le frontend utilise le composable `useAttributes()` qui communique avec l'API générique backend pour récupérer dynamiquement tous les types d'attributs.

## Composable useAttributes

### Import et initialisation

```typescript
import { useAttributes } from '~/composables/useAttributes'

const {
  // États réactifs
  categories,
  conditions,
  genders,
  seasons,
  brands,

  // États de chargement
  loadingCategories,
  loadingConditions,
  loadingGenders,
  loadingSeasons,
  loadingBrands,

  // Méthodes spécifiques
  fetchCategories,
  fetchConditions,
  fetchGenders,
  fetchSeasons,
  fetchBrands,
  fetchAllAttributes,
  clearCache,

  // Méthode générique
  fetchAttribute
} = useAttributes()
```

## Utilisation dans un composant

### 1. Méthodes spécifiques (attributs préchargés)

Pour les attributs courants (categories, conditions, genders, seasons, brands) :

```vue
<script setup lang="ts">
const { fetchCategories, categories, loadingCategories } = useAttributes()

onMounted(async () => {
  await fetchCategories('fr') // Langue: en, fr, de, it, es, nl, pl
})
</script>

<template>
  <Dropdown
    :options="categories"
    optionLabel="label"
    optionValue="value"
    :loading="loadingCategories"
  />
</template>
```

### 2. Méthode générique (nouveaux attributs)

Pour charger n'importe quel attribut dynamiquement :

```vue
<script setup lang="ts">
import type { AttributeOption } from '~/composables/useAttributes'

const { fetchAttribute } = useAttributes()

const colors = ref<AttributeOption[]>([])
const loadingColors = ref(false)

const fetchColors = async () => {
  loadingColors.value = true
  try {
    colors.value = await fetchAttribute('colors', 'fr')
  } finally {
    loadingColors.value = false
  }
}

onMounted(() => {
  fetchColors()
})
</script>

<template>
  <Dropdown
    :options="colors"
    optionLabel="label"
    optionValue="value"
    :loading="loadingColors"
  />
</template>
```

## Exemple complet - ProductForm.vue

Voici comment le ProductForm.vue utilise le système :

```vue
<script setup lang="ts">
import { computed, onMounted } from 'vue'
import type { AttributeOption } from '~/composables/useAttributes'

// Attributs prédéfinis
const {
  categories,
  conditions,
  genders,
  seasons,
  fetchAllAttributes,
  fetchAttribute,
  loadingCategories,
  loadingConditions
} = useAttributes()

// Attributs personnalisés
const colors = ref<AttributeOption[]>([])
const materials = ref<AttributeOption[]>([])
const fits = ref<AttributeOption[]>([])

const loadingColors = ref(false)
const loadingMaterials = ref(false)
const loadingFits = ref(false)

// Fonction pour charger tous les attributs
const loadAttributes = async (lang: string = 'en') => {
  // Charger attributs prédéfinis
  await fetchAllAttributes(lang)

  // Charger attributs personnalisés en parallèle
  await Promise.all([
    // Colors
    (async () => {
      loadingColors.value = true
      try {
        colors.value = await fetchAttribute('colors', lang)
      } finally {
        loadingColors.value = false
      }
    })(),

    // Materials
    (async () => {
      loadingMaterials.value = true
      try {
        materials.value = await fetchAttribute('materials', lang)
      } finally {
        loadingMaterials.value = false
      }
    })(),

    // Fits
    (async () => {
      loadingFits.value = true
      try {
        fits.value = await fetchAttribute('fits', lang)
      } finally {
        loadingFits.value = false
      }
    })()
  ])
}

onMounted(() => {
  loadAttributes('en') // ou 'fr' pour français
})
</script>

<template>
  <form>
    <!-- Catégorie -->
    <Dropdown
      :options="categories"
      optionLabel="label"
      optionValue="value"
      :loading="loadingCategories"
    />

    <!-- Couleur -->
    <Dropdown
      :options="colors"
      optionLabel="label"
      optionValue="value"
      :loading="loadingColors"
    />

    <!-- Matière -->
    <Dropdown
      :options="materials"
      optionLabel="label"
      optionValue="value"
      :loading="loadingMaterials"
    />
  </form>
</template>
```

## Ajouter un nouvel attribut dans le formulaire

### Étape 1 : Vérifier que l'attribut existe côté backend

Consultez `/backend/docs/ATTRIBUTES_API.md` pour la liste complète.

Types disponibles :
- `categories`, `conditions`, `genders`, `seasons`, `brands`
- `colors`, `materials`, `fits`, `sizes`
- *(ajoutez les vôtres selon la config backend)*

### Étape 2 : Ajouter dans votre composant

```vue
<script setup lang="ts">
import type { AttributeOption } from '~/composables/useAttributes'

const { fetchAttribute } = useAttributes()

// 1. Créer les états
const patterns = ref<AttributeOption[]>([])
const loadingPatterns = ref(false)

// 2. Créer la fonction de chargement
const fetchPatterns = async () => {
  loadingPatterns.value = true
  try {
    patterns.value = await fetchAttribute('patterns', 'fr')
  } finally {
    loadingPatterns.value = false
  }
}

// 3. Appeler au montage
onMounted(() => {
  fetchPatterns()
})
</script>

<template>
  <!-- 4. Utiliser dans un Dropdown -->
  <Dropdown
    :options="patterns"
    optionLabel="label"
    optionValue="value"
    :loading="loadingPatterns"
    placeholder="Sélectionner le motif"
  />
</template>
```

## Format des données

Tous les attributs retournent le même format :

```typescript
interface AttributeOption {
  value: string        // Valeur technique (ex: "Jeans")
  label: string        // Label traduit (ex: "Jean" en FR)
  [key: string]: any   // Champs supplémentaires selon le type
}
```

### Exemples de champs supplémentaires

**Categories** :
```typescript
{
  value: "Jeans",
  label: "Jeans",
  parent_category: "Clothing",
  default_gender: "unisex"
}
```

**Conditions** :
```typescript
{
  value: "EXCELLENT",
  label: "Excellent",
  coefficient: 0.95,
  vinted_id: 1,
  ebay_condition: "PRE_OWNED_EXCELLENT"
}
```

**Sizes** :
```typescript
{
  value: "M",
  label: "M",
  category: "Shirts",
  sort_order: 3
}
```

## Configuration PrimeVue Dropdown

Pour que les dropdowns fonctionnent correctement avec les attributs :

```vue
<Dropdown
  v-model="selectedValue"
  :options="attributesList"
  optionLabel="label"     <!-- Affiche le label traduit -->
  optionValue="value"     <!-- Stocke la valeur technique -->
  placeholder="Sélectionner..."
  :loading="isLoading"    <!-- Affiche un spinner pendant le chargement -->
  class="w-full"
/>
```

**Important** :
- `optionLabel="label"` : Affiche le texte visible à l'utilisateur
- `optionValue="value"` : Stocke la valeur technique dans le model
- `:loading="isLoading"` : Feedback visuel pendant le chargement

## Gestion du cache

Le composable met automatiquement en cache les données :

```typescript
// Premier appel : fetch depuis l'API
await fetchCategories('fr') // → Appel API

// Deuxième appel : retourne le cache
await fetchCategories('fr') // → Aucun appel API, données en cache

// Vider le cache si nécessaire
const { clearCache } = useAttributes()
clearCache()
```

## Changement de langue

Pour changer la langue des labels :

```typescript
// Charger en français
await fetchAllAttributes('fr')
await fetchAttribute('colors', 'fr')

// Changer pour l'anglais (vide le cache et recharge)
clearCache()
await fetchAllAttributes('en')
await fetchAttribute('colors', 'en')
```

## Gestion des erreurs

Le composable gère automatiquement les erreurs :

```typescript
try {
  const colors = await fetchAttribute('colors', 'fr')
  // colors sera toujours un tableau, vide si erreur
} catch (error) {
  // Les erreurs sont loggées dans la console
  // Aucune exception n'est lancée
}
```

## Recherche (brands uniquement)

Seul l'attribut `brands` supporte la recherche :

```typescript
const { fetchBrands } = useAttributes()

// Rechercher "Nike"
const brands = await fetchBrands('nike', 50) // search, limit
```

## Performance

### Chargement en parallèle

Toujours charger les attributs en parallèle pour optimiser les performances :

```typescript
// ✅ BON - Chargement parallèle
await Promise.all([
  fetchCategories('fr'),
  fetchConditions('fr'),
  fetchAttribute('colors', 'fr'),
  fetchAttribute('materials', 'fr')
])

// ❌ MAUVAIS - Chargement séquentiel
await fetchCategories('fr')
await fetchConditions('fr')
await fetchAttribute('colors', 'fr')
await fetchAttribute('materials', 'fr')
```

### Lazy loading

Pour les formulaires longs, chargez uniquement les attributs nécessaires :

```typescript
// Au montage : charger uniquement les attributs obligatoires
onMounted(async () => {
  await fetchAllAttributes('fr')
})

// Au clic sur un onglet : charger les attributs optionnels
const showOptionalFields = ref(false)

const loadOptionalAttributes = async () => {
  showOptionalFields.value = true
  await Promise.all([
    fetchAttribute('colors', 'fr'),
    fetchAttribute('materials', 'fr')
  ])
}
```

## Debugging

Pour voir les données chargées dans la console :

```typescript
const { categories } = useAttributes()

watch(categories, (newValue) => {
  console.log('Categories loaded:', newValue)
}, { immediate: true })
```

---

**Version :** 1.0
**Dernière mise à jour :** 2025-12-09
**Auteur :** Claude Code
