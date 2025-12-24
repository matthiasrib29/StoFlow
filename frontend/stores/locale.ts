import { defineStore } from 'pinia'

export type SupportedLocale = 'en' | 'fr' | 'de' | 'it' | 'es' | 'nl' | 'pl'

export interface LocaleOption {
  code: SupportedLocale
  label: string
  flag: string
}

export const AVAILABLE_LOCALES: LocaleOption[] = [
  { code: 'fr', label: 'Français', flag: '🇫🇷' },
  { code: 'en', label: 'English', flag: '🇬🇧' },
  { code: 'de', label: 'Deutsch', flag: '🇩🇪' },
  { code: 'it', label: 'Italiano', flag: '🇮🇹' },
  { code: 'es', label: 'Español', flag: '🇪🇸' },
  { code: 'nl', label: 'Nederlands', flag: '🇳🇱' },
  { code: 'pl', label: 'Polski', flag: '🇵🇱' }
]

export const useLocaleStore = defineStore('locale', {
  state: () => ({
    currentLocale: 'fr' as SupportedLocale, // Français par défaut
  }),

  getters: {
    /**
     * Retourne la locale courante
     */
    locale: (state): SupportedLocale => state.currentLocale,

    /**
     * Retourne les infos de la locale courante
     */
    currentLocaleInfo: (state): LocaleOption => {
      return AVAILABLE_LOCALES.find(l => l.code === state.currentLocale) ?? AVAILABLE_LOCALES[0]!
    },
  },

  actions: {
    /**
     * Change la locale courante
     */
    setLocale(locale: SupportedLocale) {
      this.currentLocale = locale

      // Sauvegarder dans localStorage pour persistance
      if (import.meta.client) {
        localStorage.setItem('user-locale', locale)
      }
    },

    /**
     * Initialise la locale depuis localStorage ou utilise le défaut
     */
    initLocale() {
      if (import.meta.client) {
        const savedLocale = localStorage.getItem('user-locale') as SupportedLocale
        if (savedLocale && AVAILABLE_LOCALES.some(l => l.code === savedLocale)) {
          this.currentLocale = savedLocale
        }
      }
    },
  },
})
