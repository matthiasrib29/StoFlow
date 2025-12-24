<template>
  <div class="col-span-full lg:col-span-8 bg-white rounded-xl border border-gray-100 overflow-hidden flex flex-col">
    <!-- No conversation selected -->
    <div v-if="!conversation" class="flex-1 flex items-center justify-center bg-gray-50">
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
            v-if="conversation.opposite_user?.photo_url"
            :src="conversation.opposite_user.photo_url"
            :alt="conversation.opposite_user.login || 'User'"
            class="w-10 h-10 rounded-full object-cover"
          >
          <div v-else class="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
            <i class="pi pi-user text-gray-500" />
          </div>
          <div>
            <p class="font-semibold text-secondary-900">
              {{ conversation.opposite_user?.login || 'Utilisateur' }}
            </p>
            <p v-if="conversation.item" class="text-xs text-gray-500">
              {{ conversation.item.title }}
            </p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <Button
            v-tooltip.top="'Synchroniser les messages'"
            icon="pi pi-sync"
            class="bg-primary-100 text-primary-700 border-0"
            size="small"
            :loading="isLoadingMessages"
            @click="$emit('sync')"
          />
          <Button
            v-if="conversation.transaction_id"
            v-tooltip.top="'Voir la transaction'"
            icon="pi pi-external-link"
            class="bg-gray-100 text-gray-600 border-0"
            size="small"
            @click="$emit('open-transaction')"
          />
        </div>
      </div>

      <!-- Messages list -->
      <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
        <!-- Loading -->
        <div v-if="isLoadingMessages && messages.length === 0" class="space-y-3">
          <div class="flex justify-start">
            <Skeleton width="60%" height="50px" class="rounded-lg" />
          </div>
          <div class="flex justify-end">
            <Skeleton width="40%" height="50px" class="rounded-lg" />
          </div>
        </div>

        <!-- No messages -->
        <div v-else-if="messages.length === 0" class="text-center py-8">
          <i class="pi pi-comments text-4xl text-gray-300 mb-3" />
          <p class="text-gray-500">Aucun message</p>
          <p class="text-sm text-gray-400 mt-1">
            Cliquez sur le bouton sync pour récupérer les messages
          </p>
        </div>

        <!-- Messages -->
        <template v-else>
          <MessageBubble
            v-for="message in messages"
            :key="message.id"
            :message="message"
          />
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
</template>

<script setup lang="ts">
import type { VintedConversation, VintedMessage } from '~/stores/vintedMessages'
import MessageBubble from './MessageBubble.vue'

interface Props {
  conversation: VintedConversation | null
  messages: VintedMessage[]
  isLoadingMessages: boolean
}

defineProps<Props>()

defineEmits<{
  sync: []
  'open-transaction': []
}>()

const messagesContainer = ref<HTMLElement | null>(null)

/**
 * Scroll messages to bottom
 */
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// Expose scrollToBottom for parent component
defineExpose({ scrollToBottom })
</script>
