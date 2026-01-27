<template>
  <div class="mb-6">
    <!-- Progress bar minimaliste -->
    <div class="flex items-center gap-3">
      <div class="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          class="h-full transition-all duration-500 ease-out"
          :class="progressColorClass"
          :style="{ width: `${progress}%` }"
        />
      </div>
      <div class="flex items-center gap-1.5">
        <span class="text-xs font-medium text-gray-500">{{ progress }}%</span>
        <i
          v-if="progress === 100"
          class="pi pi-check-circle text-success-500 text-xs"
        />
      </div>
    </div>
    <p class="text-[11px] text-gray-400 mt-1">Plus vous remplissez, meilleure sera la visibilité de votre annonce. Visez au moins 80%.</p>
  </div>
</template>

<script setup lang="ts">
import type { ProductFormData } from '~/types/product'

interface SectionStatus {
  id: string
  label: string
  filled: number
  total: number
  isComplete: boolean
}

interface Props {
  formData: ProductFormData
  hasPhotos?: boolean
  sections?: SectionStatus[]
  activeSection?: string
}

const props = withDefaults(defineProps<Props>(), {
  hasPhotos: false,
  sections: undefined,
  activeSection: undefined
})

defineEmits<{
  navigate: [sectionId: string]
}>()

const requiredFields = [
  'title', 'description', 'category', 'brand', 'condition',
  'size_original', 'color', 'gender', 'material'
] as const

const progress = computed(() => {
  const filledCount = requiredFields.filter(field => {
    const value = props.formData[field]
    return value !== null && value !== undefined && value !== ''
  }).length

  const fieldsProgress = (filledCount / requiredFields.length) * 90
  const photosProgress = props.hasPhotos ? 10 : 0

  return Math.round(fieldsProgress + photosProgress)
})

const progressColorClass = computed(() => {
  if (progress.value < 34) return 'bg-error-400'
  if (progress.value < 67) return 'bg-warning-400'
  return 'bg-success-500'
})

const progressTextClass = computed(() => {
  if (progress.value < 34) return 'text-error-500'
  if (progress.value < 67) return 'text-warning-500'
  return 'text-success-600'
})
</script>

<style scoped>
.section-nav-compact {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 6px;
  background: transparent;
  color: #6b7280;
  transition: all 0.15s ease;
  font-size: 0.75rem;
}

.section-nav-compact:hover {
  background: #f9fafb;
  color: #374151;
}

.section-nav-compact.active {
  background: #fef9c3;
  color: #854d0e;
  font-weight: 500;
}

.section-nav-compact.complete {
  color: #16a34a;
}
</style>
