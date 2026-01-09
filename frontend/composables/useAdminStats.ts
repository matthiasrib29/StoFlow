/**
 * Composable for admin dashboard statistics
 *
 * Provides methods to fetch KPIs, subscription stats, and registration trends
 */

import { useApi } from '~/composables/useApi'

// Types
export interface AdminStatsUsersByRole {
  admin: number
  user: number
  support: number
}

export interface AdminStatsOverview {
  total_users: number
  active_users: number
  inactive_users: number
  locked_users: number
  users_by_role: AdminStatsUsersByRole
}

export interface AdminStatsUsersByTier {
  free: number
  starter: number
  pro: number
  enterprise: number
}

export interface AdminStatsSubscriptions {
  users_by_tier: AdminStatsUsersByTier
  total_mrr: number
  paying_subscribers: number
  active_subscriptions: number
}

export interface AdminStatsRegistrationData {
  date: string
  count: number
}

export interface AdminStatsRegistrations {
  period: string
  start_date: string
  end_date: string
  data: AdminStatsRegistrationData[]
  total: number
  average_per_day: number
}

export interface AdminRecentLogin {
  id: number
  email: string
  full_name: string
  last_login: string | null
}

export interface AdminNewRegistration {
  id: number
  email: string
  full_name: string
  created_at: string | null
  subscription_tier: string
}

export interface AdminStatsRecentActivity {
  recent_logins: AdminRecentLogin[]
  new_registrations: AdminNewRegistration[]
}

export const useAdminStats = () => {
  const api = useApi()

  // State
  const overview = ref<AdminStatsOverview | null>(null)
  const subscriptions = ref<AdminStatsSubscriptions | null>(null)
  const registrations = ref<AdminStatsRegistrations | null>(null)
  const recentActivity = ref<AdminStatsRecentActivity | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  /**
   * Fetch overview statistics
   */
  const fetchOverview = async (): Promise<AdminStatsOverview> => {
    isLoading.value = true
    error.value = null

    try {
      const response = await api.get<AdminStatsOverview>('/admin/stats/overview')
      overview.value = response
      return response
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch overview stats'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch subscription statistics
   */
  const fetchSubscriptions = async (): Promise<AdminStatsSubscriptions> => {
    isLoading.value = true
    error.value = null

    try {
      const response = await api.get<AdminStatsSubscriptions>('/admin/stats/subscriptions')
      subscriptions.value = response
      return response
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch subscription stats'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch registration statistics
   */
  const fetchRegistrations = async (
    period: 'week' | 'month' | '3months' = 'month'
  ): Promise<AdminStatsRegistrations> => {
    isLoading.value = true
    error.value = null

    try {
      const response = await api.get<AdminStatsRegistrations>(
        `/api/admin/stats/registrations?period=${period}`
      )
      registrations.value = response
      return response
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch registration stats'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch recent activity
   */
  const fetchRecentActivity = async (limit: number = 10): Promise<AdminStatsRecentActivity> => {
    isLoading.value = true
    error.value = null

    try {
      const response = await api.get<AdminStatsRecentActivity>(
        `/api/admin/stats/recent-activity?limit=${limit}`
      )
      recentActivity.value = response
      return response
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch recent activity'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch all stats at once
   */
  const fetchAll = async (period: 'week' | 'month' | '3months' = 'month') => {
    isLoading.value = true
    error.value = null

    try {
      const [overviewData, subscriptionsData, registrationsData, activityData] = await Promise.all([
        api.get<AdminStatsOverview>('/admin/stats/overview'),
        api.get<AdminStatsSubscriptions>('/admin/stats/subscriptions'),
        api.get<AdminStatsRegistrations>(`/admin/stats/registrations?period=${period}`),
        api.get<AdminStatsRecentActivity>('/admin/stats/recent-activity?limit=5'),
      ])

      overview.value = overviewData
      subscriptions.value = subscriptionsData
      registrations.value = registrationsData
      recentActivity.value = activityData

      return {
        overview: overviewData,
        subscriptions: subscriptionsData,
        registrations: registrationsData,
        recentActivity: activityData,
      }
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch stats'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  return {
    // State
    overview,
    subscriptions,
    registrations,
    recentActivity,
    isLoading,
    error,

    // Methods
    fetchOverview,
    fetchSubscriptions,
    fetchRegistrations,
    fetchRecentActivity,
    fetchAll,
  }
}
