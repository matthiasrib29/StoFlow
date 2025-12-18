<template>
  <div class="p-8">
    <div v-if="loading" class="flex items-center justify-center py-20">
      <ProgressSpinner />
    </div>

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

    <div v-else>
      <!-- Header -->
      <div class="mb-8">
        <div class="flex items-center justify-between mb-2">
          <div>
            <h1 class="text-3xl font-bold text-secondary-900 mb-1">Modifier le produit</h1>
            <p class="text-gray-600">{{ product.title }}</p>
          </div>
          <Button
            label="Retour"
            icon="pi pi-arrow-left"
            class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
            @click="$router.push('/dashboard/products')"
          />
        </div>
      </div>

      <Card class="shadow-md modern-rounded">
        <template #content>
          <!-- Photo Uploader -->
          <ProductsPhotoUploader v-model:photos="photos" class="mb-6" />

          <!-- Product Form -->
          <ProductsProductForm
            v-model="form"
            :is-submitting="isSubmitting"
            @submit="handleSubmit"
            @cancel="$router.push('/dashboard/products')"
          />
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">

definePageMeta({
  layout: 'dashboard'
})

const route = useRoute()
const router = useRouter()
const { showSuccess, showError, showInfo, showWarn } = useAppToast()
const productsStore = useProductsStore()

const id = parseInt(route.params.id as string)

// State
const loading = ref(true)
const product = ref<any>(null)
const isSubmitting = ref(false)

// Form data
const form = ref({
  title: '',
  description: '',
  price: 0,
  stock_quantity: 1,
  category: '',
  brand: '',
  condition: 'good',
  label_size: '',
  color: ''
})

// Photos management
interface Photo {
  file: File
  preview: string
}

const photos = ref<Photo[]>([])

// Charger le produit
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
        price: parseFloat(product.value.price) || 0,
        stock_quantity: product.value.stock_quantity || 1,
        category: product.value.category || '',
        brand: product.value.brand || '',
        condition: product.value.condition || 'good',
        label_size: product.value.label_size || '',
        color: product.value.color || ''
      }

      // Note: Les images existantes sont affichées via product_images
      // L'utilisateur peut uploader de nouvelles images si nécessaire
    }
  } catch (error) {
    console.error('Erreur chargement produit:', error)
    showError('Erreur', 'Impossible de charger le produit', 5000)
  } finally {
    loading.value = false
  }
})

const handleSubmit = async () => {
  isSubmitting.value = true

  try {
    // Prepare product data
    const productData = {
      title: form.value.title,
      description: form.value.description,
      price: form.value.price.toString(),
      stock_quantity: form.value.stock_quantity,
      brand: form.value.brand,
      category: form.value.category,
      label_size: form.value.label_size,
      color: form.value.color,
      condition: form.value.condition,
      status: 'draft'
    }

    // Update product
    await productsStore.updateProduct(product.value.id, productData)

    // Upload new photos if any
    if (photos.value.length > 0) {
      for (const photo of photos.value) {
        await productsStore.uploadProductImage(product.value.id, photo.file)
      }
    }

    showSuccess('Produit modifié', `${form.value.title} a été mis à jour avec succès`)

    // Redirect to product list
    router.push('/dashboard/products')
  } catch (error: any) {
    showError('Erreur', error.message || 'Impossible de modifier le produit', 5000)
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
