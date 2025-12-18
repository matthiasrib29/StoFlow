/**
 * Configuration de l'environnement de test Vitest
 */

import { vi } from 'vitest';

// Mock de chrome.storage API
global.chrome = {
  storage: {
    local: {
      get: vi.fn(),
      set: vi.fn(),
      remove: vi.fn(),
      clear: vi.fn()
    },
    sync: {
      get: vi.fn(),
      set: vi.fn(),
      remove: vi.fn(),
      clear: vi.fn()
    }
  },
  tabs: {
    query: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    remove: vi.fn()
  },
  windows: {
    update: vi.fn()
  },
  runtime: {
    sendMessage: vi.fn(),
    onMessage: {
      addListener: vi.fn()
    }
  }
} as any;

// Mock de import.meta.env pour les tests
vi.stubGlobal('import.meta', {
  env: {
    VITE_BACKEND_URL: 'http://localhost:8000',
    VITE_POLL_INTERVAL: '5000',
    VITE_POLL_MAX_INTERVAL: '60000',
    VITE_API_TIMEOUT: '30000',
    VITE_ENABLE_DEBUG_LOGS: 'false',
    VITE_APP_VERSION: '2.0.0',
    DEV: true,
    PROD: false
  }
});
