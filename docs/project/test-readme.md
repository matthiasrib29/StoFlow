# 🧪 Guide de Test - eBay Orders Management

Ce guide explique comment tester l'implémentation complète de la gestion des commandes eBay.

## 📋 Prérequis

### 1. Serveurs lancés
```bash
# Backend (doit tourner sur port 8000)
cd backend
source venv/bin/activate
uvicorn main:app --reload

# Frontend (doit tourner sur port 3000)
cd frontend
npm run dev
```

### 2. Compte eBay connecté
- Tu dois avoir un compte eBay avec des credentials OAuth configurés
- Des commandes doivent exister sur ton compte eBay (ou avoir existé récemment)

### 3. Token JWT
Tu auras besoin d'un token JWT valide. Deux options :

**Option A : Via le frontend**
1. Va sur http://localhost:3000
2. Connecte-toi
3. Ouvre DevTools (F12) → Console
4. Exécute : `localStorage.getItem('access_token')`
5. Copie le token

**Option B : Via l'API**
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "ton-email@example.com", "password": "ton-password"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])"
```

---

## 🚀 Lancer les tests automatisés

### Méthode 1 : Interactive (recommandée)
```bash
cd /home/maribeiro/StoFlow-ebay-order
./test-ebay-orders.sh
```

Le script te demandera ton token JWT de manière interactive.

### Méthode 2 : Avec variable d'environnement
```bash
export EBAY_TOKEN="ton_token_jwt_ici"
./test-ebay-orders.sh
```

---

## 📊 Ce que le script teste

### ✅ Tests Backend (automatiques)

1. **Pre-flight checks**
   - Backend accessible (port 8000)
   - Frontend accessible (port 3000)
   - Token JWT valide

2. **Test 1 : Synchronisation**
   - POST /api/ebay/orders/sync
   - Vérifie le format : `{created, updated, errors, total_fetched}`

3. **Test 2 : Liste paginée**
   - GET /api/ebay/orders?page=1&page_size=10
   - Vérifie le format : `{items, total, page, page_size, total_pages}`

4. **Test 3 : Filtres**
   - GET /api/ebay/orders?status=NOT_STARTED
   - Vérifie que le filtrage fonctionne

5. **Test 4 : Détails**
   - GET /api/ebay/orders/{id}
   - Vérifie les champs : buyer, shipping address, products

6. **Test 5 : Update fulfillment**
   - PATCH /api/ebay/orders/{id}/fulfillment
   - Change le status à IN_PROGRESS

7. **Test 6 : Pagination page 2**
   - GET /api/ebay/orders?page=2&page_size=5
   - Vérifie que les items sont différents de page 1

8. **Test 7 : Tracking** (manuel)
   - POST /api/ebay/orders/{id}/tracking
   - Info affichée pour test manuel (nécessite commande PAID)

9. **Test 8 : Workflow complet**
   - Sync dernière heure → Vérification en DB

### ℹ️ Tests Frontend (manuels)

Le script affiche une checklist pour tester manuellement :

1. Accès à la page orders
2. Affichage des stats
3. Recherche et filtres
4. Détails d'une commande

---

## 📁 Résultats des tests

Les résultats sont sauvegardés dans :
```
./test-results/
├── test_1_YYYYMMDD_HHMMSS.json   # Sync response
├── test_2_YYYYMMDD_HHMMSS.json   # List response
├── test_3_YYYYMMDD_HHMMSS.json   # Filter response
├── test_4_YYYYMMDD_HHMMSS.json   # Detail response
├── test_5_YYYYMMDD_HHMMSS.json   # Update response
└── test_6_YYYYMMDD_HHMMSS.json   # Pagination response
```

Tu peux inspecter ces fichiers pour voir les réponses complètes de l'API.

---

## 🔍 Interpréter les résultats

### ✅ Succès attendu
```
========================================
BACKEND API TESTS
========================================

