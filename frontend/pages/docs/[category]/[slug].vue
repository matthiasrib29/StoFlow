<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div class="flex items-center justify-between">
          <!-- Logo & Back -->
          <div class="flex items-center gap-4">
            <NuxtLink to="/" class="flex items-center gap-2 text-secondary-900 hover:text-primary-600 transition-colors">
              <div class="w-8 h-8 bg-secondary-900 rounded-lg flex items-center justify-center">
                <span class="text-primary-400 font-bold text-sm">S</span>
              </div>
              <span class="text-xl font-bold">Stoflow</span>
            </NuxtLink>
            <span class="text-gray-300">|</span>
            <NuxtLink to="/docs" class="text-gray-600 hover:text-secondary-900 transition-colors">
              Documentation
            </NuxtLink>
          </div>

          <!-- Actions -->
          <div class="hidden md:flex items-center gap-4">
            <NuxtLink
              to="/login"
              class="text-gray-600 hover:text-secondary-900 transition-colors"
            >
              Connexion
            </NuxtLink>
            <NuxtLink
              to="/register"
              class="px-4 py-2 bg-secondary-900 text-white rounded-lg hover:bg-secondary-800 transition-colors"
            >
              Essai gratuit
            </NuxtLink>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
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
                <NuxtLink to="/docs" class="hover:text-secondary-900 transition-colors">
                  Documentation
                </NuxtLink>
              </li>
              <li><i class="pi pi-angle-right text-xs" /></li>
              <li v-if="article?.category_name">
                <NuxtLink
                  :to="`/docs/${categorySlug}`"
                  class="hover:text-secondary-900 transition-colors"
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

          <!-- Loading State -->
          <div v-if="loading" class="bg-white rounded-xl border border-gray-200 p-8">
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
          <div v-else-if="error" class="bg-white rounded-xl border border-gray-200 p-8 text-center">
            <i class="pi pi-exclamation-circle text-5xl text-red-400 mb-4" />
            <h3 class="text-xl font-semibold text-secondary-900 mb-2">
              Article introuvable
            </h3>
            <p class="text-gray-600 mb-4">{{ error }}</p>
            <NuxtLink
              to="/docs"
              class="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              <i class="pi pi-arrow-left" />
              Retour &agrave; la documentation
            </NuxtLink>
          </div>

          <!-- Article Content -->
          <div v-else-if="article" class="bg-white rounded-xl border border-gray-200 p-8">
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
              v-html="renderedContent"
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
    <footer class="bg-white border-t border-gray-200 mt-12">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div class="flex flex-col md:flex-row justify-between items-center gap-4">
          <div class="flex items-center gap-2">
            <div class="w-6 h-6 bg-secondary-900 rounded flex items-center justify-center">
              <span class="text-primary-400 font-bold text-xs">S</span>
            </div>
            <span class="text-gray-600 text-sm">
              &copy; {{ new Date().getFullYear() }} Stoflow. Tous droits r&eacute;serv&eacute;s.
            </span>
          </div>
          <div class="flex items-center gap-6 text-sm">
            <NuxtLink to="/" class="text-gray-600 hover:text-secondary-900">
              Accueil
            </NuxtLink>
            <NuxtLink to="/#pricing" class="text-gray-600 hover:text-secondary-900">
              Tarifs
            </NuxtLink>
            <NuxtLink to="/login" class="text-gray-600 hover:text-secondary-900">
              Connexion
            </NuxtLink>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { marked } from 'marked'

definePageMeta({
  layout: false // Custom layout for docs page
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

// Render Markdown content
const renderedContent = computed(() => {
  if (!article.value?.content) return ''
  return marked(article.value.content)
})

// Format date
const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })
}

// SEO
useSeoMeta({
  title: computed(() => article.value ? `${article.value.title} - Documentation Stoflow` : 'Documentation - Stoflow'),
  description: computed(() => article.value?.summary || 'Documentation Stoflow')
})
</script>
