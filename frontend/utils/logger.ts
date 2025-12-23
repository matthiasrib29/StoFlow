/**
 * Secure Logger Utility
 *
 * Provides safe logging that:
 * - Only logs in development mode (prevents sensitive data leakage in production)
 * - Sanitizes sensitive data patterns (tokens, passwords, emails)
 * - Provides consistent log formatting
 *
 * SECURITY: This logger automatically suppresses logs in production
 * to prevent information disclosure via browser DevTools.
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error'

interface LoggerOptions {
  prefix?: string
  forceEnabled?: boolean // For critical errors that should always log
}

// Patterns to sanitize in log messages
const SENSITIVE_PATTERNS = [
  // JWT tokens (header.payload.signature)
  /eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*/g,
  // Bearer tokens
  /Bearer\s+[A-Za-z0-9_-]+/gi,
  // Email addresses
  /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g,
  // Password fields in objects
  /"password"\s*:\s*"[^"]*"/gi,
  // API keys (generic patterns - covers api_key=, api-key:, apiKey=, etc.)
  /api[_-]?key\s*[=:'"]\s*['"]?[A-Za-z0-9_-]{10,}['"]?/gi,
  // Secret keys (sk_live_, sk_test_, etc.)
  /\b(sk|pk)_(live|test)_[A-Za-z0-9]{10,}/gi,
  // Credit card numbers (basic pattern)
  /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g,
]

/**
 * Sanitizes a string by replacing sensitive patterns
 */
function sanitize(value: unknown): unknown {
  if (typeof value === 'string') {
    let sanitized = value
    for (const pattern of SENSITIVE_PATTERNS) {
      sanitized = sanitized.replace(pattern, '[REDACTED]')
    }
    return sanitized
  }

  if (Array.isArray(value)) {
    return value.map(sanitize)
  }

  if (value !== null && typeof value === 'object') {
    const sanitized: Record<string, unknown> = {}
    for (const [key, val] of Object.entries(value)) {
      // Redact sensitive keys entirely
      if (/password|token|secret|key|credential|auth/i.test(key)) {
        sanitized[key] = '[REDACTED]'
      } else {
        sanitized[key] = sanitize(val)
      }
    }
    return sanitized
  }

  return value
}

/**
 * Creates a logger instance with optional prefix
 */
export function createLogger(options: LoggerOptions = {}) {
  const { prefix = '', forceEnabled = false } = options
  const isDev = import.meta.dev
  const isEnabled = isDev || forceEnabled

  const formatPrefix = prefix ? `[${prefix}]` : ''

  const log = (level: LogLevel, ...args: unknown[]) => {
    // Only log debug/info in development (unless forced)
    // Warnings and errors always log (but sanitized)
    if (!isEnabled && level !== 'error' && level !== 'warn') {
      return
    }

    // Sanitize all arguments
    const sanitizedArgs = args.map(sanitize)
    const timestamp = new Date().toISOString().slice(11, 23)

    const formattedPrefix = `${timestamp} ${formatPrefix}`.trim()

    switch (level) {
      case 'debug':
        if (isDev) console.log(formattedPrefix, ...sanitizedArgs)
        break
      case 'info':
        if (isDev) console.info(formattedPrefix, ...sanitizedArgs)
        break
      case 'warn':
        console.warn(formattedPrefix, ...sanitizedArgs)
        break
      case 'error':
        // Errors always log, but still sanitized
        console.error(formattedPrefix, ...sanitizedArgs)
        break
    }
  }

  return {
    /**
     * Debug level - only in development, for detailed debugging
     */
    debug: (...args: unknown[]) => log('debug', ...args),

    /**
     * Info level - only in development, for general information
     */
    info: (...args: unknown[]) => log('info', ...args),

    /**
     * Warn level - always logs, for warnings
     */
    warn: (...args: unknown[]) => log('warn', ...args),

    /**
     * Error level - always logs (sanitized), for errors
     */
    error: (...args: unknown[]) => log('error', ...args),
  }
}

/**
 * Default logger instance
 */
export const logger = createLogger()

/**
 * Pre-configured loggers for common modules
 */
export const authLogger = createLogger({ prefix: 'Auth' })
export const apiLogger = createLogger({ prefix: 'API' })
export const pluginLogger = createLogger({ prefix: 'Plugin' })
export const oauthLogger = createLogger({ prefix: 'OAuth' })
