# Rapport d'Audit - SEO

**Projet**: StoFlow Frontend (Nuxt.js)
**Date d'analyse**: 2026-01-27
**Scope**: `frontend/`

---

## Résumé Exécutif

Le frontend dispose d'une bonne base SEO (SSR, meta tags, structured data) mais présente des lacunes critiques sur les images, les canonical URLs, et la couverture des meta tags sur les pages.

---

## 1. Meta Tags

### Points Positifs
- `useSeoHead()` composable bien structuré avec title, description, OG tags
- `useSeoMeta()` pour les pages publiques
- `<html lang="fr">` configuré

### Problèmes Critiques

#### 1.1 Canonical URL manquante (CRITIQUE)
**Fichier**: `frontend/composables/useSeoHead.ts`
Aucune canonical URL n'est définie. Risque de duplicate content.

**Fix**: Ajouter `link: [{ rel: 'canonical', href: canonicalUrl }]`

#### 1.2 og:url manquante (CRITIQUE)
Open Graph URL absente → aperçus réseaux sociaux incorrects.

#### 1.3 Image Open Graph manquante (CRITIQUE)
Pas de `og:image` configurée. Fichier `/public/images/og-stoflow.jpg` (1200x630px) nécessaire.

#### 1.4 Meta tags absentes sur 53/59 pages (HAUTE)
Seulement 6 pages ont des meta tags SEO (index, login, register, legal pages). Toutes les pages dashboard devraient avoir `noindex`.

#### 1.5 Meta description trop longue (MOYENNE)
182 caractères au lieu de 150-160 recommandés dans `nuxt.config.ts`.

---

## 2. Structured Data (Schema.org)

### Points Positifs
- Organization Schema ✅
- SoftwareApplication Schema ✅
- 5 composables réutilisables (FAQ, Breadcrumb, Article)

### Améliorations

#### 2.1 FAQ Schema manquant sur landing page (HAUTE)
Le composant `LandingFAQ.vue` contient 8 Q&A mais pas de FAQPage Schema → rich snippets manqués, -20-30% CTR.

#### 2.2 BreadcrumbList Schema manquant (MOYENNE)
Breadcrumbs visuels présents mais sans structured data.

#### 2.3 AggregateRating hardcodé (BASSE)
4.8 étoiles / 127 avis hardcodés → risque de pénalité Google pour "fake rating".

---

## 3. Images

### Problèmes Critiques

#### 3.1 NuxtImg jamais utilisé (CRITIQUE)
Module @nuxt/image installé et configuré, mais **0 occurrences** de `<NuxtImg>`. Toutes les images utilisent `<img>` standard.

**Impact**: Pas de WebP/AVIF, pas de responsive images, pas de lazy loading → pénalité LCP, -20-30 points PageSpeed.

**Fichiers prioritaires**: ProductCard.vue, ProductsDataTable.vue, LandingPlatforms.vue (~30-40 occurrences)

#### 3.2 Lazy loading absent (CRITIQUE)
0 occurrences de `loading="lazy"`. Toutes les images chargées immédiatement.

### Points Positifs
- Alt text présent sur la majorité des images (30 occurrences)

---

## 4. URL Structure

### Points Positifs
- URLs propres avec slugs ✅
- Hiérarchie logique ✅
- Tout en minuscules ✅
- Trailing slashes gérés ✅

---

## 5. Sitemap & Robots.txt

### robots.txt ✅
Configuration correcte : Allow /, Disallow dashboard/auth/admin/api.

**Bug mineur**: Sitemap pointe vers `stoflow.io` au lieu de `www.stoflow.io`.

### Sitemap
Configuré dans `nuxt.config.ts` mais pas de fichier généré dans `/public/`. Nécessite `npm run generate`.

---

## 6. SSR/SSG Configuration

### Points Positifs
- SSR activé par défaut ✅
- Meta tags rendus côté serveur ✅

### Recommandation
Hybrid rendering : SSG pour pages publiques, SSR pour dashboard.

```typescript
routeRules: {
  '/': { prerender: true },
  '/legal/**': { prerender: true },
  '/dashboard/**': { ssr: true },
}
```

---

## 7. Core Web Vitals

### Points Positifs
- CSS dédié `core-web-vitals.css` ✅
- Google Fonts avec `display:swap` ✅
- Preconnect Google Fonts ✅
- `prefers-reduced-motion` respecté ✅

### Problèmes
- Lazy loading absent (voir section 3)
- Images non optimisées (voir section 3)
- PrimeVue importé globalement (bundle size)

---

## 8. Accessibilité impactant le SEO

### Points Positifs
- `lang="fr"` ✅
- `sr-only` sur H1 cachés ✅
- Bon contraste sur couleurs principales ✅

### Améliorations
- Skip-to-content link manquant
- Focus visible insuffisant sur éléments custom

---

## Actions Prioritaires

### Critiques (immédiatement)
1. Créer image Open Graph (1200x630px)
2. Ajouter canonical URLs et og:url
3. Remplacer `<img>` par `<NuxtImg>` (~30-40 occurrences)
4. Ajouter lazy loading
5. Ajouter meta tags sur les 53 pages manquantes

### Hautes (2 semaines)
6. Ajouter FAQ Schema sur page d'accueil
7. Générer le sitemap en production
8. Ajouter BreadcrumbList Schema
9. Corriger URL sitemap dans robots.txt

### Moyennes (1 mois)
10. Raccourcir meta description
11. Skip-to-content link
12. Hybrid rendering (SSG public + SSR dashboard)
13. Retirer/rendre dynamique AggregateRating

---

## Outils de Validation

- [Google Rich Results Test](https://search.google.com/test/rich-results)
- [PageSpeed Insights](https://pagespeed.web.dev/)
- [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/)
- Lighthouse (Chrome DevTools)

---

**Rapport généré le**: 2026-01-27
**Analyste**: Claude Code (SEO Optimizer)
