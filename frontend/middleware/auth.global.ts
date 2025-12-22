/**
 * Global Authentication Middleware
 *
 * This middleware runs on EVERY route change and handles:
 * - Loading auth state from localStorage on first navigation
 * - Protecting dashboard routes from unauthenticated access
 * - Redirecting authenticated users away from login/register pages
 * - Token validation before allowing access
 */

export default defineNuxtRouteMiddleware((to, from) => {
  // Skip middleware on server-side (no localStorage)
  if (import.meta.server) {
    return
  }

  const authStore = useAuthStore()

  // On first client-side navigation, load auth state from storage
  // This ensures tokens are restored before checking authentication
  if (!authStore.isAuthenticated && !authStore.token) {
    authStore.loadFromStorage()
  }

  // Define public routes that don't require authentication
  const publicRoutes = ['/', '/login', '/register', '/forgot-password', '/reset-password']
  const isPublicRoute = publicRoutes.some(route =>
    to.path === route || to.path.startsWith('/reset-password/')
  )

  // Define protected routes (dashboard and all sub-routes)
  const isProtectedRoute = to.path.startsWith('/dashboard')

  // Case 1: User is NOT authenticated and trying to access protected route
  if (isProtectedRoute && !authStore.isAuthenticated) {
    console.log('[Auth Middleware] Unauthenticated user trying to access protected route, redirecting to login')

    // Store the intended destination for redirect after login
    if (import.meta.client) {
      sessionStorage.setItem('redirectAfterLogin', to.fullPath)
    }

    return navigateTo('/login')
  }

  // Case 2: User IS authenticated and trying to access login/register
  if ((to.path === '/login' || to.path === '/register') && authStore.isAuthenticated) {
    console.log('[Auth Middleware] Authenticated user on login/register, redirecting to dashboard')

    // Check if there's a stored redirect destination
    if (import.meta.client) {
      const redirectPath = sessionStorage.getItem('redirectAfterLogin')
      if (redirectPath) {
        sessionStorage.removeItem('redirectAfterLogin')
        return navigateTo(redirectPath)
      }
    }

    return navigateTo('/dashboard')
  }

  // Case 3: User IS authenticated, check token validity for protected routes
  if (isProtectedRoute && authStore.isAuthenticated) {
    // Use token validator to check if token is about to expire
    const { willExpireSoon } = useTokenValidator()
    const token = authStore.token

    if (token && willExpireSoon(token, 2)) {
      // Token expires in less than 2 minutes, try to refresh
      console.log('[Auth Middleware] Token expiring soon, triggering refresh')
      authStore.refreshAccessToken().catch(() => {
        // If refresh fails, the store will logout and we redirect
        console.log('[Auth Middleware] Token refresh failed')
      })
    }
  }
})
