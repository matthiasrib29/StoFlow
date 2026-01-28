# Rapport d'Audit - Frontend Design & UI/UX

**Projet**: StoFlow Frontend (Nuxt.js + Tailwind CSS + PrimeVue)
**Date d'analyse**: 2026-01-27
**Scope**: `frontend/`

---

## Score Global : 7.5/10

| Domaine | Score | État |
|---------|-------|------|
| Design system | 9/10 | ✅ |
| Consistance visuelle | 7/10 | ⚠️ |
| Réutilisabilité | 6/10 | ⚠️ |
| Accessibilité | 4/10 | ❌ |
| Responsive | 8/10 | ✅ |
| Animations | 8/10 | ✅ |
| Performance | 7/10 | ⚠️ |

---

## Points Forts

1. **Identité visuelle forte** : Palette jaune/noir distinctive et cohérente
2. **Design system solide** : Tokens CSS complets (270 lignes), 8 palettes de couleurs
3. **PrimeVue bien intégré** : Overrides cohérents avec le design system
4. **Animations riches** : Micro-interactions, stagger fade-in, form validation
5. **Typographie professionnelle** : Plus Jakarta Sans, IBM Plex Sans, JetBrains Mono

---

## 1. Composants Réutilisables - Duplication

### P1.1 - Boutons Non Standardisés (Impact: Élevé)

40+ fichiers utilisent `<Button>` avec classes inline incohérentes au lieu d'un composant `UiButton` centralisé.

```vue
<!-- Patterns inconsistants détectés -->
<Button class="bg-primary-400 hover:bg-primary-500 text-secondary-900 font-semibold rounded-xl px-6 py-3" />
<Button severity="secondary" class="font-semibold rounded-xl !bg-gray-100" />
```

**Recommandation**: Créer `components/ui/UiButton.vue` avec variants (primary, secondary, danger, ghost) et sizes (sm, md, lg).

### P1.2 - Stat Cards Dupliqués (Impact: Moyen)

`StatCard.vue` existe et est bien conçu, mais `dashboard/index.vue` réimplémente les stat cards en inline.

### P1.3 - Badges Inconsistants (Impact: Moyen)

Classes design system définies (`badge-success`, `badge-warning`, etc.) mais les composants utilisent des classes inline au lieu des badges standardisés.

**Recommandation**: Créer `UiBadge.vue` avec variants et statuses.

---

## 2. Tailwind Usage

### P2.1 - Inline Styles dans Components (Impact: Moyen)

15 fichiers avec `style="background:..."` au lieu de classes Tailwind.

**Fichiers**: `FilterBar.vue`, `ProductsDataTable.vue`, `FormProgressBar.vue`

### P2.2 - Couleurs Hardcodées (Impact: Faible)

`modern-dashboard.css` contient des hex hardcodés (`#facc15`) au lieu de `var(--color-primary-400)`.

---

## 3. Theme Configuration

### Points Forts
- Design tokens complets : couleurs, typographie, spacing, shadows, z-index, transitions ✅
- 8 palettes de couleurs (primary, secondary, success, warning, error, info, platforms, UI) ✅

### Problèmes
- Variables RGB manquantes pour usage avec opacity
- Tokens définis mais ignorés (~40% d'utilisation)

---

## 4. Responsive Design

### Points Forts
- Breakpoints Tailwind standard ✅
- Mobile-first approach ✅
- `grid-cols-1 sm:grid-cols-2 md:grid-cols-3` ✅

### Problèmes
- Spacing incohérent mobile vs desktop (ratios différents)
- Font sizes avec seulement 2 breakpoints (manque `sm`)

---

## 5. Border Radius Inconsistant

| Classe | Usages | Note |
|--------|--------|------|
| `rounded-lg` | 232 | ✅ |
| `rounded-xl` | 180 | ✅ |
| `rounded-2xl` | 15 | ⚠️ Incohérent |

**Recommandation**: Standardiser → `rounded-xl` pour cards, `rounded-lg` pour boutons/inputs.

---

## 6. UI/UX Anti-Patterns

### P6.1 - Actions Hover-Only (Impact: Élevé)

**Fichier**: `components/products/ProductCard.vue:33-47`

Les boutons d'action (éditer, archiver) sont dans un overlay `group-hover:opacity-100`. **Inaccessibles sur mobile** (pas de hover).

**Fix**: Toujours visibles sur mobile (`opacity-100 sm:opacity-0 sm:group-hover:opacity-100`) ou menu dropdown.

### P6.2 - Checkbox Sans Label Accessible

**Fichier**: `ProductCard.vue:23-31`

Checkbox custom sans `role="checkbox"`, `aria-checked`, ni `aria-label`.

### P6.3 - Boutons Sans Feedback Loading

Aucun état loading standardisé sur les boutons d'action.

---

## 7. Accessibilité (WCAG 2.1)

### Statistiques Alarmantes
- Composants avec ARIA : **2/94 (2.1%)** ❌
- Focus states sur composants custom : **0/94** ❌
- Contraste WCAG AA : 85% ✅

### Problèmes Critiques

**ARIA manquants**:
- Modals : pas de `role="dialog"`, `aria-modal="true"`
- Dropdowns : pas de `aria-expanded`, `aria-haspopup`
- Tabs : pas de `role="tablist"`, `aria-selected`

**Focus states** : Aucun composant custom n'a `focus:ring-2`

**Contraste** : `text-gray-500` sur blanc = 3.6:1 ❌ (sous WCAG AA 4.5:1)

---

## 8. Loading States & Error States

### Points Forts
- Skeleton loaders existants (`SkeletonCard.vue`) ✅
- Animation skeleton en CSS ✅

### Problèmes
- Loading states inconsistants (DataTable sans skeleton)
- Error states non affichés à l'utilisateur (loggés mais pas rendus)

---

## 9. Animations

### Points Forts
- Système riche (stagger, shake, ripple, glow, bounce, drag) ✅
- `prefers-reduced-motion` respecté ✅

### Problèmes
- 4 animations définies mais jamais utilisées (scroll-reveal, parallax, card-flip, gradient-shift)
- Page transitions désactivées (`nuxt.config.ts:18-20`)

---

## Recommandations Prioritaires

### Priorité 1 - Accessibilité (2-3 jours)
1. Ajouter ARIA sur modals, dropdowns, tabs
2. Focus states sur tous les éléments interactifs
3. Corriger contraste (`text-gray-500` → `text-gray-600`)

### Priorité 2 - Composants Réutilisables (3-4 jours)
4. Créer `UiButton.vue` (variants + sizes + loading)
5. Créer `UiBadge.vue` (variants + statuses)
6. Créer `UiCard.vue` (variants + hover + shadow)

### Priorité 3 - Consistance Styling (1-2 jours)
7. Standardiser border-radius
8. Remplacer inline styles par Tailwind
9. Ajouter variables CSS RGB

### Priorité 4 - Mobile UX (2 jours)
10. ProductCard actions visibles sur mobile
11. Standardiser ratios spacing mobile/desktop
12. Touch targets minimum 44x44px

---

## Fichiers Critiques à Refactoriser

1. `components/products/ProductCard.vue` - Hover actions, badges, checkbox
2. `pages/dashboard/index.vue` - Stat cards dupliqués
3. `components/layout/DashboardSidebar.vue` - ARIA + keyboard nav
4. `components/products/FilterBar.vue` - Inline styles
5. `components/products/ProductsDataTable.vue` - Inline styles
6. `assets/css/modern-dashboard.css` - Hardcoded hex

---

**Rapport généré le**: 2026-01-27
**Analyste**: Claude Code (Frontend UI/UX Architect)
