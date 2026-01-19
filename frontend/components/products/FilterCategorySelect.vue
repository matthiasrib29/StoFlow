<template>
  <div class="relative">
    <!-- Input field that triggers dropdown -->
    <div
      class="border border-gray-200 rounded-lg px-3 py-2 cursor-pointer transition-all duration-150
             hover:border-gray-300 bg-white h-[42px] flex items-center"
      :class="{ 'border-primary-400 ring-2 ring-primary-100': isOpen }"
      @click="toggleDropdown"
    >
      <div class="flex items-center gap-2 flex-1 min-w-0">
        <i class="pi pi-sitemap text-gray-400 text-sm shrink-0" />
        <span class="text-sm truncate" :class="modelValue ? 'text-gray-900' : 'text-gray-400'">
          {{ displayValue || 'Toutes les catégories' }}
        </span>
      </div>
      <i
        class="pi pi-chevron-down text-gray-400 text-xs transition-transform duration-200 shrink-0"
        :class="{ 'rotate-180': isOpen }"
      />
    </div>

    <!-- Dropdown overlay -->
    <div
      v-if="isOpen"
      class="absolute z-50 mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-lg max-h-72 overflow-y-auto"
    >
      <!-- All categories option -->
      <div
        class="px-3 py-2 hover:bg-gray-50 cursor-pointer flex items-center gap-2 border-b border-gray-100"
        :class="{ 'bg-primary-50 text-primary-700': !modelValue }"
        @click="selectAll"
      >
        <i class="pi pi-list text-sm" />
        <span class="font-medium text-sm">Toutes les catégories</span>
      </div>

      <!-- Back button -->
      <div
        v-if="currentParent"
        class="px-3 py-2 hover:bg-gray-50 cursor-pointer flex items-center gap-2 text-primary-600 border-b border-gray-100"
        @click="goBack"
      >
        <i class="pi pi-arrow-left text-xs" />
        <span class="font-medium text-sm">Retour</span>
      </div>

      <!-- Categories list -->
      <div
        v-for="option in currentOptions"
        :key="option.value"
        class="px-3 py-2 hover:bg-gray-50 cursor-pointer flex items-center justify-between"
        :class="{ 'bg-primary-50': option.value === modelValue }"
        @click="handleSelect(option)"
      >
        <span class="text-sm">{{ option.label }}</span>
        <i
          v-if="hasChildren(option.value)"
          class="pi pi-chevron-right text-gray-400 text-xs"
        />
      </div>

      <!-- Empty state -->
      <div v-if="currentOptions.length === 0" class="px-3 py-4 text-center text-gray-400 text-sm">
        Aucune catégorie
      </div>
    </div>

    <!-- Click outside to close -->
    <div
      v-if="isOpen"
      class="fixed inset-0 z-40"
      @click="isOpen = false"
    />
  </div>
</template>

<script setup lang="ts">
import { useLocaleStore } from '~/stores/locale'

interface CategoryOption {
  value: string
  label: string
  parent_category?: string | null
}

interface Props {
  modelValue: string | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: string | null]
}>()

// Fetch categories from API
const localeStore = useLocaleStore()
const { fetchAttribute } = useAttributes()

const categories = ref<CategoryOption[]>([])
const isOpen = ref(false)
const currentParent = ref<string | null>(null)
const displayValue = ref('')

// Load categories on mount
onMounted(async () => {
  try {
    const result = await fetchAttribute('categories', localeStore.locale)
    categories.value = result.map(c => ({
      value: c.value,
      label: c.label,
      parent_category: c.parent_category ?? null
    }))

    // Initialize display value if there's a model value
    if (props.modelValue) {
      updateDisplayValue()
    }
  } catch (error) {
    console.error('Failed to load categories:', error)
  }
})

/**
 * Get root categories (no parent or parent is 'clothing'/'other')
 */
const getRootCategories = (): CategoryOption[] => {
  return categories.value.filter(cat => {
    const parent = cat.parent_category
    return parent === 'clothing' || parent === 'other'
  })
}

/**
 * Get categories at a specific parent level
 */
const getCategoriesAtLevel = (parentValue: string | null): CategoryOption[] => {
  if (parentValue === null) {
    return getRootCategories()
  }
  return categories.value.filter(cat => cat.parent_category === parentValue)
}

/**
 * Check if a category has children
 */
const hasChildren = (categoryValue: string): boolean => {
  return categories.value.some(cat => cat.parent_category === categoryValue)
}

/**
 * Current options to display
 */
const currentOptions = computed(() => {
  return getCategoriesAtLevel(currentParent.value)
})

/**
 * Toggle dropdown
 */
const toggleDropdown = () => {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    // Reset navigation when opening
    currentParent.value = null
  }
}

/**
 * Select "All categories"
 */
const selectAll = () => {
  emit('update:modelValue', null)
  displayValue.value = ''
  isOpen.value = false
}

/**
 * Handle category selection
 */
const handleSelect = (option: CategoryOption) => {
  // If has children, navigate into it
  if (hasChildren(option.value)) {
    currentParent.value = option.value
    return
  }

  // Leaf or parent without children - select it
  emit('update:modelValue', option.value)
  displayValue.value = getCategoryPath(option.value)
  isOpen.value = false
}

/**
 * Go back one level
 */
const goBack = () => {
  if (!currentParent.value) return

  const currentCategory = categories.value.find(c => c.value === currentParent.value)
  if (currentCategory) {
    const parent = currentCategory.parent_category
    // If going back to root level (clothing/other), set to null
    if (parent === 'clothing' || parent === 'other' || !parent) {
      currentParent.value = null
    } else {
      currentParent.value = parent
    }
  }
}

/**
 * Get full category path for display
 */
const getCategoryPath = (categoryValue: string): string => {
  const category = categories.value.find(c => c.value === categoryValue)
  if (!category) return categoryValue

  const trail: string[] = []
  let current: CategoryOption | undefined = category

  while (current) {
    // Skip root parents (clothing/other)
    if (current.parent_category !== 'clothing' && current.parent_category !== 'other') {
      trail.unshift(current.label)
    } else {
      trail.unshift(current.label)
      break
    }

    if (!current.parent_category) break
    current = categories.value.find(c => c.value === current!.parent_category)
  }

  return trail.join(' > ')
}

/**
 * Update display value from model
 */
const updateDisplayValue = () => {
  if (props.modelValue) {
    displayValue.value = getCategoryPath(props.modelValue)
  } else {
    displayValue.value = ''
  }
}

// Watch for external value changes
watch(() => props.modelValue, () => {
  updateDisplayValue()
})

// Watch categories loading
watch(() => categories.value, () => {
  if (props.modelValue) {
    updateDisplayValue()
  }
})
</script>
