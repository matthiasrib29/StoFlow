<template>
  <Dialog
    v-model:visible="visible"
    modal
    header="Tâches en cours"
    :style="{ width: '600px', maxHeight: '80vh' }"
    :draggable="false"
    position="topright"
    class="jobs-popup"
  >
    <template #header>
      <div class="flex items-center gap-3">
        <i class="pi pi-spin pi-spinner text-primary-400" v-if="hasRunningWorkflows" />
        <i class="pi pi-list text-primary-400" v-else />
        <span class="font-semibold text-lg">Tâches {{ platformName }}</span>
        <span
          v-if="activeWorkflowsCount > 0"
          class="bg-primary-400 text-secondary-900 text-xs font-bold px-2 py-1 rounded-full"
        >
          {{ activeWorkflowsCount }}
        </span>
        <Button
          icon="pi pi-refresh"
          size="small"
          severity="secondary"
          text
          rounded
          @click="fetchActiveWorkflows"
          :loading="isLoading"
          v-tooltip.top="'Rafraîchir'"
          class="ml-auto"
        />
      </div>
    </template>

    <!-- Loading state -->
    <div v-if="isLoading && workflows.length === 0" class="flex items-center justify-center py-8">
      <i class="pi pi-spin pi-spinner text-2xl text-primary-400" />
    </div>

    <!-- Empty state -->
    <div
      v-else-if="workflows.length === 0"
      class="flex flex-col items-center justify-center py-8 text-gray-500"
    >
      <i class="pi pi-check-circle text-4xl mb-3 text-green-500" />
      <p class="text-lg font-medium">Aucune tâche en cours</p>
      <p class="text-sm">Toutes les tâches sont terminées</p>
    </div>

    <!-- Workflows list -->
    <div v-else class="flex flex-col gap-3 max-h-96 overflow-y-auto">
      <div
        v-for="wf in workflows"
        :key="wf.workflow_id"
        class="bg-gray-50 rounded-lg p-4 border border-gray-200"
      >
        <!-- Workflow header -->
        <div class="flex items-start justify-between mb-2">
          <div class="flex-1">
            <div class="flex items-center gap-2">
              <span
                :class="[
                  'text-xs font-medium px-2 py-0.5 rounded',
                  getStatusColor(wf.status)
                ]"
              >
                {{ getStatusLabel(wf.status) }}
              </span>
              <span class="text-sm font-medium text-gray-700">
                {{ getActionLabel(wf.workflow_type) }}
              </span>
            </div>
          </div>

          <!-- Cancel button -->
          <div class="flex items-center gap-1">
            <Button
              icon="pi pi-times"
              severity="danger"
              text
              rounded
              size="small"
              @click="handleCancel(wf.workflow_id)"
              v-tooltip.top="'Annuler'"
              :loading="actionLoading === wf.workflow_id"
            />
          </div>
        </div>

        <!-- Progress info (loaded on demand) -->
        <div v-if="progressMap[wf.workflow_id]" class="mt-3">
          <div class="flex items-center gap-2 text-sm text-gray-600">
            <i class="pi pi-spin pi-spinner text-primary-400" v-if="wf.status === 'Running'" />
            <span>{{ progressMap[wf.workflow_id] }}</span>
          </div>
        </div>

        <!-- Error message from progress -->
        <div
          v-if="errorMap[wf.workflow_id]"
          class="mt-2 text-xs text-red-600 bg-red-50 rounded p-2"
        >
          <i class="pi pi-exclamation-triangle mr-1" />
          {{ errorMap[wf.workflow_id] }}
        </div>

        <!-- Workflow meta -->
        <div class="flex items-center gap-4 mt-2 text-xs text-gray-400">
          <span v-if="wf.start_time">
            <i class="pi pi-clock mr-1" />
            {{ formatTime(wf.start_time) }}
          </span>
          <span class="text-gray-300 truncate max-w-[200px]" :title="wf.workflow_id">
            {{ wf.workflow_id }}
          </span>
        </div>
      </div>
    </div>

    <!-- Footer actions -->
    <template #footer>
      <div class="flex items-center justify-between w-full">
        <Button
          v-if="workflows.length > 1"
          label="Tout annuler"
          icon="pi pi-times"
          severity="danger"
          text
          size="small"
          @click="handleCancelAll"
          :loading="cancelAllLoading"
        />
        <span v-else />

        <Button
          icon="pi pi-refresh"
          severity="secondary"
          text
          size="small"
          @click="() => fetchActiveWorkflows()"
          :loading="isLoading"
          v-tooltip.top="'Actualiser'"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
