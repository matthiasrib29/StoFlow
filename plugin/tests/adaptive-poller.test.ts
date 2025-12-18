/**
 * Tests pour AdaptivePoller
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { AdaptivePoller } from '../src/utils/adaptive-poller';

describe('AdaptivePoller', () => {
  let poller: AdaptivePoller;

  beforeEach(() => {
    poller = new AdaptivePoller({
      minInterval: 5000,
      maxInterval: 60000,
      backoffMultiplier: 1.5,
      resetOnActivity: true
    });
  });

  describe('Construction', () => {
    it('devrait initialiser avec l\'intervalle minimum', () => {
      expect(poller.getCurrentInterval()).toBe(5000);
    });

    it('devrait être actif au démarrage', () => {
      expect(poller.isActive()).toBe(true);
      expect(poller.isIdle()).toBe(false);
    });
  });

  describe('onTaskFound()', () => {
    it('devrait réinitialiser l\'intervalle au minimum', () => {
      // Augmenter d'abord l'intervalle
      poller.onNoTask();
      poller.onNoTask();
      expect(poller.getCurrentInterval()).toBeGreaterThan(5000);

      // Trouver une tâche devrait reset
      poller.onTaskFound();
      expect(poller.getCurrentInterval()).toBe(5000);
    });

    it('devrait réinitialiser le compteur de polls vides', () => {
      poller.onNoTask();
      poller.onNoTask();

      const statsBefore = poller.getStats();
      expect(statsBefore.consecutiveEmptyPolls).toBe(2);

      poller.onTaskFound();

      const statsAfter = poller.getStats();
      expect(statsAfter.consecutiveEmptyPolls).toBe(0);
    });

    it('devrait marquer le poller comme actif', () => {
      // Rendre idle
      for (let i = 0; i < 20; i++) {
        poller.onNoTask();
      }
      expect(poller.isIdle()).toBe(true);

      // Trouver une tâche
      poller.onTaskFound();
      expect(poller.isActive()).toBe(true);
      expect(poller.isIdle()).toBe(false);
    });
  });

  describe('onNoTask()', () => {
    it('devrait augmenter l\'intervalle progressivement', () => {
      const intervals: number[] = [];

      for (let i = 0; i < 5; i++) {
        intervals.push(poller.getCurrentInterval());
        poller.onNoTask();
      }

      // Chaque intervalle devrait être >= au précédent
      for (let i = 1; i < intervals.length; i++) {
        expect(intervals[i]).toBeGreaterThanOrEqual(intervals[i - 1]);
      }
    });

    it('devrait respecter le backoff multiplier (1.5x)', () => {
      const interval1 = poller.getCurrentInterval(); // 5000
      poller.onNoTask();
      const interval2 = poller.getCurrentInterval(); // 7500

      expect(interval2).toBe(Math.round(interval1 * 1.5));
    });

    it('devrait plafonner à l\'intervalle maximum', () => {
      // Augmenter jusqu'au max
      for (let i = 0; i < 20; i++) {
        poller.onNoTask();
      }

      const interval = poller.getCurrentInterval();
      expect(interval).toBe(60000);
      expect(poller.isIdle()).toBe(true);
    });

    it('devrait incrémenter le compteur de polls vides', () => {
      poller.onNoTask();
      poller.onNoTask();
      poller.onNoTask();

      const stats = poller.getStats();
      expect(stats.consecutiveEmptyPolls).toBe(3);
    });
  });

  describe('onError()', () => {
    it('devrait augmenter l\'intervalle plus rapidement qu\'onNoTask', () => {
      const poller1 = new AdaptivePoller({ minInterval: 5000, maxInterval: 60000, backoffMultiplier: 1.5, resetOnActivity: true });
      const poller2 = new AdaptivePoller({ minInterval: 5000, maxInterval: 60000, backoffMultiplier: 1.5, resetOnActivity: true });

      // Poll vide normal
      poller1.onNoTask();
      const intervalNoTask = poller1.getCurrentInterval();

      // Erreur
      poller2.onError(new Error('Test error'));
      const intervalError = poller2.getCurrentInterval();

      // L'intervalle après erreur devrait être > après no task
      expect(intervalError).toBeGreaterThan(intervalNoTask);
    });

    it('devrait incrémenter le compteur d\'erreurs', () => {
      poller.onError(new Error('Test 1'));
      poller.onError(new Error('Test 2'));

      const stats = poller.getStats();
      expect(stats.consecutiveErrors).toBe(2);
    });

    it('devrait reset après 10 erreurs consécutives', () => {
      // Augmenter l'intervalle
      for (let i = 0; i < 5; i++) {
        poller.onNoTask();
      }

      const intervalBefore = poller.getCurrentInterval();
      expect(intervalBefore).toBeGreaterThan(5000);

      // 10 erreurs consécutives
      for (let i = 0; i < 10; i++) {
        poller.onError(new Error(`Test ${i}`));
      }

      // Devrait avoir reset
      const intervalAfter = poller.getCurrentInterval();
      expect(intervalAfter).toBe(5000);

      const stats = poller.getStats();
      expect(stats.consecutiveErrors).toBe(0);
    });
  });

  describe('reset()', () => {
    it('devrait réinitialiser tous les compteurs', () => {
      poller.onNoTask();
      poller.onNoTask();
      poller.onError(new Error('Test'));

      poller.reset();

      const stats = poller.getStats();
      expect(stats.currentInterval).toBe(5000);
      expect(stats.consecutiveEmptyPolls).toBe(0);
      expect(stats.consecutiveErrors).toBe(0);
      expect(poller.isActive()).toBe(true);
    });
  });

  describe('getStats()', () => {
    it('devrait retourner les statistiques complètes', () => {
      poller.onNoTask();
      poller.onNoTask();

      const stats = poller.getStats();

      expect(stats).toHaveProperty('currentInterval');
      expect(stats).toHaveProperty('currentIntervalFormatted');
      expect(stats).toHaveProperty('consecutiveEmptyPolls');
      expect(stats).toHaveProperty('consecutiveErrors');
      expect(stats).toHaveProperty('timeSinceLastActivity');
      expect(stats).toHaveProperty('isIdle');
      expect(stats).toHaveProperty('isActive');
    });

    it('devrait formater l\'intervalle en secondes', () => {
      const stats = poller.getStats();

      expect(stats.currentIntervalFormatted).toBe('5s');
    });

    it('devrait calculer le temps depuis la dernière activité', () => {
      const stats = poller.getStats();

      expect(stats.timeSinceLastActivity).toBeGreaterThanOrEqual(0);
    });
  });

  describe('isIdle()', () => {
    it('devrait retourner true quand l\'intervalle est au maximum', () => {
      for (let i = 0; i < 20; i++) {
        poller.onNoTask();
      }

      expect(poller.isIdle()).toBe(true);
    });

    it('devrait retourner false quand l\'intervalle n\'est pas au maximum', () => {
      poller.onNoTask();

      expect(poller.isIdle()).toBe(false);
    });
  });

  describe('isActive()', () => {
    it('devrait retourner true quand l\'intervalle est au minimum', () => {
      expect(poller.isActive()).toBe(true);
    });

    it('devrait retourner false quand l\'intervalle n\'est pas au minimum', () => {
      poller.onNoTask();

      expect(poller.isActive()).toBe(false);
    });
  });

  describe('Configuration personnalisée', () => {
    it('devrait respecter un minInterval personnalisé', () => {
      const customPoller = new AdaptivePoller({
        minInterval: 10000,
        maxInterval: 60000,
        backoffMultiplier: 2,
        resetOnActivity: true
      });

      expect(customPoller.getCurrentInterval()).toBe(10000);
    });

    it('devrait respecter un maxInterval personnalisé', () => {
      const customPoller = new AdaptivePoller({
        minInterval: 5000,
        maxInterval: 30000,
        backoffMultiplier: 2,
        resetOnActivity: true
      });

      for (let i = 0; i < 20; i++) {
        customPoller.onNoTask();
      }

      expect(customPoller.getCurrentInterval()).toBe(30000);
    });

    it('devrait respecter un backoffMultiplier personnalisé', () => {
      const customPoller = new AdaptivePoller({
        minInterval: 5000,
        maxInterval: 60000,
        backoffMultiplier: 2,
        resetOnActivity: true
      });

      const interval1 = customPoller.getCurrentInterval(); // 5000
      customPoller.onNoTask();
      const interval2 = customPoller.getCurrentInterval(); // 10000

      expect(interval2).toBe(interval1 * 2);
    });

    it('devrait respecter resetOnActivity=false', () => {
      const customPoller = new AdaptivePoller({
        minInterval: 5000,
        maxInterval: 60000,
        backoffMultiplier: 1.5,
        resetOnActivity: false
      });

      // Augmenter l'intervalle
      customPoller.onNoTask();
      const intervalBefore = customPoller.getCurrentInterval();

      // Trouver une tâche ne devrait pas reset
      customPoller.onTaskFound();
      const intervalAfter = customPoller.getCurrentInterval();

      expect(intervalAfter).toBe(intervalBefore);
    });
  });
});
