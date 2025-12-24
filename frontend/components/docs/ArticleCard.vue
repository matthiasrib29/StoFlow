<template>
  <NuxtLink
    :to="`/docs/${article.category_slug}/${article.slug}`"
    class="block p-6 bg-white border border-gray-200 rounded-xl hover:border-primary-300 hover:shadow-md transition-all group"
  >
    <!-- Category Badge -->
    <div v-if="showCategory && article.category_name" class="mb-3">
      <span class="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-primary-700 bg-primary-50 rounded-full">
        <i v-if="categoryIcon" :class="['pi', categoryIcon, 'text-xs']" />
        {{ article.category_name }}
      </span>
    </div>

    <!-- Title -->
    <h3 class="text-lg font-semibold text-secondary-900 group-hover:text-primary-600 transition-colors mb-2">
      {{ article.title }}
    </h3>

    <!-- Summary -->
    <p v-if="article.summary" class="text-gray-600 text-sm line-clamp-2 mb-4">
      {{ article.summary }}
    </p>

    <!-- Read More -->
    <div class="flex items-center gap-1 text-primary-600 text-sm font-medium">
      <span>Lire l'article</span>
      <i class="pi pi-arrow-right text-xs group-hover:translate-x-1 transition-transform" />
    </div>
  </NuxtLink>
</template>

<script setup lang="ts">
import type { DocArticleSummary, DocCategory } from '~/composables/useDocs'

const props = defineProps<{
  article: DocArticleSummary
  category?: DocCategory
  showCategory?: boolean
}>()

// Get category icon
const categoryIcon = computed(() => {
  return props.category?.icon || null
})
</script>
