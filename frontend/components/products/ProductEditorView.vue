<template>
  <!-- Loading (edit mode only) -->
  <div v-if="mode === 'edit' && editor.isLoading.value" class="p-6 flex items-center justify-center py-20">
    <ProgressSpinner />
  </div>

  <!-- Product not found (edit mode only) -->
  <div v-else-if="mode === 'edit' && !editor.product.value" class="p-6 text-center py-20">
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

  <!-- Editor Form -->
  <ProductsProductEditorPage
      v-else
      :title="mode === 'create' ? 'Créer un produit' : 'Modifier le produit'"
      :subtitle="mode === 'edit' ? editor.product.value?.title : undefined"
      :submit-label="mode === 'create' ? 'Créer le produit' : 'Enregistrer les modifications'"
      :show-progress-bar="true"
      :show-draft="mode === 'create'"
      :has-draft="mode === 'create' ? (editor.draft?.hasDraft.value || false) : false"
      :last-saved="mode === 'create' ? (editor.draft?.lastSaved.value || null) : null"
      :format-last-saved="mode === 'create' ? (editor.draft?.formatLastSaved || (() => '')) : (() => '')"
      :product-id="productId"
      :form="editor.form.value"
      :photos="editor.images.photos.value"
      :existing-images="mode === 'edit' ? editor.images.existingImages.value : []"
      :ai-credits-remaining="editor.aiCreditsRemaining.value"
      :is-analyzing="editor.ai.isAnalyzing.value"
      :filled-count="editor.filledRequiredCount.value"
      :total-count="editor.totalRequiredCount"
      :missing-fields="editor.missingFields.value"
      :progress="editor.formProgress.value"
      :can-publish="editor.canPublish.value"
      :can-save-draft="editor.canSaveDraft.value"
      :is-publishing="editor.isPublishing.value"
      :form-sections="editor.formSections.value"
      :is-scrolled="editor.isScrolled.value"
      :is-submitting="editor.isSubmitting.value"
      @update:form="editor.handleFormUpdate"
      @update:photos="handlePhotosUpdate"
      @update:existing-images="handleExistingImagesUpdate"
      @remove-existing="handleRemoveExisting"
      @reorder="editor.images.handleReorder"
      @analyze="editor.analyzeWithAI"
      @save-draft="handleSaveDraft"
      @publish="handlePublish"
      @cancel="handleCancel"
      @navigate="editor.scrollToSection"
      @clear-draft="editor.clearDraftAndReset"
    >
      <template #pricing>
        <!-- Pricing Section -->
        <div class="mt-6 bg-white rounded-xl shadow-sm border border-gray-100 p-4">
          <!-- Header -->
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-base font-bold text-secondary-900 flex items-center gap-2">
              <i class="pi pi-calculator" />
              Prix
            </h3>
            <Button
              v-if="editor.form.value.brand && editor.form.value.category && editor.form.value.condition !== null"
              label="Calculer suggestions"
              icon="pi pi-refresh"
              class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
              size="small"
              :loading="editor.pricing.isLoading.value"
              @click="editor.calculatePrice"
            />
          </div>

          <!-- Price Input Field -->
          <div class="mb-4">
            <label for="price" class="block text-xs font-semibold mb-1 text-secondary-900">
              Prix de vente (EUR)
            </label>
            <InputNumber
              id="price"
              :model-value="editor.form.value.price"
              mode="currency"
              currency="EUR"
              locale="fr-FR"
              class="w-full"
              :min="0"
              :min-fraction-digits="2"
              placeholder="Entrer le prix de vente"
              @update:model-value="editor.handleFormUpdate({ ...editor.form.value, price: $event })"
            />
          </div>

          <!-- Loading state -->
          <div v-if="editor.pricing.isLoading.value" class="flex items-center justify-center py-6 border-t border-gray-100 mt-4">
            <i class="pi pi-spin pi-spinner text-xl text-primary-500 mr-3" />
            <span class="text-gray-600">Calcul du prix recommandé...</span>
          </div>

          <!-- Pricing Suggestions Display -->
          <div v-else-if="editor.form.value.brand && editor.form.value.category && editor.form.value.condition !== null">
            <ProductsPricingDisplay
              v-if="editor.pricing.priceResult.value"
              :pricing="editor.pricing.priceResult.value"
            />

            <!-- No pricing yet -->
            <div v-else class="text-center py-4 text-gray-500 border-t border-gray-100 mt-4">
              <i class="pi pi-info-circle text-xl mb-2" />
              <p class="text-sm">Cliquez sur "Calculer suggestions" pour obtenir des prix suggérés</p>
            </div>

            <!-- Error -->
            <div v-if="editor.pricing.error.value" class="mt-3 p-3 bg-red-50 rounded-lg text-red-700 text-sm">
              {{ editor.pricing.error.value }}
            </div>
          </div>

          <!-- Message if missing required fields -->
          <div v-else class="text-center py-4 text-gray-500 border-t border-gray-100 mt-4">
            <i class="pi pi-exclamation-circle text-xl mb-2" />
            <p class="text-sm">Remplissez marque, catégorie et état pour obtenir des suggestions de prix</p>
          </div>
        </div>
      </template>
    </ProductsProductEditorPage>
</template>

<script setup lang="ts">
import { useProductEditor } from '~/composables/useProductEditor'
import type { Photo, ExistingImage } from '~/composables/useProductImages'

interface Props {
  mode: 'create' | 'edit'
  productId?: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  success: [product: any]
  cancel: []
}>()

const router = useRouter()

// Initialize the product editor based on mode
const editor = useProductEditor({
  mode: props.mode,
  productId: props.productId
})

// Handle photos update
const handlePhotosUpdate = (newPhotos: Photo[]) => {
  editor.images.photos.value = newPhotos
}

// Handle existing images update (edit mode only)
const handleExistingImagesUpdate = (newImages: ExistingImage[]) => {
  if (props.mode === 'edit') {
    editor.images.existingImages.value = newImages
  }
}

// Handle remove existing image (edit mode only)
const handleRemoveExisting = (imageId: number) => {
  if (props.mode === 'edit') {
    editor.images.removeExistingImage(imageId)
  }
}

// Handle save as draft
const handleSaveDraft = async () => {
  const product = await editor.handleSaveDraft()
  if (product) {
    emit('success', product)
  }
}

// Handle publish
const handlePublish = async () => {
  const product = await editor.handlePublish()
  if (product) {
    emit('success', product)
  }
}

// Handle cancel
const handleCancel = () => {
  emit('cancel')
}

// Initialize on mount
onMounted(async () => {
  if (props.mode === 'create') {
    await editor.initialize()
  } else {
    await editor.loadProduct()
  }
})

// Cleanup on unmount
onUnmounted(() => {
  editor.cleanup()
})

// Expose editor for parent access if needed
defineExpose({
  editor
})
</script>
