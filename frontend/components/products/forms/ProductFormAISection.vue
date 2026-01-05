<template>
  <div
    v-if="productId && hasImages"
    class="bg-gradient-to-r from-primary-50 to-blue-50 border border-primary-200 rounded-lg p-4 mb-4"
  >
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="bg-primary-100 rounded-full p-2">
          <i class="pi pi-sparkles text-primary-600 text-lg" />
        </div>
        <div>
          <h4 class="text-sm font-semibold text-primary-900">Remplissage automatique</h4>
          <p class="text-xs text-primary-700">Analysez les images pour remplir le formulaire automatiquement</p>
        </div>
      </div>
      <Button
        type="button"
        label="Remplir avec l'IA"
        icon="pi pi-sparkles"
        class="p-button-primary"
        :loading="isAnalyzing"
        :disabled="isAnalyzing || isGenerating"
        @click="$emit('analyze')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  productId?: number
  hasImages: boolean
  isAnalyzing: boolean
  isGenerating: boolean
}>()

defineEmits<{
  analyze: []
}>()
</script>
