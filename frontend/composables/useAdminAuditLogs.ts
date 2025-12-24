/**
 * Composable for admin audit logs
 *
 * Provides methods to fetch and filter audit log entries
 */

import { useApi } from '~/composables/useApi'

// Types
export interface AdminAuditLog {
  id: number
  admin_id: number | null
  admin_email: string | null
  action: 'CREATE' | 'UPDATE' | 'DELETE' | 'TOGGLE_ACTIVE' | 'UNLOCK'
  resource_type: 'user' | 'brand' | 'category' | 'color' | 'material'
  resource_id: string | null
  resource_name: string | null
  details: Record<string, any> | null
  ip_address: string | null
  created_at: string
}

export interface AdminAuditLogListResponse {
  logs: AdminAuditLog[]
  total: number
  skip: number
  limit: number
}

export interface AuditLogFilters {
  skip?: number
  limit?: number
  admin_id?: number
  action?: string
  resource_type?: string
  date_from?: string
  date_to?: string
  search?: string
}

export const useAdminAuditLogs = () => {
  const api = useApi()

  // State
  const logs = ref<AdminAuditLog[]>([])
  const total = ref(0)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  /**
   * Fetch audit logs with filters
   */
  const fetchLogs = async (filters?: AuditLogFilters): Promise<AdminAuditLogListResponse> => {
    isLoading.value = true
    error.value = null

    try {
      const queryParams = new URLSearchParams()

      if (filters?.skip !== undefined) queryParams.set('skip', filters.skip.toString())
      if (filters?.limit !== undefined) queryParams.set('limit', filters.limit.toString())
      if (filters?.admin_id) queryParams.set('admin_id', filters.admin_id.toString())
      if (filters?.action) queryParams.set('action', filters.action)
      if (filters?.resource_type) queryParams.set('resource_type', filters.resource_type)
      if (filters?.date_from) queryParams.set('date_from', filters.date_from)
      if (filters?.date_to) queryParams.set('date_to', filters.date_to)
      if (filters?.search) queryParams.set('search', filters.search)

      const query = queryParams.toString() ? `?${queryParams.toString()}` : ''
      const response = await api.get<AdminAuditLogListResponse>(`/api/admin/audit-logs${query}`)

      logs.value = response.logs
      total.value = response.total

      return response
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch audit logs'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Get a single audit log
   */
  const getLog = async (logId: number): Promise<AdminAuditLog> => {
    isLoading.value = true
    error.value = null

    try {
      return await api.get<AdminAuditLog>(`/api/admin/audit-logs/${logId}`)
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch audit log'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Get resource history
   */
  const getResourceHistory = async (
    resourceType: string,
    resourceId: string,
    limit: number = 50
  ): Promise<AdminAuditLogListResponse> => {
    isLoading.value = true
    error.value = null

    try {
      return await api.get<AdminAuditLogListResponse>(
        `/api/admin/audit-logs/resource/${resourceType}/${resourceId}?limit=${limit}`
      )
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch resource history'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  return {
    // State
    logs,
    total,
    isLoading,
    error,

    // Methods
    fetchLogs,
    getLog,
    getResourceHistory,
  }
}
