/**
 * Logger Professionnel - Système de loggimport { Logger } from '../utils/logger';
ing centralisé
 *
 * Remplace les 433 console.log par un système structuré avec:
 * - Niveaux de log (DEBUG, INFO, WARN, ERROR)
 * - Désactivable en production
 * - Format cohérent
 * - Contextes multiples (Background, Content, Popup)
 */

import { ENV } from '../config/environment';

/**
 * Niveaux de log
 */
export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
  NONE = 4
}

/**
 * Contextes d'exécution
 */
export type LogContext =
  | 'Background'
  | 'Content'
  | 'Popup'
  | 'Auth'
  | 'TaskPoller'
  | 'Proxy'
  | 'Vinted'
  | 'API';

/**
 * Configuration du logger
 */
interface LoggerConfig {
  level: LogLevel;
  enableColors: boolean;
  enableTimestamps: boolean;
  enableContext: boolean;
}

/**
 * Patterns de données sensibles à masquer
 */
const SENSITIVE_PATTERNS = {
  // JWT tokens (eyJ...)
  jwt: /eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g,
  // Bearer tokens
  bearer: /Bearer\s+[A-Za-z0-9_-]+/gi,
  // Generic tokens (32+ chars alphanumeric)
  genericToken: /[a-f0-9]{32,}/gi,
};

/**
 * Clés de champs sensibles (case insensitive)
 */
const SENSITIVE_KEYS = [
  'token', 'access_token', 'refresh_token', 'accessToken', 'refreshToken',
  'password', 'secret', 'api_key', 'apiKey', 'authorization',
  'csrf', 'csrfToken', 'csrf_token', 'session', 'cookie'
];

/**
 * Masque une valeur sensible en gardant les premiers/derniers caractères
 */
function maskSensitiveValue(value: string): string {
  if (value.length <= 10) {
    return '***MASKED***';
  }
  // Garder les 4 premiers et 4 derniers caractères
  return `${value.substring(0, 4)}...${value.substring(value.length - 4)}[MASKED]`;
}

/**
 * Sanitize une chaîne en masquant les patterns sensibles
 */
function sanitizeString(str: string): string {
  let result = str;

  // Masquer les JWT tokens
  result = result.replace(SENSITIVE_PATTERNS.jwt, (match) => maskSensitiveValue(match));

  // Masquer les Bearer tokens
  result = result.replace(SENSITIVE_PATTERNS.bearer, 'Bearer ***MASKED***');

  return result;
}

/**
 * Sanitize récursivement un objet/valeur pour masquer les données sensibles
 */
function sanitizeValue(value: any, depth: number = 0): any {
  // Éviter la récursion infinie
  if (depth > 5) return '[MAX_DEPTH]';

  // Null/undefined
  if (value === null || value === undefined) return value;

  // String: chercher les patterns sensibles
  if (typeof value === 'string') {
    return sanitizeString(value);
  }

  // Number/boolean: retourner tel quel
  if (typeof value === 'number' || typeof value === 'boolean') {
    return value;
  }

  // Array: sanitize chaque élément
  if (Array.isArray(value)) {
    return value.map(item => sanitizeValue(item, depth + 1));
  }

  // Object: sanitize chaque propriété
  if (typeof value === 'object') {
    const sanitized: Record<string, any> = {};

    for (const [key, val] of Object.entries(value)) {
      // Vérifier si la clé est sensible
      const isSensitiveKey = SENSITIVE_KEYS.some(
        sensitiveKey => key.toLowerCase().includes(sensitiveKey.toLowerCase())
      );

      if (isSensitiveKey && typeof val === 'string') {
        sanitized[key] = maskSensitiveValue(val);
      } else {
        sanitized[key] = sanitizeValue(val, depth + 1);
      }
    }

    return sanitized;
  }

  // Fonction ou autre: retourner une représentation
  return String(value);
}

/**
 * Logger centralisé
 */
export class Logger {
  private static config: LoggerConfig = {
    level: ENV.ENABLE_DEBUG_LOGS ? LogLevel.DEBUG : LogLevel.WARN,
    enableColors: true,
    enableTimestamps: true,
    enableContext: true
  };

