<template>
  <div class="p-6">
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <ProgressSpinner />
    </div>

    <!-- Product not found -->
    <div v-else-if="!product" class="text-center py-20">
      <i class="pi pi-exclamation-circle text-gray-300 text-6xl mb-4"/>
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
    <div v-else>
      <!-- Page Header -->
      <div class="flex items-center justify-between mb-3">
        <div>
          <h1 class="text-2xl font-bold text-secondary-900">Modifier le produit</h1>
          <p class="text-sm text-gray-500">{{ product.title }}</p>
        </div>
        <Button
          label="Retour"
          icon="pi pi-arrow-left"
          class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
          @click="$router.push('/dashboard/products')"
        />
      </div>

      <!-- Photo Section Title -->
      <div class="flex items-center justify-between mb-2">
        <h3 class="text-base font-bold text-secondary-900 flex items-center gap-2">
          <i class="pi pi-images"/>
          Photos du produit
          <span class="text-sm font-normal text-gray-400">{{ existingImages.length + newPhotos.length }}/20</span>
        </h3>

        <Button
          v-if="existingImages.length > 0 || newPhotos.length > 0"
          label="Ajouter"
          icon="pi pi-plus"
          class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
          size="small"
          :disabled="existingImages.length + newPhotos.length >= 20"
          @click="openPhotoSelector"
        />
      </div>

      <!-- Photos Section -->
      <div class="mb-4">
        <ProductsPhotoUploader
          ref="photoUploader"
          v-model:photos="newPhotos"
          v-model:existing-images="existingImages"
          @remove-existing="removeExistingImage"
          @reorder="handleReorder"
        />
      </div>

      <!-- Form Section -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
        <ProductsProductForm
          v-model="form"
          :is-submitting="isSubmitting"
          :product-id="id"
          :has-images="existingImages.length > 0 || newPhotos.length > 0"
          submit-label="Enregistrer les modifications"
          @submit="handleSubmit"
          @cancel="$router.push('/dashboard/products')"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useProductsStore } from '~/stores/products'

definePageMeta({
  layout: 'dashboard'
})

const route = useRoute()
const router = useRouter()
const config = useRuntimeConfig()
const { showSuccess, showError, showWarn } = useAppToast()
const productsStore = useProductsStore()

const id = parseInt(route.params.id as string)

// Helper to build full image URL
const buildImageUrl = (imagePath: string): string => {
  if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
    return imagePath
  }
  const path = imagePath.startsWith('/') ? imagePath : `/${imagePath}`
  return `${config.public.apiUrl}${path}`
}

// State
const loading = ref(true)
const product = ref<any>(null)
const isSubmitting = ref(false)

// Form data (same structure as create.vue)
const form = ref({
  // Informations de base
  title: '',
  description: '',
  price: null as number | null,

  // Attributs obligatoires
  brand: '',
  category: '',
  condition: '',
  label_size: '',
  color: '',

  // Attributs optionnels
  material: null as string | null,
  fit: null as string | null,
  gender: null as string | null,
  season: null as string | null,

  // Dimensions
  dim1: null as number | null,
  dim2: null as number | null,
  dim3: null as number | null,
  dim4: null as number | null,
  dim5: null as number | null,
  dim6: null as number | null,

  // Stock
  stock_quantity: 1
})

// Photos management
interface Photo {
  file: File
  preview: string
}

interface ExistingImage {
  id: number
  url: string
  position: number
}

const newPhotos = ref<Photo[]>([])
const existingImages = ref<ExistingImage[]>([])
const imagesToDelete = ref<number[]>([])

// Reference to PhotoUploader component
const photoUploader = ref<{ openFileSelector: () => void } | null>(null)

// Method to open photo selector
const openPhotoSelector = () => {
  if (photoUploader.value) {
    photoUploader.value.openFileSelector()
  }
}

// Remove existing image
const removeExistingImage = (imageId: number) => {
  existingImages.value = existingImages.value.filter(img => img.id !== imageId)
  imagesToDelete.value.push(imageId)
}

// Track if images were reordered
const imagesReordered = ref(false)

// Handle reorder event from PhotoUploader
const handleReorder = (_order: { existingImages: ExistingImage[], photos: Photo[] }) => {
  imagesReordered.value = true
}

