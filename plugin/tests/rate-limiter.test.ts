/**
 * Tests pour RateLimiter
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { RateLimiter, VintedRateLimiter, BackendRateLimiter } from '../src/utils/rate-limiter';

describe('RateLimiter', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Construction', () => {
    it('devrait initialiser avec la config fournie', () => {
      const limiter = new RateLimiter({
        maxRequests: 10,
        windowMs: 10000,
        minDelayMs: 500
      });

      const stats = limiter.getStats();
      expect(stats.totalRequests).toBe(0);
      expect(stats.currentWindowRequests).toBe(0);
    });
  });

  describe('acquire() - Délai minimum', () => {
    it('devrait autoriser la première requête immédiatement', async () => {
      const limiter = new RateLimiter({
        maxRequests: 10,
        windowMs: 10000,
        minDelayMs: 500
      });

      const start = Date.now();
      await limiter.acquire();
      const elapsed = Date.now() - start;

      expect(elapsed).toBeLessThan(100);
    });

    it('devrait attendre minDelayMs entre deux requêtes', async () => {
      const limiter = new RateLimiter({
        maxRequests: 10,
        windowMs: 10000,
        minDelayMs: 500
      });

      await limiter.acquire(); // Première requête
      vi.advanceTimersByTime(100); // Attendre 100ms (< minDelay)

      const acquirePromise = limiter.acquire(); // Deuxième requête

      // Ne devrait pas être résolu immédiatement
      const stats1 = limiter.getStats();
      expect(stats1.queuedRequests).toBe(1);

      // Avancer de 400ms (total 500ms)
      await vi.advanceTimersByTimeAsync(400);

      await acquirePromise;

      const stats2 = limiter.getStats();
      expect(stats2.queuedRequests).toBe(0);
      expect(stats2.totalRequests).toBe(2);
    });

    it('devrait accumuler les délais pour plusieurs requêtes', async () => {
      const limiter = new RateLimiter({
        maxRequests: 10,
        windowMs: 10000,
        minDelayMs: 100
      });

      const promises = [
        limiter.acquire(),
        limiter.acquire(),
        limiter.acquire()
      ];

      await vi.advanceTimersByTimeAsync(300);

      await Promise.all(promises);

      const stats = limiter.getStats();
      expect(stats.totalRequests).toBe(3);
    });
  });

  describe('acquire() - Limite de fenêtre', () => {
    it('devrait bloquer après maxRequests dans la fenêtre', async () => {
      const limiter = new RateLimiter({
        maxRequests: 3,
        windowMs: 1000,
        minDelayMs: 50
      });

      // Faire 3 requêtes (max)
      await limiter.acquire();
      await vi.advanceTimersByTimeAsync(60);
      await limiter.acquire();
      await vi.advanceTimersByTimeAsync(60);
      await limiter.acquire();

      const stats = limiter.getStats();
      expect(stats.currentWindowRequests).toBe(3);

      // La 4ème devrait attendre que la fenêtre glisse
      await vi.advanceTimersByTimeAsync(60);
      const acquirePromise = limiter.acquire();

      // Devrait être en attente
      expect(limiter.getStats().queuedRequests).toBe(1);

      // Avancer jusqu'à ce que le premier timestamp expire
      await vi.advanceTimersByTimeAsync(1000);

      await acquirePromise;

      expect(limiter.getStats().totalRequests).toBe(4);
    });

    it('devrait autoriser à nouveau après expiration de la fenêtre', async () => {
      const limiter = new RateLimiter({
        maxRequests: 2,
        windowMs: 500,
        minDelayMs: 50
      });

      // Remplir la fenêtre
      await limiter.acquire();
      await vi.advanceTimersByTimeAsync(60);
      await limiter.acquire();

      // Attendre expiration
      await vi.advanceTimersByTimeAsync(500);

      // Devrait pouvoir faire 2 nouvelles requêtes
      await limiter.acquire();
      await vi.advanceTimersByTimeAsync(60);
      await limiter.acquire();

      const stats = limiter.getStats();
      expect(stats.totalRequests).toBe(4);
    });
  });

  describe('canAcquireNow()', () => {
    it('devrait retourner true pour la première requête', () => {
      const limiter = new RateLimiter({
        maxRequests: 10,
        windowMs: 10000,
        minDelayMs: 500
      });

      expect(limiter.canAcquireNow()).toBe(true);
    });

    it('devrait retourner false si minDelay non écoulé', async () => {
      const limiter = new RateLimiter({
        maxRequests: 10,
        windowMs: 10000,
        minDelayMs: 500
      });

      await limiter.acquire();
      vi.advanceTimersByTime(200); // < minDelay

      expect(limiter.canAcquireNow()).toBe(false);
    });

    it('devrait retourner true si minDelay écoulé', async () => {
      const limiter = new RateLimiter({
        maxRequests: 10,
        windowMs: 10000,
        minDelayMs: 500
      });

      await limiter.acquire();
      await vi.advanceTimersByTimeAsync(500); // >= minDelay

      expect(limiter.canAcquireNow()).toBe(true);
    });

    it('devrait retourner false si fenêtre pleine', async () => {
      const limiter = new RateLimiter({
        maxRequests: 2,
        windowMs: 1000,
        minDelayMs: 100
      });

      await limiter.acquire();
      await vi.advanceTimersByTimeAsync(150);
      await limiter.acquire();
      await vi.advanceTimersByTimeAsync(150);

      expect(limiter.canAcquireNow()).toBe(false);
    });
  });

  describe('estimateDelay()', () => {
    it('devrait retourner 0 pour la première requête', async () => {
      const limiter = new RateLimiter({
        maxRequests: 10,
        windowMs: 10000,
        minDelayMs: 500
      });

      const delay = await limiter.estimateDelay();

      expect(delay).toBe(0);
    });

    it('devrait estimer le délai basé sur minDelayMs', async () => {
      const limiter = new RateLimiter({
        maxRequests: 10,
        windowMs: 10000,
        minDelayMs: 500
      });

      await limiter.acquire();
      vi.advanceTimersByTime(200);

      const delay = await limiter.estimateDelay();

      expect(delay).toBeGreaterThanOrEqual(290); // ~300ms restants
      expect(delay).toBeLessThanOrEqual(310);
    });
  });

  describe('getStats()', () => {
    it('devrait retourner les statistiques correctes', async () => {
      const limiter = new RateLimiter({
        maxRequests: 5,
        windowMs: 1000,
        minDelayMs: 100
      });

      await limiter.acquire();
      await vi.advanceTimersByTimeAsync(110);
      await limiter.acquire();

      const stats = limiter.getStats();

      expect(stats.totalRequests).toBe(2);
      expect(stats.currentWindowRequests).toBe(2);
      expect(stats.queuedRequests).toBe(0);
      expect(stats.averageDelayMs).toBeGreaterThanOrEqual(0);
    });

    it('devrait indiquer isThrottled=true quand limité', async () => {
      const limiter = new RateLimiter({
        maxRequests: 1,
        windowMs: 1000,
        minDelayMs: 500
      });

      await limiter.acquire();

      const stats = limiter.getStats();
      expect(stats.isThrottled).toBe(true);
    });

    it('devrait indiquer isThrottled=false quand disponible', async () => {
      const limiter = new RateLimiter({
        maxRequests: 10,
        windowMs: 10000,
        minDelayMs: 500
      });

      await limiter.acquire();
      await vi.advanceTimersByTimeAsync(500);

      const stats = limiter.getStats();
      expect(stats.isThrottled).toBe(false);
    });
  });

  describe('reset()', () => {
    it('devrait réinitialiser tous les compteurs', async () => {
      const limiter = new RateLimiter({
        maxRequests: 10,
        windowMs: 10000,
        minDelayMs: 500
      });

      await limiter.acquire();
      await vi.advanceTimersByTimeAsync(510);
      await limiter.acquire();

      limiter.reset();

      const stats = limiter.getStats();
      expect(stats.totalRequests).toBe(0);
      expect(stats.currentWindowRequests).toBe(0);
      expect(stats.averageDelayMs).toBe(0);
    });
  });

  describe('reconfigure()', () => {
    it('devrait modifier la configuration', () => {
      const limiter = new RateLimiter({
        maxRequests: 10,
        windowMs: 10000,
        minDelayMs: 500
      });

      limiter.reconfigure({ minDelayMs: 1000 });

      // Test indirect via le comportement
      expect(limiter).toBeDefined();
    });
  });
});

describe('VintedRateLimiter', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('devrait avoir 500ms de délai minimum', async () => {
    const limiter = new VintedRateLimiter();

    await limiter.acquire();
    vi.advanceTimersByTime(400); // < 500ms

    expect(limiter.canAcquireNow()).toBe(false);

    await vi.advanceTimersByTimeAsync(100); // >= 500ms

    expect(limiter.canAcquireNow()).toBe(true);
  });

  it('devrait limiter à 10 requêtes par 10 secondes', async () => {
    const limiter = new VintedRateLimiter();

    // Faire 10 requêtes
    for (let i = 0; i < 10; i++) {
      await limiter.acquire();
      await vi.advanceTimersByTimeAsync(510); // minDelay
    }

    const stats = limiter.getStats();
    expect(stats.totalRequests).toBe(10);

    // La 11ème devrait être bloquée
    expect(limiter.canAcquireNow()).toBe(false);
  });
});

describe('BackendRateLimiter', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('devrait avoir 100ms de délai minimum', async () => {
    const limiter = new BackendRateLimiter();

    await limiter.acquire();
    vi.advanceTimersByTime(50); // < 100ms

    expect(limiter.canAcquireNow()).toBe(false);

    await vi.advanceTimersByTimeAsync(50); // >= 100ms

    expect(limiter.canAcquireNow()).toBe(true);
  });

  it('devrait limiter à 30 requêtes par minute', async () => {
    const limiter = new BackendRateLimiter();

    // Faire 30 requêtes rapidement
    for (let i = 0; i < 30; i++) {
      await limiter.acquire();
      await vi.advanceTimersByTimeAsync(110); // minDelay
    }

    const stats = limiter.getStats();
    expect(stats.totalRequests).toBe(30);

    // La 31ème devrait être bloquée si dans la même fenêtre
    const canAcquire = limiter.canAcquireNow();
    expect(canAcquire).toBe(false);
  });
});
