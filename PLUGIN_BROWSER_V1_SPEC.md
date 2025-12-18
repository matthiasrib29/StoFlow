# 🔌 STOFLOW BROWSER PLUGIN - Spécification V1

**Date**: 5 décembre 2024
**Type**: Extension Chrome & Firefox
**Langage**: TypeScript + Vue 3
**Objectif**: Interagir avec Vinted, eBay, Etsy via les cookies du navigateur sans API officielle

---

## 🎯 VISION & PROBLÉMATIQUE

### Problème à Résoudre
Les marketplaces (Vinted, eBay, Etsy) ne fournissent **pas d'API publique facile** ou ont des **limitations OAuth complexes**. Pour contourner cela, on utilise les **cookies de session de l'utilisateur** directement depuis son navigateur.

### Solution: Plugin Browser
Un plugin qui :
1. **Intercepte** les cookies de session quand l'utilisateur est connecté
2. **Exécute** les requêtes HTTP vers les marketplaces **au nom de l'utilisateur**
3. **Transmet** les données à l'API Stoflow backend
4. **Synchronise** automatiquement les ventes et stocks

---

## 📋 FONCTIONNALITÉS V1

### 1. 🔐 Authentification & Connexion

#### 1.1 Détection Automatique des Sessions
```typescript
// Détecter si l'utilisateur est connecté à Vinted
interface SessionDetector {
  platform: 'vinted' | 'ebay' | 'etsy';
  isLoggedIn(): Promise<boolean>;
  extractCookies(): Promise<Cookie[]>;
  getUserInfo(): Promise<UserInfo>;
}

// Exemple Vinted
class VintedSessionDetector implements SessionDetector {
  async isLoggedIn(): Promise<boolean> {
    // Check si cookie 'v_sid' existe et est valide
    const cookies = await chrome.cookies.getAll({ domain: '.vinted.fr' });
    return cookies.some(c => c.name === 'v_sid' && !this.isExpired(c));
  }

  async extractCookies(): Promise<Cookie[]> {
    // Récupérer tous les cookies Vinted nécessaires
    return await chrome.cookies.getAll({
      domain: '.vinted.fr'
    });
  }

  async getUserInfo(): Promise<UserInfo> {
    // Faire requête GET /api/v2/users/current avec cookies
    const response = await fetch('https://www.vinted.fr/api/v2/users/current', {
      credentials: 'include'
    });
    return await response.json();
  }
}
```

#### 1.2 Stockage Sécurisé des Cookies
```typescript
// Stocker cookies de manière sécurisée
interface CookieStorage {
  save(platform: string, cookies: Cookie[]): Promise<void>;
  load(platform: string): Promise<Cookie[]>;
  clear(platform: string): Promise<void>;
}

// Implémentation avec encryption
class EncryptedCookieStorage implements CookieStorage {
  async save(platform: string, cookies: Cookie[]): Promise<void> {
    // Encrypt cookies avant stockage
    const encrypted = await this.encrypt(JSON.stringify(cookies));

    await chrome.storage.local.set({
      [`cookies_${platform}`]: encrypted,
      [`last_sync_${platform}`]: Date.now()
    });
  }

  private async encrypt(data: string): Promise<string> {
    // Utiliser Web Crypto API pour encryption
    const encoder = new TextEncoder();
    const dataBuffer = encoder.encode(data);

    // Générer clé depuis password utilisateur
    const key = await this.getEncryptionKey();

    const encryptedBuffer = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv: this.getIV() },
      key,
      dataBuffer
    );

    return btoa(String.fromCharCode(...new Uint8Array(encryptedBuffer)));
  }
}
```

#### 1.3 Connexion à Stoflow Backend
```typescript
// Authentifier le plugin avec l'API Stoflow
interface StoflowAuth {
  login(email: string, password: string): Promise<string>; // JWT token
  validateToken(token: string): Promise<boolean>;
  refreshToken(token: string): Promise<string>;
}

class StoflowAuthClient implements StoflowAuth {
  private apiUrl = 'https://api.stoflow.com';

  async login(email: string, password: string): Promise<string> {
    const response = await fetch(`${this.apiUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const { access_token } = await response.json();

    // Stocker token
    await chrome.storage.local.set({ stoflow_token: access_token });

    return access_token;
  }
}
```

---

### 2. 📥 Import de Produits depuis Vinted

#### 2.1 Récupération Liste Produits
```typescript
interface ProductImporter {
  fetchProducts(status: 'active' | 'sold' | 'all'): Promise<Product[]>;
  importToStoflow(products: Product[]): Promise<void>;
}

class VintedProductImporter implements ProductImporter {
  async fetchProducts(status: 'active'): Promise<VintedProduct[]> {
    // Faire requête à l'API Vinted avec cookies
    const response = await fetch(
      'https://www.vinted.fr/api/v2/users/current/items?status=visible',
      {
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
          'User-Agent': navigator.userAgent
        }
      }
    );

