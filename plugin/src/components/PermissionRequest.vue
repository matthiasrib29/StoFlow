<script setup lang="ts">
import { ref, onMounted } from 'vue';

const hasPermission = ref<boolean | null>(null);
const isRequesting = ref(false);
const error = ref<string | null>(null);

const LOCALHOST_PERMISSIONS = {
  origins: [
    'http://localhost:3000/*',
    'http://127.0.0.1:3000/*',
    'http://localhost:5173/*',
    'http://127.0.0.1:5173/*'
  ]
};

async function checkPermissions() {
  try {
    const result = await chrome.permissions.contains(LOCALHOST_PERMISSIONS);
    hasPermission.value = result;
  } catch (err: any) {
    console.error('Error checking permissions:', err);
    hasPermission.value = false;
  }
}

async function requestPermissions() {
  isRequesting.value = true;
  error.value = null;

  try {
    const granted = await chrome.permissions.request(LOCALHOST_PERMISSIONS);

    if (granted) {
      hasPermission.value = true;
      console.log('✅ Localhost permissions granted!');

      // Register content script for future page loads (persists across reloads)
      await registerLocalhostContentScript();

      // Also inject now on all localhost tabs
      await injectContentScriptOnLocalhostTabs();
    } else {
      hasPermission.value = false;
      error.value = 'Permissions refusées par l\'utilisateur';
    }
  } catch (err: any) {
    console.error('Error requesting permissions:', err);
    error.value = err.message || 'Erreur lors de la demande de permissions';
    hasPermission.value = false;
  } finally {
    isRequesting.value = false;
  }
}

/**
 * Register content script for localhost URLs using scripting.registerContentScripts
 * This persists across page reloads (Firefox best practice)
 */
async function registerLocalhostContentScript() {
  try {
    // First, try to unregister any existing registration to avoid conflicts
    try {
      await chrome.scripting.unregisterContentScripts({ ids: ['stoflow-localhost'] });
      console.log('🗑️ Unregistered existing localhost content script');
    } catch (e) {
      // Ignore - script may not be registered
    }

    // Register the content script for localhost URLs
    await chrome.scripting.registerContentScripts([{
      id: 'stoflow-localhost',
      matches: [
        'http://localhost:3000/*',
        'http://127.0.0.1:3000/*',
        'http://localhost:5173/*',
        'http://127.0.0.1:5173/*'
      ],
      js: ['/assets/stoflow-web.ts-h6NQ0vQk.js'],
      runAt: 'document_idle',
      persistAcrossSessions: true
    }]);

    console.log('✅ Registered localhost content script (persists across reloads)');
  } catch (err: any) {
    console.warn('⚠️ Could not register content script:', err.message);
    // Fall back to manual injection
  }
}

async function injectContentScriptOnLocalhostTabs() {
  try {
    // Get all tabs
    const tabs = await chrome.tabs.query({});

    for (const tab of tabs) {
      if (!tab.id || !tab.url) continue;

      const isLocalhost = tab.url.startsWith('http://localhost:') ||
                          tab.url.startsWith('http://127.0.0.1:');

      if (isLocalhost) {
        console.log('📥 Injecting content script on:', tab.url);

        try {
          await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ['/assets/stoflow-web.ts-h6NQ0vQk.js']
          });
          console.log('✅ Content script injected on:', tab.url);
        } catch (err: any) {
          console.warn('⚠️ Could not inject on tab:', tab.url, err.message);
        }
      }
    }
  } catch (err: any) {
    console.error('Error injecting content scripts:', err);
  }
}

onMounted(async () => {
  await checkPermissions();

  // If permissions are already granted, register and inject content scripts
  // This helps Firefox "activate" the permissions after user interaction (opening popup)
  if (hasPermission.value === true) {
    console.log('🔄 Permissions already granted, registering and injecting content scripts...');

    // Register content script for future page loads (persists across reloads)
    await registerLocalhostContentScript();

    // Also inject now on existing localhost tabs
    await injectContentScriptOnLocalhostTabs();
  }
});
</script>

<template>
  <div v-if="hasPermission === false" class="permission-card">
    <div class="permission-icon">🔒</div>
    <h3>Permissions Localhost Requises</h3>
    <p class="permission-text">
      Pour communiquer avec votre environnement de développement local,
      le plugin a besoin d'accéder à <strong>localhost</strong>.
    </p>

    <button
      @click="requestPermissions"
      :disabled="isRequesting"
      class="permission-button"
    >
      {{ isRequesting ? 'Demande en cours...' : 'Autoriser Localhost' }}
    </button>

    <p v-if="error" class="error-text">❌ {{ error }}</p>

    <p class="info-text-small">
      ℹ️ Cette permission est nécessaire uniquement en développement.
    </p>
  </div>

  <div v-else-if="hasPermission === true" class="permission-card success">
    <div class="permission-icon">✅</div>
    <p class="success-text">
      Permissions localhost accordées !
    </p>
  </div>
</template>

<style scoped>
.permission-card {
  background: white;
  border: 2px solid #fbbf24;
  border-radius: 12px;
  padding: 20px;
  margin: 16px 0;
  text-align: center;
}

.permission-card.success {
  border-color: #10b981;
  background: #f0fdf4;
}

.permission-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #1f2937;
}

.permission-text {
  font-size: 14px;
  color: #6b7280;
  margin: 0 0 16px 0;
  line-height: 1.5;
}

.permission-button {
  width: 100%;
  padding: 12px 24px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.permission-button:hover:not(:disabled) {
  background: #2563eb;
}

.permission-button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.error-text {
  margin: 12px 0 0 0;
  font-size: 13px;
  color: #dc2626;
}

.info-text-small {
  margin: 12px 0 0 0;
  font-size: 12px;
  color: #9ca3af;
}

.success-text {
  margin: 0;
  font-size: 14px;
  color: #059669;
  font-weight: 500;
}
</style>
