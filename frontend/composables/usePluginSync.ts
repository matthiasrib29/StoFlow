/**
 * Utilitaire pour synchroniser l'auth avec le plugin navigateur
 *
 * SÉCURITÉ: Communication bidirectionnelle sécurisée
 * 1. Le plugin s'annonce avec son origine (STOFLOW_PLUGIN_READY)
 * 2. Le frontend mémorise l'origine et envoie les tokens uniquement vers celle-ci
 * 3. Validation stricte des origines pour éviter les attaques postMessage
 */

// ID de l'extension (défini dans manifest.json browser_specific_settings.gecko.id)
const EXTENSION_ID = 'stoflow@stoflow.com'

// Origines autorisées pour la communication plugin
const ALLOWED_EXTENSION_PREFIXES = [
  'moz-extension://',   // Firefox
  'chrome-extension://' // Chrome/Edge
]

// Origine du plugin mémorisée après handshake
let pluginOrigin: string | null = null

// Flag pour éviter les logs en production
const isDev = import.meta.dev

/**
 * Logger sécurisé - logs uniquement en développement
 */
const secureLog = {
  debug: (...args: any[]) => {
    if (isDev) console.log('[PluginSync]', ...args)
  },
  info: (...args: any[]) => {
    if (isDev) console.info('[PluginSync]', ...args)
  },
  warn: (...args: any[]) => {
    console.warn('[PluginSync]', ...args)
  },
  error: (...args: any[]) => {
    console.error('[PluginSync]', ...args)
  }
}

/**
 * Vérifie si une origine est une extension valide
 */
const isValidExtensionOrigin = (origin: string): boolean => {
  return ALLOWED_EXTENSION_PREFIXES.some(prefix => origin.startsWith(prefix))
}

/**
 * Initialise le listener pour recevoir l'annonce du plugin
 * Doit être appelé au démarrage de l'application
 */
export const initPluginListener = () => {
  if (!import.meta.client) return

  secureLog.debug('Initialisation du listener plugin...')

  window.addEventListener('message', (event) => {
    // SÉCURITÉ: Valider l'origine avant tout traitement
    if (!isValidExtensionOrigin(event.origin)) {
      // Ignorer silencieusement les messages d'autres origines
      return
    }

    // Traiter l'annonce du plugin
    if (event.data?.type === 'STOFLOW_PLUGIN_READY') {
      pluginOrigin = event.origin
      secureLog.info('Plugin détecté, origine mémorisée:', pluginOrigin)

      // Notifier le plugin que le frontend est prêt
      window.postMessage({
        type: 'STOFLOW_FRONTEND_ACK'
      }, pluginOrigin)
    }

    // Traiter les autres messages du plugin si nécessaire
    if (event.data?.type === 'STOFLOW_PLUGIN_REQUEST_TOKEN') {
      secureLog.debug('Plugin demande les tokens')
      // Le plugin demande une re-synchronisation
      // Récupérer les tokens du store et les envoyer
      const accessToken = localStorage.getItem('token')
      const refreshToken = localStorage.getItem('refresh_token')

      if (accessToken && pluginOrigin) {
        sendTokensToPlugin(accessToken, refreshToken)
      }
    }
  })

  secureLog.debug('Listener plugin initialisé')
}

/**
 * Envoie les tokens au plugin de manière sécurisée
 */
const sendTokensToPlugin = (accessToken: string, refreshToken: string | null) => {
  if (!pluginOrigin) {
    secureLog.warn('Plugin non détecté, impossible d\'envoyer les tokens via postMessage')
    return false
  }

  // SÉCURITÉ: Envoyer uniquement vers l'origine du plugin mémorisée
  window.postMessage({
    type: 'STOFLOW_SYNC_TOKEN',
    access_token: accessToken,
    refresh_token: refreshToken
  }, pluginOrigin)

  secureLog.debug('Tokens envoyés au plugin (origine sécurisée)')
  return true
}

/**
 * Envoie le token au plugin (appelé après login)
 */
