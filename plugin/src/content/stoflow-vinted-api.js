/**
 * Stoflow Vinted API Hook - Multi-API Version
 *
 * Hook pour accéder aux APIs Vinted avec tous les headers gérés automatiquement.
 * Utilise les modules Webpack de Vinted pour récupérer les instances Axios configurées.
 *
 * Features:
 * - Multi-API: api (main), images, notifications, messaging, inbox
 * - fetchHtml() pour récupérer des pages HTML
 * - Auto-reconnexion si l'API devient invalide
 * - Détection des navigations Next.js
 * - Retry automatique sur erreur
 *
 * Author: Claude
 * Date: 2025-12-17
 */

(function() {
    'use strict';

    // Éviter la double initialisation
    if (window.StoflowAPI && window.StoflowAPI._initialized) {
        console.log('🛍️ [Stoflow] StoflowAPI déjà initialisé, skip');
        return;
    }

    /**
     * Configuration des différentes APIs Vinted
     * Chaque API a un pattern unique dans le code webpack
     */
    const API_CONFIGS = {
        api: {
            name: 'api',
            patterns: ['baseURL:', 'UserVerificationRequired', 'interceptors.response.use'],
            exportKey: 'F'
        },
        images: {
            name: 'images',
            patterns: ['baseURL:', '/images/', 'multipart/form-data'],
            exportKey: 'F'
        },
        notifications: {
            name: 'notifications',
            patterns: ['baseURL:', '/notifications/', 'interceptors'],
            exportKey: 'F'
        },
        messaging: {
            name: 'messaging',
            patterns: ['baseURL:', '/messaging/', 'interceptors'],
            exportKey: 'F'
        },
        inbox: {
            name: 'inbox',
            patterns: ['baseURL:', '/inbox/', 'interceptors'],
            exportKey: 'F'
        }
    };

    const StoflowAPI = {
        _apis: {},
        _ready: null,
        _initAttempts: 0,
        _maxAttempts: 5,
        _retryDelay: 1000,
        _initialized: true,
        _lastValidation: 0,
        _validationInterval: 30000, // Revalider toutes les 30s

        /**
         * Vérifie si une API est valide
         */
        _isApiValid(apiName = 'api') {
            const api = this._apis[apiName];
            if (!api) return false;

            // Vérifier que l'instance Axios a toujours ses méthodes
            if (typeof api.get !== 'function') return false;
            if (typeof api.post !== 'function') return false;

            return true;
        },

        /**
         * Force une réinitialisation de toutes les APIs
         */
        _reset() {
            console.log('🛍️ [Stoflow] 🔄 Reset des APIs...');
            this._apis = {};
            this._ready = null;
            this._initAttempts = 0;
        },

        /**
         * Recherche un module webpack par patterns
         */
        _findModuleByPatterns(patterns) {
            if (!window.webpackChunk_N_E) return null;

            for (const chunk of window.webpackChunk_N_E) {
                if (!chunk[1]) continue;

                for (const [id, fn] of Object.entries(chunk[1])) {
                    const code = fn.toString();
                    const allPatternsMatch = patterns.every(pattern => code.includes(pattern));

                    if (allPatternsMatch) {
                        return id;
                    }
                }
            }
            return null;
        },

        /**
         * Initialise ou réinitialise le hook vers les APIs Vinted
         */
        async init(force = false) {
            // Si on force ou si l'API principale n'est plus valide, reset
            if (force || (this._ready && !this._isApiValid('api'))) {
                this._reset();
            }

            // Si déjà initialisé et valide, retourner
            if (this._ready && this._isApiValid('api')) {
                return this._ready;
            }

            this._ready = new Promise((resolve) => {
                const attemptInit = () => {
                    this._initAttempts++;

                    if (!window.webpackChunk_N_E) {
                        console.log(`🛍️ [Stoflow] ❌ Webpack non trouvé (tentative ${this._initAttempts}/${this._maxAttempts})`);
                        if (this._initAttempts < this._maxAttempts) {
                            setTimeout(attemptInit, this._retryDelay * this._initAttempts);
                        } else {
                            resolve(false);
                        }
                        return;
                    }

                    // Chercher l'API principale avec les patterns spécifiques
                    const mainConfig = API_CONFIGS.api;
                    const targetId = this._findModuleByPatterns(mainConfig.patterns);

                    if (!targetId) {
                        console.log(`🛍️ [Stoflow] ❌ Module API non trouvé (tentative ${this._initAttempts}/${this._maxAttempts})`);
                        if (this._initAttempts < this._maxAttempts) {
                            setTimeout(attemptInit, this._retryDelay * this._initAttempts);
                        } else {
                            resolve(false);
                        }
                        return;
                    }

                    console.log('🛍️ [Stoflow] 📍 Module principal trouvé, ID:', targetId);

                    try {
                        window.webpackChunk_N_E.push([
                            ['stoflow-api-hook-' + Date.now()],
                            {},
                            (require) => {
                                try {
                                    const module = require(Number(targetId));
                                    if (module?.F) {
                                        this._apis.api = module.F;
                                        this._lastValidation = Date.now();
                                        console.log('🛍️ [Stoflow] ✅ API principale Vinted connectée');

                                        // Essayer de charger les autres APIs (non bloquant)
                                        this._loadSecondaryApis(require);

                                        resolve(true);
                                    } else {
                                        if (this._initAttempts < this._maxAttempts) {
                                            setTimeout(attemptInit, this._retryDelay * this._initAttempts);
                                        } else {
                                            resolve(false);
                                        }
                                    }
                                } catch(e) {
                                    console.log('🛍️ [Stoflow] ❌ Erreur chargement module:', e);
                                    if (this._initAttempts < this._maxAttempts) {
                                        setTimeout(attemptInit, this._retryDelay * this._initAttempts);
                                    } else {
                                        resolve(false);
                                    }
                                }
                            }
                        ]);
                    } catch (error) {
                        console.log('🛍️ [Stoflow] ❌ Erreur injection webpack:', error);
                        if (this._initAttempts < this._maxAttempts) {
                            setTimeout(attemptInit, this._retryDelay * this._initAttempts);
                        } else {
                            resolve(false);
                        }
                    }
                };

                attemptInit();
            });

            return this._ready;
        },

        /**
         * Charge les APIs secondaires (images, notifications, etc.)
         */
        _loadSecondaryApis(require) {
            for (const [name, config] of Object.entries(API_CONFIGS)) {
                if (name === 'api') continue; // Déjà chargé

                try {
                    const moduleId = this._findModuleByPatterns(config.patterns);
                    if (moduleId) {
                        const module = require(Number(moduleId));
                        if (module?.[config.exportKey]) {
                            this._apis[name] = module[config.exportKey];
                            console.log(`🛍️ [Stoflow] ✅ API ${name} connectée`);
                        }
                    }
                } catch (e) {
                    console.log(`🛍️ [Stoflow] ⚠️ API ${name} non disponible:`, e.message);
                }
            }
        },

        /**
         * Assure que l'API est prête avant un appel
         */
        async _ensureReady(apiName = 'api') {
            // Vérifier périodiquement la validité
            const now = Date.now();
            if (now - this._lastValidation > this._validationInterval) {
                if (!this._isApiValid(apiName)) {
                    console.log(`🛍️ [Stoflow] ⚠️ API ${apiName} invalide détectée, reconnexion...`);
                    await this.init(true);
                }
                this._lastValidation = now;
            }

            await this.init();

            const api = this._apis[apiName];
            if (!api) {
                throw new Error(`API Vinted (${apiName}) non disponible - actualise la page Vinted`);
            }

            return api;
        },

        /**
         * Vérifie si l'API principale est prête
         */
        isReady() {
            return this._isApiValid('api');
        },

        /**
         * Liste des APIs disponibles
         */
        getAvailableApis() {
            return Object.keys(this._apis);
        },

        // ===== MÉTHODES HTTP (API PRINCIPALE) =====

        async get(endpoint, params = {}) {
            const api = await this._ensureReady('api');
            try {
                return await api.get(endpoint, { params });
            } catch (error) {
                if (error.message?.includes('Network') || error.code === 'ERR_NETWORK') {
                    console.log('🛍️ [Stoflow] 🔄 Erreur réseau, tentative reconnexion...');
                    await this.init(true);
                    const newApi = await this._ensureReady('api');
                    return await newApi.get(endpoint, { params });
                }
                throw error;
            }
        },

        async post(endpoint, data = {}, config = {}) {
            const api = await this._ensureReady('api');
            try {
                return await api.post(endpoint, data, config);
            } catch (error) {
                if (error.message?.includes('Network') || error.code === 'ERR_NETWORK') {
                    await this.init(true);
                    const newApi = await this._ensureReady('api');
                    return await newApi.post(endpoint, data, config);
                }
                throw error;
            }
        },

        async put(endpoint, data = {}) {
            const api = await this._ensureReady('api');
            try {
                return await api.put(endpoint, data);
            } catch (error) {
                if (error.message?.includes('Network') || error.code === 'ERR_NETWORK') {
                    await this.init(true);
                    const newApi = await this._ensureReady('api');
                    return await newApi.put(endpoint, data);
                }
                throw error;
            }
        },

        async delete(endpoint) {
            const api = await this._ensureReady('api');
            try {
                return await api.delete(endpoint);
            } catch (error) {
                if (error.message?.includes('Network') || error.code === 'ERR_NETWORK') {
                    await this.init(true);
                    const newApi = await this._ensureReady('api');
                    return await newApi.delete(endpoint);
                }
                throw error;
            }
        },

        // ===== FETCH HTML (NOUVEAU) =====

        /**
         * Récupère une page HTML avec les cookies de session Vinted
         * @param {string} url - URL complète ou relative de la page
         * @returns {Promise<{status: number, html: string}>}
         */
        async fetchHtml(url) {
            console.log(`🛍️ [Stoflow] 📄 Fetch HTML: ${url}`);

            // Construire l'URL complète si relative
            let fullUrl = url;
            if (url.startsWith('/')) {
                fullUrl = `https://www.vinted.fr${url}`;
            } else if (!url.startsWith('http')) {
                fullUrl = `https://www.vinted.fr/${url}`;
            }

            try {
                const response = await fetch(fullUrl, {
                    method: 'GET',
                    credentials: 'include',
                    headers: {
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7'
                    }
                });

                // IMPORTANT: Check for HTTP errors (403, 404, 500, etc.)
                if (!response.ok) {
                    const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
                    error.status = response.status;
                    error.statusText = response.statusText;
                    console.error(`🛍️ [Stoflow] ❌ HTTP Error: ${response.status} ${response.statusText}`);
                    throw error;
                }

                const html = await response.text();

                console.log(`🛍️ [Stoflow] ✅ HTML récupéré: ${html.length} caractères`);

                return {
                    status: response.status,
                    html: html
                };
            } catch (error) {
                console.error('🛍️ [Stoflow] ❌ Erreur fetch HTML:', error);
                throw error;
            }
        },

        // ===== MÉTHODES MULTI-API =====

        /**
         * Obtient une instance API spécifique
         * @param {string} apiName - Nom de l'API (api, images, notifications, messaging, inbox)
         */
        async getApi(apiName) {
            return await this._ensureReady(apiName);
        },

        /**
         * Appel API générique sur une instance spécifique
         */
        async call(apiName, method, endpoint, data = null, config = {}) {
            const api = await this._ensureReady(apiName);

            switch (method.toUpperCase()) {
                case 'GET':
                    return await api.get(endpoint, { params: data });
                case 'POST':
                    return await api.post(endpoint, data, config);
                case 'PUT':
                    return await api.put(endpoint, data);
                case 'DELETE':
                    return await api.delete(endpoint);
                default:
                    throw new Error(`Méthode ${method} non supportée`);
            }
        }
    };

    // Exposer globalement
    window.StoflowAPI = StoflowAPI;

    // Eager init
    console.log('🛍️ [Stoflow] 🚀 Démarrage eager init...');
    StoflowAPI.init().then((ready) => {
        if (ready) {
            console.log('🛍️ [Stoflow] ✅ API prête');
            console.log('🛍️ [Stoflow] 📋 APIs disponibles:', StoflowAPI.getAvailableApis().join(', '));
        } else {
            console.log('🛍️ [Stoflow] ⚠️ API non disponible');
        }
    });

    // Détecter les navigations Next.js (soft navigation)
    let lastUrl = location.href;
    const urlObserver = new MutationObserver(() => {
        if (location.href !== lastUrl) {
            lastUrl = location.href;
            console.log('🛍️ [Stoflow] 🔄 Navigation détectée, revalidation API...');
            // Forcer revalidation au prochain appel
            StoflowAPI._lastValidation = 0;
        }
    });
    urlObserver.observe(document.body, { childList: true, subtree: true });

    // ===== MESSAGE LISTENERS =====

    window.addEventListener('message', async (event) => {
        if (event.source !== window) return;

        const message = event.data;

        // ===== INIT API =====
        if (message.type === 'STOFLOW_INIT_API') {
            console.log('🛍️ [Stoflow] Initialisation API demandée...');
            try {
                const ready = await StoflowAPI.init(true);
                window.postMessage({
                    type: ready ? 'STOFLOW_API_READY' : 'STOFLOW_API_ERROR',
                    apis: ready ? StoflowAPI.getAvailableApis() : [],
                    error: ready ? null : 'API Vinted non disponible'
                }, '*');
            } catch (error) {
                window.postMessage({ type: 'STOFLOW_API_ERROR', error: error.message }, '*');
            }
        }

        // ===== API CALL (JSON) =====
        if (message.type === 'STOFLOW_API_CALL') {
            const { method, endpoint, params, data, config, requestId, apiName } = message;

            console.log(`🛍️ [Stoflow] 📡 API CALL: ${method} ${endpoint} (api: ${apiName || 'api'})`);

            try {
                let response;
                const targetApi = apiName || 'api';

                if (targetApi === 'api') {
                    // Utiliser les méthodes standard pour l'API principale
                    switch (method) {
                        case 'GET':
                            response = await StoflowAPI.get(endpoint, params);
                            break;
                        case 'POST':
                            response = await StoflowAPI.post(endpoint, data, config);
                            break;
                        case 'PUT':
                            response = await StoflowAPI.put(endpoint, data);
                            break;
                        case 'DELETE':
                            response = await StoflowAPI.delete(endpoint);
                            break;
                        default:
                            throw new Error(`Méthode ${method} non supportée`);
                    }
                } else {
                    // Utiliser la méthode générique pour les autres APIs
                    response = await StoflowAPI.call(targetApi, method, endpoint, data || params, config);
                }

                // Normaliser la réponse
                let responseData;
                if (response && typeof response === 'object') {
                    if ('data' in response && 'status' in response) {
                        responseData = response.data;
                    } else {
                        responseData = response;
                    }
                } else {
                    responseData = response;
                }

                window.postMessage({
                    type: 'STOFLOW_API_RESPONSE',
                    requestId,
                    success: true,
                    status: response?.status || 200,
                    data: responseData
                }, '*');

            } catch (error) {
                console.error('🛍️ [Stoflow] ❌ API CALL Error:', error);
                window.postMessage({
                    type: 'STOFLOW_API_RESPONSE',
                    requestId,
                    success: false,
                    error: error.message,
                    status: error.response?.status,
                    statusText: error.response?.statusText
                }, '*');
            }
        }

        // ===== FETCH HTML (NOUVEAU) =====
        if (message.type === 'STOFLOW_FETCH_HTML') {
            const { url, requestId } = message;

            console.log(`🛍️ [Stoflow] 📄 FETCH HTML: ${url}`);

            try {
                const result = await StoflowAPI.fetchHtml(url);

                window.postMessage({
                    type: 'STOFLOW_FETCH_HTML_RESPONSE',
                    requestId,
                    success: true,
                    status: result.status,
                    data: result.html
                }, '*');

            } catch (error) {
                console.error('🛍️ [Stoflow] ❌ FETCH HTML Error:', error);
                window.postMessage({
                    type: 'STOFLOW_FETCH_HTML_RESPONSE',
                    requestId,
                    success: false,
                    status: error.status || 500,
                    statusText: error.statusText || 'Error',
                    error: error.message
                }, '*');
            }
        }
    });

    console.log('🛍️ [Stoflow] ✅ Vinted API Hook chargé (multi-API + fetchHtml)');

})();
