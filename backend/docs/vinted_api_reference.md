# Vinted API Reference - Reverse Engineering Documentation

> **Source**: Extracted from pythonApiWOO project (2024)
> **Architecture Stoflow**: Plugin browser executes HTTP requests (no cookies/headers needed in backend)

---

## Table of Contents

1. [API Endpoints](#api-endpoints)
2. [Product Operations](#product-operations)
3. [Image Upload](#image-upload)
4. [Orders & Transactions](#orders--transactions)
5. [Payload Formats](#payload-formats)
6. [Mapping IDs Reference](#mapping-ids-reference)

---

## API Endpoints

### Base URL
```
https://www.vinted.fr
```

### Products

| Operation | Method | URL | Notes |
|-----------|--------|-----|-------|
| List shop products | GET | `/api/v2/wardrobe/{shop_id}/items?page={page}&per_page={per_page}&order=relevance` | Pagination, 80/page max |
| Create product | POST | `/api/v2/item_upload/items` | Full payload required |
| Update product | PUT | `/api/v2/item_upload/items/{item_id}` | Same payload as create |
| Delete product | POST | `/api/v2/items/{item_id}/delete` | Empty body |
| Get product status | GET | `/api/v2/items/{item_id}/status` | Check listing status |

### Drafts

| Operation | Method | URL | Notes |
|-----------|--------|-----|-------|
| Create draft | POST | `/api/v2/item_upload/drafts` | Same payload as create |
| Delete draft | DELETE | `/api/v2/item_upload/drafts/{draft_id}` | |

### Images

| Operation | Method | URL | Notes |
|-----------|--------|-----|-------|
| Upload image | POST | `/api/v2/photos` | multipart/form-data |

### Orders

| Operation | Method | URL | Notes |
|-----------|--------|-----|-------|
| Get orders | GET | `/api/v2/my_orders?type={sold/bought}&status={completed}&page={page}&per_page={per_page}` | |
| Get transaction details | GET | `/api/v2/transactions/{transaction_id}` | Full order details |
| Get shipment label | GET | `/api/v2/shipments/{shipment_id}/label_url` | PDF label URL |

### Auth

| Operation | Method | URL | Notes |
|-----------|--------|-----|-------|
| Refresh token | POST | `/web/api/auth/refresh` | Refresh access_token_web cookie |

---

## Product Operations

### Create Product (POST /api/v2/item_upload/items)

**Referer**: `https://www.vinted.fr/items/new`

```json
{
  "item": {
    "id": null,
    "currency": "EUR",
    "temp_uuid": "uuid-v4",
    "title": "Levi's 501 Jeans [SKU123]",
    "description": "Description du produit...",
    "brand_id": 53,
    "brand": "",
    "size_id": 206,
    "catalog_id": 5,
    "isbn": null,
    "is_unisex": false,
    "status_id": 6,
    "video_game_rating_id": null,
    "price": 27.90,
    "package_size_id": 1,
    "shipment_prices": {
      "domestic": null,
      "international": null
    },
    "color_ids": [12],
    "assigned_photos": [
      {"id": 123456, "orientation": 0},
      {"id": 123457, "orientation": 0}
    ],
    "measurement_length": 75,
    "measurement_width": 52,
    "item_attributes": [],
    "manufacturer": null,
    "manufacturer_labelling": null
  },
  "feedback_id": null,
  "push_up": false,
  "parcel": null,
  "upload_session_id": "uuid-v4"
}
```

### Update Product (PUT /api/v2/item_upload/items/{item_id})

**Referer**: `https://www.vinted.fr/items/{item_id}/edit`

Same payload as create, but with `item.id` set to the existing Vinted ID.

### Delete Product (POST /api/v2/items/{item_id}/delete)

**Referer**: Product URL (e.g., `https://www.vinted.fr/items/1234567890-titre-du-produit`)

No body required. Returns 200 on success.

---

## Image Upload

### Upload Image (POST /api/v2/photos)

**Content-Type**: `multipart/form-data`

**Form fields**:
```
photo[type] = "item"
photo[temp_uuid] = ""
photo[file] = <binary file data>
```

**Response**:
```json
{
  "id": 123456789,
  "url": "https://images1.vinted.net/...",
  "width": 800,
  "height": 1200
}
```

**Image Requirements**:
- Format: JPEG preferred
- Recommended aspect ratio: 3:4 (portrait)
- Max size: ~10MB
- Conversion to 3:4 portrait recommended for clothing (except jeans/pants)

---

## Orders & Transactions

### Get Orders (GET /api/v2/my_orders)

**Query params**:
- `type`: `sold` | `bought`
- `status`: `completed` | `pending` | `all`
- `page`: Page number
- `per_page`: Items per page (default 20)

**Response**:
```json
{
  "my_orders": [
    {
      "transaction_id": 123456789,
      "status": "completed",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5
  }
}
```

### Get Transaction Details (GET /api/v2/transactions/{transaction_id})

**Response structure**:
```json
{
  "id": 123456789,
  "buyer": {
    "id": 12345,
    "login": "buyer_username",
    "country_code": "FR"
  },
  "offer": {
    "price": {
      "amount": "25.00",
      "currency_code": "EUR"
    }
  },
  "order": {
    "items": [
      {
        "id": 987654321,
        "title": "Product title",
        "price": {
          "amount": "27.90",
          "currency_code": "EUR"
        }
      }
    ]
  },
  "debit_processed_at": "2024-01-15T10:35:00Z"
}
```

---

## Payload Formats

### Shop Items Response

**GET /api/v2/wardrobe/{shop_id}/items**

```json
{
  "items": [
    {
      "id": 123456789,
      "title": "Levi's 501 Jeans [SKU123]",
      "price": {
        "amount": "27.90",
        "currency_code": "EUR"
      },
      "url": "https://www.vinted.fr/items/123456789-levis-501-jeans",
      "photos": [
        {
          "id": 111222333,
          "url": "https://images1.vinted.net/..."
        }
      ],
      "view_count": 42,
      "favourite_count": 5,
      "is_closed": false,
      "is_draft": false,
      "item_closing_action": null
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 76,
    "total_entries": 6050
  },
  "code": 0
}
```

### Status Mapping

| API Fields | DB Status |
|------------|-----------|
| `is_draft=true` | `draft` |
| `is_closed=false` | `published` |
| `is_closed=true, item_closing_action=sold` | `sold` |
| `is_closed=true, item_closing_action=deleted` | `deleted` |

---

## Mapping IDs Reference

### Condition IDs (status_id)

| ID | Name FR | Name EN |
|----|---------|---------|
| 6 | Neuf avec étiquette | New with tags |
| 1 | Neuf sans étiquette | New without tags |
| 2 | Très bon état | Very good condition |
| 3 | Bon état | Good condition |
| 4 | Satisfaisant | Satisfactory |

### Package Size IDs (package_size_id)

| ID | Description |
|----|-------------|
| 1 | Petit colis (< 1kg) |
| 2 | Moyen colis (1-2kg) |
| 3 | Grand colis (2-5kg) |
| 5 | Très grand colis (> 5kg) |

### Category IDs (catalog_id)

Categories are hierarchical. Key categories for clothing:

| ID | Category | Gender |
|----|----------|--------|
| 5 | Jeans | Men |
| 1187 | Jeans | Women |
| 98 | Lunettes | Unisex |

> Full category mapping in `category_mapping` table

### Brand IDs (brand_id)

Stored in `brands` table. Example mappings:
- Levi's: 53
- Nike: 54
- Adidas: 14

### Color IDs (color_ids)

Stored in `colors` table. Example mappings:
- Bleu/Blue: 12
- Noir/Black: 1
- Blanc/White: 12

### Size IDs (size_id)

Depends on:
1. Gender (men/women)
2. Category type (top/bottom)

Stored in `sizes` table with columns:
- `vinted_woman_id`
- `vinted_man_top_id`
- `vinted_man_bottom_id`

---

## Rate Limiting

**Observed limits**:
- Mutating requests (POST/PUT/DELETE): ~50/hour
- GET requests: More lenient
- Recommended delay: 20-50 seconds between mutating requests
- On 403 (blocked): Wait 60+ minutes before retrying

**Anti-detection tips**:
- Random delays with jitter
- Vary User-Agent
- Include realistic Referer headers
- Maintain session cookies

---

## Stoflow Implementation Notes

### Architecture Differences

| pythonApiWOO | Stoflow |
|--------------|---------|
| Direct HTTP with cookies | Browser plugin proxy |
| Cookie management | Plugin handles auth |
| Rate limiting in backend | Rate limiting in plugin |
| Sync operations | Async via PluginTask |

### Plugin Task Format

For Stoflow's step-by-step architecture:

```python
task = PluginTask(
    platform="vinted",
    http_method="POST",
    path="https://www.vinted.fr/api/v2/item_upload/items",
    payload={
        "body": {  # Payload sent to Vinted API
            "item": {...},
            "feedback_id": null,
            ...
        }
    }
)
```

The plugin:
1. Receives task via polling
2. Injects CSRF token + Anon-ID automatically
3. Uses browser session cookies
4. Returns raw response to backend

---

## Appendix: Full URL Reference

```python
# Products
VINTED_URL_API_PRODUCTS = "https://www.vinted.fr/api/v2/wardrobe/{id_shop}/items?page={page}&per_page={per_page}&order=relevance"
VINTED_URL_API_ITEMS = "https://www.vinted.fr/api/v2/item_upload/items"
VINTED_URL_API_ITEMS_UPDATE = "https://www.vinted.fr/api/v2/item_upload/items/{item_id}"
VINTED_URL_API_ITEMS_STATUS = "https://www.vinted.fr/api/v2/items/{item_id}/status"

# Drafts
VINTED_URL_API_DRAFT = "https://www.vinted.fr/api/v2/item_upload/drafts"
VINTED_URL_API_DRAFT_DELETE = "https://www.vinted.fr/api/v2/item_upload/drafts/{draft_id}"

# Deletion
VINTED_URL_API_PUBLISH_DELETE = "https://www.vinted.fr/api/v2/items/{item_id}/delete"

# Images
VINTED_URL_API_PHOTOS = "https://www.vinted.fr/api/v2/photos"

# Orders
VINTED_URL_API_ORDERS = "https://www.vinted.fr/api/v2/my_orders"
VINTED_URL_API_TRANSACTIONS = "https://www.vinted.fr/api/v2/transactions/{transaction_id}"

# Shipping
VINTED_URL_API_SHIPMENT_LABEL = "https://www.vinted.fr/api/v2/shipments/{shipment_id}/label_url"

# Referers
VINTED_REFERER_MEMBER = "https://www.vinted.fr/member/{user_id}"
VINTED_REFERER_NEW_ITEM = "https://www.vinted.fr/items/new"
VINTED_REFERER_EDIT_ITEM = "https://www.vinted.fr/items/{item_id}/edit"
VINTED_REFERER_ORDERS = "https://www.vinted.fr/my_orders/sold"
```
