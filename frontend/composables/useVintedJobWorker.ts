/**
 * useVintedJobWorker - Frontend worker for executing Vinted jobs
 *
 * This composable listens for pending Vinted jobs from the backend
 * (via WebSocket or polling) and executes them using the browser plugin.
 *
 * Architecture:
 *   Backend Celery -> VintedJobBridgeService -> MarketplaceJob -> WebSocket notify
 *                                                                      |
 *   Frontend useVintedJobWorker <- 'vinted_job_pending' event <--------+
 *                    |
 *                    v
 *          useVintedBridge -> Browser Plugin -> Vinted API
 *
 * Usage:
 *   const { startWorker, stopWorker, processAllPendingJobs } = useVintedJobWorker()
 *
 *   // Auto-process jobs as they arrive
 *   startWorker()
 *
 *   // Or manually process all pending
 *   await processAllPendingJobs()
 *
 * @author Claude
 * @date 2026-01-20
 */

import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useVintedBridge } from './useVintedBridge'
import { useWebSocket } from './useWebSocket'

// ============================================================
// TYPES
// ============================================================

export interface VintedJob {
  id: number
  action_code: string | null
  action_name: string | null
  product_id: number | null
  product_title: string | null
  status: string
  priority: number
  input_data?: Record<string, any>
  error_message: string | null
  created_at: string
}

export interface JobListResponse {
  jobs: VintedJob[]
  total: number
  pending: number
  running: number
  completed: number
  failed: number
}

// ============================================================
// SINGLETON STATE
// ============================================================

const isWorkerActive = ref(false)
const isProcessing = ref(false)
const currentJobId = ref<number | null>(null)
const processedCount = ref(0)
const failedCount = ref(0)
const lastError = ref<string | null>(null)

// Queue for jobs waiting to be processed
const jobQueue = ref<VintedJob[]>([])

// ============================================================
// COMPOSABLE
// ============================================================

