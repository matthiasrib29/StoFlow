# Roadmap: Improve eBay Capability - Order Management

## Overview

Implémentation complète de la gestion post-vente eBay dans StoFlow. Progression : Foundation → Returns (backend → frontend) → Cancellations → Refunds → Payment Disputes → INR Inquiries → Dashboard unifié. Chaque domaine suit le pattern : Client API → Model/Repository → Service → Endpoints REST → Frontend.

## Domain Expertise

None (eBay API patterns, internal architecture established)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Foundation** - Post-Order API base client, shared utilities, OAuth scope verification
- [x] **Phase 2: Returns Backend Core** - EbayReturnClient, EbayReturn model, repository
- [x] **Phase 3: Returns Backend Service** - EbayReturnService, sync service, business logic
- [x] **Phase 4: Returns API** - REST endpoints pour retours
- [x] **Phase 5: Returns Frontend** - Pages liste/détail, composants, actions
- [x] **Phase 6: Cancellations Backend** - Client, model, repository, service
- [x] **Phase 7: Cancellations API & Frontend** - Endpoints, sync, pages, actions
- [x] **Phase 8: Refunds** - Extend FulfillmentClient, model, service, endpoints, UI
- [x] **Phase 9: Payment Disputes Backend** - Client, model, repository, service, API endpoints
- [x] **Phase 10: Payment Disputes Frontend** - Pages, evidence upload, contest actions
- [x] **Phase 11: INR Inquiries** - Client, model, service, endpoints, UI complète
- [x] **Phase 12: Dashboard & Alerts** - Dashboard unifié, AlertService, notifications urgentes

## Phase Details

### Phase 1: Foundation
**Goal**: Établir les bases pour Post-Order API - base client, utilities partagées, vérification OAuth scopes
**Depends on**: Nothing (first phase)
**Research**: Likely (Post-Order API authentication, deprecated endpoints)
**Research topics**: Post-Order API auth requirements, scopes needed, deprecated methods to avoid
**Plans**: TBD

### Phase 2: Returns Backend Core
**Goal**: Créer le client API retours, le modèle EbayReturn et le repository
**Depends on**: Phase 1
**Research**: Likely (Post-Order API returns endpoints)
**Research topics**: GET /return/search, GET /return/{id}, response schemas, status values
**Plans**: TBD

### Phase 3: Returns Backend Service
**Goal**: Implémenter EbayReturnService avec logique métier et sync
**Depends on**: Phase 2
**Research**: Unlikely (internal service patterns)
**Plans**: TBD

### Phase 4: Returns API
**Goal**: Exposer les endpoints REST pour gestion des retours
**Depends on**: Phase 3
**Research**: Unlikely (FastAPI patterns existants)
**Plans**: TBD

### Phase 5: Returns Frontend
**Goal**: Créer les pages et composants frontend pour gestion des retours
**Depends on**: Phase 4
**Research**: Unlikely (Vue/Nuxt patterns existants)
**Plans**: TBD

### Phase 6: Cancellations Backend
**Goal**: Implémenter client, model, repository et service pour annulations
**Depends on**: Phase 1
**Research**: Likely (Post-Order API cancellation endpoints)
**Research topics**: Cancellation API methods, approval/rejection flow, seller-initiated cancellation
**Plans**: TBD

### Phase 7: Cancellations API & Frontend
**Goal**: Endpoints REST et interface frontend pour annulations
**Depends on**: Phase 6
**Research**: Unlikely (patterns établis phases précédentes)
**Plans**: TBD

### Phase 8: Refunds
**Goal**: Étendre FulfillmentClient avec issueRefund, tracking des remboursements
**Depends on**: Phase 5, Phase 7 (retours et annulations génèrent des refunds)
**Research**: Likely (Fulfillment API issueRefund, Digital Signatures EU/UK)
**Research topics**: issueRefund endpoint, refund status tracking, Digital Signature requirements
**Plans**: TBD

### Phase 9: Payment Disputes Backend
**Goal**: Client, model, repository et service pour litiges de paiement
**Depends on**: Phase 1
**Research**: Likely (Fulfillment API payment dispute methods)
**Research topics**: getPaymentDispute, contestPaymentDispute, evidence upload flow
**Plans**: TBD

### Phase 10: Payment Disputes Frontend
**Goal**: Interface frontend avec upload de preuves et actions contest/accept
**Depends on**: Phase 9
**Research**: Unlikely (patterns établis)
**Plans**: TBD

### Phase 11: INR Inquiries
**Goal**: Gestion complète des réclamations "Article non reçu"
**Depends on**: Phase 1
**Research**: Likely (Post-Order API inquiry methods)
**Research topics**: Inquiry search, respond with tracking, escalation to case
**Plans**: TBD

### Phase 12: Dashboard & Alerts
**Goal**: Dashboard eBay unifié avec compteurs, AlertService pour actions urgentes
**Depends on**: Phases 5, 7, 10, 11 (tous les domaines)
**Research**: Unlikely (aggregation interne)
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 1/1 | Complete | 2026-01-13 |
| 2. Returns Backend Core | 1/1 | Complete | 2026-01-13 |
| 3. Returns Backend Service | 1/1 | Complete | 2026-01-13 |
| 4. Returns API | 1/1 | Complete | 2026-01-13 |
| 5. Returns Frontend | 1/1 | Complete | 2026-01-13 |
| 6. Cancellations Backend | 1/1 | Complete | 2026-01-14 |
| 7. Cancellations API & Frontend | 1/1 | Complete | 2026-01-14 |
| 8. Refunds | 1/1 | Complete | 2026-01-14 |
| 9. Payment Disputes Backend | 1/1 | Complete | 2026-01-14 |
| 10. Payment Disputes Frontend | 1/1 | Complete | 2026-01-14 |
| 11. INR Inquiries | 1/1 | Complete | 2026-01-14 |
| 12. Dashboard & Alerts | 1/1 | Complete | 2026-01-14 |

---

*Roadmap created: 2026-01-13*
