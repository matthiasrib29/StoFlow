<template>
  <div class="relative">
    <!-- Input field that triggers dropdown -->
    <div
      class="border-2 border-gray-300 rounded-md px-3 py-2.5 cursor-pointer transition-all duration-150
             hover:border-primary-400 hover:shadow-sm
             focus-within:border-primary-500 focus-within:ring-2 focus-within:ring-primary-200 bg-white"
      :class="{ 'border-primary-500 ring-2 ring-primary-200': isOpen }"
      @click="toggleDropdown"
    >
      <div class="flex items-center gap-2">
        <!-- NOUVEAU : Icône sitemap -->
        <i class="pi pi-sitemap text-gray-500 text-sm" />

        <div class="flex-1">
          <span v-if="displayValue" class="text-gray-900 text-sm">
            {{ displayValue }}
          </span>
          <div v-else class="space-y-0.5">
            <span class="text-gray-400 text-sm">Sélectionner une catégorie...</span>
            <span class="text-gray-400 text-xs block">Cliquez pour naviguer</span>
          </div>
        </div>

        <i
          class="pi pi-chevron-down text-gray-400 text-xs transition-transform duration-200"
          :class="{ 'rotate-180': isOpen }"
        />
      </div>
    </div>

    <!-- Dropdown overlay -->
    <div
      v-if="isOpen"
      class="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-y-auto"
    >
      <div
        v-for="option in currentOptions"
        :key="option.value"
        class="px-3 py-2 hover:bg-gray-100 cursor-pointer flex items-center justify-between"
        :class="{ 'bg-primary-50 border-l-2 border-primary-500': option.value === modelValue }"
        @click="handleSelect(option)"
      >
        <!-- Gender selection -->
        <template v-if="option.value.startsWith('__gender__')">
          <span class="font-medium">{{ option.label }}</span>
          <i class="pi pi-chevron-right text-gray-400 text-xs" />
        </template>
        <!-- Back to gender button -->
        <template v-else-if="option.value === '__back_to_gender__'">
          <div class="flex items-center gap-2 text-primary-600 font-semibold">
            <i class="pi pi-arrow-left text-xs" />
            <span>{{ option.label }}</span>
          </div>
        </template>
        <!-- Back button -->
        <template v-else-if="option.value === '__back__'">
          <div class="flex items-center gap-2 text-primary-600 font-semibold">
            <i class="pi pi-arrow-left text-xs" />
            <span>{{ option.label }}</span>
          </div>
        </template>
        <!-- Regular category -->
        <template v-else>
          <span>{{ option.label }}</span>
          <i
            v-if="hasChildren(option.value)"
            class="pi pi-chevron-right text-gray-400 text-xs"
          />
        </template>
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
interface CategoryOption {
  value: string
  label: string
  parent_category?: string | null
  genders?: string[] | null
}

interface Props {
  categories: CategoryOption[]
  modelValue: string | null
  genders?: { value: string; label: string }[]
}

