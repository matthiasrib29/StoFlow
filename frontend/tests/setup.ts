/**
 * Vitest setup file for mocking Nuxt auto-imports
 *
 * This file provides mock implementations of Nuxt's auto-imported functions
 * to enable testing of composables that depend on them.
 */

import { vi } from 'vitest'
import { ref, readonly, computed } from 'vue'

// Extend globalThis to include Nuxt auto-imports
declare global {
  var ref: typeof ref
  var readonly: typeof readonly
  var computed: typeof computed
  var useApi: ReturnType<typeof vi.fn>
  var useRouter: ReturnType<typeof vi.fn>
  var useRoute: ReturnType<typeof vi.fn>
  var navigateTo: ReturnType<typeof vi.fn>
  var useState: ReturnType<typeof vi.fn>
  var useFetch: ReturnType<typeof vi.fn>
  var useAsyncData: ReturnType<typeof vi.fn>
}

// Mock Nuxt auto-imports by making them globally available
// Re-export Vue's reactivity functions
globalThis.ref = ref
globalThis.readonly = readonly
globalThis.computed = computed

// Mock useApi composable (will be overridden in tests)
globalThis.useApi = vi.fn()

// Mock other commonly used Nuxt composables as needed
globalThis.useRouter = vi.fn()
globalThis.useRoute = vi.fn()
globalThis.navigateTo = vi.fn()
globalThis.useState = vi.fn()
globalThis.useFetch = vi.fn()
globalThis.useAsyncData = vi.fn()
