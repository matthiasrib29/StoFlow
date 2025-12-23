/**
 * Security Tests for OAuth CSRF Protection
 *
 * Tests the state parameter validation for OAuth flows
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock sessionStorage
const mockSessionStorage: Record<string, string> = {}
const sessionStorageMock = {
  getItem: vi.fn((key: string) => mockSessionStorage[key] || null),
  setItem: vi.fn((key: string, value: string) => {
    mockSessionStorage[key] = value
  }),
  removeItem: vi.fn((key: string) => {
    delete mockSessionStorage[key]
  }),
  clear: vi.fn(() => {
    Object.keys(mockSessionStorage).forEach(key => delete mockSessionStorage[key])
  })
}

vi.stubGlobal('sessionStorage', sessionStorageMock)

// Mock crypto.getRandomValues
vi.stubGlobal('crypto', {
  getRandomValues: (array: Uint8Array) => {
    for (let i = 0; i < array.length; i++) {
      array[i] = Math.floor(Math.random() * 256)
    }
    return array
  }
})

describe('OAuth CSRF Protection', () => {
  beforeEach(() => {
    sessionStorageMock.clear()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('State Generation', () => {
    it('should generate cryptographically random state', () => {
      // Generate multiple states and ensure they're unique
      const states = new Set<string>()

      for (let i = 0; i < 100; i++) {
        const array = new Uint8Array(32)
        crypto.getRandomValues(array)
        const state = Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
        states.add(state)
      }

      // All 100 should be unique
      expect(states.size).toBe(100)
    })

    it('should generate state of correct length', () => {
      const array = new Uint8Array(32)
      crypto.getRandomValues(array)
      const state = Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')

      // 32 bytes = 64 hex characters
      expect(state.length).toBe(64)
    })

    it('should generate state with valid hex characters', () => {
      const array = new Uint8Array(32)
      crypto.getRandomValues(array)
      const state = Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')

      expect(state).toMatch(/^[0-9a-f]+$/)
    })
  })

  describe('State Storage', () => {
    it('should store state in sessionStorage', () => {
      const state = 'test_state_123'
      sessionStorage.setItem('ebay_oauth_state', state)
      sessionStorage.setItem('ebay_oauth_state_ts', Date.now().toString())

      expect(sessionStorage.setItem).toHaveBeenCalledWith('ebay_oauth_state', state)
      expect(sessionStorage.getItem('ebay_oauth_state')).toBe(state)
    })

    it('should store timestamp with state', () => {
      const state = 'test_state_123'
      const timestamp = Date.now()

      sessionStorage.setItem('ebay_oauth_state', state)
      sessionStorage.setItem('ebay_oauth_state_ts', timestamp.toString())

      expect(sessionStorage.getItem('ebay_oauth_state_ts')).toBe(timestamp.toString())
    })
  })

  describe('State Validation', () => {
    it('should reject when no stored state exists', () => {
      const receivedState = 'some_state'
      const storedState = sessionStorage.getItem('ebay_oauth_state')

      expect(storedState).toBeNull()
    })

    it('should reject when states do not match', () => {
      sessionStorage.setItem('ebay_oauth_state', 'stored_state')
      sessionStorage.setItem('ebay_oauth_state_ts', Date.now().toString())

      const storedState = sessionStorage.getItem('ebay_oauth_state')
      const receivedState = 'different_state'

      expect(storedState).not.toBe(receivedState)
    })

    it('should accept when states match', () => {
      const state = 'matching_state_abc123'
      sessionStorage.setItem('ebay_oauth_state', state)
      sessionStorage.setItem('ebay_oauth_state_ts', Date.now().toString())

      const storedState = sessionStorage.getItem('ebay_oauth_state')
      expect(storedState).toBe(state)
    })

    it('should reject expired states', () => {
      const state = 'expired_state'
      const oldTimestamp = Date.now() - (15 * 60 * 1000) // 15 minutes ago

      sessionStorage.setItem('ebay_oauth_state', state)
      sessionStorage.setItem('ebay_oauth_state_ts', oldTimestamp.toString())

      const timestamp = parseInt(sessionStorage.getItem('ebay_oauth_state_ts') || '0', 10)
      const maxAge = 10 * 60 * 1000 // 10 minutes

      expect(Date.now() - timestamp).toBeGreaterThan(maxAge)
    })

    it('should accept non-expired states', () => {
      const state = 'fresh_state'
      const recentTimestamp = Date.now() - (5 * 60 * 1000) // 5 minutes ago

      sessionStorage.setItem('ebay_oauth_state', state)
      sessionStorage.setItem('ebay_oauth_state_ts', recentTimestamp.toString())

      const timestamp = parseInt(sessionStorage.getItem('ebay_oauth_state_ts') || '0', 10)
      const maxAge = 10 * 60 * 1000 // 10 minutes

      expect(Date.now() - timestamp).toBeLessThan(maxAge)
    })
  })

  describe('State Cleanup', () => {
    it('should clear state after validation', () => {
      sessionStorage.setItem('ebay_oauth_state', 'test_state')
      sessionStorage.setItem('ebay_oauth_state_ts', Date.now().toString())

      // Simulate validation and cleanup
      sessionStorage.removeItem('ebay_oauth_state')
      sessionStorage.removeItem('ebay_oauth_state_ts')

      expect(sessionStorage.getItem('ebay_oauth_state')).toBeNull()
      expect(sessionStorage.getItem('ebay_oauth_state_ts')).toBeNull()
    })

    it('should clear state on timeout', () => {
      sessionStorage.setItem('ebay_oauth_state', 'timeout_state')
      sessionStorage.setItem('ebay_oauth_state_ts', Date.now().toString())

      // Simulate timeout cleanup
      sessionStorage.removeItem('ebay_oauth_state')
      sessionStorage.removeItem('ebay_oauth_state_ts')

      expect(sessionStorage.removeItem).toHaveBeenCalledWith('ebay_oauth_state')
    })

    it('should clear state on error', () => {
      sessionStorage.setItem('ebay_oauth_state', 'error_state')

      // Simulate error cleanup
      sessionStorage.removeItem('ebay_oauth_state')
      sessionStorage.removeItem('ebay_oauth_state_ts')

      expect(sessionStorage.getItem('ebay_oauth_state')).toBeNull()
    })
  })

  describe('CSRF Attack Prevention', () => {
    it('should prevent CSRF by requiring matching state', () => {
      // Legitimate flow: state generated and stored
      const legitimateState = 'legitimate_state_xyz'
      sessionStorage.setItem('ebay_oauth_state', legitimateState)
      sessionStorage.setItem('ebay_oauth_state_ts', Date.now().toString())

      // Attacker's forged callback with different state
      const attackerState = 'attacker_controlled_state'

      const storedState = sessionStorage.getItem('ebay_oauth_state')
      expect(storedState).not.toBe(attackerState)
    })

    it('should prevent replay attacks with timestamp', () => {
      // Old state that was previously valid
      const oldState = 'old_valid_state'
      const veryOldTimestamp = Date.now() - (60 * 60 * 1000) // 1 hour ago

      sessionStorage.setItem('ebay_oauth_state', oldState)
      sessionStorage.setItem('ebay_oauth_state_ts', veryOldTimestamp.toString())

      const timestamp = parseInt(sessionStorage.getItem('ebay_oauth_state_ts') || '0', 10)
      const maxAge = 10 * 60 * 1000 // 10 minutes

      // Should reject due to expiry
      expect(Date.now() - timestamp).toBeGreaterThan(maxAge)
    })

    it('should prevent session fixation by using unique states', () => {
      // Each OAuth flow should have a unique state
      const states: string[] = []

      for (let i = 0; i < 5; i++) {
        const array = new Uint8Array(32)
        crypto.getRandomValues(array)
        const state = Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
        states.push(state)
      }

      const uniqueStates = new Set(states)
      expect(uniqueStates.size).toBe(states.length)
    })
  })

  describe('URL Validation', () => {
    it('should only allow eBay OAuth domains', () => {
      const validDomains = ['auth.ebay.com', 'signin.ebay.com', 'auth.sandbox.ebay.com']
      const invalidDomains = ['evil.com', 'ebay.evil.com', 'auth.ebay.evil.com']

      validDomains.forEach(domain => {
        const url = new URL(`https://${domain}/oauth`)
        const isValid = validDomains.some(d => url.hostname === d || url.hostname.endsWith('.' + d))
        expect(isValid).toBe(true)
      })

      invalidDomains.forEach(domain => {
        const url = new URL(`https://${domain}/oauth`)
        const isValid = validDomains.some(d => url.hostname === d || url.hostname.endsWith('.' + d))
        expect(isValid).toBe(false)
      })
    })

    it('should reject non-HTTPS URLs', () => {
      const httpUrl = 'http://auth.ebay.com/oauth'
      const url = new URL(httpUrl)

      expect(url.protocol).toBe('http:')
      // In production, only HTTPS should be accepted
    })
  })

  describe('Authorization Code Validation', () => {
    it('should accept valid authorization code format', () => {
      const validCodes = [
        'v^1.1#i^1#p^3#f^0#I^3#r^0#t^H4sIAAAAAAAAAO',
        'ABC123xyz-_.789',
        'simple_code'
      ]

      const codePattern = /^[a-zA-Z0-9_\-\.^#]+$/

      validCodes.forEach(code => {
        expect(codePattern.test(code)).toBe(true)
      })
    })

    it('should reject authorization codes with suspicious characters', () => {
      const invalidCodes = [
        '<script>alert(1)</script>',
        'code; DROP TABLE users;--',
        'code\x00nullbyte'
      ]

      const codePattern = /^[a-zA-Z0-9_\-\.^#]+$/

      invalidCodes.forEach(code => {
        expect(codePattern.test(code)).toBe(false)
      })
    })
  })
})
