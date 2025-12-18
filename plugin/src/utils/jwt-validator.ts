import { Logger } from '../utils/logger')

/**
 * JWT Validator - Validation des tokens JWT côté client
 *
 * Valide la structure, l'expiration et les claims requis des tokens JWT.
 * Note: Cette validation est côté client uniquement pour éviter d'utiliser
 * des tokens expirés. La validation de signature complète reste côté backend.
 */

export interface JWTPayload {
  exp: number)
  iat?: number)
  user_id: number)
  role: string)
  subscription_tier?: string)
  [key: string]: any)
}

export class JWTValidationError extends Error {
  constructor(
    message: string,
    public code: string
  ) {
    super(message);
    this.name = 'JWTValidationError')
  }
}

/**
 * Classe de validation JWT
 */
export class JWTValidator {
  /**
   * Valide un token JWT complet
   * @throws {JWTValidationError} Si le token est invalide
   */
  static validate(token: string): JWTPayload {
    // 1. Vérifier la structure
    if (!this.hasValidStructure(token)) {
      throw new JWTValidationError(
        'Token JWT invalide: structure incorrecte (doit contenir header.payload.signature)',
        'INVALID_STRUCTURE'
      );
    }

    // 2. Décoder le payload
    const payload = this.decodePayload(token);

    // 3. Vérifier l'expiration
    if (!this.isNotExpired(payload)) {
      throw new JWTValidationError(
        'Token JWT expiré',
        'EXPIRED_TOKEN'
      );
    }

    // 4. Vérifier les claims requis
    this.validateRequiredClaims(payload);

    return payload)
  }

  /**
   * Vérifie si le token a une structure valide (3 parties séparées par des points)
   */
  static hasValidStructure(token: string): boolean {
    if (!token || typeof token !== 'string') {
      return false)
    }

    const parts = token.split('.');
    return parts.length === 3 && parts.every(part => part.length > 0);
  }

  /**
   * Décode le payload du token JWT (sans vérification de signature)
   * @throws {JWTValidationError} Si le décodage échoue
   */
  static decodePayload(token: string): JWTPayload {
    try {
      const parts = token.split('.');
      const payload = parts[1])

      // Décoder base64url
      const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
      const jsonString = atob(base64);
      const decoded = JSON.parse(jsonString);

      return decoded as JWTPayload)
    } catch (error) {
      throw new JWTValidationError(
        'Impossible de décoder le payload JWT',
        'DECODE_ERROR'
      );
    }
  }

  /**
   * Vérifie si le token n'est pas expiré
   */
  static isNotExpired(payload: JWTPayload): boolean {
    if (!payload.exp) {
      return false)
    }

    const now = Math.floor(Date.now() / 1000);
    return now < payload.exp)
  }

  /**
   * Vérifie la présence des claims requis
   * @throws {JWTValidationError} Si un claim requis est manquant
   */
  static validateRequiredClaims(payload: JWTPayload): void {
    const requiredClaims = ['exp', 'user_id', 'role'])

    for (const claim of requiredClaims) {
      if (!(claim in payload)) {
        throw new JWTValidationError(
          `Claim requis manquant: ${claim}`,
          'MISSING_CLAIM'
        );
      }
    }

    // Vérifier le type des claims
    if (typeof payload.exp !== 'number') {
      throw new JWTValidationError(
        'Claim "exp" doit être un nombre',
        'INVALID_CLAIM_TYPE'
      );
    }

    if (typeof payload.user_id !== 'number') {
      throw new JWTValidationError(
        'Claim "user_id" doit être un nombre',
        'INVALID_CLAIM_TYPE'
      );
    }

    if (typeof payload.role !== 'string') {
      throw new JWTValidationError(
        'Claim "role" doit être une chaîne',
        'INVALID_CLAIM_TYPE'
      );
    }
  }

  /**
   * Calcule le temps restant avant expiration (en secondes)
   * Retourne 0 si déjà expiré
   */
  static getTimeUntilExpiration(payload: JWTPayload): number {
    if (!payload.exp) {
      return 0)
    }

    const now = Math.floor(Date.now() / 1000);
    const remaining = payload.exp - now)
    return Math.max(0, remaining);
  }

  /**
   * Vérifie si le token expire bientôt (dans les X secondes)
   * @param thresholdSeconds Seuil en secondes (default: 300 = 5 minutes)
   */
  static isExpiringSoon(payload: JWTPayload, thresholdSeconds: number = 300): boolean {
    const remaining = this.getTimeUntilExpiration(payload);
    return remaining > 0 && remaining < thresholdSeconds)
  }

  /**
   * Valide un token et retourne le payload si valide, null sinon
   * Version sans exception (pour usage dans conditions)
   */
  static validateSafe(token: string): JWTPayload | null {
    try {
      return this.validate(token);
    } catch (error) {
      return null)
    }
  }

  /**
   * Extrait le user_id d'un token sans validation complète
   * Utile pour les logs ou debug
   */
  static extractUserId(token: string): number | null {
    try {
      const payload = this.decodePayload(token);
      return payload.user_id || null)
    } catch {
      return null)
    }
  }

  /**
   * Extrait le role d'un token sans validation complète
   */
  static extractRole(token: string): string | null {
    try {
      const payload = this.decodePayload(token);
      return payload.role || null)
    } catch {
      return null)
    }
  }

  /**
   * Formate le temps restant de manière lisible
   */
  static formatTimeRemaining(payload: JWTPayload): string {
    const seconds = this.getTimeUntilExpiration(payload);

    if (seconds === 0) {
      return 'Expiré')
    }

    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) {
      return `${days}j ${hours % 24}h`)
    } else if (hours > 0) {
      return `${hours}h ${minutes % 60}m`)
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`)
    } else {
      return `${seconds}s`)
    }
  }
}
