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

// ==================== ERREURS VINTED ====================

/**
 * Erreur quand aucun onglet Vinted n'est ouvert
 */
export class VintedNotFoundError extends StoflowError {
  constructor() {
    super(
      'No Vinted tab found',
      'NO_VINTED_TAB',
      'Veuillez ouvrir vinted.fr dans un onglet',
      undefined,
      'vinted',
      false // Not retryable - user action required
    );
    this.name = 'VintedNotFoundError';
  }
}

/**
 * Erreur lors de l'extraction des tokens Vinted
 */
export class VintedTokenExtractionError extends StoflowError {
  constructor(tokenType: 'CSRF' | 'Anon-Id') {
    super(
      `Failed to extract ${tokenType} from Vinted page`,
      'TOKEN_EXTRACTION_FAILED',
      `Impossible de récupérer le token ${tokenType}. Rechargez la page Vinted.`,
      { tokenType },
      'vinted',
      true // Retryable - page reload might fix it
    );
    this.name = 'VintedTokenExtractionError';
  }
}

/**
 * Erreur lors d'une requête API Vinted
 */
export class VintedAPIError extends StoflowError {
  constructor(
    public statusCode: number,
    public statusText: string,
    public endpoint: string,
    responseData?: any
  ) {
    // 429 = rate limited (retryable), 5xx = server error (retryable), others = not retryable
    const isRetryable = statusCode === 429 || statusCode >= 500;
    super(
      `Vinted API error: ${statusCode} ${statusText} (${endpoint})`,
      'VINTED_API_ERROR',
      `Erreur Vinted (${statusCode}): ${statusText}`,
      { statusCode, statusText, endpoint, responseData },
      'vinted',
      isRetryable
    );
    this.name = 'VintedAPIError';
  }
}

// ==================== ERREURS AUTHENTIFICATION ====================

/**
 * Erreur d'authentification générique
 */
export class AuthenticationError extends StoflowError {
  constructor(message: string, code: string = 'AUTH_ERROR', isRetryable: boolean = false) {
    super(
      message,
      code,
      'Erreur d\'authentification. Veuillez vous reconnecter.',
      undefined,
      'auth',
      isRetryable
    );
    this.name = 'AuthenticationError';
  }
}

/**
 * Token expiré
 */
export class TokenExpiredError extends AuthenticationError {
  constructor() {
    super(
      'Authentication token expired',
      'TOKEN_EXPIRED',
      true // Retryable - token refresh might fix it
    );
    this.name = 'TokenExpiredError';
    this.userMessage = 'Votre session a expiré. Veuillez vous reconnecter.';
  }
}

/**
 * Token invalide
 */
export class InvalidTokenError extends AuthenticationError {
  constructor() {
    super(
      'Invalid authentication token',
      'INVALID_TOKEN',
      false // Not retryable - user must re-authenticate
    );
    this.name = 'InvalidTokenError';
    this.userMessage = 'Token d\'authentification invalide. Veuillez vous reconnecter.';
  }
}

// ==================== ERREURS RÉSEAU ====================

/**
 * Erreur réseau générique
 */
export class NetworkError extends StoflowError {
  constructor(
    message: string,
    public url: string,
    public originalError?: Error
  ) {
    super(
      message,
      'NETWORK_ERROR',
      'Erreur de connexion. Vérifiez votre connexion internet.',
      { url, originalError: originalError?.message },
      'network',
      true // Network errors are generally retryable
    );
    this.name = 'NetworkError';
  }
}

/**
 * Timeout de requête
 */
export class TimeoutError extends NetworkError {
  constructor(url: string, timeoutMs: number) {
    super(
      `Request timeout after ${timeoutMs}ms`,
      url
    );
    this.code = 'TIMEOUT_ERROR';
    this.userMessage = `La requête a pris trop de temps (${timeoutMs / 1000}s). Réessayez.`;
    this.details = { ...this.details, timeoutMs };
    this.name = 'TimeoutError';
    // isRetryable inherited from NetworkError (true)
  }
}

// ==================== ERREURS VALIDATION ====================

/**
 * Erreur de validation générique
 */