  /**
   * Configure le logger
   */
  static configure(config: Partial<LoggerConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Définit le niveau de log minimum
   */
  static setLevel(level: LogLevel): void {
    this.config.level = level;
  }

  /**
   * Log niveau DEBUG (développement uniquement)
   */
  static debug(context: LogContext, message: string, ...args: any[]): void {
    if (this.config.level <= LogLevel.DEBUG) {
      this.log('DEBUG', context, message, args, console.log, '🔍');
    }
  }

  /**
   * Log niveau INFO (informations importantes)
   */
  static info(context: LogContext, message: string, ...args: any[]): void {
    if (this.config.level <= LogLevel.INFO) {
      this.log('INFO', context, message, args, console.log, 'ℹ️');
    }
  }

  /**
   * Log niveau WARN (avertissements)
   */
  static warn(context: LogContext, message: string, ...args: any[]): void {
    if (this.config.level <= LogLevel.WARN) {
      this.log('WARN', context, message, args, console.warn, '⚠️');
    }
  }

  /**
   * Log niveau ERROR (erreurs)
   */
  static error(context: LogContext, message: string, error?: Error | any, ...args: any[]): void {
    if (this.config.level <= LogLevel.ERROR) {
      const errorArgs = error ? [error, ...args] : args;
      this.log('ERROR', context, message, errorArgs, console.error, '❌');
    }
  }

  /**
   * Log de succès (toujours affiché)
   */
  static success(context: LogContext, message: string, ...args: any[]): void {
    if (this.config.level <= LogLevel.INFO) {
      this.log('SUCCESS', context, message, args, console.log, '✅');
    }
  }

  /**
   * Groupe de logs (pour regrouper des logs liés)
   */
  static group(context: LogContext, title: string): void {
    if (this.config.level <= LogLevel.INFO) {
      const formatted = this.formatPrefix('GROUP', context, '📦');
      console.group(`${formatted} ${title}`);
    }
  }

  /**
   * Fin du groupe de logs
   */
  static groupEnd(): void {
    if (this.config.level <= LogLevel.INFO) {
      console.groupEnd();
    }
  }

  /**
   * Log avec table (pour afficher des objets structurés)
   */
  static table(context: LogContext, label: string, data: any): void {
    if (this.config.level <= LogLevel.DEBUG) {
      const formatted = this.formatPrefix('TABLE', context, '📊');
      Logger.debug(`${formatted} ${label}`);
      console.table(data);
    }
  }

  /**
   * Log de temps d'exécution
   */
  static time(context: LogContext, label: string): void {
    if (this.config.level <= LogLevel.DEBUG) {
      const formatted = this.formatPrefix('TIME', context, '⏱️');
      console.time(`${formatted} ${label}`);
    }
  }

  /**
   * Fin du log de temps
   */
  static timeEnd(context: LogContext, label: string): void {
    if (this.config.level <= LogLevel.DEBUG) {
      const formatted = this.formatPrefix('TIME', context, '⏱️');
      console.timeEnd(`${formatted} ${label}`);
    }
  }

  /**
   * Fonction de log interne
   * Sanitize automatiquement les données sensibles (tokens, passwords, etc.)
   */
  private static log(
    level: string,
    context: LogContext,
    message: string,
    args: any[],
    logFn: (...args: any[]) => void,
    icon: string
  ): void {
    const prefix = this.formatPrefix(level, context, icon);

    // Sanitize le message et les arguments pour masquer les données sensibles
    const sanitizedMessage = sanitizeString(message);
    const sanitizedArgs = args.map(arg => sanitizeValue(arg));

    const formattedMessage = `${prefix} ${sanitizedMessage}`;

    if (sanitizedArgs.length > 0) {
      logFn(formattedMessage, ...sanitizedArgs);
    } else {
      logFn(formattedMessage);
    }
  }

  /**
   * Formate le préfixe du log
   */
  private static formatPrefix(level: string, context: LogContext, icon: string): string {
    const parts: string[] = [];

    // Timestamp (optionnel)
    if (this.config.enableTimestamps) {
      const now = new Date();
      const time = now.toLocaleTimeString('fr-FR', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        fractionalSecondDigits: 3
      });
      parts.push(`[${time}]`);
    }

    // Contexte (optionnel)
    if (this.config.enableContext) {
      parts.push(`[${context}]`);
    }

    // Niveau + icône
    parts.push(`${icon} ${level}:`);

    return parts.join(' ');
  }

  /**
   * Désactive tous les logs (production)
   */
  static silence(): void {
    this.config.level = LogLevel.NONE;
  }

  /**
   * Réactive les logs
   */
  static unsilence(): void {
    this.config.level = ENV.ENABLE_DEBUG_LOGS ? LogLevel.DEBUG : LogLevel.WARN;
  }
}

