# 🚀 Setup Initial Plugin Stoflow (Vue 3)

**Guide rapide pour démarrer le développement du plugin**

---

## 📦 Installation

```bash
# Créer le projet
npm create vite@latest stoflow-plugin -- --template vue-ts

cd stoflow-plugin

# Installer dépendances
npm install

# Installer dépendances extension
npm install -D @types/chrome @crxjs/vite-plugin
npm install pinia # State management (optionnel)
```

---

## ⚙️ Configuration Vite

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { crx } from '@crxjs/vite-plugin';
import manifest from './manifest.json';

export default defineConfig({
  plugins: [
    vue(),
    crx({ manifest })
  ],
  build: {
    rollupOptions: {
      input: {
        popup: 'src/popup/index.html',
        options: 'src/options/index.html'
      }
    }
  }
});
```

---

## 📋 package.json

```json
{
  "name": "stoflow-plugin",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.0"
  },
  "devDependencies": {
    "@crxjs/vite-plugin": "^2.0.0",
    "@types/chrome": "^0.0.256",
    "@vitejs/plugin-vue": "^5.0.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "vue-tsc": "^1.8.0"
  }
}
```

---

## 🎨 Composables Vue 3

### usePlatforms.ts
```typescript
// src/composables/usePlatforms.ts
import { ref, onMounted } from 'vue';

export interface PlatformStatus {
  name: string;
  icon: string;
  connected: boolean;
}

export function usePlatforms() {
  const platforms = ref<PlatformStatus[]>([]);
  const loading = ref(true);

  const loadPlatforms = async () => {
    loading.value = true;

    try {
      const { cookies_vinted, cookies_ebay, cookies_etsy } =
        await chrome.storage.local.get([
          'cookies_vinted',
          'cookies_ebay',
          'cookies_etsy'
        ]);

      platforms.value = [
        {
          name: 'Vinted',
          icon: '/icons/vinted.svg',
          connected: !!cookies_vinted
        },
        {
          name: 'eBay',
          icon: '/icons/ebay.svg',
          connected: !!cookies_ebay
        },
        {
          name: 'Etsy',
          icon: '/icons/etsy.svg',
          connected: !!cookies_etsy
        }
      ];
    } finally {
      loading.value = false;
    }
  };

  const disconnectPlatform = async (platformName: string) => {
    const key = `cookies_${platformName.toLowerCase()}`;
    await chrome.storage.local.remove(key);
    await loadPlatforms();
  };

  onMounted(() => {
    loadPlatforms();
  });

  return {
    platforms,
    loading,
    loadPlatforms,
    disconnectPlatform
  };
}
```

### useAuth.ts
```typescript
// src/composables/useAuth.ts
import { ref, computed } from 'vue';

export interface LoginCredentials {
  email: string;
  password: string;
}

export function useAuth() {
  const token = ref<string | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const isAuthenticated = computed(() => !!token.value);

  const checkAuth = async () => {
    const { stoflow_token } = await chrome.storage.local.get('stoflow_token');
    token.value = stoflow_token || null;
    return !!stoflow_token;
  };

  const login = async (credentials: LoginCredentials) => {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch('https://api.stoflow.com/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
      });

      if (!response.ok) {
        throw new Error('Identifiants incorrects');
      }

      const { access_token } = await response.json();

      // Stocker le token
      await chrome.storage.local.set({ stoflow_token: access_token });
      token.value = access_token;

      return true;
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Erreur de connexion';
      return false;
    } finally {
      loading.value = false;
    }
  };

  const logout = async () => {
    await chrome.storage.local.remove('stoflow_token');
    token.value = null;
  };

  return {
    token,
    loading,
    error,
    isAuthenticated,
    checkAuth,
    login,
    logout
  };
}
```

### useSync.ts
```typescript
// src/composables/useSync.ts
import { ref } from 'vue';

export interface SyncStatus {
  type: 'idle' | 'importing' | 'syncing' | 'success' | 'error';
  message: string;
}

