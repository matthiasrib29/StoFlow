<template>
  <div class="bg-gradient-to-r from-primary-50 to-blue-50 border border-primary-200 rounded-lg p-4 mb-4">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="bg-primary-100 rounded-full p-2">
          <i class="pi pi-sparkles text-primary-600 text-lg" />
        </div>
        <div>
          <h4 class="text-sm font-semibold text-primary-900">Remplissage automatique</h4>
          <p class="text-xs text-primary-700">L'IA analyse vos photos et remplit le formulaire</p>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <!-- AI Credits Display -->
        <div v-if="aiCreditsRemaining !== null" class="flex items-center gap-1.5 text-sm">
          <i class="pi pi-bolt" :class="aiCreditsRemaining > 0 ? 'text-primary-600' : 'text-red-500'" />
          <span :class="aiCreditsRemaining > 0 ? 'text-primary-700' : 'text-red-600'">
            {{ aiCreditsRemaining }} crédit{{ aiCreditsRemaining !== 1 ? 's' : '' }}
          </span>
        </div>
        <Button
          type="button"
          label="Remplir avec l'IA"
          icon="pi pi-sparkles"
          class="bg-primary-500 hover:bg-primary-600 text-white border-0 font-semibold"
          :loading="loading"
          :disabled="loading || aiCreditsRemaining === 0"
          @click="$emit('analyze')"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  aiCreditsRemaining: number | null
  loading: boolean
}>()

defineEmits<{
  analyze: []
}>()
</script>
