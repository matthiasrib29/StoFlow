/**
 * Security Tests for Validation Utilities
 *
 * Tests various attack vectors and edge cases for input validation
 */
import { describe, it, expect } from 'vitest'
import {
  validateEmail,
  validatePassword,
  validateName,
  validateText,
  validatePrice,
  sanitizeText,
  sanitizeMultilineText,
  VALIDATION_LIMITS
} from '../../utils/validation'

describe('Email Validation Security', () => {
  describe('Valid emails', () => {
    it('should accept standard email formats', () => {
      expect(validateEmail('user@example.com').valid).toBe(true)
      expect(validateEmail('user.name@example.com').valid).toBe(true)
      expect(validateEmail('user+tag@example.com').valid).toBe(true)
      expect(validateEmail('user@subdomain.example.com').valid).toBe(true)
    })
  })

  describe('Invalid email formats', () => {
    it('should reject emails without @', () => {
      expect(validateEmail('userexample.com').valid).toBe(false)
    })

    it('should reject emails without domain', () => {
      expect(validateEmail('user@').valid).toBe(false)
      expect(validateEmail('user@.com').valid).toBe(false)
    })

    it('should reject emails with double dots', () => {
      expect(validateEmail('user..name@example.com').valid).toBe(false)
      expect(validateEmail('user@example..com').valid).toBe(false)
    })

    it('should reject emails starting or ending with dot', () => {
      expect(validateEmail('.user@example.com').valid).toBe(false)
      expect(validateEmail('user.@example.com').valid).toBe(false)
    })
  })

  describe('Common typos detection', () => {
    it('should detect common email typos', () => {
      expect(validateEmail('user@gmial.com').valid).toBe(false)
      expect(validateEmail('user@gmal.com').valid).toBe(false)
      expect(validateEmail('user@hotmal.com').valid).toBe(false)
    })
  })

  describe('Length limits', () => {
    it('should reject emails exceeding max length', () => {
      const longEmail = 'a'.repeat(250) + '@example.com'
      expect(validateEmail(longEmail).valid).toBe(false)
    })

    it('should accept emails at max length', () => {
      // RFC 5321 allows 254 characters
      const email = 'a'.repeat(240) + '@example.com'
      if (email.length <= VALIDATION_LIMITS.EMAIL_MAX_LENGTH) {
        expect(validateEmail(email).valid).toBe(true)
      }
    })
  })

  describe('XSS prevention', () => {
    it('should reject emails with script tags', () => {
      expect(validateEmail('<script>@example.com').valid).toBe(false)
      expect(validateEmail('user<script>@example.com').valid).toBe(false)
    })

    it('should reject emails with HTML entities', () => {
      expect(validateEmail('user&lt;@example.com').valid).toBe(false)
    })
  })

  describe('SQL injection prevention', () => {
    it('should reject emails with SQL injection patterns', () => {
      expect(validateEmail("user'; DROP TABLE users;--@example.com").valid).toBe(false)
      expect(validateEmail('user" OR "1"="1@example.com').valid).toBe(false)
    })
  })
})

describe('Password Validation Security', () => {
  describe('Length requirements', () => {
    it('should reject passwords shorter than minimum', () => {
      expect(validatePassword('Abc123!').valid).toBe(false) // 7 chars
    })

    it('should accept passwords meeting minimum length', () => {
      expect(validatePassword('Abcd1234').valid).toBe(true) // 8 chars with complexity
    })

    it('should reject passwords exceeding maximum length', () => {
      const longPassword = 'Aa1' + 'x'.repeat(130)
      expect(validatePassword(longPassword).valid).toBe(false)
    })
  })

  describe('Complexity requirements', () => {
    it('should reject passwords without uppercase', () => {
      expect(validatePassword('abcd12345678').valid).toBe(false)
    })

    it('should reject passwords without lowercase', () => {
      expect(validatePassword('ABCD12345678').valid).toBe(false)
    })

    it('should reject passwords without numbers', () => {
      expect(validatePassword('Abcdefghijk').valid).toBe(false)
    })

    it('should accept passwords meeting all complexity requirements', () => {
      expect(validatePassword('SecurePass123').valid).toBe(true)
    })
  })

  describe('Common weak passwords', () => {
    it('should reject common weak passwords', () => {
      expect(validatePassword('Password123').valid).toBe(false)
      expect(validatePassword('Qwerty123456').valid).toBe(false)
      expect(validatePassword('Azerty123456').valid).toBe(false)
    })
  })

  describe('Empty and null inputs', () => {
    it('should reject empty passwords', () => {
      expect(validatePassword('').valid).toBe(false)
    })
  })
})

