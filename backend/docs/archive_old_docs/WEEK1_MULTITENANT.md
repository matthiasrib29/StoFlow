# Week 1-2 : Architecture Multi-Tenant - Guide Détaillé

**Projet :** Stoflow Backend
**Durée :** 10 jours (adaptable selon disponibilité)
**Objectif :** Mettre en place l'architecture multi-tenant complète avec authentification

---

## 📋 Vue d'Ensemble Week 1-2

### Ce qui sera accompli

- ✅ Models SQLAlchemy (schema public + tenant)
- ✅ Migrations Alembic multi-schema
- ✅ API authentification JWT
- ✅ Middleware multi-tenant
- ✅ Repositories pour accès données
- ✅ Tests unitaires complets

### Prérequis

- ✅ Week 0 complétée
- ✅ Docker services opérationnels
- ✅ Configuration testée

---

## 📅 Planning Détaillé

### Jour 1-2 : Models SQLAlchemy Schema Public (4-6h)

#### Étape 1.1 : Model Tenant (1h30)

**Objectif :** Créer le model pour stocker les informations des clients (tenants)

**Créer `models/public/tenant.py` :**

```python
"""
Model Tenant - Représente un client de la plateforme.
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from shared.database import Base


class Tenant(Base):
    """
    Tenant représente un client (entreprise ou particulier) utilisant Stoflow.
    Chaque tenant a son propre schema PostgreSQL pour l'isolation des données.
    """
    __tablename__ = 'tenants'
    __table_args__ = {'schema': 'public'}

    # Identité
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment="Nom du client")
    email = Column(String(255), unique=True, nullable=False, index=True, comment="Email principal")

    # Subscription
    subscription_tier = Column(
        String(50),
        nullable=False,
        default='starter',
        comment="Tier: starter, standard, premium, business, enterprise"
    )
    subscription_status = Column(
        String(50),
        nullable=False,
        default='active',
        comment="Status: active, suspended, cancelled"
    )

    # Limites par tier
    max_products = Column(Integer, default=50, comment="Nombre max de produits")
    max_platforms = Column(Integer, default=2, comment="Nombre max de plateformes")
    ai_credits_monthly = Column(Integer, default=0, comment="Crédits IA par mois")

    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant(id={self.id}, name='{self.name}', tier='{self.subscription_tier}')>"

    @property
    def schema_name(self) -> str:
        """Retourne le nom du schema PostgreSQL pour ce tenant."""
        return f"client_{self.id}"
```

**Actions :**
```bash
# Créer le fichier
touch models/public/tenant.py
# Copier le code ci-dessus
```

---

#### Étape 1.2 : Model User (1h30)

**Objectif :** Créer le model pour les utilisateurs avec authentification

**Créer `models/public/user.py` :**

```python
"""
Model User - Représente un utilisateur de la plateforme.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from shared.database import Base


class User(Base):
    """
    User représente un utilisateur pouvant se connecter à Stoflow.
    Chaque user appartient à un tenant.
    """
    __tablename__ = 'users'
    __table_args__ = {'schema': 'public'}

    # Identité
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey('public.tenants.id', ondelete='CASCADE'), nullable=False, index=True)

    # Credentials
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False, comment="Mot de passe hashé avec bcrypt")

    # Profile
    full_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    # Role & Permissions
    role = Column(
        String(50),
        nullable=False,
        default='user',
        comment="Roles: admin, user, viewer"
    )

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False, comment="Email vérifié")

    # Metadata
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    tenant = relationship("Tenant", back_populates="users")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', tenant_id={self.tenant_id})>"
```

---

#### Étape 1.3 : Model Subscription (1h)

**Objectif :** Détailler les abonnements et historique de paiement

**Créer `models/public/subscription.py` :**

```python
"""
Model Subscription - Historique des abonnements.
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from shared.database import Base


class Subscription(Base):
    """
    Subscription stocke l'historique des abonnements d'un tenant.
    """
    __tablename__ = 'subscriptions'
    __table_args__ = {'schema': 'public'}

    # Identité
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey('public.tenants.id', ondelete='CASCADE'), nullable=False, index=True)

    # Détails abonnement
    tier = Column(String(50), nullable=False, comment="starter, standard, premium, business, enterprise")
    price_monthly = Column(Numeric(10, 2), nullable=False, comment="Prix mensuel en euros")
    currency = Column(String(3), default='EUR', nullable=False)

    # Période
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True, comment="Null = abonnement actif")

    # Status
    status = Column(
        String(50),
        nullable=False,
        default='active',
        comment="active, cancelled, expired, suspended"
    )

    # Payment
    payment_method = Column(String(50), nullable=True, comment="stripe, paypal, etc.")
    last_payment_date = Column(DateTime, nullable=True)
    next_billing_date = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    tenant = relationship("Tenant")

    def __repr__(self):
        return f"<Subscription(id={self.id}, tenant_id={self.tenant_id}, tier='{self.tier}')>"
```

