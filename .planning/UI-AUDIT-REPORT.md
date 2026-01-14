# StoFlow UI Audit Report

**Date:** 2026-01-14
**Auditor:** Claude Code (Playwright-based analysis)
**Pages Analyzed:** 10 key pages

---

## Executive Summary

L'audit UI de StoFlow révèle une application fonctionnelle avec une identité visuelle claire (couleur primaire jaune/or), mais plusieurs incohérences de design qui impactent la perception professionnelle et l'expérience utilisateur. Les problèmes principaux concernent la typographie, les badges de statut, et l'espacement des composants.

**Score Global:** 6.5/10 (Fonctionnel mais amélioration nécessaire)

---

## Pages Auditées

| # | Page | URL | Screenshot |
|---|------|-----|------------|
| 1 | Dashboard | `/dashboard` | audit-01-dashboard.png |
| 2 | Products List | `/dashboard/products` | audit-02-products-list.png |
| 3 | Product Create | `/dashboard/products/create` | audit-03-product-create.png |
| 4 | Platforms | `/dashboard/platforms` | audit-04-platforms.png |
| 5 | Vinted Products | `/dashboard/platforms/vinted/products` | audit-05-vinted-products.png |
| 6 | Settings | `/dashboard/settings` | audit-06-settings.png |
| 7 | Subscription | `/dashboard/subscription` | audit-07-subscription.png |
| 8 | Error 404 | N/A | audit-08-error-404.png |
| 9 | Login | `/login` | audit-09-login.png |
| 10 | Register | `/register` | audit-10-register.png |

---

## Issues Identified

### CRITICAL - Typography

| Issue | Location | Description | Impact |
|-------|----------|-------------|--------|
| **TYP-01** | Global | Police body text non appliquée uniformément | Les fonts configurées (Plus Jakarta Sans, IBM Plex Sans) ne semblent pas utilisées partout |
| **TYP-02** | Dashboard | Texte "Bienvenue" trop léger (gray-400) | Faible lisibilité, contraste insuffisant |
| **TYP-03** | Tables | Poids de font variable dans les en-têtes | Incohérence visuelle entre les colonnes |
| **TYP-04** | Sidebar | Labels de menu avec poids inconsistant | Certains items semblent plus "bold" que d'autres |

### HIGH - Color & Contrast

| Issue | Location | Description | Impact |
|-------|----------|-------------|--------|
| **COL-01** | Badges de statut | Couleurs incohérentes pour états similaires | "Connecté" = vert, "Publié" = vert différent, "Actif" = vert encore différent |
| **COL-02** | Bouton Annuler | Bouton "Annuler" en jaune/orange (product create) | Conflit avec la convention (annuler = gris/outline) |
| **COL-03** | Badge "Déconnecté" | Gris peu visible vs fond blanc | Contraste faible, difficile à distinguer |
| **COL-04** | Stat cards | Icônes avec fond jaune inconsistant | Certaines avec fond rond, d'autres sans |
| **COL-05** | Links | Liens "Gérer" et "S'inscrire" en couleurs différentes | Jaune vs bleu selon le contexte |

### MEDIUM - Spacing & Layout

| Issue | Location | Description | Impact |
|-------|----------|-------------|--------|
| **SPC-01** | Platform cards | Espacement inégal entre les cartes | 2 cartes sur une ligne, 1 seule sur la suivante |
| **SPC-02** | Tables | Padding des cellules variable | Colonnes "Actions" plus serrées |
| **SPC-03** | Forms | Gap entre labels et inputs variable | 4px sur certains, 8px sur d'autres |
| **SPC-04** | Sidebar | Padding des sous-menus incohérent | Indentation variable |

### MEDIUM - Component Inconsistencies

| Issue | Location | Description | Impact |
|-------|----------|-------------|--------|
| **CMP-01** | Badges | Mix de styles (pill vs rectangle) | "Connecté" = pill, "Inactif" = rectangle |
| **CMP-02** | Buttons | Boutons primaires avec styles variables | Certains avec icône, d'autres sans |
| **CMP-03** | Cards | Border-radius variable | 12px vs 16px selon les cards |
| **CMP-04** | Inputs | Hauteur d'input variable | Select vs TextInput ont des hauteurs différentes |
| **CMP-05** | Icons | Taille d'icônes variable dans la sidebar | 18px vs 20px selon les items |

### LOW - Visual Polish

| Issue | Location | Description | Impact |
|-------|----------|-------------|--------|
| **VIS-01** | Empty states | État vide de la table produits basique | Manque d'illustration, peu engageant |
| **VIS-02** | 404 Page | Page d'erreur très basique | Pas de branding, pas d'illustration |
| **VIS-03** | Loading states | Spinner simple sans personnalisation | Pas de skeleton loading |
| **VIS-04** | Hover effects | Effets hover incohérents | Certaines cards ont un lift, d'autres non |

---

## Positive Observations

