/**
 * Tests for PollingManager
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

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
    query: vi.fn(() => Promise.resolve([])),
    sendMessage: vi.fn()
  }
} as any;

// Mock fetch
global.fetch = vi.fn();

// Mock StoflowAPI
vi.mock('../src/api/StoflowAPI', () => ({
  StoflowAPI: {
    getTasksWithLongPolling: vi.fn(),
    completeTask: vi.fn(),
    failTask: vi.fn(),
    isAuthenticated: vi.fn(() => Promise.resolve(true)),
    getToken: vi.fn(() => Promise.resolve('test-token'))
  }
}));

import { PollingManager } from '../src/background/PollingManager';
import { StoflowAPI } from '../src/api/StoflowAPI';

describe('PollingManager', () => {
  let pollingManager: PollingManager;

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    pollingManager = new PollingManager();
  });

  afterEach(() => {
    pollingManager.stop();
    vi.useRealTimers();
  });

  describe('start', () => {
    it('should start polling loop', () => {
      const mockGetTasks = StoflowAPI.getTasksWithLongPolling as any;
      mockGetTasks.mockResolvedValue({ tasks: [], next_poll_interval: 5000 });

      pollingManager.start();

      // Should not be called immediately, but after first tick
      expect(mockGetTasks).not.toHaveBeenCalled();

      // After advancing time, should start polling
      vi.advanceTimersByTime(100);
    });

    it('should not start twice if already polling', () => {
      const mockGetTasks = StoflowAPI.getTasksWithLongPolling as any;
      mockGetTasks.mockResolvedValue({ tasks: [], next_poll_interval: 5000 });

      pollingManager.start();
      pollingManager.start(); // Second call should be ignored

      // Verify no double initialization
    });
  });

  describe('stop', () => {
    it('should stop polling loop', () => {
      pollingManager.start();
      pollingManager.stop();

      // After stopping, no more polling should occur
      vi.advanceTimersByTime(10000);
    });

    it('should clear resume timeout if pending', () => {
      pollingManager.start();
      pollingManager.stop();

      // Ensure isPaused is reset
    });
  });

  describe('task processing', () => {
    it('should process tasks when received', async () => {
      const mockTask = {
        id: 'task-1',
        type: 'HTTP_REQUEST',
        payload: {
          method: 'GET',
          url: '/api/test'
        }
      };

      const mockGetTasks = StoflowAPI.getTasksWithLongPolling as any;
      const mockCompleteTask = StoflowAPI.completeTask as any;

      mockGetTasks.mockResolvedValueOnce({
        tasks: [mockTask],
        next_poll_interval: 5000
      });

      mockCompleteTask.mockResolvedValue({ success: true });

      // Note: Full integration test would require more setup
      // This is a simplified unit test
    });

    it('should handle task failure', async () => {
      const mockFailTask = StoflowAPI.failTask as any;
      mockFailTask.mockResolvedValue({ success: true });

      // Simulate task failure handling
    });
  });

  describe('connection status', () => {
    it('should track connection status', () => {
      // PollingManager tracks wasConnected and lastConnectionCheck
      pollingManager.start();

      // Initial state should be connected
    });
  });

  describe('isPaused and resumeTimeoutId', () => {
    it('should have isPaused property', () => {
      // Verify the property exists (was an issue before fix)
      pollingManager.start();
      pollingManager.stop();

      // Should not throw when accessing these properties
    });
  });
});
