/**
 * Composable for unified product image management
 *
 * Provides a unified interface for managing both existing images (from DB)
 * and new photos (from file uploads). Handles reordering, deletion, and
 * tracking changes for API submission.
 *
 * Created: 2026-01-13
 * Phase: Product Editor Unification
 */

import { productLogger } from '~/utils/logger'

// Unified image type for drag and drop
export interface UnifiedImage {
  key: string
  type: 'existing' | 'new'
  preview: string
  position: number
  // For existing images
  id?: number
  originalPosition?: number
  // For new photos
  file?: File
}

// Photo interface (for new uploads)
export interface Photo {
  file: File
  preview: string
}

// Existing image interface (from DB)
export interface ExistingImage {
  id: number
  url: string
  position: number
}

// Image changes for API submission
export interface ImageChanges {
  toDelete: number[]
  toUpload: { file: File; position: number }[]
  toReorder: { id: number; position: number }[]
  hasChanges: boolean
}

export interface UseProductImagesOptions {
  maxPhotos?: number
}

/**
 * Unified product image management composable
 *
 * @example
 * ```typescript
 * const images = useProductImages({ maxPhotos: 20 })
 *
 * // Initialize with existing images (edit mode)
 * images.initFromExisting(product.images)
 *
 * // Add new photos
 * images.addPhotos(files)
 *
 * // Get changes for API submission
 * const changes = images.getChanges()
 * ```
 */
