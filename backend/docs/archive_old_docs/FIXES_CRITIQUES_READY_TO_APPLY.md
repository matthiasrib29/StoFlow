# 🔧 Fixes Critiques - Code Prêt à Appliquer

**Date**: 2025-12-05
**Bugs Identifiés**: 3 critiques
**Effort Total**: ~1.5 heures
**Impact**: Stabilité + Maintenabilité long terme

---

## 📋 Résumé des Bugs

| # | Bug | Sévérité | Effort | Fichiers Impactés |
|---|-----|----------|--------|-------------------|
| **1** | `func.now()` mal utilisé | 🔴 CRITIQUE | 15 min | `services/product_service.py`, nouveau `shared/datetime_utils.py` |
| **2** | Produits supprimés modifiables | ✅ RÉSOLU | 0 min | Déjà protégé par `get_product_by_id()` |
| **3** | Références circulaires categories | 🔴 CRITIQUE | 1h | `models/public/category.py`, migration, tests |

---

## 🔴 BUG #1 : func.now() - Corruption de Données

### Problème
```python
# ❌ INCORRECT - Stocke un objet SQL au lieu d'une datetime
product.deleted_at = func.now()
product.published_at = func.now()
product.sold_at = func.now()
```

### Solution Choisie: Option B - Helper Centralisé

**Effort**: 15 minutes
**ROI**: Maintenabilité long terme + fix immédiat

---

### Étape 1/3 : Créer le Helper

**Fichier**: `shared/datetime_utils.py` (NOUVEAU)

```python
"""
Datetime Utilities

Fonctions utilitaires pour gérer les timestamps de manière cohérente
dans toute l'application.

Business Rules (2025-12-05):
- Tous les timestamps en UTC
- Format ISO 8601 pour JSON
- Timezone-aware datetime objects
"""

from datetime import datetime, timezone
from typing import Optional


def utc_now() -> datetime:
    """
    Retourne l'heure UTC actuelle (timezone-aware).

    Cette fonction est la source unique de vérité pour tous les timestamps
    dans l'application. Elle garantit:
    - Timezone UTC explicite
    - Cohérence entre tous les services
    - Facilité de mock dans les tests

    Returns:
        datetime: Heure actuelle en UTC avec timezone info

    Example:
        >>> now = utc_now()
        >>> print(now)
        2025-12-05 15:30:45.123456+00:00
        >>> now.tzinfo
        datetime.timezone.utc
    """
    return datetime.now(timezone.utc)


def format_iso(dt: Optional[datetime]) -> Optional[str]:
    """
    Formate une datetime en ISO 8601 pour JSON.

    Args:
        dt: Datetime à formater (peut être None)

    Returns:
        str | None: Format ISO ou None

    Example:
        >>> dt = utc_now()
        >>> format_iso(dt)
        '2025-12-05T15:30:45.123456+00:00'
    """
    return dt.isoformat() if dt else None


def parse_iso(iso_string: str) -> datetime:
    """
    Parse une string ISO 8601 en datetime.

    Args:
        iso_string: String au format ISO 8601

    Returns:
        datetime: Datetime parsée (timezone-aware)

    Raises:
        ValueError: Si format invalide

    Example:
        >>> parse_iso('2025-12-05T15:30:45.123456+00:00')
        datetime.datetime(2025, 12, 5, 15, 30, 45, 123456, tzinfo=timezone.utc)
    """
    return datetime.fromisoformat(iso_string)
```

---

### Étape 2/3 : Mettre à Jour ProductService

**Fichier**: `services/product_service.py`

**Changement 1 - Ajouter l'import (ligne ~10)**
```python
# Existing imports
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

# ... existing imports ...

# ✅ AJOUTER CET IMPORT
from shared.datetime_utils import utc_now
```

**Changement 2 - Ligne 350 (soft delete)**
```python
# ❌ AVANT
product.deleted_at = func.now()

# ✅ APRÈS
product.deleted_at = utc_now()
```

