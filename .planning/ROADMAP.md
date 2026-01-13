# Roadmap: AI Product Generation

## Overview

Implémentation d'un générateur automatique de titres SEO et descriptions dynamiques pour produits vestimentaires. Templates Python déterministes avec gestion intelligente des attributs manquants. Backend service → API → User settings → Frontend composable → UI intégration.

## Domain Expertise

None (internal patterns, no external integrations)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [ ] **Phase 1: Backend Service** - Service Python de génération templates
- [ ] **Phase 2: Backend API** - Endpoints REST génération et preview
- [ ] **Phase 3: User Settings** - Préférences format/style par utilisateur
- [ ] **Phase 4: Frontend Composable** - useProductTextGenerator.ts
- [ ] **Phase 5: Frontend UI** - Boutons et modal dans formulaire produit

## Phase Details

### Phase 1: Backend Service
**Goal**: Créer le service `ProductTextGeneratorService` avec les 3 formats de titre et 3 styles de description
**Depends on**: Nothing (first phase)
**Research**: Unlikely (Python templates, internal patterns)
**Plans**: 2 plans

Plans:
- [ ] 01-01: Implémentation des 3 formats de titre
- [ ] 01-02: Implémentation des 3 styles de description

### Phase 2: Backend API
**Goal**: Exposer les endpoints REST pour générer et preview les textes
**Depends on**: Phase 1
**Research**: Unlikely (FastAPI patterns existants)
**Plans**: 1 plan

Plans:
- [ ] 02-01: Endpoints generate-text et preview-text

### Phase 3: User Settings
**Goal**: Ajouter les préférences utilisateur pour format titre et style description par défaut
**Depends on**: Phase 2
**Research**: Unlikely (user settings pattern existant)
**Plans**: 1 plan

Plans:
- [ ] 03-01: Migration DB + API settings

### Phase 4: Frontend Composable
**Goal**: Créer le composable `useProductTextGenerator.ts` pour l'intégration frontend
**Depends on**: Phase 2
**Research**: Unlikely (Vue composable patterns existants)
**Plans**: 1 plan

Plans:
- [ ] 04-01: Composable avec generate, preview, state management

### Phase 5: Frontend UI
**Goal**: Intégrer les boutons de génération et modal preview dans le formulaire produit
**Depends on**: Phase 4
**Research**: Unlikely (UI patterns existants)
**Plans**: 2 plans

Plans:
- [ ] 05-01: TextGeneratorButton + TextPreviewModal components
- [ ] 05-02: Intégration dans pages create/edit product

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Backend Service | 0/2 | Not started | - |
| 2. Backend API | 0/1 | Not started | - |
| 3. User Settings | 0/1 | Not started | - |
| 4. Frontend Composable | 0/1 | Not started | - |
| 5. Frontend UI | 0/2 | Not started | - |

---

*Roadmap created: 2026-01-13*