export function useSync() {
  const status = ref<SyncStatus>({ type: 'idle', message: '' });
  const isSyncing = ref(false);

  const importVintedProducts = async () => {
    status.value = { type: 'importing', message: 'Import en cours...' };

    try {
      await chrome.runtime.sendMessage({ action: 'IMPORT_ALL_VINTED' });

      status.value = {
        type: 'success',
        message: 'Import terminé avec succès !'
      };

      // Reset après 3s
      setTimeout(() => {
        status.value = { type: 'idle', message: '' };
      }, 3000);
    } catch (error) {
      status.value = {
        type: 'error',
        message: 'Erreur lors de l\'import'
      };
    }
  };

  const startSync = async () => {
    try {
      await chrome.runtime.sendMessage({ action: 'START_SYNC' });

      isSyncing.value = true;
      status.value = {
        type: 'syncing',
        message: 'Synchronisation activée'
      };
    } catch (error) {
      status.value = {
        type: 'error',
        message: 'Impossible de démarrer la sync'
      };
    }
  };

  const stopSync = async () => {
    try {
      await chrome.runtime.sendMessage({ action: 'STOP_SYNC' });

      isSyncing.value = false;
      status.value = { type: 'idle', message: '' };
    } catch (error) {
      console.error('Failed to stop sync:', error);
    }
  };

  return {
    status,
    isSyncing,
    importVintedProducts,
    startSync,
    stopSync
  };
}
```

---

## 🧩 Composants Vue Simplifiés

### LoginForm.vue
```vue
<script setup lang="ts">
import { ref } from 'vue';

const emit = defineEmits<{
  login: [credentials: { email: string; password: string }]
}>();

const email = ref('');
const password = ref('');

const handleSubmit = () => {
  emit('login', {
    email: email.value,
    password: password.value
  });
};
</script>

<template>
  <form @submit.prevent="handleSubmit" class="login-form">
    <h2>Connexion Stoflow</h2>

    <div class="form-group">
      <label for="email">Email</label>
      <input
        id="email"
        v-model="email"
        type="email"
        placeholder="votre@email.com"
        required
      />
    </div>

    <div class="form-group">
      <label for="password">Mot de passe</label>
      <input
        id="password"
        v-model="password"
        type="password"
        placeholder="••••••••"
        required
      />
    </div>

    <button type="submit" class="btn btn-primary">
      Se connecter
    </button>
  </form>
</template>

<style scoped>
.login-form {
  padding: 20px;
}

h2 {
  font-size: 18px;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 16px;
}

label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 6px;
  color: #374151;
}

input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
}

input:focus {
  outline: none;
  border-color: #3b82f6;
}

.btn {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
}
</style>
```

### SyncStatusBanner.vue
```vue
<script setup lang="ts">
import type { SyncStatus } from '../composables/useSync';

defineProps<{
  status: SyncStatus
}>();

const iconMap = {
  idle: '',
  importing: '📥',
  syncing: '🔄',
  success: '✅',
  error: '❌'
};
</script>

<template>
  <div class="status-banner" :class="status.type">
    <span class="icon">{{ iconMap[status.type] }}</span>
    <span class="message">{{ status.message }}</span>
  </div>
</template>

<style scoped>
.status-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  margin-top: 16px;
  border-radius: 8px;
  font-size: 14px;
}

.importing,
.syncing {
  background: #dbeafe;
  color: #1e40af;
}

.success {
  background: #dcfce7;
  color: #166534;
}

.error {
  background: #fee2e2;
  color: #991b1b;
}

.icon {
  font-size: 18px;
}
</style>
```

---

## 🎯 Popup Entry Point

```typescript
// src/popup/main.ts
import { createApp } from 'vue';
import Popup from './Popup.vue';
import './style.css';

createApp(Popup).mount('#app');
```

```html
<!-- src/popup/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Stoflow Plugin</title>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="./main.ts"></script>
</body>
</html>
```

---

## 🎨 CSS Global

```css
/* src/popup/style.css */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  width: 400px;
  min-height: 500px;
}
```

---

## 🚀 Commandes de Développement

```bash
# Mode développement (hot reload)
npm run dev

# Build production
npm run build

# Le build génère dans dist/
# Charger dist/ dans Chrome Extensions en mode développeur
```

---

## 📂 Structure Finale

```
stoflow-plugin/
├── src/
│   ├── popup/
│   │   ├── Popup.vue
│   │   ├── main.ts
│   │   ├── index.html
│   │   ├── style.css
│   │   └── components/
│   │       ├── LoginForm.vue
│   │       ├── PlatformCard.vue
│   │       ├── PlatformsList.vue
│   │       └── SyncStatusBanner.vue
│   ├── composables/
│   │   ├── usePlatforms.ts
│   │   ├── useAuth.ts
│   │   └── useSync.ts
│   └── background/
│       └── index.ts
├── manifest.json
├── vite.config.ts
├── tsconfig.json
└── package.json
```

---

## ✅ Prochaines Étapes

1. **Maintenant**: Setup projet avec ces fichiers
2. **Jour 1**: Implémenter Popup.vue complet
3. **Jour 2**: Background service worker
4. **Jour 3**: Vinted adapter + import

**Besoin d'aide pour créer le projet ?** Je peux vous guider étape par étape !
