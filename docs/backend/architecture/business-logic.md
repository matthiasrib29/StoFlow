# Business Logic Stoflow Backend

**Version:** 1.0
**Dernière mise à jour:** 2025-12-08

---

## 🎯 Vue d'ensemble

Ce document décrit toutes les règles métier critiques, validations, et contraintes business du système Stoflow.

---

## 📦 Cycle de Vie d'un Produit

### Statuts Disponibles (MVP)

```python
class ProductStatus(str, Enum):
    DRAFT = "draft"           # Brouillon (non visible)
    PUBLISHED = "published"   # Publié (visible sur marketplaces)
    SOLD = "sold"            # Vendu (transaction complétée)
    ARCHIVED = "archived"    # Archivé (terminal, non modifiable)
```

### Diagramme de Transitions

```
┌──────┐
│DRAFT │ (Création initiale)
└──┬───┘
   │
   │ (Publication autorisée si stock > 0)
   ▼
┌───────────┐
│ PUBLISHED │ (Visible sur marketplaces)
└─────┬─────┘
      │
      ├─────► SOLD (Vendu)
      │
      └─────► ARCHIVED (Archivé)

SOLD ─────► ARCHIVED (Optionnel)
```

### Règles de Transition

#### ✅ Transitions Autorisées

| De | Vers | Conditions |
|----|------|------------|
| `DRAFT` | `PUBLISHED` | `stock_quantity > 0` |
| `PUBLISHED` | `SOLD` | Aucune |
| `PUBLISHED` | `ARCHIVED` | Aucune |
| `SOLD` | `ARCHIVED` | Aucune |

#### ❌ Transitions Interdites

- `ARCHIVED` → Toute autre état (état terminal)
- `DRAFT` → `SOLD` (doit passer par `PUBLISHED`)
- `DRAFT` → `ARCHIVED` (doit passer par `PUBLISHED`)
- `SOLD` → `DRAFT` (irréversible)
- `SOLD` → `PUBLISHED` (irréversible)

### Validation des Transitions

**Localisation:** `services/product_service.py:validate_status_transition()`

```python
VALID_TRANSITIONS = {
    ProductStatus.DRAFT: {ProductStatus.PUBLISHED},
    ProductStatus.PUBLISHED: {ProductStatus.SOLD, ProductStatus.ARCHIVED},
    ProductStatus.SOLD: {ProductStatus.ARCHIVED},
    ProductStatus.ARCHIVED: set(),  # Terminal state
}

def validate_status_transition(current_status: str, new_status: str) -> bool:
    """
    Valide qu'une transition de statut est autorisée.

    Business Rule (Updated: 2025-12-07):
    - ARCHIVED est un état terminal, aucune transition sortante autorisée
    - DRAFT peut seulement aller vers PUBLISHED (avec stock > 0)
    - PUBLISHED peut aller vers SOLD ou ARCHIVED
    - SOLD peut seulement aller vers ARCHIVED
    """
    if current_status == new_status:
        return True

    current = ProductStatus(current_status)
    new = ProductStatus(new_status)

    return new in VALID_TRANSITIONS.get(current, set())
```

---

## 🚫 Soft Delete & Produits Supprimés

### Principe

Les produits ne sont **jamais** physiquement supprimés de la base de données. Ils sont marqués comme supprimés via le champ `deleted_at`.

**Localisation:** `models/user/product.py`

```python
class Product(Base):
    # ...
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
```

### Règles de Soft Delete

#### ✅ Comportement Attendu

1. **Exclusion automatique des queries:**
   - Tous les produits avec `deleted_at IS NOT NULL` doivent être exclus
   - Filtrage appliqué à TOUTES les queries (list, get, update, delete)

2. **Protection contre modification:**
   - ❌ Impossible de modifier un produit supprimé
   - ❌ Impossible de publier un produit supprimé
   - ❌ Impossible de changer le statut d'un produit supprimé

3. **Cascade sur images:**
   - Quand un produit est soft-deleted, toutes ses images doivent être marquées `deleted_at`

