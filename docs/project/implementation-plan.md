# Plan d'Implémentation - 3 Problèmes Critiques Restants

## Status Actuel

✅ #1: Secrets - SKIPPÉ (pas de config sensible)
✅ #2: XSS - COMPLET (DOMPurify + 16 tests)
✅ #6: Timing - COMPLET (decorator + imports)
✅ #5: Migrations - COMPLET (bare except fixé + logging)

⏳ #3: JWT HS256 → RS256 - PRÊT
⏳ #4: JWT 15min + Refresh - PRÊT
⏳ #7: Dual-Write Cleanup - PRÊT

---

## #3: JWT HS256 → RS256 (7h)

### Fichiers à Modifier
```
backend/services/auth_service.py     # JWT logic
backend/shared/config.py              # JWT settings
backend/.env                          # Config keys
```

### Implémentation

#### Step 1: Générer RSA Keypair (30min)
```bash
openssl genrsa -out backend/keys/private_key.pem 2048
openssl rsa -in backend/keys/private_key.pem -pubout -out backend/keys/public_key.pem
```

#### Step 2: Charger Clés dans config.py (1h)
```python
# backend/shared/config.py

def load_rsa_keys():
    """Charger les clés RSA depuis l'environnement."""
    with open(os.getenv('JWT_PRIVATE_KEY_PATH', 'keys/private_key.pem')) as f:
        private_key_pem = f.read()
    with open(os.getenv('JWT_PUBLIC_KEY_PATH', 'keys/public_key.pem')) as f:
        public_key_pem = f.read()

    return private_key_pem, public_key_pem

class Settings(BaseSettings):
    jwt_algorithm: str = "RS256"  # Changed from HS256
    jwt_private_key_pem: str  # New
    jwt_public_key_pem: str   # New
```

#### Step 3: Modifier auth_service.py (3h)
- Remplacer `jwt.encode(payload, secret, algorithm="HS256")` par RS256
- Remplacer `jwt.decode(token, secret, algorithms=["HS256"])` par RS256
- Ajouter fallback HS256 pour tokens anciens (30 jours)
- Logger les fallbacks

**Code à changer (ligne ~92):**
```python
def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    # ANCIEN
    return jwt.encode(data, settings.jwt_secret_key, algorithm="HS256")

    # NOUVEAU
    return jwt.encode(data, settings.jwt_private_key_pem, algorithm="RS256")

def verify_token(token: str) -> Optional[dict]:
    # NOUVEAU: Try RS256 first
    try:
        return jwt.decode(token, settings.jwt_public_key_pem, algorithms=["RS256"])
    except JWTError:
        # Fallback HS256 (30 jours seulement)
        logger.warning("Token HS256 ancien - backward compat")
        return jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
```

#### Step 4: Tests (1.5h)
```python
def test_create_token_rs256():
    # Vérifier que le token est créé en RS256
    token = AuthService.create_access_token({"user_id": 1})
    header = jwt.decode(token, options={"verify_signature": False})
    assert header['alg'] == 'RS256'

def test_old_hs256_tokens_still_work():
    # Vérifier backward compatibility
    old_token = jwt.encode({"user_id": 1}, settings.jwt_secret_key, algorithm="HS256")
    payload = AuthService.verify_token(old_token)
    assert payload['user_id'] == 1
```

#### Step 5: Migration Users (1h)
- Tous les users connectés = logout (tokens HS256 ne matchent plus)
- Communication: "Nouvelle session sécurisée requise"

### Dépendances
- Dépend de: Rien (indépendant)
- Bloque: #4 (JWT refresh)

---

## #4: JWT 15min + Refresh Token (7.5h)

### Configuration
```
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15    # De 1440
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7       # Nouveau
```

### Implémentation

#### Step 1: Configuration (30min)
**backend/.env:**
```env
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_TOKEN_TYPE=access  # or "refresh"
```

#### Step 2: Table Revocation (1h)
```python
# backend/models/public/revoked_token.py

class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    __table_args__ = (
        Index('idx_revoked_tokens_token_hash', 'token_hash'),
        Index('idx_revoked_tokens_expires_at', 'expires_at'),
    )

    token_hash: Mapped[str] = mapped_column(primary_key=True)  # SHA256 du token
    revoked_at: Mapped[datetime] = mapped_column(default=utc_now)
    expires_at: Mapped[datetime]  # Pour cleanup
```

**Alembic migration:**
```bash
alembic revision --autogenerate -m "Add revoked_tokens table"
```

#### Step 3: Dual Token Strategy en auth_service.py (2h)

