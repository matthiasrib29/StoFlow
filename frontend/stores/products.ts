import { defineStore } from 'pinia'
import { useAuthStore } from './auth'

export interface Product {
  // Identifiants
  id: number

  // Informations de base
  title: string
  description: string
  price: number | null  // Peut être null (calculé automatiquement)

  // Attributs obligatoires (Updated 2025-12-08)
  category: string
  condition: string
  brand: string
  label_size: string  // Renamed from 'size' to match API
  color: string

  // Attributs optionnels avec FK
  material?: string | null
  fit?: string | null
  gender?: string | null
  season?: string | null

  // Attributs supplémentaires
  condition_sup?: string | null
  rise?: string | null
  closure?: string | null
  sleeve_length?: string | null
  origin?: string | null
  decade?: string | null
  trend?: string | null
  name_sup?: string | null
  location?: string | null
  model?: string | null

  // Dimensions (cm)
  dim1?: number | null  // Tour de poitrine/Épaules
  dim2?: number | null  // Longueur totale
  dim3?: number | null  // Longueur manche
  dim4?: number | null  // Tour de taille
  dim5?: number | null  // Tour de hanches
  dim6?: number | null  // Entrejambe

  // Stock
  stock_quantity: number  // Default: 1

  // Status et workflow
  status: string  // 'draft', 'published', 'sold', 'archived'
  is_active?: boolean  // Indicates if product is active/visible
  published_at?: string | null
  sold_at?: string | null

  // Timestamps
  created_at: string
  updated_at: string
  deleted_at?: string | null

  // Images (JSONB array)
  images?: Array<{
    url: string
    order: number
    created_at: string
  }>

  // Computed/Legacy properties (for backwards compatibility)
  image_url?: string  // Primary image URL
  size?: string  // Alias for label_size
}

/**
 * Helper pour obtenir l'URL complète de la première image d'un produit
 */
export const getProductImageUrl = (product: Product): string => {
  if (!product.images || product.images.length === 0) {
    // Image placeholder par défaut
    return '/images/placeholder-product.png'
  }

  // Trier par order et prendre la première
  const sortedImages = [...product.images].sort((a, b) => a.order - b.order)
  const firstImage = sortedImages[0]

  if (!firstImage || !firstImage.url) {
    return '/images/placeholder-product.png'
  }

  // Les images sont stockées avec URL absolue (R2/CDN)
  return firstImage.url
}

