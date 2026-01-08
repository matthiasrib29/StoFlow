# Marketplace Publication Handlers

Système de handlers génériques pour la publication de produits sur toutes les marketplaces (Vinted, eBay, Etsy).

## Architecture

```
BasePublishHandler (abstract)
├── VintedPublishHandler
├── EbayPublishHandler
└── EtsyPublishHandler
```

## Fonctionnalités

- ✅ **Idempotence** : Évite les doubles publications via `idempotency_key`
- ✅ **Upload photos** : Avec tracking et logging des orphelines
- ✅ **Validation produit** : Commune à toutes les marketplaces
- ✅ **Logging structuré** : Avec contexte marketplace/job
- ✅ **Gestion erreurs** : Cleanup automatique en cas d'échec

## Usage

### 1. Créer un MarketplaceJob

```python
from models.user.marketplace_job import MarketplaceJob, JobStatus
from uuid import uuid4

# Générer clé d'idempotence (côté frontend ou backend)
idempotency_key = f"pub_{product_id}_{uuid4().hex[:16]}"

# Créer job
job = MarketplaceJob(
    marketplace="vinted",  # ou "ebay", "etsy"
    product_id=product_id,
    action_type_id=1,  # ID de l'action "publish"
    idempotency_key=idempotency_key,
    status=JobStatus.PENDING,
    input_data={
        # Vinted: pas de params requis
        # eBay: {"marketplace_id": "EBAY_FR", "category_id": "optional"}
        # Etsy: {"taxonomy_id": 1234, "shipping_profile_id": 5678, "state": "active"}
    }
)
db.add(job)
db.commit()
```

### 2. Exécuter avec le bon handler

#### Vinted

```python
from services.marketplace.handlers.vinted.publish_handler import VintedPublishHandler

handler = VintedPublishHandler(db, job_id=job.id, user_id=user_id)
result = await handler.execute()

# result = {
#     "success": True,
#     "listing_id": "123456789",
#     "url": "https://www.vinted.fr/items/123456789",
#     "photo_ids": [111, 222, 333],
#     "price": 29.99,
#     "title": "Nike Air Max..."
# }
```

#### eBay

```python
from services.marketplace.handlers.ebay.publish_handler import EbayPublishHandler

# Input data requis
job.input_data = {
    "marketplace_id": "EBAY_FR",
    "category_id": "12345"  # optionnel
}

handler = EbayPublishHandler(db, job_id=job.id, user_id=user_id)
result = await handler.execute()

# result = {
#     "success": True,
#     "listing_id": "123456789012",
#     "url": "https://www.ebay.fr/itm/123456789012",
#     "offer_id": "987654321",
#     "sku_derived": "1234-FR",
#     "marketplace_id": "EBAY_FR"
# }
```

#### Etsy

```python
from services.marketplace.handlers.etsy.publish_handler import EtsyPublishHandler

# Input data requis
job.input_data = {
    "taxonomy_id": 1234,
    "shipping_profile_id": 5678,
    "return_policy_id": 9012,  # optionnel
    "shop_section_id": 3456,   # optionnel
    "state": "active"  # "draft" ou "active"
}

handler = EtsyPublishHandler(db, job_id=job.id, user_id=user_id)
result = await handler.execute()

# result = {
#     "success": True,
#     "listing_id": "123456789",
#     "url": "https://www.etsy.com/listing/123456789",
#     "state": "active"
# }
```

### 3. Gestion de l'idempotence

```python
# Premier appel
handler1 = VintedPublishHandler(db, job_id=job1.id, user_id=user_id)
result1 = await handler1.execute()
# → Crée le listing

# Deuxième appel avec MÊME idempotency_key
job2 = MarketplaceJob(
    idempotency_key="pub_123_abc123",  # MÊME clé
    product_id=product_id,
    ...
)
handler2 = VintedPublishHandler(db, job_id=job2.id, user_id=user_id)
result2 = await handler2.execute()
# → Retourne result1 en cache (pas de nouvelle publication)

# result2 = {
#     "success": True,
#     "cached": True,  # ← Indique cache hit
#     ...mêmes données que result1
# }
```

### 4. Gestion des erreurs

```python
try:
    result = await handler.execute()
except ConflictError:
    # Publication déjà en cours
    print("Veuillez attendre la fin de la publication en cours")
except ValidationError as e:
    # Produit invalide
    print(f"Erreur de validation: {e}")
except Exception as e:
    # Autre erreur
    print(f"Erreur lors de la publication: {e}")

    # Si échec après upload de photos, les photo_ids sont loggés:
    # 🚨 PARTIAL FAILURE: 3 orphaned photos (product_id=123, photo_ids=[111, 222, 333])
```

## Tests

### Test idempotence

```python
def test_idempotence():
    # Créer job 1
    job1 = create_job(idempotency_key="test_key_1")
    result1 = await handler1.execute()

    # Créer job 2 avec MÊME clé
    job2 = create_job(idempotency_key="test_key_1")
    result2 = await handler2.execute()

    # Vérifier cache hit
    assert result2["cached"] == True
    assert result1["listing_id"] == result2["listing_id"]

    # Vérifier 1 seul listing créé
    listings = db.query(VintedProduct).filter_by(product_id=product_id).all()
    assert len(listings) == 1
```

### Test photos orphelines

```python
def test_orphaned_photos_logging(caplog):
    # Mocker échec après upload photo 2
    with patch("handler._create_listing", side_effect=Exception("API Error")):
        try:
            await handler.execute()
        except Exception:
            pass

    # Vérifier log contient photo_ids
    assert "PARTIAL FAILURE" in caplog.text
    assert "photo_ids=[111, 222]" in caplog.text
```

## Migration depuis VintedJob

### Ancien code (VintedJob)

```python
from services.vinted.vinted_job_service import VintedJobService

job_service = VintedJobService(db)
job = job_service.create_job(
    action_code="publish",
    product_id=product_id
)
processor = VintedJobProcessor(db, shop_id=connection.vinted_user_id)
result = await processor._execute_job(job)
```

### Nouveau code (MarketplaceJob)

```python
from services.marketplace.handlers.vinted.publish_handler import VintedPublishHandler

# Créer MarketplaceJob
job = MarketplaceJob(
    marketplace="vinted",
    product_id=product_id,
    action_type_id=1,  # publish
    idempotency_key=f"pub_{product_id}_{uuid4().hex[:16]}",
    status=JobStatus.PENDING
)
db.add(job)
db.commit()

# Exécuter
handler = VintedPublishHandler(db, job_id=job.id, user_id=user_id)
result = await handler.execute()
```

## Notes de sécurité

- ✅ `idempotency_key` est **UNIQUE** en DB (index partiel)
- ✅ Validation produit **AVANT** toute action externe
- ✅ Logs **structurés** avec contexte complet
- ✅ Photos orphelines **loggées** pour cleanup manuel
- ✅ Exceptions **typées** (ConflictError, ValidationError)

## Fichiers modifiés (Security Audit 2)

- ✅ `models/user/marketplace_job.py` : Ajout `idempotency_key`
- ✅ `migrations/versions/20260108_1640_add_idempotency_key_to_marketplace_jobs.py`
- ✅ `services/marketplace/handlers/base_publish_handler.py` (nouveau)
- ✅ `services/marketplace/handlers/vinted/publish_handler.py` (nouveau)
- ✅ `services/marketplace/handlers/ebay/publish_handler.py` (nouveau)
- ✅ `services/marketplace/handlers/etsy/publish_handler.py` (nouveau)