▶ Test 1: Synchronize orders from eBay (last 24h)
✅ Sync completed: Created=5, Updated=3, Errors=0, Total=8

▶ Test 2: List orders (page 1, 10 items)
✅ List returned: 10 items (Total in DB: 23)

▶ Test 3: Filter orders by status (NOT_STARTED)
✅ Filter returned 7 orders with status NOT_STARTED

...

✅ All automated tests completed successfully!
```

### ❌ Erreurs possibles

**Erreur : Backend not accessible**
```bash
❌ Backend server not accessible. Start it with: cd backend && uvicorn main:app --reload
```
→ Lance le backend

**Erreur : Token is invalid**
```bash
❌ Token is invalid or expired (HTTP 401)
```
→ Récupère un nouveau token JWT

**Erreur : Sync returned unexpected format**
```bash
❌ Sync failed or returned unexpected format
```
→ Vérifie les logs backend, probablement un problème de connexion eBay

**Erreur : No orders found**
```bash
⚠️  Workflow failed: No orders found
```
→ Ton compte eBay n'a pas de commandes récentes, c'est normal si compte de test

---

## 🧪 Tests manuels supplémentaires

### Test tracking avec commande PAID

Si tu as une commande avec status `PAID`, tu peux tester l'ajout de tracking :

```bash
# Remplace ORDER_ID par l'ID d'une commande PAID
curl -X POST "http://localhost:8000/api/ebay/orders/123/tracking" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tracking_number": "ABC123456789",
    "carrier_code": "COLISSIMO",
    "shipped_date": "2026-01-07T12:00:00Z"
  }' | python3 -m json.tool
```

**Résultat attendu :**
```json
{
  "success": true,
  "fulfillment_id": "xyz789...",
  "order_id": "12-34567-89012",
  "tracking_number": "ABC123456789"
}
```

### Tests de stress

Pour tester avec beaucoup de commandes :

```bash
# Sync des 30 derniers jours
curl -X POST "http://localhost:8000/api/ebay/orders/sync" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hours": 720}' | python3 -m json.tool
```

---

## 📝 Checklist complète

### Backend
- [ ] Pre-flight checks passent
- [ ] Sync réussit avec statistiques correctes
- [ ] Liste retourne format paginé
- [ ] Filtres fonctionnent (status, marketplace, dates)
- [ ] Détails complets d'une commande
- [ ] Update fulfillment status (DB locale)
- [ ] Pagination avec items différents
- [ ] (Optionnel) Tracking avec commande PAID

### Frontend
- [ ] Page charge sans erreur (http://localhost:3000/dashboard/platforms/ebay/orders)
- [ ] Stats cards s'affichent (Total, Revenue, Pending, Shipped)
- [ ] Bouton "Rafraîchir" fonctionne
- [ ] Tableau affiche les commandes
- [ ] Recherche par Order ID fonctionne
- [ ] Filtre par Payment Status fonctionne
- [ ] Filtre par Fulfillment Status fonctionne
- [ ] Clic sur commande affiche détails
- [ ] Détails montrent : buyer, shipping, products

---

## 🐛 Debugging

### Logs Backend
```bash
# Tail les logs du backend
tail -f logs/backend.log
```

### Logs Frontend
```bash
# DevTools Console dans le navigateur
# Ou tail les logs npm
tail -f logs/frontend.log
```

### Vérifier la DB directement
```bash
psql -h localhost -p 5433 -U stoflow_user -d stoflow_db

# Liste les commandes
SELECT id, order_id, buyer_username, total_price, order_fulfillment_status
FROM user_1.ebay_orders
ORDER BY creation_date DESC
LIMIT 10;
```

---

## 📞 Support

Si un test échoue :
1. Vérifie les logs backend/frontend
2. Vérifie que ton compte eBay a des credentials valides
3. Vérifie que des commandes existent sur ton compte eBay
4. Consulte les fichiers de résultats dans `test-results/`

---

**Dernière mise à jour** : 2026-01-07