/**
 * Platform workflows popup component
 *
 * Displays active Temporal workflows for any platform with cancel action.
 * Replaces PlatformJobsPopup (MarketplaceJob-based).
 */
import { useToast } from 'primevue/usetoast'
import { useWorkflows, type PlatformCode } from '~/composables/useWorkflows'

const props = defineProps<{
  modelValue: boolean
  platformCode: PlatformCode
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const toast = import.meta.client ? useToast() : null

const {
  platformName,
  workflows,
  activeWorkflowsCount,
  isLoading,
  fetchActiveWorkflows,
  fetchProgress,
  cancelWorkflow,
  cancelAllWorkflows,
  getStatusLabel,
  getStatusColor,
  getActionLabel,
} = useWorkflows(props.platformCode)

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const actionLoading = ref<string | null>(null)
const cancelAllLoading = ref(false)

// Progress and error maps (loaded per-workflow)
const progressMap = ref<Record<string, string>>({})
const errorMap = ref<Record<string, string>>({})

const hasRunningWorkflows = computed(() =>
  workflows.value.some(w => w.status === 'Running')
)

// Fetch workflows and progress when dialog opens
watch(visible, async (isVisible) => {
  if (isVisible) {
    await fetchActiveWorkflows()
    await loadProgressForAll()
  }
})

/**
 * Load progress for all active workflows
 */
const loadProgressForAll = async () => {
  const newProgress: Record<string, string> = {}
  const newErrors: Record<string, string> = {}

  await Promise.all(
    workflows.value.map(async (wf) => {
      const progress = await fetchProgress(wf.workflow_id)
      if (progress) {
        if (progress.error) {
          newErrors[wf.workflow_id] = progress.error
        }
        // Build progress label from result data
        if (progress.result) {
          const label = formatProgressLabel(progress.result)
          if (label) newProgress[wf.workflow_id] = label
        }
      }
    })
  )

  progressMap.value = newProgress
  errorMap.value = newErrors
}

/**
 * Format progress result into a human-readable label
 */
const formatProgressLabel = (result: Record<string, any>): string => {
  // FetchUsers / Import workflows: page-based progress
  if (result.page !== undefined && result.total_saved !== undefined) {
    return `Page ${result.page} — ${result.total_saved} sauvegardés`
  }
  // Sync workflows: counts
  if (result.synced !== undefined) {
    return `${result.synced} synchronisés`
  }
  // Generic: show status if available
  if (result.status) {
    return String(result.status)
  }
  return ''
}

const handleCancel = async (workflowId: string) => {
  actionLoading.value = workflowId
  const success = await cancelWorkflow(workflowId)
  actionLoading.value = null

  if (success) {
    toast?.add({
      severity: 'success',
      summary: 'Tâche annulée',
      detail: 'La demande d\'annulation a été envoyée',
      life: 3000,
    })
  } else {
    toast?.add({
      severity: 'error',
      summary: 'Erreur',
      detail: 'Impossible d\'annuler la tâche',
      life: 5000,
    })
  }
}

const handleCancelAll = async () => {
  cancelAllLoading.value = true
  const count = await cancelAllWorkflows()
  cancelAllLoading.value = false

  toast?.add({
    severity: 'success',
    summary: 'Tâches annulées',
    detail: `${count} tâche(s) annulée(s)`,
    life: 3000,
  })
}

const formatTime = (dateStr: string): string => {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return 'À l\'instant'
  if (diffMins < 60) return `Il y a ${diffMins} min`

  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `Il y a ${diffHours}h`

  return date.toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// Expose for parent component
defineExpose({
  activeWorkflowsCount,
  fetchActiveWorkflows,
})
</script>

<style scoped>
.jobs-popup :deep(.p-dialog-content) {
  padding: 1rem;
}
</style>
