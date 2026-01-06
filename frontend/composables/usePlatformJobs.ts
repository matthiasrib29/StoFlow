/**
 * Generic composable for managing platform jobs with polling and actions
 *
 * Provides real-time job status updates and cancel/pause/resume actions
 * for any marketplace platform (Vinted, eBay, Etsy)
 */
import { platformLogger } from '~/utils/logger'

export type PlatformCode = 'vinted' | 'ebay' | 'etsy'

export type JobStatus = 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled' | 'expired'

export interface PlatformJobTask {
  id: number
  status: 'pending' | 'processing' | 'success' | 'failed' | 'timeout' | 'cancelled'
  http_method: string | null
  path: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
  error_message: string | null
}

export interface PlatformJobProgress {
  total: number
  completed: number
  failed: number
  pending: number
  progress_percent: number
}

export interface PlatformJob {
  id: number
  batch_id: string | null
  action_code: string
  action_name: string
  status: JobStatus
  priority: number
  product_id: number | null
  product_title: string | null
  error_message: string | null
  retry_count: number
  progress: PlatformJobProgress
  created_at: string
  started_at: string | null
  completed_at: string | null
  expires_at: string | null
}

export interface JobsListResponse {
  jobs: PlatformJob[]
  total: number
  pending: number
  running: number
  completed: number
  failed: number
}

export interface JobActionResponse {
  success: boolean
  job_id: number
  new_status: string
  message?: string
}

// Platform configuration
interface PlatformConfig {
  name: string
  apiPrefix: string
  logoPath: string
}

const PLATFORM_CONFIGS: Record<PlatformCode, PlatformConfig> = {
  vinted: {
    name: 'Vinted',
    apiPrefix: '/api/vinted',
    logoPath: '/images/platforms/vinted-logo.png',
  },
  ebay: {
    name: 'eBay',
    apiPrefix: '/api/ebay',
    logoPath: '/images/platforms/ebay-logo.png',
  },
  etsy: {
    name: 'Etsy',
    apiPrefix: '/api/etsy',
    logoPath: '/images/platforms/etsy-logo.png',
  },
}

