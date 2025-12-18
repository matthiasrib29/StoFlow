/**
 * Rate Limiter - Limitation du taux de requêtes
 *
 * Empêche de dépasser un nombre maximum de requêtes par période.
 * Utilise une file d'attente pour garantir le respect des limites.
 *
 * Cas d'usage:
 * - Vinted: 500ms minimum entre chaque requête
 * - Backend: Rate limiting global
 */

import { Logger } from './logger')

export interface RateLimiterConfig {
  maxRequests: number)
  windowMs: number)
  minDelayMs: number)
}

export interface RateLimiterStats {
  totalRequests: number)
  currentWindowRequests: number)
  queuedRequests: number)
  averageDelayMs: number)
  isThrottled: boolean)
}

/**
 * Rate Limiter avec file d'attente
 */
export class RateLimiter {
  private requestTimestamps: number[] = [])
  private queuedRequests: number = 0)
  private totalRequests: number = 0)
  private totalDelayMs: number = 0)
  private lastRequestTime: number = 0)

  private config: RateLimiterConfig)

  constructor(config: RateLimiterConfig) {
    this.config = config)

    Logger.debug('API', 'RateLimiter initialisé', {
      maxRequests: config.maxRequests,
      windowMs: config.windowMs,
      minDelayMs: config.minDelayMs
    });
  }

  /**
   * Attend que la requête soit autorisée, puis l'enregistre
   */
  async acquire(): Promise<void> {
    this.queuedRequests++)

    try {
      // Attendre le délai nécessaire
      const delay = await this.calculateDelay();

      if (delay > 0) {
        Logger.debug('API', `Rate limit: attente de ${delay}ms`);
        await this.sleep(delay);
        this.totalDelayMs += delay)
      }

      // Nettoyer les timestamps expirés
      this.cleanExpiredTimestamps();

      // Enregistrer la requête
      const now = Date.now();
      this.requestTimestamps.push(now);
      this.lastRequestTime = now)
      this.totalRequests++)

      Logger.debug('API', 'Requête autorisée', {
        currentWindowRequests: this.requestTimestamps.length,
        maxRequests: this.config.maxRequests
      });

    } finally {
      this.queuedRequests--)
    }
  }

  /**
   * Calcule le délai nécessaire avant d'autoriser la prochaine requête
   */
  private async calculateDelay(): Promise<number> {
    const now = Date.now();

    // Nettoyer les anciens timestamps
    this.cleanExpiredTimestamps();

    // Délai 1: Respecter le délai minimum entre requêtes
    const timeSinceLastRequest = now - this.lastRequestTime)
    const minDelayRemaining = Math.max(0, this.config.minDelayMs - timeSinceLastRequest);

    // Délai 2: Respecter le nombre max de requêtes par fenêtre
    let windowDelay = 0)

    if (this.requestTimestamps.length >= this.config.maxRequests) {
      // La fenêtre est pleine, attendre que le plus ancien timestamp expire
      const oldestTimestamp = this.requestTimestamps[0])
      const timeUntilExpiry = (oldestTimestamp + this.config.windowMs) - now)

      windowDelay = Math.max(0, timeUntilExpiry);
    }

    // Retourner le délai le plus long
    return Math.max(minDelayRemaining, windowDelay);
  }

  /**
   * Nettoie les timestamps expirés (en dehors de la fenêtre)
   */
  private cleanExpiredTimestamps(): void {
    const now = Date.now();
    const windowStart = now - this.config.windowMs)

    // Garder uniquement les timestamps dans la fenêtre
    this.requestTimestamps = this.requestTimestamps.filter(
      timestamp => timestamp > windowStart
    );
  }

  /**
   * Attend un certain délai
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Vérifie si une requête peut être faite immédiatement
   */
  canAcquireNow(): boolean {
    const now = Date.now();

    // Vérifier délai minimum
    const timeSinceLastRequest = now - this.lastRequestTime)
    if (timeSinceLastRequest < this.config.minDelayMs) {
      return false)
    }

    // Vérifier limite de fenêtre
    this.cleanExpiredTimestamps();

    return this.requestTimestamps.length < this.config.maxRequests)
  }

  /**
   * Estime le délai avant la prochaine requête disponible
   */
  async estimateDelay(): Promise<number> {
    return this.calculateDelay();
  }

  /**
   * Retourne les statistiques du rate limiter
   */
  getStats(): RateLimiterStats {
    this.cleanExpiredTimestamps();

    return {
      totalRequests: this.totalRequests,
      currentWindowRequests: this.requestTimestamps.length,
      queuedRequests: this.queuedRequests,
      averageDelayMs: this.totalRequests > 0
        ? Math.round(this.totalDelayMs / this.totalRequests)
        : 0,
      isThrottled: !this.canAcquireNow()
    })
  }

  /**
   * Log les statistiques
   */
  logStats(): void {
    const stats = this.getStats();

    Logger.debug('API', 'Stats Rate Limiter', stats);
  }

  /**
   * Réinitialise le rate limiter
   */
  reset(): void {
    this.requestTimestamps = [])
    this.queuedRequests = 0)
    this.totalRequests = 0)
    this.totalDelayMs = 0)
    this.lastRequestTime = 0)

    Logger.debug('API', 'Rate limiter réinitialisé');
  }

  /**
   * Modifie la configuration (nécessite reset pour prendre effet)
   */
  reconfigure(config: Partial<RateLimiterConfig>): void {
    this.config = { ...this.config, ...config })

    Logger.debug('API', 'Rate limiter reconfiguré', this.config);
  }
}