    const data = await response.json();
    return data.items;
  }

  async importToStoflow(products: VintedProduct[]): Promise<void> {
    const stoflowToken = await this.getStoflowToken();

    // Convertir produits Vinted → format Stoflow
    const mappedProducts = products.map(p => this.mapVintedToStoflow(p));

    // Envoyer à l'API Stoflow
    for (const product of mappedProducts) {
      await fetch('https://api.stoflow.com/api/products/import', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${stoflowToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...product,
          source: 'vinted',
          source_id: product.vinted_id,
          imported_via: 'plugin'
        })
      });
    }
  }

  private mapVintedToStoflow(vinted: VintedProduct): StoflowProduct {
    return {
      title: vinted.title,
      description: vinted.description,
      price: vinted.price,
      brand: vinted.brand_title,
      category: this.mapCategory(vinted.catalog_id),
      size: vinted.size_title,
      color: vinted.color,
      condition: this.mapCondition(vinted.status_id),
      images: vinted.photos.map(p => p.full_size_url),
      vinted_id: vinted.id,
      vinted_url: vinted.url,
      metadata: {
        vinted_user_id: vinted.user_id,
        vinted_created_at: vinted.created_at_ts
      }
    };
  }

  private mapCondition(vintedStatusId: number): string {
    const mapping = {
      1: 'NEW',      // Neuf avec étiquette
      2: 'EXCELLENT', // Très bon état
      3: 'GOOD',     // Bon état
      4: 'FAIR',     // Satisfaisant
      5: 'POOR'      // Utilisé
    };
    return mapping[vintedStatusId] || 'GOOD';
  }

  private mapCategory(catalogId: number): string {
    // Mapping manuel Vinted catalog_id → catégories Stoflow
    const categoryMap: Record<number, string> = {
      1193: 'Jeans',
      1203: 'T-Shirts',
      1209: 'Shoes',
      // ... mapping complet à définir
    };
    return categoryMap[catalogId] || 'Other';
  }
}
```

#### 2.2 Téléchargement des Images
```typescript
interface ImageDownloader {
  downloadImages(urls: string[]): Promise<Blob[]>;
  uploadToStoflow(images: Blob[], productId: string): Promise<string[]>;
}

class VintedImageDownloader implements ImageDownloader {
  async downloadImages(urls: string[]): Promise<Blob[]> {
    // Télécharger images depuis Vinted
    const downloads = urls.map(async (url) => {
      const response = await fetch(url, {
        credentials: 'include' // Cookies Vinted pour accès
      });
      return await response.blob();
    });

    return await Promise.all(downloads);
  }

  async uploadToStoflow(images: Blob[], productId: string): Promise<string[]> {
    const token = await this.getStoflowToken();
    const uploadedUrls: string[] = [];

    for (let i = 0; i < images.length; i++) {
      const formData = new FormData();
      formData.append('file', images[i], `image_${i}.jpg`);
      formData.append('product_id', productId);
      formData.append('display_order', i.toString());

      const response = await fetch('https://api.stoflow.com/api/products/images', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      const { url } = await response.json();
      uploadedUrls.push(url);
    }

    return uploadedUrls;
  }
}
```

---

### 3. 🚀 Publication de Produits

#### 3.1 Publication sur Vinted
```typescript
interface ProductPublisher {
  publish(product: StoflowProduct, config: PublishConfig): Promise<PublishResult>;
  update(listingId: string, product: StoflowProduct): Promise<void>;
  delete(listingId: string): Promise<void>;
}

class VintedPublisher implements ProductPublisher {
  async publish(product: StoflowProduct, config: VintedConfig): Promise<PublishResult> {
    // 1. Upload images vers Vinted
    const imageIds = await this.uploadImagesToVinted(product.images);

    // 2. Créer le listing
    const response = await fetch('https://www.vinted.fr/api/v2/items', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': await this.getCSRFToken()
      },
      body: JSON.stringify({
        title: product.title,
        description: product.description,
        price: product.price,
        currency: 'EUR',
        catalog_id: this.getCatalogId(product.category),
        brand_id: await this.getBrandId(product.brand),
        size_id: await this.getSizeId(product.size),
        status_id: this.getStatusId(product.condition),
        color_ids: [await this.getColorId(product.color)],
        photo_ids: imageIds,
        // Champs additionnels Vinted
        is_for_sell: true,
        is_visible: 1
      })
    });

    const listing = await response.json();

