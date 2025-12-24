<template>
  <div class="vinted-messages">
    <!-- Header with sync button -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
      <div class="flex items-center gap-3">
        <!-- Mobile: Back button when viewing messages -->
        <button
          v-if="selectedConversationId && isMobileView"
          class="lg:hidden p-2 -ml-2 rounded-lg hover:bg-gray-100"
          @click="selectedConversationId = null"
        >
          <i class="pi pi-arrow-left text-gray-600" />
        </button>
        <h3 class="text-lg font-bold text-secondary-900">Messages Vinted</h3>
        <Badge
          v-if="messagesStore.unreadCount > 0"
          :value="`${messagesStore.unreadCount} non lu(s)`"
          severity="danger"
        />
        <Badge
          :value="`${messagesStore.totalConversations} conv.`"
          severity="info"
          class="hidden sm:inline-flex"
        />
      </div>
      <div class="flex items-center gap-2">
        <!-- Search (hidden on mobile when viewing messages) -->
        <IconField :class="{ 'hidden': selectedConversationId && isMobileView }" class="flex-1 sm:flex-none">
          <InputIcon class="pi pi-search" />
          <InputText
            v-model="searchQuery"
            placeholder="Rechercher..."
            class="w-full sm:w-48"
            @keyup.enter="handleSearch"
          />
        </IconField>
        <Button
          label="Sync"
          icon="pi pi-sync"
          class="btn-primary"
          :loading="messagesStore.isSyncing"
          @click="handleSyncInbox"
        />
      </div>
    </div>

    <!-- Sync result banner -->
    <div
      v-if="messagesStore.lastSyncResult"
      class="mb-4 p-3 rounded-lg flex items-center justify-between"
      :class="messagesStore.lastSyncResult.errors.length > 0 ? 'bg-warning-50' : 'bg-success-50'"
    >
      <div class="flex items-center gap-2">
        <i
          :class="messagesStore.lastSyncResult.errors.length > 0
            ? 'pi pi-exclamation-triangle text-warning-600'
            : 'pi pi-check-circle text-success-600'"
        />
        <span class="text-sm">
          {{ messagesStore.lastSyncResult.synced }} conversation(s) synchronisée(s)
          ({{ messagesStore.lastSyncResult.created }} nouvelle(s),
          {{ messagesStore.lastSyncResult.updated }} mise(s) à jour)
        </span>
      </div>
      <Button
        icon="pi pi-times"
        class="bg-transparent hover:bg-gray-100 text-gray-500 border-0"
        size="small"
        text
        @click="messagesStore.lastSyncResult = null"
      />
    </div>

    <!-- Main content: 2 columns on desktop, stacked on mobile -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-4 min-h-[500px] lg:min-h-[600px]">
      <!-- Left column: Conversations list (hidden on mobile when viewing messages) -->
      <ConversationsList
        :class="{ 'hidden lg:flex': selectedConversationId }"
        :conversations="messagesStore.conversations"
        :selected-conversation-id="selectedConversationId"
        :show-unread-only="showUnreadOnly"
        :is-loading="messagesStore.isLoadingConversations"
        :has-more="messagesStore.hasMoreConversations"
        @select="selectConversation"
        @refresh="loadConversations"
        @toggle-unread-filter="toggleUnreadFilter"
        @load-more="loadMoreConversations"
      />

      <!-- Right column: Messages view (hidden on mobile when no conversation selected) -->
      <MessagesView
        ref="messagesViewRef"
        :class="{ 'hidden lg:flex': !selectedConversationId }"
        :conversation="messagesStore.currentConversation"
        :messages="messagesStore.currentMessages"
        :is-loading-messages="messagesStore.isLoadingMessages"
        @sync="syncCurrentConversation"
        @open-transaction="openTransaction"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useVintedMessagesStore, type VintedConversation } from '~/stores/vintedMessages'
import { useToast } from 'primevue/usetoast'
import ConversationsList from './messages/ConversationsList.vue'
import MessagesView from './messages/MessagesView.vue'

const messagesStore = useVintedMessagesStore()
const toast = import.meta.client ? useToast() : null

// Refs
const selectedConversationId = ref<number | null>(null)
const showUnreadOnly = ref(false)
const searchQuery = ref('')
const messagesViewRef = ref<InstanceType<typeof MessagesView> | null>(null)

