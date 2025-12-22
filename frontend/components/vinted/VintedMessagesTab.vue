<template>
  <div class="vinted-messages">
    <!-- Header with sync button -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-3">
        <h3 class="text-lg font-bold text-secondary-900">Messages Vinted</h3>
        <Badge
          v-if="messagesStore.unreadCount > 0"
          :value="`${messagesStore.unreadCount} non lu(s)`"
          severity="danger"
        />
        <Badge
          :value="`${messagesStore.totalConversations} conversation(s)`"
          severity="info"
        />
      </div>
      <div class="flex items-center gap-2">
        <!-- Search -->
        <IconField>
          <InputIcon class="pi pi-search" />
          <InputText
            v-model="searchQuery"
            placeholder="Rechercher..."
            class="w-48"
            @keyup.enter="handleSearch"
          />
        </IconField>
        <Button
          label="Sync inbox"
          icon="pi pi-sync"
          class="bg-cyan-500 hover:bg-cyan-600 text-white border-0"
          :loading="messagesStore.isSyncing"
          @click="handleSyncInbox"
        />
      </div>
    </div>

    <!-- Sync result banner -->
    <div
      v-if="messagesStore.lastSyncResult"
      class="mb-4 p-3 rounded-lg flex items-center justify-between"
      :class="messagesStore.lastSyncResult.errors.length > 0 ? 'bg-yellow-50' : 'bg-green-50'"
    >
      <div class="flex items-center gap-2">
        <i
          :class="messagesStore.lastSyncResult.errors.length > 0
            ? 'pi pi-exclamation-triangle text-yellow-600'
            : 'pi pi-check-circle text-green-600'"
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

    <!-- Main content: 2 columns -->
    <div class="grid grid-cols-12 gap-4 min-h-[600px]">
      <!-- Left column: Conversations list -->
      <ConversationsList
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

      <!-- Right column: Messages view -->
      <MessagesView
        ref="messagesViewRef"
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
