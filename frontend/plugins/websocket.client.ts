/**
 * WebSocket Plugin - Debug logging only
 *
 * WebSocket connection is now managed EXPLICITLY by auth.ts:
 * - login() calls ws.connect() after successful login
 * - logout() calls ws.disconnect() before clearing auth
 * - loadFromStorage() calls ws.connect() after session restore
 *
 * This plugin is kept for debug logging only.
 *
 * Author: Claude
 * Date: 2026-01-08
 * Updated: 2026-01-19 - Removed watcher, connection now managed by auth store
 */
import { createLogger } from '~/utils/logger'

const wsLogger = createLogger({ prefix: 'WS Plugin' })

export default defineNuxtPlugin(() => {
  wsLogger.debug('WebSocket connection managed by auth store (no watcher)')
})