export const syncTokenToPlugin = async (accessToken: string, refreshToken: string) => {
  if (!import.meta.client) return false

  secureLog.info('Synchronisation des tokens vers le plugin...')

  try {
    // Méthode 1 : Via chrome.runtime (plus sécurisé, si l'extension autorise externally_connectable)
    if (typeof chrome !== 'undefined' && chrome.runtime) {
      try {
        secureLog.debug('Tentative via chrome.runtime.sendMessage...')
        await chrome.runtime.sendMessage(EXTENSION_ID, {
          action: 'SYNC_TOKEN_FROM_WEBSITE',
          access_token: accessToken,
          refresh_token: refreshToken
        })
        secureLog.info('Token synchronisé via chrome.runtime')
        return true
      } catch (error: any) {
        secureLog.debug('chrome.runtime non disponible:', error.message)
      }
    }

    // Méthode 2 : Via window.postMessage sécurisé (écouté par le content script)
    if (pluginOrigin) {
      const success = sendTokensToPlugin(accessToken, refreshToken)
      if (success) {
        secureLog.info('Token synchronisé via postMessage sécurisé')
        return true
      }
    } else {
      secureLog.warn('Plugin non détecté. En attente de l\'annonce du plugin...')

      // Attendre que le plugin s'annonce (max 5 secondes)
      const waitForPlugin = new Promise<boolean>((resolve) => {
        const timeout = setTimeout(() => {
          secureLog.warn('Timeout: plugin non détecté après 5 secondes')
          resolve(false)
        }, 5000)

        const checkInterval = setInterval(() => {
          if (pluginOrigin) {
            clearTimeout(timeout)
            clearInterval(checkInterval)
            const success = sendTokensToPlugin(accessToken, refreshToken)
            resolve(success)
          }
        }, 100)
      })

      return await waitForPlugin
    }

    return false
  } catch (error: any) {
    secureLog.error('Erreur synchronisation:', error.message)
    return false
  }
}

/**
 * Notifie le plugin lors de la déconnexion
 */
export const syncLogoutToPlugin = async () => {
  if (!import.meta.client) return false

  secureLog.info('Synchronisation logout vers le plugin...')

  try {
    // Méthode 1 : Via chrome.runtime
    if (typeof chrome !== 'undefined' && chrome.runtime) {
      try {
        await chrome.runtime.sendMessage(EXTENSION_ID, {
          action: 'LOGOUT_FROM_WEBSITE'
        })
        secureLog.info('Logout synchronisé via chrome.runtime')
        return true
      } catch (error: any) {
        secureLog.debug('chrome.runtime non disponible:', error.message)
      }
    }

    // Méthode 2 : Via postMessage sécurisé
    if (pluginOrigin) {
      window.postMessage({
        type: 'STOFLOW_LOGOUT'
      }, pluginOrigin)
      secureLog.info('Logout synchronisé via postMessage sécurisé')
      return true
    } else {
      secureLog.warn('Plugin non détecté, logout non synchronisé')
      return false
    }
  } catch (error: any) {
    secureLog.error('Erreur logout:', error.message)
    return false
  }
}

/**
 * Vérifie si le plugin est installé et connecté
 */
export const isPluginInstalled = async (): Promise<boolean> => {
  if (!import.meta.client) return false

  // Vérifier si le plugin s'est déjà annoncé
  if (pluginOrigin) {
    return true
  }

  // Essayer via chrome.runtime
  try {
    if (typeof chrome !== 'undefined' && chrome.runtime) {
      await chrome.runtime.sendMessage(EXTENSION_ID, { action: 'PING' })
      return true
    }
  } catch {
    // Plugin non disponible via chrome.runtime
  }

  return false
}

/**
 * Retourne l'origine du plugin si détectée
 */
export const getPluginOrigin = (): string | null => {
  return pluginOrigin
}

/**
 * Force la réinitialisation de la connexion plugin
 * Utile après un refresh de page
 */
export const resetPluginConnection = () => {
  pluginOrigin = null
  secureLog.debug('Connexion plugin réinitialisée')
}

// Injecter l'API browser/chrome de Firefox dans window si pas déjà présent
if (typeof window !== 'undefined' && !window.chrome && typeof browser !== 'undefined') {
  window.chrome = {
    runtime: {
      sendMessage: (extensionId: string, message: any) => {
        return browser.runtime.sendMessage(extensionId, message)
      }
    }
  }
}