export const useProductsStore = defineStore('products', {
  state: () => ({
    products: [] as Product[],
    selectedProduct: null as Product | null,
    isLoading: false,
    error: null as string | null,
    // Pagination
    pagination: {
      total: 0,
      page: 1,
      pageSize: 20,
      totalPages: 0
    }
  }),

  getters: {
    activeProducts: (state) => state.products.filter(p => p.status === 'published' && !p.deleted_at),
    draftProducts: (state) => state.products.filter(p => p.status === 'draft' && !p.deleted_at),
    totalProducts: (state) => state.products.length,
    getProductById: (state) => (id: number) => state.products.find(p => p.id === id)
  },

  actions: {
    /**
     * Charger les produits depuis l'API avec pagination
     */
    async fetchProducts(options?: {
      page?: number
      limit?: number
      status?: string
      category?: string
      brand?: string
    }) {
      this.isLoading = true
      this.error = null

      try {
        const api = useApi()

        // Build query params
        const params = new URLSearchParams()
        params.append('page', String(options?.page || 1))
        params.append('limit', String(options?.limit || 20))
        if (options?.status) params.append('status', options.status)
        if (options?.category) params.append('category', options.category)
        if (options?.brand) params.append('brand', options.brand)

        const queryString = params.toString()
        const endpoint = `/api/products?${queryString}`

        const data = await api.get<{
          products: Product[]
          total: number
          page: number
          page_size: number
          total_pages: number
        }>(endpoint)

        this.products = data?.products || []
        this.pagination = {
          total: data?.total || 0,
          page: data?.page || 1,
          pageSize: data?.page_size || 20,
          totalPages: data?.total_pages || 0
        }
      } catch (error: any) {
        this.error = error.message
        console.error('Error fetching products:', error)
        throw error
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Récupérer un produit par ID depuis l'API
     */
    async fetchProduct(id: number) {
      this.isLoading = true
      this.error = null

      try {
        const api = useApi()
        const product = await api.get<Product>(`/api/products/${id}`)
        this.selectedProduct = product
        return product
      } catch (error: any) {
        this.error = error.message
        console.error('Error fetching product:', error)
        throw error
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Créer un nouveau produit via l'API
     */
    async createProduct(productData: Partial<Product>) {
      this.isLoading = true
      this.error = null

      try {
        const api = useApi()
        const newProduct = await api.post<Product>('/api/products', productData)
        if (newProduct) {
          this.products.push(newProduct)
        }
        return newProduct
      } catch (error: any) {
        this.error = error.message
        console.error('Error creating product:', error)
        throw error
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Mettre à jour un produit existant via l'API
     */
    async updateProduct(id: number, productData: Partial<Product>) {
      this.isLoading = true
      this.error = null

      try {
        const api = useApi()
        const updatedProduct = await api.patch<Product>(`/api/products/${id}`, productData)

        // Mettre à jour dans la liste locale
        const index = this.products.findIndex(p => p.id === id)
        if (index !== -1 && updatedProduct) {
          this.products[index] = updatedProduct
        }

        return updatedProduct
      } catch (error: any) {
        this.error = error.message
        console.error('Error updating product:', error)
        throw error
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Supprimer un produit via l'API (soft delete)
     */
    async deleteProduct(id: number) {
      this.isLoading = true
      this.error = null

      try {
        const api = useApi()
        await api.delete(`/api/products/${id}`)

        // Retirer de la liste locale
        const index = this.products.findIndex(p => p.id === id)
        if (index !== -1) {
          this.products.splice(index, 1)
        }
      } catch (error: any) {
        this.error = error.message
        console.error('Error deleting product:', error)
        throw error
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Uploader une image pour un produit
     */
    async uploadProductImage(productId: number, file: File, displayOrder: number = 0) {
      this.isLoading = true
      this.error = null

      try {
        const authStore = useAuthStore()
        const config = useRuntimeConfig()

        const formData = new FormData()
        formData.append('file', file)
        formData.append('display_order', displayOrder.toString())

        // Note: Pour FormData, on doit utiliser fetch directement avec le token actuel
        // car useApi() gère JSON par défaut. On garde la logique manuelle mais avec
        // le token du store
        const token = authStore.token

        const response = await fetch(`${config.public.apiUrl}/api/products/${productId}/images`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
            // Note: Don't set Content-Type for FormData, browser will set it with boundary
          },
          body: formData
        })

        // Si 401, essayer de refresh et retry
        if (response.status === 401) {
          const refreshed = await authStore.refreshAccessToken()
          if (refreshed) {
            const retryResponse = await fetch(`${config.public.apiUrl}/api/products/${productId}/images`, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${authStore.token}`
              },
              body: formData
            })

            if (!retryResponse.ok) {
              const errorData = await retryResponse.json().catch(() => ({ detail: retryResponse.statusText }))
              throw new Error(errorData.detail || `HTTP ${retryResponse.status}: ${retryResponse.statusText}`)
            }

            return await retryResponse.json()
          } else {
            throw new Error('Session expirée. Veuillez vous reconnecter.')
          }
        }

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: response.statusText }))
          throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
        }

        const imageData = await response.json()
        return imageData
      } catch (error: any) {
        this.error = error.message
        console.error('Error uploading image:', error)
        throw error
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Supprimer une image de produit
     */
    async deleteProductImage(productId: number, imageId: number) {
      this.isLoading = true
      this.error = null

      try {
        const api = useApi()
        await api.delete(`/api/products/${productId}/images/${imageId}`)
      } catch (error: any) {
        this.error = error.message
        console.error('Error deleting image:', error)
        throw error
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Réorganiser les images d'un produit
     * @param productId ID du produit
     * @param imageOrder Mapping imageId -> newPosition
     */
    async reorderProductImages(productId: number, imageOrder: Record<number, number>) {
      this.isLoading = true
      this.error = null

      try {
        const api = useApi()
        await api.put(`/api/products/${productId}/images/reorder`, imageOrder)
      } catch (error: any) {
        this.error = error.message
        console.error('Error reordering images:', error)
        throw error
      } finally {
        this.isLoading = false
      }
    }
  }
})