    return {
      platform: 'vinted',
      listing_id: listing.item.id,
      url: listing.item.url,
      status: 'active',
      published_at: new Date().toISOString()
    };
  }

  private async uploadImagesToVinted(imageUrls: string[]): Promise<number[]> {
    const imageIds: number[] = [];

    for (const url of imageUrls) {
      // Télécharger l'image depuis Stoflow CDN
      const imageBlob = await fetch(url).then(r => r.blob());

      // 1. Demander upload URL à Vinted
      const uploadReq = await fetch('https://www.vinted.fr/api/v2/photos', {
        method: 'POST',
        credentials: 'include',
        headers: { 'X-CSRF-Token': await this.getCSRFToken() }
      });

      const { upload_url, photo_id } = await uploadReq.json();

      // 2. Upload l'image vers l'URL fournie
      const formData = new FormData();
      formData.append('file', imageBlob);

      await fetch(upload_url, {
        method: 'PUT',
        body: formData
      });

      imageIds.push(photo_id);
    }

    return imageIds;
  }

  private async getCSRFToken(): Promise<string> {
    // Récupérer CSRF token depuis cookie ou meta tag
    const cookies = await chrome.cookies.getAll({ domain: '.vinted.fr' });
    const csrfCookie = cookies.find(c => c.name === 'anon_id' || c.name === '_csrf_token');
    return csrfCookie?.value || '';
  }

  private getCatalogId(category: string): number {
    // Inverse mapping Stoflow → Vinted
    const mapping: Record<string, number> = {
      'Jeans': 1193,
      'T-Shirts': 1203,
      'Shoes': 1209,
      // ...
    };
    return mapping[category] || 0;
  }
}
```

#### 3.2 Publication Multi-Plateforme
```typescript
class MultiPlatformPublisher {
  private publishers: Map<string, ProductPublisher>;

  constructor() {
    this.publishers = new Map([
      ['vinted', new VintedPublisher()],
      ['ebay', new EbayPublisher()],
      ['etsy', new EtsyPublisher()]
    ]);
  }

  async publishToAll(
    product: StoflowProduct,
    platforms: string[]
  ): Promise<PublishResult[]> {
    const results: PublishResult[] = [];

    for (const platform of platforms) {
      const publisher = this.publishers.get(platform);
      if (!publisher) continue;

      try {
        const result = await publisher.publish(product, {});
        results.push(result);

        // Notifier Stoflow API du succès
        await this.notifyStoflow('success', platform, result);
      } catch (error) {
        // Notifier Stoflow API de l'erreur
        await this.notifyStoflow('error', platform, { error: error.message });
      }
    }

    return results;
  }

  private async notifyStoflow(
    status: 'success' | 'error',
    platform: string,
    data: any
  ): Promise<void> {
    const token = await this.getStoflowToken();

    await fetch('https://api.stoflow.com/api/publications', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        platform,
        status,
        ...data,
        source: 'plugin'
      })
    });
  }
}
```

---

### 4. 🔄 Synchronisation des Ventes

#### 4.1 Polling Automatique
```typescript
interface SalesSyncManager {
  startPolling(intervalMs: number): void;
  stopPolling(): void;
  checkForSales(): Promise<Sale[]>;
}

class VintedSalesSyncManager implements SalesSyncManager {
  private intervalId: number | null = null;

  startPolling(intervalMs: number = 60000): void {
    // Vérifier les ventes toutes les 60 secondes
    this.intervalId = setInterval(async () => {
      await this.checkForSales();
    }, intervalMs);
  }

  stopPolling(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  async checkForSales(): Promise<Sale[]> {
    // 1. Récupérer transactions récentes depuis Vinted
    const response = await fetch(
      'https://www.vinted.fr/api/v2/transactions?status=sold',
      { credentials: 'include' }
    );

    const { transactions } = await response.json();

    // 2. Filter uniquement nouvelles ventes (dernières 5 min)
    const fiveMinutesAgo = Date.now() - 5 * 60 * 1000;
    const recentSales = transactions.filter(t =>
      new Date(t.created_at).getTime() > fiveMinutesAgo
    );

    // 3. Notifier Stoflow pour chaque vente
    for (const sale of recentSales) {
      await this.notifySale(sale);
    }

    return recentSales;
  }

  private async notifySale(sale: VintedTransaction): Promise<void> {
    const token = await this.getStoflowToken();

    await fetch('https://api.stoflow.com/api/webhooks/vinted/sale', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        platform: 'vinted',
        listing_id: sale.item_id,
        sold_at: sale.created_at,
        buyer_id: sale.buyer_id,
        price: sale.total_item_price,
        source: 'plugin_polling'
      })
    });
  }
}
```

#### 4.2 Retrait Automatique des Autres Plateformes
```typescript
class CrossPlatformSyncManager {
  async handleSale(saleEvent: SaleEvent): Promise<void> {
    // 1. Trouver le produit dans Stoflow
    const product = await this.findProductByListingId(
      saleEvent.platform,
      saleEvent.listing_id
    );

    if (!product) return;

    // 2. Récupérer toutes les publications actives du produit
    const publications = await this.getActivePublications(product.id);

    // 3. Retirer de toutes les autres plateformes
    for (const pub of publications) {
      if (pub.platform === saleEvent.platform) continue; // Skip la plateforme de vente

      const publisher = this.getPublisher(pub.platform);

      try {
        await publisher.delete(pub.listing_id);

        // Notifier Stoflow du retrait
        await this.updatePublicationStatus(pub.id, 'removed');
      } catch (error) {
        console.error(`Failed to remove from ${pub.platform}:`, error);
      }
    }

    // 4. Marquer produit comme vendu dans Stoflow
    await this.markProductAsSold(product.id, saleEvent);
  }

