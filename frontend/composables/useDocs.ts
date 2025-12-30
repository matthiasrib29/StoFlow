/**
 * Composable for fetching documentation from the API.
 *
 * Used on the documentation page to display articles.
 * Data comes from the database, allowing content management without code deployment.
 *
 * @author Claude
 * @date 2024-12-24
 */

export interface DocArticleSummary {
  id: number
  category_id: number
  category_slug: string | null
  category_name: string | null
  slug: string
  title: string
  summary: string | null
  display_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface DocArticleDetail extends DocArticleSummary {
  content: string
}

export interface DocCategory {
  id: number
  slug: string
  name: string
  description: string | null
  icon: string | null
  display_order: number
  is_active?: boolean
  article_count?: number
  articles?: DocArticleSummary[]
  created_at?: string
  updated_at?: string
}

export interface DocsIndexResponse {
  categories: DocCategory[]
}

export const useDocs = () => {
  const config = useRuntimeConfig()

  // Use useState for persistent state across route changes (prevents flash)
  const categories = useState<DocCategory[]>('docs-categories', () => [])
  const currentCategory = useState<DocCategory | null>('docs-current-category', () => null)
  const currentArticle = useState<DocArticleDetail | null>('docs-current-article', () => null)
  const loading = useState<boolean>('docs-loading', () => false)
  const error = useState<string | null>('docs-error', () => null)

  /**
   * Fetch documentation index (all categories with articles).
   * This is a public endpoint - no authentication required.
   */
  const fetchDocumentationIndex = async (): Promise<DocCategory[]> => {
    loading.value = true
    error.value = null

    try {
      const data = await $fetch<DocsIndexResponse>(
        `${config.public.apiBaseUrl}/docs`
      )
      categories.value = data.categories
      return data.categories
    } catch (err) {
      console.error('Failed to fetch documentation:', err)
      error.value = 'Failed to load documentation'
      return []
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch articles for a specific category.
   */
  const fetchCategoryArticles = async (categorySlug: string): Promise<DocCategory | null> => {
    loading.value = true
    error.value = null

    try {
      const data = await $fetch<DocCategory>(
        `${config.public.apiBaseUrl}/docs/${categorySlug}`
      )
      currentCategory.value = data
      return data
    } catch (err) {
      console.error(`Failed to fetch category ${categorySlug}:`, err)
      error.value = 'Category not found'
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch a specific article with full content.
   */
  const fetchArticle = async (categorySlug: string, articleSlug: string): Promise<DocArticleDetail | null> => {
    loading.value = true
    error.value = null

    try {
      const data = await $fetch<DocArticleDetail>(
        `${config.public.apiBaseUrl}/docs/${categorySlug}/${articleSlug}`
      )
      currentArticle.value = data
      return data
    } catch (err) {
      console.error(`Failed to fetch article ${articleSlug}:`, err)
      error.value = 'Article not found'
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Get category by slug from loaded categories.
   */
  const getCategoryBySlug = (slug: string): DocCategory | undefined => {
    return categories.value.find(cat => cat.slug === slug)
  }

  /**
   * Get all articles across all categories.
   */
  const getAllArticles = (): DocArticleSummary[] => {
    return categories.value.flatMap(cat => cat.articles || [])
  }

  /**
   * Search articles by title or summary.
   */
  const searchArticles = (query: string): DocArticleSummary[] => {
    const lowerQuery = query.toLowerCase()
    return getAllArticles().filter(article =>
      article.title.toLowerCase().includes(lowerQuery) ||
      (article.summary && article.summary.toLowerCase().includes(lowerQuery))
    )
  }

  return {
    // State
    categories,
    currentCategory,
    currentArticle,
    loading,
    error,
    // Methods
    fetchDocumentationIndex,
    fetchCategoryArticles,
    fetchArticle,
    getCategoryBySlug,
    getAllArticles,
    searchArticles
  }
}
