/**
 * useAppToast - Wrapper SSR-safe pour PrimeVue useToast
 *
 * Ce composable est auto-importé par Nuxt et remplace l'usage direct de
 * `import { useToast } from 'primevue/usetoast'`
 *
 * Usage:
 *   const toast = useAppToast()
 *   toast.success('Message de succès')
 *   toast.error('Message d\'erreur')
 *   toast.warn('Message d\'avertissement')
 *   toast.info('Message d\'information')
 *
 * Ou avec l'API native PrimeVue:
 *   toast.add({ severity: 'success', summary: 'Titre', detail: 'Message', life: 3000 })
 */

import { useToast } from 'primevue/usetoast'

interface ToastOptions {
  summary?: string
  detail?: string
  life?: number
  closable?: boolean
  group?: string
}

export function useAppToast() {
  // SSR-safe: useToast only works on client
  const toast = import.meta.client ? useToast() : null

  return {
    /**
     * Add a toast message (native PrimeVue API)
     */
    add: (options: {
      severity: 'success' | 'info' | 'warn' | 'error' | 'secondary' | 'contrast'
      summary?: string
      detail?: string
      life?: number
      closable?: boolean
      group?: string
    }) => {
      toast?.add(options)
    },

    /**
     * Remove all toast messages
     */
    removeAll: () => {
      toast?.removeAllGroups()
    },

    /**
     * Success toast (shorthand)
     */
    success: (message: string, options?: ToastOptions) => {
      toast?.add({
        severity: 'success',
        summary: options?.summary ?? 'Succès',
        detail: message,
        life: options?.life ?? 3000,
        ...options
      })
    },

    /**
     * Error toast (shorthand)
     */
    error: (message: string, options?: ToastOptions) => {
      toast?.add({
        severity: 'error',
        summary: options?.summary ?? 'Erreur',
        detail: message,
        life: options?.life ?? 5000,
        ...options
      })
    },

    /**
     * Warning toast (shorthand)
     */
    warn: (message: string, options?: ToastOptions) => {
      toast?.add({
        severity: 'warn',
        summary: options?.summary ?? 'Attention',
        detail: message,
        life: options?.life ?? 4000,
        ...options
      })
    },

    /**
     * Info toast (shorthand)
     */
    info: (message: string, options?: ToastOptions) => {
      toast?.add({
        severity: 'info',
        summary: options?.summary ?? 'Information',
        detail: message,
        life: options?.life ?? 3000,
        ...options
      })
    },

    // =========================================================================
    // ALIASES - Pour compatibilité avec le code existant (showSuccess, showError)
    // =========================================================================

    /**
     * Show success toast (alias with title, message signature)
     */
    showSuccess: (title: string, message: string, life = 3000) => {
      toast?.add({
        severity: 'success',
        summary: title,
        detail: message,
        life
      })
    },

    /**
     * Show error toast (alias with title, message signature)
     */
    showError: (title: string, message: string, life = 5000) => {
      toast?.add({
        severity: 'error',
        summary: title,
        detail: message,
        life
      })
    },

    /**
     * Show warning toast (alias with title, message signature)
     */
    showWarn: (title: string, message: string, life = 4000) => {
      toast?.add({
        severity: 'warn',
        summary: title,
        detail: message,
        life
      })
    },

    /**
     * Show info toast (alias with title, message signature)
     */
    showInfo: (title: string, message: string, life = 3000) => {
      toast?.add({
        severity: 'info',
        summary: title,
        detail: message,
        life
      })
    }
  }
}