---

#### Étape 1.4 : Model PlatformMapping (1h)

**Objectif :** Stocker les mappings de marques/catégories réutilisables

**Créer `models/public/platform_mapping.py` :**

```python
"""
Model PlatformMapping - Templates de mapping réutilisables.
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from shared.database import Base


class PlatformMapping(Base):
    """
    PlatformMapping stocke les correspondances entre nos données
    et les IDs des plateformes (ex: marque Nike → brand_id Vinted).
    """
    __tablename__ = 'platform_mappings'
    __table_args__ = {'schema': 'public'}

    # Identité
    id = Column(Integer, primary_key=True, index=True)

    # Platform
    platform = Column(String(50), nullable=False, index=True, comment="vinted, ebay, etsy, etc.")

    # Type de mapping
    mapping_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="brand, category, color, size, condition, material"
    )

    # Valeurs
    our_value = Column(String(255), nullable=False, index=True, comment="Notre valeur standardisée")
    platform_value = Column(String(255), nullable=False, comment="Valeur sur la plateforme")
    platform_id = Column(Integer, nullable=True, comment="ID sur la plateforme si applicable")

    # Metadata
    usage_count = Column(Integer, default=0, comment="Nombre d'utilisations (pour stats)")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PlatformMapping(platform='{self.platform}', type='{self.mapping_type}', {self.our_value}→{self.platform_value})>"
```

---

### Jour 3-4 : Models SQLAlchemy Schema Tenant (4-6h)

#### Étape 2.1 : Model Product (2h)

**Objectif :** Créer le model pour les produits (dans schema client_X)

**Créer `models/tenant/product.py` :**

```python
"""
Model Product - Produit d'un client (isolé dans son schema).
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, Boolean

from shared.database import Base


class Product(Base):
    """
    Product représente un produit d'un client.
    Stocké dans le schema client_{tenant_id} pour isolation.
    """
    __tablename__ = 'products'
    # Pas de __table_args__ car le schema est défini dynamiquement via search_path

    # Identité
    sku = Column(String(100), primary_key=True, comment="SKU unique du produit")

    # Informations produit
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    # Prix & Stock
    price = Column(Float, nullable=False, comment="Prix de vente")
    cost_price = Column(Float, nullable=True, comment="Prix d'achat/coût")
    stock_quantity = Column(Integer, default=1, nullable=False)

    # Attributs
    brand = Column(String(255), nullable=True)
    category = Column(String(255), nullable=True)
    size = Column(String(50), nullable=True)
    color = Column(String(100), nullable=True)
    material = Column(String(255), nullable=True)
    condition = Column(String(50), nullable=True, comment="neuf, très bon état, bon état, etc.")

    # Images
    image_url_1 = Column(String(1000), nullable=True)
    image_url_2 = Column(String(1000), nullable=True)
    image_url_3 = Column(String(1000), nullable=True)
    image_url_4 = Column(String(1000), nullable=True)
    image_url_5 = Column(String(1000), nullable=True)

    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Product(sku='{self.sku}', title='{self.title[:30]}...')>"
```

---

#### Étape 2.2 : Model VintedProduct (1h30)

**Objectif :** Stocker les données spécifiques à Vinted

**Créer `models/tenant/vinted_product.py` :**

```python
"""
Model VintedProduct - Données spécifiques Vinted d'un produit.
"""
from datetime import datetime

from sqlalchemy import Column, BigInteger, DateTime, Float, ForeignKey, String, Text

from shared.database import Base


class VintedProduct(Base):
    """
    VintedProduct stocke les informations spécifiques à la publication sur Vinted.
    """
    __tablename__ = 'vinted_products'

    # Relation avec Product
    sku = Column(String(100), ForeignKey('products.sku', ondelete='CASCADE'), primary_key=True)

    # Identifiants Vinted
    id_vinted = Column(BigInteger, unique=True, nullable=True, index=True, comment="ID produit sur Vinted")
    url_vinted = Column(String(1000), nullable=True, comment="URL du produit sur Vinted")

    # Statut
    status = Column(
        String(50),
        nullable=False,
        default='draft',
        comment="draft, published, sold, deleted, error"
    )

    # Prix spécifique Vinted
    price_vinted = Column(Float, nullable=True, comment="Prix final sur Vinted (peut différer)")

    # Informations publication
    published_at = Column(DateTime, nullable=True)
    last_synced_at = Column(DateTime, nullable=True, comment="Dernière sync avec Vinted")

    # Statistiques Vinted
    views_count = Column(BigInteger, default=0)
    favorites_count = Column(BigInteger, default=0)

    # Erreurs
    last_error = Column(Text, nullable=True)
    error_count = Column(BigInteger, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<VintedProduct(sku='{self.sku}', id_vinted={self.id_vinted}, status='{self.status}')>"
```

