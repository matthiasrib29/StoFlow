// https://nuxt.com/docs/api/configuration/nuxt-config

// Detect dev environment based on port
const devPort = process.env.NUXT_PORT || '3000'
const getFavicon = () => {
  if (devPort === '3000') return '/favicon-dev1.svg'
  if (devPort === '3001') return '/favicon-dev2.svg'
  if (devPort === '3002') return '/favicon-dev3.svg'
  return '/favicon.ico'
}

export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },

  // SEO Meta Tags
  app: {
    // Disable all transitions to prevent white flash
    pageTransition: false,
    layoutTransition: false,
    head: {
      title: 'Stoflow - Gérez Vinted, eBay & Etsy',
      htmlAttrs: {
        lang: 'fr'
      },
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        {
          name: 'description',
          content: 'Gérez vos ventes Vinted, eBay et Etsy en un seul endroit. Synchronisation des stocks, publication multi-marketplace en un clic. Essai gratuit.'
        },
        { name: 'author', content: 'Stoflow' },
        { name: 'robots', content: 'index, follow' },
        // Open Graph
        { property: 'og:type', content: 'website' },
        { property: 'og:site_name', content: 'Stoflow' },
        { property: 'og:title', content: 'Stoflow - Gérez Vinted, eBay & Etsy' },
        { property: 'og:description', content: 'Synchronisez vos stocks, automatisez vos publications et gérez vos ventes multi-marketplace en un clic. Essai gratuit 14 jours.' },
        { property: 'og:image', content: '/images/og-stoflow.jpg' },
        { property: 'og:image:width', content: '1200' },
        { property: 'og:image:height', content: '630' },
        { property: 'og:image:alt', content: 'Stoflow - Plateforme de gestion multi-marketplace' },
        { property: 'og:locale', content: 'fr_FR' },
        // Twitter Card
        { name: 'twitter:card', content: 'summary_large_image' },
        { name: 'twitter:site', content: '@stoflow' },
        { name: 'twitter:creator', content: '@stoflow' },
        { name: 'twitter:title', content: 'Stoflow - Gérez Vinted, eBay & Etsy' },
        { name: 'twitter:description', content: 'Gérez vos produits Vinted, eBay et Etsy depuis une seule plateforme. Essai gratuit 14 jours.' },
        { name: 'twitter:image', content: '/images/og-stoflow.jpg' },
        // Theme color
        { name: 'theme-color', content: '#1a1a1a' },
        // Apple
        { name: 'apple-mobile-web-app-capable', content: 'yes' },
        { name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent' }
      ],
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: getFavicon() },
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' } // Fallback
      ]
    }
  },

  modules: [
    '@pinia/nuxt',
    '@nuxtjs/tailwindcss',
    '@vueuse/nuxt',
    '@nuxt/eslint',
    '@nuxtjs/sitemap',
    '@nuxt/image',
    '@nuxtjs/google-fonts'
  ],

  // Google Fonts configuration
  googleFonts: {
    families: {
      // Headings - Modern geometric sans-serif (similar to Satoshi)
      'Plus+Jakarta+Sans': [400, 500, 600, 700, 800],
      // Body - Excellent readability for data-heavy dashboards
      'IBM+Plex+Sans': [400, 500, 600, 700],
      // Mono - For SKUs, references, code
      'JetBrains+Mono': [400, 500, 600]
    },
    display: 'swap', // Prevent FOIT (Flash of Invisible Text)
    preload: true,
    prefetch: true,
    preconnect: true
  },

  css: [
    'primeicons/primeicons.css',
    '~/assets/css/design-tokens.css',
    '~/assets/css/design-system.css',
    '~/assets/css/modern-dashboard.css',
    '~/assets/css/form-tokens.css',
    '~/assets/css/focus-overrides.css',
    '~/assets/css/core-web-vitals.css'
  ],

  // SEO - Sitemap configuration
  sitemap: {
    hostname: 'https://www.stoflow.io',
    gzip: true,
    routes: async () => {
      // Pages statiques publiques
      return [
        '/',
        '/login',
        '/register',
        '/legal/privacy',
        '/legal/mentions',
        '/legal/cgu',
        '/legal/cgv',
        '/docs',
      ]
    },
    exclude: [
      '/dashboard/**',      // Pages privées
      '/auth/**',           // Auth flows
      '/admin/**',          // Admin
    ]
  },

  // Image optimization
  image: {
    quality: 80,
    formats: ['webp', 'jpeg', 'png'],
    screens: {
      xs: 320,
      sm: 640,
      md: 768,
      lg: 1024,
      xl: 1280,
      '2xl': 1536,
    },
    // Enable lazy loading by default
    loading: 'lazy',
    // Preload critical images
    preload: true
  },

  build: {
    transpile: ['primevue']
  },

  // Runtime config - Environment variables override these defaults
  // NUXT_PUBLIC_API_URL and NUXT_PUBLIC_API_BASE_URL are auto-injected by Nuxt
  // See: https://nuxt.com/docs/guide/going-further/runtime-config
  runtimeConfig: {
    public: {
      // URL de base de l'API (sans /api) - overridden by NUXT_PUBLIC_API_URL
      apiUrl: 'http://localhost:8000',
      // URL de base de l'API (avec /api) - overridden by NUXT_PUBLIC_API_BASE_URL
      apiBaseUrl: 'http://localhost:8000/api',
      // Dev environment number (1, 2, or 3) - overridden by NUXT_PUBLIC_DEV_ENV
      devEnv: ''
    }
  },

  // Security headers (CSP)
  // Protects against XSS attacks by controlling which resources can be loaded
  routeRules: {
    // SSG: Pre-render public pages as static HTML
    '/': { prerender: true },
    '/login': { prerender: true },
    '/register': { prerender: true },
    '/legal/**': { prerender: true },
    '/docs': { prerender: true },
    '/docs/**': { prerender: true },

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
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
              "img-src 'self' data: blob: https:",
              "font-src 'self' data: https://fonts.gstatic.com",
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
