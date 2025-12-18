# API Endpoints - Marketplaces (eBay & Etsy)

Documentation des endpoints API pour la connexion au frontend.

## 🔗 Base URL

```
http://localhost:8000/api
```

## 📚 Documentation Interactive

Swagger UI: `http://localhost:8000/docs`

---

## 🛍️ eBay API Endpoints

### **OAuth2 & Connection**

#### `GET /api/ebay/oauth/connect`
Génère l'URL d'autorisation eBay OAuth2.

**Headers:**
```json
{
  "Authorization": "Bearer <access_token>"
}
```

**Response:**
```json
{
  "authorization_url": "https://auth.ebay.com/oauth2/authorize?...",
  "state": "random_state_string"
}
```

**Frontend Usage:**
```javascript
const response = await fetch('/api/ebay/oauth/connect', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { authorization_url } = await response.json();
window.location.href = authorization_url; // Redirect to eBay
```

---

#### `GET /api/ebay/oauth/callback`
Callback OAuth2 - Échange authorization code contre tokens.

**Query Params:**
- `code`: Authorization code from eBay
- `state`: State parameter (CSRF protection)

**Response:**
```json
{
  "success": true,
  "user_id": 123,
  "access_token_expires_at": "2025-12-10T15:00:00Z",
  "error": null
}
```

---

#### `GET /api/ebay/connection/status`
Vérifie le status de connexion eBay.

**Response:**
```json
{
  "connected": true,
  "user_id": "test_user",
  "access_token_expires_at": "2025-12-10T15:00:00Z",
  "refresh_token_expires_at": "2025-12-10T15:00:00Z"
}
```

---

### **Product Publication**

#### `POST /api/ebay/products/publish`
Publie un produit sur eBay.

**Request Body:**
```json
{
  "product_id": 123,
  "marketplace_id": "EBAY_FR",
  "category_id": "11450"
}
```

**Response:**
```json
{
  "success": true,
  "sku_derived": "STOFLOW-123-EBAY_FR",
  "offer_id": "987654321",
  "listing_id": "110123456789",
  "marketplace_id": "EBAY_FR",
  "message": "✅ Product published successfully"
}
```

---

#### `POST /api/ebay/products/unpublish`
Dé-publie un produit d'eBay.

**Request Body:**
```json
{
  "product_id": 123,
  "marketplace_id": "EBAY_FR"
}
```

**Response:**
```json
{
  "success": true,
  "sku_derived": "STOFLOW-123-EBAY_FR",
  "message": "Product unpublished successfully"
}
```

---

### **Listings & Inventory**

#### `GET /api/ebay/marketplaces`
Liste des marketplaces eBay disponibles.

**Response:**
```json
[
  {
    "marketplace_id": "EBAY_FR",
    "country_code": "FR",
    "site_id": 71,
    "currency": "EUR",
    "is_active": true,
    "language": "fr-FR",
    "content_language": "fr"
  }
]
```

---

#### `GET /api/ebay/orders`
Récupère les commandes eBay.

**Query Params:**
- `status`: Optional filter (PAID, SHIPPED, etc.)
- `limit`: Default 50

**Response:**
```json
{
  "orders": [
    {
      "order_id": "123-456789-0",
      "order_status": "PAID",
      "total_amount": 29.99,
      "buyer_username": "buyer123"
    }
  ]
}
```

---

## 🎨 Etsy API Endpoints

### **OAuth2 & Connection**

#### `GET /api/etsy/oauth/connect`
Génère l'URL d'autorisation Etsy OAuth2 (avec PKCE).

**Headers:**
```json
{
  "Authorization": "Bearer <access_token>"
}
```

**Response:**
```json
{
  "authorization_url": "https://www.etsy.com/oauth/connect?...",
  "state": "random_state_string"
}
```

**Frontend Usage:**
```javascript
const response = await fetch('/api/etsy/oauth/connect', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { authorization_url } = await response.json();
window.location.href = authorization_url; // Redirect to Etsy
```

---

#### `GET /api/etsy/oauth/callback`
Callback OAuth2 - Échange authorization code contre tokens.

**Query Params:**
- `code`: Authorization code from Etsy
- `state`: State parameter (CSRF protection)

**Response:**
```json
{
  "success": true,
  "shop_id": "12345678",
  "shop_name": "MyEtsyShop",
  "access_token_expires_at": "2025-12-10T15:00:00Z",
  "error": null
}
```

---

#### `POST /api/etsy/oauth/disconnect`
Déconnecte le compte Etsy.

**Response:**
```json
{
  "success": true,
  "message": "Etsy account disconnected successfully"
}
```

---

