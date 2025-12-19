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
          :class="messagesStore.lastSyncResult.errors.length > 0 ? 'pi pi-exclamation-triangle text-yellow-600' : 'pi pi-check-circle text-green-600'"
        />
        <span class="text-sm">
          {{ messagesStore.lastSyncResult.synced }} conversation(s) synchronisée(s)
          ({{ messagesStore.lastSyncResult.created }} nouvelle(s), {{ messagesStore.lastSyncResult.updated }} mise(s) à jour)
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
      <div class="col-span-4 bg-white rounded-xl border border-gray-100 overflow-hidden flex flex-col">
        <!-- Conversations header -->
        <div class="p-3 border-b border-gray-100 flex items-center justify-between bg-gray-50">
          <span class="font-semibold text-secondary-900">Conversations</span>
          <div class="flex items-center gap-1">
            <Button
              v-tooltip.top="'Non lus seulement'"
              :icon="showUnreadOnly ? 'pi pi-envelope' : 'pi pi-envelope-open'"
              :class="showUnreadOnly ? 'bg-cyan-100 text-cyan-700' : 'bg-gray-100 text-gray-600'"
              class="border-0"
              size="small"
              text
              @click="toggleUnreadFilter"
            />
            <Button
              v-tooltip.top="'Actualiser'"
              icon="pi pi-refresh"
              class="bg-gray-100 text-gray-600 border-0"
              size="small"
              text
              :loading="messagesStore.isLoadingConversations"
              @click="loadConversations"
            />
          </div>
        </div>

        <!-- Conversations list -->
        <div class="flex-1 overflow-y-auto">
          <!-- Loading -->
          <div v-if="messagesStore.isLoadingConversations && messagesStore.conversations.length === 0" class="p-4">
            <Skeleton height="60px" class="mb-2" />
            <Skeleton height="60px" class="mb-2" />
            <Skeleton height="60px" />
          </div>

          <!-- Empty state -->
          <div v-else-if="messagesStore.conversations.length === 0" class="p-6 text-center">
            <i class="pi pi-inbox text-4xl text-gray-300 mb-3" />
            <p class="text-gray-500">Aucune conversation</p>
            <p class="text-sm text-gray-400 mt-1">Cliquez sur "Sync inbox" pour récupérer vos messages</p>
          </div>

          <!-- List -->
          <div v-else>
            <div
              v-for="conv in messagesStore.conversations"
              :key="conv.id"
              class="conversation-item p-3 border-b border-gray-50 cursor-pointer hover:bg-gray-50 transition-colors"
              :class="{
                'bg-cyan-50': selectedConversationId === conv.id,
                'bg-blue-50/50': conv.is_unread && selectedConversationId !== conv.id
              }"
              @click="selectConversation(conv)"
            >
              <div class="flex items-start gap-3">
                <!-- Avatar -->
                <div class="relative flex-shrink-0">
                  <img
                    v-if="conv.opposite_user?.photo_url"
                    :src="conv.opposite_user.photo_url"
                    :alt="conv.opposite_user.login || 'User'"
                    class="w-10 h-10 rounded-full object-cover"
                  >
                  <div v-else class="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
                    <i class="pi pi-user text-gray-500" />
                  </div>
                  <!-- Unread indicator -->
                  <div
                    v-if="conv.is_unread"
                    class="absolute -top-1 -right-1 w-3 h-3 bg-cyan-500 rounded-full border-2 border-white"
                  />
                </div>

                <!-- Content -->
                <div class="flex-1 min-w-0">
                  <div class="flex items-center justify-between">
                    <span class="font-semibold text-secondary-900 truncate" :class="{ 'text-cyan-700': conv.is_unread }">
                      {{ conv.opposite_user?.login || 'Utilisateur' }}
                    </span>
                    <span class="text-xs text-gray-400">
                      {{ formatRelativeTime(conv.updated_at) }}
                    </span>
                  </div>
                  <p class="text-sm text-gray-600 truncate mt-0.5">
                    {{ conv.last_message_preview || 'Pas de message' }}
                  </p>
                  <!-- Item info -->
                  <div v-if="conv.item" class="flex items-center gap-1 mt-1">
                    <img
                      v-if="conv.item.photo_url"
                      :src="conv.item.photo_url"
                      :alt="conv.item.title || 'Item'"
                      class="w-5 h-5 rounded object-cover"
                    >
                    <span class="text-xs text-gray-400 truncate">{{ conv.item.title || 'Article' }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Load more -->
            <div v-if="messagesStore.hasMoreConversations" class="p-3 text-center">
              <Button
                label="Charger plus"
                class="bg-gray-100 text-gray-700 border-0"
                size="small"
                :loading="messagesStore.isLoadingConversations"
                @click="loadMoreConversations"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Right column: Messages view -->
      <div class="col-span-8 bg-white rounded-xl border border-gray-100 overflow-hidden flex flex-col">
        <!-- No conversation selected -->
        <div v-if="!selectedConversationId" class="flex-1 flex items-center justify-center bg-gray-50">
          <div class="text-center">
            <i class="pi pi-comments text-6xl text-gray-300 mb-4" />
            <p class="text-gray-500">Sélectionnez une conversation</p>
            <p class="text-sm text-gray-400 mt-1">Les messages apparaîtront ici</p>
          </div>
        </div>

        <!-- Conversation view -->
        <template v-else>
          <!-- Conversation header -->
          <div class="p-4 border-b border-gray-100 flex items-center justify-between bg-gray-50">
            <div class="flex items-center gap-3">
              <img
                v-if="messagesStore.currentConversation?.opposite_user?.photo_url"
                :src="messagesStore.currentConversation.opposite_user.photo_url"
                :alt="messagesStore.currentConversation.opposite_user.login || 'User'"
                class="w-10 h-10 rounded-full object-cover"
              >
              <div v-else class="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
                <i class="pi pi-user text-gray-500" />
              </div>
              <div>
                <p class="font-semibold text-secondary-900">
                  {{ messagesStore.currentConversation?.opposite_user?.login || 'Utilisateur' }}
                </p>
                <p v-if="messagesStore.currentConversation?.item" class="text-xs text-gray-500">
                  {{ messagesStore.currentConversation.item.title }}
                </p>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <Button
                v-tooltip.top="'Synchroniser les messages'"
                icon="pi pi-sync"
                class="bg-cyan-100 text-cyan-700 border-0"
                size="small"
                :loading="messagesStore.isLoadingMessages"
                @click="syncCurrentConversation"
              />
              <Button
                v-if="messagesStore.currentConversation?.transaction_id"
                v-tooltip.top="'Voir la transaction'"
                icon="pi pi-external-link"
                class="bg-gray-100 text-gray-600 border-0"
                size="small"
                @click="openTransaction"
              />
            </div>
          </div>

          <!-- Messages list -->
          <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
            <!-- Loading -->
            <div v-if="messagesStore.isLoadingMessages && messagesStore.currentMessages.length === 0" class="space-y-3">
              <div class="flex justify-start">
                <Skeleton width="60%" height="50px" class="rounded-lg" />
              </div>
              <div class="flex justify-end">
                <Skeleton width="40%" height="50px" class="rounded-lg" />
              </div>
            </div>

            <!-- No messages -->
            <div v-else-if="messagesStore.currentMessages.length === 0" class="text-center py-8">
              <i class="pi pi-comments text-4xl text-gray-300 mb-3" />
              <p class="text-gray-500">Aucun message</p>
              <p class="text-sm text-gray-400 mt-1">Cliquez sur le bouton sync pour récupérer les messages</p>
            </div>

            <!-- Messages -->
            <template v-else>
              <div
                v-for="message in messagesStore.currentMessages"
                :key="message.id"
                class="flex"
                :class="message.is_from_current_user ? 'justify-end' : 'justify-start'"
              >
                <!-- Message bubble -->
                <div
                  class="max-w-[70%] rounded-2xl px-4 py-2"
                  :class="getMessageClass(message)"
                >
                  <!-- Regular message -->
                  <template v-if="message.entity_type === 'message'">
                    <p class="text-sm whitespace-pre-wrap">{{ message.body }}</p>
                  </template>

                  <!-- Offer message -->
                  <template v-else-if="message.entity_type === 'offer_request_message'">
                    <div class="flex items-center gap-2 mb-1">
                      <i class="pi pi-tag text-sm" />
                      <span class="font-semibold">Offre: {{ message.offer?.price }}€</span>
                    </div>
                    <p v-if="message.title" class="text-sm">{{ message.title }}</p>
                    <p v-if="message.offer?.status" class="text-xs opacity-75 mt-1">{{ message.offer.status }}</p>
                  </template>

                  <!-- Status message -->
                  <template v-else-if="message.entity_type === 'status_message'">
                    <div class="text-center">
                      <p class="font-semibold text-sm">{{ message.title }}</p>
                      <p v-if="message.subtitle" class="text-xs opacity-75">{{ message.subtitle }}</p>
                    </div>
                  </template>

                  <!-- Action message -->
                  <template v-else-if="message.entity_type === 'action_message'">
                    <div class="text-center">
                      <i class="pi pi-info-circle mr-1" />
                      <span class="text-sm">{{ message.title || message.subtitle }}</span>
                    </div>
                  </template>

                  <!-- Timestamp -->
                  <p class="text-xs mt-1 opacity-60">
                    {{ formatMessageTime(message.created_at) }}
                  </p>
                </div>
              </div>
            </template>
          </div>

          <!-- Note: Response not implemented yet -->
          <div class="p-3 border-t border-gray-100 bg-gray-50">
            <p class="text-center text-sm text-gray-400">
              <i class="pi pi-info-circle mr-1" />
              La réponse aux messages n'est pas encore disponible
            </p>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useVintedMessagesStore, type VintedConversation, type VintedMessage } from '~/stores/vintedMessages'
import { useToast } from 'primevue/usetoast'

const messagesStore = useVintedMessagesStore()
const toast = import.meta.client ? useToast() : null

// Local state
const selectedConversationId = ref<number | null>(null)
const showUnreadOnly = ref(false)
const searchQuery = ref('')
const messagesContainer = ref<HTMLElement | null>(null)

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
    scrollToBottom()
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
    scrollToBottom()
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
    // TODO: Display search results in a modal or panel
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

/**
 * Scroll messages to bottom
 */
function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

/**
 * Get message bubble class based on type and sender
 */
function getMessageClass(message: VintedMessage): string {
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

/**
 * Format relative time
 */
function formatRelativeTime(dateStr: string | null): string {
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
function formatMessageTime(dateStr: string | null): string {
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
</script>

<style scoped>
.vinted-messages {
  min-height: 700px;
}

.conversation-item:hover {
  transform: translateX(2px);
}

.conversation-item {
  transition: all 0.15s ease;
}
</style>
