import { VintedLogger } from '../utils/logger';

/**
 * Vinted User Detector - Extraction simplifiée de l'identité utilisateur
 * Fonctionne sur n'importe quelle page Vinted si l'utilisateur est connecté
 */

interface VintedUserInfo {
  userId: string | null;
  login: string | null;
}

/**
 * Extrait les informations utilisateur depuis le HTML de la page
 */
export function getVintedUserInfo(): VintedUserInfo {
  VintedLogger.debug('');
  VintedLogger.debug('🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍');
  VintedLogger.debug('🔍 [VINTED DETECTOR] Extraction userId + login...');
  VintedLogger.debug('🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍');

  const html = document.documentElement.innerHTML;
  VintedLogger.debug('🔍 Taille HTML:', html.length, 'caractères');

  // Chercher le bloc qui contient userId ET login ensemble
  const userIdMatch = html.match(/\\"userId\\":\\"(\d+)\\"/);
  const userId = userIdMatch ? userIdMatch[1] : null;

  VintedLogger.debug('🔍 userId trouvé:', userId || 'AUCUN');

  if (!userId) {
    VintedLogger.debug('🔍 ❌ Pas de userId → utilisateur non connecté');
    VintedLogger.debug('🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍');
    VintedLogger.debug('');
    return { userId: null, login: null };
  }

  // Chercher login près du userId dans le même contexte
  const pattern = new RegExp(`\\\\"userId\\\\":\\\\"${userId}\\\\"[^}]*\\\\"login\\\\":\\\\"([^"\\\\]+)\\\\"`);
  const loginMatch = html.match(pattern);

  VintedLogger.debug('🔍 Login (contexte userId):', loginMatch ? loginMatch[1] : 'non trouvé');

  // Sinon prendre le premier login trouvé
  const fallbackLogin = html.match(/\\"login\\":\\"([^"\\]+)\\"/);
  const finalLogin = loginMatch ? loginMatch[1] : (fallbackLogin ? fallbackLogin[1] : null);

  VintedLogger.debug('🔍 Login (fallback):', fallbackLogin ? fallbackLogin[1] : 'non trouvé');
  VintedLogger.debug('🔍 ✅ Login final:', finalLogin || 'AUCUN');

  const result = {
    userId: userId,
    login: finalLogin
  };

  VintedLogger.debug('🔍 Résultat final:', result);
  VintedLogger.debug('🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍');
  VintedLogger.debug('');

  return result;
}

/**
 * Vérifie si l'utilisateur est connecté
 */
export function isVintedConnected(): boolean {
  const userInfo = getVintedUserInfo();
  return !!(userInfo.userId && userInfo.login);
}

// Export pour usage dans d'autres scripts
if (typeof window !== 'undefined') {
  (window as any).getVintedUserInfo = getVintedUserInfo;
  (window as any).isVintedConnected = isVintedConnected;
}
