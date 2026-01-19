<template>
  <div class="pb-24">
    <!-- Page Header outside sticky container -->
    <div class="px-6 pt-4">
      <PageHeader :title="title" :subtitle="subtitle">
        <template v-if="showBackButton" #actions>
          <Button
            label="Retour"
            icon="pi pi-arrow-left"
            class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
            @click="$emit('cancel')"
          />
        </template>
      </PageHeader>
    </div>

    <!-- Sticky Photos Section -->
    <ProductsPhotosSection
      ref="photosSection"
      :photos="photos"
      :existing-images="existingImages"
      :compact="isScrolled"
      @update:photos="$emit('update:photos', $event)"
      @update:existing-images="$emit('update:existingImages', $event)"
      @remove-existing="$emit('remove-existing', $event)"
      @reorder="$emit('reorder', $event)"
      @add="openPhotoSelector"
    />

    <!-- Content with padding -->
    <div class="px-6">
      <!-- AI Auto-fill Section (visible when photos exist) -->
      <ProductsAiAutoFillSection
        v-if="hasPhotos"
        :ai-credits-remaining="aiCreditsRemaining"
        :loading="isAnalyzing"
        @analyze="$emit('analyze')"
      />

      <!-- Form Section -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <!-- Progress Bar with Navigation -->
        <ProductsFormProgressBar
          v-if="showProgressBar"
          :form-data="form"
          :has-photos="hasPhotos"
          :sections="formSections"
          :active-section="activeSection"
          @navigate="$emit('navigate', $event)"
        />

        <ProductsProductForm
          :model-value="form"
          :is-submitting="isSubmitting"
          :product-id="productId"
          @update:model-value="$emit('update:form', $event)"
        />
      </div>

      <!-- Pricing Section Slot -->
      <slot name="pricing" />
    </div>

    <!-- Sticky Footer -->
    <ProductsEditorFooter
      :filled-count="filledCount"
      :total-count="totalCount"
      :missing-fields="missingFields"
      :has-photos="hasPhotos"
      :progress="progress"
      :can-publish="canPublish"
      :can-save-draft="canSaveDraft"
      :is-submitting="isSubmitting"
      :is-publishing="isPublishing"
      :show-draft="showDraft"
      :has-draft="hasDraft"
      :last-saved="lastSaved"
      :format-last-saved="formatLastSaved"
      @save-draft="$emit('save-draft')"
      @publish="$emit('publish')"
      @cancel="$emit('cancel')"
      @clear-draft="$emit('clear-draft')"
    />
  </div>
</template>

<script setup lang="ts">
import type { ProductFormData } from '~/types/product'

interface Photo {
  file: File
  preview: string
}

interface ExistingImage {
  id: number
  url: string
  position: number
}

interface FormSection {
  id: string
  label: string
  filled: number
  total: number
  isComplete: boolean
}

interface Props {
  // Page
  title: string
  subtitle?: string
  showBackButton?: boolean
  showProgressBar?: boolean
  productId?: number

  // Form
  form: ProductFormData

  // Photos
  photos: Photo[]
  existingImages?: ExistingImage[]

  // AI
  aiCreditsRemaining: number | null
  isAnalyzing: boolean

  // Progress
  filledCount: number
  totalCount: number
  missingFields: string[]
  progress: number
  canPublish: boolean
  canSaveDraft: boolean
  formSections: FormSection[]
  activeSection?: string

  // State
  isScrolled: boolean
  isSubmitting: boolean
  isPublishing?: boolean

  // Draft (optional, for create mode)
  showDraft?: boolean
  hasDraft?: boolean
  lastSaved?: Date | null
  formatLastSaved?: () => string
}

const props = withDefaults(defineProps<Props>(), {
  subtitle: '',
  existingImages: () => [],
  showBackButton: false,
  showProgressBar: true,
  activeSection: 'info',
  isPublishing: false,
  showDraft: false,
  hasDraft: false,
  lastSaved: null,
  formatLastSaved: () => ''
})

const emit = defineEmits<{
  'update:form': [form: ProductFormData]
  'update:photos': [photos: Photo[]]
  'update:existingImages': [images: ExistingImage[]]
  'remove-existing': [imageId: number]
  'reorder': [order: { existingImages: ExistingImage[]; photos: Photo[] }]
  'analyze': []
  'save-draft': []
  'publish': []
  'cancel': []
  'navigate': [sectionId: string]
  'clear-draft': []
}>()

// Computed
const hasPhotos = computed(() => props.photos.length + props.existingImages.length > 0)

// Photos section ref
const photosSection = ref<{ openFileSelector: () => void } | null>(null)

// Open photo selector
const openPhotoSelector = () => {
  if (photosSection.value) {
    photosSection.value.openFileSelector()
  }
}

// Expose for parent
defineExpose({
  openPhotoSelector
})
</script>
