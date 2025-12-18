# 📊 eBay Integration - Deep Dive Analysis & Recommendations

**Date:** 2025-12-10
**Author:** Claude
**Project:** Stoflow Backend - eBay MVP Integration

---

## 📋 Table des matières

1. [Analyse de l'implémentation actuelle](#analyse-implémentation)
2. [Comparaison avec standards eBay](#comparaison-standards)
3. [Incohérences identifiées](#incohérences)
4. [Fonctionnalités eBay non implémentées](#fonctionnalités-manquantes)
5. [Recommandations et roadmap](#recommandations)

---

## 1. 🔍 Analyse de l'implémentation actuelle

### ✅ Ce qui est bien implémenté

#### 1.1 OAuth2 Authentication Flow
**Status: ✅ CONFORME aux standards eBay**

Ton implémentation dans `api/ebay_oauth.py` :
- ✅ Utilise le flow "Authorization Code Grant" (user access tokens)
- ✅ Stocke access_token + refresh_token dans `platform_mappings`
- ✅ Gère les expiration timestamps (2h pour access, 18 mois pour refresh)
- ✅ CSRF protection via state parameter
- ✅ Support multi-marketplace (sandbox + production)

**Référence officielle:**
- [OAuth Best Practices](https://developer.ebay.com/api-docs/static/oauth-best-practices.html)
- [Authorization Code Grant Flow](https://developer.ebay.com/api-docs/static/oauth-authorization-code-grant.html)

**✨ Points forts:**
```python
# Bon: Génération state CSRF-safe
def generate_state(user_id: int) -> str:
    random_token = secrets.token_urlsafe(32)
    return f"{user_id}:{random_token}"

# Bon: Stockage sécurisé des tokens
platform_mapping.ebay_oauth_access_token = access_token
platform_mapping.ebay_oauth_refresh_token = refresh_token
platform_mapping.ebay_oauth_token_expires_at = access_token_expires_at
```

#### 1.2 Inventory API Client
**Status: ✅ CONFORME avec limitations**

Implémentation dans `services/ebay/ebay_inventory_client.py` :
- ✅ createOrReplaceInventoryItem
- ✅ getInventoryItem
- ✅ deleteInventoryItem
- ✅ bulkCreateOrReplaceInventoryItem
- ✅ createInventoryLocation
- ✅ getInventoryLocations

**Référence officielle:**
- [Inventory API Overview](https://developer.ebay.com/api-docs/sell/inventory/overview.html)
- [Inventory API Resources](https://developer.ebay.com/api-docs/sell/inventory/resources/methods)

#### 1.3 Offer API Client
**Status: ✅ CONFORME**

Implémentation dans `services/ebay/ebay_offer_client.py` :
- ✅ createOffer
- ✅ updateOffer
- ✅ publishOffer (renvoie listingId)
- ✅ withdrawOffer
- ✅ deleteOffer
- ✅ getOffers
- ✅ bulkPublishOffer
- ✅ bulkUpdatePriceQuantity

**Référence officielle:**
- [publishOffer Method](https://developer.ebay.com/api-docs/sell/inventory/resources/offer/methods/publishOffer)
- [Required fields for publishing](https://developer.ebay.com/api-docs/sell/static/inventory/publishing-offers.html)

#### 1.4 Account API Client
**Status: ✅ CONFORME**

Implémentation dans `services/ebay/ebay_account_client.py` :
- ✅ Business Policies (payment, fulfillment, return)
- ✅ getOptedInPrograms
- ✅ getAdvertisingEligibility

---

## 2. ⚖️ Comparaison avec standards eBay

### 2.1 Workflow de publication

**Standard eBay (documentation officielle):**
```
1. Opt-in to Business Policies ✅
2. Create Business Policies (Payment, Fulfillment, Return) ✅
3. Create Inventory Location ✅
4. Create/Update Inventory Item ✅
5. Create Offer (with policies + location) ✅
6. Publish Offer → get listingId ✅
```

**Ton implémentation (`EbayPublicationService.publish_product`):**
```python
# ✅ CONFORME - Suit le workflow officiel
1. Load Product from DB ✅
2. Generate SKU dérivé (product_id-marketplace_code) ✅
3. Get business policies from platform_mappings ✅
4. Convert Product → Inventory Item ✅
5. createOrReplaceInventoryItem ✅
6. createOffer with policies ✅
7. publishOffer → get listingId ✅
8. Save to ebay_products_marketplace ✅
```

**✅ Verdict: 100% conforme au workflow officiel**

### 2.2 Format des données

#### Inventory Item Structure

**Standard eBay:**
```json
{
  "product": {
    "title": "string (80 chars max)",
    "description": "string (HTML)",
    "aspects": { "Brand": ["Nike"], "Color": ["Black"] },
    "imageUrls": ["https://..."] // 12 max
  },
  "condition": "NEW_WITH_TAGS | USED_EXCELLENT | ...",
  "availability": {
    "shipToLocationAvailability": { "quantity": 1 }
  }
}
```

**Ton implémentation:**
```python
# ✅ CONFORME
inventory_item = {
    "product": {
        "title": title,  # ✅ Limité à 80 chars
        "description": description,  # ✅ HTML
        "aspects": aspects,  # ✅ Dict[str, List[str]]
        "imageUrls": image_urls  # ✅ List[str] (limité à 12)
    },
    "condition": self._map_condition(product.condition),  # ✅
    "availability": {
        "shipToLocationAvailability": { "quantity": product.stock_quantity or 1 }
    }
}
```

**✅ Verdict: Structure 100% conforme**

---

## 3. ⚠️ Incohérences identifiées

### 🔴 CRITIQUE - Incohérences à corriger immédiatement

#### 3.1 Token Refresh automatique manquant

**Problème:**
Selon la documentation eBay, les access tokens expirent après 2h. Tu stockes `ebay_oauth_token_expires_at` mais **tu ne gères PAS le refresh automatique** dans `EbayBaseClient`.

**Code actuel (`ebay_base_client.py`):**
```python
def get_access_token(self, scopes: List[str]) -> str:
    # ❌ PROBLÈME: Cache sans vérification expiration
    cache_key = tuple(sorted(scopes))
    if self.user_id in self._token_cache:
        cached = self._token_cache[self.user_id].get(cache_key)
        if cached:
            token, cached_time = cached
            if time.time() - cached_time < self._token_max_age:
                return token  # ❌ Retourne même si expiré selon eBay
```

**Solution recommandée:**
```python
def get_access_token(self, scopes: List[str]) -> str:
    """Get access token with automatic refresh if expired."""
    cache_key = tuple(sorted(scopes))

    # Check cache
    if self.user_id in self._token_cache:
        cached = self._token_cache[self.user_id].get(cache_key)
        if cached:
            token, cached_time = cached
            # ✅ Vérifier si expiré
            if time.time() - cached_time < self._token_max_age:
                return token

    # ✅ Check if DB token is still valid
    if self.platform_mapping.ebay_oauth_token_expires_at:
        now = datetime.now(timezone.utc)
        if self.platform_mapping.ebay_oauth_token_expires_at > now:
            # Token still valid, use it
            token = self.platform_mapping.ebay_oauth_access_token
            self._token_cache.setdefault(self.user_id, {})[cache_key] = (token, time.time())
            return token

    # ✅ Token expired, use refresh token
    return self._refresh_access_token(scopes)

def _refresh_access_token(self, scopes: List[str]) -> str:
    """Refresh access token using refresh_token grant."""
    if not self.platform_mapping.ebay_oauth_refresh_token:
        raise ValueError("No refresh token available. User needs to re-authenticate.")

    token_url = self.SANDBOX_TOKEN_URL if self.sandbox else self.TOKEN_URL

    data = {
        "grant_type": "refresh_token",
        "refresh_token": self.platform_mapping.ebay_oauth_refresh_token,
        "scope": " ".join(scopes)
    }

    response = requests.post(
        token_url,
        auth=(self.client_id, self.client_secret),
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    if not response.ok:
        raise RuntimeError(f"Token refresh failed: {response.text}")

    token_data = response.json()
    access_token = token_data["access_token"]
    expires_in = token_data["expires_in"]

    # Update DB
    from datetime import datetime, timedelta, timezone
    self.platform_mapping.ebay_oauth_access_token = access_token
    self.platform_mapping.ebay_oauth_token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    self.db.commit()

    # Update cache
    cache_key = tuple(sorted(scopes))
    self._token_cache.setdefault(self.user_id, {})[cache_key] = (access_token, time.time())

    return access_token
```

**Référence:** [OAuth Tokens Documentation](https://developer.ebay.com/api-docs/static/oauth-tokens.html)

---

#### 3.2 Aspects multilingues incomplets

**Problème:**
Tu as créé `aspect_mappings` avec traductions par marketplace (ebay_gb, ebay_fr, etc.) mais **tu ne les utilises PAS** dans `EbayProductConversionService._build_aspects()`.

**Code actuel:**
```python
def _build_aspects(self, product: Product, marketplace_id: str) -> Dict[str, List[str]]:
    """MVP: Aspects basiques en anglais (eBay GB format)."""
    aspects = {}

    # ❌ PROBLÈME: Toujours en anglais
    if product.brand:
        aspects["Brand"] = [product.brand]
    if product.color:
        aspects["Colour"] = [product.color]  # ❌ "Colour" uniquement pour GB
```

**Solution recommandée:**
```python
def _build_aspects(self, product: Product, marketplace_id: str) -> Dict[str, List[str]]:
    """Build aspects with marketplace-specific translations."""
    aspects = {}

    # ✅ Récupérer traductions depuis aspect_mappings
    marketplace_code = marketplace_id.split("_")[1].lower()  # EBAY_FR → fr

    # Brand (universel)
    if product.brand:
        aspect_key = self._get_aspect_name("brand", marketplace_code)
        aspects[aspect_key] = [product.brand]

    # Color
    if product.color:
        aspect_key = self._get_aspect_name("color", marketplace_code)
        aspects[aspect_key] = [product.color]

    # Size
    if product.label_size:
        aspect_key = self._get_aspect_name("size", marketplace_code)
        aspects[aspect_key] = [product.label_size]

    return aspects

def _get_aspect_name(self, aspect_key: str, marketplace_code: str) -> str:
    """Get localized aspect name from aspect_mappings table."""
    from models.public.ebay_aspect_mapping import AspectMapping

    mapping = self.db.query(AspectMapping).filter(
        AspectMapping.aspect_key == aspect_key
    ).first()

    if not mapping:
        # Fallback to English
        return aspect_key.title()

    # Get marketplace-specific translation
    field_name = f"ebay_{marketplace_code}"
    return getattr(mapping, field_name, aspect_key.title())
```

---

#### 3.3 Category ID fallback dangereux

**Problème:**
```python
# ❌ DANGEREUX
"categoryId": category_id or "11450"  # Fallback: T-shirts homme
```

Si `category_id` est None, tu publies **tous les produits en T-shirts homme** (catégorie 11450) même si c'est une robe ou un pantalon !

**Solution recommandée:**
```python
def create_offer_data(self, ..., category_id: Optional[str] = None) -> Dict[str, Any]:
    # ✅ Lever une erreur si category_id manquant
    if not category_id:
        raise ProductValidationError(
            "category_id is required for publishing. "
            "Use eBay Taxonomy API to find the correct category for this product."
        )

    offer_data = {
        ...
        "categoryId": category_id,  # ✅ Pas de fallback
        ...
    }
```

---

### 🟡 MOYEN - Améliorations recommandées

#### 3.4 Images publiques requises

**Standard eBay:**
> "This array is required and **at least one image URL must be specified** before an offer can be published."

**Code actuel:**
```python
def _get_image_urls(self, product: Product) -> List[str]:
    # ⚠️ PROBLÈME: Peut retourner []
    if product.images:
        try:
            images = json.loads(product.images)
            if isinstance(images, list):
                return images[:12]
        except Exception:
            pass
    return []  # ❌ Liste vide = échec publication
```

**Solution:**
```python
def _get_image_urls(self, product: Product) -> List[str]:
    """Get product images with validation."""
    images = []

    if product.images:
        try:
            parsed = json.loads(product.images)
            if isinstance(parsed, list):
                # Filter valid URLs
                images = [url for url in parsed if url.startswith("http")][:12]
        except Exception:
            pass

    # ✅ Valider qu'on a au moins 1 image
    if not images:
        raise ProductValidationError(
            f"Product {product.id} must have at least one public image URL. "
            "Upload images and store URLs in product.images field."
        )

    return images
```

---

#### 3.5 GPSR (General Product Safety Regulation) - Nouveau depuis Dec 2024

**⚠️ IMPORTANT:** Depuis le 13 décembre 2024, l'UE impose de fournir des informations GPSR pour les produits vendus dans l'UE.

**Documentation:** [Inventory API Release Notes](https://developer.ebay.com/api-docs/sell/inventory/release-notes.html)

**Ce qui manque:**
```python
# ❌ Pas de support GPSR dans ton code actuel
inventory_item = {
    "product": {
        "title": "...",
        "description": "...",
        # ❌ Manque: productSafetyInformation pour EU
    }
}
```

**Solution recommandée (pour Phase 2):**
```python
# ✅ Ajouter support GPSR
inventory_item = {
    "product": {
        ...
        # Pour marketplaces EU (FR, DE, IT, ES, NL, BE, PL)
        "productSafetyInformation": {
            "component": "Product Safety Information",
            "pictograms": ["..."],  # URLs des pictogrammes
            "statements": ["Keep away from children"],
            "dangerousGoods": {
                "unNumber": "UN1234",
                "hazmatSignalWord": "WARNING"
            }
        }
    }
}
```

---

## 4. 🚀 Fonctionnalités eBay non implémentées

### 4.1 Fulfillment API (Gestion des commandes)

**Status: ❌ NON IMPLÉMENTÉ**

**Ce qu'eBay propose:**
- Récupérer les commandes (getOrders)
- Mettre à jour le statut d'expédition (shipment tracking)
- Gérer les retours (returns)
- Traiter les annulations (cancellations)

**Référence:** [Fulfillment API Documentation](https://developer.ebay.com/api-docs/sell/fulfillment/overview.html)

**Implémentation recommandée:**
```python
# services/ebay/ebay_fulfillment_client.py

class EbayFulfillmentClient(EbayBaseClient):
    """Client pour eBay Fulfillment API (orders management)."""

    ORDERS_URL = "/sell/fulfillment/v1/order"

    def get_orders(
        self,
        filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get orders.

        filter examples:
        - "orderfulfillmentstatus:{IN_PROGRESS|FULFILLED}"
        - "creationdate:[2024-01-01T00:00:00.000Z..2024-12-31T23:59:59.999Z]"
        """
        params = {"limit": limit, "offset": offset}
        if filter:
            params["filter"] = filter

        return self.api_call("GET", self.ORDERS_URL, params=params)

    def add_shipping_info(
        self,
        order_id: str,
        shipment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add tracking number and mark order as shipped.

        shipment_data = {
            "shippingCarrierCode": "USPS",
            "trackingNumber": "1234567890",
            "lineItems": [{"lineItemId": "12345678901"}]
        }
        """
        return self.api_call(
            "POST",
            f"{self.ORDERS_URL}/{order_id}/shipping_fulfillment",
            json_data=shipment_data
        )
```

**Cas d'usage:** Synchronisation commandes eBay → Stoflow pour gestion stocks

---

### 4.2 Marketing API (Promoted Listings)

**Status: ⚠️ PARTIELLEMENT IMPLÉMENTÉ**

Tu as `getAdvertisingEligibility` dans `EbayAccountClient` mais **pas de création de campagnes**.

**Ce qu'eBay propose:**
- Créer des campagnes Promoted Listings (CPS ou CPC)
- Ajouter des produits à des campagnes
- Gérer les budgets et ad rates
- Récupérer les rapports de performance

**Référence:**
- [Marketing API Overview](https://developer.ebay.com/api-docs/sell/marketing/overview.html)
- [Promoted Listings Reports](https://developer.ebay.com/api-docs/sell/static/marketing/pl-reports.html)

**Implémentation recommandée:**
```python
# services/ebay/ebay_marketing_client.py

class EbayMarketingClient(EbayBaseClient):
    """Client pour eBay Marketing API (Promoted Listings)."""

    CAMPAIGN_URL = "/sell/marketing/v1/ad_campaign"
    AD_URL = "/sell/marketing/v1/ad"
    REPORT_URL = "/sell/marketing/v1/ad_report"

    def create_campaign(
        self,
        campaign_name: str,
        marketplace_id: str,
        funding_strategy: str = "COST_PER_SALE"  # ou "COST_PER_CLICK"
    ) -> Dict[str, Any]:
        """
        Create Promoted Listings campaign.

        funding_strategy:
        - COST_PER_SALE (CPS) = pay % on sale
        - COST_PER_CLICK (CPC) = pay per click
        """
        data = {
            "campaignName": campaign_name,
            "marketplaceId": marketplace_id,
            "fundingStrategy": funding_strategy,
            "campaignStatus": "RUNNING"
        }

        return self.api_call("POST", self.CAMPAIGN_URL, json_data=data)

    def add_items_to_campaign(
        self,
        campaign_id: str,
        inventory_references: List[Dict[str, str]],  # [{"inventoryReferenceId": "SKU", "inventoryReferenceType": "INVENTORY_ITEM"}]
        ad_rate: str  # "5.0" = 5% commission
    ) -> Dict[str, Any]:
        """Add products to Promoted Listings campaign."""
        data = {
            "bidPercentage": ad_rate,
            "inventoryReferences": inventory_references
        }

        return self.api_call(
            "POST",
            f"{self.CAMPAIGN_URL}/{campaign_id}/bulk_create_ads_by_inventory_reference",
            json_data=data
        )

    def get_campaign_report(
        self,
        campaign_ids: List[str],
        date_from: str,  # "2024-12-01"
        date_to: str,     # "2024-12-31"
        report_type: str = "CAMPAIGN_PERFORMANCE_REPORT"
    ) -> Dict[str, Any]:
        """Get Promoted Listings performance report."""
        data = {
            "campaignIds": campaign_ids,
            "dateFrom": date_from,
            "dateTo": date_to,
            "reportType": report_type,
            "dimensions": ["campaign_id"],
            "metrics": ["CLICK", "IMPRESSION", "SALE", "SPEND"]
        }

        # Create report task
        task_response = self.api_call(
            "POST",
            f"{self.REPORT_URL}_task",
            json_data=data
        )

        report_task_id = task_response["reportTaskId"]

        # Get report (will be PENDING initially)
        return self.api_call("GET", f"{self.REPORT_URL}_task/{report_task_id}")
```

**Cas d'usage:** Promotion automatique des nouveaux produits avec budget défini

---

### 4.3 Analytics API (Métriques de performance)

**Status: ❌ NON IMPLÉMENTÉ**

**Ce qu'eBay propose:**
- Traffic reports (impressions, views, click-through rate)
- Sales conversion rate
- Customer service metrics
- Seller standards profile

**Référence:**
- [Analytics API Overview](https://developer.ebay.com/api-docs/sell/analytics/overview.html)
- [Traffic Report Documentation](https://developer.ebay.com/api-docs/sell/static/performance/traffic-report.html)

**Implémentation recommandée:**
```python
# services/ebay/ebay_analytics_client.py

class EbayAnalyticsClient(EbayBaseClient):
    """Client pour eBay Analytics API (performance metrics)."""

    TRAFFIC_REPORT_URL = "/sell/analytics/v1/traffic_report"

    def get_traffic_report(
        self,
        marketplace_id: str,
        date_from: str,  # "2024-12-01"
        date_to: str,    # "2024-12-31"
        dimension: str = "DAY",  # DAY | WEEK | MONTH
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get traffic report for seller's listings.

        Available metrics:
        - LISTING_IMPRESSION_SEARCH_RESULTS_PAGE
        - LISTING_IMPRESSION_STORE
        - LISTING_VIEWS_TOTAL
        - SALES_CONVERSION_RATE
        - CLICK_THROUGH_RATE
        """
        if metrics is None:
            metrics = [
                "LISTING_IMPRESSION_SEARCH_RESULTS_PAGE",
                "LISTING_VIEWS_TOTAL",
                "SALES_CONVERSION_RATE"
            ]

        filter_query = f"marketplace_ids:{{{marketplace_id}}},date_range:[{date_from}..{date_to}]"

        params = {
            "filter": filter_query,
            "dimension": dimension,
            "metric": ",".join(metrics)
        }

        return self.api_call("GET", self.TRAFFIC_REPORT_URL, params=params)
```

**Cas d'usage:** Dashboard analytics dans Stoflow avec KPIs eBay

---

### 4.4 Notification API (Webhooks)

**Status: ❌ NON IMPLÉMENTÉ**

**Ce qu'eBay propose:**
- Notifications en temps réel pour:
  - Nouvelles commandes (ORDER.COMPLETED)
  - Paiements reçus (PAYMENT.RECEIVED)
  - Retours/litiges (RETURN.INITIATED)
  - Changements de stock (INVENTORY.QUANTITY_CHANGED)

**Référence:** [Notification API Overview](https://developer.ebay.com/api-docs/commerce/notification/overview.html)

**Implémentation recommandée:**
```python
# services/ebay/ebay_notification_client.py

class EbayNotificationClient(EbayBaseClient):
    """Client pour eBay Notification API (webhooks)."""

    DESTINATION_URL = "/commerce/notification/v1/destination"
    SUBSCRIPTION_URL = "/commerce/notification/v1/subscription"

    def create_webhook_destination(
        self,
        name: str,
        destination_url: str  # "https://stoflow.com/api/webhooks/ebay"
    ) -> Dict[str, Any]:
        """Create webhook destination endpoint."""
        data = {
            "name": name,
            "endpoint": destination_url,
            "status": "ENABLED",
            "verificationToken": secrets.token_urlsafe(32)
        }

        return self.api_call("POST", self.DESTINATION_URL, json_data=data)

    def subscribe_to_topic(
        self,
        destination_id: str,
        topic_id: str  # "MARKETPLACE_ACCOUNT_DELETION" | "ORDER.COMPLETED" | ...
    ) -> Dict[str, Any]:
        """Subscribe to notification topic."""
        data = {
            "destinationId": destination_id,
            "topicId": topic_id,
            "status": "ENABLED"
        }

        return self.api_call("POST", self.SUBSCRIPTION_URL, json_data=data)

# api/webhooks.py (nouveau fichier)

@router.post("/webhooks/ebay")
async def ebay_webhook_handler(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle eBay webhook notifications.

    Example payload:
    {
      "topic": "ORDER.COMPLETED",
      "data": { "orderId": "12345", "buyer": {...}, "lineItems": [...] }
    }
    """
    payload = await request.json()

    # Verify signature
    signature = request.headers.get("X-EBAY-SIGNATURE")
    # ... verify with public key

    topic = payload.get("topic")

    if topic == "ORDER.COMPLETED":
        # Create order in Stoflow
        order_data = payload["data"]
        # ... process order

    elif topic == "INVENTORY.QUANTITY_CHANGED":
        # Update stock
        # ...

    return {"status": "received"}
```

**Cas d'usage:** Synchronisation automatique commandes/stocks sans polling

---

### 4.5 Taxonomy API (Catégories & Aspects)

**Status: ❌ NON IMPLÉMENTÉ**

**Ce qu'eBay propose:**
- Récupérer l'arbre des catégories par marketplace
- Trouver la catégorie suggérée pour un produit
- Récupérer les aspects requis/recommandés par catégorie
- Valider les valeurs d'aspects

**Référence:** [Taxonomy API Documentation](https://developer.ebay.com/api-docs/commerce/taxonomy/overview.html)

**Implémentation recommandée:**
```python
# services/ebay/ebay_taxonomy_client.py

class EbayTaxonomyClient(EbayBaseClient):
    """Client pour eBay Taxonomy API (categories & aspects)."""

    BASE_URL = "https://api.ebay.com/commerce/taxonomy/v1"

    def get_category_suggestions(
        self,
        q: str,  # "Nike Air Max shoes"
        marketplace_id: str = "EBAY_US"
    ) -> Dict[str, Any]:
        """
        Get suggested category for a product.

        Returns:
        {
          "categorySuggestions": [
            {
              "category": {
                "categoryId": "11450",
                "categoryName": "Athletic Shoes"
              },
              "categoryTreeNodeLevel": 3,
              "relevancy": "EXACT"
            }
          ]
        }
        """
        url = f"{self.BASE_URL}/category_tree/{marketplace_id}/get_category_suggestions"
        params = {"q": q}

        return self.api_call("GET", url, params=params, use_commerce_api=True)

    def get_item_aspects_for_category(
        self,
        category_id: str,
        marketplace_id: str = "EBAY_US"
    ) -> Dict[str, Any]:
        """
        Get required/recommended aspects for a category.

        Returns:
        {
          "aspects": [
            {
              "localizedAspectName": "Brand",
              "aspectConstraint": {
                "aspectRequired": true,
                "aspectDataType": "STRING",
                "aspectMode": "FREE_TEXT"
              },
              "aspectValues": [...]
            }
          ]
        }
        """
        url = f"{self.BASE_URL}/category_tree/{marketplace_id}/get_item_aspects_for_category"
        params = {"category_id": category_id}

        return self.api_call("GET", url, params=params, use_commerce_api=True)
```

**Cas d'usage:** Auto-suggestion catégorie + validation aspects avant publication

---

### 4.6 Inventory Item Groups (Variations multi-SKU)

**Status: ❌ NON IMPLÉMENTÉ**

**Ce qu'eBay propose:**
- Grouper plusieurs SKU en 1 listing (ex: T-shirt S/M/L)
- Gérer les variations (Size, Color, etc.)
- Publier tous les SKU d'un groupe en 1 seul appel

**Référence:** [Inventory Item Groups Documentation](https://developer.ebay.com/api-docs/sell/inventory/resources/inventory_item_group/methods/createOrReplaceInventoryItemGroup)

**Implémentation recommandée:**
```python
# services/ebay/ebay_inventory_client.py (ajouter)

def create_inventory_item_group(
    self,
    inventory_item_group_key: str,  # "nike-air-max-group"
    group_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create multi-variation listing.

    group_data = {
      "aspects": {
        "Brand": ["Nike"],
        "Type": ["Athletic Shoes"]
      },
      "title": "Nike Air Max",
      "description": "...",
      "imageUrls": ["..."],
      "variantSKUs": ["nike-air-max-S", "nike-air-max-M", "nike-air-max-L"],
      "variesBy": {
        "specifications": [
          {"name": "Size", "values": ["S", "M", "L"]}
        ]
      }
    }
    """
    url = f"{self.INVENTORY_ITEM_URL}_group/{inventory_item_group_key}"
    return self.api_call("PUT", url, json_data=group_data)
```

**Cas d'usage:** Produits avec variations (tailles, couleurs)

---

## 5. 📋 Recommandations & Roadmap

### Phase 1 (URGENT - À faire maintenant)

#### ✅ 1.1 Token refresh automatique
**Priorité: 🔴 CRITIQUE**

- Implémenter `_refresh_access_token()` dans `EbayBaseClient`
- Ajouter vérification expiration dans `get_access_token()`
- **Estimation:** 2-3 heures
- **Fichier:** `services/ebay/ebay_base_client.py`

#### ✅ 1.2 Validation images requises
**Priorité: 🔴 CRITIQUE**

- Lever `ProductValidationError` si aucune image
- **Estimation:** 30 min
- **Fichier:** `services/ebay/ebay_product_conversion_service.py`

#### ✅ 1.3 Supprimer fallback categoryId
**Priorité: 🔴 CRITIQUE**

- Lever erreur si `category_id` manquant
- **Estimation:** 15 min
- **Fichier:** `services/ebay/ebay_product_conversion_service.py`

#### ✅ 1.4 Aspects multilingues
**Priorité: 🟡 IMPORTANT**

- Implémenter `_get_aspect_name()` avec `aspect_mappings`
- **Estimation:** 1-2 heures
- **Fichier:** `services/ebay/ebay_product_conversion_service.py`

---

### Phase 2 (Court terme - 1-2 semaines)

#### 🚀 2.1 Fulfillment API (Orders)
**Priorité: 🟢 HAUTE**

**Fonctionnalités:**
- Récupération commandes automatique (polling ou webhooks)
- Synchronisation stocks Stoflow ↔ eBay
- Gestion tracking numbers

**Fichiers à créer:**
- `services/ebay/ebay_fulfillment_client.py`
- `api/ebay_orders.py`
- `models/user/ebay_order.py` (✅ existe déjà)

**Estimation:** 5-7 jours

---

#### 🚀 2.2 Marketing API (Promoted Listings)
**Priorité: 🟢 HAUTE**

**Fonctionnalités:**
- Création campagnes automatiques
- Ajout produits à campagnes avec % commission
- Rapports performance

**Fichiers à créer:**
- `services/ebay/ebay_marketing_client.py`
- `api/ebay_marketing.py`
- `models/user/ebay_promoted_listing.py` (✅ existe déjà)

**Estimation:** 3-5 jours

---

#### 🚀 2.3 Taxonomy API (Smart category suggestions)
**Priorité: 🟡 MOYENNE**

**Fonctionnalités:**
- Auto-suggestion catégorie basée sur titre/description
- Validation aspects avant publication
- Cache des catégories populaires

**Fichiers à créer:**
- `services/ebay/ebay_taxonomy_client.py`
- `api/ebay_taxonomy.py`

**Estimation:** 2-3 jours

---

### Phase 3 (Moyen terme - 1 mois)

#### 🚀 3.1 Notification API (Webhooks temps réel)
**Priorité: 🟡 MOYENNE**

**Fonctionnalités:**
- Webhook endpoint pour notifications eBay
- Gestion événements: ORDER.COMPLETED, RETURN.INITIATED, etc.
- Signature verification

**Fichiers à créer:**
- `services/ebay/ebay_notification_client.py`
- `api/webhooks.py`

**Estimation:** 3-4 jours

---

#### 🚀 3.2 Analytics API (Dashboard metrics)
**Priorité: 🟢 HAUTE pour business insights**

**Fonctionnalités:**
- Traffic reports (impressions, views, CTR)
- Sales conversion rate
- Dashboard Stoflow avec KPIs eBay

**Fichiers à créer:**
- `services/ebay/ebay_analytics_client.py`
- `api/ebay_analytics.py`

**Estimation:** 4-5 jours

---

#### 🚀 3.3 Inventory Item Groups (Variations)
**Priorité: 🟡 MOYENNE**

**Fonctionnalités:**
- Support multi-SKU (tailles, couleurs)
- Gestion variations dans Stoflow
- Publication groupée

**Fichiers à créer:**
- Étendre `EbayInventoryClient`
- Modifier `Product` model pour variations

**Estimation:** 5-7 jours

---

### Phase 4 (Long terme - 3-6 mois)

#### 🚀 4.1 GPSR Compliance (EU)
**Priorité: 🔴 OBLIGATOIRE pour EU**

**Fonctionnalités:**
- Formulaire GPSR dans Stoflow
- Stockage info sécurité produits
- Génération pictogrammes

**Estimation:** 7-10 jours

---

#### 🚀 4.2 Best Offer automation
**Priorité: 🟡 BASSE**

**Fonctionnalités:**
- Configuration règles auto-accept/decline
- Historique négociations
- A/B testing prix

**Estimation:** 3-4 jours

---

#### 🚀 4.3 Bulk operations optimization
**Priorité: 🟢 PERFORMANCE**

**Fonctionnalités:**
- Queuing system (Celery/RQ)
- Batch updates (100+ produits)
- Progress tracking

**Estimation:** 5-7 jours

---

## 📊 Résumé exécutif

### ✅ Forces de l'implémentation actuelle

1. ✅ Architecture propre (clients séparés par API)
2. ✅ OAuth2 flow conforme aux standards
3. ✅ Workflow publication correct (Inventory → Offer → Publish)
4. ✅ Support multi-marketplace (8 marketplaces)
5. ✅ Token caching pour performance
6. ✅ Business policies intégrées
7. ✅ Tables base de données bien structurées

### ⚠️ Incohérences critiques

1. 🔴 Token refresh automatique manquant
2. 🔴 Validation images insuffisante
3. 🔴 Fallback categoryId dangereux
4. 🟡 Aspects multilingues non utilisés

### 🚀 Opportunités (fonctionnalités manquantes)

1. **Fulfillment API** - Gestion commandes (HIGH)
2. **Marketing API** - Promoted Listings (HIGH)
3. **Taxonomy API** - Smart categorization (MEDIUM)
4. **Notification API** - Webhooks temps réel (MEDIUM)
5. **Analytics API** - Dashboard KPIs (HIGH)
6. **Inventory Groups** - Multi-variation (MEDIUM)

---

## 📚 Sources officielles eBay

### Documentation Principale
- [Inventory API Overview](https://developer.ebay.com/api-docs/sell/inventory/overview.html)
- [OAuth Best Practices](https://developer.ebay.com/api-docs/static/oauth-best-practices.html)
- [Required fields for publishing](https://developer.ebay.com/api-docs/sell/static/inventory/publishing-offers.html)

### APIs Non Implémentées
- [Fulfillment API](https://developer.ebay.com/api-docs/sell/fulfillment/overview.html)
- [Marketing API](https://developer.ebay.com/api-docs/sell/marketing/overview.html)
- [Analytics API](https://developer.ebay.com/api-docs/sell/analytics/overview.html)
- [Notification API](https://developer.ebay.com/api-docs/commerce/notification/overview.html)
- [Taxonomy API](https://developer.ebay.com/api-docs/commerce/taxonomy/overview.html)

### Release Notes & Updates
- [Inventory API Release Notes](https://developer.ebay.com/api-docs/sell/inventory/release-notes.html) (GPSR Dec 2024)
- [Marketing API Release Notes](https://developer.ebay.com/api-docs/sell/marketing/static/release-notes.html) (Offsite Ads 2025)

---

**Fin du rapport** 📊