  private async markProductAsSold(
    productId: string,
    sale: SaleEvent
  ): Promise<void> {
    const token = await this.getStoflowToken();

    await fetch(`https://api.stoflow.com/api/products/${productId}`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        is_sold: true,
        sold_at: sale.sold_at,
        sold_on_platform: sale.platform,
        stock_quantity: 0
      })
    });
  }
}
```

---

### 5. 🎨 Interface Utilisateur du Plugin

#### 5.1 Popup Principal
```vue
<!-- popup.vue - Interface Vue 3 avec Composition API -->
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import LoginForm from './components/LoginForm.vue';
import PlatformsList from './components/PlatformsList.vue';
import SyncStatusBanner from './components/SyncStatusBanner.vue';

const isConnected = ref(false);
const platforms = ref<PlatformStatus[]>([]);
const syncStatus = ref<SyncStatus | null>(null);

onMounted(async () => {
  await checkConnection();
  await loadPlatformStatuses();
});

const handleLogin = async (credentials: LoginCredentials) => {
  const token = await stoflowApi.login(credentials);
  isConnected.value = true;
  await loadPlatformStatuses();
};

const importVintedProducts = async () => {
  syncStatus.value = { type: 'importing', message: 'Import en cours...' };
  await chrome.runtime.sendMessage({ action: 'IMPORT_ALL_VINTED' });
  syncStatus.value = { type: 'success', message: 'Import terminé !' };
};

const startSync = async () => {
  await chrome.runtime.sendMessage({ action: 'START_SYNC' });
  syncStatus.value = { type: 'syncing', message: 'Synchronisation activée' };
};

const checkConnection = async () => {
  const { stoflow_token } = await chrome.storage.local.get('stoflow_token');
  isConnected.value = !!stoflow_token;
};

const loadPlatformStatuses = async () => {
  const { cookies_vinted, cookies_ebay, cookies_etsy } =
    await chrome.storage.local.get(['cookies_vinted', 'cookies_ebay', 'cookies_etsy']);

  platforms.value = [
    { name: 'Vinted', icon: '/icons/vinted.svg', connected: !!cookies_vinted },
    { name: 'eBay', icon: '/icons/ebay.svg', connected: !!cookies_ebay },
    { name: 'Etsy', icon: '/icons/etsy.svg', connected: !!cookies_etsy }
  ];
};
</script>

<template>
  <div class="popup-container">
    <header>
      <h1>Stoflow Plugin</h1>
      <div class="status-indicator" :class="{ connected: isConnected }">
        {{ isConnected ? '🟢 Connecté' : '🔴 Déconnecté' }}
      </div>
    </header>

    <main>
      <!-- Connexion Stoflow -->
      <LoginForm v-if="!isConnected" @login="handleLogin" />

      <!-- Plateformes connectées -->
      <template v-if="isConnected">
        <PlatformsList :platforms="platforms" />

        <!-- Actions rapides -->
        <div class="quick-actions">
          <button class="btn btn-primary" @click="importVintedProducts">
            📥 Importer Vinted
          </button>
          <button class="btn btn-secondary" @click="startSync">
            🔄 Sync Ventes
          </button>
        </div>

        <!-- Status sync -->
        <SyncStatusBanner v-if="syncStatus" :status="syncStatus" />
      </template>
    </main>
  </div>
</template>

<style scoped>
.popup-container {
  width: 400px;
  padding: 16px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

h1 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.status-indicator {
  font-size: 14px;
  padding: 4px 12px;
  border-radius: 12px;
  background: #fee2e2;
  color: #991b1b;
}

.status-indicator.connected {
  background: #dcfce7;
  color: #166534;
}

.quick-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

.btn {
  flex: 1;
  padding: 10px;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-secondary {
  background: #e5e7eb;
  color: #374151;
}

.btn-secondary:hover {
  background: #d1d5db;
}
</style>
```

```vue
<!-- components/PlatformsList.vue -->
<script setup lang="ts">
import { defineProps } from 'vue';
import PlatformCard from './PlatformCard.vue';

defineProps<{
  platforms: PlatformStatus[]
}>();
</script>

<template>
  <div class="platforms-list">
    <h2>Plateformes connectées</h2>
    <PlatformCard
      v-for="platform in platforms"
      :key="platform.name"
      :platform="platform"
    />
  </div>
</template>

<style scoped>
.platforms-list {
  margin-top: 20px;
}

h2 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #374151;
}
</style>
```

```vue
<!-- components/PlatformCard.vue -->
<script setup lang="ts">
import { defineProps, defineEmits } from 'vue';

const props = defineProps<{
  platform: PlatformStatus
}>();

const emit = defineEmits<{
  disconnect: [name: string]
}>();

const disconnectPlatform = () => {
  emit('disconnect', props.platform.name);
};
</script>

<template>
  <div class="platform-card" :class="{ connected: platform.connected }">
    <img :src="platform.icon" :alt="platform.name" class="platform-icon" />
    <div class="platform-info">
      <h3>{{ platform.name }}</h3>
      <span class="status">
        {{ platform.connected ? '✅ Connecté' : '❌ Non connecté' }}
      </span>
    </div>
    <button
      v-if="platform.connected"
      class="disconnect-btn"
      @click="disconnectPlatform"
    >
      Déconnecter
    </button>
  </div>
</template>

<style scoped>
.platform-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
}

