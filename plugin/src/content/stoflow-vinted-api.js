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
 * - DataDome ping au démarrage + tous les 15 requests
 *
 * Author: Claude
 * Date: 2025-12-22
 */

(function() {
    'use strict';

    // ===== MINI-LOGGER FOR INJECTED SCRIPT CONTEXT =====
    const DEBUG_ENABLED = true; // Set to false in production
    const log = {
        // Stoflow API logs
        api: {
            debug: (...args) => DEBUG_ENABLED && console.log('[Stoflow API]', ...args),
            info: (...args) => console.log('[Stoflow API]', '✓', ...args),
            warn: (...args) => console.warn('[Stoflow API]', '⚠', ...args),
            error: (...args) => console.error('[Stoflow API]', '✗', ...args)
        },
        // DataDome logs
        dd: {
            debug: (...args) => DEBUG_ENABLED && console.log('[DataDome]', ...args),
            info: (...args) => console.log('[DataDome]', '✓', ...args),
            warn: (...args) => console.warn('[DataDome]', '⚠', ...args),
            error: (...args) => console.error('[DataDome]', '✗', ...args)
        }
    };

    // Éviter la double initialisation
    if (window.StoflowAPI && window.StoflowAPI._initialized) {
        log.api.debug('Already initialized, skipping');
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

    // ===== DATADOME HANDLER (defined early for startup ping) =====

    /**
     * DataDome KeepAlive Handler
     *
     * Maintains the DataDome session by triggering periodic pings.
     * DataDome uses 'datadome-det-a' custom event to collect and send data.
     * The 'dd_post_done' event is fired when the ping completes.
     */
    const DataDomeHandler = {
        _pingCount: 0,
        _isReloading: false,

        /**
         * Check if DataDome is present on the page
         */
        isPresent() {
            return !!(window.dataDomeOptions || window.ddjskey);
        },

        /**
         * Get DataDome version info
         */
        getInfo() {
            return {
                present: this.isPresent(),
                version: window.dataDomeOptions?.version || 'unknown',
                endpoint: window.dataDomeOptions?.endpoint || window.ddoptions?.endpoint || null,
                key: window.ddjskey ? window.ddjskey.substring(0, 8) + '...' : null
            };
        },

        /**
         * Trigger a DataDome ping
         * Uses the custom event 'datadome-det-a' to force data submission
         * @returns {Promise<{success: boolean, pingCount: number, error?: string}>}
         */
        async ping() {
            return new Promise((resolve) => {
                if (!this.isPresent()) {
                    log.dd.debug('Not present on page');
                    resolve({
                        success: false,
                        pingCount: this._pingCount,
                        error: 'DataDome not present on page'
                    });
                    return;
                }

                // Timeout if no response
                const timeout = setTimeout(() => {
                    window.removeEventListener('dd_post_done', handler);
                    log.dd.warn('Ping timeout (3s)');
                    resolve({
                        success: false,
                        pingCount: this._pingCount,
                        error: 'Ping timeout (3s)'
                    });
                }, 3000);

                // Listen for completion
                const handler = (e) => {
                    clearTimeout(timeout);
                    window.removeEventListener('dd_post_done', handler);
                    this._pingCount++;
                    log.dd.info(`Ping OK (#${this._pingCount})`);
                    resolve({
                        success: true,
                        pingCount: this._pingCount
                    });
                };

                window.addEventListener('dd_post_done', handler);

                // Trigger the ping
                log.dd.debug('Triggering ping...');
                window.dispatchEvent(new CustomEvent('datadome-det-a'));
            });
        },

        /**
         * Reload the DataDome script to reactivate listeners
         * Necessary because DataDome uses once: true for event listeners
         * @returns {Promise<boolean>}
         */
        async reload() {
            if (this._isReloading) {
                log.dd.debug('Already reloading, skip');
                return false;
            }

            this._isReloading = true;

            return new Promise((resolve) => {
                // Reset the processing flag
                window.dataDomeProcessed = false;

                // Find the DataDome script version
                const version = window.dataDomeOptions?.version || '5.1.9';
                const scriptUrl = `https://static-assets.vinted.com/datadome/${version}/tags.js`;

                log.dd.debug('Reloading script:', scriptUrl);

                // Create and inject new script
                const script = document.createElement('script');
                script.src = scriptUrl;

                script.onload = () => {
                    log.dd.info('Script reloaded successfully');
                    this._isReloading = false;
                    // Wait for DataDome to initialize
                    setTimeout(() => resolve(true), 500);
                };

                script.onerror = () => {
                    log.dd.error('Script reload failed');
                    this._isReloading = false;
                    resolve(false);
                };

                document.head.appendChild(script);
            });
        },

        /**
         * Ping with auto-reload if needed
         * If ping fails (listener exhausted), reload DataDome and retry
         * @returns {Promise<{success: boolean, pingCount: number, reloaded?: boolean, error?: string}>}
         */
        async safePing() {
            let result = await this.ping();

            if (!result.success && !this._isReloading) {
                log.dd.debug('Ping failed, attempting reload...');

                const reloadSuccess = await this.reload();

                if (reloadSuccess) {
                    // Wait a bit after reload
                    await new Promise(r => setTimeout(r, 1000));
                    result = await this.ping();
                    result.reloaded = true;
                }
            }

            return result;
        },

        /**
         * Get ping statistics
         */
        getStats() {
            return {
                pingCount: this._pingCount,
                isReloading: this._isReloading,
                datadomeInfo: this.getInfo()
            };
        }
    };

    // Expose DataDomeHandler globally early
    window.DataDomeHandler = DataDomeHandler;

    const StoflowAPI = {
        _apis: {},
        _ready: null,
        _initAttempts: 0,
        _maxAttempts: 5,
        _retryDelay: 1000,
        _initialized: true,
        _lastValidation: 0,
        _validationInterval: 30000, // Revalider toutes les 30s

        // DataDome ping configuration (2025-12-22)
        _requestCount: 0,
        _dataDomePingInterval: 15, // Ping DataDome every 15 requests
        _lastDataDomePing: 0,
        _startupPingDone: false,

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
            log.api.debug('Resetting APIs...');
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
                        log.api.debug(`Webpack not found (attempt ${this._initAttempts}/${this._maxAttempts})`);
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
                        log.api.debug(`API module not found (attempt ${this._initAttempts}/${this._maxAttempts})`);
                        if (this._initAttempts < this._maxAttempts) {
                            setTimeout(attemptInit, this._retryDelay * this._initAttempts);
                        } else {
                            resolve(false);
                        }
                        return;
                    }

                    log.api.debug('Main module found, ID:', targetId);

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
                                        log.api.info('Main Vinted API connected');

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
                                    log.api.error('Module loading error:', e);
                                    if (this._initAttempts < this._maxAttempts) {
                                        setTimeout(attemptInit, this._retryDelay * this._initAttempts);
                                    } else {
                                        resolve(false);
                                    }
                                }
                            }
                        ]);
                    } catch (error) {
                        log.api.error('Webpack injection error:', error);
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
                            log.api.debug(`API ${name} connected`);
                        }
                    }
                } catch (e) {
                    log.api.debug(`API ${name} not available:`, e.message);
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
                    log.api.warn(`API ${apiName} invalid, reconnecting...`);
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
         * Check if DataDome ping is needed (every 15 requests)
         * This helps maintain the session during bulk operations
         * @private
         */
        async _checkDataDomePing() {
            this._requestCount++;

            // Check if we should ping DataDome
            if (this._requestCount % this._dataDomePingInterval === 0) {
                log.dd.debug(`Auto-ping triggered (request #${this._requestCount})`);
                try {
                    const result = await DataDomeHandler.safePing();
                    if (result.success) {
                        log.dd.info(`Auto-ping OK (total: ${result.pingCount})`);
                    } else {
                        log.dd.warn(`Auto-ping failed: ${result.error}`);
                    }
                } catch (error) {
                    log.dd.error('Auto-ping error:', error);
                }
                this._lastDataDomePing = Date.now();
            }
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
            // Check DataDome ping before each request (every 15 requests)
            await this._checkDataDomePing();

            const api = await this._ensureReady('api');
            try {
                return await api.get(endpoint, { params });
            } catch (error) {
                if (error.message?.includes('Network') || error.code === 'ERR_NETWORK') {
                    log.api.warn('Network error, reconnecting...');
                    await this.init(true);
                    const newApi = await this._ensureReady('api');
                    return await newApi.get(endpoint, { params });
                }
                throw error;
            }
        },

        async post(endpoint, data = {}, config = {}) {
            // Check DataDome ping before each request (every 15 requests)
            await this._checkDataDomePing();

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
            // Check DataDome ping before each request (every 15 requests)
            await this._checkDataDomePing();

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
            // Check DataDome ping before each request (every 15 requests)
            await this._checkDataDomePing();

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

        async patch(endpoint, data = {}) {
            // Check DataDome ping before each request (every 15 requests)
            await this._checkDataDomePing();

            const api = await this._ensureReady('api');
            try {
                return await api.patch(endpoint, data);
            } catch (error) {
                if (error.message?.includes('Network') || error.code === 'ERR_NETWORK') {
                    await this.init(true);
                    const newApi = await this._ensureReady('api');
                    return await newApi.patch(endpoint, data);
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
            // Check DataDome ping before each request (every 15 requests)
            await this._checkDataDomePing();

            log.api.debug('Fetch HTML:', url);

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
                    log.api.error(`HTTP Error: ${response.status} ${response.statusText}`);
                    throw error;
                }

                const html = await response.text();

                log.api.debug(`HTML fetched: ${html.length} chars`);

                return {
                    status: response.status,
                    html: html
                };
            } catch (error) {
                log.api.error('Fetch HTML error:', error);
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
                case 'PATCH':
                    return await api.patch(endpoint, data);
                case 'DELETE':
                    return await api.delete(endpoint);
                default:
                    throw new Error(`Méthode ${method} non supportée`);
            }
        }
    };

    // Exposer globalement
    window.StoflowAPI = StoflowAPI;

    // ===== STARTUP: Eager init + DataDome ping =====
    log.api.debug('Starting eager init...');
    StoflowAPI.init().then(async (ready) => {
        if (ready) {
            log.api.info('API ready, available:', StoflowAPI.getAvailableApis().join(', '));

            // ===== STARTUP DATADOME PING =====
            if (DataDomeHandler.isPresent() && !StoflowAPI._startupPingDone) {
                log.dd.debug('Startup ping...');
                try {
                    const result = await DataDomeHandler.safePing();
                    StoflowAPI._startupPingDone = true;
                    if (result.success) {
                        log.dd.info(`Startup ping OK (#${result.pingCount})`);
                    } else {
                        log.dd.warn(`Startup ping failed: ${result.error}`);
                    }
                } catch (error) {
                    log.dd.error('Startup ping error:', error);
                }
            }
        } else {
            log.api.warn('API not available');
        }
    });

    // Détecter les navigations Next.js (soft navigation)
    let lastUrl = location.href;
    const urlObserver = new MutationObserver(() => {
        if (location.href !== lastUrl) {
            lastUrl = location.href;
            log.api.debug('Navigation detected, will revalidate API');
            // Forcer revalidation au prochain appel
            StoflowAPI._lastValidation = 0;
        }
    });
    urlObserver.observe(document.body, { childList: true, subtree: true });

    // Log DataDome status on init
    if (DataDomeHandler.isPresent()) {
        log.dd.debug('Detected:', DataDomeHandler.getInfo());
    }

    // ===== MESSAGE LISTENERS =====

    window.addEventListener('message', async (event) => {
        if (event.source !== window) return;

        const message = event.data;

        // ===== INIT API =====
        if (message.type === 'STOFLOW_INIT_API') {
            log.api.debug('Init requested');
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

            log.api.debug(`${method} ${endpoint} (api: ${apiName || 'api'})`);

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
                        case 'PATCH':
                            response = await StoflowAPI.patch(endpoint, data);
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
                log.api.error('API call error:', error);
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

        // ===== DATADOME PING =====
        if (message.type === 'STOFLOW_DATADOME_PING') {
            const { requestId } = message;

            log.dd.debug('Ping request received');

            try {
                const result = await DataDomeHandler.safePing();

                window.postMessage({
                    type: 'STOFLOW_DATADOME_PING_RESPONSE',
                    requestId,
                    success: result.success,
                    data: {
                        success: result.success,
                        ping_count: result.pingCount,
                        reloaded: result.reloaded || false,
                        error: result.error || null,
                        datadome_info: DataDomeHandler.getInfo()
                    }
                }, '*');

            } catch (error) {
                log.dd.error('Ping error:', error);
                window.postMessage({
                    type: 'STOFLOW_DATADOME_PING_RESPONSE',
                    requestId,
                    success: false,
                    error: error.message
                }, '*');
            }
        }

        // ===== FETCH HTML (NOUVEAU) =====
        if (message.type === 'STOFLOW_FETCH_HTML') {
            const { url, requestId } = message;

            log.api.debug('Fetch HTML request:', url);

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
                log.api.error('Fetch HTML error:', error);
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

    log.api.info('Vinted API Hook loaded (multi-API + fetchHtml + DataDome)');

})();
