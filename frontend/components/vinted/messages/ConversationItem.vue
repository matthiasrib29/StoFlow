<template>
  <div
    class="conversation-item p-3 border-b border-gray-50 cursor-pointer hover:bg-gray-50 transition-colors"
    :class="{
      'bg-cyan-50': isSelected,
      'bg-blue-50/50': conversation.is_unread && !isSelected
    }"
    @click="$emit('select', conversation)"
  >
    <div class="flex items-start gap-3">
      <!-- Avatar -->
      <div class="relative flex-shrink-0">
        <img
          v-if="conversation.opposite_user?.photo_url"
          :src="conversation.opposite_user.photo_url"
          :alt="conversation.opposite_user.login || 'User'"
          class="w-10 h-10 rounded-full object-cover"
        >
        <div v-else class="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
          <i class="pi pi-user text-gray-500" />
        </div>
        <!-- Unread indicator -->
        <div
          v-if="conversation.is_unread"
          class="absolute -top-1 -right-1 w-3 h-3 bg-cyan-500 rounded-full border-2 border-white"
        />
      </div>

      <!-- Content -->
      <div class="flex-1 min-w-0">
        <div class="flex items-center justify-between">
          <span
            class="font-semibold text-secondary-900 truncate"
            :class="{ 'text-cyan-700': conversation.is_unread }"
          >
            {{ conversation.opposite_user?.login || 'Utilisateur' }}
          </span>
          <span class="text-xs text-gray-400">
            {{ formatRelativeTime(conversation.updated_at) }}
          </span>
        </div>
        <p class="text-sm text-gray-600 truncate mt-0.5">
          {{ conversation.last_message_preview || 'Pas de message' }}
        </p>
        <!-- Item info -->
        <div v-if="conversation.item" class="flex items-center gap-1 mt-1">
          <img
            v-if="conversation.item.photo_url"
            :src="conversation.item.photo_url"
            :alt="conversation.item.title || 'Item'"
            class="w-5 h-5 rounded object-cover"
          >
          <span class="text-xs text-gray-400 truncate">
            {{ conversation.item.title || 'Article' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { VintedConversation } from '~/stores/vintedMessages'
import { useVintedMessagesFormatters } from '~/composables/useVintedMessagesFormatters'

interface Props {
  conversation: VintedConversation
  isSelected: boolean
}

defineProps<Props>()

defineEmits<{
  select: [conversation: VintedConversation]
}>()

const { formatRelativeTime } = useVintedMessagesFormatters()
</script>

<style scoped>
.conversation-item:hover {
  transform: translateX(2px);
}

.conversation-item {
  transition: all 0.15s ease;
}
</style>
