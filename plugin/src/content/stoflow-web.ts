/**
 * Content Script pour le site web Stoflow (localhost:3000)
 *
 * Ce script s'injecte sur le site web Stoflow et récupère le token JWT
 * depuis localStorage pour l'envoyer au plugin (SSO automatique).
 *
 * Flow:
 * 1. User se connecte sur localhost:3000
 * 2. Frontend Nuxt stocke le token dans localStorage
 * 3. Ce script lit le token et l'envoie au background
 * 4. Background stocke dans chrome.storage
 * 5. Plugin est maintenant authentifié automatiquement
 */

// TEST SIMPLE : Log immédiat sans imports
console.log('');
console.log('📡📡📡📡📡📡📡📡📡📡📡📡📡📡📡📡📡📡📡📡📡');
console.log('📡 [CONTENT SCRIPT] CHARGÉ SUR:', window.location.href);
console.log('📡📡📡📡📡📡📡📡📡📡📡📡📡📡📡📡📡📡📡📡📡');
console.log('');
alert('🚀 Extension Stoflow détectée sur ' + window.location.href);

import { CONSTANTS } from '../config/environment';

console.log('[Stoflow Web SSO] 🔗 Content script chargé sur', window.location.href);

/**
 * Récupère le token depuis localStorage du site web
 */
function getTokenFromLocalStorage() {
  try {
    // Le frontend Nuxt stocke probablement le token sous une de ces clés
    const possibleKeys = [
      'stoflow_access_token',
      'stoflow_token',
      'access_token',
      'auth_token',
      'token'
    ];

    for (const key of possibleKeys) {
      const token = localStorage.getItem(key);
      if (token) {
        console.log(`[Stoflow Web SSO] ✅ Token trouvé dans localStorage.${key}`);
        return token;
      }
    }

    // Essayer de récupérer depuis un objet auth complet
    const authData = localStorage.getItem('auth');
    if (authData) {
      try {
        const parsed = JSON.parse(authData);
        if (parsed.access_token || parsed.token) {
          console.log('[Stoflow Web SSO] ✅ Token trouvé dans localStorage.auth');
          return parsed.access_token || parsed.token;
        }
      } catch (e) {
        // Ignore parsing errors
      }
    }

    console.log('[Stoflow Web SSO] ⚠️ Aucun token trouvé dans localStorage');
    return null;
  } catch (error) {
    console.error('[Stoflow Web SSO] ❌ Erreur lecture localStorage:', error);
    return null;
  }
}

/**
 * Récupère le refresh token depuis localStorage
 */
function getRefreshTokenFromLocalStorage() {
  try {
    const possibleKeys = [
      'stoflow_refresh_token',
      'refresh_token'
    ];

    for (const key of possibleKeys) {
      const token = localStorage.getItem(key);
      if (token) {
        return token;
      }
    }

    // Essayer depuis objet auth
    const authData = localStorage.getItem('auth');
    if (authData) {
      try {
        const parsed = JSON.parse(authData);
        if (parsed.refresh_token) {
          return parsed.refresh_token;
        }
      } catch (e) {
        // Ignore
      }
    }

    return null;
  } catch (error) {
    console.error('[Stoflow Web SSO] ❌ Erreur lecture refresh token:', error);
    return null;
  }
}

/**
 * Envoie le token au background script pour stockage
 */
async function syncTokenToPlugin() {
  const accessToken = getTokenFromLocalStorage();
  const refreshToken = getRefreshTokenFromLocalStorage();

  if (!accessToken) {
    console.log('[Stoflow Web SSO] ℹ️ Aucun token à synchroniser');
    return;
  }

  try {
    // Envoyer au background script
    const response = await chrome.runtime.sendMessage({
      action: 'SYNC_TOKEN_FROM_WEBSITE',
      access_token: accessToken,
      refresh_token: refreshToken
    });

    if (response?.success) {
      console.log('[Stoflow Web SSO] ✅ Token synchronisé avec le plugin');

      // Optionnel: afficher une notification discrète
      showSyncNotification();
    } else {
      console.error('[Stoflow Web SSO] ❌ Échec de synchronisation:', response?.error);
    }
  } catch (error) {
    console.error('[Stoflow Web SSO] ❌ Erreur envoi au plugin:', error);
  }
}

/**
 * Affiche une notification discrète de synchronisation
 */
