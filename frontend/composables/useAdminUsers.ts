/**
 * Composable for admin user management
 *
 * Provides CRUD operations for managing users (admin only)
 */

import { useApi } from '~/composables/useApi'

export interface AdminUser {
  id: number
  email: string
  full_name: string
  role: 'admin' | 'user' | 'support'
  is_active: boolean
  subscription_tier: string
  subscription_status: string
  business_name: string | null
  account_type: string | null
  phone: string | null
  country: string
  language: string
  email_verified: boolean
  failed_login_attempts: number
  locked_until: string | null
  last_login: string | null
  current_products_count: number
  current_platforms_count: number
  created_at: string
  updated_at: string
}

export interface AdminUserListResponse {
  users: AdminUser[]
  total: number
  skip: number
  limit: number
}

export interface AdminUserCreate {
  email: string
  password: string
  full_name: string
  role?: string
  is_active?: boolean
  subscription_tier?: string
  business_name?: string
}

export interface AdminUserUpdate {
  email?: string
  full_name?: string
  role?: string
  is_active?: boolean
  unlock?: boolean
  subscription_tier?: string
  business_name?: string
  password?: string
}

export interface AdminUserDeleteResponse {
  success: boolean
  message: string
  user_id: number
}

export const useAdminUsers = () => {
  const api = useApi()

  const users = ref<AdminUser[]>([])
  const total = ref(0)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  /**
   * Fetch users with pagination and filtering
   */
  const fetchUsers = async (params?: {
    skip?: number
    limit?: number
    search?: string
    role?: string
    is_active?: boolean
  }) => {
    isLoading.value = true
    error.value = null

    try {
      const queryParams = new URLSearchParams()
      if (params?.skip !== undefined) queryParams.set('skip', params.skip.toString())
      if (params?.limit !== undefined) queryParams.set('limit', params.limit.toString())
      if (params?.search) queryParams.set('search', params.search)
      if (params?.role) queryParams.set('role', params.role)
      if (params?.is_active !== undefined) queryParams.set('is_active', params.is_active.toString())

      const query = queryParams.toString() ? `?${queryParams.toString()}` : ''
      const response = await api.get<AdminUserListResponse>(`/api/admin/users${query}`)

      users.value = response.users
      total.value = response.total

      return response
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch users'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Get a single user by ID
   */
  const getUser = async (userId: number): Promise<AdminUser> => {
    isLoading.value = true
    error.value = null

    try {
      const response = await api.get<AdminUser>(`/api/admin/users/${userId}`)
      return response
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch user'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Create a new user
   */
  const createUser = async (userData: AdminUserCreate): Promise<AdminUser> => {
    isLoading.value = true
    error.value = null

    try {
      const response = await api.post<AdminUser>('/api/admin/users', userData)
      // Refresh the list
      await fetchUsers()
      return response
    } catch (e: any) {
      error.value = e.message || 'Failed to create user'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Update a user
   */
  const updateUser = async (userId: number, userData: AdminUserUpdate): Promise<AdminUser> => {
    isLoading.value = true
    error.value = null

    try {
      const response = await api.patch<AdminUser>(`/api/admin/users/${userId}`, userData)
      // Update in local list
      const index = users.value.findIndex(u => u.id === userId)
      if (index !== -1) {
        users.value[index] = response
      }
      return response
    } catch (e: any) {
      error.value = e.message || 'Failed to update user'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Delete a user (hard delete)
   */
  const deleteUser = async (userId: number): Promise<AdminUserDeleteResponse> => {
    isLoading.value = true
    error.value = null

    try {
      const response = await api.delete<AdminUserDeleteResponse>(`/api/admin/users/${userId}`)
      // Remove from local list
      users.value = users.value.filter(u => u.id !== userId)
      total.value--
      return response
    } catch (e: any) {
      error.value = e.message || 'Failed to delete user'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Toggle user active status (uses PATCH endpoint)
   */
  const toggleUserActive = async (userId: number, currentIsActive: boolean): Promise<AdminUser> => {
    return updateUser(userId, { is_active: !currentIsActive })
  }

  /**
   * Unlock a locked user account (uses PATCH endpoint)
   */
  const unlockUser = async (userId: number): Promise<AdminUser> => {
    return updateUser(userId, { unlock: true })
  }

  return {
    // State
    users,
    total,
    isLoading,
    error,

    // Methods
    fetchUsers,
    getUser,
    createUser,
    updateUser,
    deleteUser,
    toggleUserActive,
    unlockUser,
  }
}
