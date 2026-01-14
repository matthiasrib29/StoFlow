<template>
  <ProductsProductEditorPage
    title="Créer un produit"
    submit-label="Créer le produit"
    :form="editor.form.value"
    :photos="editor.images.photos.value"
    :existing-images="[]"
    :ai-credits-remaining="editor.aiCreditsRemaining.value"
    :is-analyzing="editor.ai.isAnalyzing.value"
    :filled-count="editor.filledRequiredCount.value"
    :total-count="editor.totalRequiredCount"
    :missing-fields="editor.missingFields.value"
    :progress="editor.formProgress.value"
    :can-submit="editor.canSubmit.value"
    :form-sections="editor.formSections.value"
    :is-scrolled="editor.isScrolled.value"
    :is-submitting="editor.isSubmitting.value"
    :show-progress-bar="true"
    :show-draft="true"
    :has-draft="editor.draft?.hasDraft.value || false"
    :last-saved="editor.draft?.lastSaved.value || null"
    :format-last-saved="editor.draft?.formatLastSaved || (() => '')"
    @update:form="editor.handleFormUpdate"
    @update:photos="handlePhotosUpdate"
    @analyze="editor.analyzeWithAI"
    @submit="handleSubmit"
    @cancel="router.push('/dashboard/products')"
    @navigate="editor.scrollToSection"
    @clear-draft="editor.clearDraftAndReset"
  >
    <template #pricing>
      <!-- Pricing Section -->
      <div v-if="editor.pricing.priceResult.value || editor.pricing.isLoading.value" class="mt-6 bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div v-if="editor.pricing.isLoading.value" class="flex items-center justify-center py-8">
          <i class="pi pi-spin pi-spinner text-2xl text-primary-500 mr-3" />
          <span class="text-gray-600">Calcul du prix recommandé...</span>
        </div>
        <template v-else-if="editor.pricing.priceResult.value">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <i class="pi pi-calculator text-primary-500" />
              Prix recommandé
            </h3>
            <button
              type="button"
              class="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
              @click="editor.calculatePrice"
            >
              <i class="pi pi-refresh" />
              Recalculer
            </button>
          </div>
          <ProductsPricingDisplay
            :pricing="editor.pricing.priceResult.value"
          />
        </template>
      </div>

      <!-- Manual Pricing Button (when no result yet and form has required fields) -->
      <div
        v-else-if="editor.form.value.brand && editor.form.value.category && !editor.pricing.isLoading.value"
        class="mt-6 bg-gradient-to-r from-primary-50 to-primary-100 border border-primary-200 rounded-lg p-4"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="bg-primary-100 rounded-full p-2">
              <i class="pi pi-calculator text-primary-600 text-lg" />
            </div>
            <div>
              <h4 class="text-sm font-semibold text-secondary-900">Estimation de prix</h4>
              <p class="text-xs text-gray-600">Calculer le prix recommandé basé sur les attributs</p>
            </div>
          </div>
          <Button
            type="button"
            label="Calculer le prix"
            icon="pi pi-calculator"
            class="btn-primary"
            :loading="editor.pricing.isLoading.value"
            @click="editor.calculatePrice"
          />
        </div>
      </div>
    </template>
  </ProductsProductEditorPage>
</template>

<script setup lang="ts">
import { useProductEditor } from '~/composables/useProductEditor'
import type { Photo } from '~/composables/useProductImages'

definePageMeta({
  layout: 'dashboard'
})

const router = useRouter()

// Initialize the product editor in create mode
const editor = useProductEditor({ mode: 'create' })

// Handle photos update from component
const handlePhotosUpdate = (newPhotos: Photo[]) => {
  editor.images.photos.value = newPhotos
}

// Handle form submission
const handleSubmit = async () => {
  const product = await editor.handleSubmit()
  if (product) {
    router.push('/dashboard/products')
  }
}

// Initialize on mount
onMounted(async () => {
  await editor.initialize()
})

// Cleanup on unmount
onUnmounted(() => {
  editor.cleanup()
})
</script>
