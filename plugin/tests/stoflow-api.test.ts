/**
 * Tests for StoflowAPI client
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

  describe('isAuthenticated', () => {
    it('should return false when no token is stored', async () => {
      (chrome.storage.local.get as any).mockResolvedValue({});

      const result = await StoflowAPI.isAuthenticated();

      expect(result).toBe(false);
    });

    it('should return true when token exists', async () => {
      (chrome.storage.local.get as any).mockResolvedValue({
        stoflow_access_token: 'valid-token'
      });

      const result = await StoflowAPI.isAuthenticated();

      expect(result).toBe(true);
    });
  });

  describe('getToken', () => {
    it('should return null when no token', async () => {
      (chrome.storage.local.get as any).mockResolvedValue({});

      const token = await StoflowAPI.getToken();

      expect(token).toBe(null);
    });

    it('should return token when available', async () => {
      (chrome.storage.local.get as any).mockResolvedValue({
        stoflow_access_token: 'my-token'
      });

      const token = await StoflowAPI.getToken();

      expect(token).toBe('my-token');
    });
  });

  describe('request', () => {
    it('should make authenticated request with correct headers', async () => {
      (chrome.storage.local.get as any).mockResolvedValue({
        stoflow_access_token: 'test-token'
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ data: 'test' })
      });

      await StoflowAPI.request('/test-endpoint', { method: 'GET' });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/test-endpoint'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
            'Content-Type': 'application/json'
          })
        })
      );
    });

    it('should throw error on 401 response', async () => {
      (chrome.storage.local.get as any).mockResolvedValue({
        stoflow_access_token: 'expired-token'
      });

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Token expired' })
      });

      await expect(StoflowAPI.request('/test', { method: 'GET' }))
        .rejects.toThrow();
    });
  });

  describe('getTasksWithLongPolling', () => {
    it('should make request with correct timeout', async () => {
      (chrome.storage.local.get as any).mockResolvedValue({
        stoflow_access_token: 'test-token'
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ tasks: [] })
      });

      await StoflowAPI.getTasksWithLongPolling(30);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('timeout=30'),
        expect.any(Object)
      );
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
        expect.stringContaining('/vinted/sync'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('12345')
        })
      );
    });
  });

  describe('completeTask', () => {
    it('should send task completion to backend', async () => {
      (chrome.storage.local.get as any).mockResolvedValue({
        stoflow_access_token: 'test-token'
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true })
      });

      await StoflowAPI.completeTask('task-123', { result: 'done' });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/tasks/task-123/complete'),
        expect.objectContaining({
          method: 'POST'
        })
      );
    });
  });

  describe('failTask', () => {
    it('should send task failure to backend', async () => {
      (chrome.storage.local.get as any).mockResolvedValue({
        stoflow_access_token: 'test-token'
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true })
      });

      await StoflowAPI.failTask('task-456', 'Something went wrong');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/tasks/task-456/fail'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('Something went wrong')
        })
      );
    });
  });
});
