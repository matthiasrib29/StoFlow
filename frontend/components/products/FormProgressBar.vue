<template>
  <div class="flex items-center gap-3">
    <div class="flex-1 h-2.5 bg-gray-200 rounded-full overflow-hidden">
      <div
        class="h-full transition-all duration-500 ease-out rounded-full"
        :class="progressColorClass"
        :style="{ width: `${progress}%` }"
      />
    </div>
    <div class="flex items-center gap-2 min-w-[80px]">
      <span class="text-sm font-semibold" :class="progressTextClass">{{ progress }}%</span>
      <i
        v-if="progress === 100"
        class="pi pi-check-circle text-green-500 text-sm"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ProductFormData } from '~/types/product'

interface Props {
  formData: ProductFormData
  hasPhotos?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  hasPhotos: false
})

// Required fields
const requiredFields = ['title', 'description', 'category', 'brand', 'condition', 'size_original', 'color', 'gender', 'material'] as const

// Calculate progress
const progress = computed(() => {
  const filledCount = requiredFields.filter(field => {
    const value = props.formData[field]
    return value !== null && value !== undefined && value !== ''
  }).length

  // 90% for fields, 10% for photos
  const fieldsProgress = (filledCount / requiredFields.length) * 90
  const photosProgress = props.hasPhotos ? 10 : 0

  return Math.round(fieldsProgress + photosProgress)
})

// Progress bar color based on percentage
const progressColorClass = computed(() => {
  if (progress.value < 34) return 'bg-red-400'
  if (progress.value < 67) return 'bg-orange-400'
  return 'bg-green-500'
})

// Text color based on percentage
const progressTextClass = computed(() => {
  if (progress.value < 34) return 'text-red-500'
  if (progress.value < 67) return 'text-orange-500'
  return 'text-green-600'
})
</script>
