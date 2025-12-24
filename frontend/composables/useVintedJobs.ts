/**
 * Composable for managing Vinted jobs with polling and actions
 *
 * Provides real-time job status updates and cancel/pause/resume actions
 */

export interface VintedJobTask {
  id: number
  status: 'pending' | 'processing' | 'success' | 'failed' | 'timeout' | 'cancelled'
  http_method: string | null
  path: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
  error_message: string | null
}

export interface VintedJobProgress {
  total: number
  completed: number
  failed: number
  pending: number
  progress_percent: number
}

export interface VintedJob {
  id: number
  batch_id: string | null
  action_code: string
  action_name: string
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled' | 'expired'
  priority: number
  product_id: number | null
  product_title: string | null
  error_message: string | null
  retry_count: number
  progress: VintedJobProgress
  created_at: string
  started_at: string | null
  completed_at: string | null
  expires_at: string | null
}

// Note: Using internal interfaces to avoid conflicts with usePlatformJobs.ts exports
interface VintedJobsListResponse {
  jobs: VintedJob[]
  total: number
  pending: number
  running: number
  completed: number
  failed: number
}

interface VintedJobActionResponse {
  success: boolean
  job_id: number
  new_status: string
  message?: string
}

export const useVintedJobs = () => {
  const { get, post } = useApi()

  // State
  const jobs = ref<VintedJob[]>([])
  const activeJobs = ref<VintedJob[]>([])
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

      let endpoint = `/api/vinted/jobs?limit=${limit}`
      if (statusFilter) {
        endpoint += `&status_filter=${statusFilter}`
      }

      const response = await get<VintedJobsListResponse>(endpoint)
      jobs.value = response.jobs
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch jobs'
      console.error('[useVintedJobs] fetchJobs error:', err)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch only active jobs (pending, running, paused)
   */
  const fetchActiveJobs = async (): Promise<void> => {
    try {
      error.value = null

      // Fetch pending and running jobs
      const [pendingRes, runningRes, pausedRes] = await Promise.all([
        get<VintedJobsListResponse>('/api/vinted/jobs?status_filter=pending&limit=50'),
        get<VintedJobsListResponse>('/api/vinted/jobs?status_filter=running&limit=50'),
        get<VintedJobsListResponse>('/api/vinted/jobs?status_filter=paused&limit=50'),
      ])

      // Combine and sort by created_at desc
      const allActive = [
        ...pendingRes.jobs,
        ...runningRes.jobs,
        ...pausedRes.jobs,
      ].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

      activeJobs.value = allActive
      activeJobsCount.value = allActive.length
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch active jobs'
      console.error('[useVintedJobs] fetchActiveJobs error:', err)
    }
  }

  /**
   * Cancel a specific job
   */
  const cancelJob = async (jobId: number): Promise<boolean> => {
    try {
      const response = await post<VintedJobActionResponse>(`/api/vinted/jobs/${jobId}/cancel`)
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
      console.error('[useVintedJobs] cancelJob error:', err)
      return false
    }
  }

  /**
   * Pause a specific job
   */
  const pauseJob = async (jobId: number): Promise<boolean> => {
    try {
      const response = await post<VintedJobActionResponse>(`/api/vinted/jobs/${jobId}/pause`)
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
      console.error('[useVintedJobs] pauseJob error:', err)
      return false
    }
  }

  /**
   * Resume a paused job
   */
  const resumeJob = async (jobId: number): Promise<boolean> => {
    try {
      const response = await post<VintedJobActionResponse>(`/api/vinted/jobs/${jobId}/resume`)
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
      console.error('[useVintedJobs] resumeJob error:', err)
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
  const getStatusLabel = (status: VintedJob['status']): string => {
    const labels: Record<VintedJob['status'], string> = {
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
  const getStatusColor = (status: VintedJob['status']): string => {
    const colors: Record<VintedJob['status'], string> = {
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
    }
    return labels[actionCode] || actionCode
  }

  // Cleanup on unmount
  onUnmounted(() => {
    stopPolling()
  })

  return {
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