// Fetch product on mount
onMounted(async () => {
  try {
    loading.value = true

    // Charger le produit depuis l'API
    product.value = await productsStore.fetchProduct(id)

    if (product.value) {
      // Pré-remplir le formulaire avec les données existantes
      form.value = {
        title: product.value.title || '',
        description: product.value.description || '',
        price: product.value.price !== null ? parseFloat(product.value.price) : null,
        brand: product.value.brand || '',
        category: product.value.category || '',
        condition: product.value.condition || '',
        label_size: product.value.label_size || '',
        color: product.value.color || '',
        material: product.value.material || null,
        fit: product.value.fit || null,
        gender: product.value.gender || null,
        season: product.value.season || null,
        dim1: product.value.dim1 || null,
        dim2: product.value.dim2 || null,
        dim3: product.value.dim3 || null,
        dim4: product.value.dim4 || null,
        dim5: product.value.dim5 || null,
        dim6: product.value.dim6 || null,
        stock_quantity: product.value.stock_quantity || 1
      }

      // Charger les images existantes
      if (product.value.product_images && product.value.product_images.length > 0) {
        existingImages.value = product.value.product_images
          .sort((a: any, b: any) => a.display_order - b.display_order)
          .map((img: any) => ({
            id: img.id,
            url: buildImageUrl(img.image_path),
            position: img.display_order
          }))
      }
    }
  } catch (error) {
    console.error('Erreur chargement produit:', error)
    showError('Erreur', 'Impossible de charger le produit', 5000)
  } finally {
    loading.value = false
  }
})

const handleSubmit = async () => {
  // Validation: Vérifier les champs obligatoires
  if (!form.value.title || !form.value.description) {
    showWarn(
      'Champs manquants',
      'Veuillez remplir tous les champs obligatoires (titre, description)',
      3000
    )
    return
  }

  if (!form.value.brand || !form.value.category || !form.value.condition ||
      !form.value.label_size || !form.value.color) {
    showWarn(
      'Attributs manquants',
      'Veuillez remplir tous les attributs obligatoires (marque, catégorie, état, taille, couleur)',
      3000
    )
    return
  }

  // Validation: Vérifier qu'au moins 1 image existe
  if (existingImages.value.length === 0 && newPhotos.value.length === 0) {
    showWarn(
      'Photo manquante',
      'Veuillez conserver ou ajouter au moins 1 photo pour le produit',
      3000
    )
    return
  }

  isSubmitting.value = true

  try {
    // Mettre à jour le produit via API
    await productsStore.updateProduct(product.value.id, {
      title: form.value.title,
      description: form.value.description,
      price: form.value.price,
      brand: form.value.brand,
      category: form.value.category,
      condition: form.value.condition,
      label_size: form.value.label_size,
      color: form.value.color,
      material: form.value.material || null,
      fit: form.value.fit || null,
      gender: form.value.gender || null,
      season: form.value.season || null,
      dim1: form.value.dim1 || null,
      dim2: form.value.dim2 || null,
      dim3: form.value.dim3 || null,
      dim4: form.value.dim4 || null,
      dim5: form.value.dim5 || null,
      dim6: form.value.dim6 || null,
      stock_quantity: form.value.stock_quantity
    })

    // Supprimer les images marquées pour suppression
    for (const imageId of imagesToDelete.value) {
      try {
        await productsStore.deleteProductImage(product.value.id, imageId)
      } catch (e) {
        console.error('Error deleting image:', e)
      }
    }

    // Réorganiser les images existantes si l'ordre a changé
    if (imagesReordered.value && existingImages.value.length > 0) {
      try {
        // Create mapping: imageId -> newPosition
        const imageOrder: Record<number, number> = {}
        existingImages.value.forEach((img, index) => {
          imageOrder[img.id] = index
        })
        await productsStore.reorderProductImages(product.value.id, imageOrder)
      } catch (e) {
        console.error('Error reordering images:', e)
      }
    }

    // Upload nouvelles photos
    if (newPhotos.value.length > 0) {
      // After reordering, positions are sequential (0 to n-1), so start at n
      const startPosition = existingImages.value.length
      for (let i = 0; i < newPhotos.value.length; i++) {
        const photo = newPhotos.value[i]
        if (photo) {
          await productsStore.uploadProductImage(product.value.id, photo.file, startPosition + i)
        }
      }
    }

    showSuccess(
      'Produit modifié',
      `${form.value.title} a été mis à jour avec succès`,
      3000
    )

    // Redirect to product list
    router.push('/dashboard/products')
  } catch (error: any) {
    console.error('Error updating product:', error)
    showError('Erreur', error.message || 'Impossible de modifier le produit', 5000)
  } finally {
    isSubmitting.value = false
  }
}

// Cleanup on unmount
onUnmounted(() => {
  newPhotos.value.forEach(photo => {
    URL.revokeObjectURL(photo.preview)
  })
})
</script>