**Changement 3 - Ligne 533 (publication)**
```python
# ❌ AVANT
product.published_at = func.now()

# ✅ APRÈS
product.published_at = utc_now()
```

**Changement 4 - Ligne 537 (vente)**
```python
# ❌ AVANT
product.sold_at = func.now()

# ✅ APRÈS
product.sold_at = utc_now()
```

---

### Étape 3/3 : Tests de Vérification

**Fichier**: `tests/test_datetime_utils.py` (NOUVEAU)

```python
"""
Tests pour datetime_utils

Vérifie que les fonctions utilitaires datetime fonctionnent correctement.
"""

from datetime import datetime, timezone
from shared.datetime_utils import utc_now, format_iso, parse_iso


def test_utc_now_returns_timezone_aware():
    """Test que utc_now() retourne bien une datetime timezone-aware."""
    now = utc_now()

    assert isinstance(now, datetime)
    assert now.tzinfo is not None
    assert now.tzinfo == timezone.utc


def test_utc_now_returns_current_time():
    """Test que utc_now() retourne l'heure actuelle (à quelques secondes près)."""
    before = datetime.now(timezone.utc)
    now = utc_now()
    after = datetime.now(timezone.utc)

    assert before <= now <= after


def test_format_iso_with_datetime():
    """Test format_iso() avec une datetime valide."""
    dt = datetime(2025, 12, 5, 15, 30, 45, 123456, tzinfo=timezone.utc)
    result = format_iso(dt)

    assert result == "2025-12-05T15:30:45.123456+00:00"


def test_format_iso_with_none():
    """Test format_iso() avec None."""
    assert format_iso(None) is None


def test_parse_iso():
    """Test parse_iso() avec une string ISO valide."""
    iso_str = "2025-12-05T15:30:45.123456+00:00"
    result = parse_iso(iso_str)

    assert isinstance(result, datetime)
    assert result.year == 2025
    assert result.month == 12
    assert result.day == 5
    assert result.hour == 15
    assert result.minute == 30
    assert result.second == 45
    assert result.microsecond == 123456
    assert result.tzinfo is not None


def test_roundtrip_iso_conversion():
    """Test que format_iso() et parse_iso() sont symétriques."""
    original = utc_now()
    iso_str = format_iso(original)
    parsed = parse_iso(iso_str)

    # Compare timestamps (microsecond precision)
    assert parsed == original
```

**Commande pour exécuter les tests**:
```bash
pytest tests/test_datetime_utils.py -v
```

---

### Vérification du Fix

**Test manuel** :
```bash
# 1. Créer un produit
POST /api/products/
{
  "title": "Test Product",
  "description": "Test",
  "price": 10.00,
  "category": "Jeans",
  "condition": "GOOD",
  "stock_quantity": 1
}

# 2. Publier le produit
PATCH /api/products/{id}/status?new_status=PUBLISHED

# 3. Vérifier published_at
GET /api/products/{id}

# Vérifier que published_at est une vraie datetime:
# ✅ "published_at": "2025-12-05T15:30:45.123456+00:00"
# ❌ "published_at": "now()" ou objet bizarre
```

---

## ✅ BUG #2 : Produits Supprimés Modifiables

### Résultat de l'Analyse

**✅ PAS DE BUG !**

Le code utilise déjà correctement `get_product_by_id()` qui filtre `deleted_at == None` dans toutes les méthodes :
- ✅ `update_product()` - ligne 288
- ✅ `update_product_status()` - ligne 510
- ✅ `add_image()` - ligne 380

**Aucune action requise.**

---

## 🔴 BUG #3 : Références Circulaires Categories

### Problème

```python
# Scénario catastrophe
Clothing (parent: None)
Jeans (parent: Clothing)
Skinny (parent: Jeans)

# Admin fait une erreur:
UPDATE categories SET parent_category = 'Skinny' WHERE name_en = 'Clothing';

# Résultat: BOUCLE INFINIE
Clothing → Jeans → Skinny → Clothing → ...
```

