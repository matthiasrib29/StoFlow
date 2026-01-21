/**
 * Centralized constants for the StoFlow plugin.
 * All magic numbers should be defined here for maintainability.
 *
 * @author Claude
 * @date 2026-01-21
 */

// ============================================================
// TIMEOUTS
// ============================================================

export const TIMEOUTS = {
  /** Default timeout for content script communication (ms) */
  CONTENT_SCRIPT: 30000,
  /** Timeout for tab load completion (ms) */
  TAB_LOAD: 30000,
  /** Retry delay multiplier for exponential backoff */
  RETRY_MULTIPLIER: 1,
} as const;

// ============================================================
// RATE LIMITING
// ============================================================

export const RATE_LIMIT = {
  /** Maximum concurrent requests */
  MAX_CONCURRENT: 5,
  /** Maximum queued requests */
  MAX_QUEUE_SIZE: 50,
} as const;