.platform-card.connected {
  border-color: #86efac;
  background: #f0fdf4;
}

.platform-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
}

.platform-info {
  flex: 1;
}

.platform-info h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.status {
  font-size: 12px;
  color: #6b7280;
}

.disconnect-btn {
  padding: 6px 12px;
  font-size: 12px;
  background: #fee2e2;
  color: #991b1b;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.disconnect-btn:hover {
  background: #fecaca;
}
</style>
```

#### 5.2 Page d'Options/Settings
```vue
<!-- options.vue - Page de configuration -->
<script setup lang="ts">
import { ref, onMounted } from 'vue';

interface Settings {
  syncInterval: number;
  autoSync: boolean;
  notifications: boolean;
  platforms: {
    vinted: { enabled: boolean; autoImport: boolean };
    ebay: { enabled: boolean; autoImport: boolean };
    etsy: { enabled: boolean; autoImport: boolean };
  };
}

const settings = ref<Settings>({
  syncInterval: 60,
  autoSync: true,
  notifications: true,
  platforms: {
    vinted: { enabled: true, autoImport: false },
    ebay: { enabled: true, autoImport: false },
    etsy: { enabled: false, autoImport: false }
  }
});

const saving = ref(false);
const saveMessage = ref('');

onMounted(async () => {
  const stored = await chrome.storage.local.get('settings');
  if (stored.settings) {
    settings.value = stored.settings;
  }
});

const saveSettings = async () => {
  saving.value = true;
  saveMessage.value = '';

  try {
    await chrome.storage.local.set({ settings: settings.value });

    // Mettre à jour l'intervalle de sync
    await chrome.runtime.sendMessage({
      action: 'UPDATE_SYNC_INTERVAL',
      interval: settings.value.syncInterval
    });

    saveMessage.value = '✅ Paramètres enregistrés !';
  } catch (error) {
    saveMessage.value = '❌ Erreur lors de l\'enregistrement';
  } finally {
    saving.value = false;
    setTimeout(() => saveMessage.value = '', 3000);
  }
};
</script>

<template>
  <div class="options-page">
    <header>
      <h1>⚙️ Paramètres Stoflow Plugin</h1>
    </header>

    <main>
      <section class="settings-section">
        <h2>🔄 Synchronisation</h2>
        <div class="setting-item">
          <label class="checkbox-label">
            <input
              v-model="settings.autoSync"
              type="checkbox"
            />
            <span>Synchronisation automatique des ventes</span>
          </label>
          <p class="help-text">
            Vérifie automatiquement les nouvelles ventes sur toutes les plateformes
          </p>
        </div>

        <div class="setting-item">
          <label>
            <span class="label-text">Intervalle de synchronisation</span>
            <select v-model.number="settings.syncInterval" class="select-input">
              <option :value="30">30 secondes</option>
              <option :value="60">1 minute (recommandé)</option>
              <option :value="300">5 minutes</option>
              <option :value="900">15 minutes</option>
            </select>
          </label>
          <p class="help-text">
            Temps entre chaque vérification des ventes
          </p>
        </div>
      </section>

      <section class="settings-section">
        <h2>🔔 Notifications</h2>
        <div class="setting-item">
          <label class="checkbox-label">
            <input
              v-model="settings.notifications"
              type="checkbox"
            />
            <span>Afficher notifications lors des ventes</span>
          </label>
          <p class="help-text">
            Recevoir une notification desktop quand un produit est vendu
          </p>
        </div>
      </section>

      <section class="settings-section">
        <h2>🌐 Plateformes</h2>

        <div v-for="(config, name) in settings.platforms" :key="name" class="platform-setting">
          <div class="platform-header">
            <h3>{{ name.charAt(0).toUpperCase() + name.slice(1) }}</h3>
          </div>

          <div class="setting-item">
            <label class="checkbox-label">
              <input v-model="config.enabled" type="checkbox" />
              <span>Activer {{ name }}</span>
            </label>
          </div>

          <div class="setting-item" v-if="config.enabled">
            <label class="checkbox-label">
              <input v-model="config.autoImport" type="checkbox" />
              <span>Import automatique au démarrage</span>
            </label>
          </div>
        </div>
      </section>

      <div class="actions">
        <button
          class="btn btn-primary"
          :disabled="saving"
          @click="saveSettings"
        >
          {{ saving ? 'Enregistrement...' : 'Enregistrer les paramètres' }}
        </button>

        <div v-if="saveMessage" class="save-message" :class="{ error: saveMessage.includes('❌') }">
          {{ saveMessage }}
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.options-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 40px 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

