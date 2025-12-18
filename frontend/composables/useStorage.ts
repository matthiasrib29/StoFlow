/**
 * SSR-safe localStorage wrapper with error handling
 *
 * Provides a centralized abstraction for localStorage access
 * with proper error handling and SSR safety
 *
 * @example
 * const { getItem, setItem, removeItem } = useStorage()
 *
 * // Save user preferences
 * setItem('theme', 'dark')
 *
 * // Load preferences with default fallback
 * const theme = getItem('theme', 'light')
 *
 * // Save complex objects (auto-serialized)
 * setItem('user', { id: 1, name: 'John' })
 * const user = getItem<{ id: number, name: string }>('user')
 */
export const useStorage = () => {
  /**
   * Get item from localStorage with optional default value
   * Automatically parses JSON values
   *
   * @param key - localStorage key
   * @param defaultValue - Value to return if key doesn't exist
   * @returns Stored value or default
   */
  const getItem = <T = string>(key: string, defaultValue?: T): T | null => {
    // SSR safety: localStorage only available on client
    if (!import.meta.client) {
      return defaultValue ?? null
    }

    try {
      const value = localStorage.getItem(key)
      if (!value) {
        return defaultValue ?? null
      }

      // Try to parse as JSON, fallback to raw string
      try {
        return JSON.parse(value) as T
      } catch {
        // If not valid JSON, return as string (cast to T)
        return value as T
      }
    } catch (error) {
      if (import.meta.dev) {
        console.error(`[Storage] Failed to get "${key}":`, error)
      }
      return defaultValue ?? null
    }
  }

  /**
   * Set item in localStorage with automatic JSON serialization
   *
   * @param key - localStorage key
   * @param value - Value to store (will be JSON.stringified if not string)
   * @returns Success boolean
   */
  const setItem = <T = string>(key: string, value: T): boolean => {
    // SSR safety: localStorage only available on client
    if (!import.meta.client) {
      return false
    }

    try {
      const serialized = typeof value === 'string'
        ? value
        : JSON.stringify(value)

      localStorage.setItem(key, serialized)
      return true
    } catch (error) {
      if (import.meta.dev) {
        console.error(`[Storage] Failed to set "${key}":`, error)
      }
      return false
    }
  }

  /**
   * Remove item from localStorage
   *
   * @param key - localStorage key to remove
   * @returns Success boolean
   */
  const removeItem = (key: string): boolean => {
    // SSR safety: localStorage only available on client
    if (!import.meta.client) {
      return false
    }

    try {
      localStorage.removeItem(key)
      return true
    } catch (error) {
      if (import.meta.dev) {
        console.error(`[Storage] Failed to remove "${key}":`, error)
      }
      return false
    }
  }

  /**
   * Clear all items from localStorage
   *
   * @returns Success boolean
   */
  const clear = (): boolean => {
    // SSR safety: localStorage only available on client
    if (!import.meta.client) {
      return false
    }

    try {
      localStorage.clear()
      return true
    } catch (error) {
      if (import.meta.dev) {
        console.error('[Storage] Failed to clear storage:', error)
      }
      return false
    }
  }

  return {
    getItem,
    setItem,
    removeItem,
    clear
  }
}
