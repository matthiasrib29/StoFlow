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

  // Runtime config
  runtimeConfig: {
    public: {
      // URL de base de l'API (sans /api) - utilisée par stores et composables
      apiUrl: process.env.NUXT_PUBLIC_API_URL || 'http://localhost:8000',
      // URL de base de l'API (avec /api) - utilisée par certains composables
      apiBaseUrl: process.env.NUXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api'
    }
  }
})
