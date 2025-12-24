<template>
  <div
    class="bg-white rounded-lg p-4 relative"
    @dragover.prevent="handleDragOver"
    @dragleave.prevent="handleDragLeave"
    @drop.prevent="handleDrop"
  >
    <!-- Drag Overlay -->
    <transition name="fade">
      <div
        v-if="isDragging"
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

    <!-- Photo Preview Horizontal Scroll -->
    <div v-if="photos.length > 0" class="relative mb-4">
      <!-- Navigation Button Left -->
      <button
        v-if="canScrollLeft"
        class="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-primary-400 hover:bg-primary-500 text-secondary-900 rounded-full p-3 shadow-lg transition-all duration-300 hover:scale-110"
        aria-label="Défiler à gauche"
        @click="scrollLeft"
      >
        <i class="pi pi-chevron-left text-xl font-bold"/>
      </button>

      <!-- Photos Container -->
      <div
        ref="scrollContainer"
        class="overflow-x-auto scroll-smooth pb-2 hide-scrollbar"
        @scroll="checkScrollPosition"
      >
        <div class="flex gap-4 min-w-max px-12">
          <div
            v-for="(photo, index) in photos"
            :key="index"
            class="relative group rounded-lg overflow-hidden shadow-md flex-shrink-0 hover:shadow-xl transition-shadow duration-300"
            style="width: 280px; height: 280px;"
          >
            <img :src="photo.preview" class="w-full h-full object-cover" >

            <!-- Delete Button - Top Right -->
            <button
              class="absolute top-2 right-2 z-20 w-8 h-8 flex items-center justify-center bg-red-500 hover:bg-red-600 text-white rounded-full shadow-lg opacity-0 group-hover:opacity-100 transition-all duration-200 hover:scale-110"
              aria-label="Supprimer la photo"
              @click="removePhoto(index)"
            >
              <i class="pi pi-times text-sm font-bold"/>
            </button>

            <!-- Main Badge - Top Left -->
            <div v-if="index === 0" class="absolute top-2 left-2 bg-primary-400 text-secondary-900 text-xs font-bold px-2 py-1 rounded z-10">
              Principale
            </div>
          </div>
        </div>
      </div>

      <!-- Navigation Button Right -->
      <button
        v-if="canScrollRight"
        class="absolute right-0 top-1/2 -translate-y-1/2 z-10 bg-primary-400 hover:bg-primary-500 text-secondary-900 rounded-full p-3 shadow-lg transition-all duration-300 hover:scale-110"
        aria-label="Défiler à droite"
        @click="scrollRight"
      >
        <i class="pi pi-chevron-right text-xl font-bold"/>
      </button>
    </div>

    <!-- Upload Zone - Only show when no photos -->
    <div v-if="photos.length === 0" class="border-2 border-dashed rounded-xl p-6 transition-all duration-300 border-gray-300 hover:border-primary-400">
      <div class="flex flex-col items-center justify-center gap-4">
        <!-- Icon -->
        <div class="w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300 bg-primary-400">
          <i class="pi pi-cloud-upload text-4xl text-secondary-900"/>
        </div>

        <!-- Text -->
        <div class="text-center">
          <p class="text-lg font-bold text-secondary-900 mb-1">
            Glissez-déposez vos photos n'importe où
          </p>
          <p class="text-sm text-secondary-600">
            ou cliquez sur le bouton ci-dessous
          </p>
          <p class="text-xs text-primary-600 font-bold mt-2">
            ⚠️ Au moins 1 photo est obligatoire
          </p>
        </div>

        <!-- Upload Button -->
        <label class="cursor-pointer">
          <input
            ref="fileInput"
            type="file"
            multiple
            accept="image/*"
            class="hidden"
            :disabled="photos.length >= maxPhotos"
            @change="handleFileUpload"
          >
          <div class="flex items-center gap-3 px-6 py-3 bg-primary-400 hover:bg-primary-500 text-secondary-900 font-bold rounded-lg transition-all duration-200 hover:scale-105">
            <i class="pi pi-upload text-xl"/>
            <span>Sélectionner des photos</span>
          </div>
        </label>

        <!-- Info -->
        <p class="text-xs text-secondary-600 text-center">
          Maximum {{ maxPhotos }} photos • Formats : JPG, PNG, WEBP, GIF
        </p>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
interface Photo {
  file: File
  preview: string
}

interface Props {
  photos: Photo[]
  maxPhotos?: number
}

const props = withDefaults(defineProps<Props>(), {
  maxPhotos: 20
})

const emit = defineEmits<{
  'update:photos': [photos: Photo[]]
}>()

const { showSuccess, showError, showWarn } = useAppToast()

// File input ref
const fileInput = ref<HTMLInputElement | null>(null)

// Drag and drop state
const isDragging = ref(false)
let dragCounter = 0

// Scroll navigation
const scrollContainer = ref<HTMLElement | null>(null)
const canScrollLeft = ref(false)
const canScrollRight = ref(false)

const checkScrollPosition = () => {
  if (!scrollContainer.value) return

  const { scrollLeft, scrollWidth, clientWidth } = scrollContainer.value
  canScrollLeft.value = scrollLeft > 0
  canScrollRight.value = scrollLeft < scrollWidth - clientWidth - 10
}

const scrollLeft = () => {
  if (!scrollContainer.value) return
  scrollContainer.value.scrollBy({
    left: -300,
    behavior: 'smooth'
  })
}

const scrollRight = () => {
  if (!scrollContainer.value) return
  scrollContainer.value.scrollBy({
    left: 300,
    behavior: 'smooth'
  })
}

// Check scroll position when photos change
watch(() => props.photos.length, () => {
  nextTick(() => {
    checkScrollPosition()
  })
})

// Initial check
onMounted(() => {
  checkScrollPosition()
})

// Drag and drop handlers
const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  if (!isDragging.value) {
    dragCounter++
    isDragging.value = true
  }
}

const handleDragLeave = (event: DragEvent) => {
  event.preventDefault()
  dragCounter--
  if (dragCounter === 0) {
    isDragging.value = false
  }
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  isDragging.value = false
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
  // Filter only image files
  const imageFiles = files.filter(file => file.type.startsWith('image/'))

  if (imageFiles.length === 0) {
    showWarn('Aucune image', 'Veuillez sélectionner des fichiers images valides')
    return
  }

  // Check limit
  const remainingSlots = props.maxPhotos - props.photos.length

  if (remainingSlots === 0) {
    showWarn('Limite atteinte', `Vous avez atteint la limite de ${props.maxPhotos} photos`)
    return
  }

  if (imageFiles.length > remainingSlots) {
    showWarn('Limite dépassée', `Vous ne pouvez ajouter que ${remainingSlots} photo(s) supplémentaire(s)`)
    return
  }

  // Add photos with preview
  const newPhotos = imageFiles.map(file => ({
    file,
    preview: URL.createObjectURL(file)
  }))

  emit('update:photos', [...props.photos, ...newPhotos])

  showSuccess('Photos ajoutées', `${newPhotos.length} photo(s) ajoutée(s) avec succès`, 2000)

  // Reset file input
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const removePhoto = (index: number) => {
  const photo = props.photos[index]
  if (photo?.preview) {
    URL.revokeObjectURL(photo.preview)
  }
  const newPhotos = [...props.photos]
  newPhotos.splice(index, 1)
  emit('update:photos', newPhotos)
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
</style>
