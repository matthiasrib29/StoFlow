/**
 * Stoflow Vinted API Core
 * Module 3/4 - Main API implementation
 *
 * Hook into Vinted's Webpack modules to access their configured Axios instances.
 * Provides HTTP methods (GET, POST, PUT, DELETE, PATCH) and HTML fetching.
 *
 * Author: Claude
 * Date: 2026-01-06
 */

(function() {
    'use strict';

    // Get shared namespace
    const modules = window.StoflowModules;
    if (!modules || !modules.log) {
        console.error('[Stoflow API] Logger module not loaded');
        return;
    }

    const log = modules.log;
    const DataDomeHandler = modules.DataDomeHandler;

    // Prevent double initialization
    if (window.StoflowAPI && window.StoflowAPI._initialized) {
        log.api.debug('Already initialized, skipping');
        return;
    }

    /**
     * Configuration for different Vinted APIs
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
        _validationInterval: 30000,

        // DataDome ping configuration
        _requestCount: 0,
        _dataDomePingInterval: 15,
        _lastDataDomePing: 0,
        _startupPingDone: false,

        /**
         * Check if an API is valid
         */
        _isApiValid(apiName = 'api') {
            const api = this._apis[apiName];
            if (!api) return false;
            if (typeof api.get !== 'function') return false;
            if (typeof api.post !== 'function') return false;
            return true;
        },

        /**
         * Reset all APIs
         */
        _reset() {
            log.api.debug('Resetting APIs...');
            this._apis = {};
            this._ready = null;
            this._initAttempts = 0;
        },

        /**
         * Find webpack module by patterns
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
         * Check if object is a valid Axios instance
         */
        _isAxiosInstance(obj) {
            if (!obj || (typeof obj !== 'object' && typeof obj !== 'function')) return false;

            const hasDefaults = obj.defaults && typeof obj.defaults === 'object';
            const hasHeaders = hasDefaults && obj.defaults.headers;
            const hasInterceptors = obj.interceptors &&
                                   obj.interceptors.request &&
                                   obj.interceptors.response;

            const hasGet = typeof obj.get === 'function';
            const hasPost = typeof obj.post === 'function';
            const hasPut = typeof obj.put === 'function';
            const hasDelete = typeof obj.delete === 'function';

            const hasBaseURL = hasDefaults && typeof obj.defaults.baseURL === 'string';

            return hasHeaders && hasInterceptors && hasGet && hasPost && hasPut && hasDelete && hasBaseURL;
        },

        /**
         * Find Axios instance by signature (more robust than code patterns)
         */
        _findAxiosBySignature() {
            if (!window.webpackChunk_N_E) return null;

            let webpackRequire = null;

            try {
                window.webpackChunk_N_E.push([
                    ['stoflow-require-hack-' + Date.now()],
                    {},
                    (req) => { webpackRequire = req; }
                ]);
            } catch (e) {
                log.api.debug('Failed to get webpack require:', e);
                return null;
            }

            if (!webpackRequire || !webpackRequire.c) {
                log.api.debug('Webpack require or cache not available');
                return null;
            }

            log.api.debug('Searching for Axios by signature in', Object.keys(webpackRequire.c).length, 'modules');

            for (const moduleId in webpackRequire.c) {
                const module = webpackRequire.c[moduleId];
                if (!module?.exports) continue;

                for (const key of ['A', 'F', 'default', 'a', 'Z']) {
                    const candidate = module.exports[key];
                    if (this._isAxiosInstance(candidate)) {
                        log.api.debug(`Found Axios instance at module ${moduleId}, export key: ${key}`);
                        return { moduleId, exportKey: key, instance: candidate };
                    }
                }

                if (this._isAxiosInstance(module.exports)) {
                    log.api.debug(`Found Axios instance at module ${moduleId} (direct export)`);
                    return { moduleId, exportKey: null, instance: module.exports };
                }
            }

            log.api.debug('No Axios instance found by signature');
            return null;
        },

        /**
         * Initialize or reinitialize the Vinted API hook
         */
        async init(force = false) {
            if (force || (this._ready && !this._isApiValid('api'))) {
                this._reset();
            }

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

                    const mainConfig = API_CONFIGS.api;
                    let targetId = this._findModuleByPatterns(mainConfig.patterns);

                    if (!targetId) {
                        log.api.debug('Pattern search failed, trying signature detection...');
                        const signatureResult = this._findAxiosBySignature();

                        if (signatureResult) {
                            this._apis.api = signatureResult.instance;
                            this._lastValidation = Date.now();
                            log.api.info('Main Vinted API connected via signature detection');
                            resolve(true);
                            return;
                        }

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
         * Load secondary APIs (images, notifications, etc.)
         */
        _loadSecondaryApis(require) {
            for (const [name, config] of Object.entries(API_CONFIGS)) {
                if (name === 'api') continue;

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
         * Ensure API is ready before a call
         */
        async _ensureReady(apiName = 'api') {
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
         * Check if DataDome ping is needed
         */
        async _checkDataDomePing() {
            this._requestCount++;

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
         * Check if main API is ready
         */
        isReady() {
            return this._isApiValid('api');
        },

        /**
         * List available APIs
         */
        getAvailableApis() {
            return Object.keys(this._apis);
        },

        // ===== HTTP METHODS =====

        async get(endpoint, params = {}) {
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

        // ===== FETCH HTML =====

        /**
         * Fetch an HTML page with Vinted session cookies
         */
        async fetchHtml(url) {
            await this._checkDataDomePing();

            log.api.debug('Fetch HTML:', url);

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

        // ===== MULTI-API METHODS =====

        async getApi(apiName) {
            return await this._ensureReady(apiName);
        },

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
                    throw new Error(`Method ${method} not supported`);
            }
        },

        // ===== SESSION REFRESH =====

        async refreshVintedSession() {
            log.api.debug('Refreshing Vinted session via /web/api/auth/refresh...');

            try {
                const response = await fetch('https://www.vinted.fr/web/api/auth/refresh', {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    }
                });

                if (response.ok) {
                    log.api.info('Vinted session refreshed successfully');
                    await this.init(true);
                    return { success: true };
                } else {
                    const error = `HTTP ${response.status}: ${response.statusText}`;
                    log.api.warn('Session refresh failed:', error);
                    return { success: false, error };
                }
            } catch (error) {
                log.api.error('Session refresh error:', error);
                return { success: false, error: error.message };
            }
        }
    };

    // Export to shared namespace and globally
    modules.StoflowAPI = StoflowAPI;
    modules.API_CONFIGS = API_CONFIGS;
    window.StoflowAPI = StoflowAPI;

    log.api.debug('API Core module loaded');

})();
