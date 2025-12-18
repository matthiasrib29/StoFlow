# Endpoints à protéger - Liste complète

## ✅ Déjà fait

### api/products.py
- ✅ `POST /products/` - Ajout vérification limite + current_user

---

## ⚠️ À modifier

### api/products.py

#### Endpoints manquant `current_user` :

1. **`GET /products/` (ligne 81)**
   - Ajouter : `current_user: User = Depends(get_current_user)`
   - Raison : USER ne doit voir que SES produits, ADMIN/SUPPORT peuvent voir tous

2. **`GET /products/{product_id}` (ligne 119)**
   - Ajouter : `current_user: User = Depends(get_current_user)`
   - Ajouter après récup produit : `ensure_user_owns_resource(current_user, product, "produit")`
   - Raison : Vérifier ownership

3. **`PUT /products/{product_id}` (ligne 146)**
   - Ajouter : `current_user: User = Depends(get_current_user)`
   - Ajouter après récup produit : `ensure_user_owns_resource(current_user, product, "produit")`
   - Raison : Vérifier ownership avant modification

4. **`DELETE /products/{product_id}` (ligne 180)**
   - Ajouter : `current_user: User = Depends(get_current_user)`
   - Récupérer produit d'abord, puis : `ensure_user_owns_resource(current_user, product, "produit")`
   - Raison : Vérifier ownership avant suppression

5. **`PATCH /products/{product_id}/status` (ligne 207)**
   - Ajouter : `current_user: User = Depends(get_current_user)`
   - Récupérer produit d'abord, puis : `ensure_user_owns_resource(current_user, product, "produit")`
   - Raison : Vérifier ownership avant changement status

6. **`GET /products/sku/{sku}` (ligne 246)**
   - Ajouter : `current_user: User = Depends(get_current_user)`
   - Ajouter après récup produit : `ensure_user_owns_resource(current_user, product, "produit")`
   - Raison : Vérifier ownership

7. **`POST /products/{product_id}/images` (ligne 275)**
   - Ajouter : `current_user: User = Depends(get_current_user)`
   - Ajouter après récup produit (ligne 307) : `ensure_user_owns_resource(current_user, product, "produit")`
   - Raison : Vérifier ownership avant upload image

8. **`DELETE /products/{product_id}/images/{image_id}` (ligne 336)**
   - Ajouter : `current_user: User = Depends(get_current_user)`
   - Après récup image, récupérer product et : `ensure_user_owns_resource(current_user, product, "produit")`
   - Raison : Vérifier ownership avant suppression image

9. **`PUT /products/{product_id}/images/reorder` (ligne 382)**
   - Ajouter : `current_user: User = Depends(get_current_user)`
   - Ajouter après récup produit (ligne 413) : `ensure_user_owns_resource(current_user, product, "produit")`
   - Raison : Vérifier ownership avant réordonnancement

---

### api/integrations.py

**Tous les endpoints doivent avoir:**
- `current_user: User = Depends(get_current_user)`
- Vérification limite : `check_platform_limit(current_user, db)` avant connexion
- Vérification ownership des intégrations existantes

---

### api/plugin.py

**Tous les endpoints doivent avoir:**
- `current_user: User = Depends(get_current_user)`
- Vérification ownership des tâches

---

## 📋 Pattern à suivre

### Pour GET (consultation)
```python
@router.get("/{resource_id}")
def get_resource(
    resource_id: int,
    current_user: User = Depends(get_current_user),  # ← Ajouter
    db: Session = Depends(get_db),
):
    resource = Service.get_by_id(db, resource_id)

    if not resource:
        raise HTTPException(404, detail="Resource not found")

    # Vérifier ownership (ADMIN/SUPPORT peuvent voir, USER seulement les siens)
    ensure_user_owns_resource(current_user, resource, "resource_type")  # ← Ajouter

    return resource
```

### Pour PUT/PATCH/DELETE (modification/suppression)
```python
@router.put("/{resource_id}")
def update_resource(
    resource_id: int,
    data: UpdateSchema,
    current_user: User = Depends(get_current_user),  # ← Ajouter
    db: Session = Depends(get_db),
):
    resource = Service.get_by_id(db, resource_id)

    if not resource:
        raise HTTPException(404, detail="Resource not found")

    # Vérifier ownership (seul propriétaire ou ADMIN peuvent modifier)
    ensure_user_owns_resource(current_user, resource, "resource_type")  # ← Ajouter

    # Modifier
    updated = Service.update(db, resource_id, data)
    return updated
```

### Pour POST création avec limite
```python
@router.post("/")
def create_resource(
    data: CreateSchema,
    current_user: User = Depends(get_current_user),  # ← Ajouter
    db: Session = Depends(get_db),
):
    # Vérifier limite AVANT création (sauf ADMIN)
    if current_user.role != UserRole.ADMIN:
        check_resource_limit(current_user, db)  # ← Ajouter

    # Créer
    resource = Service.create(db, data, current_user.id)
    return resource
```

### Pour GET list (lister ressources)
```python
@router.get("/")
def list_resources(
    current_user: User = Depends(get_current_user),  # ← Ajouter
    db: Session = Depends(get_db),
):
    # ADMIN/SUPPORT voient tout, USER voit seulement les siennes
    if current_user.role in [UserRole.ADMIN, UserRole.SUPPORT]:
        resources = Service.get_all(db)
    else:
        resources = Service.get_by_user(db, current_user.id)

    return resources
```

---

## 🔧 Imports nécessaires

Ajouter en haut de chaque fichier :

```python
from api.dependencies import get_current_user
from models.public.user import User, UserRole
from shared.ownership import ensure_user_owns_resource
from shared.subscription_limits import check_product_limit, check_platform_limit
```

---

## 🎯 Priorités

1. **URGENT** : api/products.py (tous les endpoints)
2. **IMPORTANT** : api/integrations.py
3. **IMPORTANT** : api/plugin.py

---

## ✅ Checklist par endpoint

Pour chaque endpoint, vérifier :
- [ ] A `current_user: User = Depends(get_current_user)` dans params
- [ ] Vérifie ownership avec `ensure_user_owns_resource()` (GET/PUT/PATCH/DELETE d'une ressource spécifique)
- [ ] Vérifie limite avec `check_*_limit()` (POST création)
- [ ] Filtre par user_id pour GET list (USER ne voit que ses données)
- [ ] Documentation à jour avec permissions

---

Veux-tu que je modifie automatiquement tous ces endpoints ou préfères-tu que je te montre comment faire pour quelques exemples ?