const props = withDefaults(defineProps<Props>(), {
  genders: () => []
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

// Current navigation state
const selectedGender = ref<string | null>(null)
const currentParent = ref<string | null>(null)
const displayValue = ref<string>('')
const isOpen = ref(false)

/**
 * Get categories at a specific parent level
 * Filters by selected gender and skips "Autre"/"Vêtements" parents
 */
const getCategoriesAtLevel = (parentValue: string | null): CategoryOption[] => {
  // Normalize gender for comparison (API returns "Men" but categories store "men")
  const normalizedGender = selectedGender.value?.toLowerCase()

  // At root level (after gender selection), show children of "Autre" and "Vêtements"
  if (parentValue === null && normalizedGender) {
    return props.categories.filter(cat => {
      const parent = cat.parent_category === undefined ? null : cat.parent_category
      // Compare lowercase values for gender matching
      const hasMatchingGender = cat.genders?.some(g => g.toLowerCase() === normalizedGender) || !cat.genders
      return (parent === 'other' || parent === 'clothing') && hasMatchingGender
    })
  }

  // For other levels, filter by parent and gender
  return props.categories.filter(cat => {
    const parent = cat.parent_category === undefined ? null : cat.parent_category
    // Compare lowercase values for gender matching
    const hasMatchingGender = cat.genders?.some(g => g.toLowerCase() === normalizedGender) || !cat.genders
    return parent === parentValue && hasMatchingGender
  })
}

/**
 * Check if a category has children
 */
const hasChildren = (categoryValue: string): boolean => {
  return props.categories.some(cat => cat.parent_category === categoryValue)
}

/**
 * Current options to display in dropdown
 */
const currentOptions = computed(() => {
  const options: CategoryOption[] = []

  // Level 1: Show genders if none selected yet (exclude "Unisexe")
  if (!selectedGender.value) {
    return props.genders
      .filter(g => g.value !== 'unisex')
      .map(g => ({
        value: `__gender__${g.value}`,
        label: g.label,
        parent_category: null
      }))
  }

  // Level 2+: Show "Back to gender" button if at root categories
  if (currentParent.value === null) {
    options.push({
      value: '__back_to_gender__',
      label: 'Changer de genre',
      parent_category: null
    })
  }
  // Or show "Back" button for sub-categories
  else {
    options.push({
      value: '__back__',
      label: 'Retour',
      parent_category: null
    })
  }

  // Add categories at current level
  const categories = getCategoriesAtLevel(currentParent.value)
  options.push(...categories)

  return options
})

/**
 * Get full category path for display with gender first
 */
const getCategoryPath = (categoryValue: string): string => {
  const category = props.categories.find(c => c.value === categoryValue)
  if (!category) return ''

  const trail: string[] = []
  let current: CategoryOption | undefined = category

  // Build category trail (excluding "Vêtements" and "Autre")
  while (current) {
    // Skip "Vêtements" and "Autre" parent categories
    if (current.label !== 'Vêtements' && current.label !== 'Autre') {
      trail.unshift(current.label)
    }
    if (!current.parent_category) {
      break
    }
    current = props.categories.find(c => c.value === current!.parent_category)
  }

  // Prepend gender label at the beginning
  if (category.genders && category.genders.length > 0) {
    const genderValue = category.genders[0]
    const genderOption = props.genders.find(g => g.value === genderValue)
    if (genderOption) {
      trail.unshift(genderOption.label)
    }
  }

  return trail.join(' > ')
}

/**
 * Toggle dropdown open/close
 */
const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}

/**
 * Handle item selection
 */
const handleSelect = (option: CategoryOption) => {
  // Handle gender selection
  if (option.value.startsWith('__gender__')) {
    const genderValue = option.value.replace('__gender__', '')
    selectedGender.value = genderValue
    currentParent.value = null // Reset to root categories
    displayValue.value = '' // Clear display
    // Keep dropdown open to show categories
    return
  }

  // Handle back to gender selection
  if (option.value === '__back_to_gender__') {
    selectedGender.value = null
    currentParent.value = null
    displayValue.value = ''
    // Keep dropdown open
    return
  }

  // Handle back button
  if (option.value === '__back__') {
    goBack()
    // Keep dropdown open
    return
  }

  // If category has children, navigate into it
  if (hasChildren(option.value)) {
    currentParent.value = option.value
    displayValue.value = '' // Clear display
    // Keep dropdown open for navigation
    return
  }

  // Leaf category - emit final selection and close
  emit('update:modelValue', option.value)
  displayValue.value = getCategoryPath(option.value)
  isOpen.value = false // Close dropdown
}

/**
 * Go back one level
 */
const goBack = () => {
  if (currentParent.value === null) return

  // Find parent of current parent
  const currentCategory = props.categories.find(c => c.value === currentParent.value)
  if (currentCategory) {
    const parentCat = currentCategory.parent_category === undefined
      ? null
      : currentCategory.parent_category

    // If parent is "other" or "clothing", go back to root categories (with "Changer de genre")
    if (parentCat === 'other' || parentCat === 'clothing') {
      currentParent.value = null
    } else {
      currentParent.value = parentCat
    }
  }

  displayValue.value = ''
}

/**
 * Initialize from existing value
 */
const initializeFromValue = () => {
  if (!props.modelValue) {
    currentParent.value = null
    displayValue.value = ''
    selectedGender.value = null
    return
  }

  // Set display value to full path
  displayValue.value = getCategoryPath(props.modelValue)

  // Navigate to parent of selected category
  const selectedCategory = props.categories.find(c => c.value === props.modelValue)
  if (selectedCategory) {
    currentParent.value = selectedCategory.parent_category === undefined
      ? null
      : selectedCategory.parent_category

    // Set gender from the selected category to preserve navigation context
    if (selectedCategory.genders && selectedCategory.genders.length > 0) {
      selectedGender.value = selectedCategory.genders[0]
    }
  }
}

// Watch for external value changes
watch(() => props.modelValue, () => {
  initializeFromValue()
}, { immediate: true })

// Watch categories loading
watch(() => props.categories, () => {
  if (props.modelValue) {
    initializeFromValue()
  }
}, { immediate: true })
</script>
