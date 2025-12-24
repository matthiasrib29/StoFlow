import { ref, computed } from 'vue';
import { CONSTANTS, getActiveBackendUrl } from '../config/environment';
import { AuthLogger } from '../utils/logger';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user_id: number;
  role: string;
  subscription_tier?: string;
}

export function useAuth() {
  const token = ref<string | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const isAuthenticated = computed(() => !!token.value);

  /**
   * Vérifie si l'utilisateur est déjà authentifié
   * Supporte SSO: lit le token depuis chrome.storage (peut être injecté par le site web)
   */
  const checkAuth = async () => {
    const result = await chrome.storage.local.get([
      CONSTANTS.STORAGE_KEYS.ACCESS_TOKEN,
      CONSTANTS.STORAGE_KEYS.REFRESH_TOKEN
    ]);

    const accessToken = result[CONSTANTS.STORAGE_KEYS.ACCESS_TOKEN];

    if (accessToken) {
      token.value = accessToken;
      AuthLogger.debug('[Auth] ✅ Token trouvé (SSO ou login précédent);');
      return true;
    }

    AuthLogger.debug('[Auth] ⚠️ Aucun token trouvé');
    return false;
  };

  /**
   * Authentification via API backend
   */
  const login = async (credentials: LoginCredentials) => {
    loading.value = true;
    error.value = null;

    try {
      AuthLogger.debug('[Auth] 🔐 Tentative de connexion:', credentials.email);

      const backendUrl = await getActiveBackendUrl();
      const response = await fetch(`${backendUrl}/api/auth/login?source=plugin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Identifiants incorrects');
      }

      const data: AuthResponse = await response.json();

      // Stocker les tokens avec les clés standards
      await chrome.storage.local.set({
        [CONSTANTS.STORAGE_KEYS.ACCESS_TOKEN]: data.access_token,
        [CONSTANTS.STORAGE_KEYS.REFRESH_TOKEN]: data.refresh_token,
        [CONSTANTS.STORAGE_KEYS.USER_DATA]: {
          user_id: data.user_id,
          role: data.role,
          subscription_tier: data.subscription_tier
        }
      });

      token.value = data.access_token;

      AuthLogger.success('Connexion réussie', {
        userId: data.user_id,
        role: data.role
      });

      return true;
    } catch (err) {
      AuthLogger.error('[Auth] ❌ Erreur de connexion:', err);
      error.value = err instanceof Error ? err.message : 'Erreur de connexion';
      return false;
    } finally {
      loading.value = false;
    }
  };

  /**
   * Déconnexion
   */
  const logout = async () => {
    await chrome.storage.local.remove([
      CONSTANTS.STORAGE_KEYS.ACCESS_TOKEN,
      CONSTANTS.STORAGE_KEYS.REFRESH_TOKEN,
      CONSTANTS.STORAGE_KEYS.USER_DATA
    ]);
    token.value = null;
    AuthLogger.debug('[Auth] 🚪 Déconnexion réussie');
  };

  /**
   * Permet au site web d'injecter un token (SSO)
   * Cette fonction peut être appelée par un content script sur localhost:3000
   */
  const setTokenFromWebsite = async (accessToken: string, refreshToken: string, userData?: any) => {
    await chrome.storage.local.set({
      [CONSTANTS.STORAGE_KEYS.ACCESS_TOKEN]: accessToken,
      [CONSTANTS.STORAGE_KEYS.REFRESH_TOKEN]: refreshToken,
      ...(userData && { [CONSTANTS.STORAGE_KEYS.USER_DATA]: userData })
    });
    token.value = accessToken;
    AuthLogger.debug('[Auth] 🔗 Token injecté depuis le site web (SSO);');
  };

  return {
    token,
    loading,
    error,
    isAuthenticated,
    checkAuth,
    login,
    logout,
    setTokenFromWebsite
  };
}
