# Système de Rôles - Récapitulatif de l'implémentation

## 🎯 Ce qui a été mis en place

### 1. **Trois rôles définis**

| Rôle | Description | Permissions |
|------|-------------|-------------|
| **ADMIN** | Super-utilisateur | • Accès complet à tout<br>• Gestion utilisateurs<br>• Modification abonnements<br>• Configuration système |
| **USER** | Utilisateur standard | • Gestion de SES produits uniquement<br>• Gestion de SES intégrations<br>• Ses statistiques<br>• Utilisation IA (limité par crédits) |
| **SUPPORT** | Assistance client | • Lecture seule sur TOUS les utilisateurs<br>• Lecture seule sur TOUTES les intégrations<br>• Réinitialisation mots de passe<br>• **Aucune modification possible** |

---

## 📂 Fichiers créés/modifiés

### Modèles
✅ **`models/public/user.py`**
- Ajout du rôle `SUPPORT` dans l'enum `UserRole`
- Documentation des permissions par rôle

### Dependencies (Protection des endpoints)
✅ **`api/dependencies/__init__.py`**
- `get_current_user()` - Récupère l'utilisateur authentifié
- `require_admin()` - Vérifie que l'utilisateur est ADMIN
- `require_admin_or_support()` - Vérifie ADMIN ou SUPPORT
- `require_role(*roles)` - Factory pour rôles multiples

### Helpers de vérification
✅ **`shared/ownership.py`** (nouveau)
- `check_resource_ownership()` - Vérifie qu'un USER possède une ressource
- `ensure_user_owns_resource()` - Raccourci automatique
- `can_modify_resource()` - Check si peut modifier
- `can_view_resource()` - Check si peut consulter

✅ **`shared/subscription_limits.py`** (nouveau)
- `check_product_limit()` - Vérifie limite produits
- `check_platform_limit()` - Vérifie limite plateformes
- `check_ai_credits()` - Vérifie crédits IA
- `SubscriptionLimitError` - Exception personnalisée

### Documentation
✅ **`docs/ROLE_EXAMPLES.md`** (nouveau)
- Guide complet avec exemples d'utilisation
- Patterns courants
- Tests recommandés

### Migration
✅ **`migrations/versions/20251209_1019_add_support_role_to_users.py`** (nouveau)
- Ajoute la valeur `'support'` à l'enum `user_role` PostgreSQL
- ⚠️ **À exécuter** : `alembic upgrade head`

---

## 🚀 Comment utiliser

### Exemple 1: Protéger un endpoint ADMIN uniquement
```python
from fastapi import APIRouter, Depends
from api.dependencies import require_admin
from models.public.user import User

router = APIRouter()

@router.post("/admin/users")
async def create_user(
    current_user: User = Depends(require_admin),  # ← Seul ADMIN peut accéder
    db: Session = Depends(get_db)
):
    # Code ici
    return {"message": "User created"}
```

### Exemple 2: USER ne peut accéder qu'à SES produits
```python
from api.dependencies import get_current_user
from shared.ownership import ensure_user_owns_resource

@router.get("/products/{product_id}")
async def get_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()

    # Vérifie ownership (ADMIN passe, USER doit être propriétaire)
    ensure_user_owns_resource(current_user, product, resource_type="produit")

    return product
```

### Exemple 3: Vérifier limite avant création
```python
from shared.subscription_limits import check_product_limit

@router.post("/products")
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Vérifie la limite AVANT de créer
    check_product_limit(current_user, db)  # Lève exception si limite atteinte

    # Créer le produit
    new_product = Product(user_id=current_user.id, **product_data.dict())
    db.add(new_product)
    db.commit()

    return new_product
```

---

## ⚙️ Configuration

### Règles d'isolation des données
- **USER** : Isolation stricte → ne voit QUE ses données
- **ADMIN** : Accès à toutes les données
- **SUPPORT** : Lecture seule sur toutes les données

### Limites d'abonnement
- Gérées **uniquement par subscription_tier** (pas par rôle)
- Comportement : **Avertissement + blocage** si limite atteinte
- Les limites ne s'appliquent pas aux ADMIN

---

## 📝 Prochaines étapes

### 1. Exécuter la migration
```bash
source venv/bin/activate
alembic upgrade head
```

### 2. Protéger les endpoints existants
Tu dois maintenant protéger tes endpoints en ajoutant les dependencies:

**Endpoints à protéger:**

#### **Admin uniquement** (`require_admin`)
- `POST /admin/users` - Créer utilisateur
- `PUT /users/{user_id}/role` - Changer rôle
- `PUT /users/{user_id}/subscription` - Modifier abonnement
- `DELETE /users/{user_id}` - Supprimer utilisateur

#### **Admin ou Support** (`require_admin_or_support`)
- `GET /users` - Lister tous les utilisateurs
- `GET /users/{user_id}` - Voir détails utilisateur
- `GET /integrations` - Voir toutes les intégrations
- `POST /users/{user_id}/reset-password` - Réinitialiser MDP

#### **User authentifié** (`get_current_user`)
- `GET /products` - Lister SES produits
- `POST /products` - Créer produit (+ vérifier limite)
- `PUT /products/{id}` - Modifier produit (+ vérifier ownership)
- `DELETE /products/{id}` - Supprimer produit (+ vérifier ownership)
- `POST /integrations/{platform}` - Connecter plateforme (+ vérifier limite)
- `POST /products/{id}/generate-description` - IA (+ vérifier crédits)

### 3. Ajouter les vérifications de limites
Dans les endpoints de création:
- `POST /products` → `check_product_limit()`
- `POST /integrations/{platform}` → `check_platform_limit()`
- `POST /products/{id}/generate-description` → `check_ai_credits()`

### 4. Tests à créer
- Test: USER ne peut pas accéder à endpoint ADMIN → 403
- Test: USER ne peut pas voir produits d'un autre USER → 403
- Test: Limite produits respectée → 403 si dépassement
- Test: ADMIN peut changer rôle d'un utilisateur → 200
- Test: SUPPORT peut voir utilisateurs mais pas modifier → 403

---

## 🛠️ Aide-mémoire

### Imports courants
```python
# Dependencies
from api.dependencies import get_current_user, require_admin, require_admin_or_support

# Ownership
from shared.ownership import ensure_user_owns_resource

# Limites
from shared.subscription_limits import check_product_limit, check_platform_limit, check_ai_credits

# Models
from models.public.user import User, UserRole
```

### Erreurs possibles
- **401 Unauthorized** : Token invalide/expiré
- **403 Forbidden** : Rôle insuffisant ou ownership invalide ou limite atteinte

---

## ✅ Statut actuel

- [x] Rôles définis (ADMIN, USER, SUPPORT)
- [x] Dependencies créées
- [x] Helpers ownership créés
- [x] Helpers limites créés
- [x] Migration créée
- [ ] **Migration à exécuter** (`alembic upgrade head`)
- [ ] **Endpoints à protéger** (voir section "Prochaines étapes")
- [ ] **Tests à créer**

---

## 📖 Documentation complète

Pour des exemples détaillés et tous les patterns, consulte:
- **`docs/ROLE_EXAMPLES.md`** - Guide complet avec 20+ exemples

---

**Système de rôles prêt à l'emploi** 🎉

Il ne reste plus qu'à:
1. Exécuter la migration
2. Ajouter les dependencies aux endpoints existants
3. Tester !