#### 🔧 Implémentation

**Service Layer:** `services/product_service.py`

```python
def get_all_products(db: Session, tenant_id: int, status: Optional[str] = None):
    """
    Récupère tous les produits (NON supprimés).

    Business Rule (Updated: 2025-12-07):
    - Exclut automatiquement les produits avec deleted_at IS NOT NULL
    """
    query = db.query(Product).filter(Product.deleted_at.is_(None))

    if status:
        query = query.filter(Product.status == status)

    return query.all()

def soft_delete_product(db: Session, product_id: int, tenant_id: int):
    """
    Supprime logiquement un produit et ses images.

    Business Rule (Updated: 2025-12-07):
    - Marque deleted_at sur le produit
    - Marque deleted_at sur TOUTES les images associées (CASCADE)
    """
    product = get_product_by_id(db, product_id, tenant_id)

    if not product:
        raise HTTPException(404, "Product not found")

    if product.is_deleted:
        raise HTTPException(400, "Product already deleted")

    # Soft delete du produit
    product.deleted_at = datetime.now(timezone.utc)

    # Soft delete des images (CASCADE)
    db.query(ProductImage)\
        .filter(ProductImage.product_id == product_id)\
        .update({"deleted_at": datetime.now(timezone.utc)})

    db.commit()
```

---

## 📸 Gestion des Images

### Contraintes Images

**Localisation:** `models/user/product_image.py`

```python
class ProductImage(Base):
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    image_path = Column(String(500), nullable=False)
    display_order = Column(Integer, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### Règles Business

#### ✅ Validation Obligatoire

1. **Foreign Key Validation:**
   - `product_id` doit exister dans la table `products`
   - Le produit référencé ne doit PAS être soft-deleted

2. **Display Order:**
   - Doit être >= 1
   - Pas de doublons pour un même produit
   - Doit être séquentiel (1, 2, 3, ...)

3. **Image Path:**
   - Doit être non vide
   - Doit pointer vers un fichier existant
   - Format: `uploads/{tenant_id}/{product_id}/{filename}`

4. **Soft Delete Cascade:**
   - Quand un produit est soft-deleted, TOUTES ses images le sont aussi
   - Les images orphelines (product_id inexistant ou deleted) sont invalides

#### 🔧 Validation Service

**Localisation:** `services/product_service.py`

```python
def add_product_image(
    db: Session,
    product_id: int,
    image_path: str,
    tenant_id: int
) -> ProductImage:
    """
    Ajoute une image à un produit.

    Business Rule (Updated: 2025-12-07):
    - Valide que le produit existe et n'est pas deleted
    - Calcule automatiquement le display_order (max + 1)
    - Interdit les images orphelines
    """
    # Valider produit existe et non supprimé
    product = get_product_by_id(db, product_id, tenant_id)
    if not product:
        raise HTTPException(404, "Product not found")

    if product.is_deleted:
        raise HTTPException(400, "Cannot add image to deleted product")

    # Calculer display_order
    max_order = db.query(func.max(ProductImage.display_order))\
        .filter(
            ProductImage.product_id == product_id,
            ProductImage.deleted_at.is_(None)
        )\
        .scalar() or 0

    # Créer image
    image = ProductImage(
        product_id=product_id,
        image_path=image_path,
        display_order=max_order + 1
    )

    db.add(image)
    db.commit()
    db.refresh(image)

    return image
```

---

## 🏷️ Catégories Hiérarchiques

### Structure

Les catégories forment un arbre hiérarchique avec 3 niveaux maximum:

```
Vêtements (root, gender=null)
├── Homme (gender=men)
│   ├── T-shirts (gender=men)
│   ├── Pantalons (gender=men)
│   └── Vestes (gender=men)
└── Femme (gender=women)
    ├── Robes (gender=women)
    ├── Jupes (gender=women)
    └── Chemisiers (gender=women)
