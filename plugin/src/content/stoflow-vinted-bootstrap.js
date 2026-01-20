/**
 * Stoflow Vinted Bootstrap
 * Module 4/4 - Startup and message listeners
 *
 * Initializes the API, sets up navigation detection, and handles postMessage communication.
 *
 * Author: Claude
 * Date: 2026-01-06
 */

(function() {
    'use strict';

    // Get shared namespace
    const modules = window.StoflowModules;
    if (!modules || !modules.log || !modules.StoflowAPI || !(modules.SessionHandler || modules.SessionHandler)) {
        console.error('[Stoflow Bootstrap] Required modules not loaded');
        return;
    }

    const log = modules.log;
    const StoflowAPI = modules.StoflowAPI;
    const SessionHandler = modules.SessionHandler || modules.DataDomeHandler;

    // ===== STARTUP: Eager init + session ping =====
    log.api.debug('Starting eager init...');
    StoflowAPI.init().then(async (ready) => {
        if (ready) {
            log.api.info('API ready, available:', StoflowAPI.getAvailableApis().join(', '));

            // Startup session ping
            if (SessionHandler.isPresent() && !StoflowAPI._startupPingDone) {
                log.session.debug('Startup ping...');
                try {
                    const result = await SessionHandler.safePing();
                    StoflowAPI._startupPingDone = true;
                    if (result.success) {
                        log.session.info(`Startup ping OK (#${result.pingCount})`);
                    } else {
                        log.session.warn(`Startup ping failed: ${result.error}`);
                    }
                } catch (error) {
                    log.session.error('Startup ping error:', error);
                }
            }
        } else {
            log.api.warn('API not available');
        }
    });

    // ===== NAVIGATION DETECTION =====
    let lastUrl = location.href;
    const urlObserver = new MutationObserver(() => {
        if (location.href !== lastUrl) {
            lastUrl = location.href;
            log.api.debug('Navigation detected, will revalidate API');
            StoflowAPI._lastValidation = 0;
        }
    });
    urlObserver.observe(document.body, { childList: true, subtree: true });

    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        urlObserver.disconnect();
    });

    // Log session status
    if (SessionHandler.isPresent()) {
        log.session.debug('Detected:', SessionHandler.getInfo());
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
                }, window.location.origin);
            } catch (error) {
                window.postMessage({ type: 'STOFLOW_API_ERROR', error: error.message }, window.location.origin);
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
                            throw new Error(`Method ${method} not supported`);
                    }
                } else {
                    response = await StoflowAPI.call(targetApi, method, endpoint, data || params, config);
                }

                // Normalize response
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

                // CRITICAL FIX: Clean responseData to remove AxiosHeaders and other special objects
                // JSON.stringify passes but postMessage fails on objects with methods (like AxiosHeaders)
                let cleanData;
                try {
                    // First attempt: JSON round-trip to strip functions and special objects
                    cleanData = JSON.parse(JSON.stringify(responseData));
                    log.api.debug(`[DEBUG-SERIALIZE] ✅ JSON cleanup successful`);
                } catch (jsonErr) {
                    log.api.warn(`[DEBUG-SERIALIZE] ⚠️ JSON cleanup failed, manual extraction...`);
                    // Manual extraction of safe fields only
                    if (responseData && typeof responseData === 'object') {
                        cleanData = {};
                        for (const key in responseData) {
                            if (!responseData.hasOwnProperty(key)) continue;
                            // Skip known problematic fields
                            if (key === 'responseHeaders' || key === 'config' || key === 'request') {
                                log.api.debug(`[DEBUG-SERIALIZE] Skipping field '${key}'`);
                                continue;
                            }
                            const val = responseData[key];
                            const valType = typeof val;
                            if (valType === 'function') continue;
                            if (valType === 'object' && val !== null) {
                                const proto = Object.prototype.toString.call(val);
                                if (proto !== '[object Object]' && proto !== '[object Array]') {
                                    log.api.debug(`[DEBUG-SERIALIZE] Skipping special object '${key}': ${proto}`);
                                    continue;
                                }
                                try {
                                    cleanData[key] = JSON.parse(JSON.stringify(val));
                                } catch {
                                    log.api.debug(`[DEBUG-SERIALIZE] Skipping non-serializable '${key}'`);
                                }
                            } else {
                                cleanData[key] = val;
                            }
                        }
                    } else {
                        cleanData = responseData;
                    }
                }

                // Final safety check: remove any remaining problematic fields
                if (cleanData && typeof cleanData === 'object') {
                    delete cleanData.responseHeaders;
                    delete cleanData.config;
                    delete cleanData.request;
                }

                log.api.debug(`[DEBUG-SERIALIZE] Sending clean data with keys:`, Object.keys(cleanData || {}).join(', '));

                window.postMessage({
                    type: 'STOFLOW_API_RESPONSE',
                    requestId,
                    success: true,
                    status: response?.status || 200,
                    data: cleanData
                }, window.location.origin);

            } catch (error) {
                // Extract HTTP status from Axios error structure
                const httpStatus = error.response?.status || error.status || null;
                const httpStatusText = error.response?.statusText || error.statusText || null;

                // Extract error response data (if any), cleaning non-serializable fields
                let errorData = null;
                if (error.response?.data) {
                    try {
                        errorData = JSON.parse(JSON.stringify(error.response.data));
                    } catch {
                        errorData = { message: 'Response data not serializable' };
                    }
                }

                log.api.error(`API call error: ${httpStatus || 'unknown'} - ${error.message}`);
                if (httpStatus) {
                    log.api.debug(`[ERROR-DETAIL] HTTP ${httpStatus} ${httpStatusText || ''}`);
                }

                window.postMessage({
                    type: 'STOFLOW_API_RESPONSE',
                    requestId,
                    success: false,
                    error: error.message || 'Unknown error',
                    status: httpStatus,
                    statusText: httpStatusText,
                    errorData: errorData  // Include cleaned response data
                }, window.location.origin);
            }
        }

        // ===== DATADOME PING =====
        if (message.type === 'STOFLOW_DATADOME_PING') {
            const { requestId } = message;

            log.session.debug('Ping request received');

            try {
                const result = await SessionHandler.safePing();

                window.postMessage({
                    type: 'STOFLOW_DATADOME_PING_RESPONSE',
                    requestId,
                    success: result.success,
                    data: {
                        success: result.success,
                        ping_count: result.pingCount,
                        reloaded: result.reloaded || false,
                        error: result.error || null,
                        datadome_info: SessionHandler.getInfo()
                    }
                }, window.location.origin);

            } catch (error) {
                log.session.error('Ping error:', error);
                window.postMessage({
                    type: 'STOFLOW_DATADOME_PING_RESPONSE',
                    requestId,
                    success: false,
                    error: error.message
                }, window.location.origin);
            }
        }

        // ===== FETCH HTML =====
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
                }, window.location.origin);

            } catch (error) {
                log.api.error('Fetch HTML error:', error);
                window.postMessage({
                    type: 'STOFLOW_FETCH_HTML_RESPONSE',
                    requestId,
                    success: false,
                    status: error.status || 500,
                    statusText: error.statusText || 'Error',
                    error: error.message
                }, window.location.origin);
            }
        }

        // ===== REFRESH VINTED SESSION =====
        if (message.type === 'STOFLOW_REFRESH_SESSION') {
            const { requestId } = message;

            log.api.debug('Refresh session request received');

            try {
                const result = await StoflowAPI.refreshVintedSession();

                window.postMessage({
                    type: 'STOFLOW_REFRESH_SESSION_RESPONSE',
                    requestId,
                    success: result.success,
                    error: result.error || null
                }, window.location.origin);

            } catch (error) {
                log.api.error('Refresh session error:', error);
                window.postMessage({
                    type: 'STOFLOW_REFRESH_SESSION_RESPONSE',
                    requestId,
                    success: false,
                    error: error.message
                }, window.location.origin);
            }
        }
    });

    log.api.info('Vinted API Hook loaded (multi-API + fetchHtml + session + refreshSession)');

})();
