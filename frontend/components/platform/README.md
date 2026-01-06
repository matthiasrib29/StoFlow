# 🧩 Composants Réutilisables Platform

> Composants génériques pour créer rapidement des pages pour les plateformes (Vinted, eBay, Etsy)

---

## 📦 Composants Disponibles

### 1. `PageHeader.vue` (Universel)
Header réutilisable pour **toutes les pages** du frontend.

```vue
<PageHeader
  title="Mon Titre"
  subtitle="Ma description"
  logo="/path/to/logo.png"
  back-to="/previous/page"
>
  <template #icon>
    <!-- Icon/logo custom -->
  </template>

  <template #actions>
    <Button label="Action 1" />
    <Button label="Action 2" />
  </template>
</PageHeader>
```

**Props:**
- `title` (string, required) - Titre de la page
- `subtitle` (string, optional) - Sous-titre
- `logo` (string, optional) - URL du logo
- `backTo` (string, optional) - Route pour le bouton retour

**Slots:**
- `icon` - Remplace le logo par un élément custom
- `actions` - Boutons/actions à droite du header

---

### 2. `PlatformNotConnected.vue`
Composant intelligent pour gérer l'état "non connecté" avec routing automatique.

```vue
<PlatformNotConnected
  platform="ebay"
  message="Message custom"
  button-label="Se connecter"
  redirect-to="/custom/route"
/>
```

**Props:**
- `platform` ('vinted' | 'ebay' | 'etsy', required)
- `message` (string, optional) - Message affiché
- `buttonLabel` (string, optional) - Label du bouton
- `redirectTo` (string, optional) - Route custom (sinon auto `/dashboard/platforms/{platform}/products`)

**Comportement:**
- Affiche automatiquement le bon nom de plateforme
- Redirige automatiquement vers la bonne page

---

### 3. `PlatformProductsPage.vue`
Template complet pour les pages "Produits" des plateformes.

```vue
<PlatformProductsPage
  platform="ebay"
  :is-connected="ebayStore.isConnected"
  :loading="loading"
  :error="error"
  :is-empty="products.length === 0"
  empty-message="Aucun produit importé"
>
  <!-- Header actions (import, sync, etc.) -->
  <template #header-actions>
    <Button label="Importer" @click="importProducts" />
    <Button label="Synchroniser" @click="syncProducts" />
  </template>

  <!-- Stats cards -->
  <template #stats>
    <div class="grid grid-cols-4 gap-4">
      <StatsCard label="Total" :value="totalProducts" />
    </div>
  </template>

  <!-- Toolbar (search, filters) -->
  <template #toolbar>
    <div class="flex items-center justify-between">
      <InputText v-model="searchQuery" placeholder="Rechercher..." />
      <Select v-model="statusFilter" :options="statusOptions" />
    </div>
  </template>

  <!-- Products table/list -->
  <template #content>
    <DataTable :value="products" />
  </template>

  <!-- Empty state actions -->
  <template #empty-actions>
    <Button label="Importer maintenant" @click="importProducts" />
  </template>
</PlatformProductsPage>
```

**Props:**
- `platform` ('vinted' | 'ebay' | 'etsy', required)
- `isConnected` (boolean, required) - État de connexion
- `loading` (boolean, optional) - État de chargement
- `error` (string | null, optional) - Message d'erreur
- `isEmpty` (boolean, optional) - Pas de produits
- `emptyMessage` (string, optional) - Message quand vide
- `logo` (string, optional) - Logo de la plateforme
- `backTo` (string, optional) - Route retour

**Slots:**
- `header-actions` - Boutons dans le header (Import, Sync, etc.)
- `stats` - Cartes de statistiques
- `toolbar` - Barre de recherche/filtres
- `content` - Contenu principal (DataTable, liste, etc.)
- `empty-actions` - Actions à afficher quand vide

**Events:**
- `@retry` - Émis quand l'utilisateur clique sur "Réessayer" (en cas d'erreur)

---

### 4. `PlatformStatisticsPage.vue`
Template pour les pages "Statistiques" des plateformes.

```vue
<PlatformStatisticsPage
  platform="vinted"
  :is-connected="vintedStore.isConnected"
  :loading="loading"
  :is-empty="!hasData"
  empty-message="Aucune donnée disponible"
>
  <!-- Graphiques et stats -->
  <template #content>
    <div class="space-y-6">
      <ChartComponent :data="chartData" />
      <StatsGrid :stats="stats" />
    </div>
  </template>
</PlatformStatisticsPage>
```