---

#### Étape 2.3 : Model PublicationHistory (1h)

**Objectif :** Historique des publications sur toutes plateformes

**Créer `models/tenant/publication_history.py` :**

```python
"""
Model PublicationHistory - Historique des publications.
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Boolean

from shared.database import Base


class PublicationHistory(Base):
    """
    PublicationHistory trace toutes les tentatives de publication.
    """
    __tablename__ = 'publications_history'

    # Identité
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(100), ForeignKey('products.sku', ondelete='CASCADE'), nullable=False, index=True)

    # Plateforme
    platform = Column(String(50), nullable=False, index=True, comment="vinted, ebay, etsy, etc.")

    # Détails publication
    action = Column(String(50), nullable=False, comment="create, update, delete")
    status = Column(String(50), nullable=False, comment="pending, success, error")

    # Erreur
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)

    # RQ Job
    job_id = Column(String(100), nullable=True, index=True, comment="ID du job RQ")

    # Timing
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<PublicationHistory(id={self.id}, sku='{self.sku}', platform='{self.platform}', status='{self.status}')>"
```

---

#### Étape 2.4 : Model AIGenerationLog (30min)

**Objectif :** Logger les générations de descriptions par IA

**Créer `models/tenant/ai_generation_log.py` :**

```python
"""
Model AIGenerationLog - Log des générations IA.
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Numeric, Boolean

from shared.database import Base


class AIGenerationLog(Base):
    """
    AIGenerationLog trace toutes les générations de descriptions par IA.
    """
    __tablename__ = 'ai_generations_log'

    # Identité
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(100), ForeignKey('products.sku', ondelete='CASCADE'), nullable=False, index=True)

    # Paramètres génération
    platform = Column(String(50), nullable=False, comment="Plateforme cible")
    model = Column(String(100), nullable=False, comment="gpt-4-turbo, claude-3, etc.")
    prompt_template = Column(String(100), nullable=True)

    # Résultat
    generated_text = Column(Text, nullable=False)
    tokens_used = Column(Integer, nullable=True)
    cost = Column(Numeric(10, 6), nullable=True, comment="Coût en euros")

    # Cache
    was_cached = Column(Boolean, default=False, comment="Résultat depuis cache ?")
    cache_key = Column(String(255), nullable=True, index=True)

    # Timing
    generation_time_ms = Column(Integer, nullable=True, comment="Temps génération en ms")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AIGenerationLog(id={self.id}, sku='{self.sku}', platform='{self.platform}', cached={self.was_cached})>"
```

---

### Jour 5-6 : Migrations Alembic (4-6h)

#### Étape 3.1 : Migration Schema Public (2h)

**Objectif :** Créer la première migration pour les tables publiques

**Actions :**

```bash
# Activer venv
source venv/bin/activate

# Importer tous les models dans migrations/env.py
# (déjà fait à la Week 0, mais à compléter)
```

**Éditer `migrations/env.py` pour importer les models :**

```python
# Ligne 21-24, remplacer:
# Import all models here pour autodétection
# from models.public.tenant import Tenant
# from models.public.user import User
# ... autres imports quand les models seront créés

# Par:
# Import all models here pour autodétection
from models.public.tenant import Tenant
from models.public.user import User
from models.public.subscription import Subscription
from models.public.platform_mapping import PlatformMapping
```

**Créer la migration :**

```bash
# Générer migration automatique
alembic revision --autogenerate -m "create public schema tables"

# Vérifier le fichier généré dans migrations/versions/
# Devrait contenir la création de tenants, users, subscriptions, platform_mappings
```

**Appliquer la migration :**

```bash
alembic upgrade head

# Vérifier les tables créées
python scripts/verify_migration.py  # À créer
```

---

#### Étape 3.2 : Script Création Schema Client (1h)

**Objectif :** Créer un script pour initialiser un schema client avec toutes les tables

**Créer `scripts/create_tenant_schema.py` :**

