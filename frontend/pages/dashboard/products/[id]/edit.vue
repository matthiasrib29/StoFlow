<template>
  <div class="p-6">
    <!-- Loading -->
    <div v-if="editor.isLoading.value" class="flex items-center justify-center py-20">
      <ProgressSpinner />
    </div>

    <!-- Product not found -->
    <div v-else-if="!editor.product.value" class="text-center py-20">
      <i class="pi pi-exclamation-circle text-gray-300 text-6xl mb-4" />
      <h2 class="text-2xl font-bold text-secondary-900 mb-2">Produit introuvable</h2>
      <p class="text-gray-600 mb-6">Ce produit n'existe pas ou a été supprimé</p>
      <Button
        label="Retour aux produits"
        icon="pi pi-arrow-left"
        class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
        @click="$router.push('/dashboard/products')"
      />
    </div>

    <!-- Edit Form -->
    <ProductsProductEditorPage
      v-else
      title="Modifier le produit"
      :subtitle="editor.product.value.title"
      submit-label="Enregistrer les modifications"
      :show-back-button="true"
      :show-progress-bar="false"
      :product-id="productId"
      :form="editor.form.value"
      :photos="editor.images.photos.value"
      :existing-images="editor.images.existingImages.value"
      :ai-credits-remaining="editor.aiCreditsRemaining.value"
      :is-analyzing="editor.ai.isAnalyzing.value"
      :filled-count="editor.filledRequiredCount.value"
      :total-count="editor.totalRequiredCount"
      :missing-fields="editor.missingFields.value"
      :progress="editor.formProgress.value"
      :can-submit="editor.canSubmit.value"
      :form-sections="editor.formSections.value"
      :is-scrolled="false"
      :is-submitting="editor.isSubmitting.value"
      @update:form="editor.handleFormUpdate"
      @update:photos="handlePhotosUpdate"
      @update:existing-images="handleExistingImagesUpdate"
      @remove-existing="handleRemoveExisting"
      @reorder="editor.images.handleReorder"
      @analyze="editor.analyzeWithAI"
      @submit="handleSubmit"
      @cancel="router.push('/dashboard/products')"
    >
      <template #pricing>
        <!-- Pricing Suggestions Section -->
        <div v-if="editor.form.value.brand && editor.form.value.category && editor.form.value.condition !== null" class="mt-6">
          <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
            <!-- Header with Calculate Button -->
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-base font-bold text-secondary-900 flex items-center gap-2">
                <i class="pi pi-calculator" />
                Prix suggérés
              </h3>
              <Button
                label="Calculer"
                icon="pi pi-refresh"
                class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
                size="small"
                :loading="editor.pricing.isLoading.value"
                @click="editor.calculatePrice"
              />
            </div>

            <!-- Pricing Display -->
            <ProductsPricingDisplay
              v-if="editor.pricing.priceResult.value"
              :pricing="editor.pricing.priceResult.value"
            />

            <!-- No pricing yet -->
            <div v-else-if="!editor.pricing.isLoading.value" class="text-center py-6 text-gray-500">
              <i class="pi pi-info-circle text-2xl mb-2" />
              <p class="text-sm">Cliquez sur "Calculer" pour obtenir des suggestions de prix</p>
            </div>

            <!-- Error -->
            <div v-if="editor.pricing.error.value" class="mt-3 p-3 bg-red-50 rounded-lg text-red-700 text-sm">
              {{ editor.pricing.error.value }}
            </div>
          </div>
        </div>
      </template>
    </ProductsProductEditorPage>
  </div>
</template>

<script setup lang="ts">
import { useProductEditor } from '~/composables/useProductEditor'
import type { Photo, ExistingImage } from '~/composables/useProductImages'

definePageMeta({
  layout: 'dashboard'
})

const route = useRoute()
const router = useRouter()
const { showSuccess } = useAppToast()

const productId = parseInt(route.params.id as string)

// Initialize the product editor in edit mode
const editor = useProductEditor({ mode: 'edit', productId })

// Handle photos update
const handlePhotosUpdate = (newPhotos: Photo[]) => {
  editor.images.photos.value = newPhotos
}

// Handle existing images update
const handleExistingImagesUpdate = (newImages: ExistingImage[]) => {
  editor.images.existingImages.value = newImages
}

// Handle remove existing image
const handleRemoveExisting = (imageId: number) => {
  editor.images.removeExistingImage(imageId)
}

// Handle form submission
const handleSubmit = async () => {
  const product = await editor.handleSubmit()
  if (product) {
    router.push('/dashboard/products')
  }
}

// Load product on mount
onMounted(async () => {
  await editor.loadProduct()
})

// Cleanup on unmount
onUnmounted(() => {
  editor.cleanup()
})
</script>