#### `GET /api/etsy/connection/status`
Vérifie le status de connexion Etsy.

**Response:**
```json
{
  "connected": true,
  "shop_id": "12345678",
  "shop_name": "MyEtsyShop",
  "access_token_expires_at": "2025-12-10T15:00:00Z",
  "refresh_token_expires_at": "2026-03-10T15:00:00Z"
}
```

---

### **Product Publication**

#### `POST /api/etsy/products/publish`
Publie un produit sur Etsy.

**Request Body:**
```json
{
  "product_id": 123,
  "taxonomy_id": 1234,
  "shipping_profile_id": 5678,
  "return_policy_id": 9012,
  "shop_section_id": 3456,
  "state": "active"
}
```

**Response:**
```json
{
  "success": true,
  "listing_id": 987654321,
  "listing_url": "https://www.etsy.com/listing/987654321",
  "state": "active",
  "error": null
}
```

---

#### `PUT /api/etsy/products/update`
Met à jour un listing Etsy.

**Request Body:**
```json
{
  "listing_id": 987654321,
  "product_id": 123
}
```

**Response:**
```json
{
  "success": true,
  "listing_id": 987654321,
  "error": null
}
```

---

#### `DELETE /api/etsy/products/delete`
Supprime un listing Etsy.

**Request Body:**
```json
{
  "listing_id": 987654321
}
```

**Response:**
```json
{
  "success": true,
  "error": null
}
```

---

### **Listings Management**

#### `GET /api/etsy/listings/active`
Récupère les listings actifs.

**Query Params:**
- `limit`: Default 25 (max 100)
- `offset`: Default 0

**Response:**
```json
[
  {
    "listing_id": 987654321,
    "title": "Handmade Necklace",
    "state": "active",
    "price": 29.99,
    "quantity": 10,
    "url": "https://www.etsy.com/listing/987654321",
    "created_timestamp": 1701234567,
    "updated_timestamp": 1701234567
  }
]
```

---

#### `GET /api/etsy/listings/{listing_id}`
Récupère les détails d'un listing.

**Response:**
```json
{
  "listing_id": 987654321,
  "title": "Handmade Necklace",
  "description": "Beautiful vintage...",
  "state": "active",
  "price": {...},
  "quantity": 10,
  "images": [...],
  "taxonomy_id": 1234
}
```

---

### **Shop Management**

#### `GET /api/etsy/shop`
Récupère les infos du shop.

**Response:**
```json
{
  "shop_id": 12345678,
  "shop_name": "MyEtsyShop",
  "title": "My Vintage Shop",
  "url": "https://www.etsy.com/shop/MyEtsyShop",
  "listing_active_count": 42,
  "currency_code": "USD"
}
```

---

#### `GET /api/etsy/shop/sections`
Récupère les sections du shop.

**Response:**
```json
[
  {
    "shop_section_id": 12345,
    "title": "Necklaces",
    "rank": 1,
    "active_listing_count": 15
  }
]
```

---

### **Orders (Receipts)**

#### `GET /api/etsy/orders`
Récupère les commandes.

**Query Params:**
- `status_filter`: Optional (open, completed, canceled)
- `limit`: Default 25 (max 100)
- `offset`: Default 0

**Response:**
```json
[
  {
    "receipt_id": 123456789,
    "buyer_user_id": 987654,
    "buyer_email": "buyer@example.com",
    "status": "completed",
    "is_paid": true,
    "is_shipped": true,
    "grandtotal": {...},
    "transactions": [...]
  }
]
```

---

#### `GET /api/etsy/orders/{receipt_id}`
Récupère les détails d'une commande.

**Response:**
```json
{
  "receipt_id": 123456789,
  "buyer_email": "buyer@example.com",
  "name": "John Doe",
  "first_line": "123 Main St",
  "city": "New York",
  "status": "completed",
  "transactions": [...]
}
```

---

### **Shipping Profiles**

#### `GET /api/etsy/shipping/profiles`
Récupère les shipping profiles.

**Response:**
```json
[
  {
    "shipping_profile_id": 12345,
    "title": "Standard Shipping",
    "min_processing_days": 1,
    "max_processing_days": 3,
    "origin_country_iso": "US"
  }
]
```

---

### **Taxonomy (Categories)**

#### `GET /api/etsy/taxonomy/nodes`
Récupère les catégories Etsy.

**Query Params:**
- `search`: Optional keyword filter

**Response:**
```json
[
  {
    "id": 1234,
    "level": 2,
    "name": "Necklaces",
    "parent_id": 1000,
    "children": [1235, 1236],
    "full_path_taxonomy_ids": [1000, 1234]
  }
]
```

