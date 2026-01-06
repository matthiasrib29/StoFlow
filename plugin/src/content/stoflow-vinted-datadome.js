/**
 * Stoflow Vinted DataDome Handler
 * Module 2/4 - DataDome session management
 *
 * Maintains the DataDome session by triggering periodic pings.
 * DataDome uses 'datadome-det-a' custom event to collect and send data.
 *
 * Author: Claude
 * Date: 2026-01-06
 */

(function() {
    'use strict';

    // Get shared namespace
    const modules = window.StoflowModules;
    if (!modules || !modules.log) {
        console.error('[DataDome] Logger module not loaded');
        return;
    }

    const log = modules.log;

    /**
     * DataDome KeepAlive Handler
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

    // Export to shared namespace and globally
    modules.DataDomeHandler = DataDomeHandler;
    window.DataDomeHandler = DataDomeHandler;

    log.dd.debug('DataDome module loaded');

})();
