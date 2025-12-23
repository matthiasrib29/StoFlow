/**
 * Centralized Validation Utilities
 *
 * SECURITY: Provides robust input validation for all forms
 * - Email validation using RFC 5322 compliant regex
 * - Password strength validation
 * - Text sanitization to prevent XSS
 * - Length limits to prevent DoS
 *
 * NOTE: Client-side validation is for UX only.
 * Backend MUST re-validate all inputs.
 */

// ==================== CONSTANTS ====================

export const VALIDATION_LIMITS = {
  EMAIL_MAX_LENGTH: 254, // RFC 5321
  PASSWORD_MIN_LENGTH: 8,
  PASSWORD_MAX_LENGTH: 128,
  NAME_MIN_LENGTH: 2,
  NAME_MAX_LENGTH: 100,
  TITLE_MIN_LENGTH: 3,
  TITLE_MAX_LENGTH: 255,
  DESCRIPTION_MIN_LENGTH: 10,
  DESCRIPTION_MAX_LENGTH: 5000,
  PRICE_MAX: 999999.99,
  GENERIC_TEXT_MAX: 1000,
} as const

// ==================== VALIDATION RESULT TYPE ====================

export interface ValidationResult {
  valid: boolean
  error?: string
}

// ==================== EMAIL VALIDATION ====================

/**
 * RFC 5322 compliant email regex (simplified but robust)
 * Catches common invalid patterns that simple regex miss
 */