```python
def create_tokens(user: User) -> dict:
    """Créer access + refresh tokens."""
    # Access token (15 min)
    access_token = jwt.encode({
        "user_id": user.id,
        "role": user.role,
        "type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=15),
        "iat": datetime.utcnow()
    }, settings.jwt_private_key_pem, algorithm="RS256")

    # Refresh token (7 jours)
    refresh_token = jwt.encode({
        "user_id": user.id,
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=7),
        "iat": datetime.utcnow()
    }, settings.jwt_private_key_pem, algorithm="RS256")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 900  # 15 * 60 seconds
    }

def refresh_access_token(db: Session, refresh_token: str) -> Optional[dict]:
    """Échanger un refresh token pour un nouveau access token."""
    try:
        payload = jwt.decode(
            refresh_token,
            settings.jwt_public_key_pem,
            algorithms=["RS256"]
        )

        if payload.get("type") != "refresh":
            return None

        # Vérifier que le token n'est pas révoqué
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        if is_token_revoked(db, token_hash):
            return None

        # Créer nouveau access token
        new_access_token = jwt.encode({
            "user_id": payload["user_id"],
            "type": "access",
            "exp": datetime.utcnow() + timedelta(minutes=15),
            "iat": datetime.utcnow()
        }, settings.jwt_private_key_pem, algorithm="RS256")

        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
    except JWTError:
        return None

def revoke_token(db: Session, token: str):
    """Révoquer un token (logout)."""
    payload = jwt.decode(token, settings.jwt_public_key_pem, algorithms=["RS256"])
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    db.add(RevokedToken(
        token_hash=token_hash,
        expires_at=datetime.utcfromtimestamp(payload['exp'])
    ))
    db.commit()
```

#### Step 4: API Endpoints (2h)

**POST /api/auth/login** - Modifier:
```python
@router.post("/login")
def login(credentials: LoginSchema) -> TokenResponse:
    # ... auth check ...
    tokens = AuthService.create_tokens(user)
    return tokens  # Retourner access + refresh
```

**POST /api/auth/refresh** - Créer:
```python
@router.post("/refresh")
def refresh(request: RefreshTokenRequest) -> AccessTokenResponse:
    # ... dans endpoint ...
    new_token = AuthService.refresh_access_token(db, request.refresh_token)
    if not new_token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return new_token
```

**POST /api/auth/logout** - Créer:
```python
@router.post("/logout", dependencies=[Depends(get_current_user)])
def logout(current_user: User = Depends(get_current_user), request: Request):
    # Récupérer le token depuis le header
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")

    AuthService.revoke_token(db, token)
    return {"message": "Logged out"}
```

#### Step 5: Frontend - Refresh Logic (2h)

**composables/useTokenRefresh.ts:**
```typescript
export const useTokenRefresh = () => {
  const authStore = useAuthStore()

  // Refresh toutes les 10 minutes (avant expiration 15 min)
  const startAutoRefresh = () => {
    setInterval(async () => {
      const { data } = await $fetch('/api/auth/refresh', {
        method: 'POST',
        body: { refresh_token: authStore.refreshToken }
      })
      authStore.accessToken = data.access_token
    }, 10 * 60 * 1000)
  }

  return { startAutoRefresh }
}
```

**stores/auth.ts:**
```typescript
export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref('')
  const refreshToken = ref('')

  const login = async (email: string, password: string) => {
    const { access_token, refresh_token } = await $fetch('/api/auth/login', {
      method: 'POST',
      body: { email, password }
    })

    accessToken.value = access_token
    refreshToken.value = refresh_token

    // Démarrer le refresh auto
    const { startAutoRefresh } = useTokenRefresh()
    startAutoRefresh()
  }

  return { accessToken, refreshToken, login }
})
```

#### Step 6: Tests (1.5h)
```python
def test_access_token_expires_15min():
    tokens = AuthService.create_tokens(test_user)
    payload = jwt.decode(tokens['access_token'], settings.jwt_public_key_pem, algorithms=["RS256"])
    assert (payload['exp'] - payload['iat']) == 900  # 15 * 60

def test_refresh_token_valid_7days():
    tokens = AuthService.create_tokens(test_user)
    payload = jwt.decode(tokens['refresh_token'], settings.jwt_public_key_pem, algorithms=["RS256"])
    assert (payload['exp'] - payload['iat']) == 604800  # 7 * 24 * 60 * 60

def test_revoked_token_rejected(db):
    tokens = AuthService.create_tokens(test_user)
    AuthService.revoke_token(db, tokens['access_token'])

    # Vérifier que le token est rejeté
    with pytest.raises(HTTPException):
        get_current_user(tokens['access_token'], db)
```

### Dépendances
- Dépend de: #3 (JWT RS256)
- Bloque: Rien

---

## #7: Dual-Write Cleanup (8-10h)

### Fichiers à Modifier
```
backend/services/product_service.py         # Écriture M2M only
backend/services/vinted/products.py         # Lire M2M
backend/models/user/product.py              # Valider data
backend/migrations/versions/...             # Drop colonnes
```

