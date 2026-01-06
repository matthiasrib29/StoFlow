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
          :loading="loading"
          class="hidden lg:block"
        />

        <!-- Content Area -->
        <div class="flex-1 min-w-0">
          <!-- Hero Section -->
          <div class="mb-12">
            <h2 class="text-3xl font-bold text-secondary-900 mb-4">
              Centre d'aide Stoflow
            </h2>
            <p class="text-lg text-gray-600 max-w-2xl">
              Bienvenue dans notre documentation. Trouvez des guides, tutoriels et
              r&eacute;ponses &agrave; vos questions pour tirer le meilleur parti de Stoflow.
            </p>
          </div>

          <!-- Categories Grid (stays visible during reload with reduced opacity) -->
          <div
            v-if="categories.length > 0"
            class="space-y-12 transition-opacity duration-150"
            :class="{ 'opacity-60': loading }"
          >
            <section v-for="category in categories" :key="category.id">
              <!-- Category Header -->
              <div class="flex items-center gap-3 mb-6">
                <div class="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                  <i
                    :class="['pi', category.icon || 'pi-folder', 'text-primary-600 text-lg']"
                  />
                </div>
                <div>
                  <h3 class="text-xl font-semibold text-secondary-900">
                    {{ category.name }}
                  </h3>
                  <p v-if="category.description" class="text-sm text-gray-500">
                    {{ category.description }}
                  </p>
                </div>
              </div>

              <!-- Articles Grid -->
              <div
                v-if="category.articles && category.articles.length > 0"
                class="grid gap-4 md:grid-cols-2"
              >
                <DocsArticleCard
                  v-for="article in category.articles"
                  :key="article.id"
                  :article="article"
                  :category="category"
                />
              </div>

              <!-- No Articles -->
              <div
                v-else
                class="text-center py-8 bg-white rounded-xl border border-gray-200"
              >
                <i class="pi pi-file text-3xl text-gray-300 mb-2" />
                <p class="text-gray-500">Aucun article dans cette cat&eacute;gorie</p>
              </div>
            </section>
          </div>

          <!-- Loading State (only on initial load) -->
          <div v-else-if="loading && categories.length === 0" class="space-y-8">
            <div v-for="i in 2" :key="i" class="animate-pulse">
              <div class="flex items-center gap-3 mb-6">
                <div class="w-10 h-10 bg-gray-200 rounded-lg" />
                <div>
                  <div class="h-6 bg-gray-200 rounded w-32 mb-1" />
                  <div class="h-4 bg-gray-100 rounded w-48" />
                </div>
              </div>
              <div class="grid gap-4 md:grid-cols-2">
                <div v-for="j in 2" :key="j" class="h-40 bg-gray-100 rounded-xl" />
              </div>
            </div>
          </div>

          <!-- Error State -->
          <div v-else-if="error" class="text-center py-12">
            <i class="pi pi-exclamation-circle text-5xl text-red-400 mb-4" />
            <h3 class="text-xl font-semibold text-secondary-900 mb-2">
              Erreur de chargement
            </h3>
            <p class="text-gray-600 mb-4">{{ error }}</p>
            <button
              class="px-4 py-2 bg-primary-400 text-secondary-900 font-semibold rounded-lg hover:bg-primary-500 transition-colors"
              @click="loadDocs"
            >
              Réessayer
            </button>
          </div>

          <!-- Empty State -->
          <div
            v-else-if="categories.length === 0"
            class="text-center py-12"
          >
            <i class="pi pi-book text-5xl text-gray-300 mb-4" />
            <h3 class="text-xl font-semibold text-secondary-900 mb-2">
              Documentation en cours de r&eacute;daction
            </h3>
            <p class="text-gray-600">
              Notre documentation sera bient&ocirc;t disponible. Revenez nous voir !
            </p>
          </div>
        </div>
      </div>
    </main>

    <!-- Footer -->
    <div class="mt-12">
      <LayoutFooterMinimal />
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'docs' // Use docs layout for consistent rendering
})

// SEO
useSeoMeta({
  title: 'Documentation - Stoflow',
  description: 'Centre d\'aide et documentation Stoflow. Guides, tutoriels et FAQ pour la gestion multi-marketplace.'
})

const { categories, loading, error, fetchDocumentationIndex } = useDocs()

// Load documentation on mount
const loadDocs = async () => {
  await fetchDocumentationIndex()
}

onMounted(() => {
  loadDocs()
})
</script>