```python
"""
Script pour créer un nouveau schema tenant avec toutes les tables.
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from shared.config import settings
from shared.database import get_db_context, create_tenant_schema
from models.tenant.product import Product
from models.tenant.vinted_product import VintedProduct
from models.tenant.publication_history import PublicationHistory
from models.tenant.ai_generation_log import AIGenerationLog


def create_tenant_with_schema(tenant_id: int) -> bool:
    """
    Crée le schema PostgreSQL pour un tenant et crée toutes les tables.

    Args:
        tenant_id: ID du tenant

    Returns:
        True si succès
    """
    try:
        schema_name = f"{settings.tenant_schema_prefix}{tenant_id}"

        print(f"🔨 Creating schema: {schema_name}")

        # 1. Créer le schema
        create_tenant_schema(tenant_id)
        print(f"   ✅ Schema {schema_name} created")

        # 2. Créer les tables dans ce schema
        with get_db_context() as db:
            # Set search_path to the new schema
            db.execute(text(f"SET search_path TO {schema_name}, public"))

            # Créer toutes les tables tenant
            from shared.database import Base
            Base.metadata.create_all(
                bind=db.get_bind(),
                tables=[
                    Product.__table__,
                    VintedProduct.__table__,
                    PublicationHistory.__table__,
                    AIGenerationLog.__table__,
                ]
            )

            db.commit()
            print(f"   ✅ Tables created in schema {schema_name}")

        # 3. Vérifier
        with get_db_context() as db:
            result = db.execute(text(f"""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = '{schema_name}'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"   ✅ Verified {len(tables)} tables: {', '.join(tables)}")

        return True

    except Exception as e:
        print(f"   ❌ Error creating tenant schema: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/create_tenant_schema.py <tenant_id>")
        sys.exit(1)

    tenant_id = int(sys.argv[1])
    success = create_tenant_with_schema(tenant_id)
    sys.exit(0 if success else 1)
```

**Tester :**

```bash
# Créer un schema de test
python scripts/create_tenant_schema.py 999

# Devrait créer client_999 avec 4 tables
```

---

#### Étape 3.3 : Migration Verification Script (30min)

**Créer `scripts/verify_migration.py` :**

```python
"""
Script pour vérifier les migrations Alembic.
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from shared.database import get_db_context


def verify_public_tables():
    """Vérifie que les tables public sont créées."""
    expected_tables = ['tenants', 'users', 'subscriptions', 'platform_mappings']

    with get_db_context() as db:
        result = db.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result.fetchall()]

    print("\n📋 PUBLIC SCHEMA TABLES:")
    for table in expected_tables:
        if table in tables:
            print(f"   ✅ {table}")
        else:
            print(f"   ❌ {table} - MISSING!")

    return all(table in tables for table in expected_tables)


def verify_alembic_version():
    """Vérifie la version Alembic."""
    with get_db_context() as db:
        result = db.execute(text("SELECT version_num FROM alembic_version"))
        version = result.scalar()

    print(f"\n🔢 ALEMBIC VERSION: {version if version else 'No migrations applied'}")
    return version is not None


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔍 VERIFYING MIGRATIONS")
    print("="*60)

    tables_ok = verify_public_tables()
    version_ok = verify_alembic_version()

    if tables_ok and version_ok:
        print("\n✅ All migrations verified successfully!\n")
        sys.exit(0)
    else:
        print("\n❌ Migration verification failed!\n")
        sys.exit(1)
```

---

### Jour 7-8 : API Authentification (6-8h)

#### Étape 4.1 : Service Authentification (2h)

**Créer `services/auth_service.py` :**

```python
"""
Service d'authentification JWT.
"""
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from models.public.user import User
from models.public.tenant import Tenant
from shared.config import settings

# Context pour hasher les mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe contre son hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash un mot de passe."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crée un token JWT.

    Args:
        data: Données à encoder dans le token
        expires_delta: Durée de validité

    Returns:
        Token JWT encodé
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )

    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Décode un token JWT.

    Args:
        token: Token JWT à décoder

    Returns:
        Payload du token ou None si invalide
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authentifie un utilisateur.

    Args:
        db: Session database
        email: Email de l'utilisateur
        password: Mot de passe en clair

    Returns:
        User si authentification réussie, None sinon
    """
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    if not user.is_active:
        return None

    return user


def create_user(
    db: Session,
    tenant_id: int,
    email: str,
    password: str,
    full_name: Optional[str] = None,
    role: str = "user"
) -> User:
    """
    Crée un nouvel utilisateur.

    Args:
        db: Session database
        tenant_id: ID du tenant
        email: Email de l'utilisateur
        password: Mot de passe en clair
        full_name: Nom complet (optionnel)
        role: Rôle (admin, user, viewer)

    Returns:
        User créé
    """
    hashed_password = get_password_hash(password)

    user = User(
        tenant_id=tenant_id,
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        role=role,
        is_active=True,
        is_verified=False
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user
```

