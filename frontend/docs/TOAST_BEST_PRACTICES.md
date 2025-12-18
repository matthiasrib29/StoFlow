# 🍞 Bonnes Pratiques - PrimeVue Toast avec Nuxt 3 SSR

## ❌ Problème : "useToast is not defined"

Ce problème survient lorsque vous utilisez `useToast()` de PrimeVue dans un contexte SSR (Server-Side Rendering) de Nuxt 3.

### Pourquoi ça arrive ?

1. **SSR Context** : Nuxt 3 fait du rendu côté serveur par défaut
2. **Toast dépend du DOM** : Le ToastService de PrimeVue a besoin du navigateur
3. **Import manquant** : Oublier d'importer `useToast` depuis `primevue/usetoast`

## ✅ Solution Recommandée : Utiliser `useAppToast`

Nous avons créé un composable custom qui gère automatiquement le SSR.

### Usage Simple

```vue
<script setup lang="ts">
const { showSuccess, showError, showInfo, showWarn } = useAppToast()

const handleAction = async () => {
  try {
    // Votre logique...
    showSuccess('Succès!', 'Opération réussie')
  } catch (error) {
    showError('Erreur', 'Une erreur est survenue')
  }
}
</script>
```

### Avantages

✅ **Pas d'import nécessaire** : Auto-importé par Nuxt
✅ **Compatible SSR** : Fonctionne côté serveur et client
✅ **API simplifiée** : Méthodes dédiées par type
✅ **Type-safe** : TypeScript support complet
✅ **Logs en dev** : Console warnings si Toast pas disponible

## 📋 API du Composable

### `showSuccess(message, detail?, life?)`
```ts
showSuccess('Produit créé', 'Le produit a été ajouté avec succès', 3000)
```

### `showError(message, detail?, life?)`
```ts
showError('Erreur', 'Impossible de sauvegarder', 5000)
```

### `showInfo(message, detail?, life?)`
```ts
showInfo('Information', 'Mise à jour disponible', 3000)
```

### `showWarn(message, detail?, life?)`
```ts
showWarn('Attention', 'Action irréversible', 4000)
```

### `showToast(options)` - Avancé
```ts
const { showToast } = useAppToast()

showToast({
  severity: 'success',
  summary: 'Titre',
  detail: 'Détail',
  life: 3000,
  closable: true,
  // ... autres options PrimeVue Toast
})
```

## 🔧 Exemples Complets

### Exemple 1 : Login
```vue
<script setup lang="ts">
const authStore = useAuthStore()
const router = useRouter()
const { showSuccess, showError } = useAppToast()

const handleLogin = async () => {
  try {
    await authStore.login(email.value, password.value)
    showSuccess('Connexion réussie', `Bienvenue ${authStore.user?.full_name}!`)
    router.push('/dashboard')
  } catch (error: any) {
    showError('Erreur de connexion', error.message)
  }
}
</script>
```

### Exemple 2 : Création de Produit
```vue
<script setup lang="ts">
const { showSuccess, showError } = useAppToast()
const productsStore = useProductsStore()

const createProduct = async (data: ProductData) => {
  try {
    const product = await productsStore.createProduct(data)
    showSuccess('Produit créé', `${product.title} a été ajouté`)
  } catch (error: any) {
    showError('Erreur', error.data?.detail || 'Impossible de créer le produit')
  }
}
</script>
```

### Exemple 3 : Opération Longue avec Info
```vue
<script setup lang="ts">
const { showInfo, showSuccess } = useAppToast()

const syncProducts = async () => {
  showInfo('Synchronisation en cours', 'Veuillez patienter...')

  try {
    await api.syncProducts()
    showSuccess('Synchronisation terminée', 'Tous les produits sont à jour')
  } catch (error) {
    // ...
  }
}
</script>
```

## ⚠️ Ce qu'il NE FAUT PAS faire

### ❌ Mauvais : Import direct sans gestion SSR
```vue
<script setup lang="ts">
import { useToast } from 'primevue/usetoast'

// ❌ ERREUR : useToast is not defined (SSR)
const toast = useToast()

const action = () => {
  toast.add({ ... }) // ❌ Crash SSR
}
</script>
```

### ❌ Mauvais : Initialisation manuelle avec onMounted
```vue
<script setup lang="ts">
import { useToast } from 'primevue/usetoast'

let toast: any = null

onMounted(() => {
  if (import.meta.client) {
    toast = useToast()
  }
})

const action = () => {
  toast?.add({ ... }) // ❌ Verbose et répétitif
}
</script>
```

### ✅ Bon : Utiliser useAppToast
```vue
<script setup lang="ts">
const { showSuccess } = useAppToast()

const action = () => {
  showSuccess('Succès!') // ✅ Simple et fonctionne partout
}
</script>
```

## 🎯 Checklist Migration

Si vous avez du code existant avec `useToast()` :

- [ ] Remplacer `const toast = useToast()` par `const { showSuccess, showError } = useAppToast()`
- [ ] Supprimer `import { useToast } from 'primevue/usetoast'`
- [ ] Remplacer `toast.add({ severity: 'success', ... })` par `showSuccess(...)`
- [ ] Remplacer `toast.add({ severity: 'error', ... })` par `showError(...)`
- [ ] Supprimer les blocs `onMounted` qui initialisaient le toast
- [ ] Supprimer les variables `let toast: any = null`
- [ ] Remplacer `toast?.add(` par les méthodes simplifiées

## 📚 Références

- [PrimeVue Toast Documentation](https://primevue.org/toast/)
- [Nuxt 3 SSR Guide](https://nuxt.com/docs/guide/concepts/rendering)
- [Vue 3 Composables](https://vuejs.org/guide/reusability/composables.html)

---

**Note** : Le composable `useAppToast` se trouve dans `/composables/useAppToast.ts` et est auto-importé par Nuxt 3.
