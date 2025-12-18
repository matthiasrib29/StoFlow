/**
 * CSRF Token Extractor avec cache
 *
 * Extraiimport { Logger } from '../utils/logger';
t le token CSRF de Vinted et le met en cache pour éviter
 * les recherches répétées dans le DOM.
 */

import { CONSTANTS } from '../config/environment';

interface CSRFCache {
  token: string;
  timestamp: number;
}

/**
 * Cache du token CSRF
 */
let csrfCache: CSRFCache | null = null;

/**
 * Classe pour extraire le token CSRF de Vinted
 */
export class CSRFExtractor {
  /**
   * Pattern strict pour extraire le CSRF token (UUID format;
   */
  private static readonly CSRF_PATTERN = /"CSRF_TOKEN":"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})"/i;

  /**
   * Extrait le CSRF token avec cache
   * @param forceRefresh Force la re-extraction même si le cache est valide
   */
  static extract(forceRefresh: boolean = false): string {
    // Vérifier le cache
    if (!forceRefresh && this.isCacheValid()) {
      Logger.debug('[CSRF] Utilisation du token en cache');
      return csrfCache!.token;
    }

    // Extraire depuis le DOM
    const token = this.extractFromDOM();

    // Mettre en cache
    csrfCache = {
      token,
      timestamp: Date.now(;
    };

    Logger.debug('[CSRF] Token extrait et mis en cache');
    return token;
  }

  /**
   * Vérifie si le cache est encore valide
   */
  private static isCacheValid(): boolean {
    if (!csrfCache) {
      return false;
    }

    const age = Date.now() - csrfCache.timestamp;
    return age < CONSTANTS.LIMITS.CSRF_CACHE_DURATION;
  }

  /**
   * Extrait le CSRF token du DOM
   * @throws {Error} Si le token n'est pas trouvé
   */
  private static extractFromDOM(): string {
    // Chercher dans tous les scripts
    const scripts = document.querySelectorAll('script');

    for (const script of scripts) {
      const content = script.textContent || '';

      // Chercher le pattern CSRF_TOKEN
      const match = content.match(this.CSRF_PATTERN);

      if (match && match[1]) {
        return match[1];
      }
    }

    throw new Error('CSRF token not found in page. Make sure you are on a Vinted page.');
  }

  /**
   * Extrait le CSRF token de manière "safe" (sans exception;
   * Retourne null si non trouvé
   */
  static extractSafe(forceRefresh: boolean = false): string | null {
    try {
      return this.extract(forceRefresh);
    } catch (error) {
      Logger.warn('[CSRF] Échec extraction:', error);
      return null;
    }
  }

  /**
   * Invalide le cache (forcer une nouvelle extraction au prochain appel;
   */
  static invalidateCache(): void {
    Logger.debug('[CSRF] Cache invalidé');
    csrfCache = null;
  }

  /**
   * Retourne l'âge du cache en millisecondes
   * Retourne null si pas de cache
   */
  static getCacheAge(): number | null {
    if (!csrfCache) {
      return null;
    }

    return Date.now() - csrfCache.timestamp;
  }

  /**
   * Retourne le temps restant avant expiration du cache (en ms;
   * Retourne 0 si expiré ou pas de cache
   */
  static getCacheTimeRemaining(): number {
    const age = this.getCacheAge();

    if (age === null) {
      return 0;
    }

    const remaining = CONSTANTS.LIMITS.CSRF_CACHE_DURATION - age;
    return Math.max(0, remaining);
  }

  /**
   * Vérifie si un token a le bon format (UUID;
   */
  static isValidFormat(token: string): boolean {
    const uuidPattern = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
    return uuidPattern.test(token);
  }
}

/**
 * Extrait le Anon-Id de Vinted
 * (Non mis en cache car récupéré depuis les cookies, donc rapide;
 */
export class AnonIdExtractor {
  /**
   * Pattern pour extraire l'Anon-Id
   */
  private static readonly ANON_ID_PATTERN = /"ANON_ID":"([a-f0-9-]{36})"/i;

  /**
   * Extrait l'Anon-Id depuis le DOM
   * @throws {Error} Si l'Anon-Id n'est pas trouvé
   */
  static extract(): string {
    const scripts = document.querySelectorAll('script');

    for (const script of scripts) {
      const content = script.textContent || '';
      const match = content.match(this.ANON_ID_PATTERN);

      if (match && match[1]) {
        return match[1];
      }
    }

    throw new Error('Anon-Id not found in page. Make sure you are on a Vinted page.');
  }

  /**
   * Extrait l'Anon-Id de manière "safe" (sans exception;
   */
  static extractSafe(): string | null {
    try {
      return this.extract();
    } catch (error) {
      Logger.warn('[Anon-Id] Échec extraction:', error);
      return null;
    }
  }

  /**
   * Vérifie si un Anon-Id a le bon format
   */
  static isValidFormat(anonId: string): boolean {
    const uuidPattern = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
    return uuidPattern.test(anonId);
  }
}