describe('Name Validation Security', () => {
  describe('Valid names', () => {
    it('should accept standard names', () => {
      expect(validateName('John').valid).toBe(true)
      expect(validateName('Jean-Pierre').valid).toBe(true)
      expect(validateName("O'Brien").valid).toBe(true)
      expect(validateName('María García').valid).toBe(true)
    })

    it('should accept Unicode names', () => {
      expect(validateName('日本語').valid).toBe(true)
      expect(validateName('Müller').valid).toBe(true)
      expect(validateName('Δημήτρης').valid).toBe(true)
    })
  })

  describe('Invalid names', () => {
    it('should reject names with numbers', () => {
      expect(validateName('John123').valid).toBe(false)
    })

    it('should reject names with special characters', () => {
      expect(validateName('John@Doe').valid).toBe(false)
      expect(validateName('John<script>').valid).toBe(false)
    })

    it('should reject names too short', () => {
      expect(validateName('J').valid).toBe(false)
    })

    it('should reject names too long', () => {
      const longName = 'A'.repeat(VALIDATION_LIMITS.NAME_MAX_LENGTH + 1)
      expect(validateName(longName).valid).toBe(false)
    })
  })

  describe('XSS prevention', () => {
    it('should reject names with HTML/script tags', () => {
      expect(validateName('<script>alert(1)</script>').valid).toBe(false)
      expect(validateName('<img src=x onerror=alert(1)>').valid).toBe(false)
    })
  })
})

describe('Text Sanitization Security', () => {
  describe('HTML entity encoding', () => {
    it('should encode < and >', () => {
      expect(sanitizeText('<script>')).toBe('&lt;script&gt;')
    })

    it('should encode ampersands', () => {
      expect(sanitizeText('Tom & Jerry')).toBe('Tom &amp; Jerry')
    })

    it('should encode quotes', () => {
      expect(sanitizeText('"Hello"')).toBe('&quot;Hello&quot;')
      expect(sanitizeText("'Hello'")).toBe('&#x27;Hello&#x27;')
    })
  })

  describe('XSS prevention', () => {
    it('should neutralize script tags', () => {
      const malicious = '<script>alert("XSS")</script>'
      const sanitized = sanitizeText(malicious)
      expect(sanitized).not.toContain('<script>')
      expect(sanitized).not.toContain('</script>')
    })

    it('should neutralize event handlers', () => {
      const malicious = '<img src=x onerror=alert(1)>'
      const sanitized = sanitizeText(malicious)
      expect(sanitized).not.toContain('onerror')
    })

    it('should neutralize javascript: URLs', () => {
      const malicious = '<a href="javascript:alert(1)">click</a>'
      const sanitized = sanitizeText(malicious)
      expect(sanitized).not.toContain('javascript:')
    })
  })

  describe('Control character removal', () => {
    it('should remove null bytes', () => {
      expect(sanitizeText('Hello\x00World')).toBe('HelloWorld')
    })

    it('should remove control characters', () => {
      expect(sanitizeText('Hello\x01\x02World')).toBe('HelloWorld')
    })
  })

  describe('Multiline text preservation', () => {
    it('should preserve newlines in multiline sanitization', () => {
      const text = 'Line 1\nLine 2\r\nLine 3'
      const sanitized = sanitizeMultilineText(text)
      expect(sanitized).toContain('\n')
    })
  })
})

describe('Price Validation Security', () => {
  describe('Valid prices', () => {
    it('should accept positive numbers', () => {
      expect(validatePrice(10.99).valid).toBe(true)
      expect(validatePrice(0.01).valid).toBe(true)
      expect(validatePrice(999999.99).valid).toBe(true)
    })

    it('should accept string numbers', () => {
      expect(validatePrice('10.99').valid).toBe(true)
    })
  })

  describe('Invalid prices', () => {
    it('should reject negative prices', () => {
      expect(validatePrice(-10).valid).toBe(false)
    })

    it('should reject prices exceeding maximum', () => {
      expect(validatePrice(1000000).valid).toBe(false)
    })

    it('should reject non-numeric strings', () => {
      expect(validatePrice('abc').valid).toBe(false)
    })

    it('should reject prices with too many decimals', () => {
      expect(validatePrice(10.999).valid).toBe(false)
    })

    it('should reject null/undefined', () => {
      expect(validatePrice(null).valid).toBe(false)
    })
  })

  describe('Overflow prevention', () => {
    it('should reject extremely large numbers', () => {
      expect(validatePrice(Number.MAX_VALUE).valid).toBe(false)
      expect(validatePrice(Infinity).valid).toBe(false)
    })
  })
})

describe('Generic Text Validation', () => {
  describe('Length limits', () => {
    it('should respect minimum length', () => {
      const result = validateText('ab', {
        fieldName: 'Test',
        minLength: 3
      })
      expect(result.valid).toBe(false)
    })

    it('should respect maximum length', () => {
      const result = validateText('a'.repeat(101), {
        fieldName: 'Test',
        maxLength: 100
      })
      expect(result.valid).toBe(false)
    })
  })

  describe('Required fields', () => {
    it('should reject empty strings when required', () => {
      const result = validateText('', {
        fieldName: 'Test',
        required: true
      })
      expect(result.valid).toBe(false)
    })

    it('should accept empty strings when not required', () => {
      const result = validateText('', {
        fieldName: 'Test',
        required: false
      })
      expect(result.valid).toBe(true)
    })
  })

  describe('Pattern matching', () => {
    it('should validate against custom patterns', () => {
      const result = validateText('abc123', {
        fieldName: 'Test',
        allowedPattern: /^[a-z]+$/
      })
      expect(result.valid).toBe(false)
    })
  })
})
