import { useToast } from 'primevue/usetoast'
import type { ToastMessageOptions } from 'primevue/toast'
import { logger } from '~/utils/logger'

/**
 * Composable sécurisé pour utiliser PrimeVue Toast avec SSR
 *
 * Usage:
 * ```ts
 * const { showSuccess, showError, showInfo } = useAppToast()
 * showSuccess('Opération réussie!')
 * ```
 */
export const useAppToast = () => {
  let toast: ReturnType<typeof useToast> | null = null

  // Initialiser le toast uniquement côté client
  if (import.meta.client) {
    toast = useToast()
  }

  const showToast = (options: ToastMessageOptions) => {
    if (toast) {
      toast.add(options)
    } else {
      logger.warn('Toast not available (SSR context)', { options })
    }
  }

  const showSuccess = (message: string, detail?: string, life = 3000) => {
    showToast({
      severity: 'success',
      summary: message,
      detail,
      life,
    })
  }

  const showError = (message: string, detail?: string, life = 5000) => {
    showToast({
      severity: 'error',
      summary: message,
      detail,
      life,
    })
  }

  const showInfo = (message: string, detail?: string, life = 3000) => {
    showToast({
      severity: 'info',
      summary: message,
      detail,
      life,
    })
  }

  const showWarn = (message: string, detail?: string, life = 4000) => {
    showToast({
      severity: 'warn',
      summary: message,
      detail,
      life,
    })
  }

  return {
    showToast,
    showSuccess,
    showError,
    showInfo,
    showWarn,
  }
}
