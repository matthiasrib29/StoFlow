import { ContentLogger } from '../utils/logger';
import { ENV } from '../config/environment';

/**
 * Script injector for Stoflow Vinted API
 *
 * Injects modular scripts into MAIN world to access Webpack modules.
 * Scripts are loaded in sequence: logger -> session -> api-core -> bootstrap
 *
 * Author: Claude
 * Date: 2026-01-06
 */

// Module files to inject in order
const API_MODULES = [
  'src/content/stoflow-vinted-logger.js',
  'src/content/stoflow-vinted-session.js',
  'src/content/stoflow-vinted-api-core.js',
  'src/content/stoflow-vinted-bootstrap.js'
];

/**
 * Inject a single script and return a promise
 */
function injectScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = chrome.runtime.getURL(src);
    script.type = 'text/javascript';

    script.onload = () => {
      ContentLogger.debug(`🛍️ [Stoflow] Loaded: ${src}`);
      resolve();
    };

    script.onerror = (error) => {
      ContentLogger.error(`🛍️ [Stoflow] Failed to load: ${src}`, error);
      reject(error);
    };

    (document.head || document.documentElement).appendChild(script);
  });
}

// Inject the Stoflow API scripts into the page's MAIN world
async function injectStoflowAPI() {
  // Guard: Avoid double injection (check both window flag and DOM marker)
  if ((window as any).__STOFLOW_INJECTED__) {
    ContentLogger.debug('🛍️ [Stoflow] Already injected (window flag), skip');
    return;
  }

  if (document.getElementById('stoflow-api-marker')) {
    ContentLogger.debug('🛍️ [Stoflow] API scripts already injected (DOM marker), skip');
    return;
  }

  // SECURITY: Set injection flag as read-only to prevent tampering
  Object.defineProperty(window, '__STOFLOW_INJECTED__', {
    value: true,
    writable: false,
    configurable: false
  });

  // Mark as injected
  const marker = document.createElement('div');
  marker.id = 'stoflow-api-marker';
  marker.style.display = 'none';
  document.body.appendChild(marker);

  // SECURITY: Set debug flag in MAIN world as read-only
  const debugScript = document.createElement('script');
  debugScript.textContent = `
    Object.defineProperty(window, '__STOFLOW_DEBUG__', {
      value: ${ENV.ENABLE_DEBUG_LOGS},
      writable: false,
      configurable: false
    });
  `;
  (document.head || document.documentElement).appendChild(debugScript);
  debugScript.remove();

  try {
    // Load modules sequentially (order matters)
    for (const module of API_MODULES) {
      await injectScript(module);
    }

    ContentLogger.debug('🛍️ [Stoflow] All API modules loaded');

    // Notify MAIN world to initialize
    window.postMessage({ type: 'STOFLOW_INIT_API' }, window.location.origin);
  } catch (error) {
    ContentLogger.error('🛍️ [Stoflow] Error loading API modules:', error);
  }
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