### Solution Choisie: Protection 3 Couches

**Effort**: 1 heure
**Protection**: Defense-in-depth

---

### Couche 1/3 : Contrainte CHECK en SQL

**Fichier**: `migrations/versions/YYYYMMDD_HHMM_add_category_circular_ref_check.py` (NOUVEAU)

```python
"""Add circular reference check for categories

Revision ID: add_category_check
Revises: <previous_revision_id>
Create Date: 2025-12-05

Business Rules:
- Empêche une catégorie d'être son propre parent
- Première ligne de défense au niveau base de données
"""

from alembic import op


def upgrade():
    """Add CHECK constraint to prevent direct self-reference."""
    # Add CHECK constraint
    op.execute("""
        ALTER TABLE public.categories
        ADD CONSTRAINT chk_category_not_self_parent
        CHECK (name_en <> parent_category)
    """)


def downgrade():
    """Remove CHECK constraint."""
    op.execute("""
        ALTER TABLE public.categories
        DROP CONSTRAINT IF EXISTS chk_category_not_self_parent
    """)
```

**Commande pour appliquer** :
```bash
alembic upgrade head
```

---

### Couche 2/3 : Méthode Safe avec Protection

**Fichier**: `models/public/category.py`

**Remplacer la méthode `get_full_path()` (lignes 77-86)** :

```python
def get_full_path(self, max_depth: int = 10) -> str:
    """
    Retourne le chemin complet de la catégorie avec protection contre boucles.

    Business Rules (2025-12-05):
    - Protection contre références circulaires
    - Limite de profondeur configurable (défaut: 10 niveaux)
    - Format: "Parent > Enfant > Petit-enfant"

    Args:
        max_depth: Profondeur maximale de la hiérarchie (défaut: 10)

    Returns:
        str: Chemin complet de la catégorie

    Raises:
        ValueError: Si boucle circulaire détectée

    Example:
        >>> category = Category(name_en="Skinny Jeans")
        >>> category.get_full_path()
        "Clothing > Jeans > Skinny Jeans"
    """
    path = [self.name_en]
    current = self
    visited = {self.name_en}  # Track visited nodes to detect cycles

    depth = 0
    while current.parent_category and depth < max_depth:
        # Circular reference detection
        if current.parent_category in visited:
            raise ValueError(
                f"Circular reference detected in category hierarchy: "
                f"{' > '.join(path)} > {current.parent_category}"
            )

        visited.add(current.parent_category)
        path.append(current.parent_category)
        current = current.parent
        depth += 1

    if depth >= max_depth:
        raise ValueError(
            f"Category hierarchy too deep (>{max_depth} levels): "
            f"{' > '.join(path)}"
        )

    return " > ".join(reversed(path))


def get_depth(self, max_depth: int = 10) -> int:
    """
    Retourne la profondeur de la catégorie dans la hiérarchie.

    Args:
        max_depth: Profondeur maximale autorisée (protection contre boucles)

    Returns:
        int: Profondeur (0 = racine, 1 = niveau 1, etc.)

    Raises:
        ValueError: Si boucle circulaire détectée ou profondeur excessive

    Example:
        >>> root = Category(name_en="Clothing", parent_category=None)
        >>> root.get_depth()
        0
        >>> child = Category(name_en="Jeans", parent_category="Clothing")
        >>> child.get_depth()
        1
    """
    depth = 0
    current = self
    visited = {self.name_en}

    while current.parent_category and depth < max_depth:
        if current.parent_category in visited:
            raise ValueError(
                f"Circular reference detected at depth {depth}"
            )

        visited.add(current.parent_category)
        current = current.parent
        depth += 1

    if depth >= max_depth:
        raise ValueError(f"Category hierarchy exceeds max depth: {max_depth}")

    return depth
```

---

### Couche 3/3 : Validation Python dans Service

