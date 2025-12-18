import { defineStore } from 'pinia'

/**
 * Store Pinia pour gérer le thème (dark/light mode)
 * Avec persistance localStorage et transitions fluides
 */

export type ThemeMode = 'light' | 'dark' | 'system'

export const useThemeStore = defineStore('theme', {
  state: () => ({
    mode: 'light' as ThemeMode,
    isTransitioning: false
  }),

  getters: {
    /**
     * Mode effectif (résout 'system' en light/dark)
     */
    effectiveMode(): 'light' | 'dark' {
      if (this.mode === 'system') {
        if (typeof window !== 'undefined') {
          return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
        }
        return 'light'
      }
      return this.mode
    },

    /**
     * Est-ce le mode sombre ?
     */
    isDark(): boolean {
      return this.effectiveMode === 'dark'
    }
  },

  actions: {
    /**
     * Définir le mode avec animation de transition
     */
    setMode(mode: ThemeMode) {
      this.isTransitioning = true

      // Ajouter classe de transition globale
      document.documentElement.classList.add('dark-mode-transition')

      // Petit délai pour que la transition CSS s'applique
      setTimeout(() => {
        this.mode = mode
        this.applyTheme()
        this.saveToStorage()

        // Retirer la classe après la transition
        setTimeout(() => {
          document.documentElement.classList.remove('dark-mode-transition')
          this.isTransitioning = false
        }, 300)
      }, 10)
    },

    /**
     * Basculer entre light et dark
     */
    toggle() {
      const newMode = this.effectiveMode === 'dark' ? 'light' : 'dark'
      this.setMode(newMode)
    },

    /**
     * Appliquer le thème au DOM
     */
    applyTheme() {
      const isDark = this.effectiveMode === 'dark'

      if (isDark) {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }

      // Mettre à jour le meta theme-color pour les navigateurs mobiles
      const metaThemeColor = document.querySelector('meta[name="theme-color"]')
      if (metaThemeColor) {
        metaThemeColor.setAttribute('content', isDark ? '#1f2937' : '#ffffff')
      }
    },

    /**
     * Sauvegarder dans localStorage
     */
    saveToStorage() {
      if (typeof window !== 'undefined') {
        localStorage.setItem('stoflow-theme', this.mode)
      }
    },

    /**
     * Charger depuis localStorage
     */
    loadFromStorage() {
      if (typeof window !== 'undefined') {
        const stored = localStorage.getItem('stoflow-theme') as ThemeMode | null
        if (stored && ['light', 'dark', 'system'].includes(stored)) {
          this.mode = stored
        }
        this.applyTheme()

        // Écouter les changements de préférence système
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
          if (this.mode === 'system') {
            this.applyTheme()
          }
        })
      }
    }
  }
})
