# Guide d'utilisation du système de rôles

## Vue d'ensemble

Le système de rôles de Stoflow utilise les **Dependencies FastAPI** pour gérer les permissions.

### Rôles disponibles

| Rôle | Permissions |
|------|-------------|
| **ADMIN** | Accès complet : gestion utilisateurs, modification abonnements, accès à toutes les données |
| **USER** | Accès limité : gestion de ses propres produits, intégrations, statistiques |
| **SUPPORT** | Lecture seule : consultation de tous les utilisateurs et intégrations, réinitialisation MDP |

---

## 1. Protéger un endpoint avec un rôle spécifique

### Exemple : Endpoint réservé aux ADMIN

```python
from fastapi import APIRouter, Depends
from api.dependencies import require_admin
from models.public.user import User

router = APIRouter()

@router.post("/admin/users")
async def create_user(
    current_user: User = Depends(require_admin),  # ← Vérifie que l'utilisateur est ADMIN
    db: Session = Depends(get_db)
):
    # Seuls les ADMIN peuvent exécuter ce code
    # current_user contient l'utilisateur admin authentifié
    return {"message": "User created"}
```

### Exemple : Endpoint accessible par ADMIN ou SUPPORT

```python
from api.dependencies import require_admin_or_support

@router.get("/support/users/{user_id}")
async def get_user_details(
    user_id: int,
    current_user: User = Depends(require_admin_or_support),  # ← ADMIN ou SUPPORT
    db: Session = Depends(get_db)
):
    # ADMIN et SUPPORT peuvent consulter
    user = db.query(User).filter(User.id == user_id).first()
    return user
```

### Exemple : Endpoint avec plusieurs rôles autorisés (méthode flexible)

```python
from api.dependencies import require_role
from models.public.user import UserRole

@router.get("/data/export")
async def export_data(
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPPORT)),  # ← Multiple rôles
    db: Session = Depends(get_db)
):
    # ADMIN et SUPPORT peuvent exporter
    return {"data": "..."}
```

---

## 2. Vérifier l'ownership des ressources

### Exemple : USER ne peut accéder qu'à ses propres produits

```python
from fastapi import HTTPException, status
from api.dependencies import get_current_user
from shared.ownership import ensure_user_owns_resource

@router.get("/products/{product_id}")
async def get_product(
    product_id: int,
    current_user: User = Depends(get_current_user),  # ← Utilisateur authentifié
    db: Session = Depends(get_db)
):
    # Récupérer le produit
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    # Vérifier que l'utilisateur a le droit d'accéder
    # ADMIN: accès à tous les produits
    # USER: uniquement ses propres produits
    ensure_user_owns_resource(current_user, product, resource_type="produit")

    return product
```

### Exemple : Modification avec vérification manuelle

```python
from shared.ownership import can_modify_resource

@router.put("/products/{product_id}")
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    # Vérifier si l'utilisateur peut modifier
    if not can_modify_resource(current_user, product.user_id):
        raise HTTPException(
            status_code=403,
            detail="Vous ne pouvez pas modifier ce produit"
        )

    # Modifier le produit
    product.title = product_data.title
    db.commit()
    return product
```

---

## 3. Vérifier les limites d'abonnement

### Exemple : Créer un produit avec vérification de limite

```python
from shared.subscription_limits import check_product_limit, SubscriptionLimitError

@router.post("/products")
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Vérifier la limite de produits AVANT de créer
    try:
        current_count, max_allowed = check_product_limit(current_user, db)
    except SubscriptionLimitError as e:
        # Retourne automatiquement 403 avec détails
        raise e

    # Créer le produit
    new_product = Product(
        user_id=current_user.id,
        title=product_data.title,
        # ...
    )
    db.add(new_product)
    db.commit()

    return {
        "product": new_product,
        "limits_info": {
            "products_count": current_count + 1,
            "products_max": max_allowed
        }
    }
```

### Exemple : Connecter une plateforme avec vérification de limite

```python
from shared.subscription_limits import check_platform_limit

@router.post("/integrations/vinted")
async def connect_vinted(
    credentials: VintedCredentials,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Vérifier la limite de plateformes
    check_platform_limit(current_user, db)  # Lève exception si limite atteinte

    # Connecter Vinted
    # ...
```

### Exemple : Utiliser l'IA avec vérification de crédits

```python
from shared.subscription_limits import check_ai_credits

@router.post("/products/{product_id}/generate-description")
async def generate_description(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Vérifier les crédits IA
    check_ai_credits(current_user, db, credits_needed=1)

    # Générer la description
    # ...
```

