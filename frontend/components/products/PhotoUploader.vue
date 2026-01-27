<template>
  <div
    class="bg-white rounded-lg relative transition-all duration-300"
    :class="compact ? 'p-2' : ''"
    @dragover.prevent="handleDragOver"
    @dragleave.prevent="handleDragLeave"
    @drop.prevent="handleDrop"
  >
    <!-- Drag Overlay for file upload -->
    <transition name="fade">
      <div
        v-if="isDraggingFile"
        class="absolute inset-0 bg-primary-400 bg-opacity-90 rounded-lg z-30 flex items-center justify-center pointer-events-none"
      >
        <div class="text-center">
          <div class="w-32 h-32 mx-auto mb-4 bg-white rounded-full flex items-center justify-center animate-bounce">
            <i class="pi pi-cloud-download text-6xl text-primary-500"/>
          </div>
          <p class="text-2xl font-bold text-secondary-900">Déposez vos photos ici !</p>
        </div>
      </div>
    </transition>

    <!-- Photo Preview Horizontal Scroll with Drag & Drop Reorder -->
    <div v-if="allImages.length > 0" class="flex items-stretch gap-2">
      <!-- Navigation Button Left -->
      <button
        class="flex items-center justify-center w-8 flex-shrink-0 rounded-lg text-secondary-600 hover:text-secondary-900 hover:bg-gray-100 transition-all duration-200"
        :class="canScrollLeft ? 'cursor-pointer' : 'opacity-30 cursor-default'"
        aria-label="Défiler à gauche"
        @click="scrollLeft"
      >
        <i class="pi pi-chevron-left text-xl font-bold"/>
      </button>

      <!-- Photos Container with Draggable -->
      <div
        ref="scrollContainer"
        class="overflow-x-auto scroll-smooth pb-2 hide-scrollbar min-w-0 flex-1"
        @scroll="checkScrollPosition"
      >
        <draggable
          v-model="allImages"
          item-key="key"
          class="flex gap-4 min-w-max"
          :class="compact ? 'px-2' : 'px-4'"
          ghost-class="opacity-50"
          drag-class="rotate-3"
          :animation="200"
          @start="onDragStart"
          @end="onDragEnd"
        >
          <template #item="{ element, index }">
            <div
              class="photo-item relative group rounded-lg overflow-hidden shadow-md flex-shrink-0 hover:shadow-xl transition-all duration-300 cursor-grab active:cursor-grabbing"
              :class="compact ? 'compact-size' : 'normal-size'"
            >
              <img :src="element.preview" class="w-full h-full object-cover select-none" draggable="false">

              <!-- Overlay with actions on hover -->
              <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center gap-3 z-10">
                <!-- Set as primary button (only for non-first images) -->
                <button
                  v-if="index !== 0"
                  class="w-10 h-10 flex items-center justify-center rounded-full bg-primary-400 hover:bg-primary-500 text-secondary-900 shadow-lg transition-all duration-200 hover:scale-110"
                  aria-label="Définir comme principale"
                  title="Définir comme principale"
                  @click.stop="setAsPrimary(element, index)"
                >
                  <i class="pi pi-star text-lg"/>
                </button>

                <!-- Toggle label button (admin only, existing images only) -->
                <button
                  v-if="canToggleLabel && element.type === 'existing'"
                  class="w-10 h-10 flex items-center justify-center rounded-full shadow-lg transition-all duration-200 hover:scale-110"
                  :class="element.is_label ? 'bg-orange-500 hover:bg-orange-600 text-white' : 'bg-gray-500 hover:bg-gray-600 text-white'"
                  :aria-label="element.is_label ? 'Retirer le label' : 'Marquer comme label'"
                  :title="element.is_label ? 'Retirer le label' : 'Marquer comme label'"
                  :disabled="isTogglingLabel"
                  @click.stop="toggleLabel(element)"
                >
                  <i v-if="isTogglingLabel" class="pi pi-spin pi-spinner text-lg"/>
                  <i v-else class="pi pi-tag text-lg"/>
                </button>

                <!-- Delete button -->
                <button
                  class="w-10 h-10 flex items-center justify-center rounded-full bg-red-500 hover:bg-red-600 text-white shadow-lg transition-all duration-200 hover:scale-110"
                  aria-label="Supprimer la photo"
                  title="Supprimer"
                  @click.stop="removeImage(element)"
                >
                  <i class="pi pi-trash text-lg"/>
                </button>
              </div>

              <!-- Main Badge - Top Left (first image) -->
              <div v-if="index === 0" class="absolute top-2 left-2 bg-primary-400 text-secondary-900 text-xs font-bold px-2 py-1 rounded-full z-20 flex items-center gap-1 shadow-md">
                <i class="pi pi-star-fill text-xs"/>
                Principale
              </div>

              <!-- Label Badge - Top Right (for label images) -->
              <div v-if="element.is_label" class="absolute top-2 right-2 bg-orange-500 text-white text-xs font-bold px-2 py-1 rounded-full z-20 flex items-center gap-1 shadow-md">
                <i class="pi pi-tag text-xs"/>
                Label
              </div>

              <!-- Drag Handle Indicator -->
              <div class="absolute bottom-2 right-2 bg-black/60 text-white text-xs px-2 py-1 rounded z-20 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                <i class="pi pi-arrows-alt text-xs"/>
                <span>Déplacer</span>
              </div>
            </div>
          </template>
        </draggable>
      </div>

      <!-- Navigation Button Right -->
      <button
        class="flex items-center justify-center w-8 flex-shrink-0 rounded-lg text-secondary-600 hover:text-secondary-900 hover:bg-gray-100 transition-all duration-200"
        :class="canScrollRight ? 'cursor-pointer' : 'opacity-30 cursor-default'"
        aria-label="Défiler à droite"
        @click="scrollRight"
      >
        <i class="pi pi-chevron-right text-xl font-bold"/>
      </button>
    </div>

    <!-- Hidden file input (always present for programmatic access) -->
    <input
      ref="fileInput"
      type="file"
      multiple
      accept="image/*"
      class="hidden"
      :disabled="allImages.length >= maxPhotos"
      @change="handleFileUpload"
    >

    <!-- Upload Zone - Only show when no images at all -->
    <div
      v-if="allImages.length === 0"
      class="border-2 border-dashed rounded-xl transition-all duration-300"
      :class="{
        'border-primary-400 bg-primary-50 scale-[1.01]': isDraggingFile,
        'border-gray-300 hover:border-primary-400 hover:bg-gray-50': !isDraggingFile,
        'p-3': compact,
        'p-4': !compact
      }"
    >
      <div class="flex flex-col items-center justify-center" :class="compact ? 'gap-2' : 'gap-3'">
        <!-- Icon -->
        <div
          class="rounded-full flex items-center justify-center transition-all duration-300"
          :class="[
            compact ? 'w-12 h-12' : 'w-16 h-16',
            {
              'bg-primary-400 scale-110': isDraggingFile,
              'bg-primary-400': !isDraggingFile
            }
          ]"
        >
          <i
            class="pi pi-cloud-upload text-secondary-900"
            :class="[
              compact ? 'text-xl' : 'text-3xl',
              { 'animate-bounce': isDraggingFile }
            ]"
          />
        </div>

        <!-- Text -->
        <div class="text-center">
          <p
            class="font-bold text-secondary-900"
            :class="compact ? 'text-xs mb-0' : 'text-base mb-1'"
          >
            Glissez-déposez vos photos n'importe où
          </p>
          <p
            v-if="!compact"
            class="text-xs text-secondary-600"
          >
            ou cliquez sur le bouton ci-dessous
          </p>
          <p
            class="text-primary-600 font-bold"
            :class="compact ? 'text-[10px] mt-0.5' : 'text-xs mt-1'"
          >
            Au moins 1 photo est obligatoire
          </p>
        </div>

        <!-- Upload Button -->
        <label class="cursor-pointer">
          <div
            class="flex items-center bg-primary-400 hover:bg-primary-500 text-secondary-900 font-bold rounded-lg transition-all duration-200 hover:scale-105"
            :class="compact ? 'gap-2 px-4 py-2 text-sm' : 'gap-3 px-6 py-3'"
            @click="openFileSelector"
          >
            <i class="pi pi-upload" :class="compact ? 'text-base' : 'text-xl'"/>
            <span>Sélectionner des photos</span>
          </div>
        </label>

        <!-- Info -->
        <p
          v-if="!compact"
          class="text-xs text-secondary-600 text-center"
        >
          Maximum {{ maxPhotos }} photos • Formats : JPG, PNG, WEBP, GIF
        </p>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import draggable from 'vuedraggable'

