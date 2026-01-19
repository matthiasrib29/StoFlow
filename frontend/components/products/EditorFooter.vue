<template>
  <div class="fixed bottom-0 left-0 right-0 md:left-64 bg-white/95 backdrop-blur-sm border-t border-gray-200 p-4 z-40 shadow-lg">
    <div class="flex items-center justify-between max-w-4xl mx-auto">
      <!-- Left side: Progress and info -->
      <div class="flex items-center gap-4">
        <!-- Progress indicator -->
        <div class="flex items-center gap-2 text-sm">
          <i
            class="pi pi-check-circle"
            :class="canPublish ? 'text-green-500' : 'text-gray-400'"
          />
          <span class="text-gray-500">{{ filledCount }}/{{ totalCount }}</span>

          <!-- Missing fields warning -->
          <span
            v-if="missingFields.length > 0 || !hasPhotos"
            class="text-orange-500 flex items-center gap-1"
          >
            <i class="pi pi-exclamation-triangle text-xs" />
            <span class="text-xs">
              Manque :
              <span
                v-if="missingFields.length > 0"
                v-tooltip.top="missingFields.length > 3 ? missingFields.join(', ') : undefined"
                :class="{ 'cursor-help': missingFields.length > 3 }"
              >
                {{ missingFields.slice(0, 3).join(', ') }}
                <span v-if="missingFields.length > 3" class="underline decoration-dotted">
                  +{{ missingFields.length - 3 }}
                </span>
              </span>
              <template v-if="missingFields.length > 0 && !hasPhotos">, </template>
              <template v-if="!hasPhotos">Photo</template>
            </span>
          </span>

          <!-- All complete - ready to publish -->
          <span v-else class="text-green-500 flex items-center gap-1 text-xs">
            <i class="pi pi-check text-xs" />
            Prêt à publier
          </span>
        </div>

        <!-- Draft saved indicator (create mode only) -->
        <div v-if="showDraft && hasDraft && lastSaved" class="flex items-center gap-2 text-xs text-gray-400">
          <i class="pi pi-save" />
          <span>Brouillon {{ formatLastSaved() }}</span>
          <button
            class="text-red-400 hover:text-red-500 underline transition-colors"
            title="Effacer le brouillon"
            @click="$emit('clear-draft')"
          >
            Effacer
          </button>
        </div>
      </div>

      <!-- Right side: Actions -->
      <div class="flex items-center gap-3">
        <Button
          type="button"
          label="Annuler"
          icon="pi pi-times"
          class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
          @click="$emit('cancel')"
        />
        <!-- Save as Draft button -->
        <Button
          type="button"
          label="Brouillon"
          icon="pi pi-save"
          class="bg-gray-100 hover:bg-gray-200 text-secondary-900 border border-gray-300"
          :loading="isSubmitting && !isPublishing"
          :disabled="!canSaveDraft"
          @click="$emit('save-draft')"
        />
        <!-- Publish button -->
        <Button
          type="button"
          label="Publier"
          icon="pi pi-send"
          class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-bold"
          :loading="isSubmitting && isPublishing"
          :disabled="!canPublish"
          @click="$emit('publish')"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  filledCount: number
  totalCount: number
  missingFields: string[]
  hasPhotos: boolean
  progress: number
  canPublish: boolean
  canSaveDraft: boolean
  isSubmitting: boolean
  isPublishing?: boolean
  // Draft props (optional, for create mode)
  showDraft?: boolean
  hasDraft?: boolean
  lastSaved?: Date | null
  formatLastSaved?: () => string
}

withDefaults(defineProps<Props>(), {
  isPublishing: false,
  showDraft: false,
  hasDraft: false,
  lastSaved: null,
  formatLastSaved: () => ''
})

defineEmits<{
  'save-draft': []
  'publish': []
  'cancel': []
  'clear-draft': []
}>()
</script>