**Fichier**: `services/category_service.py` (NOUVEAU)

```python
"""
Category Service

Service pour gérer les catégories avec validation de hiérarchie.

Business Rules (2025-12-05):
- Empêche les références circulaires
- Limite de profondeur hiérarchique
- Validation avant toute insertion/modification
"""

from typing import Optional

from sqlalchemy.orm import Session

from models.public.category import Category


class CategoryService:
    """Service pour les opérations sur les catégories."""

    MAX_HIERARCHY_DEPTH = 5  # Maximum 5 niveaux de profondeur

    @staticmethod
    def validate_parent_category(
        db: Session, category_name: str, parent_name: Optional[str]
    ) -> None:
        """
        Valide qu'un parent category est valide et ne crée pas de cycle.

        Business Rules:
        - Parent doit exister
        - Pas d'auto-référence (déjà protégé par CHECK constraint)
        - Pas de cycle indirect (A > B > C > A)
        - Profondeur maximale respectée

        Args:
            db: Session SQLAlchemy
            category_name: Nom de la catégorie à valider
            parent_name: Nom du parent (None pour catégorie racine)

        Raises:
            ValueError: Si validation échoue
        """
        # Catégorie racine (pas de parent) → OK
        if not parent_name:
            return

        # Auto-référence (normalement empêchée par CHECK mais on vérifie)
        if category_name == parent_name:
            raise ValueError(
                f"Category '{category_name}' cannot be its own parent"
            )

        # Vérifier que le parent existe
        parent = db.query(Category).filter(Category.name_en == parent_name).first()
        if not parent:
            raise ValueError(f"Parent category '{parent_name}' does not exist")

        # Vérifier que le parent n'aurait pas category_name dans SES parents
        # (empêche cycle indirect: A > B, puis B > A)
        try:
            parent_path = parent.get_full_path(max_depth=CategoryService.MAX_HIERARCHY_DEPTH)

            if category_name in parent_path:
                raise ValueError(
                    f"Circular reference detected: '{category_name}' is already "
                    f"an ancestor of '{parent_name}' ({parent_path})"
                )
        except ValueError as e:
            # Si le parent lui-même a un problème de cycle
            raise ValueError(
                f"Cannot set parent '{parent_name}': {str(e)}"
            )

        # Vérifier que la profondeur ne dépasse pas la limite
        try:
            parent_depth = parent.get_depth(max_depth=CategoryService.MAX_HIERARCHY_DEPTH)

            if parent_depth + 1 >= CategoryService.MAX_HIERARCHY_DEPTH:
                raise ValueError(
                    f"Cannot add category: would exceed maximum hierarchy depth "
                    f"({CategoryService.MAX_HIERARCHY_DEPTH} levels). "
                    f"Parent '{parent_name}' is already at depth {parent_depth}."
                )
        except ValueError as e:
            raise ValueError(
                f"Cannot validate parent depth: {str(e)}"
            )

    @staticmethod
    def create_category(
        db: Session,
        name_en: str,
        parent_category: Optional[str] = None,
        name_fr: Optional[str] = None,
        name_de: Optional[str] = None,
        name_it: Optional[str] = None,
        name_es: Optional[str] = None,
    ) -> Category:
        """
        Crée une nouvelle catégorie avec validation de hiérarchie.

        Args:
            db: Session SQLAlchemy
            name_en: Nom en anglais (clé primaire)
            parent_category: Nom du parent (optionnel)
            name_fr: Nom en français (optionnel)
            name_de: Nom en allemand (optionnel)
            name_it: Nom en italien (optionnel)
            name_es: Nom en espagnol (optionnel)

        Returns:
            Category: La catégorie créée

        Raises:
            ValueError: Si validation échoue
        """
        # Valider le parent
        CategoryService.validate_parent_category(db, name_en, parent_category)

        # Créer la catégorie
        category = Category(
            name_en=name_en,
            parent_category=parent_category,
            name_fr=name_fr,
            name_de=name_de,
            name_it=name_it,
            name_es=name_es,
        )

        db.add(category)
        db.commit()
        db.refresh(category)

        return category

    @staticmethod
    def update_category_parent(
        db: Session, category_name: str, new_parent_name: Optional[str]
    ) -> Category:
        """
        Met à jour le parent d'une catégorie avec validation.

        Args:
            db: Session SQLAlchemy
            category_name: Nom de la catégorie à modifier
            new_parent_name: Nouveau parent (None pour catégorie racine)

        Returns:
            Category: La catégorie modifiée

        Raises:
            ValueError: Si validation échoue ou catégorie non trouvée
        """
        category = db.query(Category).filter(Category.name_en == category_name).first()
        if not category:
            raise ValueError(f"Category '{category_name}' not found")

        # Valider le nouveau parent
        CategoryService.validate_parent_category(db, category_name, new_parent_name)

        # Mettre à jour
        category.parent_category = new_parent_name
        db.commit()
        db.refresh(category)

        return category
```