---

#### `GET /api/etsy/taxonomy/nodes/{taxonomy_id}/properties`
Récupère les propriétés requises pour une catégorie.

**Response:**
```json
[
  {
    "property_id": 100,
    "name": "primary_color",
    "display_name": "Primary Color",
    "is_required": true,
    "possible_values": [...]
  }
]
```

---

### **Polling (Alternative Webhooks)**

#### `GET /api/etsy/polling/status`
Exécute un cycle de polling Etsy.

**Query Params:**
- `check_orders`: Default true
- `check_listings`: Default true
- `check_stock`: Default true
- `order_interval`: Default 5 (minutes)
- `listing_interval`: Default 15 (minutes)
- `stock_threshold`: Default 5

**Response:**
```json
{
  "timestamp": "2025-12-10T15:00:00Z",
  "new_orders_count": 3,
  "updated_listings_count": 1,
  "low_stock_count": 2,
  "new_orders": [...],
  "updated_listings": [...],
  "low_stock_listings": [...]
}
```

---

## 🔐 Authentication

Tous les endpoints (sauf `/oauth/callback`) requièrent un JWT token:

```javascript
headers: {
  'Authorization': `Bearer ${access_token}`
}
```

---

## 📋 Configuration Requise (.env)

### eBay:
```env
EBAY_APP_ID=your_app_id
EBAY_CERT_ID=your_cert_id
EBAY_DEV_ID=your_dev_id
EBAY_REDIRECT_URI=http://localhost:3000/ebay/callback
EBAY_WEBHOOK_VERIFICATION_TOKEN=your_webhook_token
```

### Etsy:
```env
ETSY_API_KEY=your_client_id
ETSY_API_SECRET=your_client_secret
ETSY_REDIRECT_URI=http://localhost:3000/etsy/callback
```

---

## 🎯 Frontend Integration Examples

### eBay Connection Flow

```javascript
// 1. Start OAuth flow
const connectEbay = async () => {
  const res = await fetch('/api/ebay/oauth/connect', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const { authorization_url } = await res.json();
  window.location.href = authorization_url;
};

// 2. Handle callback (in /ebay/callback page)
useEffect(() => {
  const params = new URLSearchParams(window.location.search);
  const code = params.get('code');
  const state = params.get('state');

  fetch(`/api/ebay/oauth/callback?code=${code}&state=${state}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }).then(res => res.json()).then(data => {
    if (data.success) {
      router.push('/dashboard');
    }
  });
}, []);
```

### Etsy Connection Flow

```javascript
// 1. Start OAuth flow
const connectEtsy = async () => {
  const res = await fetch('/api/etsy/oauth/connect', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const { authorization_url } = await res.json();
  window.location.href = authorization_url;
};

// 2. Handle callback (in /etsy/callback page)
useEffect(() => {
  const params = new URLSearchParams(window.location.search);
  const code = params.get('code');
  const state = params.get('state');

  fetch(`/api/etsy/oauth/callback?code=${code}&state=${state}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }).then(res => res.json()).then(data => {
    if (data.success) {
      router.push('/dashboard');
    }
  });
}, []);
```

### Publish Product

```javascript
// eBay
const publishToEbay = async (productId, marketplaceId = 'EBAY_FR') => {
  const res = await fetch('/api/ebay/products/publish', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      product_id: productId,
      marketplace_id: marketplaceId,
      category_id: '11450' // T-shirts category
    })
  });
  return await res.json();
};

// Etsy
const publishToEtsy = async (productId, taxonomyId) => {
  const res = await fetch('/api/etsy/products/publish', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      product_id: productId,
      taxonomy_id: taxonomyId,
      state: 'active'
    })
  });
  return await res.json();
};
```

---

## 📊 Rate Limits

- **eBay**: 5000 requêtes/jour par défaut
- **Etsy**: 10 requêtes/seconde, 10 000 requêtes/jour

---

## ⚠️ Notes Importantes

1. **Etsy Webhooks**: Etsy n'a PAS de webhooks natifs. Utiliser le polling endpoint régulièrement (ex: toutes les 5 minutes).

2. **Token Expiry**:
   - eBay access token: 2 heures (refresh automatique)
   - Etsy access token: 1 heure (refresh automatique)
   - Etsy refresh token: 90 jours

3. **PKCE**: Etsy requiert PKCE (Proof Key for Code Exchange) obligatoire pour OAuth2.

4. **CORS**: Configurer les origins autorisées dans `.env`:
   ```env
   CORS_ORIGINS=http://localhost:3000,https://app.stoflow.com
   ```

---

Généré le: 2025-12-10