```

### Règles de Hiérarchie

**Localisation:** `models/public/category.py`

```python
class Category(Base):
    name_en = Column(String(100), primary_key=True)
    name_fr = Column(String(100), nullable=False)
    parent_category = Column(String(100), ForeignKey("categories.name_en"), nullable=True)
    gender = Column(Enum(Gender), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

#### ✅ Contraintes

1. **Profondeur maximale:** 3 niveaux
   - Niveau 1: Catégorie racine (parent_category = NULL)
   - Niveau 2: Sous-catégorie (parent_category = catégorie racine)
   - Niveau 3: Sous-sous-catégorie (parent_category = sous-catégorie)

2. **Circularité interdite:**
   - Une catégorie ne peut pas être son propre parent (direct ou indirect)
   - Exemple interdit: A → B → C → A

3. **Gender inheritance:**
   - Si une catégorie a un gender, toutes ses sous-catégories doivent avoir le même gender
   - Les catégories racines peuvent avoir gender=null

4. **Foreign Key Validation:**
   - `parent_category` doit exister dans `categories.name_en` (si non NULL)

#### 🔧 Validation Service

**Localisation:** `services/category_service.py`

```python
def validate_category_hierarchy(db: Session, category_name: str, parent_name: Optional[str]):
    """
    Valide qu'une catégorie respecte les règles de hiérarchie.

    Business Rule (Updated: 2025-12-07):
    - Profondeur max: 3 niveaux
    - Circularité interdite
    - Gender hérité du parent
    """
    if not parent_name:
        return  # Catégorie racine OK

    # Vérifier que parent existe
    parent = db.query(Category).filter(Category.name_en == parent_name).first()
    if not parent:
        raise HTTPException(400, f"Parent category '{parent_name}' not found")

    # Calculer profondeur
    depth = 1
    current = parent
    while current.parent_category:
        depth += 1
        current = db.query(Category).filter(Category.name_en == current.parent_category).first()

        if depth >= 3:
            raise HTTPException(400, "Category hierarchy max depth is 3 levels")

    # Vérifier circularité
    visited = {category_name}
    current = parent
    while current:
        if current.name_en in visited:
            raise HTTPException(400, "Circular category hierarchy detected")
        visited.add(current.name_en)

        if current.parent_category:
            current = db.query(Category).filter(Category.name_en == current.parent_category).first()
        else:
            break
```

---

## 💰 Gestion des Prix

### Contraintes Prix

**Localisation:** `models/user/product.py`

```python
class Product(Base):
    price = Column(Numeric(10, 2), nullable=False)
    cost_price = Column(Numeric(10, 2), nullable=True)
```

### Règles Business

#### ✅ Validation

1. **Prix de vente (price):**
   - Doit être > 0
   - Maximum 2 décimales
   - Maximum: 99999.99 €
   - Format: Decimal(10, 2)

2. **Prix de revient (cost_price):**
   - Optionnel (peut être NULL)
   - Si présent, doit être >= 0
   - Si présent, recommandé que `price > cost_price` (warning si égal ou inférieur)

3. **Calcul de marge:**
   ```python
   margin_percent = ((price - cost_price) / cost_price) * 100
   ```

#### 🔧 Validation Service

**Localisation:** `services/validators.py`

```python
def validate_price(price: Decimal, cost_price: Optional[Decimal] = None):
    """
    Valide les prix d'un produit.

    Business Rule (Updated: 2025-12-07):
    - price > 0 obligatoire
    - cost_price >= 0 si présent
    - Warning si price <= cost_price (marge négative)
    """
    if price <= 0:
        raise ValueError("Price must be greater than 0")

    if price > Decimal("99999.99"):
        raise ValueError("Price cannot exceed 99999.99")

    if cost_price is not None:
        if cost_price < 0:
            raise ValueError("Cost price cannot be negative")

        if price <= cost_price:
            # Log warning mais n'empêche pas création
            logger.warning(
                f"Price ({price}) is lower or equal to cost_price ({cost_price}). "
                f"Negative or zero margin."
            )
```

---

## 📦 Gestion du Stock

### Contraintes Stock

**Localisation:** `models/user/product.py`

```python
class Product(Base):
    stock_quantity = Column(Integer, nullable=False, default=1)
```

### Règles Business

#### ✅ Validation

1. **Stock minimum:**
   - Doit être >= 0
   - Stock = 0 autorisé (produit épuisé)

2. **Publication:**
   - ❌ **CRITIQUE:** Impossible de publier un produit avec `stock_quantity = 0`
   - Transition `DRAFT → PUBLISHED` interdite si stock = 0
   - Si produit `PUBLISHED` passe à stock = 0, statut doit changer vers `SOLD` ou rester `PUBLISHED` (au choix métier)

3. **Vente:**
   - Quand produit vendu (status = SOLD), le stock n'est PAS décrémenté automatiquement
   - Le stock doit être géré manuellement ou via intégration marketplace

#### 🔧 Validation Service

**Localisation:** `services/product_service.py`

```python
def publish_product(db: Session, product_id: int, tenant_id: int):
    """
    Publie un produit (DRAFT → PUBLISHED).

    Business Rule (Updated: 2025-12-07):
    - Stock quantity doit être > 0 pour publier
    - Status doit être DRAFT
    """
    product = get_product_by_id(db, product_id, tenant_id)

    if not product:
        raise HTTPException(404, "Product not found")

    if product.is_deleted:
        raise HTTPException(400, "Cannot publish deleted product")

    if product.status != ProductStatus.DRAFT:
        raise HTTPException(400, f"Cannot publish product with status {product.status}")

    # 🚨 CRITIQUE: Validation stock
    if product.stock_quantity <= 0:
        raise HTTPException(
            400,
            "Cannot publish product with zero stock. Please update stock_quantity first."
        )

    product.status = ProductStatus.PUBLISHED
    product.published_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(product)

    return product
```

---

## 🔑 SKU (Stock Keeping Unit)

### Contraintes SKU

**Localisation:** `models/user/product.py`

```python
class Product(Base):
    sku = Column(String(100), nullable=True, unique=True, index=True)
```

### Règles Business

#### ✅ Validation

1. **Unicité:**
   - SKU doit être unique **par tenant** (schema isolation)
   - Deux tenants différents peuvent avoir le même SKU
   - Contrainte: `UNIQUE (sku)` dans le schema `client_X`

2. **Format:**
   - Optionnel (peut être NULL)
   - Max 100 caractères
   - Recommandé: Alphanumerique + tirets/underscores
   - Exemple: `TSHIRT-NIKE-M-BLACK-001`

3. **Auto-génération:**
   - Si SKU non fourni, peut être auto-généré
   - Format suggéré: `{category}-{brand}-{timestamp}`

#### 🔧 Validation Service

**Localisation:** `services/product_service.py`

```python
def validate_sku_uniqueness(db: Session, sku: str, product_id: Optional[int] = None):
    """
    Valide que le SKU est unique dans le schema tenant.

    Business Rule (Updated: 2025-12-07):
    - SKU unique par tenant (isolation via schema)
    - Exclut le produit courant si update
    - Ignore les produits soft-deleted
    """
    if not sku:
        return  # SKU optionnel

    query = db.query(Product).filter(
        Product.sku == sku,
        Product.deleted_at.is_(None)
    )

    if product_id:
        query = query.filter(Product.id != product_id)

    existing = query.first()

    if existing:
        raise HTTPException(
            400,
            f"SKU '{sku}' already exists for another product (ID: {existing.id})"
        )
```

---

## 🎨 Attributs Produit

### Tables d'Attributs Partagées (Schema Public)

Les attributs produit sont stockés dans le schema `public` et partagés entre tous les tenants:

```
public.brands
public.colors
public.sizes
public.materials
public.fits
public.seasons
public.conditions
public.condition_sup
public.closures
public.decades
```

### Règles de Validation FK

**Localisation:** `services/validators.py`

```python
def validate_product_attributes(db: Session, product_data: dict):
    """
    Valide que tous les attributs d'un produit existent dans les tables de référence.

    Business Rule (Updated: 2025-12-07):
    - Tous les attributs doivent exister dans les tables public
    - Validation obligatoire AVANT insertion
    - Retourne une erreur claire si attribut invalide
    """
    validations = [
        ("brand", Brand, product_data.get("brand")),
        ("color", Color, product_data.get("color")),
        ("size", Size, product_data.get("size")),
        ("material", Material, product_data.get("material")),
        ("fit", Fit, product_data.get("fit")),
        ("season", Season, product_data.get("season")),
        ("condition", Condition, product_data.get("condition")),
        ("condition_sup", ConditionSup, product_data.get("condition_sup")),
        ("closure", Closure, product_data.get("closure")),
        ("decade", Decade, product_data.get("decade")),
    ]

    for attr_name, model_class, value in validations:
        if value is None:
            continue  # Attribut optionnel

        exists = db.query(model_class).filter(model_class.name == value).first()
        if not exists:
            raise HTTPException(
                400,
                f"Invalid {attr_name}: '{value}' not found in reference table"
            )
```

---

## 📊 Historique des Publications

### Table publications_history

**Localisation:** `models/user/publication_history.py`

```python
class PublicationHistory(Base):
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### Règles Business

#### ✅ Tracking des Publications

1. **Actions trackées:**
   - `create` - Création produit sur marketplace
   - `update` - Mise à jour produit existant
   - `delete` - Suppression produit
   - `sync` - Synchronisation bidirectionnelle

2. **Status possibles:**
   - `pending` - En attente d'exécution
   - `in_progress` - En cours
   - `completed` - Réussi
   - `failed` - Échoué
   - `cancelled` - Annulé

3. **Platforms supportées:**
   - `vinted`
   - `ebay`
   - `etsy`
   - `leboncoin`

4. **Error handling:**
   - Si `status = failed`, `error_message` doit être rempli
   - `completed_at` est NULL pour les publications en cours
   - Durée = `completed_at - started_at`

#### 🔧 Service Layer

**Localisation:** `services/plugin_task_service.py`

```python
def create_publication_record(
    db: Session,
    product_id: int,
    platform: str,
    action: str
) -> PublicationHistory:
    """
    Crée un enregistrement de publication.

    Business Rule (Updated: 2025-12-07):
    - Enregistre TOUTES les tentatives de publication
    - Status initial = 'pending'
    - started_at = now()
    """
    record = PublicationHistory(
        product_id=product_id,
        platform=platform,
        action=action,
        status="pending",
        started_at=datetime.now(timezone.utc)
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record

def complete_publication(
    db: Session,
    record_id: int,
    success: bool,
    error_message: Optional[str] = None
):
    """
    Marque une publication comme terminée.

    Business Rule (Updated: 2025-12-07):
    - Status = 'completed' si success=True, 'failed' sinon
    - completed_at = now()
    - error_message obligatoire si failed
    """
    record = db.query(PublicationHistory).filter(PublicationHistory.id == record_id).first()

    if not record:
        raise HTTPException(404, "Publication record not found")

    record.status = "completed" if success else "failed"
    record.completed_at = datetime.now(timezone.utc)

    if not success and error_message:
        record.error_message = error_message

    db.commit()
```

---

## 🔒 Règles de Sécurité Business

### Multi-tenant Isolation

**Principe:** Chaque tenant ne peut accéder qu'à SES données.

#### ✅ Vérifications Obligatoires

1. **Toutes les queries doivent filtrer par tenant:**
   ```python
   # ❌ MAL - Pas de filtre tenant
   product = db.query(Product).filter(Product.id == product_id).first()

   # ✅ BON - Filtre tenant appliqué via middleware
   # Le middleware set automatiquement search_path = client_{tenant_id}
   product = db.query(Product).filter(Product.id == product_id).first()
   ```

2. **Validation tenant dans les endpoints:**
   ```python
   @router.get("/products/{product_id}")
   def get_product(
       product_id: int,
       current_user: User = Depends(get_current_user),
       db: Session = Depends(get_db)
   ):
       # Le middleware a déjà set search_path = client_{current_user.tenant_id}
       # Donc la query ci-dessous ne voit QUE les produits du tenant
       product = db.query(Product).filter(Product.id == product_id).first()

       if not product:
           raise HTTPException(404, "Product not found")

       return product
   ```

3. **Cross-tenant queries interdites:**
   - Jamais de requêtes qui joignent des tables de deux schemas `client_X` différents
   - Les tables `public` sont OK (partagées)

### Rate Limiting

**Localisation:** `middleware/rate_limit.py`

#### ✅ Limites Business

1. **Vinted:**
   - 40 requêtes par 2 heures par compte Vinted
   - Tracking via Redis
   - Key: `ratelimit:vinted:{user_id}`

2. **API Backend:**
   - 1000 requêtes par heure par tenant
   - 100 requêtes par minute par user
   - Status 429 si dépassement

---

## 📝 Checklist Business Logic

### ✅ Avant de Créer un Produit

- [ ] Valider que tous les attributs existent (brand, color, size, etc.)
- [ ] Valider que category existe et n'est pas circulaire
- [ ] Valider que price > 0
- [ ] Valider que stock_quantity >= 0
- [ ] Valider que SKU est unique (si fourni)
- [ ] Appliquer tenant isolation

### ✅ Avant de Publier un Produit

- [ ] Vérifier que status = DRAFT
- [ ] Vérifier que stock_quantity > 0
- [ ] Vérifier que produit n'est pas deleted
- [ ] Vérifier que produit a au moins 1 image

### ✅ Avant de Modifier un Produit

- [ ] Vérifier que produit n'est pas deleted
- [ ] Vérifier que produit n'est pas archived
- [ ] Valider la transition de status si changement
- [ ] Valider les nouveaux attributs si modification

### ✅ Avant de Supprimer un Produit

- [ ] Soft delete (deleted_at) au lieu de hard delete
- [ ] Marquer TOUTES les images comme deleted (cascade)
- [ ] Créer un enregistrement dans publications_history si publié sur marketplaces

---

## 🚨 Erreurs Business Critiques à Éviter

### P0 - Critiques (Bloquant Production)

1. **Modification de produits supprimés**
   - ❌ Permettre UPDATE sur produits avec `deleted_at IS NOT NULL`
   - ✅ Filtrer `deleted_at IS NULL` sur TOUTES les queries

2. **Publication avec stock = 0**
   - ❌ Transition `DRAFT → PUBLISHED` sans vérifier stock
   - ✅ Bloquer publication si `stock_quantity <= 0`

3. **Images orphelines**
   - ❌ Créer images sans valider que product_id existe et n'est pas deleted
   - ✅ Valider FK + soft delete avant insertion

4. **Circularité catégories**
   - ❌ Permettre `A → B → C → A`
   - ✅ Détecter circularité avant insertion/update

5. **Régression état ARCHIVED**
   - ❌ Permettre transitions depuis ARCHIVED
   - ✅ ARCHIVED est terminal, aucune transition sortante

### P1 - Importantes (Non Bloquant mais Critique)

1. **Validation FK incomplète**
   - ❌ Insérer produit sans valider que brand/color/size existent
   - ✅ Valider TOUS les attributs avant insertion

2. **Race condition image count**
   - ❌ Calculer display_order sans lock
   - ✅ Utiliser transaction + select for update

3. **SKU non unique**
   - ❌ Permettre doublons SKU dans même schema
   - ✅ Vérifier unicité avant insert/update

---

## 📚 Références

- **Architecture:** `docs/ARCHITECTURE.md`
- **API Documentation:** `docs/API.md`
- **Plugin Integration:** `docs/PLUGIN_INTEGRATION.md`
- **Checklist Critiques:** `CRITICAL_FIXES_CHECKLIST.md` (racine projet)

---

**Dernière mise à jour:** 2025-12-08