---

### Tests de Vérification

**Fichier**: `tests/test_category_circular_refs.py` (NOUVEAU)

```python
"""
Tests pour la protection contre références circulaires dans categories.

Ces tests vérifient les 3 couches de protection:
1. CHECK constraint SQL
2. Méthodes model avec protection
3. Validation service
"""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.public.category import Category
from services.category_service import CategoryService


def test_check_constraint_prevents_self_reference(db: Session):
    """Test que la contrainte CHECK empêche l'auto-référence."""
    # Tenter de créer une catégorie qui est son propre parent
    category = Category(
        name_en="SelfRef",
        parent_category="SelfRef"  # ❌ Interdit par CHECK constraint
    )
    db.add(category)

    with pytest.raises(IntegrityError) as exc:
        db.commit()

    assert "chk_category_not_self_parent" in str(exc.value)


def test_get_full_path_detects_circular_reference(db: Session):
    """Test que get_full_path() détecte les cycles."""
    # Créer cycle manuellement (sans validation)
    cat_a = Category(name_en="A", parent_category="C")
    cat_b = Category(name_en="B", parent_category="A")
    cat_c = Category(name_en="C", parent_category="B")

    db.add_all([cat_a, cat_b, cat_c])
    db.commit()

    # Tenter de récupérer le chemin → doit détecter le cycle
    with pytest.raises(ValueError) as exc:
        cat_a.get_full_path()

    assert "Circular reference detected" in str(exc.value)


def test_get_full_path_max_depth(db: Session):
    """Test que get_full_path() respecte la profondeur max."""
    # Créer hiérarchie très profonde
    root = Category(name_en="Root", parent_category=None)
    db.add(root)

    current_parent = "Root"
    for i in range(15):  # Créer 15 niveaux
        cat = Category(name_en=f"Level{i}", parent_category=current_parent)
        db.add(cat)
        current_parent = f"Level{i}"

    db.commit()

    # Récupérer dernière catégorie
    deep_cat = db.query(Category).filter(Category.name_en == "Level14").first()

    # Tenter get_full_path avec max_depth=10 → doit échouer
    with pytest.raises(ValueError) as exc:
        deep_cat.get_full_path(max_depth=10)

    assert "too deep" in str(exc.value).lower()


def test_service_validates_parent_exists(db: Session):
    """Test que CategoryService valide l'existence du parent."""
    with pytest.raises(ValueError) as exc:
        CategoryService.create_category(
            db,
            name_en="Test",
            parent_category="NonExistent"  # ❌ Parent n'existe pas
        )

    assert "does not exist" in str(exc.value)


def test_service_prevents_indirect_cycle(db: Session):
    """Test que CategoryService empêche les cycles indirects."""
    # Créer A > B > C
    CategoryService.create_category(db, name_en="A", parent_category=None)
    CategoryService.create_category(db, name_en="B", parent_category="A")
    CategoryService.create_category(db, name_en="C", parent_category="B")

    # Tenter de faire C > A (créerait cycle A > B > C > A)
    with pytest.raises(ValueError) as exc:
        CategoryService.update_category_parent(db, "A", "C")

    assert "Circular reference" in str(exc.value)


def test_service_enforces_max_depth(db: Session):
    """Test que CategoryService respecte MAX_HIERARCHY_DEPTH."""
    # Créer hiérarchie à la limite (profondeur = MAX_DEPTH - 1)
    CategoryService.create_category(db, name_en="L0", parent_category=None)
    CategoryService.create_category(db, name_en="L1", parent_category="L0")
    CategoryService.create_category(db, name_en="L2", parent_category="L1")
    CategoryService.create_category(db, name_en="L3", parent_category="L2")

    # Tenter d'ajouter un niveau de plus → doit échouer si MAX_DEPTH = 5
    with pytest.raises(ValueError) as exc:
        CategoryService.create_category(db, name_en="L4", parent_category="L3")

    assert "exceed maximum hierarchy depth" in str(exc.value)


def test_valid_hierarchy_works(db: Session):
    """Test qu'une hiérarchie valide fonctionne correctement."""
    # Créer hiérarchie valide
    root = CategoryService.create_category(db, name_en="Clothing", parent_category=None)
    child = CategoryService.create_category(db, name_en="Jeans", parent_category="Clothing")
    grandchild = CategoryService.create_category(
        db, name_en="Skinny Jeans", parent_category="Jeans"
    )

    # Vérifier chemins
    assert root.get_full_path() == "Clothing"
    assert child.get_full_path() == "Clothing > Jeans"
    assert grandchild.get_full_path() == "Clothing > Jeans > Skinny Jeans"

    # Vérifier profondeurs
    assert root.get_depth() == 0
    assert child.get_depth() == 1
    assert grandchild.get_depth() == 2
```

