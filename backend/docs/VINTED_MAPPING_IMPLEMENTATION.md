# Category Platform Mapping Implementation Guide - Stoflow

> Document technique pour implémenter le système de mapping catégories multi-plateformes dans Stoflow Backend.
> Mis à jour le 2025-12-17 pour refléter l'état actuel du code.

---

## Table des matières

1. [État actuel](#1-état-actuel)
2. [Ce qui reste à implémenter](#2-ce-qui-reste-à-implémenter)
3. [Architecture cible](#3-architecture-cible)
4. [Modifications à apporter](#4-modifications-à-apporter)
5. [Migrations Alembic](#5-migrations-alembic)
6. [Services de mapping](#6-services-de-mapping)
7. [Checklist d'implémentation](#7-checklist-dimplémentation)

---

## 1. État actuel

### 1.1 Services DÉJÀ implémentés ✅

| Service | Fichier | Statut |
|---------|---------|--------|
| **VintedTitleService** | `services/vinted/vinted_title_service.py` | ✅ Complet |
| **VintedDescriptionService** | `services/vinted/vinted_description_service.py` | ✅ Complet |
| **VintedPricingService** | `services/vinted/vinted_pricing_service.py` | ✅ Complet |
| **VintedProductConverter** | `services/vinted/vinted_product_converter.py` | ✅ Complet |
| **VintedMappingService** | `services/vinted/vinted_mapping_service.py` | ⚠️ Partiel (category_id = None) |
| **VintedMapper** | `services/vinted/vinted_mapper.py` | ✅ Maps hardcodées |

### 1.2 Modèles d'attributs avec vinted_id ✅

| Modèle | Schema | Colonne vinted_id | Statut |
|--------|--------|-------------------|--------|
| **Brand** | `product_attributes` | `vinted_id` (Text) | ✅ Existe |
| **Color** | `product_attributes` | `vinted_id` (BigInteger) | ✅ Existe |
| **Condition** | `product_attributes` | `vinted_id` (BigInteger) | ✅ Existe |
| **Size** | `product_attributes` | `vinted_woman_id`, `vinted_man_top_id`, `vinted_man_bottom_id` | ✅ Existe |
| **Category** | `product_attributes` | ❌ Pas de vinted_id | ❌ À créer via mapping |

### 1.3 Modèle Product actuel

Le modèle `Product` (`models/user/product.py`) utilise des **colonnes String** pour les attributs (pas de FK):

```python
# Colonnes actuelles (String, pas de FK)
category: Mapped[str] = mapped_column(String(255), nullable=False)
brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
condition: Mapped[str] = mapped_column(String(100), nullable=False)
label_size: Mapped[str | None] = mapped_column(String(100), nullable=True)
color: Mapped[str | None] = mapped_column(String(100), nullable=True)
fit: Mapped[str | None] = mapped_column(String(100), nullable=True)
gender: Mapped[str | None] = mapped_column(String(100), nullable=True)
```

### 1.4 Modèle VintedProduct actuel

Le modèle `VintedProduct` (`models/user/vinted_product.py`) est **standalone** (pas de FK vers Product):

```python
# Colonnes actuelles
id: Mapped[int]           # PK interne
vinted_id: Mapped[int]    # ID Vinted (unique)
# Pas de product_id
```

---

## 2. Ce qui reste à implémenter

### 2.1 Décisions prises

| Question | Choix |
|----------|-------|
| Mapping catégories | **Table `category_platform_mappings`** générique multi-plateformes |
| Relation VintedProduct ↔ Product | **FK optionnelle** `product_id` nullable |
| Stockage IDs catégories | **Une seule table** avec colonnes par plateforme |
| Services existants | **Garder tels quels** |

### 2.2 Éléments à ajouter

1. **Table `category_platform_mappings`** avec clé composite `(category, gender, fit)` et colonnes pour chaque plateforme :
   - `vinted_category_id`, `vinted_category_name`
   - `etsy_taxonomy_id`, `etsy_category_name`
   - `ebay_category_id_fr`, `ebay_category_id_de`, `ebay_category_id_gb`, etc.
2. **Colonne `product_id`** optionnelle sur `VintedProduct`
3. **Repository `CategoryMappingRepository`** avec méthodes par plateforme
4. **Mise à jour des services** de mapping pour utiliser la nouvelle table

---

## 3. Architecture cible

### 3.1 Schéma des tables

```
product_attributes schema (existant)
├── brands (name PK, vinted_id) ✅
├── colors (name_en PK, vinted_id) ✅
├── conditions (name PK, vinted_id) ✅
├── sizes (name PK, vinted_woman_id, vinted_man_top_id, vinted_man_bottom_id) ✅
├── categories (name_en PK, parent_category) ✅
└── fits (name_en PK) ✅

public schema
├── users ✅
├── genders (name_en PK) ✅
└── category_platform_mappings (NEW)  ← À créer
    ├── category (FK → categories.name_en)
    ├── gender (FK → genders.name_en)
    ├── fit (FK → fits.name_en, nullable)
    ├── vinted_category_id, vinted_category_name, vinted_category_path
    ├── etsy_taxonomy_id, etsy_category_name
    └── ebay_category_id_fr, ebay_category_id_de, ebay_category_id_gb, ...

user_{id} schema
├── products (id PK, category String, ...) ✅
├── vinted_products (id PK, vinted_id, product_id nullable) ← À modifier
├── ebay_products ✅
├── etsy_products ✅
└── ...
```

### 3.2 Flux de mapping catégorie (multi-plateformes)

```
Product.category (String, ex: "Jeans")
    │
    ├── Product.gender (String, ex: "male")
    │
    ├── Product.fit (String, ex: "slim", nullable)
    │
    └── CategoryMappingRepository.get_mapping(category, gender, fit)
        │
        └── Query category_platform_mappings
            WHERE category = "Jeans"
              AND gender = "male"
              AND (fit = "slim" OR fit IS NULL)
            │
            └── Returns {
                  vinted_category_id: 1193,
                  etsy_taxonomy_id: 67152259,
                  ebay_category_id_fr: 11483
                }
```

---

## 4. Modifications à apporter

### 4.1 Nouveau modèle: CategoryPlatformMapping

**Fichier à créer** : `models/public/category_platform_mapping.py`

```python
"""
CategoryPlatformMapping Model - Schema Public

Table de mapping des catégories Stoflow vers les IDs catégories de TOUTES les plateformes.
Utilise une clé composite (category, gender, fit) pour un mapping précis.

Business Rules:
- category + gender sont requis
- fit est optionnel (NULL = mapping par défaut pour la catégorie/genre)
- Recherche avec fallback: exact match → sans fit → premier trouvé
- Chaque plateforme a ses propres colonnes d'ID
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class CategoryPlatformMapping(Base):
    """
    Mapping catégorie Stoflow → IDs catégories multi-plateformes.

    Clé composite: (category, gender, fit)

    Exemples:
    - ("Jeans", "male", "slim") → Vinted 1193, Etsy 67152259, eBay FR 11483
    - ("Jeans", "male", NULL) → Fallback générique pour Jeans homme
    - ("Jeans", "female", NULL) → Vinted 1211, Etsy 67152260, eBay FR 11484
    """

    __tablename__ = "category_platform_mappings"
    __table_args__ = (
        UniqueConstraint("category", "gender", "fit", name="uq_category_platform_mapping"),
        Index("idx_category_platform_lookup", "category", "gender", "fit"),
        {"schema": "public"}
    )

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # === CLÉ COMPOSITE ===

    # Catégorie Stoflow (ex: "Jeans", "T-shirt")
    category: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("product_attributes.categories.name_en", onupdate="CASCADE"),
        nullable=False,
        index=True,
        comment="Catégorie Stoflow (FK categories.name_en)"
    )

    # Genre (ex: "male", "female")
    gender: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("public.genders.name_en", onupdate="CASCADE"),
        nullable=False,
        index=True,
        comment="Genre (FK genders.name_en)"
    )

    # Coupe/Fit (optionnel, ex: "slim", "regular", NULL)
    fit: Mapped[str | None] = mapped_column(
        String(100),
        ForeignKey("public.fits.name_en", onupdate="CASCADE"),
        nullable=True,
        default=None,
        comment="Coupe (FK fits.name_en, NULL = fallback)"
    )

    # ================================================================
    # VINTED MAPPING
    # ================================================================

    vinted_category_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="ID catégorie Vinted (catalog_id)"
    )

    vinted_category_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        comment="Nom catégorie Vinted"
    )

    vinted_category_path: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
        comment="Chemin Vinted (ex: 'Homme > Pantalons > Jeans')"
    )

    # ================================================================
    # ETSY MAPPING
    # ================================================================

    etsy_taxonomy_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="ID taxonomy Etsy"
    )

    etsy_category_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        comment="Nom catégorie Etsy"
    )

    etsy_category_path: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
        comment="Chemin Etsy (ex: 'Clothing > Men > Pants')"
    )

    # Attributs Etsy requis pour cette catégorie (JSON)
    etsy_required_attributes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="JSON des attributs Etsy requis (property_id, etc.)"
    )

    # ================================================================
    # EBAY MAPPING (par marketplace)
    # ================================================================

    # France
    ebay_category_id_fr: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="ID catégorie eBay France"
    )

    # Allemagne
    ebay_category_id_de: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="ID catégorie eBay Allemagne"
    )

    # Royaume-Uni
    ebay_category_id_gb: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="ID catégorie eBay UK"
    )

    # Italie
    ebay_category_id_it: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="ID catégorie eBay Italie"
    )

    # Espagne
    ebay_category_id_es: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="ID catégorie eBay Espagne"
    )

    # Nom commun eBay
    ebay_category_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        comment="Nom catégorie eBay (commun)"
    )

    # Item Specifics eBay (JSON par marketplace)
    ebay_item_specifics: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="JSON des Item Specifics eBay requis"
    )

    # ================================================================
    # METADATA
    # ================================================================

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        comment="Mapping actif/inactif"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True
    )

    # ================================================================
    # HELPERS
    # ================================================================

    def get_ebay_category_id(self, marketplace: str = "EBAY_FR") -> int | None:
        """
        Retourne l'ID catégorie eBay pour une marketplace donnée.

        Args:
            marketplace: Code marketplace (EBAY_FR, EBAY_DE, EBAY_GB, EBAY_IT, EBAY_ES)

        Returns:
            ID catégorie ou None
        """
        mapping = {
            "EBAY_FR": self.ebay_category_id_fr,
            "EBAY_DE": self.ebay_category_id_de,
            "EBAY_GB": self.ebay_category_id_gb,
            "EBAY_IT": self.ebay_category_id_it,
            "EBAY_ES": self.ebay_category_id_es,
        }
        return mapping.get(marketplace.upper()) or self.ebay_category_id_fr

    def __repr__(self) -> str:
        return (
            f"<CategoryPlatformMapping("
            f"category='{self.category}', gender='{self.gender}', fit='{self.fit}' "
            f"→ vinted={self.vinted_category_id}, etsy={self.etsy_taxonomy_id}, "
            f"ebay_fr={self.ebay_category_id_fr})>"
        )
```

### 4.2 Modification: VintedProduct (ajouter product_id optionnel)

**Fichier à modifier** : `models/user/vinted_product.py`

Ajouter la colonne `product_id` nullable:

```python
# === AJOUTER APRÈS vinted_id ===

# Lien optionnel vers Product Stoflow
product_id: Mapped[int | None] = mapped_column(
    Integer,
    ForeignKey("products.id", ondelete="SET NULL"),
    nullable=True,
    index=True,
    comment="ID du produit Stoflow lié (optionnel)"
)

# Relationship (ajouter dans la section relationships)
# product: Mapped["Product | None"] = relationship(
#     "Product",
#     back_populates="vinted_product",
#     foreign_keys=[product_id]
# )
```

**Note**: La relationship est commentée car `Product` n'a pas de relationship inverse actuellement.

### 4.3 Nouveau repository: CategoryMappingRepository

**Fichier à créer** : `repositories/category_mapping_repository.py`

```python
"""
CategoryMappingRepository - Accès aux mappings catégories multi-plateformes.

Fournit des méthodes spécifiques par plateforme avec fallback intelligent.
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from models.public.category_platform_mapping import CategoryPlatformMapping


class CategoryMappingRepository:
    """Repository pour accéder aux mappings catégories."""

    def __init__(self, db: Session):
        self.db = db

    def _normalize_gender(self, gender: str) -> str:
        """Normalise le genre vers 'male' ou 'female'."""
        gender_lower = gender.lower() if gender else 'unisex'
        if gender_lower in ['men', 'man', 'homme', 'boys', 'boy', 'male']:
            return 'male'
        elif gender_lower in ['women', 'woman', 'femme', 'girls', 'girl', 'female']:
            return 'female'
        return 'unisex'

    def _get_mapping(
        self,
        category: str,
        gender: str,
        fit: Optional[str] = None
    ) -> Optional[CategoryPlatformMapping]:
        """
        Récupère le mapping avec stratégie de fallback.

        Ordre de recherche:
        1. Match exact (category + gender + fit)
        2. Match sans fit (category + gender + fit=NULL)
        3. Premier trouvé pour category
        """
        gender_normalized = self._normalize_gender(gender)
        fit_normalized = fit.lower() if fit else None

        # 1. Recherche exacte avec fit
        if fit_normalized:
            mapping = self.db.query(CategoryPlatformMapping).filter(
                CategoryPlatformMapping.category == category,
                CategoryPlatformMapping.gender == gender_normalized,
                CategoryPlatformMapping.fit == fit_normalized,
                CategoryPlatformMapping.is_active == True
            ).first()
            if mapping:
                return mapping

        # 2. Recherche sans fit
        mapping = self.db.query(CategoryPlatformMapping).filter(
            CategoryPlatformMapping.category == category,
            CategoryPlatformMapping.gender == gender_normalized,
            CategoryPlatformMapping.fit == None,  # noqa: E711
            CategoryPlatformMapping.is_active == True
        ).first()
        if mapping:
            return mapping

        # 3. Fallback: premier mapping pour cette catégorie
        return self.db.query(CategoryPlatformMapping).filter(
            CategoryPlatformMapping.category == category,
            CategoryPlatformMapping.is_active == True
        ).first()

    # ================================================================
    # VINTED
    # ================================================================

    def get_vinted_mapping(
        self,
        category: str,
        gender: str,
        fit: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Récupère le mapping Vinted pour une catégorie.

        Returns:
            {'id': int, 'name': str, 'path': str} ou {'id': None, ...}
        """
        mapping = self._get_mapping(category, gender, fit)
        if mapping and mapping.vinted_category_id:
            return {
                'id': mapping.vinted_category_id,
                'name': mapping.vinted_category_name,
                'path': mapping.vinted_category_path
            }
        return {'id': None, 'name': None, 'path': None}

    # ================================================================
    # ETSY
    # ================================================================

    def get_etsy_mapping(
        self,
        category: str,
        gender: str,
        fit: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Récupère le mapping Etsy pour une catégorie.

        Returns:
            {'taxonomy_id': int, 'name': str, 'path': str, 'attributes': dict}
        """
        mapping = self._get_mapping(category, gender, fit)
        if mapping and mapping.etsy_taxonomy_id:
            import json
            attributes = {}
            if mapping.etsy_required_attributes:
                try:
                    attributes = json.loads(mapping.etsy_required_attributes)
                except json.JSONDecodeError:
                    pass

            return {
                'taxonomy_id': mapping.etsy_taxonomy_id,
                'name': mapping.etsy_category_name,
                'path': mapping.etsy_category_path,
                'attributes': attributes
            }
        return {'taxonomy_id': None, 'name': None, 'path': None, 'attributes': {}}

    # ================================================================
    # EBAY
    # ================================================================

    def get_ebay_mapping(
        self,
        category: str,
        gender: str,
        fit: Optional[str] = None,
        marketplace: str = "EBAY_FR"
    ) -> Dict[str, Any]:
        """
        Récupère le mapping eBay pour une catégorie.

        Args:
            marketplace: EBAY_FR, EBAY_DE, EBAY_GB, EBAY_IT, EBAY_ES

        Returns:
            {'category_id': int, 'name': str, 'item_specifics': dict}
        """
        mapping = self._get_mapping(category, gender, fit)
        if mapping:
            category_id = mapping.get_ebay_category_id(marketplace)
            if category_id:
                import json
                item_specifics = {}
                if mapping.ebay_item_specifics:
                    try:
                        item_specifics = json.loads(mapping.ebay_item_specifics)
                    except json.JSONDecodeError:
                        pass

                return {
                    'category_id': category_id,
                    'name': mapping.ebay_category_name,
                    'item_specifics': item_specifics
                }
        return {'category_id': None, 'name': None, 'item_specifics': {}}

    # ================================================================
    # MULTI-PLATFORM
    # ================================================================

    def get_all_mappings(
        self,
        category: str,
        gender: str,
        fit: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Récupère les mappings pour TOUTES les plateformes en une seule requête.

        Returns:
            {
                'vinted': {'id': int, 'name': str, 'path': str},
                'etsy': {'taxonomy_id': int, 'name': str, ...},
                'ebay': {'fr': int, 'de': int, 'gb': int, ...}
            }
        """
        mapping = self._get_mapping(category, gender, fit)
        if not mapping:
            return {
                'vinted': {'id': None},
                'etsy': {'taxonomy_id': None},
                'ebay': {'fr': None, 'de': None, 'gb': None}
            }

        return {
            'vinted': {
                'id': mapping.vinted_category_id,
                'name': mapping.vinted_category_name,
                'path': mapping.vinted_category_path
            },
            'etsy': {
                'taxonomy_id': mapping.etsy_taxonomy_id,
                'name': mapping.etsy_category_name,
                'path': mapping.etsy_category_path
            },
            'ebay': {
                'fr': mapping.ebay_category_id_fr,
                'de': mapping.ebay_category_id_de,
                'gb': mapping.ebay_category_id_gb,
                'it': mapping.ebay_category_id_it,
                'es': mapping.ebay_category_id_es,
                'name': mapping.ebay_category_name
            }
        }
```

---

## 5. Migrations Alembic

### 5.1 Migration: Créer table category_platform_mappings

```bash
alembic revision --autogenerate -m "add_category_platform_mappings_table"
```

**Contenu de la migration:**

```python
"""add_category_platform_mappings_table

Revision ID: xxxxx
Revises: previous_revision
Create Date: 2025-12-17
"""
from alembic import op
import sqlalchemy as sa


def upgrade():
    # Créer la table category_platform_mappings dans public schema
    op.create_table(
        'category_platform_mappings',

        # Primary Key
        sa.Column('id', sa.Integer(), primary_key=True),

        # Clé composite
        sa.Column('category', sa.String(100), sa.ForeignKey('product_attributes.categories.name_en', onupdate='CASCADE'), nullable=False),
        sa.Column('gender', sa.String(50), sa.ForeignKey('public.genders.name_en', onupdate='CASCADE'), nullable=False),
        sa.Column('fit', sa.String(100), sa.ForeignKey('public.fits.name_en', onupdate='CASCADE'), nullable=True),

        # VINTED
        sa.Column('vinted_category_id', sa.Integer(), nullable=True),
        sa.Column('vinted_category_name', sa.String(150), nullable=True),
        sa.Column('vinted_category_path', sa.String(300), nullable=True),

        # ETSY
        sa.Column('etsy_taxonomy_id', sa.BigInteger(), nullable=True),
        sa.Column('etsy_category_name', sa.String(150), nullable=True),
        sa.Column('etsy_category_path', sa.String(300), nullable=True),
        sa.Column('etsy_required_attributes', sa.Text(), nullable=True),

        # EBAY (par marketplace)
        sa.Column('ebay_category_id_fr', sa.Integer(), nullable=True),
        sa.Column('ebay_category_id_de', sa.Integer(), nullable=True),
        sa.Column('ebay_category_id_gb', sa.Integer(), nullable=True),
        sa.Column('ebay_category_id_it', sa.Integer(), nullable=True),
        sa.Column('ebay_category_id_es', sa.Integer(), nullable=True),
        sa.Column('ebay_category_name', sa.String(150), nullable=True),
        sa.Column('ebay_item_specifics', sa.Text(), nullable=True),

        # Metadata
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),

        schema='public'
    )

    # Contrainte unique
    op.create_unique_constraint(
        'uq_category_platform_mapping',
        'category_platform_mappings',
        ['category', 'gender', 'fit'],
        schema='public'
    )

    # Index pour lookup rapide
    op.create_index(
        'idx_category_platform_lookup',
        'category_platform_mappings',
        ['category', 'gender', 'fit'],
        schema='public'
    )

    # Index par plateforme pour queries spécifiques
    op.create_index('idx_cpm_vinted', 'category_platform_mappings', ['vinted_category_id'], schema='public')
    op.create_index('idx_cpm_etsy', 'category_platform_mappings', ['etsy_taxonomy_id'], schema='public')
    op.create_index('idx_cpm_ebay_fr', 'category_platform_mappings', ['ebay_category_id_fr'], schema='public')


def downgrade():
    op.drop_table('category_platform_mappings', schema='public')
```

### 5.2 Migration: Ajouter product_id à vinted_products

```bash
alembic revision --autogenerate -m "add_product_id_to_vinted_products"
```

**Contenu de la migration:**

```python
"""add_product_id_to_vinted_products

Revision ID: yyyyy
Revises: xxxxx
Create Date: 2025-12-17
"""
from alembic import op
import sqlalchemy as sa


def upgrade():
    # Ajouter colonne product_id nullable à vinted_products
    # Note: Cette colonne est dans le template_tenant schema
    # Elle sera automatiquement présente dans les nouveaux schemas user_{id}

    # Pour les schemas existants, exécuter manuellement:
    # ALTER TABLE user_X.vinted_products ADD COLUMN product_id INTEGER REFERENCES user_X.products(id) ON DELETE SET NULL;

    op.execute("""
        DO $$
        DECLARE
            schema_name TEXT;
        BEGIN
            -- Ajouter à template_tenant
            IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'template_tenant') THEN
                EXECUTE 'ALTER TABLE template_tenant.vinted_products ADD COLUMN IF NOT EXISTS product_id INTEGER REFERENCES template_tenant.products(id) ON DELETE SET NULL';
                EXECUTE 'CREATE INDEX IF NOT EXISTS idx_vinted_products_product_id ON template_tenant.vinted_products(product_id)';
            END IF;

            -- Ajouter aux schemas user_* existants
            FOR schema_name IN (SELECT nspname FROM pg_namespace WHERE nspname LIKE 'user_%')
            LOOP
                EXECUTE format('ALTER TABLE %I.vinted_products ADD COLUMN IF NOT EXISTS product_id INTEGER REFERENCES %I.products(id) ON DELETE SET NULL', schema_name, schema_name);
                EXECUTE format('CREATE INDEX IF NOT EXISTS idx_vinted_products_product_id ON %I.vinted_products(product_id)', schema_name);
            END LOOP;
        END $$;
    """)


def downgrade():
    op.execute("""
        DO $$
        DECLARE
            schema_name TEXT;
        BEGIN
            -- Supprimer de template_tenant
            IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'template_tenant') THEN
                EXECUTE 'ALTER TABLE template_tenant.vinted_products DROP COLUMN IF EXISTS product_id';
            END IF;

            -- Supprimer des schemas user_*
            FOR schema_name IN (SELECT nspname FROM pg_namespace WHERE nspname LIKE 'user_%')
            LOOP
                EXECUTE format('ALTER TABLE %I.vinted_products DROP COLUMN IF EXISTS product_id', schema_name);
            END LOOP;
        END $$;
    """)
```

### 5.3 Script: Peupler category_platform_mappings

**Fichier** : `scripts/seed_category_platform_mappings.py`

```python
"""
Script pour peupler la table category_platform_mappings
avec les mappings de base pour toutes les plateformes.

Usage:
    python scripts/seed_category_platform_mappings.py
"""
import sys
sys.path.insert(0, '.')

from sqlalchemy import text
from shared.database import SessionLocal

# Mappings multi-plateformes
# Format: (category, gender, fit, vinted_id, vinted_name, vinted_path, etsy_id, ebay_fr)
MAPPINGS = [
    # === JEANS ===
    {
        "category": "Jeans", "gender": "male", "fit": None,
        "vinted_category_id": 1193, "vinted_category_name": "Jeans",
        "vinted_category_path": "Homme > Vêtements > Pantalons > Jeans",
        "etsy_taxonomy_id": 67152259, "etsy_category_name": "Jeans",
        "ebay_category_id_fr": 11483, "ebay_category_name": "Jeans"
    },
    {
        "category": "Jeans", "gender": "male", "fit": "slim",
        "vinted_category_id": 1193, "vinted_category_name": "Jeans Slim",
        "vinted_category_path": "Homme > Vêtements > Pantalons > Jeans",
        "etsy_taxonomy_id": 67152259, "etsy_category_name": "Jeans",
        "ebay_category_id_fr": 11483, "ebay_category_name": "Jeans"
    },
    {
        "category": "Jeans", "gender": "female", "fit": None,
        "vinted_category_id": 1211, "vinted_category_name": "Jeans",
        "vinted_category_path": "Femme > Vêtements > Pantalons > Jeans",
        "etsy_taxonomy_id": 67152260, "etsy_category_name": "Jeans",
        "ebay_category_id_fr": 11554, "ebay_category_name": "Jeans"
    },

    # === T-SHIRTS ===
    {
        "category": "T-shirt", "gender": "male", "fit": None,
        "vinted_category_id": 1203, "vinted_category_name": "T-shirt",
        "vinted_category_path": "Homme > Vêtements > Hauts > T-shirts",
        "etsy_taxonomy_id": 67152230, "etsy_category_name": "T-Shirts",
        "ebay_category_id_fr": 15687, "ebay_category_name": "T-shirts"
    },
    {
        "category": "T-shirt", "gender": "female", "fit": None,
        "vinted_category_id": 1209, "vinted_category_name": "T-shirt",
        "vinted_category_path": "Femme > Vêtements > Hauts > T-shirts",
        "etsy_taxonomy_id": 67152231, "etsy_category_name": "T-Shirts",
        "ebay_category_id_fr": 53159, "ebay_category_name": "T-shirts"
    },

    # === SWEAT-SHIRTS ===
    {
        "category": "Sweat-shirt", "gender": "male", "fit": None,
        "vinted_category_id": 1199, "vinted_category_name": "Sweat-shirt",
        "vinted_category_path": "Homme > Vêtements > Hauts > Sweats",
        "etsy_taxonomy_id": 67152228, "etsy_category_name": "Sweatshirts",
        "ebay_category_id_fr": 155183, "ebay_category_name": "Sweats"
    },
    {
        "category": "Sweat-shirt", "gender": "female", "fit": None,
        "vinted_category_id": 1215, "vinted_category_name": "Sweat-shirt",
        "vinted_category_path": "Femme > Vêtements > Hauts > Sweats",
        "etsy_taxonomy_id": 67152229, "etsy_category_name": "Sweatshirts",
        "ebay_category_id_fr": 155226, "ebay_category_name": "Sweats"
    },

    # === VESTES ===
    {
        "category": "Jacket", "gender": "male", "fit": None,
        "vinted_category_id": 1197, "vinted_category_name": "Veste",
        "vinted_category_path": "Homme > Vêtements > Vestes",
        "etsy_taxonomy_id": 67152250, "etsy_category_name": "Jackets & Coats",
        "ebay_category_id_fr": 57988, "ebay_category_name": "Vestes"
    },
    {
        "category": "Jacket", "gender": "female", "fit": None,
        "vinted_category_id": 1217, "vinted_category_name": "Veste",
        "vinted_category_path": "Femme > Vêtements > Vestes",
        "etsy_taxonomy_id": 67152251, "etsy_category_name": "Jackets & Coats",
        "ebay_category_id_fr": 63862, "ebay_category_name": "Vestes"
    },

    # === ACCESSOIRES ===
    {
        "category": "Sunglasses", "gender": "male", "fit": None,
        "vinted_category_id": 98, "vinted_category_name": "Lunettes de soleil",
        "vinted_category_path": "Accessoires > Lunettes",
        "etsy_taxonomy_id": 67157015, "etsy_category_name": "Sunglasses",
        "ebay_category_id_fr": 79720, "ebay_category_name": "Lunettes de soleil"
    },
    {
        "category": "Sunglasses", "gender": "female", "fit": None,
        "vinted_category_id": 98, "vinted_category_name": "Lunettes de soleil",
        "vinted_category_path": "Accessoires > Lunettes",
        "etsy_taxonomy_id": 67157015, "etsy_category_name": "Sunglasses",
        "ebay_category_id_fr": 79720, "ebay_category_name": "Lunettes de soleil"
    },
]


def seed_mappings():
    """Insert les mappings dans la base de données."""
    db = SessionLocal()

    try:
        # Vérifier si la table existe
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'category_platform_mappings'
            )
        """))

        if not result.scalar():
            print("❌ Table category_platform_mappings n'existe pas.")
            print("   Exécuter: alembic upgrade head")
            return

        # Insérer les mappings
        for m in MAPPINGS:
            db.execute(text("""
                INSERT INTO public.category_platform_mappings
                (category, gender, fit,
                 vinted_category_id, vinted_category_name, vinted_category_path,
                 etsy_taxonomy_id, etsy_category_name,
                 ebay_category_id_fr, ebay_category_name,
                 is_active)
                VALUES
                (:category, :gender, :fit,
                 :vinted_category_id, :vinted_category_name, :vinted_category_path,
                 :etsy_taxonomy_id, :etsy_category_name,
                 :ebay_category_id_fr, :ebay_category_name,
                 true)
                ON CONFLICT (category, gender, fit) DO UPDATE SET
                    vinted_category_id = EXCLUDED.vinted_category_id,
                    vinted_category_name = EXCLUDED.vinted_category_name,
                    vinted_category_path = EXCLUDED.vinted_category_path,
                    etsy_taxonomy_id = EXCLUDED.etsy_taxonomy_id,
                    etsy_category_name = EXCLUDED.etsy_category_name,
                    ebay_category_id_fr = EXCLUDED.ebay_category_id_fr,
                    ebay_category_name = EXCLUDED.ebay_category_name,
                    updated_at = NOW()
            """), m)

        db.commit()
        print(f"✅ {len(MAPPINGS)} mappings multi-plateformes insérés/mis à jour")

    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_mappings()
```

---

## 6. Services de mapping

### 6.1 Utilisation dans VintedMappingService

**Modifier** : `services/vinted/vinted_mapping_service.py`

```python
from repositories.category_mapping_repository import CategoryMappingRepository


class VintedMappingService:
    """Service de mapping attributs Product → IDs Vinted."""

    def __init__(self, db: Session):
        self.db = db
        self.category_repo = CategoryMappingRepository(db)

    def map_category(self, product) -> tuple[int | None, str | None]:
        """Mappe la catégorie vers son ID Vinted."""
        mapping = self.category_repo.get_vinted_mapping(
            category=product.category,
            gender=product.gender,
            fit=product.fit
        )
        return mapping['id'], mapping['path']

    def map_all_attributes(self, product) -> Dict[str, Any]:
        """Mappe tous les attributs."""
        category_id, category_path = self.map_category(product)

        return {
            'brand_id': self.map_brand(product),
            'color_id': self.map_color(product),
            'condition_id': self.map_condition(product),
            'size_id': self.map_size(product, category_id),
            'category_id': category_id,
            'category_path': category_path,
            # ...
        }
```

### 6.2 Utilisation dans EtsyMappingService

```python
from repositories.category_mapping_repository import CategoryMappingRepository


class EtsyMappingService:
    """Service de mapping attributs Product → IDs Etsy."""

    def __init__(self, db: Session):
        self.db = db
        self.category_repo = CategoryMappingRepository(db)

    def map_category(self, product) -> Dict[str, Any]:
        """Mappe la catégorie vers l'ID taxonomy Etsy."""
        return self.category_repo.get_etsy_mapping(
            category=product.category,
            gender=product.gender,
            fit=product.fit
        )
```

### 6.3 Utilisation dans EbayMappingService

```python
from repositories.category_mapping_repository import CategoryMappingRepository


class EbayMappingService:
    """Service de mapping attributs Product → IDs eBay."""

    def __init__(self, db: Session, marketplace: str = "EBAY_FR"):
        self.db = db
        self.marketplace = marketplace
        self.category_repo = CategoryMappingRepository(db)

    def map_category(self, product) -> Dict[str, Any]:
        """Mappe la catégorie vers l'ID catégorie eBay."""
        return self.category_repo.get_ebay_mapping(
            category=product.category,
            gender=product.gender,
            fit=product.fit,
            marketplace=self.marketplace
        )
```

### 6.4 Tests

```python
# tests/unit/repositories/test_category_mapping_repository.py

import pytest
from models.public.category_platform_mapping import CategoryPlatformMapping
from repositories.category_mapping_repository import CategoryMappingRepository


class TestCategoryMappingRepository:

    def test_get_vinted_mapping_exact_match(self, db_session):
        """Test mapping Vinted avec match exact"""
        # Setup
        mapping = CategoryPlatformMapping(
            category="Jeans",
            gender="male",
            fit="slim",
            vinted_category_id=1193,
            vinted_category_name="Jeans Slim",
            etsy_taxonomy_id=67152259,
            ebay_category_id_fr=11483
        )
        db_session.add(mapping)
        db_session.commit()

        # Test
        repo = CategoryMappingRepository(db_session)
        result = repo.get_vinted_mapping("Jeans", "male", "slim")

        assert result['id'] == 1193
        assert result['name'] == "Jeans Slim"

    def test_get_all_mappings_returns_all_platforms(self, db_session):
        """Test récupération multi-plateformes"""
        mapping = CategoryPlatformMapping(
            category="T-shirt",
            gender="male",
            vinted_category_id=1203,
            etsy_taxonomy_id=67152230,
            ebay_category_id_fr=15687,
            ebay_category_id_de=15688,
            ebay_category_id_gb=15689
        )
        db_session.add(mapping)
        db_session.commit()

        repo = CategoryMappingRepository(db_session)
        result = repo.get_all_mappings("T-shirt", "male")

        assert result['vinted']['id'] == 1203
        assert result['etsy']['taxonomy_id'] == 67152230
        assert result['ebay']['fr'] == 15687
        assert result['ebay']['de'] == 15688
        assert result['ebay']['gb'] == 15689

    def test_fallback_without_fit(self, db_session):
        """Test fallback quand fit non trouvé"""
        mapping = CategoryPlatformMapping(
            category="Jeans",
            gender="male",
            fit=None,  # Fallback
            vinted_category_id=1193
        )
        db_session.add(mapping)
        db_session.commit()

        repo = CategoryMappingRepository(db_session)
        result = repo.get_vinted_mapping("Jeans", "male", "bootcut")

        assert result['id'] == 1193  # Fallback
```

---

## 7. Checklist d'implémentation

### Phase 1: Modèles ✅/🔲

- [x] `Product` avec colonnes String (existant)
- [x] `VintedProduct` standalone (existant)
- [x] `Brand` avec `vinted_id` (existant)
- [x] `Color` avec `vinted_id` (existant)
- [x] `Condition` avec `vinted_id` (existant)
- [x] `Size` avec `vinted_*_id` (existant)
- [ ] **Créer `CategoryPlatformMapping`** (nouveau modèle multi-plateformes)
- [ ] **Modifier `VintedProduct`** (ajouter `product_id` nullable)

### Phase 2: Migrations 🔲

- [ ] Migration `add_category_platform_mappings_table`
- [ ] Migration `add_product_id_to_vinted_products`
- [ ] Exécuter migrations: `alembic upgrade head`

### Phase 3: Repository & Services 🔲

- [ ] **Créer `CategoryMappingRepository`** (nouveau)
- [ ] Mettre à jour `VintedMappingService` pour utiliser le repository
- [ ] Mettre à jour `EtsyMappingService` pour utiliser le repository
- [ ] Mettre à jour `EbayMappingService` pour utiliser le repository

### Phase 4: Données 🔲

- [ ] Vérifier tables FK existent (categories, genders, fits)
- [ ] Script `seed_category_platform_mappings.py`
- [ ] Exécuter seed: `python scripts/seed_category_platform_mappings.py`

### Phase 5: Tests 🔲

- [ ] Tests `CategoryMappingRepository`
- [ ] Tests `VintedMappingService.map_category()`
- [ ] Tests multi-plateformes

---

## Résumé des fichiers à créer/modifier

| Action | Fichier |
|--------|---------|
| **Créer** | `models/public/category_platform_mapping.py` |
| **Créer** | `repositories/category_mapping_repository.py` |
| **Créer** | `migrations/versions/xxxx_add_category_platform_mappings.py` |
| **Créer** | `migrations/versions/yyyy_add_product_id_to_vinted_products.py` |
| **Créer** | `scripts/seed_category_platform_mappings.py` |
| **Modifier** | `models/user/vinted_product.py` (ajouter product_id) |
| **Modifier** | `services/vinted/vinted_mapping_service.py` |
| **Modifier** | `services/etsy/etsy_mapping_service.py` (si existe) |
| **Modifier** | `services/ebay/ebay_mapping_service.py` (si existe) |
| **Modifier** | `models/public/__init__.py` (importer nouveau modèle) |

---

*Document mis à jour le 2025-12-17*
*Table `category_platform_mappings` générique pour Vinted, Etsy, eBay*