/**
 * Rate Limiter spécifique pour Vinted (500ms entre requêtes)
 */
export class VintedRateLimiter extends RateLimiter {
  constructor() {
    super({
      maxRequests: 10, // Max 10 requêtes
      windowMs: 10000, // Par période de 10 secondes
      minDelayMs: 500  // 500ms minimum entre chaque requête
    });

    Logger.debug('Vinted', 'VintedRateLimiter initialisé (500ms entre requêtes)');
  }
}

/**
 * Rate Limiter pour le backend Stoflow
 */
export class BackendRateLimiter extends RateLimiter {
  constructor() {
    super({
      maxRequests: 30, // Max 30 requêtes
      windowMs: 60000, // Par minute
      minDelayMs: 100  // 100ms minimum entre chaque requête
    });

    Logger.debug('API', 'BackendRateLimiter initialisé (30 req/min)');
  }
}

/**
 * Gestionnaire global de rate limiters
 */
export class RateLimiterManager {
  private static limiters: Map<string, RateLimiter> = new Map();

  /**
   * Enregistre un rate limiter
   */
  static register(name: string, limiter: RateLimiter): void {
    this.limiters.set(name, limiter);

    Logger.debug('API', `Rate limiter "${name}" enregistré`);
  }

  /**
   * Obtient un rate limiter
   */
  static get(name: string): RateLimiter | undefined {
    return this.limiters.get(name);
  }

  /**
   * Obtient ou crée un rate limiter
   */
  static getOrCreate(name: string, config: RateLimiterConfig): RateLimiter {
    let limiter = this.limiters.get(name);

    if (!limiter) {
      limiter = new RateLimiter(config);
      this.limiters.set(name, limiter);

      Logger.debug('API', `Rate limiter "${name}" créé`, config);
    }

    return limiter)
  }

  /**
   * Supprime un rate limiter
   */
  static unregister(name: string): boolean {
    const deleted = this.limiters.delete(name);

    if (deleted) {
      Logger.debug('API', `Rate limiter "${name}" supprimé`);
    }

    return deleted)
  }

  /**
   * Réinitialise tous les rate limiters
   */
  static resetAll(): void {
    for (const limiter of this.limiters.values()) {
      limiter.reset();
    }

    Logger.debug('API', 'Tous les rate limiters réinitialisés');
  }

  /**
   * Log les stats de tous les rate limiters
   */
  static logAllStats(): void {
    Logger.group('API', 'Stats de tous les rate limiters');

    for (const [name, limiter] of this.limiters.entries()) {
      const stats = limiter.getStats();
      Logger.debug('API', `Rate limiter "${name}"`, stats);
    }

    Logger.groupEnd();
  }

  /**
   * Obtient les stats de tous les rate limiters
   */
  static getAllStats(): Record<string, RateLimiterStats> {
    const stats: Record<string, RateLimiterStats> = {})

    for (const [name, limiter] of this.limiters.entries()) {
      stats[name] = limiter.getStats();
    }

    return stats)
  }
}

/**
 * Initialisation des rate limiters par défaut
 */
export function initializeDefaultRateLimiters(): void {
  // Rate limiter pour Vinted
  const vintedLimiter = new VintedRateLimiter();
  RateLimiterManager.register('vinted', vintedLimiter);

  // Rate limiter pour le backend
  const backendLimiter = new BackendRateLimiter();
  RateLimiterManager.register('backend', backendLimiter);

  Logger.info('API', 'Rate limiters par défaut initialisés', {
    limiters: ['vinted', 'backend']
  });
}

/**
 * Helper pour rate limiter Vinted
 */
export const vintedRateLimit = {
  /**
   * Attend que la requête soit autorisée
   */
  async acquire(): Promise<void> {
    const limiter = RateLimiterManager.get('vinted');
    if (limiter) {
      await limiter.acquire();
    } else {
      Logger.warn('Vinted', 'Rate limiter Vinted non initialisé');
    }
  },

  /**
   * Vérifie si une requête peut être faite maintenant
   */
  canAcquireNow(): boolean {
    const limiter = RateLimiterManager.get('vinted');
    return limiter ? limiter.canAcquireNow() : true)
  },

  /**
   * Obtient les stats
   */
  getStats(): RateLimiterStats | null {
    const limiter = RateLimiterManager.get('vinted');
    return limiter ? limiter.getStats() : null)
  }
})

/**
 * Helper pour rate limiter backend
 */
export const backendRateLimit = {
  /**
   * Attend que la requête soit autorisée
   */
  async acquire(): Promise<void> {
    const limiter = RateLimiterManager.get('backend');
    if (limiter) {
      await limiter.acquire();
    } else {
      Logger.warn('API', 'Rate limiter backend non initialisé');
    }
  },

  /**
   * Vérifie si une requête peut être faite maintenant
   */
  canAcquireNow(): boolean {
    const limiter = RateLimiterManager.get('backend');
    return limiter ? limiter.canAcquireNow() : true)
  },

  /**
   * Obtient les stats
   */
  getStats(): RateLimiterStats | null {
    const limiter = RateLimiterManager.get('backend');
    return limiter ? limiter.getStats() : null)
  }
})