### Implémentation

#### Step 1: Arrêter les Écritures (1-2h)

**product_service.py - create_product (L150):**
```python
# AVANT (dual-write)
material=validated_materials[0] if validated_materials else None,

# APRÈS (M2M only)
# material=...,  # DROPPED - use product_materials M2M
```

**vinted/products.py - sync (L156, L212):**
```python
# AVANT
"color1": vp.color1,

# APRÈS
"colors": [pc.color for pc in vp.product_colors],  # Utiliser M2M
```

#### Step 2: Arrêter les Lectures (1-2h)

Audit avec grep:
```bash
grep -rn "\.color\b" backend/ --include="*.py" | grep -v "product_colors\|color1"
grep -rn "\.material\b" backend/ --include="*.py" | grep -v "product_materials"
```

Remplacer par M2M:
```python
# AVANT
if product.color:
    ...

# APRÈS
if product.color_list:  # M2M property
    ...
```

#### Step 3: Valider Data (2h)

**Créer backend/scripts/validate_dual_write.py:**
```python
def validate_products_consistency(db: Session):
    """Vérifier que color/material = product_colors/materials M2M"""

    # 1. Products avec material column ≠ NULL mais product_materials vide
    inconsistent = db.query(Product).filter(
        Product.material != None,
        ~Product.product_materials.any()
    ).all()

    if inconsistent:
        print(f"ERROR: {len(inconsistent)} produits avec material orphelins")
        return False

    print("✅ Toutes les données sont cohérentes (dual-write validé)")
    return True
```

Exécuter:
```bash
cd backend && python scripts/validate_dual_write.py
```

#### Step 4: Drop Colonnes (1.5-2h)

**Alembic migration:**
```bash
alembic revision -m "drop_deprecated_product_columns"
```

**backend/migrations/versions/20260120_xxxx_drop_deprecated_product_columns.py:**
```python
def upgrade():
    connection = op.get_bind()

    # Drop de template_tenant
    op.drop_column('products', 'material', schema='template_tenant')
    op.drop_column('products', 'color1', schema='template_tenant')  # if exists

    # Drop de tous les user_X schemas
    for schema in connection.execute(text(
        "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'user_%'"
    )):
        schema_name = schema[0]
        try:
            op.drop_column('products', 'material', schema=schema_name)
            op.drop_column('products', 'color1', schema=schema_name)
        except Exception as e:
            print(f"Colonne déjà dropped dans {schema_name}")

def downgrade():
    # Recréer les colonnes si rollback
    op.add_column('products', sa.Column('material', sa.String(255)), schema='template_tenant')
    op.add_column('products', sa.Column('color1', sa.String(255)), schema='template_tenant')
```

Tester:
```bash
alembic upgrade head    # ✅
alembic downgrade -1    # ✅
```

#### Step 5: Cleanup Code (1h)

Retirer les méthodes legacy si plus utilisées:
- `primary_color()` → tester si utilisé
- `color_list()` → tester si utilisé
- Retirer comments "# Removed: color, material"

#### Step 6: Documentation (1h)

**Changelog:**
```markdown
## Deprecated: Dual-Write Columns

The following columns have been removed (migration to M2M complete):
- `products.color` → use `product_colors` M2M table
- `products.material` → use `product_materials` M2M table

Data has been validated for consistency before removal.
```

### Tests
```python
def test_product_colors_through_m2m_only():
    product = ProductService.create_product(...)

    # Vérifier M2M créée
    assert len(product.product_colors) == 2

    # Vérifier pas d'accès à la colonne dropped
    # (après suppression, ce test compilerait pas)

def test_vinted_sync_uses_m2m():
    vinted_data = VintedMapper.to_vinted_product(product)
    assert vinted_data.colors == ["red", "blue"]
```

### Dépendances
- Dépend de: #5 (Migrations)
- Bloque: Rien

---

## Timeline Recommandée

```
Jour 1-2:  #3 JWT RS256 (7h)
Jour 3-4:  #4 JWT Refresh (7.5h) + #7 Dual-Write (8h) en parallèle
Jour 5:    Tests + Validation (5h)
```

Équipe de 2:
- Personne A: #3 + #4 JWT
- Personne B: #7 Dual-Write

---

## Checklist Finale

**Avant Commit:**
- [ ] #3: JWT tokens en RS256 (vérifier alg='RS256' en header)
- [ ] #4: Access token expire 15min, Refresh 7j
- [ ] #7: Validation data complète, colonnes deprecated dropped

**Avant Merge:**
- [ ] Tous les tests passent
- [ ] Migration undo/redo OK
- [ ] Pas de regression en fonction

**Avant Deploy:**
- [ ] Clés RSA securisées (pas en git)
- [ ] Documentation secrets management
- [ ] Plan rollback préparé
