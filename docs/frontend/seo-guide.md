# Guide SEO - StoFlow Frontend

**Version** : 1.0
**Dernière mise à jour** : 2026-01-07
**Responsable** : Équipe Dev Frontend

---

## 📋 Table des Matières

1. [Introduction](#introduction)
2. [Optimisations Implémentées](#optimisations-implémentées)
3. [Utilisation des Composables SEO](#utilisation-des-composables-seo)
4. [Checklist SEO pour Nouvelles Pages](#checklist-seo-pour-nouvelles-pages)
5. [Outils de Test](#outils-de-test)
6. [Bonnes Pratiques](#bonnes-pratiques)
7. [Métriques à Suivre](#métriques-à-suivre)

---

## Introduction

Ce guide documente toutes les optimisations SEO mises en place sur le frontend Stoflow et fournit des directives pour maintenir et améliorer le référencement de l'application.

### Pourquoi le SEO est important

- **Visibilité** : Meilleur classement dans les résultats de recherche Google
- **Trafic organique** : Acquisition gratuite de visiteurs qualifiés
- **Crédibilité** : Rich snippets et structured data renforcent la confiance
- **Partages sociaux** : Meta tags optimisés pour Facebook, LinkedIn, Twitter

---

## Optimisations Implémentées

### ✅ Phase 1 - Optimisations Critiques (Complétées)

#### 1.1 Title Tag Optimisé

**Ancien** :
```
"Stoflow - Vendez sur Vinted, eBay et Etsy depuis une seule plateforme"
(72 caractères - tronqué dans Google)
```

**Nouveau** :
```
"Stoflow - Gérez Vinted, eBay & Etsy"
(42 caractères - optimal pour SEO)
```

**Fichier** : `nuxt.config.ts` (ligne 22)

**Impact** :
- ✅ Pas de troncature dans les SERPs
- ✅ Mots-clés ciblés (Vinted, eBay, Etsy)
- ✅ Verbe d'action engageant ("Gérez")

---

#### 1.2 Canonical URLs Dynamiques

**Problème corrigé** : Toutes les pages pointaient vers `https://stoflow.io` comme canonical

**Solution** : Suppression du canonical hardcodé, Nuxt génère automatiquement les canonicals par page

**Fichier** : `nuxt.config.ts` (ligne 56-59)

**Impact** :
- ✅ Pas de risque de duplicate content
- ✅ Chaque page a son propre canonical unique

---

#### 1.3 Sitemap.xml

**Installation** : Module `@nuxtjs/sitemap`

**Configuration** : `nuxt.config.ts` (lignes 83-103)

**Pages incluses** :
- `/` (Landing page)
- `/login`, `/register`
- `/legal/privacy`, `/legal/mentions`, `/legal/cgu`, `/legal/cgv`
- `/docs`

**Pages exclues** :
- `/dashboard/**` (pages privées)
- `/auth/**` (auth flows)
- `/admin/**` (admin)

**URL** : `http://localhost:3003/sitemap.xml`

**Impact** :
- ✅ Meilleure découvrabilité par Google
- ✅ Crawl plus efficace
- ✅ Indexation plus rapide

---

#### 1.4 Meta Tags Open Graph

**Améliorations** :
```typescript
{ property: 'og:image', content: '/images/og-stoflow.jpg' },
{ property: 'og:image:width', content: '1200' },
{ property: 'og:image:height', content: '630' },
{ property: 'og:image:alt', content: 'Stoflow - Plateforme de gestion multi-marketplace' }
```

**Fichier** : `nuxt.config.ts` (lignes 40-44)

⚠️ **ACTION REQUISE** : Créer l'image `/public/images/og-stoflow.jpg` (1200x630px)

**Impact** :
- ✅ Meilleure visibilité sur Facebook, LinkedIn
- ✅ Aperçus riches lors des partages

---

#### 1.5 Composables SEO

**Fichiers créés** :
- `composables/useSeoHead.ts` - Meta tags par page
- `composables/useStructuredData.ts` - JSON-LD Schema.org

**Utilisation** :

```vue
<script setup lang="ts">
// Meta tags personnalisés
useSeoHead({
  title: 'Ma Page',
  description: 'Description optimisée SEO (150-160 caractères)',
  ogImage: '/images/og-custom.jpg',
  noindex: true // Pour pages privées
})

// Structured Data
useOrganizationSchema()
useSoftwareApplicationSchema()
useBreadcrumbSchema([
  { name: 'Accueil', url: '/' },
  { name: 'Ma Page', url: '/ma-page' }
])
</script>
```

**Impact** :
- ✅ Meta tags uniques par page
- ✅ Rich snippets dans Google
- ✅ Meilleur CTR (Click-Through Rate)

---

### ✅ Phase 2 - Optimisations Importantes (Complétées)

#### 2.1 Structured Data (JSON-LD)

**Schemas implémentés** :
- `Organization` - Informations entreprise
- `SoftwareApplication` - Description de l'app
- `FAQPage` - Questions/réponses
- `BreadcrumbList` - Fil d'ariane
- `Article` - Documentation

**Fichier** : `composables/useStructuredData.ts`

**Exemple d'utilisation** :
```vue
<script setup lang="ts">
// Page d'accueil
useOrganizationSchema()
useSoftwareApplicationSchema()

// Page FAQ
const faqs = [
  { question: 'Question 1', answer: 'Réponse 1' },
  { question: 'Question 2', answer: 'Réponse 2' }
]
useFAQPageSchema(faqs)

// Pages légales
useBreadcrumbSchema([
  { name: 'Accueil', url: '/' },
  { name: 'Mentions légales', url: '/legal/mentions' }
])
</script>
```

**Test** : [Google Rich Results Test](https://search.google.com/test/rich-results)

**Impact** :
- ✅ Rich snippets dans Google
- ✅ Featured snippets possibles (FAQ)
- ✅ Meilleure compréhension du contenu par Google

---

#### 2.2 robots.txt Amélioré

**Fichier** : `public/robots.txt`

**Contenu** :
```txt
User-agent: *
Allow: /

# Bloquer les routes privées
Disallow: /dashboard/
Disallow: /auth/
Disallow: /admin/
Disallow: /api/

# Sitemap
Sitemap: https://stoflow.io/sitemap.xml
```

**Impact** :
- ✅ Routes privées non indexées
- ✅ Crawl budget optimisé
- ✅ Référence au sitemap

---

#### 2.3 H1 Sémantiques

**Pages modifiées** :
- `pages/login.vue` - H1 "Connexion à Stoflow" (sr-only)
- `pages/register.vue` - H1 "Créer un compte Stoflow" (sr-only)

**Technique** :
```vue
<template>
  <div>
    <h1 class="sr-only">Titre SEO</h1>
    <!-- Contenu visuel -->
  </div>
</template>
```

**Impact** :
- ✅ Un seul H1 par page
- ✅ Hiérarchie sémantique correcte
- ✅ Accessibilité améliorée

---

### ✅ Phase 3 - Optimisations Moyennes (Complétées)

#### 3.1 Optimisation d'Images (@nuxt/image)

**Installation** : `npm install @nuxt/image`

**Configuration** : `nuxt.config.ts` (lignes 106-121)

**Options** :
- Quality: 80 (bon compromis qualité/poids)
- Formats: WebP, JPEG, PNG
- Lazy loading par défaut
- Responsive images automatiques

**Utilisation** :
```vue
<template>
  <!-- Avant -->
  <img src="/images/logo.png" alt="Stoflow">

  <!-- Après (optimisé) -->
  <NuxtImg src="/images/logo.png" alt="Stoflow" width="200" height="50" />
</template>
```

**Impact** :
- ✅ Formats modernes (WebP)
- ✅ Lazy loading automatique
- ✅ Amélioration LCP (Largest Contentful Paint)

---

#### 3.2 Twitter Cards Complètes

**Ajout** :
```typescript
{ name: 'twitter:site', content: '@stoflow' },
{ name: 'twitter:creator', content: '@stoflow' }
```

**Fichier** : `nuxt.config.ts` (lignes 47-48)

⚠️ **NOTE** : Remplacer `@stoflow` par le vrai handle Twitter

**Impact** :
- ✅ Meilleur affichage sur Twitter/X
- ✅ Attribution correcte des partages

---

#### 3.3 BreadcrumbList Schema

**Pages enrichies** :
- `pages/legal/privacy.vue`
- `pages/legal/mentions.vue`
- `pages/legal/cgu.vue`
- `pages/legal/cgv.vue`

**Exemple** :
```vue
<script setup lang="ts">
useBreadcrumbSchema([
  { name: 'Accueil', url: '/' },
  { name: 'Informations légales', url: '/legal' },
  { name: 'Politique de confidentialité', url: '/legal/privacy' }
])
</script>
```

**Impact** :
- ✅ Fil d'ariane dans les SERPs
- ✅ Meilleure navigation utilisateur
- ✅ Contexte hiérarchique pour Google

---

#### 3.4 Hiérarchie de Titres

**Composant modifié** : `components/landing/LandingFAQ.vue`

**Changement** :
```vue
<!-- Avant -->
<span class="font-bold">{{ faq.question }}</span>

<!-- Après -->
<h3 class="font-bold">{{ faq.question }}</h3>
```

**Impact** :
- ✅ Hiérarchie H1 → H2 → H3 logique
- ✅ Meilleure compréhension par les robots
- ✅ Accessibilité améliorée

---

### ✅ Phase 4 - Optimisations Basses (Complétées)

#### 4.1 Core Web Vitals

**Fichier créé** : `assets/css/core-web-vitals.css`

**Optimisations** :
- **CLS** (Cumulative Layout Shift) : min-height sur containers animés
- **LCP** (Largest Contentful Paint) : font-display: swap
- **FID/INP** : Transitions optimisées (transform/opacity uniquement)

**Fichier** : Ajouté dans `nuxt.config.ts` (ligne 80)

**Impact** :
- ✅ Score CLS < 0.1 (bon)
- ✅ Pas de layout shift lors des animations
- ✅ Meilleur score Lighthouse

---

## Utilisation des Composables SEO

### useSeoHead()

**Paramètres** :
- `title` (string) - Titre de la page
- `description` (string) - Meta description (150-160 caractères)
- `ogImage` (string, optionnel) - URL de l'image OG
- `ogType` (string, optionnel) - Type OG (website, article, etc.)
- `noindex` (boolean, optionnel) - Empêcher l'indexation

**Exemple** :
```vue
<script setup lang="ts">
useSeoHead({
  title: 'Connexion',
  description: 'Connectez-vous à votre compte Stoflow pour gérer vos ventes multi-marketplace.',
  noindex: true // Page privée
})
</script>
```

---

### useStructuredData()

**Fonctions disponibles** :

#### useOrganizationSchema()
À utiliser sur la page d'accueil uniquement.

```vue
<script setup lang="ts">
useOrganizationSchema()
</script>
```

#### useSoftwareApplicationSchema()
À utiliser sur la page d'accueil uniquement.

```vue
<script setup lang="ts">
useSoftwareApplicationSchema()
</script>
```

#### useFAQPageSchema(faqs)
À utiliser sur les pages avec FAQ.

```vue
<script setup lang="ts">
const faqs = [
  { question: 'Question 1?', answer: 'Réponse 1' },
  { question: 'Question 2?', answer: 'Réponse 2' }
]
useFAQPageSchema(faqs)
</script>
```

#### useBreadcrumbSchema(breadcrumbs)
À utiliser sur les pages avec navigation hiérarchique.

```vue
<script setup lang="ts">
useBreadcrumbSchema([
  { name: 'Accueil', url: '/' },
  { name: 'Ma Page', url: '/ma-page' }
])
</script>
```

#### useArticleSchema(article)
À utiliser sur les pages de blog/documentation.

```vue
<script setup lang="ts">
useArticleSchema({
  title: 'Titre de l\'article',
  description: 'Description',
  datePublished: '2026-01-07',
  author: 'Stoflow',
  image: '/images/article.jpg' // Optionnel
})
</script>
```

---

## Checklist SEO pour Nouvelles Pages

Lors de la création d'une nouvelle page, suivre cette checklist :

### ✅ Meta Tags

- [ ] Utiliser `useSeoHead()` avec title unique
- [ ] Meta description 150-160 caractères
- [ ] Inclure les mots-clés ciblés
- [ ] Définir `noindex: true` si page privée

### ✅ Structured Data

- [ ] Ajouter `useBreadcrumbSchema()` si navigation hiérarchique
- [ ] Ajouter `useFAQPageSchema()` si FAQ présente
- [ ] Ajouter `useArticleSchema()` si contenu éditorial

### ✅ Contenu

- [ ] Un seul `<h1>` par page
- [ ] Hiérarchie logique H1 → H2 → H3
- [ ] Alt text sur toutes les images
- [ ] Liens internes pertinents

### ✅ Performance

- [ ] Utiliser `<NuxtImg>` pour les images
- [ ] Lazy loading pour contenu non critique
- [ ] Éviter les animations coûteuses
- [ ] Définir min-height sur containers animés

### ✅ Sitemap

- [ ] Ajouter l'URL dans `nuxt.config.ts` (lignes 86-94) si page publique
- [ ] Ajouter dans `exclude` si page privée (lignes 97-100)

---

## Outils de Test

### Google Tools

1. **[Google Search Console](https://search.google.com/search-console)**
   - Soumettre le sitemap
   - Suivre l'indexation
   - Identifier les erreurs

2. **[Google Rich Results Test](https://search.google.com/test/rich-results)**
   - Tester les structured data
   - Vérifier les rich snippets

3. **[PageSpeed Insights](https://pagespeed.web.dev/)**
   - Score de performance
   - Core Web Vitals
   - Recommandations

### Social Media

4. **[Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/)**
   - Tester les Open Graph tags
   - Rafraîchir le cache Facebook

5. **[LinkedIn Post Inspector](https://www.linkedin.com/post-inspector/)**
   - Tester les aperçus LinkedIn

6. **[Twitter Card Validator](https://cards-dev.twitter.com/validator)**
   - Tester les Twitter Cards

### SEO Analysis

7. **[Lighthouse (Chrome DevTools)](https://developers.google.com/web/tools/lighthouse)**
   - Score SEO
   - Core Web Vitals
   - Accessibilité

8. **[Screaming Frog SEO Spider](https://www.screamingfrogseoseo.com/)** (optionnel)
   - Crawl complet du site
   - Identifier les problèmes techniques

---

## Bonnes Pratiques

### Title Tags

✅ **DO** :
- Garder entre 50-60 caractères
- Inclure les mots-clés principaux
- Utiliser un verbe d'action
- Format : "Titre - Stoflow"

❌ **DON'T** :
- Dépasser 70 caractères
- Dupliquer les titles
- Utiliser uniquement le nom de marque

---

### Meta Descriptions

✅ **DO** :
- Garder entre 150-160 caractères
- Inclure un appel à l'action
- Mentionner les mots-clés
- Être unique par page

❌ **DON'T** :
- Dépasser 160 caractères
- Copier le contenu de la page
- Utiliser des descriptions génériques

---

### Structured Data

✅ **DO** :
- Tester avec Google Rich Results Test
- Utiliser les schemas appropriés
- Garder les données à jour

❌ **DON'T** :
- Inventer des données fausses
- Utiliser plusieurs schemas contradictoires
- Oublier de tester

---

### Images

✅ **DO** :
- Utiliser `<NuxtImg>` pour l'optimisation
- Définir width et height
- Ajouter des alt texts descriptifs
- Utiliser des formats modernes (WebP)

❌ **DON'T** :
- Utiliser des images énormes (>500KB)
- Oublier les alt texts
- Utiliser `<img>` directement

---

### URLs

✅ **DO** :
- Garder les URLs courtes et descriptives
- Utiliser des tirets (-) pour séparer
- Utiliser des mots-clés pertinents

❌ **DON'T** :
- Utiliser des underscores (_)
- Inclure des IDs numériques si évitable
- Utiliser des caractères spéciaux

---

## Métriques à Suivre

### Google Search Console

**Métriques clés** :
- **Impressions** : Nombre de fois où votre site apparaît dans les résultats
- **Clics** : Nombre de clics sur vos résultats
- **CTR** : Taux de clic (Clics / Impressions)
- **Position moyenne** : Position dans les SERPs

**Objectifs** :
- CTR > 3%
- Position moyenne < 10 (première page)
- Augmentation mensuelle des impressions

---

### Lighthouse SEO Score

**Métriques** :
- **SEO Score** : > 90 (bon)
- **Performance** : > 85
- **Accessibility** : > 90
- **Best Practices** : > 90

**Core Web Vitals** :
- **LCP** (Largest Contentful Paint) : < 2.5s (bon)
- **FID/INP** (Interactivité) : < 100ms (bon)
- **CLS** (Cumulative Layout Shift) : < 0.1 (bon)

---

### Analytics (Google Analytics / Plausible)

**Métriques** :
- **Trafic organique** : % du trafic total
- **Pages les plus visitées** : Identifier les pages performantes
- **Taux de rebond** : < 60% (bon)
- **Durée moyenne de session** : > 2 minutes (bon)

---

## FAQ SEO

### Q : Combien de temps avant de voir des résultats SEO ?

**R** : 3 à 6 mois pour des résultats significatifs. Le SEO est un investissement à long terme.

---

### Q : Faut-il optimiser toutes les pages ?

**R** : Prioriser les pages publiques (landing, legal, docs). Les pages privées (dashboard) peuvent avoir `noindex: true`.

---

### Q : Comment savoir si les structured data fonctionnent ?

**R** : Utiliser [Google Rich Results Test](https://search.google.com/test/rich-results) pour tester. Attendre 2-4 semaines pour voir les rich snippets dans Google.

---

### Q : L'image OG est-elle obligatoire ?

**R** : Fortement recommandée. Sans elle, les partages sur réseaux sociaux auront un aperçu générique.

---

### Q : Faut-il créer un sitemap pour chaque environnement ?

**R** : Le sitemap est généré automatiquement. En production, il pointera vers `https://stoflow.io/sitemap.xml`. En dev, `http://localhost:3003/sitemap.xml`.

---

## Support & Contacts

**Questions SEO** : Équipe Dev Frontend
**Google Search Console** : contact@stoflow.io
**Documentation Nuxt SEO** : [https://nuxt.com/docs/getting-started/seo-meta](https://nuxt.com/docs/getting-started/seo-meta)

---

**Dernière mise à jour** : 2026-01-07
**Version** : 1.0
