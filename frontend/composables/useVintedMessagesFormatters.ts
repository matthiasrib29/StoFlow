/**
 * Composable for Vinted messages formatting utilities
 * Provides date formatting and message styling helpers
 */

import type { VintedMessage } from '~/stores/vintedMessages'

export const useVintedMessagesFormatters = () => {
  /**
   * Format relative time (e.g., "5min", "2h", "3j")
   */
  const formatRelativeTime = (dateStr: string | null): string => {
    if (!dateStr) return ''

    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'À l\'instant'
    if (diffMins < 60) return `${diffMins}min`
    if (diffHours < 24) return `${diffHours}h`
    if (diffDays < 7) return `${diffDays}j`

    return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })
  }

  /**
   * Format message timestamp
   */
  const formatMessageTime = (dateStr: string | null): string => {
    if (!dateStr) return ''

    const date = new Date(dateStr)
    const now = new Date()
    const isToday = date.toDateString() === now.toDateString()

    if (isToday) {
      return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
    }

    return date.toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  /**
   * Get message bubble CSS class based on type and sender
   */
  const getMessageClass = (message: VintedMessage): string => {
    if (message.entity_type === 'status_message' || message.entity_type === 'action_message') {
      return 'bg-gray-200 text-gray-700'
    }

    if (message.entity_type === 'offer_request_message') {
      return message.is_from_current_user
        ? 'bg-purple-500 text-white'
        : 'bg-purple-100 text-purple-900'
    }

    return message.is_from_current_user
      ? 'bg-cyan-500 text-white'
      : 'bg-white text-secondary-900 border border-gray-200'
  }

  return {
    formatRelativeTime,
    formatMessageTime,
    getMessageClass
  }
}