export const usePlatformJobs = (platformCode: PlatformCode) => {
  const { get, post } = useApi()
  const config = PLATFORM_CONFIGS[platformCode]

  // State
  const jobs = ref<PlatformJob[]>([])
  const activeJobs = ref<PlatformJob[]>([])
  const activeJobsCount = ref(0)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const pollingInterval = ref<ReturnType<typeof setInterval> | null>(null)
  const isPolling = ref(false)

  /**
   * Fetch all jobs with optional filters
   */
  const fetchJobs = async (statusFilter?: string, limit = 50): Promise<void> => {
    try {
      isLoading.value = true
      error.value = null

      let endpoint = `${config.apiPrefix}/jobs?limit=${limit}`
      if (statusFilter) {
        endpoint += `&status_filter=${statusFilter}`
      }

      const response = await get<JobsListResponse>(endpoint)
      jobs.value = response.jobs
    } catch (err: any) {
      error.value = err.message || `Failed to fetch ${config.name} jobs`
      platformLogger.error(`[${platformCode}] fetchJobs error`, { error: err.message })
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch all jobs (single request)
   */
  const fetchActiveJobs = async (limit = 50): Promise<void> => {
    try {
      error.value = null
      isLoading.value = true

      const response = await get<JobsListResponse>(`${config.apiPrefix}/jobs?limit=${limit}`)

      // Filter active jobs (pending, running, paused) and sort by created_at desc
      const allActive = response.jobs
        .filter(job => ['pending', 'running', 'paused'].includes(job.status))
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

      activeJobs.value = allActive
      activeJobsCount.value = allActive.length
      jobs.value = response.jobs
    } catch (err: any) {
      error.value = err.message || `Failed to fetch ${config.name} jobs`
      platformLogger.error(`[${platformCode}] fetchActiveJobs error`, { error: err.message })
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Cancel a specific job
   */
  const cancelJob = async (jobId: number): Promise<boolean> => {
    try {
      const response = await post<JobActionResponse>(`${config.apiPrefix}/jobs/cancel?job_id=${jobId}`)
      if (response.success) {
        // Update local state
        const jobIndex = activeJobs.value.findIndex(j => j.id === jobId)
        if (jobIndex !== -1) {
          activeJobs.value.splice(jobIndex, 1)
          activeJobsCount.value = activeJobs.value.length
        }
        return true
      }
      return false
    } catch (err: any) {
      error.value = err.message || 'Failed to cancel job'
      platformLogger.error(`[${platformCode}] cancelJob error`, { error: err.message })
      return false
    }
  }

  /**
   * Pause a specific job
   */
  const pauseJob = async (jobId: number): Promise<boolean> => {
    try {
      const response = await post<JobActionResponse>(`${config.apiPrefix}/jobs/${jobId}/pause`)
      if (response.success) {
        // Update local state
        const job = activeJobs.value.find(j => j.id === jobId)
        if (job) {
          job.status = 'paused'
        }
        return true
      }
      return false
    } catch (err: any) {
      error.value = err.message || 'Failed to pause job'
      platformLogger.error(`[${platformCode}] pauseJob error`, { error: err.message })
      return false
    }
  }

  /**
   * Resume a paused job
   */
  const resumeJob = async (jobId: number): Promise<boolean> => {
    try {
      const response = await post<JobActionResponse>(`${config.apiPrefix}/jobs/${jobId}/resume`)
      if (response.success) {
        // Update local state
        const job = activeJobs.value.find(j => j.id === jobId)
        if (job) {
          job.status = 'pending'
        }
        return true
      }
      return false
    } catch (err: any) {
      error.value = err.message || 'Failed to resume job'
      platformLogger.error(`[${platformCode}] resumeJob error`, { error: err.message })
      return false
    }
  }

  /**
   * Cancel all active jobs
   */
  const cancelAllJobs = async (): Promise<number> => {
    let cancelledCount = 0
    const jobsToCancel = [...activeJobs.value]

    for (const job of jobsToCancel) {
      if (job.status !== 'cancelled') {
        const success = await cancelJob(job.id)
        if (success) cancelledCount++
      }
    }

    return cancelledCount
  }

  /**
   * Start polling for active jobs (client-side only)
   */
  const startPolling = (intervalMs = 3000): void => {
    // SSR safety: only run on client
    if (!import.meta.client) return

    if (pollingInterval.value) {
      stopPolling()
    }

    isPolling.value = true

    // Initial fetch
    fetchActiveJobs()

    // Set up interval
    pollingInterval.value = setInterval(() => {
      fetchActiveJobs()
    }, intervalMs)
  }

  /**
   * Stop polling
   */
  const stopPolling = (): void => {
    if (pollingInterval.value) {
      clearInterval(pollingInterval.value)
      pollingInterval.value = null
    }
    isPolling.value = false
  }

  /**
   * Get status label in French
   */
  const getStatusLabel = (status: JobStatus): string => {
    const labels: Record<JobStatus, string> = {
      pending: 'En attente',
      running: 'En cours',
      paused: 'En pause',
      completed: 'Terminé',
      failed: 'Échoué',
      cancelled: 'Annulé',
      expired: 'Expiré',
    }
    return labels[status] || status
  }

  /**
   * Get status color class
   */
  const getStatusColor = (status: JobStatus): string => {
    const colors: Record<JobStatus, string> = {
      pending: 'text-yellow-600 bg-yellow-100',
      running: 'text-blue-600 bg-blue-100',
      paused: 'text-orange-600 bg-orange-100',
      completed: 'text-green-600 bg-green-100',
      failed: 'text-red-600 bg-red-100',
      cancelled: 'text-gray-600 bg-gray-100',
      expired: 'text-gray-500 bg-gray-100',
    }
    return colors[status] || 'text-gray-600 bg-gray-100'
  }

  /**
   * Get action label in French
   */
  const getActionLabel = (actionCode: string): string => {
    const labels: Record<string, string> = {
      publish: 'Publication',
      update: 'Mise à jour',
      delete: 'Suppression',
      sync: 'Synchronisation',
      orders: 'Commandes',
      message: 'Messages',
      import: 'Import',
      export: 'Export',
    }
    return labels[actionCode] || actionCode
  }

  // Cleanup on unmount
  onUnmounted(() => {
    stopPolling()
  })

  return {
    // Platform info
    platformName: config.name,
    platformCode,
    logoPath: config.logoPath,

    // State
    jobs,
    activeJobs,
    activeJobsCount,
    isLoading,
    error,
    isPolling,

    // Methods
    fetchJobs,
    fetchActiveJobs,
    cancelJob,
    pauseJob,
    resumeJob,
    cancelAllJobs,
    startPolling,
    stopPolling,

    // Helpers
    getStatusLabel,
    getStatusColor,
    getActionLabel,
  }
}
