# Improve eBay Capability - Order Management

## Vision

Implémenter la gestion complète des commandes eBay dans StoFlow : **retours**, **annulations**, **remboursements**, et **litiges**. Permettre aux vendeurs de gérer tout le cycle de vie post-vente directement depuis l'application.

**One-liner**: Gestion complète du cycle post-vente eBay (retours, annulations, remboursements, litiges) via API REST + UI frontend.

---

## Requirements

### Validated (Existing Capabilities)

- ✓ **Synchronisation des commandes eBay** - `getOrders`, `getOrder` via Fulfillment API
- ✓ **Gestion du fulfillment** - Ajout de tracking, mise à jour statut
- ✓ **Modèles DB** - `EbayOrder`, `EbayOrderProduct` dans schema user
- ✓ **OAuth2 eBay** - Flow complet avec token refresh
- ✓ **Architecture Clean** - Services, Repositories, Clients API
- ✓ **Frontend orders** - Liste, détails, sync, tracking

### Active (To Be Built)

#### Phase 1: Returns Management (Retours)

**Backend:**
- [ ] Créer `EbayReturnClient` - Client API Post-Order pour retours
- [ ] Créer modèle `EbayReturn` avec statuts (OPEN, WAITING_SELLER, CLOSED, etc.)
- [ ] Créer `EbayReturnRepository` - CRUD + queries
- [ ] Créer `EbayReturnService` - Logique métier retours
- [ ] Créer `EbayReturnSyncService` - Sync retours depuis eBay
- [ ] Endpoints REST:
  - `GET /ebay/returns` - Lister retours avec filtres
  - `GET /ebay/returns/{id}` - Détails retour
  - `POST /ebay/returns/{id}/accept` - Accepter retour
  - `POST /ebay/returns/{id}/decline` - Refuser retour
  - `POST /ebay/returns/{id}/refund` - Émettre remboursement
  - `POST /ebay/returns/{id}/message` - Envoyer message
  - `POST /ebay/returns/sync` - Synchroniser retours

**Frontend:**
- [ ] Page `/dashboard/platforms/ebay/returns` - Liste retours
- [ ] Page `/dashboard/platforms/ebay/returns/[id]` - Détails retour
- [ ] Composants: `ReturnCard`, `ReturnActions`, `ReturnTimeline`
- [ ] Intégration dans navigation eBay

#### Phase 2: Cancellations Management (Annulations)

**Backend:**
- [ ] Créer `EbayCancellationClient` - Client API Post-Order
- [ ] Créer modèle `EbayCancellation` avec statuts
- [ ] Créer `EbayCancellationRepository`
- [ ] Créer `EbayCancellationService`
- [ ] Endpoints REST:
  - `GET /ebay/cancellations` - Lister annulations
  - `GET /ebay/cancellations/{id}` - Détails
  - `POST /ebay/cancellations/{id}/approve` - Approuver
  - `POST /ebay/cancellations/{id}/reject` - Rejeter
  - `POST /ebay/orders/{id}/cancel` - Initier annulation vendeur
  - `POST /ebay/cancellations/sync` - Synchroniser

**Frontend:**
- [ ] Page `/dashboard/platforms/ebay/cancellations` - Liste
- [ ] Composants: `CancellationCard`, `CancellationActions`
- [ ] Modal d'annulation depuis détail commande

#### Phase 3: Refunds Management (Remboursements)

**Backend:**
- [ ] Étendre `EbayFulfillmentClient` avec `issueRefund`
- [ ] Créer modèle `EbayRefund` pour tracking
- [ ] Créer `EbayRefundService`
- [ ] Endpoints REST:
  - `GET /ebay/refunds` - Lister remboursements
  - `GET /ebay/refunds/{id}` - Détails
  - `POST /ebay/orders/{id}/refund` - Initier remboursement
- [ ] Intégration avec returns (auto-refund après retour reçu)

**Frontend:**
- [ ] Section remboursements dans détail commande
- [ ] Historique des remboursements
- [ ] Modal de remboursement manuel

#### Phase 4: Payment Disputes (Litiges de paiement)

**Backend:**
- [ ] Créer `EbayPaymentDisputeClient` - Client Fulfillment API disputes
- [ ] Créer modèle `EbayPaymentDispute`
- [ ] Créer `EbayPaymentDisputeService`
- [ ] Endpoints REST:
  - `GET /ebay/disputes` - Lister litiges
  - `GET /ebay/disputes/{id}` - Détails
  - `POST /ebay/disputes/{id}/accept` - Accepter
  - `POST /ebay/disputes/{id}/contest` - Contester
  - `POST /ebay/disputes/{id}/evidence` - Ajouter preuve
  - `POST /ebay/disputes/sync` - Synchroniser

**Frontend:**
- [ ] Page `/dashboard/platforms/ebay/disputes` - Liste
- [ ] Page `/dashboard/platforms/ebay/disputes/[id]` - Détails avec upload preuves
- [ ] Alertes pour litiges urgents

#### Phase 5: INR Inquiries (Item Not Received)

**Backend:**
- [ ] Créer `EbayInquiryClient` - Client Post-Order inquiries
- [ ] Créer modèle `EbayInquiry`
- [ ] Créer `EbayInquiryService`
- [ ] Endpoints REST:
  - `GET /ebay/inquiries` - Lister INR
  - `GET /ebay/inquiries/{id}` - Détails
  - `POST /ebay/inquiries/{id}/respond` - Répondre (tracking)
  - `POST /ebay/inquiries/{id}/refund` - Rembourser
  - `POST /ebay/inquiries/sync` - Synchroniser