**Commande pour exécuter les tests** :
```bash
pytest tests/test_category_circular_refs.py -v
```

---

## 📊 Checklist d'Application

### Bug #1: func.now()

- [ ] Créer `shared/datetime_utils.py`
- [ ] Ajouter import dans `services/product_service.py`
- [ ] Remplacer ligne 350: `product.deleted_at = func.now()` → `utc_now()`
- [ ] Remplacer ligne 533: `product.published_at = func.now()` → `utc_now()`
- [ ] Remplacer ligne 537: `product.sold_at = func.now()` → `utc_now()`
- [ ] Créer `tests/test_datetime_utils.py`
- [ ] Exécuter tests: `pytest tests/test_datetime_utils.py -v`
- [ ] Tester manuellement: créer/publier un produit et vérifier timestamps

### Bug #2: Produits supprimés

- [x] Vérifier que le code utilise `get_product_by_id()` ✅ DÉJÀ OK
- [x] Aucune action requise

### Bug #3: Références circulaires

- [ ] Créer migration Alembic avec CHECK constraint
- [ ] Exécuter migration: `alembic upgrade head`
- [ ] Mettre à jour `models/public/category.py` (méthodes `get_full_path` et `get_depth`)
- [ ] Créer `services/category_service.py`
- [ ] Ajouter exports dans `services/__init__.py`
- [ ] Créer `tests/test_category_circular_refs.py`
- [ ] Exécuter tests: `pytest tests/test_category_circular_refs.py -v`
- [ ] Tester manuellement: tenter de créer cycle via API

---

## 🎯 Prochaines Étapes

Après application de ces fixes:

1. **Review duplication de code** (140 lignes → 10 lignes, ROI énorme)
2. **Edge cases business logic** (38 cas identifiés)
3. **Vulnérabilités sécurité** (SQL injection, CSRF, XSS)
4. **Refactoring attribute models** (base class multilingual)

**Effort total fixes critiques**: ~1.5 heures
**Impact**: Code stable, maintenable, production-ready
