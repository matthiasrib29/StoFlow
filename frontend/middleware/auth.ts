export default defineNuxtRouteMiddleware((to, from) => {
  const authStore = useAuthStore()

  // Si l'utilisateur n'est pas authentifié et tente d'accéder au dashboard
  if (to.path.startsWith('/dashboard') && !authStore.isAuthenticated) {
    return navigateTo('/login')
  }

  // Si l'utilisateur est authentifié et tente d'accéder à login/register
  if ((to.path === '/login' || to.path === '/register') && authStore.isAuthenticated) {
    return navigateTo('/dashboard')
  }
})
