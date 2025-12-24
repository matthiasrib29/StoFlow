// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },

  // SEO Meta Tags
  app: {
    head: {
      title: 'Stoflow - Vendez sur Vinted, eBay et Etsy depuis une seule plateforme',
      htmlAttrs: {
        lang: 'fr'
      },
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        {
          name: 'description',
          content: 'Synchronisez vos stocks, automatisez vos publications et gérez vos ventes multi-marketplace en un clic. Essai gratuit 14 jours. Support Vinted, eBay, Etsy.'
        },
        { name: 'author', content: 'Stoflow' },
        { name: 'robots', content: 'index, follow' },
        // Open Graph
        { property: 'og:type', content: 'website' },
        { property: 'og:site_name', content: 'Stoflow' },
        { property: 'og:title', content: 'Stoflow - Vendez sur Vinted, eBay et Etsy depuis une seule plateforme' },
        { property: 'og:description', content: 'Synchronisez vos stocks, automatisez vos publications et gérez vos ventes multi-marketplace en un clic. Essai gratuit 14 jours.' },
        { property: 'og:image', content: '/images/og-stoflow.jpg' },
        { property: 'og:locale', content: 'fr_FR' },
        // Twitter Card
        { name: 'twitter:card', content: 'summary_large_image' },
        { name: 'twitter:title', content: 'Stoflow - Vendez sur plusieurs marketplaces en un clic' },
        { name: 'twitter:description', content: 'Gérez vos produits Vinted, eBay et Etsy depuis une seule plateforme. Essai gratuit 14 jours.' },
        { name: 'twitter:image', content: '/images/og-stoflow.jpg' },
        // Theme color
        { name: 'theme-color', content: '#1a1a1a' },
        // Apple
        { name: 'apple-mobile-web-app-capable', content: 'yes' },
        { name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent' }
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
        { rel: 'canonical', href: 'https://stoflow.io' }
      ]
    }
  },

  modules: [
    '@pinia/nuxt',
    '@nuxtjs/tailwindcss',
    '@vueuse/nuxt',
    '@nuxt/eslint'
  ],

  css: [
    'primeicons/primeicons.css',
    '~/assets/css/design-system.css',
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
              "connect-src 'self' https://api.stoflow.io https://*.stoflow.io http://api.stoflow.io http://localhost:8000",
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