---

#### Étape 4.2 : Service Tenant (1h30)

**Créer `services/tenant_service.py` :**

```python
"""
Service de gestion des tenants.
"""
from sqlalchemy.orm import Session

from models.public.tenant import Tenant
from models.public.user import User
from shared.database import create_tenant_schema
from services.auth_service import create_user


def create_tenant(
    db: Session,
    name: str,
    email: str,
    password: str,
    subscription_tier: str = "starter"
) -> tuple[Tenant, User]:
    """
    Crée un nouveau tenant avec son schema PostgreSQL et un utilisateur admin.

    Args:
        db: Session database
        name: Nom du tenant
        email: Email de l'admin
        password: Mot de passe de l'admin
        subscription_tier: Tier d'abonnement

    Returns:
        (Tenant, User) créés
    """
    # 1. Créer le tenant
    tenant = Tenant(
        name=name,
        email=email,
        subscription_tier=subscription_tier,
        subscription_status='active',
        max_products=get_max_products_for_tier(subscription_tier),
        max_platforms=get_max_platforms_for_tier(subscription_tier),
        ai_credits_monthly=get_ai_credits_for_tier(subscription_tier),
        is_active=True
    )

    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    # 2. Créer le schema PostgreSQL
    create_tenant_schema(tenant.id)

    # 3. Créer l'utilisateur admin
    user = create_user(
        db=db,
        tenant_id=tenant.id,
        email=email,
        password=password,
        full_name=name,
        role='admin'
    )

    return tenant, user


def get_max_products_for_tier(tier: str) -> int:
    """Retourne le nombre max de produits par tier."""
    limits = {
        'starter': 50,
        'standard': 200,
        'premium': 999999,  # Illimité
        'business': 999999,
        'enterprise': 999999
    }
    return limits.get(tier, 50)


def get_max_platforms_for_tier(tier: str) -> int:
    """Retourne le nombre max de plateformes par tier."""
    limits = {
        'starter': 2,
        'standard': 5,
        'premium': 999,  # Illimité
        'business': 999,
        'enterprise': 999
    }
    return limits.get(tier, 2)


def get_ai_credits_for_tier(tier: str) -> int:
    """Retourne les crédits IA mensuels par tier."""
    credits = {
        'starter': 0,  # Pas d'IA
        'standard': 100,
        'premium': 500,
        'business': 2000,
        'enterprise': 10000
    }
    return credits.get(tier, 0)


def get_tenant_by_id(db: Session, tenant_id: int) -> Tenant:
    """Récupère un tenant par ID."""
    return db.query(Tenant).filter(Tenant.id == tenant_id).first()


def update_tenant_subscription(
    db: Session,
    tenant_id: int,
    new_tier: str
) -> Tenant:
    """
    Met à jour l'abonnement d'un tenant.

    Args:
        db: Session database
        tenant_id: ID du tenant
        new_tier: Nouveau tier

    Returns:
        Tenant mis à jour
    """
    tenant = get_tenant_by_id(db, tenant_id)

    if not tenant:
        raise ValueError(f"Tenant {tenant_id} not found")

    tenant.subscription_tier = new_tier
    tenant.max_products = get_max_products_for_tier(new_tier)
    tenant.max_platforms = get_max_platforms_for_tier(new_tier)
    tenant.ai_credits_monthly = get_ai_credits_for_tier(new_tier)

    db.commit()
    db.refresh(tenant)

    return tenant
```

---

#### Étape 4.3 : Dependencies FastAPI (1h)

**Créer `api/dependencies/auth.py` :**

```python
"""
Dependencies FastAPI pour l'authentification.
"""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from models.public.user import User
from models.public.tenant import Tenant
from services.auth_service import decode_token
from shared.database import get_db

# Schéma de sécurité Bearer token
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Récupère l'utilisateur courant depuis le token JWT.

    Raises:
        HTTPException 401: Si token invalide ou utilisateur non trouvé
    """
    token = credentials.credentials

    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: int = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Tenant:
    """
    Récupère le tenant de l'utilisateur courant.

    Raises:
        HTTPException 404: Si tenant non trouvé
    """
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant account is inactive"
        )

    return tenant


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Vérifie que l'utilisateur courant est admin.

    Raises:
        HTTPException 403: Si l'utilisateur n'est pas admin
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user
```

---

#### Étape 4.4 : Routes Authentification (2h)

**Créer `api/routes/auth.py` :**

