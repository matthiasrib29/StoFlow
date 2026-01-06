/**
 * Tests for useAuth composable
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock chrome.storage before importing useAuth
const mockStorage: Record<string, any> = {};

global.chrome = {
  storage: {
    local: {
      get: vi.fn((keys) => {
        if (Array.isArray(keys)) {
          const result: Record<string, any> = {};
          keys.forEach(key => {
            if (mockStorage[key] !== undefined) {
              result[key] = mockStorage[key];
            }
          });
          return Promise.resolve(result);
        }
        return Promise.resolve(mockStorage);
      }),
      set: vi.fn((data) => {
        Object.assign(mockStorage, data);
        return Promise.resolve();
      }),
      remove: vi.fn((keys) => {
        if (Array.isArray(keys)) {
          keys.forEach(key => delete mockStorage[key]);
        } else {
          delete mockStorage[keys];
        }
        return Promise.resolve();
      }),
      clear: vi.fn(() => {
        Object.keys(mockStorage).forEach(key => delete mockStorage[key]);
        return Promise.resolve();
      })
    },
    sync: {
      get: vi.fn(),
      set: vi.fn(),
      remove: vi.fn(),
      clear: vi.fn()
    }
  },
  runtime: {
    sendMessage: vi.fn(),
    onMessage: {
      addListener: vi.fn()
    }
  },
  tabs: {
    query: vi.fn(),
    sendMessage: vi.fn()
  }
} as any;

// Mock fetch
global.fetch = vi.fn();

// Import after mocks are set up
import { useAuth } from '../src/composables/useAuth';
import { CONSTANTS } from '../src/config/environment';

describe('useAuth', () => {
  beforeEach(() => {
    // Clear storage before each test
    Object.keys(mockStorage).forEach(key => delete mockStorage[key]);
    vi.clearAllMocks();
  });

  describe('checkAuth', () => {
    it('should return false when no token is stored', async () => {
      const { checkAuth, isAuthenticated } = useAuth();

      const result = await checkAuth();

      expect(result).toBe(false);
      expect(isAuthenticated.value).toBe(false);
    });

    it('should return true and set token when token exists', async () => {
      mockStorage[CONSTANTS.STORAGE_KEYS.ACCESS_TOKEN] = 'test-access-token';
      mockStorage[CONSTANTS.STORAGE_KEYS.USER_DATA] = { user_id: 1, role: 'user' };

      const { checkAuth, isAuthenticated, token, user } = useAuth();

      const result = await checkAuth();

      expect(result).toBe(true);
      expect(isAuthenticated.value).toBe(true);
      expect(token.value).toBe('test-access-token');
      expect(user.value).toEqual({ user_id: 1, role: 'user' });
    });
  });

  describe('login', () => {
    it('should store tokens on successful login', async () => {
      const mockResponse = {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        user_id: 42,
        role: 'admin',
        subscription_tier: 'premium'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      });

      const { login, token, isAuthenticated } = useAuth();

      const result = await login({ email: 'test@example.com', password: 'password123' });

      expect(result).toBe(true);
      expect(token.value).toBe('new-access-token');
      expect(isAuthenticated.value).toBe(true);
      expect(mockStorage[CONSTANTS.STORAGE_KEYS.ACCESS_TOKEN]).toBe('new-access-token');
      expect(mockStorage[CONSTANTS.STORAGE_KEYS.REFRESH_TOKEN]).toBe('new-refresh-token');
    });

    it('should set error on failed login', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ detail: 'Invalid credentials' })
      });

      const { login, error, isAuthenticated } = useAuth();

      const result = await login({ email: 'test@example.com', password: 'wrong' });

      expect(result).toBe(false);
      expect(error.value).toBe('Invalid credentials');
      expect(isAuthenticated.value).toBe(false);
    });
  });

  describe('logout', () => {
    it('should clear tokens and user data', async () => {
      mockStorage[CONSTANTS.STORAGE_KEYS.ACCESS_TOKEN] = 'test-token';
      mockStorage[CONSTANTS.STORAGE_KEYS.REFRESH_TOKEN] = 'test-refresh';
      mockStorage[CONSTANTS.STORAGE_KEYS.USER_DATA] = { user_id: 1 };

      const { logout, token, user, isAuthenticated, checkAuth } = useAuth();

      // First authenticate
      await checkAuth();
      expect(isAuthenticated.value).toBe(true);

      // Then logout
      await logout();

      expect(token.value).toBe(null);
      expect(user.value).toBe(null);
      expect(isAuthenticated.value).toBe(false);
    });
  });

  describe('setTokenFromWebsite', () => {
    it('should store token from external source (SSO)', async () => {
      const { setTokenFromWebsite, token, isAuthenticated } = useAuth();

      await setTokenFromWebsite('sso-access-token', 'sso-refresh-token', { user_id: 99 });

      expect(token.value).toBe('sso-access-token');
      expect(isAuthenticated.value).toBe(true);
      expect(mockStorage[CONSTANTS.STORAGE_KEYS.ACCESS_TOKEN]).toBe('sso-access-token');
      expect(mockStorage[CONSTANTS.STORAGE_KEYS.REFRESH_TOKEN]).toBe('sso-refresh-token');
    });
  });
});
