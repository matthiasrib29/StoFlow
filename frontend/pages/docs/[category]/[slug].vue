<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <!-- Header -->
    <LayoutHeaderPublic />

    <!-- Main Content -->
    <main class="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 pt-24 w-full">
      <div class="flex gap-8">
        <!-- Sidebar -->
        <DocsDocSidebar
          :categories="categories"
          :loading="sidebarLoading"
          :active-category-slug="categorySlug"
          :active-article-slug="articleSlug"
          class="hidden lg:block"
        />

        <!-- Article Content -->
        <article class="flex-1 min-w-0">
          <!-- Breadcrumb -->
          <nav class="mb-6">
            <ol class="flex items-center gap-2 text-sm text-gray-500">
              <li>
                <NuxtLink to="/docs" class="hover:text-secondary-900">
                  Documentation
                </NuxtLink>
              </li>
              <li><i class="pi pi-angle-right text-xs" /></li>
              <li v-if="article?.category_name">
                <NuxtLink
                  :to="`/docs/${categorySlug}`"
                  class="hover:text-secondary-900"
                >
                  {{ article.category_name }}
                </NuxtLink>
              </li>
              <li v-if="article?.category_name"><i class="pi pi-angle-right text-xs" /></li>
              <li class="text-secondary-900 font-medium truncate">
                {{ article?.title || 'Chargement...' }}
              </li>
            </ol>
          </nav>

          <!-- Loading State (only shown on initial load) -->
            <div v-if="loading && !article" class="bg-white rounded-xl border border-gray-200 p-8">
              <div class="animate-pulse space-y-4">
                <div class="h-8 bg-gray-200 rounded w-3/4" />
                <div class="h-4 bg-gray-100 rounded w-1/4" />
                <div class="space-y-3 mt-8">
                  <div class="h-4 bg-gray-100 rounded" />
                  <div class="h-4 bg-gray-100 rounded" />
                  <div class="h-4 bg-gray-100 rounded w-5/6" />
                </div>
              </div>
            </div>

            <!-- Error State -->
            <div v-else-if="error && !article" class="bg-white rounded-xl border border-gray-200 p-8 text-center">
              <i class="pi pi-exclamation-circle text-5xl text-red-400 mb-4" />
              <h3 class="text-xl font-semibold text-secondary-900 mb-2">
                Article introuvable
              </h3>
              <p class="text-gray-600 mb-4">{{ error }}</p>
              <NuxtLink
                to="/docs"
                class="inline-flex items-center gap-2 px-4 py-2 bg-primary-400 text-secondary-900 font-semibold rounded-lg hover:bg-primary-500 transition-colors"
              >
                <i class="pi pi-arrow-left" />
                Retour à la documentation
              </NuxtLink>
            </div>

            <!-- Article Content -->
            <div
              v-else-if="article"
              class="bg-white rounded-xl border border-gray-200 p-8"
            >
            <!-- Article Header -->
            <header class="mb-8 pb-6 border-b border-gray-100">
              <div class="flex items-center gap-2 mb-4">
                <span
                  v-if="article.category_name"
                  class="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-primary-700 bg-primary-50 rounded-full"
                >
                  {{ article.category_name }}
                </span>
              </div>
              <h1 class="text-3xl font-bold text-secondary-900 mb-3">
                {{ article.title }}
              </h1>
              <p v-if="article.summary" class="text-lg text-gray-600">
                {{ article.summary }}
              </p>
              <div class="flex items-center gap-4 mt-4 text-sm text-gray-500">
                <span class="flex items-center gap-1">
                  <i class="pi pi-calendar" />
                  Mis &agrave; jour le {{ formatDate(article.updated_at) }}
                </span>
              </div>
            </header>

            <!-- Article Body (Markdown rendered) -->
            <div
              class="prose prose-lg max-w-none prose-headings:text-secondary-900 prose-a:text-primary-600 prose-code:bg-gray-100 prose-code:px-1 prose-code:rounded"
              v-html="sanitizedContent"
            />

            <!-- Article Footer -->
            <footer class="mt-12 pt-6 border-t border-gray-100">
              <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <p class="text-gray-500 text-sm">
                  Cet article vous a-t-il &eacute;t&eacute; utile ?
                </p>
                <NuxtLink
                  to="/docs"
                  class="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 font-medium"
                >
                  <i class="pi pi-arrow-left" />
                  Retour &agrave; la documentation
                </NuxtLink>
              </div>
            </footer>
          </div>
        </article>
      </div>
    </main>

    <!-- Footer -->
    <div class="mt-12">
      <LayoutFooterMinimal />
    </div>
  </div>
</template>

<script setup lang="ts">
import { marked } from 'marked'
import { formatDate } from '~/utils/formatters'

definePageMeta({
  layout: 'docs' // Use docs layout for consistent rendering
})

const route = useRoute()
const categorySlug = computed(() => route.params.category as string)
const articleSlug = computed(() => route.params.slug as string)

const {
  categories,
  currentArticle: article,
  loading,
  error,
  fetchDocumentationIndex,
  fetchArticle
} = useDocs()

const { sanitizeHtml } = useSanitizeHtml()

// Sidebar loading state
const sidebarLoading = ref(true)

// Load article and sidebar data
onMounted(async () => {
  // Load sidebar categories
  fetchDocumentationIndex().finally(() => {
    sidebarLoading.value = false
  })

  // Load article
  await fetchArticle(categorySlug.value, articleSlug.value)
})

// Watch for route changes
watch([categorySlug, articleSlug], async ([newCategory, newArticle]) => {
  await fetchArticle(newCategory, newArticle)
})

// Render Markdown content and sanitize it
const renderedContent = computed(() => {
  if (!article.value?.content) return ''
  return marked(article.value.content) as string
})

const sanitizedContent = computed(() => {
  return sanitizeHtml(renderedContent.value)
})

// SEO
useSeoMeta({
  title: computed(() => article.value ? `${article.value.title} - Documentation Stoflow` : 'Documentation - Stoflow'),
  description: computed(() => article.value?.summary || 'Documentation Stoflow')
})
</script>