// Types
interface Photo {
  file: File
  preview: string
}

interface ExistingImage {
  id: number
  url: string
  position: number
  is_label?: boolean
}

// Unified image type for drag and drop
interface UnifiedImage {
  key: string
  type: 'existing' | 'new'
  preview: string
  // For existing images
  id?: number
  originalPosition?: number
  is_label?: boolean
  // For new photos
  file?: File
  photoIndex?: number
}

interface Props {
  photos: Photo[]
  existingImages?: ExistingImage[]
  maxPhotos?: number
  compact?: boolean
  /** Product ID - required for admin label toggle feature */
  productId?: number
  /** Enable admin-only label toggle feature */
  canToggleLabel?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  maxPhotos: 20,
  existingImages: () => [],
  compact: false,
  productId: undefined,
  canToggleLabel: false
})

const emit = defineEmits<{
  'update:photos': [photos: Photo[]]
  'update:existingImages': [images: ExistingImage[]]
  'remove-existing': [imageId: number]
  'reorder': [order: { existingImages: ExistingImage[], photos: Photo[] }]
  'label-toggled': [imageId: number, isLabel: boolean]
}>()

const { showSuccess, showWarn } = useAppToast()

// File input ref
const fileInput = ref<HTMLInputElement | null>(null)

// Drag states
const isDraggingFile = ref(false)
const isDraggingReorder = ref(false)
let dragCounter = 0

