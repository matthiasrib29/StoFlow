/**
 * Vitest setup file for mocking Nuxt auto-imports
 *
 * This file provides mock implementations of Nuxt's auto-imported functions
 * to enable testing of composables that depend on them.
 */

import { vi } from 'vitest'
import { ref, readonly, computed } from 'vue'

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
