/**
 * Origin Validator - Centralized origin whitelist management
 *
 * This module handles allowed origins validation with environment awareness.
 * In production builds, localhost/development origins are excluded.
 *
 * @author Claude
 * @date 2026-01-19
 */

// ============================================================
// PRODUCTION ORIGINS (always allowed)
// ============================================================

const PRODUCTION_ORIGINS = [
  'https://stoflow.io',
  'https://www.stoflow.io',
  'https://app.stoflow.io'
] as const;

// ============================================================
// DEVELOPMENT ORIGINS (only in dev mode)
// ============================================================

const DEVELOPMENT_ORIGINS = [
  // Dev environments (ports 3000-3003)
  'http://localhost:3000',
  'http://localhost:3001',
  'http://localhost:3002',
  'http://localhost:3003',
  'http://127.0.0.1:3000',
  'http://127.0.0.1:3001',
  'http://127.0.0.1:3002',
  'http://127.0.0.1:3003',
  // Vite HMR
  'http://localhost:5173',
  'http://127.0.0.1:5173'
] as const;

// ============================================================
// ENVIRONMENT DETECTION
// ============================================================

/**
 * Check if we're in development mode.
 * Uses Vite's import.meta.env.DEV or falls back to checking for localhost patterns.
 */
export function isDevelopmentMode(): boolean {
  // Vite provides import.meta.env.DEV in development builds
  if (typeof import.meta !== 'undefined' && import.meta.env) {
    return import.meta.env.DEV === true;
  }

  // Fallback: check if running in a localhost context
  if (typeof window !== 'undefined') {
    const hostname = window.location?.hostname;
    return hostname === 'localhost' || hostname === '127.0.0.1';
  }

  return false;
}

// ============================================================
// ALLOWED ORIGINS
// ============================================================

/**
 * Get the list of allowed origins based on current environment.
 * In production, only production origins are allowed.
 * In development, both production and development origins are allowed.
 */
export function getAllowedOrigins(): string[] {
  const origins = [...PRODUCTION_ORIGINS];

  if (isDevelopmentMode()) {
    origins.push(...DEVELOPMENT_ORIGINS);
  }

  return origins;
}

/**
 * Verify if the sender origin is allowed.
 *
 * SECURITY: Uses strict equality check (includes) instead of startsWith
 * to prevent origin bypass attacks (e.g., stoflow.io.evil.com)
 *
 * @param senderUrl - The URL or origin to validate
 * @returns true if the origin is in the allowed list
 */
export function isAllowedOrigin(senderUrl: string | undefined): boolean {
  if (!senderUrl) {
    console.warn('[Security] Blocked request: no origin provided');
    return false;
  }

  try {
    const origin = new URL(senderUrl).origin;
    const allowedOrigins = getAllowedOrigins();

    // SECURITY: Strict equality check - no startsWith to prevent bypass
    const isValid = allowedOrigins.includes(origin);

    if (!isValid) {
      console.warn('[Security] Blocked unauthorized origin:', origin);
    }

    return isValid;
  } catch (error) {
    console.error('[Security] Invalid URL format:', senderUrl);
    return false;
  }
}

// ============================================================
// EXPORTS
// ============================================================

export {
  PRODUCTION_ORIGINS,
  DEVELOPMENT_ORIGINS
};
