/**
 * Security Tests for Logger Utility
 *
 * Tests that sensitive data is properly sanitized in logs
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createLogger } from '../../utils/logger'

describe('Logger Security', () => {
  let consoleSpy: {
    log: ReturnType<typeof vi.spyOn>
    info: ReturnType<typeof vi.spyOn>
    warn: ReturnType<typeof vi.spyOn>
    error: ReturnType<typeof vi.spyOn>
  }

  beforeEach(() => {
    // Mock import.meta.dev to true for testing
    vi.stubGlobal('import', { meta: { dev: true } })

    consoleSpy = {
      log: vi.spyOn(console, 'log').mockImplementation(() => {}),
      info: vi.spyOn(console, 'info').mockImplementation(() => {}),
      warn: vi.spyOn(console, 'warn').mockImplementation(() => {}),
      error: vi.spyOn(console, 'error').mockImplementation(() => {})
    }
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  describe('JWT Token Sanitization', () => {
    it('should redact JWT tokens in strings', () => {
      const logger = createLogger({ forceEnabled: true })
      const jwtToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'

      logger.error('Token:', jwtToken)

      expect(consoleSpy.error).toHaveBeenCalled()
      const loggedArgs = consoleSpy.error.mock.calls[0]
      const loggedString = loggedArgs.join(' ')
      expect(loggedString).not.toContain('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9')
      expect(loggedString).toContain('[REDACTED]')
    })

    it('should redact Bearer tokens', () => {
      const logger = createLogger({ forceEnabled: true })

      logger.error('Header: Bearer abc123xyz456')

      expect(consoleSpy.error).toHaveBeenCalled()
      const loggedArgs = consoleSpy.error.mock.calls[0]
      const loggedString = loggedArgs.join(' ')
      expect(loggedString).toContain('[REDACTED]')
    })
  })

  describe('Email Sanitization', () => {
    it('should redact email addresses in strings', () => {
      const logger = createLogger({ forceEnabled: true })

      logger.error('User email: user@example.com')

      expect(consoleSpy.error).toHaveBeenCalled()
      const loggedArgs = consoleSpy.error.mock.calls[0]
      const loggedString = loggedArgs.join(' ')
      expect(loggedString).not.toContain('user@example.com')
      expect(loggedString).toContain('[REDACTED]')
    })
  })

  describe('Password Sanitization', () => {
    it('should redact password fields in objects', () => {
      const logger = createLogger({ forceEnabled: true })

      logger.error('User data:', { username: 'john', password: 'secret123' })

      expect(consoleSpy.error).toHaveBeenCalled()
      const loggedArgs = consoleSpy.error.mock.calls[0]
      // The password should be redacted
      expect(JSON.stringify(loggedArgs)).not.toContain('secret123')
    })

    it('should redact password in JSON strings', () => {
      const logger = createLogger({ forceEnabled: true })
      const jsonString = '{"username": "john", "password": "secret123"}'

      logger.error('Data:', jsonString)

      expect(consoleSpy.error).toHaveBeenCalled()
      const loggedArgs = consoleSpy.error.mock.calls[0]
      const loggedString = loggedArgs.join(' ')
      expect(loggedString).toContain('[REDACTED]')
    })
  })

  describe('Sensitive Key Sanitization', () => {
    it('should redact token fields in objects', () => {
      const logger = createLogger({ forceEnabled: true })

      logger.error('Auth:', { access_token: 'abc123', refresh_token: 'xyz789' })

      expect(consoleSpy.error).toHaveBeenCalled()
      const loggedArgs = consoleSpy.error.mock.calls[0]
      expect(JSON.stringify(loggedArgs)).not.toContain('abc123')
      expect(JSON.stringify(loggedArgs)).not.toContain('xyz789')
    })

    it('should redact secret fields in objects', () => {
      const logger = createLogger({ forceEnabled: true })

      logger.error('Config:', { api_secret: 'mysecret', public_key: 'pub123' })

      expect(consoleSpy.error).toHaveBeenCalled()
      const loggedArgs = consoleSpy.error.mock.calls[0]
      expect(JSON.stringify(loggedArgs)).not.toContain('mysecret')
    })

    it('should redact API key patterns', () => {
      const logger = createLogger({ forceEnabled: true })

      logger.error('API key: api_key="sk_live_1234567890abcdefghij"')

      expect(consoleSpy.error).toHaveBeenCalled()
      const loggedArgs = consoleSpy.error.mock.calls[0]
      const loggedString = loggedArgs.join(' ')
      expect(loggedString).toContain('[REDACTED]')
    })
  })

  describe('Credit Card Sanitization', () => {
    it('should redact credit card numbers', () => {
      const logger = createLogger({ forceEnabled: true })

      logger.error('Card: 4111-1111-1111-1111')

      expect(consoleSpy.error).toHaveBeenCalled()
      const loggedArgs = consoleSpy.error.mock.calls[0]
      const loggedString = loggedArgs.join(' ')
      expect(loggedString).not.toContain('4111-1111-1111-1111')
      expect(loggedString).toContain('[REDACTED]')
    })

    it('should redact card numbers without dashes', () => {
      const logger = createLogger({ forceEnabled: true })

      logger.error('Card: 4111111111111111')

      expect(consoleSpy.error).toHaveBeenCalled()
      const loggedArgs = consoleSpy.error.mock.calls[0]
      const loggedString = loggedArgs.join(' ')
      expect(loggedString).toContain('[REDACTED]')
    })
  })

  describe('Nested Object Sanitization', () => {
    it('should sanitize deeply nested objects', () => {
      const logger = createLogger({ forceEnabled: true })

      logger.error('Data:', {
        user: {
          profile: {
            credentials: {
              password: 'nested_secret'
            }
          }
        }
      })

      expect(consoleSpy.error).toHaveBeenCalled()
      const loggedArgs = consoleSpy.error.mock.calls[0]
      expect(JSON.stringify(loggedArgs)).not.toContain('nested_secret')
    })
  })

  describe('Array Sanitization', () => {
    it('should sanitize arrays containing sensitive data', () => {
      const logger = createLogger({ forceEnabled: true })

      logger.error('Users:', [
        { name: 'John', token: 'abc' },
        { name: 'Jane', token: 'xyz' }
      ])

      expect(consoleSpy.error).toHaveBeenCalled()
      const loggedArgs = consoleSpy.error.mock.calls[0]
      expect(JSON.stringify(loggedArgs)).not.toContain('abc')
      expect(JSON.stringify(loggedArgs)).not.toContain('xyz')
    })
  })

  describe('Logger Prefix', () => {
    it('should include prefix in log messages', () => {
      const logger = createLogger({ prefix: 'TestModule', forceEnabled: true })

      logger.error('Test message')

      expect(consoleSpy.error).toHaveBeenCalled()
      const loggedArgs = consoleSpy.error.mock.calls[0]
      const loggedString = loggedArgs.join(' ')
      expect(loggedString).toContain('[TestModule]')
    })
  })

  describe('Log Levels', () => {
    it('should always log errors even without forceEnabled', () => {
      const logger = createLogger()

      logger.error('Error message')

      expect(consoleSpy.error).toHaveBeenCalled()
    })

    it('should always log warnings', () => {
      const logger = createLogger()

      logger.warn('Warning message')

      expect(consoleSpy.warn).toHaveBeenCalled()
    })
  })

  describe('Safe Data Handling', () => {
    it('should not modify non-sensitive data', () => {
      const logger = createLogger({ forceEnabled: true })

      logger.error('User ID: 12345, Status: active')

      expect(consoleSpy.error).toHaveBeenCalled()
      const loggedArgs = consoleSpy.error.mock.calls[0]
      const loggedString = loggedArgs.join(' ')
      expect(loggedString).toContain('12345')
      expect(loggedString).toContain('active')
    })
  })
})
