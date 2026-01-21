/**
 * Classes d'Erreur Standardisées
 *
 * Hiérarchie d'erreurs pour une gestion cohérente dans tout le plugin.
 * Chaque erreur a une catégorie et un flag isRetryable pour guider le handling.
 */

// ===== ERROR CATEGORIES =====

export type ErrorCategory = 'network' | 'auth' | 'vinted' | 'validation' | 'config' | 'task' | 'unknown';

/**
 * Classe de base pour toutes les erreurs Stoflow
 */
export class StoflowError extends Error {
  public readonly category: ErrorCategory;
  public readonly isRetryable: boolean;
  public readonly timestamp: Date;

  constructor(
    message: string,
    public code: string,
    public userMessage?: string,
    public details?: any,
    category: ErrorCategory = 'unknown',
    isRetryable: boolean = false
  ) {
    super(message);
    this.name = 'StoflowError';
    this.category = category;
    this.isRetryable = isRetryable;
    this.timestamp = new Date();

    // Maintenir la stack trace correcte
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, this.constructor);
    }
  }

  /**
   * Retourne un message user-friendly
   */
  getUserMessage(): string {
    return this.userMessage || this.message;
  }

  /**
   * Sérialise l'erreur pour logging/transport
   */
  toJSON(): Record<string, any> {
    return {
      name: this.name,
      message: this.message,
      code: this.code,
      category: this.category,
      isRetryable: this.isRetryable,
      userMessage: this.userMessage,
      details: this.details,
      timestamp: this.timestamp.toISOString()
    };
  }
}
