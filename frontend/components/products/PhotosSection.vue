<template>
  <div
    class="sticky-photos-container bg-white z-30 transition-all duration-300"
    :class="{ 'sticky-shrink': compact }"
  >
    <!-- Photo Section Title (visible only when not compact) -->
    <div v-if="!compact" class="flex items-center justify-between mb-2">
      <h3 class="text-base font-bold text-secondary-900 flex items-center gap-2">
        <i class="pi pi-images" />
        Photos du produit *
        <span class="font-normal text-sm text-gray-500">(min. 1)</span>
        <span class="text-sm font-normal text-gray-400">{{ totalCount }}/{{ maxPhotos }}</span>
      </h3>

      <button
        type="button"
        class="flex items-center gap-2 bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold px-3 py-1.5 rounded-md transition-colors"
        :disabled="!canAddMore"
        @click="$emit('add')"
      >
        <i class="pi pi-plus" />
        <span>Ajouter</span>
      </button>
    </div>

    <!-- Photos Section -->
    <ProductsPhotoUploader
      ref="photoUploader"
      v-model:photos="localPhotos"
      v-model:existing-images="localExistingImages"
      :compact="compact"
      :max-photos="maxPhotos"
      @remove-existing="$emit('remove-existing', $event)"
      @reorder="$emit('reorder', $event)"
    />
  </div>
</template>

<script setup lang="ts">
interface Photo {
  file: File
  preview: string
}

interface ExistingImage {
  id: number
  url: string
  position: number
}

interface Props {
  photos: Photo[]
  existingImages?: ExistingImage[]
  compact?: boolean
  maxPhotos?: number
}

const props = withDefaults(defineProps<Props>(), {
  existingImages: () => [],
  compact: false,
  maxPhotos: 20
})

const emit = defineEmits<{
  'update:photos': [photos: Photo[]]
  'update:existingImages': [images: ExistingImage[]]
  'remove-existing': [imageId: number]
  'reorder': [order: { existingImages: ExistingImage[]; photos: Photo[] }]
  'add': []
}>()

// Local state for v-model
const localPhotos = computed({
  get: () => props.photos,
  set: (value) => emit('update:photos', value)
})

const localExistingImages = computed({
  get: () => props.existingImages,
  set: (value) => emit('update:existingImages', value)
})

// Computed
const totalCount = computed(() => props.photos.length + props.existingImages.length)
const hasPhotos = computed(() => totalCount.value > 0)
const canAddMore = computed(() => totalCount.value < props.maxPhotos)

// Photo uploader ref
const photoUploader = ref<{ openFileSelector: () => void } | null>(null)

// Expose method to open file selector
const openFileSelector = () => {
  if (photoUploader.value) {
    photoUploader.value.openFileSelector()
  }
}

defineExpose({
  openFileSelector
})
</script>

<style scoped>
.sticky-photos-container {
  position: sticky;
  top: 0;
  padding: 0.5rem 1.5rem 0.25rem;
  margin-bottom: 0;
  border-bottom: 1px solid transparent;
  transition: all 0.3s ease;
  z-index: 30;
}

.sticky-photos-container.sticky-shrink {
  padding: 0.5rem 1.5rem 0;
  margin-bottom: 0;
  border-bottom-color: #e5e7eb;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  background-color: white;
}
</style>