// Mobile view detection
const isMobileView = ref(false)
const updateMobileView = () => {
  isMobileView.value = window.innerWidth < 1024 // lg breakpoint
}

if (import.meta.client) {
  onMounted(() => {
    updateMobileView()
    window.addEventListener('resize', updateMobileView)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', updateMobileView)
  })
}

// Load conversations on mount
onMounted(async () => {
  await loadConversations()
})

/**
 * Load conversations
 */
async function loadConversations() {
  try {
    await messagesStore.fetchConversations({
      unread_only: showUnreadOnly.value
    })
  } catch (error: any) {
    toast?.add({
      severity: 'error',
      summary: 'Erreur',
      detail: error.message || 'Impossible de charger les conversations',
      life: 5000
    })
  }
}

/**
 * Load more conversations (pagination)
 */
async function loadMoreConversations() {
  const nextPage = (messagesStore.conversationsPagination?.page || 1) + 1
  try {
    await messagesStore.fetchConversations({
      page: nextPage,
      unread_only: showUnreadOnly.value
    })
  } catch (error: any) {
    toast?.add({
      severity: 'error',
      summary: 'Erreur',
      detail: 'Impossible de charger plus de conversations',
      life: 5000
    })
  }
}

/**
 * Toggle unread filter
 */
async function toggleUnreadFilter() {
  showUnreadOnly.value = !showUnreadOnly.value
  await loadConversations()
}

/**
 * Sync inbox
 */
async function handleSyncInbox() {
  try {
    toast?.add({
      severity: 'info',
      summary: 'Synchronisation',
      detail: 'Récupération des messages depuis Vinted...',
      life: 3000
    })

    await messagesStore.syncInbox()

    toast?.add({
      severity: 'success',
      summary: 'Synchronisé',
      detail: `${messagesStore.lastSyncResult?.synced || 0} conversation(s) synchronisée(s)`,
      life: 3000
    })
  } catch (error: any) {
    toast?.add({
      severity: 'error',
      summary: 'Erreur',
      detail: error.message || 'Échec de la synchronisation',
      life: 5000
    })
  }
}

/**
 * Select a conversation
 */
async function selectConversation(conv: VintedConversation) {
  selectedConversationId.value = conv.id

  try {
    // Fetch conversation with messages
    await messagesStore.fetchConversation(conv.id)

    // Mark as read
    if (conv.is_unread) {
      await messagesStore.markAsRead(conv.id)
    }

    // Scroll to bottom
    await nextTick()
    messagesViewRef.value?.scrollToBottom()
  } catch (error: any) {
    toast?.add({
      severity: 'error',
      summary: 'Erreur',
      detail: 'Impossible de charger les messages',
      life: 5000
    })
  }
}

/**
 * Sync current conversation
 */
async function syncCurrentConversation() {
  if (!selectedConversationId.value) return

  try {
    toast?.add({
      severity: 'info',
      summary: 'Synchronisation',
      detail: 'Récupération des messages...',
      life: 2000
    })

    const result = await messagesStore.syncConversation(selectedConversationId.value)

    toast?.add({
      severity: 'success',
      summary: 'Synchronisé',
      detail: `${result.messages_new} nouveau(x) message(s)`,
      life: 3000
    })

    // Scroll to bottom
    await nextTick()
    messagesViewRef.value?.scrollToBottom()
  } catch (error: any) {
    toast?.add({
      severity: 'error',
      summary: 'Erreur',
      detail: 'Échec de la synchronisation',
      life: 5000
    })
  }
}

/**
 * Handle search
 */
async function handleSearch() {
  if (!searchQuery.value || searchQuery.value.length < 2) return

  try {
    await messagesStore.searchMessages(searchQuery.value)
    toast?.add({
      severity: 'info',
      summary: 'Recherche',
      detail: `${messagesStore.searchResults.length} résultat(s) trouvé(s)`,
      life: 3000
    })
  } catch (error: any) {
    toast?.add({
      severity: 'error',
      summary: 'Erreur',
      detail: 'Échec de la recherche',
      life: 5000
    })
  }
}

/**
 * Open transaction on Vinted
 */
function openTransaction() {
  if (messagesStore.currentConversation?.transaction_id) {
    window.open(
      `https://www.vinted.fr/transaction/${messagesStore.currentConversation.transaction_id}`,
      '_blank'
    )
  }
}
</script>

<style scoped>
.vinted-messages {
  min-height: 700px;
}
</style>
