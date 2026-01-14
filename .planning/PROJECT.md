# PROJECT.md - StoFlow UI Improvement

**Created:** 2026-01-14
**Status:** Active

---

## Overview

Amélioration de l'interface utilisateur StoFlow pour éliminer l'aspect "AI slop" générique et créer une identité visuelle professionnelle et cohérente.

---

## Requirements

### Validated

- ✓ Application fonctionnelle (backend FastAPI + frontend Nuxt.js)
- ✓ Couleur primaire jaune/or (#facc15) définie
- ✓ Design tokens configurés (`design-tokens.css`)
- ✓ Fonts configurées (Plus Jakarta Sans, IBM Plex Sans, JetBrains Mono)
- ✓ Tailwind CSS intégré

### Active

- [ ] Typographie uniforme sur toutes les pages
- [ ] Système de couleurs sémantiques pour les statuts
- [ ] Badges avec style cohérent
- [ ] Boutons avec variants standardisés
- [ ] Espacement uniforme entre composants
- [ ] Empty states engageants
- [ ] Page 404 avec branding

### Out of Scope

- Refonte complète du layout — conserve la structure existante
- Ajout de nouvelles fonctionnalités — uniquement améliorations visuelles
- Animations complexes — focus sur la cohérence d'abord

---

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Conserver la couleur primaire jaune | Identité de marque établie | — Validé |
| Utiliser des pills pour tous les badges | Cohérence visuelle | — Pending |
| Border-radius 16px pour cards, 12px pour buttons | Hiérarchie visuelle claire | — Pending |
| Hauteur d'input standardisée 44px | Touch-friendly et cohérent | — Pending |

---

## Constraints

- **Temps**: Corrections réalisables en 8-12 heures
- **Compatibilité**: Maintenir la compatibilité avec les composants existants
- **Performance**: Ne pas ajouter de dépendances lourdes

---

## Context

### UI Audit Summary (2026-01-14)

Score global: **6.5/10**

**Issues identifiées par catégorie:**
- **CRITICAL (Typography)**: 4 issues — fonts non appliquées uniformément, contrastes faibles
- **HIGH (Colors)**: 5 issues — badges incohérents, bouton annuler en mauvaise couleur
- **MEDIUM (Spacing)**: 4 issues — espacement variable entre composants
- **MEDIUM (Components)**: 5 issues — styles de badges mixtes, border-radius variable
- **LOW (Visual Polish)**: 4 issues — empty states basiques, page 404 non stylée

**Rapport complet**: `.planning/UI-AUDIT-REPORT.md`

---

## Success Criteria

1. Score UI > 8/10 après corrections
2. Typographie uniforme sur toutes les pages
3. Badges et boutons avec styles cohérents
4. Aucune incohérence de couleur pour les statuts
5. Empty states engageants avec illustrations
6. Page 404 avec branding StoFlow

---

*Last updated: 2026-01-14 after UI audit*
