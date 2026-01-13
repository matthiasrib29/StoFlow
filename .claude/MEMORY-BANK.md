# Memory Bank StoFlow

> Patterns critiques, décisions architecturales et gotchas connus.
> Ce fichier sert de mémoire persistante pour Claude Code.

---

## Décisions architecturales

### Pourquoi schema-per-tenant (vs row-level security)

**Choix**: Un schema PostgreSQL par utilisateur (`user_X`)

**Raisons**:
- Isolation complète des données entre tenants
- Performance des queries sans `WHERE tenant_id` systématique
- Facilité de backup/restore par tenant
- Possibilité de supprimer complètement un tenant (DROP SCHEMA)

**Trade-offs**:
- Plus de schemas à gérer (migrations plus complexes)
- Connexion pool par tenant potentiellement

### Pourquoi WebSocket pour Vinted (vs polling)

**Choix**: WebSocket entre backend et plugin browser

**Raisons**:
- Rate limiting strict de Vinted (pas de direct API)
- Besoin de réponse temps réel pour sync produits
- Plugin browser = source de vérité pour auth Vinted
- Bi-directionnel: backend peut demander actions au plugin

**Trade-offs**:
- Complexité de reconnexion
- Dépendance au navigateur ouvert

### Pourquoi Git Worktrees (vs branches classiques)

**Choix**: Un worktree par feature/hotfix

**Raisons**:
- Développement parallèle sans changer de branche
- Chaque worktree a son propre état fichiers
- Pas de `git stash` constant
- Environnements de dev isolés (ports différents)

**Trade-offs**:
- Espace disque (copie des fichiers)
- node_modules dupliqués

---

## Patterns critiques

### Multi-tenant query pattern

```python
# TOUJOURS utiliser le search_path via get_tenant_session
async with get_tenant_session(user_id) as session:
    # Queries automatiquement scopées au schema user_X
    products = await session.execute(select(Product))
```

**JAMAIS**:
```python
# NE PAS faire de queries sans search_path configuré
session.execute(select(Product))  # Risque de cross-tenant leak
```

### Job processor pattern

```python
# Jobs unifiés via UnifiedJobProcessor
# Supporte: Vinted (WebSocket), eBay (API), Etsy (API)
from services.jobs import UnifiedJobProcessor

processor = UnifiedJobProcessor(user_id)
await processor.process_import(marketplace="vinted", items=items)
```

### WebSocket reconnection pattern

```javascript
// Plugin: Auto-reconnect avec backoff exponentiel
let reconnectDelay = 1000;
const maxDelay = 30000;

function connect() {
  ws = new WebSocket(url);
  ws.onclose = () => {
    setTimeout(connect, reconnectDelay);
    reconnectDelay = Math.min(reconnectDelay * 2, maxDelay);
  };
  ws.onopen = () => {
    reconnectDelay = 1000; // Reset on success
  };
}
```

---

## Gotchas connus

### 1. Alembic multi-heads

**Symptôme**: `Multiple heads detected`

**Cause**: Migrations créées en parallèle dans différents worktrees

**Solution**:
```bash
cd backend
alembic merge -m "merge heads" heads
alembic upgrade head
```

### 2. Hot reload casse WebSocket

**Symptôme**: WebSocket déconnecté après modification backend

**Cause**: uvicorn --reload redémarre le serveur

**Solution**: Reconnexion automatique côté plugin (déjà implémenté)

### 3. npm install lent

**Symptôme**: 2-3 minutes pour `npm install`

**Cause**: Normal pour le projet (nombreuses dépendances)

**Solution**: Patience, ou utiliser `npm ci` si package-lock.json existe

### 4. search_path reset

**Symptôme**: Queries retournent données du mauvais tenant

**Cause**: Connexion réutilisée sans SET search_path

**Solution**: Toujours utiliser `get_tenant_session()` context manager

### 5. Port déjà utilisé

**Symptôme**: `Address already in use`

**Cause**: Ancien processus pas terminé proprement

**Solution**:
```bash
lsof -ti:8000 -sTCP:LISTEN | xargs -r kill -9
```

### 6. Migrations manquantes après merge

**Symptôme**: `Target database is not up to date` après /sync

**Cause**: Nouvelle migration sur develop

**Solution**:
```bash
cd backend && alembic upgrade head
```

### 7. Plugin ne détecte pas les cookies Vinted

**Symptôme**: Auth Vinted échoue

**Cause**: Cookies HTTPOnly non accessibles

**Solution**: Utiliser webRequest API pour intercepter headers

---

## Conventions de code

### Backend (Python)

```python
# Services: métier
class ProductService:
    async def create_product(self, data: ProductCreate) -> Product:
        ...

# Repositories: accès données
class ProductRepository:
    async def get_by_id(self, id: int) -> Product | None:
        ...

# Schemas: validation Pydantic
class ProductCreate(BaseModel):
    title: str
    price: Decimal
```

### Frontend (Vue 3)

```vue
<script setup lang="ts">
// Composition API obligatoire
import { ref, computed, onMounted } from 'vue'

const products = ref<Product[]>([])
const totalPrice = computed(() =>
  products.value.reduce((sum, p) => sum + p.price, 0)
)
</script>
```

### Plugin (Browser Extension)

```javascript
// Manifest V3
// Background: Service Worker
// Content: DOM manipulation
// Popup: Vue app
```

---

## Flux de données

```
User Action
    │
    ▼
Frontend (Nuxt) ──HTTP──► Backend (FastAPI)
    │                          │
    │                          ▼
    │                     PostgreSQL
    │                     (user_X schema)
    │
    └──WebSocket──► Plugin ──intercept──► Vinted/eBay/Etsy
```

---

## Historique des incidents

### 2026-01-12: Perte de 8000 lignes

**Cause**: `git reset --hard` sur develop avec commits locaux non poussés

**Fix**:
- Ajout protections dans /finish et /sync
- Règle: JAMAIS `git reset --hard` sans vérification
- Backup automatique avant opérations critiques

---

*Dernière mise à jour: 2026-01-13*