/**
 * Loggers spécialisés par contexte (pour simplifier l'usage)
 */
export const BackgroundLogger = {
  debug: (msg: string, ...args: any[]) => Logger.debug('Background', msg, ...args),
  info: (msg: string, ...args: any[]) => Logger.info('Background', msg, ...args),
  warn: (msg: string, ...args: any[]) => Logger.warn('Background', msg, ...args),
  error: (msg: string, error?: Error, ...args: any[]) => Logger.error('Background', msg, error, ...args),
  success: (msg: string, ...args: any[]) => Logger.success('Background', msg, ...args),
  group: (title: string) => Logger.group('Background', title),
  groupEnd: () => Logger.groupEnd()
};

export const ContentLogger = {
  debug: (msg: string, ...args: any[]) => Logger.debug('Content', msg, ...args),
  info: (msg: string, ...args: any[]) => Logger.info('Content', msg, ...args),
  warn: (msg: string, ...args: any[]) => Logger.warn('Content', msg, ...args),
  error: (msg: string, error?: Error, ...args: any[]) => Logger.error('Content', msg, error, ...args),
  success: (msg: string, ...args: any[]) => Logger.success('Content', msg, ...args)
};

export const PopupLogger = {
  debug: (msg: string, ...args: any[]) => Logger.debug('Popup', msg, ...args),
  info: (msg: string, ...args: any[]) => Logger.info('Popup', msg, ...args),
  warn: (msg: string, ...args: any[]) => Logger.warn('Popup', msg, ...args),
  error: (msg: string, error?: Error, ...args: any[]) => Logger.error('Popup', msg, error, ...args),
  success: (msg: string, ...args: any[]) => Logger.success('Popup', msg, ...args)
};

export const AuthLogger = {
  debug: (msg: string, ...args: any[]) => Logger.debug('Auth', msg, ...args),
  info: (msg: string, ...args: any[]) => Logger.info('Auth', msg, ...args),
  warn: (msg: string, ...args: any[]) => Logger.warn('Auth', msg, ...args),
  error: (msg: string, error?: Error, ...args: any[]) => Logger.error('Auth', msg, error, ...args),
  success: (msg: string, ...args: any[]) => Logger.success('Auth', msg, ...args)
};

export const TaskPollerLogger = {
  debug: (msg: string, ...args: any[]) => Logger.debug('TaskPoller', msg, ...args),
  info: (msg: string, ...args: any[]) => Logger.info('TaskPoller', msg, ...args),
  warn: (msg: string, ...args: any[]) => Logger.warn('TaskPoller', msg, ...args),
  error: (msg: string, error?: Error, ...args: any[]) => Logger.error('TaskPoller', msg, error, ...args),
  success: (msg: string, ...args: any[]) => Logger.success('TaskPoller', msg, ...args),
  time: (label: string) => Logger.time('TaskPoller', label),
  timeEnd: (label: string) => Logger.timeEnd('TaskPoller', label)
};

export const ProxyLogger = {
  debug: (msg: string, ...args: any[]) => Logger.debug('Proxy', msg, ...args),
  info: (msg: string, ...args: any[]) => Logger.info('Proxy', msg, ...args),
  warn: (msg: string, ...args: any[]) => Logger.warn('Proxy', msg, ...args),
  error: (msg: string, error?: Error, ...args: any[]) => Logger.error('Proxy', msg, error, ...args),
  success: (msg: string, ...args: any[]) => Logger.success('Proxy', msg, ...args)
};

export const VintedLogger = {
  debug: (msg: string, ...args: any[]) => Logger.debug('Vinted', msg, ...args),
  info: (msg: string, ...args: any[]) => Logger.info('Vinted', msg, ...args),
  warn: (msg: string, ...args: any[]) => Logger.warn('Vinted', msg, ...args),
  error: (msg: string, error?: Error, ...args: any[]) => Logger.error('Vinted', msg, error, ...args),
  success: (msg: string, ...args: any[]) => Logger.success('Vinted', msg, ...args)
};

export const APILogger = {
  debug: (msg: string, ...args: any[]) => Logger.debug('API', msg, ...args),
  info: (msg: string, ...args: any[]) => Logger.info('API', msg, ...args),
  warn: (msg: string, ...args: any[]) => Logger.warn('API', msg, ...args),
  error: (msg: string, error?: Error, ...args: any[]) => Logger.error('API', msg, error, ...args),
  success: (msg: string, ...args: any[]) => Logger.success('API', msg, ...args)
};