header h1 {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 32px;
  color: #111827;
}

.settings-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.settings-section h2 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #374151;
}

.setting-item {
  margin-bottom: 20px;
}

.setting-item:last-child {
  margin-bottom: 0;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 20px;
  height: 20px;
  margin-right: 12px;
  cursor: pointer;
}

.checkbox-label span {
  font-size: 14px;
  color: #374151;
}

.label-text {
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #374151;
}

.select-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  cursor: pointer;
}

.help-text {
  margin-top: 6px;
  font-size: 12px;
  color: #6b7280;
  line-height: 1.4;
}

.platform-setting {
  padding: 16px;
  margin-bottom: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.platform-setting:last-child {
  margin-bottom: 0;
}

.platform-header h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #111827;
}

.actions {
  margin-top: 32px;
  text-align: center;
}

.btn {
  padding: 12px 32px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.save-message {
  margin-top: 16px;
  padding: 12px;
  border-radius: 8px;
  font-size: 14px;
  background: #dcfce7;
  color: #166534;
}

.save-message.error {
  background: #fee2e2;
  color: #991b1b;
}
</style>
```

#### 5.3 Content Script (Injection dans Pages)
```typescript
// content.ts - Script injecté dans pages Vinted/eBay/Etsy
class PageInjector {
  private platform: string;

  constructor() {
    this.platform = this.detectPlatform();
    if (this.platform) {
      this.inject();
    }
  }

  private detectPlatform(): string | null {
    const hostname = window.location.hostname;

    if (hostname.includes('vinted')) return 'vinted';
    if (hostname.includes('ebay')) return 'ebay';
    if (hostname.includes('etsy')) return 'etsy';

    return null;
  }

  private inject(): void {
    // Ajouter bouton "Importer vers Stoflow" sur page produit
    if (this.isProductPage()) {
      this.addImportButton();
    }

    // Ajouter bouton "Importer tous" sur liste produits
    if (this.isProductListPage()) {
      this.addBulkImportButton();
    }
  }

  private addImportButton(): void {
    const button = document.createElement('button');
    button.id = 'stoflow-import-btn';
    button.textContent = '📦 Importer vers Stoflow';
    button.className = 'stoflow-btn';
    button.onclick = () => this.handleImportClick();

    // Insérer à côté du bouton "Modifier" Vinted
    const editButton = document.querySelector('.item-edit-button');
    if (editButton) {
      editButton.parentElement?.insertBefore(button, editButton.nextSibling);
    }
  }

  private async handleImportClick(): Promise<void> {
    // Extraire données produit depuis DOM
    const product = this.extractProductData();

    // Envoyer à background script
    chrome.runtime.sendMessage({
      action: 'IMPORT_PRODUCT',
      platform: this.platform,
      product
    });

    // Feedback visuel
    this.showNotification('Produit importé vers Stoflow! ✅');
  }

  private extractProductData(): ProductData {
    // Extraire données depuis DOM (Vinted exemple)
    return {
      title: document.querySelector('.item-title')?.textContent || '',
      price: this.extractPrice(),
      description: document.querySelector('.item-description')?.textContent || '',
      images: Array.from(document.querySelectorAll('.item-photo img'))
        .map(img => (img as HTMLImageElement).src),
      // ... autres champs
    };
  }
}

// Initialiser l'injection
new PageInjector();
```

---

### 6. 🔧 Background Service Worker

#### 6.1 Gestionnaire Central
```typescript
// background.ts - Service worker (Manifest V3)
class BackgroundService {
  private syncManager: SalesSyncManager;
  private importQueue: ImportQueue;

  constructor() {
    this.syncManager = new VintedSalesSyncManager();
    this.importQueue = new ImportQueue();

    this.setupListeners();
    this.startAutoSync();
  }

  private setupListeners(): void {
    // Écouter messages depuis popup/content scripts
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      this.handleMessage(message, sender, sendResponse);
      return true; // Keep channel open for async
    });

    // Écouter installation/update
    chrome.runtime.onInstalled.addListener(() => {
      this.onInstall();
    });

    // Écouter alarmes (pour polling)
    chrome.alarms.onAlarm.addListener((alarm) => {
      this.handleAlarm(alarm);
    });
  }

  private async handleMessage(
    message: any,
    sender: chrome.runtime.MessageSender,
    sendResponse: (response: any) => void
  ): Promise<void> {
    switch (message.action) {
      case 'IMPORT_PRODUCT':
        await this.handleImportProduct(message.product);
        sendResponse({ success: true });
        break;

      case 'IMPORT_ALL_VINTED':
        await this.handleImportAllVinted();
        sendResponse({ success: true });
        break;

      case 'PUBLISH_PRODUCT':
        await this.handlePublishProduct(message.productId, message.platforms);
        sendResponse({ success: true });
        break;

      case 'START_SYNC':
        this.syncManager.startPolling(60000);
        sendResponse({ success: true });
        break;

      case 'STOP_SYNC':
        this.syncManager.stopPolling();
        sendResponse({ success: true });
        break;
    }
  }

  private startAutoSync(): void {
    // Créer alarme pour sync toutes les minutes
    chrome.alarms.create('sales-sync', {
      periodInMinutes: 1
    });
  }

  private async handleAlarm(alarm: chrome.alarms.Alarm): Promise<void> {
    if (alarm.name === 'sales-sync') {
      const settings = await this.getSettings();

      if (settings.autoSync) {
        await this.syncManager.checkForSales();
      }
    }
  }

  private async onInstall(): void {
    // Setup initial
    await chrome.storage.local.set({
      settings: {
        autoSync: true,
        syncInterval: 60,
        notifications: true
      }
    });

    // Ouvrir page onboarding
    chrome.tabs.create({
      url: chrome.runtime.getURL('onboarding.html')
    });
  }
}

