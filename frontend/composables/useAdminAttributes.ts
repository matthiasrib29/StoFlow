/**
 * Composable for admin attributes management
 *
 * Provides methods to CRUD brands, categories, colors, and materials
 */

import { useApi } from '~/composables/useApi'

// Types
export type AttributeType = 'brands' | 'categories' | 'colors' | 'materials'

export interface AdminBrand {
  pk: string
  name: string
  name_fr: string | null
  description: string | null
  vinted_id: string | null
  monitoring: boolean
  sector_jeans: string | null
  sector_jacket: string | null
}

export interface AdminCategory {
  pk: string
  name_en: string
  name_fr: string | null
  name_de: string | null
  name_it: string | null
  name_es: string | null
  parent_category: string | null
  genders: string[] | null
}

export interface AdminColor {
  pk: string
  name_en: string
  name_fr: string | null
  name_de: string | null
  name_it: string | null
  name_es: string | null
  name_nl: string | null
  name_pl: string | null
  hex_code: string | null
}

export interface AdminMaterial {
  pk: string
  name_en: string
  name_fr: string | null
  name_de: string | null
  name_it: string | null
  name_es: string | null
  name_nl: string | null
  name_pl: string | null
  vinted_id: number | null
}

export type AdminAttribute = AdminBrand | AdminCategory | AdminColor | AdminMaterial

export interface AttributeListResponse {
  items: AdminAttribute[]
  total: number
  skip: number
  limit: number
}

export interface AttributeFilters {
  skip?: number
  limit?: number
  search?: string
}

export const useAdminAttributes = () => {
  const api = useApi()

  // State (per type)
  const brands = ref<AdminBrand[]>([])
  const categories = ref<AdminCategory[]>([])
  const colors = ref<AdminColor[]>([])
  const materials = ref<AdminMaterial[]>([])

  const totals = ref<Record<AttributeType, number>>({
    brands: 0,
    categories: 0,
    colors: 0,
    materials: 0,
  })

  const isLoading = ref(false)
  const error = ref<string | null>(null)

  /**
   * Get items ref for a specific type
   */
  const getItemsRef = (type: AttributeType) => {
    switch (type) {
      case 'brands':
        return brands
      case 'categories':
        return categories
      case 'colors':
        return colors
      case 'materials':
        return materials
    }
  }

  /**
   * Fetch attributes for a specific type
   */
  const fetchAttributes = async (
    type: AttributeType,
    filters?: AttributeFilters
  ): Promise<AttributeListResponse> => {
    isLoading.value = true
    error.value = null

    try {
      const queryParams = new URLSearchParams()

      if (filters?.skip !== undefined) queryParams.set('skip', filters.skip.toString())
      if (filters?.limit !== undefined) queryParams.set('limit', filters.limit.toString())
      if (filters?.search) queryParams.set('search', filters.search)

      const query = queryParams.toString() ? `?${queryParams.toString()}` : ''
      const response = await api.get<AttributeListResponse>(`/api/admin/attributes/${type}${query}`)

      // Update the correct ref based on type
      const itemsRef = getItemsRef(type)
      itemsRef.value = response.items as any
      totals.value[type] = response.total

      return response
    } catch (e: any) {
      error.value = e.message || `Failed to fetch ${type}`
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Get a single attribute
   */
  const getAttribute = async (type: AttributeType, pk: string): Promise<AdminAttribute> => {
    isLoading.value = true
    error.value = null

    try {
      return await api.get<AdminAttribute>(`/api/admin/attributes/${type}/${encodeURIComponent(pk)}`)
    } catch (e: any) {
      error.value = e.message || `Failed to fetch ${type}`
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Create a new attribute
   */
  const createAttribute = async (type: AttributeType, data: Record<string, any>): Promise<AdminAttribute> => {
    isLoading.value = true
    error.value = null

    try {
      return await api.post<AdminAttribute>(`/api/admin/attributes/${type}`, data)
    } catch (e: any) {
      error.value = e.message || `Failed to create ${type}`
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Update an attribute
   */
  const updateAttribute = async (
    type: AttributeType,
    pk: string,
    data: Record<string, any>
  ): Promise<AdminAttribute> => {
    isLoading.value = true
    error.value = null

    try {
      return await api.patch<AdminAttribute>(
        `/api/admin/attributes/${type}/${encodeURIComponent(pk)}`,
        data
      )
    } catch (e: any) {
      error.value = e.message || `Failed to update ${type}`
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Delete an attribute
   */
  const deleteAttribute = async (type: AttributeType, pk: string): Promise<void> => {
    isLoading.value = true
    error.value = null

    try {
      await api.delete(`/api/admin/attributes/${type}/${encodeURIComponent(pk)}`)
    } catch (e: any) {
      error.value = e.message || `Failed to delete ${type}`
      throw e
    } finally {
      isLoading.value = false
    }
  }

  return {
    // State
    brands,
    categories,
    colors,
    materials,
    totals,
    isLoading,
    error,

    // Methods
    fetchAttributes,
    getAttribute,
    createAttribute,
    updateAttribute,
    deleteAttribute,
  }
}
