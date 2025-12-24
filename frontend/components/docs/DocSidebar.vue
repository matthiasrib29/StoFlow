<template>
  <aside class="w-64 flex-shrink-0">
    <nav class="sticky top-24 space-y-2">
      <!-- Categories -->
      <div v-for="category in categories" :key="category.id" class="mb-4">
        <!-- Category Header -->
        <button
          class="w-full flex items-center gap-2 px-3 py-2 text-left font-semibold text-secondary-900 hover:bg-gray-50 rounded-lg transition-colors"
          :class="{ 'bg-primary-50': isActiveCategorySlug === category.slug }"
          @click="toggleCategory(category.slug)"
        >
          <i v-if="category.icon" :class="['pi', category.icon, 'text-primary-500']" />
          <i v-else class="pi pi-folder text-primary-500" />
          <span class="flex-1">{{ category.name }}</span>
          <i
            :class="[
              'pi pi-chevron-down text-xs transition-transform',
              expandedCategories.includes(category.slug) ? 'rotate-180' : ''
            ]"
          />
        </button>

        <!-- Articles List -->
        <Transition
          enter-active-class="transition-all duration-200 ease-out"
          enter-from-class="opacity-0 max-h-0"
          enter-to-class="opacity-100 max-h-96"
          leave-active-class="transition-all duration-150 ease-in"
          leave-from-class="opacity-100 max-h-96"
          leave-to-class="opacity-0 max-h-0"
        >
          <ul
            v-if="expandedCategories.includes(category.slug)"
            class="ml-4 mt-1 space-y-1 overflow-hidden"
          >
            <li v-for="article in category.articles" :key="article.id">
              <NuxtLink
                :to="`/docs/${category.slug}/${article.slug}`"
                class="block px-3 py-1.5 text-sm text-gray-600 hover:text-secondary-900 hover:bg-gray-50 rounded-md transition-colors"
                :class="{
                  'bg-primary-50 text-secondary-900 font-medium': isActiveArticle(category.slug, article.slug)
                }"
              >
                {{ article.title }}
              </NuxtLink>
            </li>
          </ul>
        </Transition>
      </div>

      <!-- Empty State -->
      <div v-if="categories.length === 0 && !loading" class="text-center py-8 text-gray-500">
        <i class="pi pi-book text-3xl mb-2 block" />
        <p class="text-sm">Aucune documentation disponible</p>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="space-y-3">
        <div v-for="i in 3" :key="i" class="animate-pulse">
          <div class="h-8 bg-gray-200 rounded-lg mb-2" />
          <div class="ml-4 space-y-1">
            <div class="h-5 bg-gray-100 rounded w-3/4" />
            <div class="h-5 bg-gray-100 rounded w-2/3" />
          </div>
        </div>
      </div>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import type { DocCategory } from '~/composables/useDocs'

const props = defineProps<{
  categories: DocCategory[]
  loading?: boolean
  activeCategorySlug?: string
  activeArticleSlug?: string
}>()

const route = useRoute()

// Track expanded categories
const expandedCategories = ref<string[]>([])

// Initialize expanded categories based on current route
onMounted(() => {
  if (props.activeCategorySlug) {
    expandedCategories.value = [props.activeCategorySlug]
  } else if (props.categories.length > 0) {
    // Expand first category by default
    expandedCategories.value = [props.categories[0].slug]
  }
})

// Watch for route changes to update expanded state
watch(() => props.activeCategorySlug, (newSlug) => {
  if (newSlug && !expandedCategories.value.includes(newSlug)) {
    expandedCategories.value.push(newSlug)
  }
})

// Computed to get active category slug from props or route
const isActiveCategorySlug = computed(() => {
  return props.activeCategorySlug || route.params.category as string
})

// Toggle category expansion
const toggleCategory = (slug: string) => {
  const index = expandedCategories.value.indexOf(slug)
  if (index > -1) {
    expandedCategories.value.splice(index, 1)
  } else {
    expandedCategories.value.push(slug)
  }
}

// Check if article is active
const isActiveArticle = (categorySlug: string, articleSlug: string): boolean => {
  const routeCategory = route.params.category as string
  const routeArticle = route.params.slug as string
  return categorySlug === routeCategory && articleSlug === routeArticle
}
</script>