// Initialiser le service
new BackgroundService();
```

---

## 📁 STRUCTURE DU PROJET

```
stoflow-plugin/
├── manifest.json                 # Configuration extension
├── package.json
├── tsconfig.json
├── vite.config.ts               # Build config
│
├── src/
│   ├── background/
│   │   ├── index.ts             # Service worker principal
│   │   ├── sync-manager.ts      # Gestionnaire sync ventes
│   │   └── import-queue.ts      # File d'import
│   │
│   ├── content/
│   │   ├── vinted.ts            # Content script Vinted
│   │   ├── ebay.ts              # Content script eBay
│   │   └── etsy.ts              # Content script Etsy
│   │
│   ├── popup/
│   │   ├── Popup.vue            # Interface popup (Vue 3)
│   │   ├── components/
│   │   │   ├── LoginForm.vue
│   │   │   ├── PlatformCard.vue
│   │   │   ├── PlatformsList.vue
│   │   │   └── SyncStatusBanner.vue
│   │   ├── main.ts              # Entry point popup
│   │   └── index.html
│   │
│   ├── options/
│   │   ├── Options.vue          # Page settings (Vue 3)
│   │   ├── main.ts              # Entry point options
│   │   └── index.html
│   │
│   ├── adapters/
│   │   ├── vinted/
│   │   │   ├── session.ts       # Détection session
│   │   │   ├── importer.ts      # Import produits
│   │   │   ├── publisher.ts     # Publication
│   │   │   └── mapper.ts        # Mapping données
│   │   ├── ebay/
│   │   └── etsy/
│   │
│   ├── api/
│   │   ├── stoflow.ts           # Client API Stoflow
│   │   └── types.ts             # Types TypeScript
│   │
│   ├── storage/
│   │   ├── cookies.ts           # Storage cookies encrypted
│   │   └── settings.ts          # Storage settings
│   │
│   ├── composables/             # Vue 3 Composables
│   │   ├── usePlatforms.ts      # Gestion état plateformes
│   │   ├── useAuth.ts           # Gestion auth Stoflow
│   │   └── useSync.ts           # Gestion sync
│   │
│   └── utils/
│       ├── crypto.ts            # Encryption utilities
│       ├── notifications.ts     # Gestion notifications
│       └── logger.ts            # Logging
│
├── public/
│   ├── icons/
│   │   ├── icon16.png
│   │   ├── icon48.png
│   │   └── icon128.png
│   └── onboarding.html
│
└── dist/                        # Build output (généré)
```

---

## 🔐 SÉCURITÉ

### 1. Encryption des Cookies
```typescript
// Utiliser Web Crypto API pour encryptions AES-256-GCM
class CryptoService {
  private static async getKey(password: string): Promise<CryptoKey> {
    const encoder = new TextEncoder();
    const keyMaterial = await crypto.subtle.importKey(
      'raw',
      encoder.encode(password),
      'PBKDF2',
      false,
      ['deriveKey']
    );

    return await crypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt: encoder.encode('stoflow-salt'),
        iterations: 100000,
        hash: 'SHA-256'
      },
      keyMaterial,
      { name: 'AES-GCM', length: 256 },
      false,
      ['encrypt', 'decrypt']
    );
  }
}
```

### 2. Validation HTTPS Uniquement
```json
// manifest.json
{
  "host_permissions": [
    "https://www.vinted.fr/*",
    "https://www.ebay.fr/*",
    "https://www.etsy.com/*",
    "https://api.stoflow.com/*"
  ]
}
```

### 3. Content Security Policy
```json
{
  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'"
  }
}
```

---

## 🚀 DÉPLOIEMENT

### Build Production
```bash
# Build pour Chrome & Firefox
npm run build