export class ValidationError extends StoflowError {
  constructor(message: string, field?: string, value?: any) {
    super(
      message,
      'VALIDATION_ERROR',
      `Donnée invalide${field ? ` pour "${field}"` : ''}`,
      { field, value },
      'validation',
      false // Validation errors are not retryable - data must be fixed
    );
    this.name = 'ValidationError';
  }
}

/**
 * Donnée requise manquante
 */
export class MissingRequiredFieldError extends ValidationError {
  constructor(field: string) {
    super(
      `Required field missing: ${field}`,
      field
    );
    this.code = 'MISSING_REQUIRED_FIELD';
    this.userMessage = `Le champ "${field}" est requis`;
    this.name = 'MissingRequiredFieldError';
    // isRetryable inherited from ValidationError (false)
  }
}

// ==================== ERREURS CONFIGURATION ====================

/**
 * Erreur de configuration
 */
export class ConfigurationError extends StoflowError {
  constructor(message: string, configKey?: string) {
    super(
      message,
      'CONFIGURATION_ERROR',
      'Erreur de configuration du plugin',
      { configKey },
      'config',
      false // Config errors require code/config fix
    );
    this.name = 'ConfigurationError';
  }
}

// ==================== ERREURS TÂCHES ====================

/**
 * Erreur d'exécution de tâche
 */
export class TaskExecutionError extends StoflowError {
  constructor(
    public taskId: number,
    message: string,
    originalError?: Error,
    isRetryable: boolean = true
  ) {
    super(
      `Task ${taskId} execution failed: ${message}`,
      'TASK_EXECUTION_ERROR',
      `Échec de l'exécution de la tâche #${taskId}`,
      { taskId, originalError: originalError?.message },
      'task',
      isRetryable
    );
    this.name = 'TaskExecutionError';
  }
}

// ==================== UTILITAIRES ====================

/**
 * Convertit n'importe quelle erreur en StoflowError
 */
export function toStoflowError(error: unknown): StoflowError {
  // Déjà une StoflowError
  if (error instanceof StoflowError) {
    return error;
  }

  // Error standard
  if (error instanceof Error) {
    return new StoflowError(
      error.message,
      'UNKNOWN_ERROR',
      'Une erreur inattendue s\'est produite',
      { originalError: error.message, stack: error.stack }
    );
  }

  // String
  if (typeof error === 'string') {
    return new StoflowError(
      error,
      'UNKNOWN_ERROR',
      error
    );
  }

  // Autre type
  return new StoflowError(
    'Unknown error occurred',
    'UNKNOWN_ERROR',
    'Une erreur inconnue s\'est produite',
    { error: String(error) }
  );
}

/**
 * Vérifie si une erreur est de type réseau
 */
export function isNetworkError(error: unknown): error is NetworkError {
  return error instanceof NetworkError;
}

/**
 * Vérifie si une erreur est de type authentification
 */
export function isAuthError(error: unknown): error is AuthenticationError {
  return error instanceof AuthenticationError;
}

/**
 * Vérifie si une erreur est de type Vinted
 */
export function isVintedError(error: unknown): error is (VintedNotFoundError | VintedTokenExtractionError | VintedAPIError) {
  return (
    error instanceof VintedNotFoundError ||
    error instanceof VintedTokenExtractionError ||
    error instanceof VintedAPIError
  );
}

/**
 * Vérifie si une erreur est de type validation
 */
export function isValidationError(error: unknown): error is ValidationError {
  return error instanceof ValidationError;
}

/**
 * Vérifie si une erreur est de type task
 */
export function isTaskError(error: unknown): error is TaskExecutionError {
  return error instanceof TaskExecutionError;
}

/**
 * Vérifie si une erreur est retryable
 */
export function isRetryable(error: unknown): boolean {
  if (error instanceof StoflowError) {
    return error.isRetryable;
  }
  return false;
}

/**
 * Retourne la catégorie d'une erreur
 */
export function getErrorCategory(error: unknown): ErrorCategory {
  if (error instanceof StoflowError) {
    return error.category;
  }
  return 'unknown';
}