```python
"""
Routes d'authentification.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from models.public.user import User
from models.public.tenant import Tenant
from services.auth_service import authenticate_user, create_access_token
from services.tenant_service import create_tenant
from shared.database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================================
# Schemas Pydantic
# ============================================================================

class RegisterRequest(BaseModel):
    """Requête d'inscription."""
    name: str
    email: EmailStr
    password: str
    subscription_tier: Optional[str] = "starter"


class LoginRequest(BaseModel):
    """Requête de connexion."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Réponse avec token JWT."""
    access_token: str
    token_type: str = "bearer"
    user: dict
    tenant: dict


# ============================================================================
# Routes
# ============================================================================

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Inscription d'un nouveau tenant avec utilisateur admin.

    - Crée le tenant
    - Crée le schema PostgreSQL client_X
    - Crée l'utilisateur admin
    - Retourne un JWT token
    """
    # Vérifier si l'email existe déjà
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Créer tenant + schema + user
    tenant, user = create_tenant(
        db=db,
        name=request.name,
        email=request.email,
        password=request.password,
        subscription_tier=request.subscription_tier
    )

    # Générer token JWT
    access_token = create_access_token(
        data={
            "sub": user.id,
            "tenant_id": tenant.id,
            "role": user.role
        }
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        },
        tenant={
            "id": tenant.id,
            "name": tenant.name,
            "subscription_tier": tenant.subscription_tier,
            "schema_name": tenant.schema_name
        }
    )


@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Connexion d'un utilisateur.

    - Vérifie les credentials
    - Retourne un JWT token
    """
    user = authenticate_user(db, request.email, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Mettre à jour last_login
    user.last_login = datetime.utcnow()
    db.commit()

    # Récupérer tenant
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()

    # Générer token JWT
    access_token = create_access_token(
        data={
            "sub": user.id,
            "tenant_id": tenant.id,
            "role": user.role
        }
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        },
        tenant={
            "id": tenant.id,
            "name": tenant.name,
            "subscription_tier": tenant.subscription_tier,
            "schema_name": tenant.schema_name
        }
    )


@router.get("/session")
def get_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère la session actuelle.

    Protégé par JWT - nécessite un token valide.
    """
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()

    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role
        },
        "tenant": {
            "id": tenant.id,
            "name": tenant.name,
            "subscription_tier": tenant.subscription_tier,
            "schema_name": tenant.schema_name
        }
    }


# Import nécessaire pour get_current_user
from api.dependencies.auth import get_current_user
```

---

### Jour 9-10 : Middleware & Tests (4-6h)

#### Étape 5.1 : Middleware Multi-Tenant (2h)

**Créer `api/middleware/tenant.py` :**

```python
"""
Middleware pour gérer le multi-tenant automatiquement.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from services.auth_service import decode_token
from shared.database import SessionLocal, set_tenant_schema


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware qui configure automatiquement le search_path PostgreSQL
    en fonction du tenant de l'utilisateur authentifié.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Intercepte chaque requête et configure le tenant.
        """
        # Extraire le token JWT
        authorization = request.headers.get("Authorization")

        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            payload = decode_token(token)

            if payload:
                tenant_id = payload.get("tenant_id")

                if tenant_id:
                    # Stocker tenant_id dans request.state pour accès ultérieur
                    request.state.tenant_id = tenant_id

                    # Configurer le search_path pour cette requête
                    # Note: Ceci sera automatiquement appliqué aux sessions DB créées
                    # dans cette requête via le dependency get_db

        response = await call_next(request)
        return response
```

**Note :** Pour utiliser ce middleware correctement, il faudra modifier `shared/database.py:get_db()` pour appliquer le `set_tenant_schema()` automatiquement si `request.state.tenant_id` existe.

---

#### Étape 5.2 : Point d'Entrée API (1h)

**Créer `api/main.py` :**

```python
"""
Point d'entrée principal de l'API FastAPI.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.middleware.tenant import TenantMiddleware
from api.routes import auth
from shared.config import settings
from shared.logging_setup import logger

# Créer l'application FastAPI
app = FastAPI(
    title="Stoflow API",
    description="API backend pour Stoflow - Flow your products everywhere",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware Multi-Tenant
app.add_middleware(TenantMiddleware)

# Inclure les routes
app.include_router(auth.router, prefix="/api")

# Route de health check
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "stoflow-api"}


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Stoflow API",
        "version": "0.1.0",
        "docs": "/docs"
    }


# Event handlers
@app.on_event("startup")
async def startup_event():
    """Actions au démarrage de l'API."""
    logger.info("🚀 Starting Stoflow API")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Debug mode: {settings.debug}")


@app.on_event("shutdown")
async def shutdown_event():
    """Actions à l'arrêt de l'API."""
    logger.info("🛑 Shutting down Stoflow API")
```

