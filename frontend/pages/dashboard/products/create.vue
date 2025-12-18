<template>
  <div class="p-8">
    <!-- Page Header -->
    <div class="flex items-center justify-between mb-4">
      <div>
        <h1 class="text-2xl font-bold text-secondary-900">Créer un produit</h1>
      </div>
      <Button
        label="Retour"
        icon="pi pi-arrow-left"
        class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
        @click="$router.push('/dashboard/products')"
      />
    </div>

    <!-- Photo Section Title (scrolls away) -->
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-lg font-bold text-secondary-900 flex items-center gap-2">
        <i class="pi pi-images"/>
        Photos du produit * <span class="font-normal text-sm text-gray-600">(minimum 1 requise)</span>
        <span class="text-sm font-normal ml-2">{{ photos.length }}/20</span>
      </h3>

      <!-- Add Photos Button (scrolls away) -->
      <Button
        v-if="photos.length > 0"
        label="Ajouter des photos"
        icon="pi pi-plus"
        class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-bold"
        :disabled="photos.length >= 20"
        @click="openPhotoSelector"
      />
    </div>

    <!-- Photos Section (Sticky at top) -->
    <div class="sticky top-0 z-10 mb-6 bg-white pb-2">
      <ProductsPhotoUploader ref="photoUploader" v-model:photos="photos" />
    </div>

    <!-- Form Section (Scrollable) -->
    <Card class="shadow-md modern-rounded">
      <template #content>
        <ProductsProductForm
          v-model="form"
          :is-submitting="isSubmitting"
          @submit="handleSubmit"
          @cancel="$router.push('/dashboard/products')"
        />
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { useProductsStore } from '~/stores/products'

definePageMeta({
  layout: 'dashboard'
})

const router = useRouter()
const productsStore = useProductsStore()
const { showSuccess, showError, showWarn } = useAppToast()

// Form data (Updated 2025-12-08: All required fields from API)
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

const photos = ref<Photo[]>([])
const isSubmitting = ref(false)

// Reference to PhotoUploader component
const photoUploader = ref<{ openFileSelector: () => void } | null>(null)

// Method to open photo selector
const openPhotoSelector = () => {
  if (photoUploader.value) {
    photoUploader.value.openFileSelector()
  }
}

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

  // Validation: Vérifier qu'au moins 1 photo est ajoutée (Business Rule 2025-12-09)
  if (photos.value.length === 0) {
    showWarn(
      'Photo manquante',
      'Veuillez ajouter au moins 1 photo pour le produit',
      3000
    )
    return
  }

  isSubmitting.value = true

  try {
    // Créer le produit via API
    // Note: status, created_at, updated_at sont gérés automatiquement par le backend
    const newProduct = await productsStore.createProduct({
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

    // Upload images si le produit est créé avec succès
    if (photos.value.length > 0 && newProduct.id) {
      try {
        for (let i = 0; i < photos.value.length; i++) {
          await productsStore.uploadProductImage(newProduct.id, photos.value[i].file, i)
        }

        showSuccess(
          'Produit créé',
          `${form.value.title} a été créé avec ${photos.value.length} image(s)`,
          3000
        )
      } catch (imageError: any) {
        // Produit créé mais erreur sur les images
        showWarn(
          'Produit créé',
          `${form.value.title} créé, mais erreur upload images: ${imageError.message}`,
          5000
        )
      }
    } else {
      showSuccess(
        'Produit créé',
        `${form.value.title} a été créé avec succès (ID: ${newProduct.id})`,
        3000
      )
    }

    // Redirect to products list
    router.push('/dashboard/products')
  } catch (error: any) {
    console.error('Error creating product:', error)
    showError(
      'Erreur',
      error.message || 'Impossible de créer le produit',
      5000
    )
  } finally {
    isSubmitting.value = false
  }
}

// Cleanup on unmount
onUnmounted(() => {
  photos.value.forEach(photo => {
    URL.revokeObjectURL(photo.preview)
  })
})

</script>