function showSyncNotification() {
  // Créer une notification toast discrète
  const toast = document.createElement('div');
  toast.id = 'stoflow-sso-toast';
  toast.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: #10b981;
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    font-family: system-ui, -apple-system, sans-serif;
    font-size: 14px;
    z-index: 999999;
    display: flex;
    align-items: center;
    gap: 8px;
    animation: slideIn 0.3s ease-out;
  `;
  toast.innerHTML = `
    <span>✓</span>
    <span>Plugin Stoflow connecté</span>
  `;

  // Ajouter l'animation
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from { transform: translateX(400px); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
  `;
  document.head.appendChild(style);

  document.body.appendChild(toast);

  // Retirer après 3 secondes
  setTimeout(() => {
    toast.style.transition = 'opacity 0.3s';
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

/**
 * Écoute les changements de localStorage (login/logout)
 */
function watchLocalStorageChanges() {
  // Observer les changements via storage event
  window.addEventListener('storage', (event) => {
    if (event.key?.includes('token') || event.key === 'auth') {
      console.log('[Stoflow Web SSO] 🔄 Token modifié, re-synchronisation...');
      setTimeout(() => syncTokenToPlugin(), 100);
    }
  });

  // Observer les changements directs (même onglet)
  const originalSetItem = localStorage.setItem;
  localStorage.setItem = function(key, value) {
    originalSetItem.apply(this, [key, value]);
    if (key.includes('token') || key === 'auth') {
      console.log('[Stoflow Web SSO] 🔄 Token modifié (setItem), re-synchronisation...');
      setTimeout(() => syncTokenToPlugin(), 100);
    }
  };

  // Écouter les messages postMessage depuis le frontend
  console.log('📡 [CONTENT SCRIPT] Installation du listener postMessage...');
  window.addEventListener('message', (event) => {
    console.log('📡 [CONTENT SCRIPT] Message reçu:', event.data);

    if (event.data?.type === 'STOFLOW_SYNC_TOKEN') {
      console.log('');
      console.log('📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬');
      console.log('📬 [CONTENT SCRIPT] TOKEN REÇU VIA POSTMESSAGE');
      console.log('📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬');
      const { access_token, refresh_token } = event.data;
      console.log('📬 Access Token:', access_token ? 'Présent (' + access_token.substring(0, 20) + '...)' : 'MANQUANT');
      console.log('📬 Refresh Token:', refresh_token ? 'Présent' : 'Absent');

      if (access_token) {
        console.log('📬 Envoi au background script...');
        syncTokenDirectly(access_token, refresh_token);
      } else {
        console.error('📬 ❌ Pas de token à synchroniser');
      }
    }
  });
  console.log('📡 [CONTENT SCRIPT] ✅ Listener postMessage installé');
}

/**
 * Synchronise un token reçu directement (via postMessage)
 */
async function syncTokenDirectly(accessToken: string, refreshToken: string | null) {
  console.log('');
  console.log('💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌');
  console.log('💌 [CONTENT] ENVOI TOKEN AU BACKGROUND');
  console.log('💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌');

  try {
    console.log('💌 Appel chrome.runtime.sendMessage...');
    console.log('💌 Action: SYNC_TOKEN_FROM_WEBSITE');
    console.log('💌 Token:', accessToken.substring(0, 20) + '...');

    const response = await chrome.runtime.sendMessage({
      action: 'SYNC_TOKEN_FROM_WEBSITE',
      access_token: accessToken,
      refresh_token: refreshToken
    });

    console.log('💌 Réponse reçue du background:', response);

    if (response?.success) {
      console.log('💌 ✅✅✅ SUCCÈS - Token synchronisé ✅✅✅');
      showSyncNotification();
    } else {
      console.error('💌 ❌ Échec:', response?.error);
    }

    console.log('💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌');
    console.log('');
  } catch (error) {
    console.error('💌 ❌❌❌ ERREUR envoi au plugin:', error);
    console.error('💌 Stack:', error.stack);
    console.log('💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌💌');
    console.log('');
  }
}

// ==================== INIT ====================

// Synchroniser immédiatement au chargement
setTimeout(() => {
  syncTokenToPlugin();
}, 500);

// Surveiller les changements
watchLocalStorageChanges();

// Re-synchroniser toutes les 30 secondes (au cas où)
setInterval(() => {
  const token = getTokenFromLocalStorage();
  if (token) {
    syncTokenToPlugin();
  }
}, 30000);

console.log('[Stoflow Web SSO] ✅ Surveillance active du token');