export function useVintedJobWorker() {
  const vintedBridge = useVintedBridge()
  const { socket, isConnected } = useWebSocket()

  // ============================================================
  // API CALLS
  // ============================================================

  /**
   * Fetch pending jobs from backend
   */
  async function fetchPendingJobs(): Promise<VintedJob[]> {
    try {
      const response = await $fetch<JobListResponse>('/api/vinted/jobs', {
        params: { status_filter: 'pending', limit: 50 },
      })
      return response.jobs || []
    } catch (err: any) {
      console.error('[VintedJobWorker] Failed to fetch pending jobs:', err.message)
      return []
    }
  }

  /**
   * Fetch a specific job by ID
   */
  async function fetchJob(jobId: number): Promise<VintedJob | null> {
    try {
      return await $fetch<VintedJob>(`/api/vinted/jobs/${jobId}`)
    } catch (err: any) {
      console.error(`[VintedJobWorker] Failed to fetch job ${jobId}:`, err.message)
      return null
    }
  }

  /**
   * Mark job as RUNNING
   */
  async function markJobStarted(jobId: number): Promise<boolean> {
    try {
      await $fetch(`/api/vinted/jobs/${jobId}/start`, { method: 'PATCH' })
      return true
    } catch (err: any) {
      console.error(`[VintedJobWorker] Failed to start job ${jobId}:`, err.message)
      return false
    }
  }

  /**
   * Mark job as COMPLETED
   */
  async function markJobCompleted(jobId: number, result: Record<string, any>): Promise<boolean> {
    try {
      await $fetch(`/api/vinted/jobs/${jobId}/complete`, {
        method: 'PATCH',
        body: { result },
      })
      return true
    } catch (err: any) {
      console.error(`[VintedJobWorker] Failed to complete job ${jobId}:`, err.message)
      return false
    }
  }

  /**
   * Mark job as FAILED
   */
  async function markJobFailed(jobId: number, error: string): Promise<boolean> {
    try {
      await $fetch(`/api/vinted/jobs/${jobId}/fail`, {
        method: 'PATCH',
        body: { error },
      })
      return true
    } catch (err: any) {
      console.error(`[VintedJobWorker] Failed to mark job ${jobId} as failed:`, err.message)
      return false
    }
  }

  // ============================================================
  // JOB EXECUTION
  // ============================================================

  /**
   * Execute a Vinted action via the browser plugin
   */
  async function executeVintedAction(
    actionCode: string,
    inputData: Record<string, any>
  ): Promise<{ success: boolean; data?: any; error?: string }> {
    switch (actionCode) {
      case 'publish':
        return await vintedBridge.publishProduct(inputData)

      case 'update':
        return await vintedBridge.updateProduct(
          inputData.vinted_id || inputData.vintedId,
          inputData.updates || inputData
        )

      case 'delete':
        return await vintedBridge.deleteProduct(
          inputData.vinted_id || inputData.vintedId
        )

      case 'sync':
        return await vintedBridge.getWardrobe(
          inputData.user_id || inputData.userId,
          inputData.page || 1,
          inputData.per_page || 96
        )

      default:
        return {
          success: false,
          error: `Unknown action: ${actionCode}`,
        }
    }
  }

  /**
   * Process a single job
   */
  async function processJob(job: VintedJob): Promise<void> {
    if (!job.action_code) {
      console.error(`[VintedJobWorker] Job ${job.id} has no action_code`)
      await markJobFailed(job.id, 'Job has no action_code')
      failedCount.value++
      return
    }

    console.log(`[VintedJobWorker] Processing job ${job.id}: ${job.action_code}`)
    currentJobId.value = job.id

    try {
      // Mark as running
      const started = await markJobStarted(job.id)
      if (!started) {
        console.warn(`[VintedJobWorker] Could not start job ${job.id}, skipping`)
        return
      }

      // Execute via plugin
      const result = await executeVintedAction(job.action_code, job.input_data || {})

      if (result.success) {
        await markJobCompleted(job.id, result.data || {})
        processedCount.value++
        console.log(`[VintedJobWorker] Job ${job.id} completed successfully`)
      } else {
        await markJobFailed(job.id, result.error || 'Unknown error')
        failedCount.value++
        console.error(`[VintedJobWorker] Job ${job.id} failed:`, result.error)
      }

    } catch (err: any) {
      await markJobFailed(job.id, err.message)
      failedCount.value++
      lastError.value = err.message
      console.error(`[VintedJobWorker] Job ${job.id} threw error:`, err.message)
    } finally {
      currentJobId.value = null
    }
  }

  /**
   * Process all jobs in the queue
   */
  async function processQueue(): Promise<void> {
    if (isProcessing.value) {
      console.log('[VintedJobWorker] Already processing, skipping')
      return
    }

    isProcessing.value = true

    try {
      while (jobQueue.value.length > 0) {
        const job = jobQueue.value.shift()!
        await processJob(job)

        // Small delay between jobs to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 500))
      }
    } finally {
      isProcessing.value = false
    }
  }

  /**
   * Add a job to the queue
   */
  function enqueueJob(job: VintedJob): void {
    // Check if job already in queue
    if (jobQueue.value.some(j => j.id === job.id)) {
      console.log(`[VintedJobWorker] Job ${job.id} already in queue, skipping`)
      return
    }

    // Add to queue (sorted by priority, lowest number = highest priority)
    jobQueue.value.push(job)
    jobQueue.value.sort((a, b) => a.priority - b.priority)

    console.log(`[VintedJobWorker] Job ${job.id} added to queue (queue size: ${jobQueue.value.length})`)

    // Start processing if worker is active
    if (isWorkerActive.value) {
      processQueue()
    }
  }

  // ============================================================
  // WEBSOCKET EVENT HANDLER
  // ============================================================

  /**
   * Handle incoming vinted_job_pending event from backend
   */
  async function handleJobPendingEvent(data: {
    job_id: number
    action: string | null
    product_id: number | null
    priority: number
    input_data?: Record<string, any>
  }): Promise<void> {
    console.log(`[VintedJobWorker] Received vinted_job_pending event: job ${data.job_id}`)

    // Fetch full job details
    const job = await fetchJob(data.job_id)
    if (job) {
      enqueueJob(job)
    }
  }

  // ============================================================
  // WORKER CONTROL
  // ============================================================

  /**
   * Start the worker (listen for WebSocket events and process queue)
   */
  function startWorker(): void {
    if (isWorkerActive.value) {
      console.log('[VintedJobWorker] Worker already active')
      return
    }

    console.log('[VintedJobWorker] Starting worker')
    isWorkerActive.value = true

    // Attach WebSocket listener
    if (socket.value) {
      socket.value.on('vinted_job_pending', handleJobPendingEvent)
    }

    // Process any existing pending jobs
    processAllPendingJobs()
  }

  /**
   * Stop the worker
   */
  function stopWorker(): void {
    console.log('[VintedJobWorker] Stopping worker')
    isWorkerActive.value = false

    // Remove WebSocket listener
    if (socket.value) {
      socket.value.off('vinted_job_pending', handleJobPendingEvent)
    }
  }

  /**
   * Fetch and process all pending jobs (manual trigger)
   */
  async function processAllPendingJobs(): Promise<void> {
    console.log('[VintedJobWorker] Fetching all pending jobs')

    const jobs = await fetchPendingJobs()
    console.log(`[VintedJobWorker] Found ${jobs.length} pending jobs`)

    for (const job of jobs) {
      enqueueJob(job)
    }

    await processQueue()
  }

  /**
   * Reset counters
   */
  function resetCounters(): void {
    processedCount.value = 0
    failedCount.value = 0
    lastError.value = null
  }

  // ============================================================
  // LIFECYCLE
  // ============================================================

  // Watch socket connection and re-attach listener when connected
  watch(isConnected, (connected) => {
    if (connected && isWorkerActive.value && socket.value) {
      // Re-attach listener on reconnect
      socket.value.off('vinted_job_pending', handleJobPendingEvent)
      socket.value.on('vinted_job_pending', handleJobPendingEvent)
    }
  })

  // ============================================================
  // RETURN
  // ============================================================

  return {
    // State
    isWorkerActive: computed(() => isWorkerActive.value),
    isProcessing: computed(() => isProcessing.value),
    currentJobId: computed(() => currentJobId.value),
    queueLength: computed(() => jobQueue.value.length),
    processedCount: computed(() => processedCount.value),
    failedCount: computed(() => failedCount.value),
    lastError: computed(() => lastError.value),

    // Worker control
    startWorker,
    stopWorker,

    // Manual actions
    processAllPendingJobs,
    processJob,
    enqueueJob,
    resetCounters,
  }
}
