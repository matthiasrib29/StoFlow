/**
 * Utilitaire pour synchroniser l'auth avec le plugin navigateur
 * Alternative au content script si celui-ci ne s'injecte pas
 */

// ID de l'extension (défini dans manifest.json browser_specific_settings.gecko.id)
const EXTENSION_ID = 'stoflow@stoflow.com'

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

/**
 * Envoie le token au plugin (appelé après login)
 */
export const syncTokenToPlugin = async (accessToken: string, refreshToken: string) => {
    if (!process.client) return

    console.log('');
    console.log('🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀');
    console.log('🚀 [NUXT → PLUGIN] DÉBUT SYNC TOKEN');
    console.log('🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀');
    console.log('🚀 Access Token:', accessToken ? accessToken.substring(0, 30) + '...' : 'MANQUANT');
    console.log('🚀 Refresh Token:', refreshToken ? 'Présent' : 'Absent');

    try {
      // Méthode 1 : Via chrome.runtime (si l'extension autorise externally_connectable)
      console.log('🚀 Méthode 1: Tentative chrome.runtime...');
      console.log('🚀 typeof chrome:', typeof chrome);
      console.log('🚀 chrome.runtime:', typeof chrome !== 'undefined' ? chrome.runtime : 'undefined');

      if (typeof chrome !== 'undefined' && chrome.runtime) {
        try {
          console.log('🚀 Envoi via chrome.runtime.sendMessage...');
          await chrome.runtime.sendMessage(EXTENSION_ID, {
            action: 'SYNC_TOKEN_FROM_WEBSITE',
            access_token: accessToken,
            refresh_token: refreshToken
          })
          console.log('🚀 ✅✅✅ Token synchronisé via chrome.runtime ✅✅✅')
          console.log('🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀');
          console.log('');
          return true
        } catch (error) {
          console.log('🚀 ⚠️ chrome.runtime échec:', error.message)
          console.log('🚀 Erreur complète:', error)
        }
      } else {
        console.log('🚀 ⚠️ chrome.runtime non disponible')
      }

      // Méthode 2 : Via window.postMessage (écouté par le content script)
      console.log('🚀 Méthode 2: Envoi via postMessage...');
      window.postMessage({
        type: 'STOFLOW_SYNC_TOKEN',
        access_token: accessToken,
        refresh_token: refreshToken
      }, '*')
      console.log('🚀 ✅ Token envoyé via postMessage')
      console.log('🚀 (Le content script doit recevoir ce message)')
      console.log('🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀');
      console.log('');
      return true

    } catch (error) {
      console.error('🚀 ❌❌❌ ERREUR:', error)
      console.log('🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀');
      console.log('');
      return false
    }
  }

/**
 * Notifie le plugin lors de la déconnexion
 */
export const syncLogoutToPlugin = async () => {
  if (!process.client) return

  console.log('');
  console.log('🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴');
  console.log('🔴 [NUXT → PLUGIN] LOGOUT - DÉCONNEXION');
  console.log('🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴');

  try {
    // Méthode 1 : Via chrome.runtime
    console.log('🔴 Tentative chrome.runtime...');
    if (typeof chrome !== 'undefined' && chrome.runtime) {
      try {
        console.log('🔴 Envoi via chrome.runtime.sendMessage...');
        await chrome.runtime.sendMessage(EXTENSION_ID, {
          action: 'LOGOUT_FROM_WEBSITE'
        })
        console.log('🔴 ✅ Logout synchronisé via chrome.runtime')
        console.log('🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴');
        console.log('');
        return true
      } catch (error) {
        console.log('🔴 ⚠️ chrome.runtime échec:', error.message)
      }
    }

    // Méthode 2 : Via postMessage
    console.log('🔴 Envoi via postMessage...');
    window.postMessage({
      type: 'STOFLOW_LOGOUT'
    }, '*')
    console.log('🔴 ✅ Logout envoyé via postMessage')
    console.log('🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴');
    console.log('');
    return true

  } catch (error) {
    console.error('🔴 ❌ Erreur:', error)
    console.log('🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴');
    console.log('');
    return false
  }
}

/**
 * Vérifie si le plugin est installé
 */
export const isPluginInstalled = async (): Promise<boolean> => {
  if (!process.client) return false

  try {
    if (typeof chrome !== 'undefined' && chrome.runtime) {
      await chrome.runtime.sendMessage(EXTENSION_ID, { action: 'PING' })
      return true
    }
  } catch {
    return false
  }

  return false
}