// Scroll navigation
const scrollContainer = ref<HTMLElement | null>(null)
const canScrollLeft = ref(false)
const canScrollRight = ref(false)

// Create unified list of all images for drag and drop
const allImages = computed({
  get: () => {
    const images: UnifiedImage[] = []

    // Add existing images
    props.existingImages.forEach((img, idx) => {
      images.push({
        key: `existing-${img.id}`,
        type: 'existing',
        preview: img.url,
        id: img.id,
        originalPosition: img.position,
        is_label: img.is_label
      })
    })

    // Add new photos
    props.photos.forEach((photo, idx) => {
      images.push({
        key: `new-${idx}-${photo.preview}`,
        type: 'new',
        preview: photo.preview,
        file: photo.file,
        photoIndex: idx
      })
    })

    return images
  },
  set: (newOrder: UnifiedImage[]) => {
    // Separate existing images and new photos
    const reorderedExisting: ExistingImage[] = []
    const reorderedPhotos: Photo[] = []

    newOrder.forEach((item, index) => {
      if (item.type === 'existing' && item.id !== undefined) {
        reorderedExisting.push({
          id: item.id,
          url: item.preview,
          position: index // New position based on order
        })
      } else if (item.type === 'new' && item.file) {
        reorderedPhotos.push({
          file: item.file,
          preview: item.preview
        })
      }
    })

    // Emit updates
    emit('update:existingImages', reorderedExisting)
    emit('update:photos', reorderedPhotos)
    emit('reorder', { existingImages: reorderedExisting, photos: reorderedPhotos })
  }
})

// Scroll functions
const checkScrollPosition = () => {
  if (!scrollContainer.value) return
  const { scrollLeft, scrollWidth, clientWidth } = scrollContainer.value
  canScrollLeft.value = scrollLeft > 0
  canScrollRight.value = scrollLeft < scrollWidth - clientWidth - 10
}

const scrollLeft = () => {
  if (!scrollContainer.value) return
  scrollContainer.value.scrollBy({ left: -300, behavior: 'smooth' })
}

const scrollRight = () => {
  if (!scrollContainer.value) return
  scrollContainer.value.scrollBy({ left: 300, behavior: 'smooth' })
}

// Watch for changes
watch([() => props.photos.length, () => props.existingImages.length], () => {
  nextTick(() => checkScrollPosition())
})

onMounted(() => {
  checkScrollPosition()
})

// Drag handlers for reordering
const onDragStart = () => {
  isDraggingReorder.value = true
}

const onDragEnd = () => {
  isDraggingReorder.value = false
}

// File drag and drop handlers
const handleDragOver = (event: DragEvent) => {
  // Only show overlay if dragging files, not reordering
  if (isDraggingReorder.value) return
  if (!event.dataTransfer?.types.includes('Files')) return

  event.preventDefault()
  if (!isDraggingFile.value) {
    dragCounter++
    isDraggingFile.value = true
  }
}

const handleDragLeave = (event: DragEvent) => {
  if (isDraggingReorder.value) return

  event.preventDefault()
  dragCounter--
  if (dragCounter === 0) {
    isDraggingFile.value = false
  }
}

