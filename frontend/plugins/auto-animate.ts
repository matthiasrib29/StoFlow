import { autoAnimatePlugin } from '@formkit/auto-animate/vue'

export default defineNuxtPlugin((nuxtApp) => {
  // Only use the real plugin on client-side
  // On server, register a no-op directive to prevent warnings
  if (import.meta.client) {
    nuxtApp.vueApp.use(autoAnimatePlugin)
  } else {
    // Register a no-op directive for SSR to prevent "Failed to resolve directive" warnings
    nuxtApp.vueApp.directive('auto-animate', {
      // No-op - animations only happen on client
    })
  }
})