---

#### Étape 5.3 : Tests Unitaires Auth (2h)

**Créer `tests/unit/test_auth_service.py` :**

```python
"""
Tests unitaires pour le service d'authentification.
"""
import pytest
from datetime import timedelta

from services.auth_service import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_token
)


def test_password_hashing():
    """Test du hashing de mot de passe."""
    password = "super_secret_password_123"
    hashed = get_password_hash(password)

    # Le hash ne doit pas être égal au mot de passe
    assert hashed != password

    # Le hash doit commencer par $2b$ (bcrypt)
    assert hashed.startswith("$2b$")

    # Vérification doit réussir
    assert verify_password(password, hashed) is True

    # Vérification avec mauvais mot de passe doit échouer
    assert verify_password("wrong_password", hashed) is False


def test_create_and_decode_token():
    """Test création et décodage de token JWT."""
    data = {
        "sub": 123,
        "tenant_id": 456,
        "role": "admin"
    }

    # Créer token avec expiration de 1 minute
    token = create_access_token(data, expires_delta=timedelta(minutes=1))

    # Token doit être une string non vide
    assert isinstance(token, str)
    assert len(token) > 0

    # Décoder le token
    decoded = decode_token(token)

    # Vérifier les données
    assert decoded is not None
    assert decoded["sub"] == 123
    assert decoded["tenant_id"] == 456
    assert decoded["role"] == "admin"
    assert "exp" in decoded


def test_decode_invalid_token():
    """Test décodage d'un token invalide."""
    invalid_token = "invalid.token.here"

    decoded = decode_token(invalid_token)

    # Doit retourner None pour token invalide
    assert decoded is None
```

---

#### Étape 5.4 : Tests API Auth (1h)

**Créer `tests/integration/test_api_auth.py` :**

```python
"""
Tests d'intégration pour l'API d'authentification.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.main import app
from shared.database import Base, get_db
from shared.config import settings

# Configuration pour tests
TEST_DATABASE_URL = "postgresql://stoflow_user:stoflow_dev_password_2024@localhost:5433/stoflow_test"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override de get_db pour utiliser la BDD de test."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Setup de la base de données de test."""
    # Créer toutes les tables
    Base.metadata.create_all(bind=engine)
    yield
    # Supprimer toutes les tables après les tests
    Base.metadata.drop_all(bind=engine)


def test_register():
    """Test inscription d'un nouveau tenant."""
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Test Company",
            "email": "test@example.com",
            "password": "test_password_123",
            "subscription_tier": "starter"
        }
    )

    assert response.status_code == 201
    data = response.json()

    # Vérifier la structure de la réponse
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

    assert "user" in data
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["role"] == "admin"

    assert "tenant" in data
    assert data["tenant"]["name"] == "Test Company"
    assert data["tenant"]["subscription_tier"] == "starter"


def test_register_duplicate_email():
    """Test inscription avec email déjà utilisé."""
    # Première inscription
    client.post(
        "/api/auth/register",
        json={
            "name": "Company 1",
            "email": "duplicate@example.com",
            "password": "password123"
        }
    )

    # Deuxième inscription avec même email
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Company 2",
            "email": "duplicate@example.com",
            "password": "password456"
        }
    )

    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_login():
    """Test connexion."""
    # D'abord s'inscrire
    client.post(
        "/api/auth/register",
        json={
            "name": "Login Test",
            "email": "login@example.com",
            "password": "login_password_123"
        }
    )

    # Puis se connecter
    response = client.post(
        "/api/auth/login",
        json={
            "email": "login@example.com",
            "password": "login_password_123"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["user"]["email"] == "login@example.com"


def test_login_wrong_password():
    """Test connexion avec mauvais mot de passe."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "login@example.com",
            "password": "wrong_password"
        }
    )

    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_get_session():
    """Test récupération de la session."""
    # S'inscrire
    register_response = client.post(
        "/api/auth/register",
        json={
            "name": "Session Test",
            "email": "session@example.com",
            "password": "session_password_123"
        }
    )

    token = register_response.json()["access_token"]

    # Récupérer la session
    response = client.get(
        "/api/auth/session",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["user"]["email"] == "session@example.com"
    assert data["tenant"]["name"] == "Session Test"


def test_get_session_no_token():
    """Test récupération session sans token."""
    response = client.get("/api/auth/session")

    assert response.status_code == 403  # Forbidden (pas de token)
```

---

## 📊 Checklist Complète Week 1-2