const handleDrop = (event: DragEvent) => {
  if (isDraggingReorder.value) return

  event.preventDefault()
  isDraggingFile.value = false
  dragCounter = 0

  const files = Array.from(event.dataTransfer?.files || [])
  processFiles(files)
}

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = Array.from(target.files || [])
  processFiles(files)
}

const processFiles = (files: File[]) => {
  const imageFiles = files.filter(file => file.type.startsWith('image/'))

  if (imageFiles.length === 0) {
    showWarn('Aucune image', 'Veuillez sélectionner des fichiers images valides')
    return
  }

  const remainingSlots = props.maxPhotos - allImages.value.length

  if (remainingSlots === 0) {
    showWarn('Limite atteinte', `Vous avez atteint la limite de ${props.maxPhotos} photos`)
    return
  }

  if (imageFiles.length > remainingSlots) {
    showWarn('Limite dépassée', `Vous ne pouvez ajouter que ${remainingSlots} photo(s) supplémentaire(s)`)
    return
  }

  const newPhotos = imageFiles.map(file => ({
    file,
    preview: URL.createObjectURL(file)
  }))

  emit('update:photos', [...props.photos, ...newPhotos])
  showSuccess('Photos ajoutées', `${newPhotos.length} photo(s) ajoutée(s) avec succès`, 2000)

  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const removeImage = (element: UnifiedImage) => {
  if (element.type === 'existing' && element.id !== undefined) {
    emit('remove-existing', element.id)
  } else if (element.type === 'new') {
    // Find index in photos array
    const idx = props.photos.findIndex(p => p.preview === element.preview)
    if (idx !== -1) {
      const photo = props.photos[idx]
      if (photo?.preview) {
        URL.revokeObjectURL(photo.preview)
      }
      const newPhotos = [...props.photos]
      newPhotos.splice(idx, 1)
      emit('update:photos', newPhotos)
    }
  }
}

// Set an image as primary (move to first position)
const setAsPrimary = (element: UnifiedImage, currentIndex: number) => {
  const currentImages = [...allImages.value]
  // Remove from current position and insert at first position
  const [item] = currentImages.splice(currentIndex, 1)
  currentImages.unshift(item)
  // Update via computed setter
  allImages.value = currentImages
  showSuccess('Photo principale', 'La photo a été définie comme principale', 2000)
}

// Toggle label status (admin only)
const isTogglingLabel = ref(false)
const toggleLabel = async (element: UnifiedImage) => {
  if (!props.canToggleLabel || !props.productId || element.type !== 'existing' || element.id === undefined) {
    return
  }

  const newIsLabel = !element.is_label
  isTogglingLabel.value = true

  try {
    const { $api } = useNuxtApp()
    await $api(`/products/${props.productId}/images/${element.id}/label?is_label=${newIsLabel}`, {
      method: 'PUT'
    })

    // Update local state
    const idx = allImages.value.findIndex(img => img.key === element.key)
    if (idx !== -1) {
      // If setting as label, unset other labels first
      if (newIsLabel) {
        allImages.value.forEach(img => {
          if (img.type === 'existing') {
            img.is_label = false
          }
        })
      }
      allImages.value[idx].is_label = newIsLabel
    }

    emit('label-toggled', element.id, newIsLabel)
    showSuccess(
      newIsLabel ? 'Marqué comme label' : 'Label retiré',
      newIsLabel ? 'L\'image est maintenant un label interne' : 'L\'image est maintenant une photo produit',
      2000
    )
  } catch (error) {
    console.error('Failed to toggle label:', error)
    showWarn('Erreur', 'Impossible de modifier le statut label')
  } finally {
    isTogglingLabel.value = false
  }
}

// Expose method to open file selector from parent
const openFileSelector = () => {
  if (fileInput.value) {
    fileInput.value.click()
  }
}

defineExpose({
  openFileSelector
})
</script>

<style scoped>
.hide-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.hide-scrollbar::-webkit-scrollbar {
  display: none;
}

/* Fade transition for drag overlay */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Drag animation */
.rotate-3 {
  transform: rotate(3deg);
}

/* Photo sizes */
.normal-size {
  width: 350px;
  height: 350px;
}

.compact-size {
  width: 160px;
  height: 160px;
}

.photo-item {
  transition: width 0.3s ease, height 0.3s ease;
}
</style>
