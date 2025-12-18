import { ContentLogger } from '../utils/logger';

/**
 * Script injector for Stoflow Vinted API
 *
 * Injects stoflow-vinted-api.js into MAIN world to access Webpack modules
 * Creates a bridge for communication between MAIN and ISOLATED worlds
 *
 * Author: Claude
 * Date: 2025-12-11
 */

// Inject the Stoflow API script into the page's MAIN world
function injectStoflowAPI() {
  // Éviter la double injection
  if (document.getElementById('stoflow-api-script')) {
    ContentLogger.debug('🛍️ [Stoflow] API script déjà injecté, skip');
    return;
  }

  const script = document.createElement('script');
  script.id = 'stoflow-api-script';
  script.src = chrome.runtime.getURL('src/content/stoflow-vinted-api.js');
  script.type = 'text/javascript';

  script.onload = () => {
    ContentLogger.debug('🛍️ [Stoflow] API script injecté dans MAIN world');

    // Notify MAIN world to initialize
    window.postMessage({ type: 'STOFLOW_INIT_API' }, '*');
  };

  script.onerror = (error) => {
    ContentLogger.error('🛍️ [Stoflow] Erreur injection API script:', error);
  };

  (document.head || document.documentElement).appendChild(script);
}

// Initialize on load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', injectStoflowAPI);
} else {
  injectStoflowAPI();
}

// Bridge for MAIN <-> ISOLATED communication
window.addEventListener('message', (event) => {
  // Only accept messages from same origin
  if (event.source !== window) return;

  const message = event.data;

  if (message.type === 'STOFLOW_API_READY') {
    ContentLogger.debug('🛍️ [Stoflow] ✅ API Vinted prête (via Webpack hook);');
  }

  if (message.type === 'STOFLOW_API_ERROR') {
    ContentLogger.error('🛍️ [Stoflow] ❌ Erreur API:', message.error);
  }
});

ContentLogger.debug('🛍️ [Stoflow] API injector loaded');