### Models SQLAlchemy
- [ ] `models/public/tenant.py` créé et testé
- [ ] `models/public/user.py` créé et testé
- [ ] `models/public/subscription.py` créé et testé
- [ ] `models/public/platform_mapping.py` créé et testé
- [ ] `models/tenant/product.py` créé et testé
- [ ] `models/tenant/vinted_product.py` créé et testé
- [ ] `models/tenant/publication_history.py` créé et testé
- [ ] `models/tenant/ai_generation_log.py` créé et testé

### Migrations Alembic
- [ ] Migration schema public appliquée
- [ ] Tables public créées et vérifiées
- [ ] Script `create_tenant_schema.py` créé
- [ ] Script `verify_migration.py` créé
- [ ] Test création schema client réussi

### Services
- [ ] `services/auth_service.py` créé
- [ ] `services/tenant_service.py` créé
- [ ] Hash passwords avec bcrypt fonctionne
- [ ] Création JWT tokens fonctionne
- [ ] Création tenant + schema fonctionne

### API FastAPI
- [ ] `api/main.py` créé
- [ ] `api/routes/auth.py` créé
- [ ] `api/dependencies/auth.py` créé
- [ ] `api/middleware/tenant.py` créé
- [ ] Endpoint `/auth/register` fonctionne
- [ ] Endpoint `/auth/login` fonctionne
- [ ] Endpoint `/auth/session` fonctionne
- [ ] Middleware CORS configuré
- [ ] Middleware multi-tenant configuré

### Tests
- [ ] `tests/unit/test_auth_service.py` créé
- [ ] `tests/integration/test_api_auth.py` créé
- [ ] Tous les tests unitaires passent
- [ ] Tous les tests d'intégration passent
- [ ] Coverage > 80%

### Documentation
- [ ] README.md mis à jour avec nouvelles routes
- [ ] Documentation Swagger accessible
- [ ] Exemples d'utilisation API documentés

---

## 🚀 Commandes Utiles Week 1-2

### Développement

```bash
# Activer venv
source venv/bin/activate

# Lancer l'API en mode dev
uvicorn api.main:app --reload --port 8000

# Accéder à la documentation
# http://localhost:8000/docs

# Créer une migration
alembic revision --autogenerate -m "description"

# Appliquer les migrations
alembic upgrade head

# Créer un schema tenant de test
python scripts/create_tenant_schema.py 1
```

### Tests

```bash
# Tous les tests
pytest

# Tests unitaires seulement
pytest tests/unit/ -v

# Tests avec coverage
pytest --cov=. --cov-report=html

# Ouvrir le rapport coverage
open htmlcov/index.html
```

### Debug API

```bash
# Test inscription
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Company",
    "email": "test@example.com",
    "password": "test123",
    "subscription_tier": "starter"
  }'

# Test login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123"
  }'

# Test session (avec token)
curl -X GET http://localhost:8000/api/auth/session \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## ⚠️ Points d'Attention

### Sécurité
- ⚠️ Toujours vérifier que `is_active` est `True`
- ⚠️ Ne jamais exposer les `hashed_password` dans les réponses API
- ⚠️ Valider les emails avant création
- ⚠️ Implémenter rate limiting sur `/auth/login` (à venir)

### Performance
- ⚠️ Utiliser `index=True` sur les colonnes fréquemment requêtées
- ⚠️ Ne pas charger toutes les relations par défaut (lazy loading)
- ⚠️ Limiter le nombre de requêtes par endpoint

### Multi-Tenant
- ⚠️ Toujours vérifier que le `search_path` est correctement configuré
- ⚠️ Ne jamais mélanger les données de différents tenants
- ⚠️ Tester l'isolation des données régulièrement

---

## 🎯 Résultat Attendu

À la fin de la Week 1-2, vous devez avoir :

1. ✅ **Architecture multi-tenant fonctionnelle**
   - 8 models SQLAlchemy créés
   - Migrations Alembic multi-schema
   - Isolation complète des données

2. ✅ **API authentification complète**
   - Inscription avec création tenant + schema
   - Login avec JWT
   - Routes protégées par JWT
   - Middleware multi-tenant

3. ✅ **Tests complets**
   - Tests unitaires services
   - Tests intégration API
   - Coverage > 80%

4. ✅ **Documentation**
   - Swagger UI accessible
   - README à jour
   - Exemples d'utilisation

---

## 📈 Prochaines Étapes (Week 3)

Après la Week 1-2, vous pourrez passer à :

**Week 3 : API Produits + Frontend**
- Routes CRUD produits
- Upload images
- Intégration avec le frontend Nuxt
- Dashboard liste produits

---

**Document créé le :** 2024-12-04
**Durée estimée :** 10 jours
**Dépendances :** Week 0 complétée

🚀 **Ready to build multi-tenant architecture!**
