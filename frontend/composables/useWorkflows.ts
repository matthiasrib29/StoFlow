/**
 * Composable for managing Temporal workflows with polling
 *
 * Replaces usePlatformJobs.ts — polls Temporal workflow status
 * instead of MarketplaceJob database rows.
 *
 * API endpoints:
 * - GET /api/workflows?marketplace={platform}&workflow_status=Running
 * - GET /api/workflows/{workflow_id}/progress
 * - POST /api/workflows/{workflow_id}/cancel
 */
import { platformLogger } from '~/utils/logger'

export type PlatformCode = 'vinted' | 'ebay' | 'etsy'

export interface WorkflowSummary {
  workflow_id: string
  workflow_type: string
  status: string
  start_time: string | null
  marketplace: string | null
}

export interface WorkflowProgress {
  workflow_id: string
  status: string
  result: Record<string, any> | null
  error: string | null
}

interface WorkflowListResponse {
  workflows: WorkflowSummary[]
  total: number
}

interface CancelResponse {
  workflow_id: string
  status: string
}

// Platform configuration
interface PlatformConfig {
  name: string
  logoPath: string
}

const PLATFORM_CONFIGS: Record<PlatformCode, PlatformConfig> = {
  vinted: {
    name: 'Vinted',
    logoPath: '/images/platforms/vinted-logo.png',
  },
  ebay: {
    name: 'eBay',
    logoPath: '/images/platforms/ebay-logo.png',
  },
  etsy: {
    name: 'Etsy',
    logoPath: '/images/platforms/etsy-logo.png',
  },
}

/**
 * Extract action from workflow type name.
 * e.g. "VintedPublishWorkflow" → "publish"
 *      "EbayImportWorkflow" → "import"
 */
function extractAction(workflowType: string): string {
  // Remove marketplace prefix and "Workflow" suffix
  const match = workflowType.match(/^(?:Vinted|Ebay|Etsy)(\w+?)Workflow$/)
  if (match) {
    return match[1].toLowerCase()
  }
  return workflowType.toLowerCase()
}

export const useWorkflows = (platformCode: PlatformCode) => {
  const { get, post } = useApi()
  const config = PLATFORM_CONFIGS[platformCode]

  // State
  const workflows = ref<WorkflowSummary[]>([])
  const activeWorkflowsCount = ref(0)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const pollingInterval = ref<ReturnType<typeof setInterval> | null>(null)
  const isPolling = ref(false)

  /**
   * Fetch active (running) workflows for this marketplace
   */
  const fetchActiveWorkflows = async (): Promise<void> => {
    try {
      isLoading.value = true
      error.value = null

      const response = await get<WorkflowListResponse>(
        `/workflows?marketplace=${platformCode}&workflow_status=Running&limit=50`
      )

      workflows.value = response.workflows
      activeWorkflowsCount.value = response.total
    } catch (err: any) {
      error.value = err.message || `Failed to fetch ${config.name} workflows`
      platformLogger.error(`[${platformCode}] fetchActiveWorkflows error`, { error: err.message })
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch progress for a specific workflow
   */
  const fetchProgress = async (workflowId: string): Promise<WorkflowProgress | null> => {
    try {
      return await get<WorkflowProgress>(`/workflows/${workflowId}/progress`)
    } catch (err: any) {
      platformLogger.error(`[${platformCode}] fetchProgress error`, { workflowId, error: err.message })
      return null
    }
  }

  /**
   * Cancel a specific workflow
   */
  const cancelWorkflow = async (workflowId: string): Promise<boolean> => {
    try {
      const response = await post<CancelResponse>(`/workflows/${workflowId}/cancel`)
      if (response.status === 'cancel_requested') {
        // Remove from local list
        const idx = workflows.value.findIndex(w => w.workflow_id === workflowId)
        if (idx !== -1) {
          workflows.value.splice(idx, 1)
          activeWorkflowsCount.value = workflows.value.length
        }
        return true
      }
      return false
    } catch (err: any) {
      error.value = err.message || 'Failed to cancel workflow'
      platformLogger.error(`[${platformCode}] cancelWorkflow error`, { workflowId, error: err.message })
      return false
    }
  }

  /**
   * Cancel all active workflows
   */
  const cancelAllWorkflows = async (): Promise<number> => {
    let cancelledCount = 0
    const toCancel = [...workflows.value]

    for (const wf of toCancel) {
      const success = await cancelWorkflow(wf.workflow_id)
      if (success) cancelledCount++
    }

    return cancelledCount
  }

  /**
   * Start polling for active workflows (client-side only)
   */
  const startPolling = (intervalMs = 3000): void => {
    if (!import.meta.client) return

    if (pollingInterval.value) {
      stopPolling()
    }

    isPolling.value = true

    // Initial fetch
    fetchActiveWorkflows()

    pollingInterval.value = setInterval(() => {
      fetchActiveWorkflows()
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

  // ===== DISPLAY HELPERS =====

  /**
   * Get status label in French
   */
  const getStatusLabel = (status: string): string => {
    const labels: Record<string, string> = {
      running: 'En cours',
      completed: 'Terminé',
      failed: 'Échoué',
      cancelled: 'Annulé',
      terminated: 'Terminé (forcé)',
      timedout: 'Expiré',
      cancelling: 'Arrêt en cours...',
    }
    return labels[status.toLowerCase()] || status
  }

  /**
   * Get status color class
   */
  const getStatusColor = (status: string): string => {
    const colors: Record<string, string> = {
      running: 'text-blue-600 bg-blue-100',
      completed: 'text-green-600 bg-green-100',
      failed: 'text-red-600 bg-red-100',
      cancelled: 'text-gray-600 bg-gray-100',
      terminated: 'text-gray-600 bg-gray-100',
      timedout: 'text-gray-500 bg-gray-100',
      cancelling: 'text-yellow-700 bg-yellow-200',
    }
    return colors[status.toLowerCase()] || 'text-gray-600 bg-gray-100'
  }

  /**
   * Get action label in French from workflow type
   */
  const getActionLabel = (workflowType: string): string => {
    const action = extractAction(workflowType)
    const labels: Record<string, string> = {
      publish: 'Publication',
      update: 'Mise à jour',
      delete: 'Suppression',
      orderssync: 'Sync commandes',
      message: 'Message',
      linkproduct: 'Liaison produit',
      fetchusers: 'Recherche utilisateurs',
      checkconnection: 'Vérification connexion',
      import: 'Import',
      sync: 'Synchronisation',
      cleanup: 'Nettoyage',
      batchcleanup: 'Nettoyage batch',
      prosellerscan: 'Scan vendeurs pro',
    }
    return labels[action] || action
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
    workflows,
    activeWorkflowsCount,
    isLoading,
    error,
    isPolling,

    // Methods
    fetchActiveWorkflows,
    fetchProgress,
    cancelWorkflow,
    cancelAllWorkflows,
    startPolling,
    stopPolling,

    // Helpers
    getStatusLabel,
    getStatusColor,
    getActionLabel,
  }
}
