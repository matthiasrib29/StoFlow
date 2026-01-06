/**
 * Stoflow Vinted Logger
 * Module 1/4 - Logger and debug configuration
 *
 * Creates the shared namespace and provides logging utilities.
 *
 * Author: Claude
 * Date: 2026-01-06
 */

(function() {
    'use strict';

    // Create shared namespace
    window.StoflowModules = window.StoflowModules || {};

    // Debug is controlled by window.__STOFLOW_DEBUG__ (set by content script) or defaults to false
    const DEBUG_ENABLED = window.__STOFLOW_DEBUG__ === true;

    // Logger object
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

    // Export to shared namespace
    window.StoflowModules.log = log;
    window.StoflowModules.DEBUG_ENABLED = DEBUG_ENABLED;

    log.api.debug('Logger module loaded');

})();
