<template>
  <div>
    <!-- Breadcrumb -->
    <div class="mb-6">
      <NuxtLink to="/dashboard/products" class="text-primary-600 hover:underline">
        <i class="pi pi-arrow-left mr-2"></i>
        Retour aux produits
      </NuxtLink>
    </div>

    <h1 class="text-3xl font-bold mb-6">Nouveau produit</h1>

    <Card>
      <template #content>
        <form @submit.prevent="handleSubmit" class="space-y-6">
          <!-- Title -->
          <div>
            <label for="title" class="block text-sm font-medium mb-2">
              Titre *
            </label>
            <InputText
              id="title"
              v-model="form.title"
              placeholder="Ex: T-Shirt Nike Vintage"
              class="w-full"
              required
              :disabled="productsStore.isLoading"
            />
          </div>

          <!-- Description -->
          <div>
            <label for="description" class="block text-sm font-medium mb-2">
              Description
            </label>
            <textarea
              id="description"
              v-model="form.description"
              placeholder="Décrivez votre produit..."
              class="w-full p-3 border border-gray-300 rounded-md"
              rows="4"
              :disabled="productsStore.isLoading"
            ></textarea>
          </div>

          <!-- Brand & Category -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label for="brand" class="block text-sm font-medium mb-2">
                Marque *
              </label>
              <InputText
                id="brand"
                v-model="form.brand"
                placeholder="Ex: Nike"
                class="w-full"
                required
                :disabled="productsStore.isLoading"
              />
            </div>
            <div>
              <label for="category" class="block text-sm font-medium mb-2">
                Catégorie *
              </label>
              <InputText
                id="category"
                v-model="form.category"
                placeholder="Ex: Vêtements"
                class="w-full"
                required
                :disabled="productsStore.isLoading"
              />
            </div>
          </div>

          <!-- Price & Stock -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label for="price" class="block text-sm font-medium mb-2">
                Prix (€) *
              </label>
              <InputText
                id="price"
                v-model.number="form.price"
                type="number"
                step="0.01"
                min="0"
                placeholder="25.99"
                class="w-full"
                required
                :disabled="productsStore.isLoading"
              />
            </div>
            <div>
              <label for="stock" class="block text-sm font-medium mb-2">
                Stock
              </label>
              <InputText
                id="stock"
                v-model.number="form.stock_quantity"
                type="number"
                min="0"
                placeholder="1"
                class="w-full"
                :disabled="productsStore.isLoading"
              />
            </div>
          </div>

          <!-- Size, Color, Material -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label for="size" class="block text-sm font-medium mb-2">
                Taille
              </label>
              <InputText
                id="size"
                v-model="form.size"
                placeholder="M"
                class="w-full"
                :disabled="productsStore.isLoading"
              />
            </div>
            <div>
              <label for="color" class="block text-sm font-medium mb-2">
                Couleur
              </label>
              <InputText
                id="color"
                v-model="form.color"
                placeholder="Noir"
                class="w-full"
                :disabled="productsStore.isLoading"
              />
            </div>
            <div>
              <label for="material" class="block text-sm font-medium mb-2">
                Matériau
              </label>
              <InputText
                id="material"
                v-model="form.material"
                placeholder="Coton"
                class="w-full"
                :disabled="productsStore.isLoading"
              />
            </div>
          </div>

          <!-- Condition -->
          <div>
            <label for="condition" class="block text-sm font-medium mb-2">
              État *
            </label>
            <Select
              id="condition"
              v-model="form.condition"
              :options="conditionOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Sélectionnez l'état"
              class="w-full"
              :disabled="productsStore.isLoading"
            />
          </div>

          <!-- Image URL -->
          <div>
            <label for="image_url" class="block text-sm font-medium mb-2">
              URL de l'image
            </label>
            <InputText
              id="image_url"
              v-model="form.image_url"
              placeholder="https://example.com/image.jpg"
              class="w-full"
              :disabled="productsStore.isLoading"
            />
            <p class="text-xs text-gray-500 mt-1">
              Laissez vide pour utiliser une image par défaut
            </p>
          </div>

          <!-- Submit Buttons -->
          <div class="flex gap-3 pt-4">
            <Button
              type="submit"
              label="Créer le produit"
              icon="pi pi-check"
              :loading="productsStore.isLoading"
            />
            <Button
              type="button"
              label="Annuler"
              icon="pi pi-times"
              severity="secondary"
              outlined
              @click="router.push('/dashboard/products')"
              :disabled="productsStore.isLoading"
            />
          </div>
        </form>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'dashboard'
})

const router = useRouter()
const productsStore = useProductsStore()
const { showSuccess, showError, showInfo, showWarn } = useAppToast()

const form = ref({
  title: '',
  description: '',
  brand: '',
  category: '',
  price: 0,
  stock_quantity: 1,
  size: '',
  color: '',
  material: '',
  condition: 'Bon état',
  image_url: ''
})

const conditionOptions = [
  { label: 'Neuf', value: 'Neuf' },
  { label: 'Comme neuf', value: 'Comme neuf' },
  { label: 'Très bon état', value: 'Très bon état' },
  { label: 'Bon état', value: 'Bon état' },
  { label: 'État correct', value: 'État correct' }
]

const handleSubmit = async () => {
  try {
    await productsStore.createProduct(form.value)

    showSuccess('Produit créé', 'Le produit a été ajouté avec succès', 3000)

    router.push('/dashboard/products')
  } catch (error: any) {
    showError('Erreur', error.message || 'Impossible de créer le produit', 5000)
  }
}

</script>
