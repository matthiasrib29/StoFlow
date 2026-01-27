/**
 * Vitest setup file for mocking Nuxt auto-imports
 *
 * This file provides mock implementations of Nuxt's auto-imported functions
 * to enable testing of composables that depend on them.
 */

import { vi } from 'vitest'
import { ref, readonly, computed } from 'vue'

// Nuxt auto-generates global type declarations for all auto-imports
// (ref, computed, useRouter, useApi, etc.) in .nuxt/imports.d.ts.
// We only need to provide runtime values here — no `declare global` needed.

const g = globalThis as Record<string, unknown>

// Re-export Vue's reactivity functions
g.ref = ref
g.readonly = readonly
g.computed = computed

// Mock useApi composable (will be overridden in tests)
g.useApi = vi.fn()

// Mock other commonly used Nuxt composables as needed
g.useRouter = vi.fn()
g.useRoute = vi.fn()
g.navigateTo = vi.fn()
g.useState = vi.fn()
g.useFetch = vi.fn()
g.useAsyncData = vi.fn()
