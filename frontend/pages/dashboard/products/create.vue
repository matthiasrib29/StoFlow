<template>
  <div class="p-6">
    <!-- Page Header -->
    <div class="flex items-center justify-between mb-3">
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

    <!-- Photo Section Title -->
    <div class="flex items-center justify-between mb-2">
      <h3 class="text-base font-bold text-secondary-900 flex items-center gap-2">
        <i class="pi pi-images"/>
        Photos du produit * <span class="font-normal text-sm text-gray-500">(min. 1)</span>
        <span class="text-sm font-normal text-gray-400">{{ photos.length }}/20</span>
      </h3>

      <Button
        v-if="photos.length > 0"
        label="Ajouter"
        icon="pi pi-plus"
        class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
        size="small"
        :disabled="photos.length >= 20"
        @click="openPhotoSelector"
      />
    </div>

    <!-- Photos Section -->
    <div class="mb-4">
      <ProductsPhotoUploader ref="photoUploader" v-model:photos="photos" />
    </div>

    <!-- Form Section -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
      <ProductsProductForm
        v-model="form"
        :is-submitting="isSubmitting"
        @submit="handleSubmit"
        @cancel="$router.push('/dashboard/products')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useProductsStore } from '~/stores/products'
import { type ProductFormData, defaultProductFormData } from '~/types/product'

definePageMeta({
  layout: 'dashboard'
})

const router = useRouter()
const productsStore = useProductsStore()
const { showSuccess, showError, showWarn } = useAppToast()

// Form data with complete ProductFormData interface
const form = ref<ProductFormData>({ ...defaultProductFormData })

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
  // Validation: Vérifier qu'au moins 1 photo est ajoutée
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
    // Préparer les données pour l'API (mapper size_original vers le format attendu par le backend)
    const productData = {
      title: form.value.title,
      description: form.value.description,
      price: form.value.price,
      category: form.value.category,
      condition: form.value.condition,
      brand: form.value.brand || null,
      size_original: form.value.size_original || null,
      size_normalized: form.value.size_normalized || null,
      color: form.value.color || null,
      material: form.value.material || null,
      fit: form.value.fit || null,
      gender: form.value.gender || null,
      season: form.value.season || null,
      sport: form.value.sport || null,
      neckline: form.value.neckline || null,
      length: form.value.length || null,
      pattern: form.value.pattern || null,
      rise: form.value.rise || null,
      closure: form.value.closure || null,
      sleeve_length: form.value.sleeve_length || null,
      origin: form.value.origin || null,
      decade: form.value.decade || null,
      trend: form.value.trend || null,
      condition_sup: form.value.condition_sup || null,
      location: form.value.location || null,
      model: form.value.model || null,
      unique_feature: form.value.unique_feature || null,
      marking: form.value.marking || null,
      dim1: form.value.dim1 || null,
      dim2: form.value.dim2 || null,
      dim3: form.value.dim3 || null,
      dim4: form.value.dim4 || null,
      dim5: form.value.dim5 || null,
      dim6: form.value.dim6 || null,
      pricing_rarity: form.value.pricing_rarity || null,
      pricing_quality: form.value.pricing_quality || null,
      pricing_style: form.value.pricing_style || null,
      pricing_details: form.value.pricing_details || null,
      pricing_edit: form.value.pricing_edit || null,
      stock_quantity: form.value.stock_quantity
    }

    // Créer le produit via API
    const newProduct = await productsStore.createProduct(productData)

    // Upload images si le produit est créé avec succès
    if (newProduct && photos.value.length > 0 && newProduct.id) {
      try {
        for (let i = 0; i < photos.value.length; i++) {
          const photo = photos.value[i]
          if (photo) {
            await productsStore.uploadProductImage(newProduct.id, photo.file, i)
          }
        }

        showSuccess(
          'Produit créé',
          `${form.value.title} a été créé avec ${photos.value.length} image(s)`,
          3000
        )
      } catch (imageError: any) {
        showWarn(
          'Produit créé',
          `${form.value.title} créé, mais erreur upload images: ${imageError.message}`,
          5000
        )
      }
    } else if (newProduct) {
      showSuccess(
        'Produit créé',
        `${form.value.title} a été créé avec succès`,
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
