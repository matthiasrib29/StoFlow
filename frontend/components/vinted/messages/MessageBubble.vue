<template>
  <div
    class="flex"
    :class="message.is_from_current_user ? 'justify-end' : 'justify-start'"
  >
    <!-- Message bubble -->
    <div
      class="max-w-[70%] rounded-2xl px-4 py-2"
      :class="bubbleClass"
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
        <p v-if="message.offer?.status" class="text-xs opacity-75 mt-1">
          {{ message.offer.status }}
        </p>
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

<script setup lang="ts">
import type { VintedMessage } from '~/stores/vintedMessages'
import { useVintedMessagesFormatters } from '~/composables/useVintedMessagesFormatters'

interface Props {
  message: VintedMessage
}

const props = defineProps<Props>()

const { formatMessageTime, getMessageClass } = useVintedMessagesFormatters()

const bubbleClass = computed(() => getMessageClass(props.message))
</script>
