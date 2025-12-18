# Guide de Style - Stoflow Frontend

## 📦 Librairies Installées

### @formkit/auto-animate
Animations fluides automatiques pour les listes et éléments dynamiques.

**Usage :**
```vue
<template>
  <div v-auto-animate>
    <div v-for="item in items" :key="item.id">
      {{ item.name }}
    </div>
  </div>
</template>
```

### tailwindcss-primeui
Plugin Tailwind pour meilleure intégration avec PrimeVue.

**Activé dans :** `tailwind.config.js`

---

## 🎨 Classes CSS Réutilisables

### Border Radius Standardisé

Utilisez les classes Tailwind plutôt que les classes custom :

- ✅ **Recommandé :** `rounded-2xl` (16px)
- ✅ **Alternative :** `rounded-3xl` (24px)
- ⚠️  **Legacy (supporté) :** `modern-rounded` → équivalent à `rounded-2xl`

### Gradients Plateformes

Classes réutilisables pour chaque plateforme :

```css
.gradient-vinted    /* Cyan gradient */
.gradient-ebay      /* Blue gradient */
.gradient-etsy      /* Orange gradient */
.gradient-facebook  /* FB Blue gradient */
.gradient-primary   /* Yellow gradient */
```

**Usage dans stat cards :**
```vue
<div class="stat-card relative p-6 rounded-2xl stat-card-gradient vinted">
  <!-- Content -->
</div>
```

Les classes disponibles :
- `stat-card-gradient vinted`
- `stat-card-gradient ebay`
- `stat-card-gradient etsy`
- `stat-card-gradient facebook`
- `stat-card-gradient primary`

### Focus States

Focus visible automatique sur tous les composants PrimeVue :
- Outline jaune 2px
- Offset 2px pour clarté

**Automatiquement appliqué à :**
- `.p-button:focus-visible`
- `.p-inputtext:focus-visible`
- `.p-dropdown:focus-visible`

### Disabled States

Styles disabled cohérents :
- Opacity 0.5
- Cursor `not-allowed`

**Automatiquement appliqué aux composants PrimeVue désactivés**

### Ripple Effect

Effet ripple automatique sur tous les boutons PrimeVue au clic.

### Skeleton Loader

Pour les états de chargement :

```vue
<div class="skeleton h-20 w-full"></div>
```

---

## 📐 Standards de Spacing

### Pages
```vue
<div class="p-8">
  <!-- Page content -->
</div>
```

### Sections Header
```vue
<div class="mb-8">
  <h1 class="text-3xl font-bold text-secondary-900 mb-1">Titre</h1>
  <p class="text-gray-600">Sous-titre descriptif</p>
</div>
```

### Cards
```vue
<Card class="shadow-sm rounded-2xl border border-gray-100">
  <template #content>
    <div class="space-y-6">
      <!-- Content -->
    </div>
  </template>
</Card>
```

---

## 🎨 Palette de Couleurs

### Couleurs Principales

**Primaire (Jaune) :**
- `primary-400` : #facc15 (Principal)
- `primary-500` : #eab308 (Hover)
- `primary-100` : #fef9c3 (Background clair)

**Secondaire (Noir) :**
- `secondary-900` : #1a1a1a (Textes)
- `secondary-800` : #5a5a5a
- `secondary-50` : #f8f8f8 (Background)

**Neutre (Gris) :**
- `gray-50` à `gray-900`
- Utilisé pour bordures, textes secondaires

### Couleurs Sémantiques

**Boutons :**
```vue
<!-- Primary CTA -->
<Button class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold" />

<!-- Secondary -->
<Button class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0" />

<!-- Danger -->
<Button class="bg-secondary-500 hover:bg-secondary-600 text-white border-0" />
```

---

## ⚡ Bonnes Pratiques

### ✅ À Faire

1. **Border-radius cohérent :**
   ```vue
   <Card class="rounded-2xl">
   ```

2. **Spacing systématique :**
   ```vue
   <div class="space-y-6">
     <div>Item 1</div>
     <div>Item 2</div>
   </div>
   ```

3. **Hover effects :**
   ```vue
   <div class="hover:shadow-lg transition-all duration-300">
   ```

4. **Focus visible :**
   ```vue
   <button class="focus:ring-2 focus:ring-primary-400">
   ```

### ❌ À Éviter

1. **Border-radius variables :**
   ```vue
   <!-- ❌ -->
   <div class="rounded-lg">  <!-- 12px -->
   <div class="rounded-xl">  <!-- 14px -->

   <!-- ✅ -->
   <div class="rounded-2xl"> <!-- 16px - standard -->
   ```

2. **Gradients inline :**
   ```vue
   <!-- ❌ -->
   <div style="background: linear-gradient(...)">

   <!-- ✅ -->
   <div class="gradient-vinted">
   ```

3. **Spacing incohérent :**
   ```vue
   <!-- ❌ -->
   <h1 class="text-3xl font-bold">Titre</h1>
   <p>Description</p>

   <!-- ✅ -->
   <h1 class="text-3xl font-bold text-secondary-900 mb-1">Titre</h1>
   <p class="text-gray-600">Description</p>
   ```

---

## 🚀 Animations avec Auto-Animate

### Lists et Grids

```vue
<script setup>
const products = ref([...])
</script>

<template>
  <div v-auto-animate class="grid grid-cols-1 md:grid-cols-3 gap-6">
    <Card v-for="product in products" :key="product.id">
      <!-- Product card -->
    </Card>
  </div>
</template>
```

### Conditional Rendering

```vue
<template>
  <div v-auto-animate>
    <Alert v-if="showAlert" />
    <Form v-else />
  </div>
</template>
```

---

## 📋 Checklist Avant Commit

- [ ] Border-radius cohérent (`rounded-2xl`)
- [ ] Spacing des titres avec `mb-1`
- [ ] Classes Tailwind utilisées plutôt que CSS inline
- [ ] Gradients plateformes utilisent les classes réutilisables
- [ ] Hover states présents
- [ ] Focus states accessibles
- [ ] Auto-animate sur les listes dynamiques

---

**Dernière mise à jour :** 6 décembre 2025
**Version :** 1.0
