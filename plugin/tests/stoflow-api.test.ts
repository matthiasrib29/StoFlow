/**
 * Tests for StoflowAPI client
 *
 * Updated: 2026-01-06 - Removed polling-related tests (externally_connectable migration)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock chrome APIs
global.chrome = {
  storage: {
    local: {
      get: vi.fn(() => Promise.resolve({})),
      set: vi.fn(() => Promise.resolve()),
      remove: vi.fn(() => Promise.resolve()),
      clear: vi.fn(() => Promise.resolve())
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
    },
    lastError: null
  },
  tabs: {
    query: vi.fn(),
    sendMessage: vi.fn()
  }
} as any;

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Import after mocks
import { StoflowAPI } from '../src/api/StoflowAPI';

describe('StoflowAPI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset auth state
    (chrome.storage.local.get as any).mockResolvedValue({});
  });

  describe('refreshAccessToken', () => {
    it('should return error when no refresh token', async () => {
      (chrome.storage.local.get as any).mockResolvedValue({});

      const result = await StoflowAPI.refreshAccessToken();

      expect(result.success).toBe(false);
      expect(result.error).toBe('no_refresh_token');
    });

    it('should refresh token successfully', async () => {
      (chrome.storage.local.get as any).mockResolvedValue({
        stoflow_refresh_token: 'valid-refresh-token'
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          access_token: 'new-access-token',
          refresh_token: 'new-refresh-token'
        })
      });

      const result = await StoflowAPI.refreshAccessToken();

      expect(result.success).toBe(true);
      expect(chrome.storage.local.set).toHaveBeenCalledWith(
        expect.objectContaining({
          stoflow_access_token: 'new-access-token'
        })
      );
    });

    it('should clear tokens on 401 response', async () => {
      (chrome.storage.local.get as any).mockResolvedValue({
        stoflow_refresh_token: 'expired-refresh-token'
      });

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        text: () => Promise.resolve('Token expired')
      });

      const result = await StoflowAPI.refreshAccessToken();

      expect(result.success).toBe(false);
      expect(chrome.storage.local.remove).toHaveBeenCalled();
    });
  });

  describe('syncVintedUser', () => {
    it('should send vinted user data to backend', async () => {
      (chrome.storage.local.get as any).mockResolvedValue({
        stoflow_access_token: 'test-token'
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true })
      });

      await StoflowAPI.syncVintedUser('12345', 'testuser');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/vinted/connect'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('12345')
        })
      );
    });

    it('should throw error on backend failure', async () => {
      (chrome.storage.local.get as any).mockResolvedValue({
        stoflow_access_token: 'test-token'
      });

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        text: () => Promise.resolve('Server error')
      });

      await expect(StoflowAPI.syncVintedUser('12345', 'testuser'))
        .rejects.toThrow();
    });
  });

  describe('getVintedConnectionStatus', () => {
    it('should fetch vinted connection status', async () => {
      (chrome.storage.local.get as any).mockResolvedValue({
        stoflow_access_token: 'test-token'
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          is_connected: true,
          vinted_user_id: '12345',
          login: 'testuser'
        })
      });

      const result = await StoflowAPI.getVintedConnectionStatus();

      expect(result.is_connected).toBe(true);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/vinted/status'),
        expect.objectContaining({
          method: 'GET'
        })
      );
    });
  });

  describe('notifyVintedDisconnect', () => {
    it('should notify backend of vinted disconnect', async () => {
      (chrome.storage.local.get as any).mockResolvedValue({
        stoflow_access_token: 'test-token'
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ message: 'Disconnection recorded' })
      });

      const result = await StoflowAPI.notifyVintedDisconnect();

      expect(result.message).toBe('Disconnection recorded');
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/vinted/notify-disconnect'),
        expect.objectContaining({
          method: 'POST'
        })
      );
    });
  });
});
