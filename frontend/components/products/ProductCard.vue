<template>
  <div
    class="bg-white rounded-lg shadow-sm hover:shadow-md transition-all duration-200 cursor-pointer border border-gray-100 overflow-hidden group"
    @click="$emit('click', product)"
  >
    <!-- Image with overlay actions -->
    <div class="relative aspect-square overflow-hidden">
      <NuxtImg
        :src="getProductImageUrl(product)"
        :alt="product.title"
        class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
      />
      <!-- Status badge -->
      <div class="absolute top-2 right-2">
        <span
          class="px-2 py-0.5 rounded-full text-xs font-medium"
          :class="product.is_active ? 'bg-success-100 text-success-700' : 'bg-gray-100 text-gray-600'"
        >
          {{ product.is_active ? 'Actif' : 'Inactif' }}
        </span>
      </div>
      <!-- Checkbox -->
      <div v-if="selectable" class="absolute top-2 left-2">
        <div
          class="w-8 h-8 rounded-md border-2 flex items-center justify-center cursor-pointer transition-all bg-white/90 backdrop-blur-sm"
          :class="isSelected ? 'bg-primary-400 border-primary-400' : 'border-gray-300 hover:border-primary-400'"
          @click.stop="$emit('toggle-selection', product)"
        >
          <i v-if="isSelected" class="pi pi-check text-secondary-900 text-xs font-bold"/>
        </div>
      </div>
      <!-- Hover overlay with actions -->
      <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2 pointer-events-none group-hover:pointer-events-auto">
        <button
          class="w-10 h-10 rounded-full bg-white text-secondary-900 hover:bg-primary-400 transition-colors flex items-center justify-center shadow-lg pointer-events-auto"
          @click.stop="$emit('edit', product)"
        >
          <i class="pi pi-pencil text-sm"/>
        </button>
        <button
          class="w-10 h-10 rounded-full bg-white text-gray-600 hover:bg-gray-600 hover:text-white transition-colors flex items-center justify-center shadow-lg pointer-events-auto"
          title="Archiver"
          @click.stop="$emit('delete', product)"
        >
          <i class="pi pi-inbox text-sm"/>
        </button>
      </div>
    </div>

    <!-- Compact info -->
    <div class="p-3">
      <!-- Title -->
      <h3 class="text-sm font-semibold text-secondary-900 truncate">{{ product.title }}</h3>
      <!-- Brand & Category -->
      <p class="text-xs text-gray-500 truncate mt-0.5">{{ product.brand }}{{ product.category ? ` • ${product.category}` : '' }}</p>
      <!-- Price row -->
      <div class="flex items-center justify-between mt-2">
        <span class="text-lg font-bold text-secondary-900">{{ formatPrice(product.price) }}</span>
        <span
          class="text-xs px-1.5 py-0.5 rounded"
          :class="product.stock_quantity > 0 ? 'bg-success-50 text-success-600' : 'bg-error-50 text-error-500'"
        >
          {{ product.stock_quantity }}
        </span>
      </div>
    </div>
  </div>
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

const formatPrice = (price: number | null) => {
  if (price === null) return '-'
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR'
  }).format(price)
}
</script>