**Props:**
- `platform` ('vinted' | 'ebay' | 'etsy', required)
- `isConnected` (boolean, required)
- `loading` (boolean, optional)
- `isEmpty` (boolean, optional) - Pas de données
- `emptyMessage` (string, optional)
- `subtitle` (string, optional) - Subtitle custom
- `logo` (string, optional)
- `backTo` (string, optional)

**Slots:**
- `header-actions` - Actions dans le header
- `content` - Graphiques et statistiques

---

### 5. `PlatformSettingsPage.vue`
Template pour les pages "Paramètres" des plateformes.

```vue
<PlatformSettingsPage
  platform="ebay"
  :is-connected="ebayStore.isConnected"
  back-to="/dashboard/platforms/ebay/products"
  :columns="2"
>
  <template #content>
    <!-- Account Card -->
    <Card>
      <template #content>
        <h3>Compte eBay</h3>
        <p>Username: {{ account.username }}</p>
      </template>
    </Card>

    <!-- Sync Settings Card -->
    <Card>
      <template #content>
        <h3>Synchronisation</h3>
        <ToggleSwitch v-model="autoSync" />
      </template>
    </Card>
  </template>
</PlatformSettingsPage>
```

**Props:**
- `platform` ('vinted' | 'ebay' | 'etsy', required)
- `isConnected` (boolean, required)
- `subtitle` (string, optional)
- `logo` (string, optional)
- `backTo` (string, optional)
- `columns` (1 | 2, optional, default: 2) - Colonnes de la grille

**Slots:**
- `header-actions` - Actions dans le header
- `content` - Cards de paramètres (layout automatique en grille)

---

## 🎯 Exemples Complets

### Page Produits eBay (Exemple Complet)

```vue
<template>
  <PlatformProductsPage
    platform="ebay"
    :is-connected="ebayStore.isConnected"
    :loading="loading"
    :error="error"
    :is-empty="products.length === 0"
    @retry="fetchProducts"
  >
    <template #header-actions>
      <Button
        label="Importer"
        icon="pi pi-download"
        :loading="isImporting"
        @click="importProducts"
      />
      <Button
        label="Synchroniser"
        icon="pi pi-sync"
        :loading="isSyncing"
        @click="syncProducts"
      />
    </template>

    <template #stats>
      <div class="grid grid-cols-4 gap-4">
        <StatsCard label="Total" :value="totalProducts" />
        <StatsCard label="Actifs" :value="activeCount" />
        <StatsCard label="Brouillons" :value="draftCount" />
        <StatsCard label="Hors stock" :value="outOfStockCount" />
      </div>
    </template>

    <template #toolbar>
      <div class="flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <IconField>
            <InputIcon class="pi pi-search" />
            <InputText v-model="searchQuery" placeholder="Rechercher..." />
          </IconField>
          <Select v-model="statusFilter" :options="statusOptions" />
        </div>
      </div>
    </template>

    <template #content>
      <DataTable :value="filteredProducts" paginator :rows="20">
        <Column header="Produit" field="title" />
        <Column header="Prix" field="price" />
        <Column header="Stock" field="quantity" />
      </DataTable>
    </template>

    <template #empty-actions>
      <Button
        label="Importer depuis eBay"
        icon="pi pi-download"
        class="mt-4"
        @click="importProducts"
      />
    </template>
  </PlatformProductsPage>
</template>

<script setup lang="ts">
const ebayStore = useEbayStore()
const loading = ref(false)
const error = ref<string | null>(null)
const products = ref([])
const searchQuery = ref('')
const statusFilter = ref(null)

// ... rest of logic
</script>
```

---

## 🚀 Avantages

✅ **DRY** - Plus de duplication de code entre plateformes
✅ **Cohérence** - UI/UX identique sur toutes les plateformes
✅ **Maintenabilité** - Un seul endroit à modifier pour toutes les pages
✅ **Flexibilité** - Slots pour personnaliser chaque plateforme
✅ **Type-safe** - TypeScript avec types stricts
✅ **Intelligent** - Routing automatique, labels automatiques

---

## 📝 Notes

- Tous les composants sont **auto-importés** par Nuxt
- Les composants gèrent automatiquement les **labels de plateforme** (Vinted, eBay, Etsy)
- L'état "Not Connected" est **géré automatiquement** avec routing intelligent
- Les **slots sont optionnels** - utilisez uniquement ceux dont vous avez besoin

---

*Dernière mise à jour : 2026-01-06*
