<template>
  <Card
    class="shadow-sm hover:shadow-md transition-all duration-300 cursor-pointer border border-gray-100 overflow-hidden group"
    @click="$emit('click', product)"
  >
    <template #header>
      <div class="relative overflow-hidden">
        <img
          :src="getProductImageUrl(product)"
          :alt="product.title"
          class="w-full h-52 object-cover transition-transform duration-300 group-hover:scale-105"
        >
        <div class="absolute top-3 right-3">
          <Badge
            :value="product.is_active ? 'Actif' : 'Inactif'"
            :severity="product.is_active ? 'success' : 'warn'"
            class="text-xs font-semibold"
          />
        </div>
        <div v-if="selectable" class="absolute top-2 left-2">
          <!-- Touch-friendly checkbox (44px minimum tap target) -->
          <div
            class="w-10 h-10 rounded-lg border-2 flex items-center justify-center cursor-pointer transition-all shadow-sm"
            :class="isSelected ? 'bg-primary-400 border-primary-400' : 'bg-white/95 border-gray-300 hover:border-primary-400'"
            @click.stop="$emit('toggle-selection', product)"
          >
            <i v-if="isSelected" class="pi pi-check text-secondary-900 text-sm font-bold"/>
          </div>
        </div>
      </div>
    </template>

    <template #content>
      <div class="p-4 space-y-3">
        <!-- Title & Brand -->
        <div>
          <h3 class="text-base font-bold text-secondary-900 truncate mb-1">{{ product.title }}</h3>
          <p class="text-sm text-gray-500">{{ product.brand }} • {{ product.category }}</p>
        </div>

        <!-- Price & Stock -->
        <div class="flex justify-between items-center">
          <span class="text-xl font-bold text-secondary-900">{{ formatPrice(product.price) }}</span>
          <Badge
            :value="`${product.stock_quantity} en stock`"
            :severity="product.stock_quantity > 0 ? 'success' : 'danger'"
            class="text-xs"
          />
        </div>

        <!-- Description -->
        <p v-if="product.description" class="text-sm text-gray-500 line-clamp-2">{{ product.description }}</p>

        <!-- Actions -->
        <div class="flex gap-2 pt-2">
          <Button
            icon="pi pi-pencil"
            label="Éditer"
            class="flex-1 bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
            size="small"
            @click.stop="$emit('edit', product)"
          />
          <Button
            icon="pi pi-trash"
            class="bg-gray-100 hover:bg-red-50 text-gray-600 hover:text-red-500 border-0 transition-colors"
            size="small"
            @click.stop="$emit('delete', product)"
          />
        </div>
      </div>
    </template>
  </Card>
</template>

<script setup lang="ts">
import type { Product } from '~/stores/products'
import { getProductImageUrl } from '~/stores/products'

interface Props {
  product: Product
  selectable?: boolean
  isSelected?: boolean
}

defineProps<Props>()

defineEmits<{
  click: [product: Product]
  edit: [product: Product]
  delete: [product: Product]
  'toggle-selection': [product: Product]
}>()

const formatPrice = (price: number) => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR'
  }).format(price)
}
</script>
