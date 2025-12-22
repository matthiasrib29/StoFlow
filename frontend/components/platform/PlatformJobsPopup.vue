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
        <i class="pi pi-spin pi-spinner text-primary-400" v-if="hasRunningJobs" />
        <i class="pi pi-list text-primary-400" v-else />
        <span class="font-semibold text-lg">Tâches {{ platformName }}</span>
        <span
          v-if="activeJobsCount > 0"
          class="bg-primary-400 text-secondary-900 text-xs font-bold px-2 py-1 rounded-full"
        >
          {{ activeJobsCount }}
        </span>
      </div>
    </template>

    <!-- Loading state -->
    <div v-if="isLoading && activeJobs.length === 0" class="flex items-center justify-center py-8">
      <i class="pi pi-spin pi-spinner text-2xl text-primary-400" />
    </div>

    <!-- Empty state -->
    <div
      v-else-if="activeJobs.length === 0"
      class="flex flex-col items-center justify-center py-8 text-gray-500"
    >
      <i class="pi pi-check-circle text-4xl mb-3 text-green-500" />
      <p class="text-lg font-medium">Aucune tâche en cours</p>
      <p class="text-sm">Toutes les tâches sont terminées</p>
    </div>

    <!-- Jobs list -->
    <div v-else class="flex flex-col gap-3 max-h-96 overflow-y-auto">
      <div
        v-for="job in activeJobs"
        :key="job.id"
        class="bg-gray-50 rounded-lg p-4 border border-gray-200"
      >
        <!-- Job header -->
        <div class="flex items-start justify-between mb-2">
          <div class="flex-1">
            <div class="flex items-center gap-2">
              <span
                :class="[
                  'text-xs font-medium px-2 py-0.5 rounded',
                  getStatusColor(job.status)
                ]"
              >
                {{ getStatusLabel(job.status) }}
              </span>
              <span class="text-sm font-medium text-gray-700">
                {{ getActionLabel(job.action_code) }}
              </span>
            </div>
            <p
              v-if="job.product_title"
              class="text-sm text-gray-600 mt-1 truncate max-w-xs"
              :title="job.product_title"
            >
              {{ job.product_title }}
            </p>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-1">
            <!-- Pause/Resume button -->
            <Button
              v-if="job.status === 'running'"
              icon="pi pi-pause"
              severity="secondary"
              text
              rounded
              size="small"
              @click="handlePause(job.id)"
              v-tooltip.top="'Mettre en pause'"
              :loading="actionLoading === job.id"
            />
            <Button
              v-else-if="job.status === 'paused'"
              icon="pi pi-play"
              severity="secondary"
              text
              rounded
              size="small"
              @click="handleResume(job.id)"
              v-tooltip.top="'Reprendre'"
              :loading="actionLoading === job.id"
            />

            <!-- Cancel button -->
            <Button
              icon="pi pi-times"
              severity="danger"
              text
              rounded
              size="small"
              @click="handleCancel(job.id)"
              v-tooltip.top="'Annuler'"
              :loading="actionLoading === job.id"
            />
          </div>
        </div>

        <!-- Progress bar -->
        <div class="mt-3">
          <div class="flex items-center justify-between text-xs text-gray-500 mb-1">
            <span>Progression</span>
            <span>{{ job.progress.completed }}/{{ job.progress.total }} ({{ job.progress.progress_percent }}%)</span>
          </div>
          <ProgressBar
            :value="job.progress.progress_percent"
            :showValue="false"
            style="height: 6px"
            :class="{
              'progress-running': job.status === 'running',
              'progress-paused': job.status === 'paused',
              'progress-pending': job.status === 'pending'
            }"
          />
        </div>

        <!-- Error message -->
        <div
          v-if="job.error_message"
          class="mt-2 text-xs text-red-600 bg-red-50 rounded p-2"
        >
          <i class="pi pi-exclamation-triangle mr-1" />
          {{ job.error_message }}
        </div>

        <!-- Job meta -->
        <div class="flex items-center gap-4 mt-2 text-xs text-gray-400">
          <span>
            <i class="pi pi-clock mr-1" />
            {{ formatTime(job.created_at) }}
          </span>
          <span v-if="job.retry_count > 0">
            <i class="pi pi-refresh mr-1" />
            {{ job.retry_count }} retry
          </span>
        </div>
      </div>
    </div>

    <!-- Footer actions -->
    <template #footer>
      <div class="flex items-center justify-between w-full">
        <Button
          v-if="activeJobs.length > 1"
          label="Tout annuler"
          icon="pi pi-times"
          severity="danger"
          text
          size="small"
          @click="handleCancelAll"
          :loading="cancelAllLoading"
        />
        <span v-else />

        <div class="flex items-center gap-2 text-xs text-gray-500">
          <i :class="['pi', isPolling ? 'pi-spin pi-sync' : 'pi-sync']" />
          <span>Mise à jour auto</span>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
/**
 * Generic platform jobs popup component
 *
 * Displays active jobs for any platform with cancel/pause/resume actions
 */
import { useToast } from 'primevue/usetoast'
import { usePlatformJobs, type PlatformCode } from '~/composables/usePlatformJobs'

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
  activeJobs,
  activeJobsCount,
  isLoading,
  isPolling,
  fetchActiveJobs,
  cancelJob,
  pauseJob,
  resumeJob,
  cancelAllJobs,
  startPolling,
  stopPolling,
  getStatusLabel,
  getStatusColor,
  getActionLabel,
} = usePlatformJobs(props.platformCode)

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const actionLoading = ref<number | null>(null)
const cancelAllLoading = ref(false)

const hasRunningJobs = computed(() =>
  activeJobs.value.some(j => j.status === 'running')
)

// Start/stop polling based on dialog visibility
watch(visible, (isVisible) => {
  if (isVisible) {
    startPolling(3000)
  } else {
    stopPolling()
  }
})

const handleCancel = async (jobId: number) => {
  actionLoading.value = jobId
  const success = await cancelJob(jobId)
  actionLoading.value = null

  if (success) {
    toast?.add({
      severity: 'success',
      summary: 'Tâche annulée',
      detail: 'La tâche a été annulée avec succès',
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

const handlePause = async (jobId: number) => {
  actionLoading.value = jobId
  const success = await pauseJob(jobId)
  actionLoading.value = null

  if (success) {
    toast?.add({
      severity: 'info',
      summary: 'Tâche en pause',
      detail: 'La tâche a été mise en pause',
      life: 3000,
    })
  }
}

const handleResume = async (jobId: number) => {
  actionLoading.value = jobId
  const success = await resumeJob(jobId)
  actionLoading.value = null

  if (success) {
    toast?.add({
      severity: 'info',
      summary: 'Tâche reprise',
      detail: 'La tâche va reprendre',
      life: 3000,
    })
  }
}

const handleCancelAll = async () => {
  cancelAllLoading.value = true
  const count = await cancelAllJobs()
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
  activeJobsCount,
  fetchActiveJobs,
})
</script>

<style scoped>
.jobs-popup :deep(.p-dialog-content) {
  padding: 1rem;
}

.progress-running :deep(.p-progressbar-value) {
  background: linear-gradient(90deg, #3b82f6, #60a5fa);
  animation: pulse 2s infinite;
}

.progress-paused :deep(.p-progressbar-value) {
  background: #f97316;
}

.progress-pending :deep(.p-progressbar-value) {
  background: #facc15;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
</style>