# Outputs:
# dist/chrome/  → ZIP pour Chrome Web Store
# dist/firefox/ → XPI pour Firefox Add-ons
```

### Publication Chrome Web Store
1. Créer compte développeur ($5 one-time)
2. Upload ZIP depuis `dist/chrome/`
3. Remplir métadonnées + screenshots
4. Review (2-3 jours)

### Publication Firefox Add-ons
1. Créer compte Mozilla
2. Upload XPI depuis `dist/firefox/`
3. Review automatisé (quelques heures)

---

## 📊 MONITORING & ANALYTICS

### Tracking Events
```typescript
// Envoyer événements anonymes à Stoflow API
class Analytics {
  async track(event: string, properties?: any): Promise<void> {
    await fetch('https://api.stoflow.com/api/analytics', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event,
        properties,
        timestamp: Date.now(),
        plugin_version: chrome.runtime.getManifest().version
      })
    });
  }
}

// Events à tracker:
// - plugin_installed
// - platform_connected (vinted, ebay, etsy)
// - products_imported (count)
// - product_published (platform)
// - sale_detected (platform)
```

---

## ✅ CHECKLIST DÉVELOPPEMENT

### Phase 1: Setup (Jour 1)
- [ ] Init projet TypeScript + Vue 3
- [ ] Config Vite pour build extension
- [ ] Créer manifest.json
- [ ] Structure de base des dossiers
- [ ] Icons et assets
- [ ] Setup Composition API + Composables

### Phase 2: Authentification (Jour 2-3)
- [ ] Détection session Vinted
- [ ] Extraction cookies
- [ ] Storage encrypted
- [ ] Connexion API Stoflow
- [ ] UI Login popup

### Phase 3: Import Vinted (Jour 4-6)
- [ ] Fetch liste produits Vinted
- [ ] Mapping Vinted → Stoflow
- [ ] Download + upload images
- [ ] Gestion duplicatas
- [ ] UI import progress

### Phase 4: Publication (Jour 7-10)
- [ ] VintedPublisher implémentation
- [ ] Upload images vers Vinted
- [ ] Mapping catégories/tailles
- [ ] Gestion CSRF token
- [ ] Tests publication réelle

### Phase 5: Sync Ventes (Jour 11-12)
- [ ] Polling transactions Vinted
- [ ] Détection nouvelles ventes
- [ ] Notification Stoflow API
- [ ] Retrait cross-platform
- [ ] Notifications browser

### Phase 6: UI/UX (Jour 13-14)
- [ ] Polish popup interface
- [ ] Page options/settings
- [ ] Content script injection
- [ ] Animations et feedback
- [ ] Error handling UI

### Phase 7: Tests & Deploy (Jour 15)
- [ ] Tests E2E Vinted
- [ ] Tests isolation Chrome/Firefox
- [ ] Build production
- [ ] Submit Chrome Web Store
- [ ] Submit Firefox Add-ons

---

## 📝 MANIFEST.JSON Complet

```json
{
  "manifest_version": 3,
  "name": "Stoflow - Multi-Marketplace Manager",
  "version": "1.0.0",
  "description": "Import, publish and sync your products across Vinted, eBay and Etsy",

  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },

  "permissions": [
    "storage",
    "cookies",
    "alarms",
    "notifications"
  ],

  "host_permissions": [
    "https://www.vinted.fr/*",
    "https://www.vinted.com/*",
    "https://www.ebay.fr/*",
    "https://www.etsy.com/*",
    "https://api.stoflow.com/*"
  ],

  "background": {
    "service_worker": "background.js",
    "type": "module"
  },

  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png"
    }
  },

  "options_page": "options.html",

  "content_scripts": [
    {
      "matches": ["https://www.vinted.fr/*"],
      "js": ["content-vinted.js"],
      "run_at": "document_idle"
    },
    {
      "matches": ["https://www.ebay.fr/*"],
      "js": ["content-ebay.js"],
      "run_at": "document_idle"
    },
    {
      "matches": ["https://www.etsy.com/*"],
      "js": ["content-etsy.js"],
      "run_at": "document_idle"
    }
  ],

  "web_accessible_resources": [
    {
      "resources": ["icons/*"],
      "matches": ["<all_urls>"]
    }
  ]
}
```

---

## 🎯 PROCHAINES ÉTAPES

1. **Immédiat**:
   - Valider cette spec
   - Setup projet TypeScript + React
   - Analyser API Vinted (DevTools)

2. **Semaine 1**:
   - Implémenter détection session Vinted
   - Créer VintedImporter basique
   - UI popup MVP

3. **Semaine 2**:
   - Publication Vinted complète
   - Tests avec vrais produits
   - Sync ventes basique

---

**Questions ouvertes**:
1. Préférence hébergement API Stoflow ?
2. Besoin d'aide reverse engineering API Vinted ?
3. eBay/Etsy pour V1 ou V1.1 ?

**Status**: 📝 **Spec complète - Prêt pour développement**
