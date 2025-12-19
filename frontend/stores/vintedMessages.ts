import { defineStore } from 'pinia'

/**
 * Interface for Vinted conversation
 */
export interface VintedConversation {
  id: number
  opposite_user: {
    id: number | null
    login: string | null
    photo_url: string | null
  }
  last_message_preview: string | null
  is_unread: boolean
  unread_count: number
  item_count: number
  item: {
    id: number | null
    title: string | null
    photo_url: string | null
  } | null
  transaction_id: number | null
  updated_at: string | null
  last_synced_at: string | null
}

/**
 * Interface for Vinted message
 */
export interface VintedMessage {
  id: number
  vinted_message_id: number | null
  entity_type: 'message' | 'offer_request_message' | 'status_message' | 'action_message'
  sender: {
    id: number | null
    login: string | null
  } | null
  body: string | null
  title: string | null
  subtitle: string | null
  offer: {
    price: string | null
    status: string | null
  } | null
  is_from_current_user: boolean
  created_at: string | null
}

/**
 * Pagination interface
 */
interface Pagination {
  page: number
  per_page: number
  total_entries: number
  total_pages: number
}

/**
 * Pinia store for Vinted messages/conversations management
 */
export const useVintedMessagesStore = defineStore('vintedMessages', {
  state: () => ({
    // Conversations list
    conversations: [] as VintedConversation[],
    conversationsPagination: null as Pagination | null,
    unreadCount: 0,

    // Current conversation
    currentConversation: null as VintedConversation | null,
    currentMessages: [] as VintedMessage[],

    // Search results
    searchResults: [] as VintedMessage[],
    searchQuery: '',

    // Loading states
    isLoadingConversations: false,
    isLoadingMessages: false,
    isSyncing: false,
    isSearching: false,

    // Error state
    error: null as string | null,

    // Sync results
    lastSyncResult: null as {
      synced: number
      created: number
      updated: number
      unread: number
      errors: string[]
    } | null
  }),

  getters: {
    /**
     * Get unread conversations
     */
    unreadConversations: (state) => {
      return state.conversations.filter(c => c.is_unread)
    },

    /**
     * Has more pages to load
     */
    hasMoreConversations: (state) => {
      if (!state.conversationsPagination) return false
      return state.conversationsPagination.page < state.conversationsPagination.total_pages
    },

    /**
     * Current page
     */
    currentPage: (state) => {
      return state.conversationsPagination?.page || 1
    },

    /**
     * Total conversations
     */
    totalConversations: (state) => {
      return state.conversationsPagination?.total_entries || 0
    }
  },

  actions: {
    /**
     * Fetch conversations list from API
     */
    async fetchConversations(options?: {
      page?: number
      per_page?: number
      unread_only?: boolean
    }) {
      this.isLoadingConversations = true
      this.error = null

      try {
        const api = useApi()
        const params = new URLSearchParams()

        if (options?.page) params.append('page', options.page.toString())
        if (options?.per_page) params.append('per_page', options.per_page.toString())
        if (options?.unread_only) params.append('unread_only', 'true')

        const queryString = params.toString()
        const endpoint = `/api/vinted/conversations${queryString ? '?' + queryString : ''}`

        const response = await api.get<{
          conversations: VintedConversation[]
          pagination: Pagination
          unread_count: number
        }>(endpoint)

        this.conversations = response.conversations || []
        this.conversationsPagination = response.pagination
        this.unreadCount = response.unread_count || 0

        return response
      } catch (error: any) {
        this.error = error.message || 'Error fetching conversations'
        console.error('Error fetching conversations:', error)
        throw error
      } finally {
        this.isLoadingConversations = false
      }
    },

    /**
     * Fetch a single conversation with messages
     */
    async fetchConversation(conversationId: number) {
      this.isLoadingMessages = true
      this.error = null

      try {
        const api = useApi()

        const response = await api.get<{
          conversation: VintedConversation
          messages: VintedMessage[]
        }>(`/api/vinted/conversations/${conversationId}`)

        this.currentConversation = response.conversation
        this.currentMessages = response.messages || []

        return response
      } catch (error: any) {
        this.error = error.message || 'Error fetching conversation'
        console.error('Error fetching conversation:', error)
        throw error
      } finally {
        this.isLoadingMessages = false
      }
    },

    /**
     * Sync inbox from Vinted API
     */
    async syncInbox(options?: { sync_all?: boolean }) {
      this.isSyncing = true
      this.error = null
      this.lastSyncResult = null

      try {
        const api = useApi()
        const params = new URLSearchParams()

        if (options?.sync_all) params.append('sync_all', 'true')

        const queryString = params.toString()
        const endpoint = `/api/vinted/conversations/sync${queryString ? '?' + queryString : ''}`

        const response = await api.post<{
          synced: number
          created: number
          updated: number
          unread: number
          total: number
          errors: string[]
        }>(endpoint)

        this.lastSyncResult = {
          synced: response.synced,
          created: response.created,
          updated: response.updated,
          unread: response.unread,
          errors: response.errors || []
        }

        // Refresh conversations after sync
        await this.fetchConversations()

        return response
      } catch (error: any) {
        this.error = error.message || 'Error syncing inbox'
        console.error('Error syncing inbox:', error)
        throw error
      } finally {
        this.isSyncing = false
      }
    },

    /**
     * Sync a specific conversation (fetch messages)
     */
    async syncConversation(conversationId: number) {
      this.isLoadingMessages = true
      this.error = null

      try {
        const api = useApi()

        const response = await api.post<{
          conversation_id: number
          messages_synced: number
          messages_new: number
          transaction_id: number | null
          errors: string[]
        }>(`/api/vinted/conversations/${conversationId}/sync`)

        // Refresh messages after sync
        await this.fetchConversation(conversationId)

        return response
      } catch (error: any) {
        this.error = error.message || 'Error syncing conversation'
        console.error('Error syncing conversation:', error)
        throw error
      } finally {
        this.isLoadingMessages = false
      }
    },

    /**
     * Mark conversation as read
     */
    async markAsRead(conversationId: number) {
      try {
        const api = useApi()

        await api.put(`/api/vinted/conversations/${conversationId}/read`)

        // Update local state
        const conversation = this.conversations.find(c => c.id === conversationId)
        if (conversation) {
          conversation.is_unread = false
          conversation.unread_count = 0
          this.unreadCount = Math.max(0, this.unreadCount - 1)
        }

        if (this.currentConversation?.id === conversationId) {
          this.currentConversation.is_unread = false
          this.currentConversation.unread_count = 0
        }
      } catch (error: any) {
        console.error('Error marking as read:', error)
        throw error
      }
    },

    /**
     * Search messages
     */
    async searchMessages(query: string, limit?: number) {
      if (!query || query.length < 2) {
        this.searchResults = []
        this.searchQuery = ''
        return
      }

      this.isSearching = true
      this.error = null
      this.searchQuery = query

      try {
        const api = useApi()
        const params = new URLSearchParams({ q: query })
        if (limit) params.append('limit', limit.toString())

        const response = await api.get<{
          query: string
          results: VintedMessage[]
          count: number
        }>(`/api/vinted/messages/search?${params.toString()}`)

        this.searchResults = response.results || []

        return response
      } catch (error: any) {
        this.error = error.message || 'Error searching messages'
        console.error('Error searching messages:', error)
        throw error
      } finally {
        this.isSearching = false
      }
    },

    /**
     * Clear search results
     */
    clearSearch() {
      this.searchResults = []
      this.searchQuery = ''
    },

    /**
     * Select a conversation
     */
    selectConversation(conversation: VintedConversation | null) {
      this.currentConversation = conversation
      if (!conversation) {
        this.currentMessages = []
      }
    },

    /**
     * Clear current conversation
     */
    clearCurrentConversation() {
      this.currentConversation = null
      this.currentMessages = []
    },

    /**
     * Get stats
     */
    async fetchStats() {
      try {
        const api = useApi()

        const response = await api.get<{
          total_conversations: number
          unread_conversations: number
        }>('/api/vinted/conversations/stats')

        this.unreadCount = response.unread_conversations || 0

        return response
      } catch (error: any) {
        console.error('Error fetching stats:', error)
        throw error
      }
    }
  }
})
