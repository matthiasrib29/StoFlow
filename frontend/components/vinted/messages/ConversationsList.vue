<template>
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
          @click="$emit('toggle-unread-filter')"
        />
        <Button
          v-tooltip.top="'Actualiser'"
          icon="pi pi-refresh"
          class="bg-gray-100 text-gray-600 border-0"
          size="small"
          text
          :loading="isLoading"
          @click="$emit('refresh')"
        />
      </div>
    </div>

    <!-- Conversations list -->
    <div class="flex-1 overflow-y-auto">
      <!-- Loading -->
      <div v-if="isLoading && conversations.length === 0" class="p-4">
        <Skeleton height="60px" class="mb-2" />
        <Skeleton height="60px" class="mb-2" />
        <Skeleton height="60px" />
      </div>

      <!-- Empty state -->
      <div v-else-if="conversations.length === 0" class="p-6 text-center">
        <i class="pi pi-inbox text-4xl text-gray-300 mb-3" />
        <p class="text-gray-500">Aucune conversation</p>
        <p class="text-sm text-gray-400 mt-1">
          Cliquez sur "Sync inbox" pour récupérer vos messages
        </p>
      </div>

      <!-- List -->
      <div v-else>
        <ConversationItem
          v-for="conv in conversations"
          :key="conv.id"
          :conversation="conv"
          :is-selected="selectedConversationId === conv.id"
          @select="$emit('select', $event)"
        />

        <!-- Load more -->
        <div v-if="hasMore" class="p-3 text-center">
          <Button
            label="Charger plus"
            class="bg-gray-100 text-gray-700 border-0"
            size="small"
            :loading="isLoading"
            @click="$emit('load-more')"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { VintedConversation } from '~/stores/vintedMessages'
import ConversationItem from './ConversationItem.vue'

interface Props {
  conversations: VintedConversation[]
  selectedConversationId: number | null
  showUnreadOnly: boolean
  isLoading: boolean
  hasMore: boolean
}

defineProps<Props>()

defineEmits<{
  select: [conversation: VintedConversation]
  refresh: []
  'toggle-unread-filter': []
  'load-more': []
}>()
</script>