| Aspect | Description |
|--------|-------------|
| **Brand Color** | Couleur primaire jaune (#facc15) bien utilisée et reconnaissable |
| **Card Design** | Style de cards cohérent avec ombres subtiles |
| **Sidebar Structure** | Navigation bien organisée avec sous-menus |
| **Form Layout** | Disposition des formulaires claire et logique |
| **Responsive** | Layout adaptatif fonctionnel |

---

## Priority Matrix

```
                    HIGH IMPACT
                        |
    [COL-01] [TYP-01]   |   [COL-02]
         [TYP-02]       |
                        |
EASY FIX ---------------+--------------- HARD FIX
                        |
    [CMP-01] [SPC-03]   |   [VIS-01] [VIS-02]
         [COL-03]       |      [VIS-03]
                        |
                    LOW IMPACT
```

---

## Recommended Fix Order

### Phase 1: Quick Wins (Immediate)
1. **TYP-02**: Augmenter le contraste du texte "Bienvenue"
2. **COL-02**: Changer le bouton "Annuler" en style outline/gris
3. **COL-03**: Améliorer le contraste du badge "Déconnecté"
4. **CMP-01**: Unifier le style des badges (tous en pill)

### Phase 2: Typography System (1-2 heures)
1. **TYP-01**: Vérifier l'application des fonts configurées
2. **TYP-03**: Standardiser les font-weights des headers de table
3. **TYP-04**: Uniformiser les poids de font de la sidebar

### Phase 3: Color System (1-2 heures)
1. **COL-01**: Créer un système de couleurs sémantiques pour les statuts
   - `status-connected` = success-500
   - `status-disconnected` = gray-400
   - `status-published` = success-500
   - `status-sold` = info-500
   - `status-inactive` = gray-400
2. **COL-04**: Unifier les icônes des stat-cards
3. **COL-05**: Standardiser la couleur des liens (primary-500)

### Phase 4: Component Audit (2-3 heures)
1. **CMP-02**: Créer des variants de boutons standardisés
2. **CMP-03**: Unifier le border-radius (16px pour cards, 12px pour buttons)
3. **CMP-04**: Standardiser la hauteur des inputs (44px)
4. **CMP-05**: Standardiser la taille des icônes sidebar (20px)

### Phase 5: Spacing System (1-2 heures)
1. **SPC-01**: Revoir le grid des platform cards
2. **SPC-02**: Standardiser le padding des cellules de table
3. **SPC-03**: Uniformiser le gap label/input (8px)
4. **SPC-04**: Revoir l'indentation des sous-menus sidebar

### Phase 6: Visual Polish (2-3 heures)
1. **VIS-01**: Améliorer les empty states avec illustrations
2. **VIS-02**: Redesigner la page 404 avec branding
3. **VIS-03**: Ajouter skeleton loading
4. **VIS-04**: Standardiser les hover effects

---

## Technical Recommendations

### 1. Design Tokens Enforcement

Vérifier que `design-tokens.css` est bien importé et utilisé:
```css
/* Vérifier dans design-system.css */
@import './design-tokens.css';
```

### 2. Badge Component Refactor

Créer un composant Badge unifié:
```vue
<Badge variant="success|warning|error|info|neutral" />
```

### 3. Button Variants

Définir clairement les variants:
- `btn-primary`: Action principale (jaune plein)
- `btn-secondary`: Action secondaire (gris outline)
- `btn-danger`: Actions destructives (rouge)
- `btn-ghost`: Actions tertiaires (transparent)

### 4. Status Color Mapping

```css
:root {
  --status-connected: var(--color-success-500);
  --status-disconnected: var(--color-gray-400);
  --status-published: var(--color-success-500);
  --status-sold: var(--color-info-500);
  --status-draft: var(--color-gray-400);
  --status-inactive: var(--color-warning-500);
}
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `frontend/assets/css/design-system.css` | Badges, buttons, typography fixes |
| `frontend/assets/css/design-tokens.css` | Status colors, spacing variables |
| `frontend/components/ui/Badge.vue` | Unified badge component |
| `frontend/components/layout/Sidebar.vue` | Icon sizes, font weights |
| `frontend/pages/dashboard/index.vue` | Welcome text contrast |
| `frontend/pages/dashboard/products/create.vue` | Cancel button style |
| `frontend/pages/dashboard/platforms/index.vue` | Card grid spacing |
| `frontend/pages/error.vue` | 404 page redesign |

---

## Estimated Effort

| Phase | Time | Priority |
|-------|------|----------|
| Phase 1: Quick Wins | 30 min | P0 |
| Phase 2: Typography | 1-2h | P1 |
| Phase 3: Colors | 1-2h | P1 |
| Phase 4: Components | 2-3h | P2 |
| Phase 5: Spacing | 1-2h | P2 |
| Phase 6: Polish | 2-3h | P3 |
| **Total** | **8-12h** | |

---

*Report generated by Claude Code - Playwright UI Audit*
