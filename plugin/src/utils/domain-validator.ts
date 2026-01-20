/**
 * Domain Validator - Endpoint whitelist for Chrome Web Store compliance
 *
 * This module validates that all API calls go through approved endpoints only.
 * Required for Chrome Web Store security compliance.
 *
 * @author Claude
 * @date 2026-01-19
 */

// ============================================================
// ALLOWED ENDPOINTS WHITELIST
// ============================================================

/**
 * Whitelist of allowed Vinted API endpoint prefixes.
 * Only requests matching these patterns will be executed.
 */
const ALLOWED_ENDPOINT_PREFIXES = [
  // User endpoints
  '/users',
  '/user',

  // Product/Item endpoints
  '/items',
  '/item',

  // Photo/Image endpoints
  '/photos',
  '/images',

  // Reference data endpoints
  '/categories',
  '/brands',
  '/colors',
  '/sizes',
  '/materials',
  '/conditions',
  '/countries',

  // Transaction endpoints
  '/transactions',
  '/orders',
  '/payments',
  '/shipments',

  // Messaging endpoints
  '/conversations',
  '/messages',
  '/inbox',

  // Search endpoints
  '/catalog',
  '/search',
  '/feed',

  // Web API endpoints (auth, session)
  '/web/api',

  // Notifications
  '/notifications',

  // Favorites/Wishlist
  '/favorites',
  '/wishlist'
] as const;

/**
 * Whitelist of allowed HTTP methods.
 */
const ALLOWED_HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'] as const;

export type AllowedMethod = (typeof ALLOWED_HTTP_METHODS)[number];

// ============================================================
// VALIDATION FUNCTIONS
// ============================================================

/**
 * Check if an endpoint is in the allowed whitelist.
 *
 * @param endpoint - The API endpoint to validate (e.g., "/items/123")
 * @returns true if the endpoint is allowed, false otherwise
 *
 * @example
 * isEndpointAllowed('/items/123') // true
 * isEndpointAllowed('/users/456/items') // true
 * isEndpointAllowed('/evil/endpoint') // false
 */
export function isEndpointAllowed(endpoint: string): boolean {
  if (!endpoint || typeof endpoint !== 'string') {
    return false;
  }

  // Normalize: ensure endpoint starts with /
  const normalizedEndpoint = endpoint.startsWith('/')
    ? endpoint.toLowerCase()
    : `/${endpoint.toLowerCase()}`;

  // Check if endpoint starts with any allowed prefix
  return ALLOWED_ENDPOINT_PREFIXES.some(prefix =>
    normalizedEndpoint.startsWith(prefix.toLowerCase())
  );
}

/**
 * Check if an HTTP method is allowed.
 *
 * @param method - The HTTP method to validate
 * @returns true if the method is allowed, false otherwise
 */
export function isMethodAllowed(method: string): boolean {
  if (!method || typeof method !== 'string') {
    return false;
  }

  return ALLOWED_HTTP_METHODS.includes(method.toUpperCase() as AllowedMethod);
}

/**
 * Validate both endpoint and method together.
 *
 * @param endpoint - The API endpoint
 * @param method - The HTTP method
 * @returns Validation result with details
 */
export function validateRequest(
  endpoint: string,
  method: string
): { valid: boolean; error?: string; errorCode?: string } {
  // Validate method
  if (!isMethodAllowed(method)) {
    return {
      valid: false,
      error: `HTTP method '${method}' is not allowed. Allowed methods: ${ALLOWED_HTTP_METHODS.join(', ')}`,
      errorCode: 'FORBIDDEN_METHOD'
    };
  }

  // Validate endpoint
  if (!isEndpointAllowed(endpoint)) {
    return {
      valid: false,
      error: `Endpoint '${endpoint}' is not in the allowed whitelist`,
      errorCode: 'FORBIDDEN_ENDPOINT'
    };
  }

  return { valid: true };
}

// ============================================================
// EXPORTS
// ============================================================

export {
  ALLOWED_ENDPOINT_PREFIXES,
  ALLOWED_HTTP_METHODS
};