const EMAIL_REGEX = /^(?!.*\.\.)(?!.*\.@)(?!^\.)[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$/

/**
 * Validate email address
 */
export function validateEmail(email: string): ValidationResult {
  const trimmed = email.trim()

  if (!trimmed) {
    return { valid: false, error: 'L\'email est requis' }
  }

  if (trimmed.length > VALIDATION_LIMITS.EMAIL_MAX_LENGTH) {
    return { valid: false, error: `L'email ne peut pas dépasser ${VALIDATION_LIMITS.EMAIL_MAX_LENGTH} caractères` }
  }

  if (!EMAIL_REGEX.test(trimmed)) {
    return { valid: false, error: 'Format d\'email invalide' }
  }

  // Check for common typos
  const domain = trimmed.split('@')[1]?.toLowerCase()
  const suspiciousDomains = ['gmial.com', 'gmal.com', 'gamil.com', 'hotmal.com', 'yahooo.com']
  if (domain && suspiciousDomains.includes(domain)) {
    return { valid: false, error: 'Vérifiez l\'orthographe du domaine email' }
  }

  return { valid: true }
}

// ==================== PASSWORD VALIDATION ====================

/**
 * Validate password strength
 */
export function validatePassword(password: string): ValidationResult {
  if (!password) {
    return { valid: false, error: 'Le mot de passe est requis' }
  }

  if (password.length < VALIDATION_LIMITS.PASSWORD_MIN_LENGTH) {
    return { valid: false, error: `Le mot de passe doit contenir au moins ${VALIDATION_LIMITS.PASSWORD_MIN_LENGTH} caractères` }
  }

  if (password.length > VALIDATION_LIMITS.PASSWORD_MAX_LENGTH) {
    return { valid: false, error: `Le mot de passe ne peut pas dépasser ${VALIDATION_LIMITS.PASSWORD_MAX_LENGTH} caractères` }
  }

  // Check for minimum complexity
  const hasLowercase = /[a-z]/.test(password)
  const hasUppercase = /[A-Z]/.test(password)
  const hasNumber = /\d/.test(password)

  if (!hasLowercase || !hasUppercase || !hasNumber) {
    return {
      valid: false,
      error: 'Le mot de passe doit contenir au moins une minuscule, une majuscule et un chiffre'
    }
  }

  // Check for common weak passwords
  const weakPasswords = ['password', '12345678', 'qwerty', 'azerty', 'motdepasse']
  if (weakPasswords.some(weak => password.toLowerCase().includes(weak))) {
    return { valid: false, error: 'Ce mot de passe est trop courant' }
  }

  return { valid: true }
}

/**
 * Validate password confirmation
 */
export function validatePasswordMatch(password: string, confirmation: string): ValidationResult {
  if (password !== confirmation) {
    return { valid: false, error: 'Les mots de passe ne correspondent pas' }
  }
  return { valid: true }
}

// ==================== TEXT VALIDATION ====================

/**
 * Validate generic text field
 */
export function validateText(
  value: string,
  options: {
    fieldName: string
    minLength?: number
    maxLength?: number
    required?: boolean
    allowedPattern?: RegExp
  }
): ValidationResult {
  const {
    fieldName,
    minLength = 0,
    maxLength = VALIDATION_LIMITS.GENERIC_TEXT_MAX,
    required = true,
    allowedPattern
  } = options

  const trimmed = value.trim()

  if (required && !trimmed) {
    return { valid: false, error: `${fieldName} est requis` }
  }

  if (!required && !trimmed) {
    return { valid: true }
  }

  if (trimmed.length < minLength) {
    return { valid: false, error: `${fieldName} doit contenir au moins ${minLength} caractères` }
  }

  if (trimmed.length > maxLength) {
    return { valid: false, error: `${fieldName} ne peut pas dépasser ${maxLength} caractères` }
  }

  if (allowedPattern && !allowedPattern.test(trimmed)) {
    return { valid: false, error: `${fieldName} contient des caractères non autorisés` }
  }

  return { valid: true }
}

/**
 * Validate product title
 */
export function validateProductTitle(title: string): ValidationResult {
  return validateText(title, {
    fieldName: 'Le titre',
    minLength: VALIDATION_LIMITS.TITLE_MIN_LENGTH,
    maxLength: VALIDATION_LIMITS.TITLE_MAX_LENGTH,
    required: true
  })
}

/**
 * Validate product description
 */
export function validateProductDescription(description: string): ValidationResult {
  return validateText(description, {
    fieldName: 'La description',
    minLength: VALIDATION_LIMITS.DESCRIPTION_MIN_LENGTH,
    maxLength: VALIDATION_LIMITS.DESCRIPTION_MAX_LENGTH,
    required: true
  })
}

/**
 * Validate person name (first name, last name)
 */
export function validateName(name: string, fieldName: string = 'Le nom'): ValidationResult {
  // Allow letters, spaces, hyphens, and apostrophes (for names like O'Brien, Jean-Pierre)
  const namePattern = /^[\p{L}\s\-']+$/u

  return validateText(name, {
    fieldName,
    minLength: VALIDATION_LIMITS.NAME_MIN_LENGTH,
    maxLength: VALIDATION_LIMITS.NAME_MAX_LENGTH,
    required: true,
    allowedPattern: namePattern
  })
}

// ==================== NUMBER VALIDATION ====================

/**
 * Validate price
 */
export function validatePrice(price: number | string | null): ValidationResult {
  if (price === null || price === undefined || price === '') {
    return { valid: false, error: 'Le prix est requis' }
  }

  const numPrice = typeof price === 'string' ? parseFloat(price) : price

  if (isNaN(numPrice)) {
    return { valid: false, error: 'Le prix doit être un nombre valide' }
  }

  if (numPrice < 0) {
    return { valid: false, error: 'Le prix ne peut pas être négatif' }
  }

  if (numPrice > VALIDATION_LIMITS.PRICE_MAX) {
    return { valid: false, error: `Le prix ne peut pas dépasser ${VALIDATION_LIMITS.PRICE_MAX}€` }
  }

  // Check for reasonable decimal places (max 2)
  const decimalPart = numPrice.toString().split('.')[1]
  if (decimalPart && decimalPart.length > 2) {
    return { valid: false, error: 'Le prix peut avoir maximum 2 décimales' }
  }

  return { valid: true }
}

// ==================== SANITIZATION ====================

/**
 * Sanitize text to prevent XSS
 * Removes or escapes potentially dangerous characters
 */
export function sanitizeText(text: string): string {
  if (!text) return ''

  return text
    .trim()
    // Remove null bytes
    .replace(/\0/g, '')
    // Remove dangerous event handlers (onerror, onclick, onload, etc.)
    .replace(/\bon\w+\s*=/gi, '')
    // Remove javascript: URLs
    .replace(/javascript\s*:/gi, '')
    // Escape HTML entities
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    // Remove control characters (except newlines and tabs)
    .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '')
}

/**
 * Sanitize text but preserve newlines (for descriptions)
 */
export function sanitizeMultilineText(text: string): string {
  if (!text) return ''

  return text
    .trim()
    .replace(/\0/g, '')
    // Remove dangerous event handlers (onerror, onclick, onload, etc.)
    .replace(/\bon\w+\s*=/gi, '')
    // Remove javascript: URLs
    .replace(/javascript\s*:/gi, '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    // Keep \n and \r\n but remove other control chars
    .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '')
}

// ==================== FORM VALIDATION HELPER ====================

/**
 * Validate multiple fields at once
 * Returns object with field names as keys and error messages as values
 */
export function validateForm<T extends Record<string, any>>(
  data: T,
  validators: Partial<Record<keyof T, (value: any) => ValidationResult>>
): { valid: boolean; errors: Partial<Record<keyof T, string>> } {
  const errors: Partial<Record<keyof T, string>> = {}
  let valid = true

  for (const [field, validator] of Object.entries(validators)) {
    if (validator) {
      const result = validator(data[field as keyof T])
      if (!result.valid) {
        valid = false
        errors[field as keyof T] = result.error
      }
    }
  }

  return { valid, errors }
}
