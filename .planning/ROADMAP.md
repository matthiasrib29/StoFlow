# Roadmap: StoFlow UI Improvement

## Overview

Amélioration de l'interface utilisateur StoFlow pour éliminer l'aspect générique et créer une identité visuelle professionnelle et cohérente. Basé sur l'audit UI réalisé le 2026-01-14 (score 6.5/10 → objectif >8/10).

## Domain Expertise

None (internal CSS/Vue patterns, no external integrations)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [ ] **Phase 1: Quick Wins** - Corrections immédiates à fort impact (30 min)
- [ ] **Phase 2: Typography System** - Uniformisation des fonts et poids (1-2h)
- [ ] **Phase 3: Color System** - Couleurs sémantiques pour statuts (1-2h)
- [ ] **Phase 4: Component Audit** - Standardisation des composants (2-3h)
- [ ] **Phase 5: Spacing System** - Espacement uniforme (1-2h)
- [ ] **Phase 6: Visual Polish** - Empty states et page 404 (2-3h)

## Phase Details

### Phase 1: Quick Wins
**Goal**: Corrections immédiates qui améliorent significativement l'UX avec peu d'effort
**Depends on**: Nothing (first phase)
**Research**: Unlikely (simple CSS fixes)
**Plans**: 1 plan

**Issues addressed**:
- TYP-02: Augmenter le contraste du texte "Bienvenue"
- COL-02: Changer le bouton "Annuler" en style outline/gris
- COL-03: Améliorer le contraste du badge "Déconnecté"
- CMP-01: Unifier le style des badges (tous en pill)

Plans:
- [ ] 01-01: Quick wins CSS et composants

### Phase 2: Typography System
**Goal**: Garantir que les fonts configurées sont appliquées uniformément
**Depends on**: Phase 1
**Research**: Unlikely (CSS font-family verification)
**Plans**: 1 plan

**Issues addressed**:
- TYP-01: Vérifier l'application des fonts
- TYP-03: Standardiser les font-weights des headers de table
- TYP-04: Uniformiser les poids de font de la sidebar

Plans:
- [ ] 02-01: Typography system enforcement

### Phase 3: Color System
**Goal**: Créer un système de couleurs sémantiques cohérent pour tous les statuts
**Depends on**: Phase 1
**Research**: Unlikely (CSS variables)
**Plans**: 1 plan

**Issues addressed**:
- COL-01: Couleurs incohérentes pour états similaires
- COL-04: Unifier les icônes des stat-cards
- COL-05: Standardiser la couleur des liens

Plans:
- [ ] 03-01: Semantic color system

### Phase 4: Component Audit
**Goal**: Standardiser tous les composants UI (badges, buttons, inputs)
**Depends on**: Phase 2, Phase 3
**Research**: Unlikely (Vue component patterns)
**Plans**: 2 plans

**Issues addressed**:
- CMP-02: Variants de boutons standardisés
- CMP-03: Unifier le border-radius
- CMP-04: Standardiser la hauteur des inputs
- CMP-05: Standardiser la taille des icônes sidebar

Plans:
- [ ] 04-01: Badge component unification
- [ ] 04-02: Button and input standardization

### Phase 5: Spacing System
**Goal**: Uniformiser l'espacement entre tous les composants
**Depends on**: Phase 4
**Research**: Unlikely (CSS spacing)
**Plans**: 1 plan

**Issues addressed**:
- SPC-01: Grid des platform cards
- SPC-02: Padding des cellules de table
- SPC-03: Gap label/input
- SPC-04: Indentation des sous-menus sidebar

Plans:
- [ ] 05-01: Spacing system enforcement

### Phase 6: Visual Polish
**Goal**: Améliorer les états visuels pour une expérience premium
**Depends on**: Phase 5
**Research**: Unlikely (Vue components)
**Plans**: 2 plans

**Issues addressed**:
- VIS-01: Empty states avec illustrations
- VIS-02: Page 404 avec branding
- VIS-03: Skeleton loading
- VIS-04: Hover effects

Plans:
- [ ] 06-01: Empty states and 404 page
- [ ] 06-02: Loading states and hover effects

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6
(Phases 2 and 3 can run in parallel)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Quick Wins | 0/1 | Pending | — |
| 2. Typography System | 0/1 | Pending | — |
| 3. Color System | 0/1 | Pending | — |
| 4. Component Audit | 0/2 | Pending | — |
| 5. Spacing System | 0/1 | Pending | — |
| 6. Visual Polish | 0/2 | Pending | — |

---

*Roadmap created: 2026-01-14*
*Based on: UI-AUDIT-REPORT.md*