export function useProductImages(options: UseProductImagesOptions = {}) {
  const { maxPhotos = 20 } = options
  const { showSuccess, showWarn } = useAppToast()

  // State
  const images = ref<UnifiedImage[]>([])
  const deletedIds = ref<number[]>([])
  const originalOrder = ref<Map<number, number>>(new Map())
  const hasReordered = ref(false)

  // Computed
  const totalCount = computed(() => images.value.length)
  const existingCount = computed(() => images.value.filter(img => img.type === 'existing').length)
  const newCount = computed(() => images.value.filter(img => img.type === 'new').length)
  const canAddMore = computed(() => images.value.length < maxPhotos)
  const remainingSlots = computed(() => maxPhotos - images.value.length)
  const hasImages = computed(() => images.value.length > 0)

  // Separate refs for v-model compatibility with PhotoUploader
  const photos = computed({
    get: () => images.value
      .filter(img => img.type === 'new')
      .map(img => ({
        file: img.file!,
        preview: img.preview
      })),
    set: (newPhotos: Photo[]) => {
      // Remove all new photos
      images.value = images.value.filter(img => img.type === 'existing')
      // Add the new photos
      const startPosition = images.value.length
      newPhotos.forEach((photo, idx) => {
        images.value.push({
          key: `new-${Date.now()}-${idx}`,
          type: 'new',
          preview: photo.preview,
          file: photo.file,
          position: startPosition + idx
        })
      })
      updatePositions()
    }
  })

  const existingImages = computed({
    get: () => images.value
      .filter(img => img.type === 'existing')
      .map(img => ({
        id: img.id!,
        url: img.preview,
        position: img.position
      })),
    set: (newExisting: ExistingImage[]) => {
      // Remove all existing images
      images.value = images.value.filter(img => img.type === 'new')
      // Add the existing images at the beginning
      const existingUnified = newExisting.map((img, idx) => ({
        key: `existing-${img.id}`,
        type: 'existing' as const,
        preview: img.url,
        id: img.id,
        originalPosition: originalOrder.value.get(img.id) ?? img.position,
        position: idx
      }))
      images.value = [...existingUnified, ...images.value]
      updatePositions()
    }
  })

  /**
   * Initialize with existing images (for edit mode)
   */
  const initFromExisting = (dbImages: Array<{ url: string; order: number }> | undefined) => {
    if (!dbImages || dbImages.length === 0) {
      images.value = []
      originalOrder.value.clear()
      return
    }

    // Sort by order and create unified images
    const sorted = [...dbImages].sort((a, b) => a.order - b.order)

    images.value = sorted.map((img, index) => ({
      key: `existing-${index}`,
      type: 'existing' as const,
      preview: img.url,
      id: index, // Use index as ID since JSONB doesn't have IDs
      originalPosition: img.order,
      position: index
    }))

    // Store original order for change detection
    originalOrder.value.clear()
    sorted.forEach((img, index) => {
      originalOrder.value.set(index, img.order)
    })
  }

  /**
   * Add new photos from file input
   */
  const addPhotos = (files: File[]): number => {
    const imageFiles = files.filter(file => file.type.startsWith('image/'))

    if (imageFiles.length === 0) {
      showWarn('Aucune image', 'Veuillez sélectionner des fichiers images valides')
      return 0
    }

    if (!canAddMore.value) {
      showWarn('Limite atteinte', `Vous avez atteint la limite de ${maxPhotos} photos`)
      return 0
    }

    const slotsAvailable = remainingSlots.value
    const filesToAdd = imageFiles.slice(0, slotsAvailable)

    if (filesToAdd.length < imageFiles.length) {
      showWarn('Limite dépassée', `Seulement ${filesToAdd.length} photo(s) ajoutée(s) sur ${imageFiles.length}`)
    }

    const startPosition = images.value.length
    const newImages: UnifiedImage[] = filesToAdd.map((file, idx) => ({
      key: `new-${Date.now()}-${idx}`,
      type: 'new' as const,
      preview: URL.createObjectURL(file),
      file,
      position: startPosition + idx
    }))

    images.value = [...images.value, ...newImages]

    if (filesToAdd.length > 0) {
      showSuccess('Photos ajoutées', `${filesToAdd.length} photo(s) ajoutée(s)`, 2000)
    }

    return filesToAdd.length
  }

  /**
   * Remove an image by key
   */
  const removeImage = (key: string) => {
    const index = images.value.findIndex(img => img.key === key)
    if (index === -1) return

    const image = images.value[index]

    // Track deleted existing images
    if (image.type === 'existing' && image.id !== undefined) {
      deletedIds.value.push(image.id)
    }

    // Revoke object URL for new photos
    if (image.type === 'new' && image.preview) {
      URL.revokeObjectURL(image.preview)
    }

    images.value.splice(index, 1)
    updatePositions()
  }

  /**
   * Remove an existing image by ID (for PhotoUploader compatibility)
   */
  const removeExistingImage = (imageId: number) => {
    const key = `existing-${imageId}`
    removeImage(key)
  }

  /**
   * Set an image as primary (move to first position)
   */
  const setAsPrimary = (key: string) => {
    const index = images.value.findIndex(img => img.key === key)
    if (index <= 0) return // Already first or not found

    const [image] = images.value.splice(index, 1)
    images.value.unshift(image)
    updatePositions()
    hasReordered.value = true
    showSuccess('Photo principale', 'La photo a été définie comme principale', 2000)
  }

  /**
   * Reorder images (for drag and drop)
   */
  const reorderImages = (newOrder: UnifiedImage[]) => {
    images.value = newOrder
    updatePositions()
    hasReordered.value = true
  }

  /**
   * Handle reorder event from PhotoUploader
   */
  const handleReorder = (_order: { existingImages: ExistingImage[]; photos: Photo[] }) => {
    hasReordered.value = true
  }

  /**
   * Update position values after any modification
   */
  const updatePositions = () => {
    images.value.forEach((img, idx) => {
      img.position = idx
    })
  }

  /**
   * Get all changes for API submission
   */
  const getChanges = (): ImageChanges => {
    // Images to delete
    const toDelete = [...deletedIds.value]

    // New photos to upload
    const toUpload = images.value
      .filter(img => img.type === 'new' && img.file)
      .map(img => ({
        file: img.file!,
        position: img.position
      }))

    // Existing images to reorder (only if positions changed)
    const toReorder: { id: number; position: number }[] = []
    if (hasReordered.value) {
      images.value
        .filter(img => img.type === 'existing' && img.id !== undefined)
        .forEach(img => {
          const origPos = originalOrder.value.get(img.id!)
          if (origPos !== img.position) {
            toReorder.push({ id: img.id!, position: img.position })
          }
        })
    }

    const hasChanges = toDelete.length > 0 || toUpload.length > 0 || toReorder.length > 0

    return {
      toDelete,
      toUpload,
      toReorder,
      hasChanges
    }
  }

  /**
   * Get files for AI analysis (both existing URLs and new files)
   */
  const getFilesForAnalysis = (): { files: File[]; hasExistingOnly: boolean } => {
    const newFiles = images.value
      .filter(img => img.type === 'new' && img.file)
      .map(img => img.file!)

    const hasExistingOnly = newFiles.length === 0 && existingCount.value > 0

    return {
      files: newFiles,
      hasExistingOnly
    }
  }

  /**
   * Reset state
   */
  const reset = () => {
    // Revoke all object URLs
    images.value.forEach(img => {
      if (img.type === 'new' && img.preview) {
        URL.revokeObjectURL(img.preview)
      }
    })

    images.value = []
    deletedIds.value = []
    originalOrder.value.clear()
    hasReordered.value = false
  }

  /**
   * Cleanup on unmount
   */
  const cleanup = () => {
    images.value.forEach(img => {
      if (img.type === 'new' && img.preview) {
        URL.revokeObjectURL(img.preview)
      }
    })
  }

  return {
    // State
    images,
    photos,
    existingImages,

    // Computed
    totalCount,
    existingCount,
    newCount,
    canAddMore,
    remainingSlots,
    hasImages,
    maxPhotos,

    // Methods
    initFromExisting,
    addPhotos,
    removeImage,
    removeExistingImage,
    setAsPrimary,
    reorderImages,
    handleReorder,
    getChanges,
    getFilesForAnalysis,
    reset,
    cleanup
  }
}
