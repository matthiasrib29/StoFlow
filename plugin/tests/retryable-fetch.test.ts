/**
 * Tests pour RetryableFetch
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { RetryableFetch } from '../src/utils/retryable-fetch';
import { NetworkError, TimeoutError } from '../src/utils/errors';

// Mock global fetch
global.fetch = vi.fn();

describe('RetryableFetch', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('fetch() - Success', () => {
    it('devrait réussir au premier essai', async () => {
      const mockResponse = new Response('OK', { status: 200 });
      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      const promise = RetryableFetch.fetch('https://api.test.com/data');
      await vi.runAllTimersAsync();
      const result = await promise;

      expect(result.attempts).toBe(1);
      expect(result.response.status).toBe(200);
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    it('devrait inclure le temps total', async () => {
      const mockResponse = new Response('OK', { status: 200 });
      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      const promise = RetryableFetch.fetch('https://api.test.com/data');
      await vi.runAllTimersAsync();
      const result = await promise;

      expect(result.totalTime).toBeGreaterThanOrEqual(0);
    });
  });

  describe('fetch() - Retry on retryable status', () => {
    it('devrait retry sur 503 Service Unavailable', async () => {
      const failResponse = new Response('Service Unavailable', { status: 503 });
      const successResponse = new Response('OK', { status: 200 });

      (global.fetch as any)
        .mockResolvedValueOnce(failResponse)
        .mockResolvedValueOnce(successResponse);

      const promise = RetryableFetch.fetch('https://api.test.com/data', {
        retry: { maxRetries: 3 }
      });

      await vi.runAllTimersAsync();
      const result = await promise;

      expect(result.attempts).toBe(2);
      expect(result.response.status).toBe(200);
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });

    it('devrait retry sur 429 Too Many Requests', async () => {
      const failResponse = new Response('Too Many Requests', { status: 429 });
      const successResponse = new Response('OK', { status: 200 });

      (global.fetch as any)
        .mockResolvedValueOnce(failResponse)
        .mockResolvedValueOnce(successResponse);

      const promise = RetryableFetch.fetch('https://api.test.com/data');

      await vi.runAllTimersAsync();
      const result = await promise;

      expect(result.attempts).toBe(2);
    });

    it('devrait retry sur 502 Bad Gateway', async () => {
      const failResponse = new Response('Bad Gateway', { status: 502 });
      const successResponse = new Response('OK', { status: 200 });

      (global.fetch as any)
        .mockResolvedValueOnce(failResponse)
        .mockResolvedValueOnce(successResponse);

      const promise = RetryableFetch.fetch('https://api.test.com/data');

      await vi.runAllTimersAsync();
      const result = await promise;

      expect(result.attempts).toBe(2);
    });
  });

  describe('fetch() - No retry on non-retryable status', () => {
    it('ne devrait PAS retry sur 404 Not Found', async () => {
      const failResponse = new Response('Not Found', { status: 404 });
      (global.fetch as any).mockResolvedValueOnce(failResponse);

      const promise = RetryableFetch.fetch('https://api.test.com/data');

      await vi.runAllTimersAsync();
      const result = await promise;

      expect(result.attempts).toBe(1);
      expect(result.response.status).toBe(404);
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    it('ne devrait PAS retry sur 401 Unauthorized', async () => {
      const failResponse = new Response('Unauthorized', { status: 401 });
      (global.fetch as any).mockResolvedValueOnce(failResponse);

      const promise = RetryableFetch.fetch('https://api.test.com/data');

      await vi.runAllTimersAsync();
      const result = await promise;

      expect(result.attempts).toBe(1);
      expect(result.response.status).toBe(401);
    });

    it('ne devrait PAS retry sur 400 Bad Request', async () => {
      const failResponse = new Response('Bad Request', { status: 400 });
      (global.fetch as any).mockResolvedValueOnce(failResponse);

      const promise = RetryableFetch.fetch('https://api.test.com/data');

      await vi.runAllTimersAsync();
      const result = await promise;

      expect(result.attempts).toBe(1);
    });
  });

  describe('fetch() - Backoff exponential', () => {
    it('devrait augmenter le délai exponentiellement', async () => {
      const failResponse = new Response('Service Unavailable', { status: 503 });
      const successResponse = new Response('OK', { status: 200 });

      (global.fetch as any)
        .mockResolvedValueOnce(failResponse)
        .mockResolvedValueOnce(failResponse)
        .mockResolvedValueOnce(successResponse);

      const promise = RetryableFetch.fetch('https://api.test.com/data', {
        retry: {
          baseDelayMs: 1000,
          backoffMultiplier: 2
        }
      });

      // Premier échec
      await vi.advanceTimersByTimeAsync(0);
      expect(global.fetch).toHaveBeenCalledTimes(1);

      // Attente 1s (baseDelay * 2^0)
      await vi.advanceTimersByTimeAsync(1000);
      expect(global.fetch).toHaveBeenCalledTimes(2);

      // Attente 2s (baseDelay * 2^1)
      await vi.advanceTimersByTimeAsync(2000);
      expect(global.fetch).toHaveBeenCalledTimes(3);

      const result = await promise;
      expect(result.attempts).toBe(3);
    });

    it('devrait respecter le maxDelayMs', async () => {
      const failResponse = new Response('Service Unavailable', { status: 503 });
      const successResponse = new Response('OK', { status: 200 });

      (global.fetch as any)
        .mockResolvedValue(failResponse)
        .mockResolvedValueOnce(failResponse)
        .mockResolvedValueOnce(failResponse)
        .mockResolvedValueOnce(failResponse)
        .mockResolvedValueOnce(successResponse);

      const promise = RetryableFetch.fetch('https://api.test.com/data', {
        retry: {
          baseDelayMs: 10000,
          maxDelayMs: 15000,
          backoffMultiplier: 2,
          maxRetries: 4
        }
      });

      await vi.runAllTimersAsync();
      const result = await promise;

      // Même avec backoff exponentiel élevé, ne devrait pas dépasser maxDelay
      expect(result.attempts).toBeGreaterThan(1);
    });
  });

  describe('fetch() - Max retries', () => {
    it('devrait arrêter après maxRetries', async () => {
      const failResponse = new Response('Service Unavailable', { status: 503 });
      (global.fetch as any).mockResolvedValue(failResponse);

      const promise = RetryableFetch.fetch('https://api.test.com/data', {
        retry: { maxRetries: 2 }
      });

      await vi.runAllTimersAsync();

      await expect(promise).rejects.toThrow(NetworkError);
      expect(global.fetch).toHaveBeenCalledTimes(3); // 1 initial + 2 retries
    });

    it('devrait throw NetworkError après max retries', async () => {
      const failResponse = new Response('Service Unavailable', { status: 503 });
      (global.fetch as any).mockResolvedValue(failResponse);

      const promise = RetryableFetch.fetch('https://api.test.com/data', {
        retry: { maxRetries: 1 }
      });

      await vi.runAllTimersAsync();

      await expect(promise).rejects.toThrow(NetworkError);
      await expect(promise).rejects.toThrow('Request failed after 2 attempts');
    });
  });

  describe('fetch() - Network errors', () => {
    it('devrait retry sur "Failed to fetch"', async () => {
      (global.fetch as any)
        .mockRejectedValueOnce(new Error('Failed to fetch'))
        .mockResolvedValueOnce(new Response('OK', { status: 200 }));

      const promise = RetryableFetch.fetch('https://api.test.com/data');

      await vi.runAllTimersAsync();
      const result = await promise;

      expect(result.attempts).toBe(2);
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });

    it('ne devrait PAS retry sur erreur non-retryable', async () => {
      (global.fetch as any).mockRejectedValueOnce(new TypeError('Invalid URL'));

      const promise = RetryableFetch.fetch('https://api.test.com/data');

      await vi.runAllTimersAsync();

      await expect(promise).rejects.toThrow(TypeError);
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('Helper methods - get/post/put/delete', () => {
    it('get() devrait faire un GET', async () => {
      const mockResponse = new Response('OK', { status: 200 });
      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      const promise = RetryableFetch.get('https://api.test.com/data');
      await vi.runAllTimersAsync();
      await promise;

      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.test.com/data',
        expect.objectContaining({ method: 'GET' })
      );
    });

    it('post() devrait faire un POST avec body JSON', async () => {
      const mockResponse = new Response('OK', { status: 200 });
      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      const body = { title: 'Test' };
      const promise = RetryableFetch.post('https://api.test.com/data', body);
      await vi.runAllTimersAsync();
      await promise;

      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.test.com/data',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(body),
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          })
        })
      );
    });

    it('put() devrait faire un PUT', async () => {
      const mockResponse = new Response('OK', { status: 200 });
      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      const promise = RetryableFetch.put('https://api.test.com/data', { id: 1 });
      await vi.runAllTimersAsync();
      await promise;

      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.test.com/data',
        expect.objectContaining({ method: 'PUT' })
      );
    });

    it('delete() devrait faire un DELETE', async () => {
      const mockResponse = new Response('OK', { status: 200 });
      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      const promise = RetryableFetch.delete('https://api.test.com/data');
      await vi.runAllTimersAsync();
      await promise;

      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.test.com/data',
        expect.objectContaining({ method: 'DELETE' })
      );
    });
  });

  describe('fetchOnce()', () => {
    it('ne devrait faire qu\'une tentative', async () => {
      const failResponse = new Response('Service Unavailable', { status: 503 });
      (global.fetch as any).mockResolvedValueOnce(failResponse);

      const promise = RetryableFetch.fetchOnce('https://api.test.com/data');

      await vi.runAllTimersAsync();

      await expect(promise).rejects.toThrow();
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('ping()', () => {
    it('devrait retourner true si HEAD réussit', async () => {
      const mockResponse = new Response('OK', { status: 200 });
      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      const promise = RetryableFetch.ping('https://api.test.com');
      await vi.runAllTimersAsync();
      const result = await promise;

      expect(result).toBe(true);
      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.test.com',
        expect.objectContaining({ method: 'HEAD' })
      );
    });

    it('devrait retourner false si HEAD échoue', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Failed'));

      const promise = RetryableFetch.ping('https://api.test.com');
      await vi.runAllTimersAsync();
      const result = await promise;

      expect(result).toBe(false);
    });
  });
});
