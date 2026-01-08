/**
 * Admin Middleware
 *
 * Protects admin routes (/dashboard/admin/*) from non-admin users.
 * This middleware should be applied after the global auth middleware.
 *
 * Usage:
 *   definePageMeta({ middleware: ['auth', 'admin'] })
 *
 * Or apply to specific pages:
 *   definePageMeta({ middleware: 'admin' })
 */

import { adminLogger } from '~/utils/logger'

export default defineNuxtRouteMiddleware((to) => {
  // Skip on server-side
  if (import.meta.server) {
    return
  }

  const authStore = useAuthStore()

  // Check if user is authenticated (should already be handled by auth.global.ts)
  if (!authStore.isAuthenticated || !authStore.user) {
    return navigateTo('/login')
  }

  // Check if user is admin
  if (authStore.user.role !== 'admin') {
    // Redirect non-admin users to dashboard with a message
    adminLogger.warn('Access denied: user is not admin')

    // Redirect to dashboard (they'll see a permission denied or just the normal dashboard)
    return navigateTo('/dashboard')
  }

  // User is admin, allow access
})
