// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },

  modules: [
    '@pinia/nuxt',
    '@nuxtjs/tailwindcss',
    '@vueuse/nuxt',
    '@nuxt/eslint'
  ],

  css: [
    'primeicons/primeicons.css',
    '~/assets/css/modern-dashboard.css'
  ],

  build: {
    transpile: ['primevue']
  },

  // Dev server configuration
  devServer: {
    port: 3000
  },

  // Runtime config - Environment variables override these defaults
  // NUXT_PUBLIC_API_URL and NUXT_PUBLIC_API_BASE_URL are auto-injected by Nuxt
  // See: https://nuxt.com/docs/guide/going-further/runtime-config
  runtimeConfig: {
    public: {
      // URL de base de l'API (sans /api) - overridden by NUXT_PUBLIC_API_URL
      apiUrl: 'http://localhost:8000',
      // URL de base de l'API (avec /api) - overridden by NUXT_PUBLIC_API_BASE_URL
      apiBaseUrl: 'http://localhost:8000/api'
    }
  },

  // Security headers (CSP)
  // Protects against XSS attacks by controlling which resources can be loaded
  routeRules: {
    '/**': {
      headers: {
        // Content Security Policy
        // - 'self': Only allow resources from same origin
        // - 'unsafe-inline': Required for Vue/Nuxt reactivity and Tailwind
        // - 'unsafe-eval': Required for Vue template compilation in dev
        // - data: and blob: for images/fonts
        'Content-Security-Policy': process.env.NODE_ENV === 'production'
          ? [
              "default-src 'self'",
              "script-src 'self' 'unsafe-inline'",
              "style-src 'self' 'unsafe-inline'",
              "img-src 'self' data: blob: https:",
              "font-src 'self' data:",
              "connect-src 'self' https://api.stoflow.io http://localhost:8000",
              "frame-ancestors 'none'",
              "base-uri 'self'",
              "form-action 'self'"
            ].join('; ')
          : '', // Disabled in dev for hot reload compatibility
        // Prevent clickjacking
        'X-Frame-Options': 'DENY',
        // Prevent MIME type sniffing
        'X-Content-Type-Options': 'nosniff',
        // Enable XSS filter in older browsers
        'X-XSS-Protection': '1; mode=block',
        // Control referrer information
        'Referrer-Policy': 'strict-origin-when-cross-origin'
      }
    }
  }
})
