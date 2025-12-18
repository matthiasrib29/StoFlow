/**
 * Security Validator - Minimal security checks for task content
 *
 * Only checks for XSS/injection patterns in request content.
 * All other validation (URL, method, domain) is done by the backend.
 */

/**
 * Error thrown when suspicious content is detected
 */
export class SecurityValidationError extends Error {
  constructor(
    message: string,
    public code: string = 'SUSPICIOUS_CONTENT',
    public details?: any
  ) {
    super(message);
    this.name = 'SecurityValidationError';
  }
}

/**
 * Security validator for detecting XSS/injection attempts
 */
export class SecurityValidator {
  /**
   * Patterns that indicate potential XSS or injection attacks
   */
  private static readonly SUSPICIOUS_PATTERNS = [
    /<script[^>]*>[\s\S]*?<\/script>/gi, // Inline scripts
    /javascript:/gi, // javascript: protocol
    /on\w+\s*=/gi, // Event handlers (onclick, onerror, onload, etc.)
    /data:text\/html/gi, // Data URLs with HTML content
  ];

  /**
   * Checks if content contains suspicious patterns (XSS/injection)
   * @throws {SecurityValidationError} If suspicious content is detected
   */
  static checkContent(content: string): void {
    for (const pattern of this.SUSPICIOUS_PATTERNS) {
      // Reset regex lastIndex to avoid issues with global flag
      pattern.lastIndex = 0;

      if (pattern.test(content)) {
        throw new SecurityValidationError(
          'Suspicious content detected (possible XSS/injection)',
          'SUSPICIOUS_CONTENT',
          { matchedPattern: pattern.toString() }
        );
      }
    }
  }

  /**
   * Safe version that returns boolean instead of throwing
   */
  static isSafe(content: string): boolean {
    try {
      this.checkContent(content);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Validates a request body for suspicious content
   * Converts to string if needed before checking
   */
  static validateBody(body: any): void {
    if (!body) return;

    const bodyString = typeof body === 'string' ? body : JSON.stringify(body);
    this.checkContent(bodyString);
  }
}