**Frontend:**
- [ ] Page `/dashboard/platforms/ebay/inquiries` - Liste
- [ ] Actions rapides (fournir tracking, rembourser)

#### Phase 6: Dashboard & Notifications

**Backend:**
- [ ] Créer `EbayAlertService` - Détection d'actions urgentes
- [ ] Job de sync périodique pour tous les types
- [ ] Endpoints stats agrégées

**Frontend:**
- [ ] Dashboard eBay unifié avec tous les compteurs
- [ ] Notifications pour actions urgentes (délais)
- [ ] Badges dans navigation

### Out of Scope (v1)

- **Case Management (escalades)** - Géré manuellement sur eBay pour v1
- **Messages buyer complets** - Conversation complète (partiellement implémenté)
- **Shipping labels auto** - Génération automatique d'étiquettes
- **Bulk operations** - Actions en masse sur retours/annulations
- **Webhooks eBay** - Notifications push (polling pour v1)
- **Multi-compte eBay** - Un seul compte par user pour v1

---

## Context

### APIs eBay Utilisées

| API | Usage |
|-----|-------|
| **Fulfillment API** | Orders, shipping fulfillment, refunds, payment disputes |
| **Post-Order API** | Cancellations, returns, inquiries |

### Modèles de Données à Créer

```
EbayReturn
├── id, return_id (eBay), order_id (FK)
├── status (RETURN_REQUESTED, WAITING_FOR_RETURN_SHIPMENT, ITEM_SHIPPED, ITEM_DELIVERED, REFUND_ISSUED, CLOSED)
├── reason, reason_detail
├── refund_amount, refund_status
├── buyer_comments, seller_comments
├── return_tracking_number, return_carrier
├── created_at, updated_at, closed_at

EbayCancellation
├── id, cancellation_id (eBay), order_id (FK)
├── status (CANCEL_REQUESTED, CANCEL_PENDING, CANCEL_CLOSED)
├── cancel_reason, cancel_initiator (BUYER, SELLER)
├── refund_status
├── created_at, updated_at

EbayRefund
├── id, refund_id (eBay), order_id (FK)
├── amount, currency
├── reason, status (PENDING, COMPLETED, FAILED)
├── refund_type (FULL, PARTIAL)
├── created_at

EbayPaymentDispute
├── id, dispute_id (eBay), order_id (FK)
├── status (OPEN, WAITING_SELLER, ACTION_NEEDED, CLOSED)
├── reason (INR, SNAD, UNAUTHORIZED)
├── amount, currency
├── seller_response, evidence_files
├── deadline
├── created_at, updated_at

EbayInquiry
├── id, inquiry_id (eBay), order_id (FK)
├── status (OPEN, WAITING_SELLER, CLOSED)
├── inquiry_type (INR)
├── buyer_message
├── created_at, escalation_date
```

### Statuts et Workflows

**Return Flow:**
```
RETURN_REQUESTED → (accept) → WAITING_FOR_RETURN_SHIPMENT → ITEM_SHIPPED → ITEM_DELIVERED → REFUND_ISSUED → CLOSED
                 → (decline) → CLOSED
```

**Cancellation Flow:**
```
CANCEL_REQUESTED → (approve) → CANCEL_CLOSED (+ refund)
                 → (reject) → CANCEL_CLOSED
                 → (timeout 3 days) → auto-approve
```

**Dispute Flow:**
```
OPEN → (accept) → CLOSED (seller loses)
     → (contest + evidence) → WAITING_RESOLUTION → CLOSED (win/lose)
```

---

## Constraints

### Technical

- **Post-Order API** - Certains endpoints deprecated en 2026, utiliser les alternatives
- **Rate Limits** - eBay limite les appels API, implémenter retry avec backoff
- **OAuth Scopes** - Vérifier que les scopes actuels couvrent Post-Order API
- **Digital Signatures** - Requis pour `issueRefund` sur EU/UK (à implémenter si nécessaire)

### Business

- **Délais de réponse** - 3 jours pour annulations, 5 jours pour retours
- **Métriques vendeur** - Certaines actions impactent le seller rating
- **Remboursements SNAD** - Frais retour toujours à charge vendeur

### UX

- **Alertes urgentes** - Mettre en avant les actions avec deadline proche
- **Actions rapides** - Pouvoir agir depuis la liste sans ouvrir le détail
- **Historique clair** - Timeline des événements pour chaque case

---

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Post-Order API pour returns/cancellations | API officielle eBay, pas d'alternative | Post-Order API v2 |
| Fulfillment API pour refunds/disputes | Méthodes disponibles dans Fulfillment | Fulfillment API |
| Polling vs Webhooks | Webhooks complexes à setup, polling suffisant pour v1 | Polling avec jobs |
| Modèles DB séparés | Clarté, queries spécialisées | 5 nouveaux modèles |
| Sync périodique | Détection rapide des nouvelles demandes | Job toutes les 15min |
| UI pages dédiées | Gestion complexe, pas dans la page orders | Pages séparées |

---

## Success Criteria

- [ ] Vendeur peut voir et traiter les retours depuis StoFlow
- [ ] Vendeur peut approuver/rejeter les annulations
- [ ] Vendeur peut émettre des remboursements
- [ ] Vendeur peut voir et contester les litiges de paiement
- [ ] Vendeur peut répondre aux INR avec tracking
- [ ] Alertes visibles pour actions urgentes
- [ ] Sync automatique toutes les 15 minutes
- [ ] Pas de dégradation des performances existantes

---

*Last updated: 2026-01-13 after project initialization*