---

## 4. Patterns courants

### Pattern 1: Endpoint USER avec ownership

```python
@router.get("/my-products")
async def list_my_products(
    current_user: User = Depends(get_current_user),  # ← USER, ADMIN, SUPPORT
    db: Session = Depends(get_db)
):
    # USER voit ses produits, ADMIN/SUPPORT peuvent voir tous les produits
    if current_user.role == UserRole.ADMIN or current_user.role == UserRole.SUPPORT:
        # Admin/Support voit tout
        products = db.query(Product).all()
    else:
        # USER voit uniquement ses produits
        products = db.query(Product).filter(Product.user_id == current_user.id).all()

    return products
```

### Pattern 2: Endpoint avec info de limites

```python
from shared.subscription_limits import get_subscription_limits_info

@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return {
        "user": current_user,
        "limits": get_subscription_limits_info(current_user),
    }
```

### Pattern 3: Action réservée ADMIN avec log

```python
@router.put("/users/{user_id}/role")
async def change_user_role(
    user_id: int,
    new_role: UserRole,
    current_user: User = Depends(require_admin),  # ← Seul ADMIN
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    old_role = user.role
    user.role = new_role
    db.commit()

    # Log l'action (optionnel)
    logger.info(f"ADMIN {current_user.id} changed user {user_id} role from {old_role} to {new_role}")

    return {"message": f"Rôle mis à jour: {old_role} → {new_role}"}
```

---

## 5. Récapitulatif des imports

```python
# Dependencies pour vérifier les rôles
from api.dependencies import (
    get_current_user,           # Utilisateur authentifié (tous rôles)
    require_admin,              # Seuls les ADMIN
    require_admin_or_support,   # ADMIN ou SUPPORT
    require_role,               # Rôles multiples personnalisés
)

# Helpers pour ownership
from shared.ownership import (
    check_resource_ownership,   # Vérification manuelle
    ensure_user_owns_resource,  # Vérification automatique
    can_modify_resource,        # Check si peut modifier
    can_view_resource,          # Check si peut consulter
)

# Helpers pour limites d'abonnement
from shared.subscription_limits import (
    check_product_limit,        # Vérifie limite produits
    check_platform_limit,       # Vérifie limite plateformes
    check_ai_credits,           # Vérifie crédits IA
    get_subscription_limits_info, # Info limites
    SubscriptionLimitError,     # Exception limite atteinte
)

# Models
from models.public.user import User, UserRole
```

---

## 6. Erreurs retournées

### 401 Unauthorized
- Token manquant, invalide ou expiré
- Utilisateur introuvable
- Compte désactivé

### 403 Forbidden
- Rôle insuffisant (ex: USER essaie d'accéder à endpoint ADMIN)
- Ownership invalide (USER essaie d'accéder aux données d'un autre USER)
- Limite d'abonnement atteinte

**Exemple de réponse 403 (limite):**
```json
{
  "detail": {
    "error": "subscription_limit_reached",
    "message": "Limite de produits atteinte (100). Passez à un abonnement supérieur pour en créer plus.",
    "limit_type": "products",
    "current": 100,
    "max_allowed": 100
  }
}
```

---

## 7. Bonnes pratiques

1. **Toujours utiliser les dependencies** au lieu de vérifier manuellement le rôle
2. **Vérifier l'ownership** pour les ressources utilisateur (produits, intégrations)
3. **Vérifier les limites** AVANT de créer une ressource
4. **Utiliser des messages d'erreur clairs** pour guider l'utilisateur
5. **Logger les actions ADMIN** pour audit (optionnel)

---

## 8. Tests recommandés

```python
# Test 1: USER ne peut pas accéder à endpoint ADMIN
response = client.get("/admin/users", headers=user_token)
assert response.status_code == 403

# Test 2: USER ne peut pas accéder aux produits d'un autre USER
response = client.get(f"/products/{other_user_product_id}", headers=user_token)
assert response.status_code == 403

# Test 3: Limite de produits respectée
for i in range(max_products + 1):
    response = client.post("/products", json=product_data, headers=user_token)
    if i < max_products:
        assert response.status_code == 201
    else:
        assert response.status_code == 403  # Limite atteinte

# Test 4: ADMIN peut changer le rôle d'un utilisateur
response = client.put(f"/users/{user_id}/role", json={"role": "support"}, headers=admin_token)
assert response.status_code == 200
```
