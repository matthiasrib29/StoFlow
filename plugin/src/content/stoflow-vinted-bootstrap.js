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
    if (!modules || !modules.log || !modules.StoflowAPI || !modules.DataDomeHandler) {
        console.error('[Stoflow Bootstrap] Required modules not loaded');
        return;
    }

    const log = modules.log;
    const StoflowAPI = modules.StoflowAPI;
    const DataDomeHandler = modules.DataDomeHandler;

    // ===== STARTUP: Eager init + DataDome ping =====
    log.api.debug('Starting eager init...');
    StoflowAPI.init().then(async (ready) => {
        if (ready) {
            log.api.info('API ready, available:', StoflowAPI.getAvailableApis().join(', '));

            // Startup DataDome ping
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

    // Log DataDome status
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

                window.postMessage({
                    type: 'STOFLOW_API_RESPONSE',
                    requestId,
                    success: true,
                    status: response?.status || 200,
                    data: responseData
                }, window.location.origin);

            } catch (error) {
                log.api.error('API call error:', error);
                window.postMessage({
                    type: 'STOFLOW_API_RESPONSE',
                    requestId,
                    success: false,
                    error: error.message,
                    status: error.response?.status,
                    statusText: error.response?.statusText
                }, window.location.origin);
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
                }, window.location.origin);

            } catch (error) {
                log.dd.error('Ping error:', error);
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

    log.api.info('Vinted API Hook loaded (multi-API + fetchHtml + DataDome + refreshSession)');

})();
