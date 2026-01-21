<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { Logger } from '../utils/logger';

interface VintedSession {
  userId: string | null;
  login: string | null;
  isConnected: boolean;
}

const session = ref<VintedSession>({
  userId: null,
  login: null,
  isConnected: false
});

const loading = ref(true);
const error = ref('');
const showDetails = ref(false);

const vintedTabId = ref<number | null>(null);
const needsRefresh = ref(false);

const loadVintedSession = async () => {
  try {
    loading.value = true;
    error.value = '';
    needsRefresh.value = false;

    // Reset connection state
    session.value.isConnected = false;
    session.value.userId = null;
    session.value.login = null;

    // Obtenir les informations depuis un onglet Vinted
    const [tab] = await chrome.tabs.query({ url: 'https://*.vinted.fr/*' });

    if (!tab?.id) {
      error.value = 'Ouvrez un onglet Vinted pour voir les détails';
      loading.value = false;
      return;
    }

    vintedTabId.value = tab.id;

    // Envoyer un message au content script pour extraire userId + login
    try {
      Logger.debug('Popup','Requesting Vinted user info from tab', tab.id);

      const response = await chrome.tabs.sendMessage(tab.id, { action: 'GET_VINTED_USER_INFO' });

      if (response?.success) {
        session.value.userId = response.data.userId || null;
        session.value.login = response.data.login || null;

        // Connection detection: connected = userId AND login successfully extracted
        session.value.isConnected = !!(response.data.userId && response.data.login);

        if (session.value.isConnected) {
          Logger.debug('Popup','Connected to Vinted', { userId: response.data.userId, login: response.data.login });
        } else {
          Logger.debug('Popup','Not connected (userId or login missing)');
        }
      } else {
        Logger.error('Popup','Failed to extract info:', response?.error);
        error.value = 'Impossible d\'extraire les informations';
        session.value.isConnected = false;
      }
    } catch (sendError: any) {
      // Erreur de connexion = content script non chargé
      if (sendError.message?.includes('Could not establish connection') ||
          sendError.message?.includes('Receiving end does not exist')) {
        needsRefresh.value = true;
        error.value = 'Rechargez la page Vinted pour activer l\'extension';
      } else {
        throw sendError;
      }
      session.value.isConnected = false;
    }
  } catch (err: any) {
    error.value = err.message || 'Erreur lors du chargement';
    console.error('[VintedSessionInfo] Error:', err);
    session.value.isConnected = false;
  } finally {
    loading.value = false;
  }
};

const refreshVintedTab = async () => {
  if (vintedTabId.value) {
    await chrome.tabs.reload(vintedTabId.value);
    // Attendre un peu puis recharger les infos
    setTimeout(() => loadVintedSession(), 2000);
  }
};

const copyToClipboard = async (text: string, label: string) => {
  try {
    await navigator.clipboard.writeText(text);
    alert(`${label} copié !`);
  } catch (err) {
    Logger.error('Popup','Copy failed:', err);
  }
};

onMounted(() => {
  loadVintedSession();
});
</script>

<template>
  <div class="vinted-session">
    <div class="session-header" @click="showDetails = !showDetails">
      <div class="session-status">
        <div class="status-icon" :class="{ connected: session.isConnected, disconnected: !session.isConnected }">
          {{ session.isConnected ? '🟢' : '🔴' }}
        </div>
        <div>
          <h3>Vinted</h3>
          <p class="status-text">
            {{ session.isConnected ? 'Connecté' : 'Non connecté' }}
          </p>
        </div>
      </div>
      <div class="expand-icon" :class="{ expanded: showDetails }">
        {{ showDetails ? '▼' : '▶' }}
      </div>
    </div>

    <!-- Détails de la session (si connecté) -->
    <div v-if="session.isConnected && showDetails" class="session-details">
      <div v-if="loading" class="loading">
        <span class="spinner">⏳</span> Chargement...
      </div>

      <div v-else-if="error" class="error-message">
        <span>⚠️</span> {{ error }}
        <button v-if="needsRefresh" @click="refreshVintedTab" class="refresh-page-btn">
          🔄 Recharger la page
        </button>
      </div>

      <div v-else class="details-grid">
        <!-- User ID -->
        <div class="detail-row">
          <label>User ID</label>
          <div class="detail-value">
            <span class="value-text">{{ session.userId || 'N/A' }}</span>
            <button
              v-if="session.userId"
              @click="copyToClipboard(String(session.userId), 'User ID')"
              class="copy-btn"
              title="Copier"
            >
              📋
            </button>
          </div>
        </div>

        <!-- Login -->
        <div class="detail-row">
          <label>Login</label>
          <div class="detail-value">
            <span class="value-text">{{ session.login || 'N/A' }}</span>
            <button
              v-if="session.login"
              @click="copyToClipboard(session.login, 'Login')"
              class="copy-btn"
              title="Copier"
            >
              📋
            </button>
          </div>
        </div>

        <!-- Refresh Button -->
        <button @click="loadVintedSession" class="refresh-btn">
          🔄 Actualiser
        </button>
      </div>
    </div>

    <!-- Message si non connecté -->
    <div v-if="!session.isConnected && showDetails" class="help-text">
      <p>Ouvrez <a href="https://www.vinted.fr" target="_blank">vinted.fr</a> et connectez-vous</p>
    </div>
  </div>
</template>

<style scoped>
.vinted-session {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.session-header {
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.session-header:hover {
  background: #f9fafb;
}

.session-status {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-icon {
  font-size: 24px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #f3f4f6;
}

.status-icon.connected {
  background: #dcfce7;
}

.status-icon.disconnected {
  background: #fee2e2;
}

h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  color: #111827;
}

.status-text {
  font-size: 13px;
  color: #6b7280;
  margin: 2px 0 0;
}

.expand-icon {
  font-size: 14px;
  color: #9ca3af;
  transition: transform 0.2s;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

.session-details {
  padding: 0 16px 16px;
  border-top: 1px solid #f3f4f6;
  animation: slideDown 0.2s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.loading {
  text-align: center;
  padding: 20px;
  color: #6b7280;
}

.spinner {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  padding: 12px;
  background: #fee2e2;
  color: #991b1b;
  border-radius: 8px;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.refresh-page-btn {
  margin-top: 8px;
  width: 100%;
  padding: 8px 12px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.refresh-page-btn:hover {
  background: #dc2626;
}

.details-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-top: 12px;
}

.detail-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

label {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.detail-value {
  display: flex;
  align-items: center;
  gap: 6px;
}

.value-text {
  flex: 1;
  font-size: 14px;
  color: #111827;
  background: #f9fafb;
  padding: 8px 12px;
  border-radius: 6px;
  word-break: break-all;
}

.value-text.monospace {
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 12px;
}

.copy-btn, .toggle-btn {
  background: #e5e7eb;
  border: none;
  padding: 6px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
  flex-shrink: 0;
}

.copy-btn:hover, .toggle-btn:hover {
  background: #d1d5db;
}

.copy-btn:active, .toggle-btn:active {
  transform: scale(0.95);
}

.refresh-btn {
  width: 100%;
  padding: 10px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  margin-top: 8px;
}

.refresh-btn:hover {
  background: #2563eb;
}

.refresh-btn:active {
  transform: scale(0.98);
}

.help-text {
  padding: 16px;
  font-size: 13px;
  color: #6b7280;
  text-align: center;
}

.help-text a {
  color: #3b82f6;
  text-decoration: none;
}

.help-text a:hover {
  text-decoration: underline;
}
</style>
