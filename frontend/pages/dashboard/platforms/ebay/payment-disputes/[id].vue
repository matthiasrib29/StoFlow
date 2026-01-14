<script setup lang="ts">
/**
 * eBay Payment Dispute Detail Page
 *
 * Displays detailed information about a specific payment dispute
 * with actions to accept, contest, and add evidence.
 */

import type { EbayPaymentDispute, EbayPaymentDisputeEvidenceType } from '~/types/ebay'

definePageMeta({
  layout: 'dashboard',
})

const route = useRoute()
const router = useRouter()
const toast = useAppToast()

const {
  fetchDispute,
  syncDispute,
  acceptDispute,
  contestDispute,
  addEvidence,
  getStateLabel,
  getStateSeverity,
  getReasonLabel,
  getSellerResponseLabel,
  getSellerResponseSeverity,
  getEvidenceTypeLabel,
  getStateIcon,
  getReasonIcon,
  formatAmount,
  formatDate,
  getEvidenceTypeOptions,
  isUrgent,
  getDaysUntilDeadline
} = useEbayPaymentDisputes()

// =========================================================================
// STATE
// =========================================================================

const dispute = ref<EbayPaymentDispute | null>(null)
const loading = ref(false)
const syncing = ref(false)
const actionLoading = ref(false)

// Dialogs
const showAcceptDialog = ref(false)
const showContestDialog = ref(false)
const showEvidenceDialog = ref(false)

// Form data
const acceptComment = ref('')
const contestForm = ref({
  evidenceType: null as EbayPaymentDisputeEvidenceType | null,
  evidenceInfo: '',
  comment: ''
})
const evidenceForm = ref({
  evidenceType: null as EbayPaymentDisputeEvidenceType | null,
  evidenceInfo: '',
  description: ''
})

// =========================================================================
// COMPUTED
// =========================================================================

const disputeId = computed(() => {
  const id = route.params.id
  return Array.isArray(id) ? parseInt(id[0]) : parseInt(id)
})

const canTakeAction = computed(() => {
  if (!dispute.value) return false
  return (
    dispute.value.dispute_state !== 'CLOSED' &&
    !dispute.value.seller_response
  )
})

const canAddEvidence = computed(() => {
  if (!dispute.value) return false
  return (
    dispute.value.dispute_state !== 'CLOSED' &&
    dispute.value.seller_response === 'CONTEST'
  )
})

const daysUntilDeadline = computed(() => {
  if (!dispute.value) return null
  return getDaysUntilDeadline(dispute.value)
})

const deadlineStatus = computed(() => {
  const days = daysUntilDeadline.value
  if (days === null) return { text: '-', class: '' }
  if (days < 0) return { text: `${Math.abs(days)} jours en retard`, class: 'text-red-600 font-bold' }
  if (days === 0) return { text: "Aujourd'hui", class: 'text-orange-600 font-bold' }
  if (days === 1) return { text: 'Demain', class: 'text-orange-600' }
  if (days <= 3) return { text: `${days} jours`, class: 'text-yellow-600' }
  return { text: `${days} jours`, class: 'text-green-600' }
})

// =========================================================================
// DATA FETCHING
// =========================================================================

const loadDispute = async () => {
  loading.value = true
  try {
    dispute.value = await fetchDispute(disputeId.value)
  } catch (error) {
    console.error('Failed to load dispute:', error)
    toast.add({
      severity: 'error',
      summary: 'Erreur',
      detail: 'Impossible de charger le litige',
      life: 5000
    })
    router.push('/dashboard/platforms/ebay/payment-disputes')
  } finally {
    loading.value = false
  }
}

const handleSync = async () => {
  if (!dispute.value) return
  syncing.value = true
  try {
    await syncDispute(dispute.value.dispute_id)
    await loadDispute()
    toast.add({
      severity: 'success',
      summary: 'Synchronisation terminée',
      detail: 'Les données ont été mises à jour',
      life: 3000
    })
  } catch (error) {
    console.error('Sync failed:', error)
    toast.add({
      severity: 'error',
      summary: 'Erreur',
      detail: 'La synchronisation a échoué',
      life: 5000
    })
  } finally {
    syncing.value = false
  }
}

// =========================================================================
// ACTIONS
// =========================================================================

const handleAccept = async () => {
  if (!dispute.value) return
  actionLoading.value = true
  try {
    const result = await acceptDispute(dispute.value.id, acceptComment.value || null)
    if (result.success) {
      toast.add({
        severity: 'success',
        summary: 'Litige accepté',
        detail: 'Vous avez accepté ce litige',
        life: 5000
      })
      showAcceptDialog.value = false
      acceptComment.value = ''
      await loadDispute()
    } else {
      throw new Error(result.message || 'Action failed')
    }
  } catch (error) {
    console.error('Accept failed:', error)
    toast.add({
      severity: 'error',
      summary: 'Erreur',
      detail: "Impossible d'accepter le litige",
      life: 5000
    })
  } finally {
    actionLoading.value = false
  }
}

const handleContest = async () => {
  if (!dispute.value || !contestForm.value.evidenceType) return
  actionLoading.value = true
  try {
    const result = await contestDispute(dispute.value.id, {
      evidence_type: contestForm.value.evidenceType,
      evidence_info: contestForm.value.evidenceInfo || null,
      comment: contestForm.value.comment || null
    })
    if (result.success) {
      toast.add({
        severity: 'success',
        summary: 'Litige contesté',
        detail: 'Votre contestation a été soumise',
        life: 5000
      })
      showContestDialog.value = false
      contestForm.value = { evidenceType: null, evidenceInfo: '', comment: '' }
      await loadDispute()
    } else {
      throw new Error(result.message || 'Action failed')
    }
  } catch (error) {
    console.error('Contest failed:', error)
    toast.add({
      severity: 'error',
      summary: 'Erreur',
      detail: 'Impossible de contester le litige',
      life: 5000
    })
  } finally {
    actionLoading.value = false
  }
}

const handleAddEvidence = async () => {
  if (!dispute.value || !evidenceForm.value.evidenceType || !evidenceForm.value.evidenceInfo) return
  actionLoading.value = true
  try {
    const result = await addEvidence(dispute.value.id, {
      evidence_type: evidenceForm.value.evidenceType,
      evidence_info: evidenceForm.value.evidenceInfo,
      description: evidenceForm.value.description || null
    })
    if (result.success) {
      toast.add({
        severity: 'success',
        summary: 'Preuve ajoutée',
        detail: 'La preuve a été ajoutée au litige',
        life: 5000
      })
      showEvidenceDialog.value = false
      evidenceForm.value = { evidenceType: null, evidenceInfo: '', description: '' }
      await loadDispute()
    } else {
      throw new Error(result.message || 'Action failed')
    }
  } catch (error) {
    console.error('Add evidence failed:', error)
    toast.add({
      severity: 'error',
      summary: 'Erreur',
      detail: "Impossible d'ajouter la preuve",
      life: 5000
    })
  } finally {
    actionLoading.value = false
  }
}

// =========================================================================
// NAVIGATION
// =========================================================================

const goBack = () => {
  router.push('/dashboard/platforms/ebay/payment-disputes')
}

const goToOrder = () => {
  if (dispute.value?.order_id) {
    router.push(`/dashboard/platforms/ebay/orders?search=${dispute.value.order_id}`)
  }
}

// =========================================================================
// LIFECYCLE
// =========================================================================

onMounted(async () => {
  await loadDispute()
})
</script>

<template>
  <div class="p-6">
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <ProgressSpinner />
    </div>

    <!-- Content -->
    <div v-else-if="dispute">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-4">
          <Button
            icon="pi pi-arrow-left"
            severity="secondary"
            text
            rounded
            @click="goBack"
          />
          <div>
            <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
              Litige #{{ dispute.dispute_id }}
            </h1>
            <p class="text-gray-600 dark:text-gray-400 mt-1">
              {{ formatDate(dispute.creation_date || dispute.created_at) }}
            </p>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <Button
            icon="pi pi-refresh"
            severity="secondary"
            :loading="syncing"
            @click="handleSync"
            v-tooltip.top="'Actualiser'"
          />
          <Tag
            :severity="getStateSeverity(dispute.dispute_state)"
            class="text-base px-4 py-2"
          >
            <template #default>
              <i :class="getStateIcon(dispute.dispute_state)" class="mr-2" />
              {{ getStateLabel(dispute.dispute_state) }}
            </template>
          </Tag>
        </div>
      </div>

      <!-- Urgent Alert -->
      <div
        v-if="isUrgent(dispute)"
        class="mb-6 p-4 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg"
      >
        <div class="flex items-center gap-3">
          <i class="pi pi-exclamation-triangle text-orange-600 dark:text-orange-400 text-xl" />
          <div>
            <p class="font-medium text-orange-700 dark:text-orange-300">
              Action urgente requise
            </p>
            <p class="text-sm text-orange-600 dark:text-orange-400">
              <span v-if="daysUntilDeadline !== null && daysUntilDeadline < 0">
                La deadline est dépassée de {{ Math.abs(daysUntilDeadline) }} jour(s).
              </span>
              <span v-else-if="daysUntilDeadline !== null && daysUntilDeadline <= 2">
                Il vous reste {{ daysUntilDeadline }} jour(s) pour répondre.
              </span>
              <span v-else>
                Ce litige nécessite votre attention.
              </span>
            </p>
          </div>
        </div>
      </div>

      <!-- Main Content Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Left Column: Main Info -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Amount Card -->
          <Card>
            <template #title>
              <div class="flex items-center gap-2">
                <i class="pi pi-euro" />
                <span>Montant contesté</span>
              </div>
            </template>
            <template #content>
              <div class="text-center py-4">
                <p class="text-4xl font-bold text-red-600 dark:text-red-400">
                  {{ formatAmount(dispute) }}
                </p>
                <p v-if="dispute.original_order_amount" class="text-sm text-gray-500 mt-2">
                  Montant original de la commande :
                  {{ new Intl.NumberFormat('fr-FR', { style: 'currency', currency: dispute.dispute_currency || 'EUR' }).format(dispute.original_order_amount) }}
                </p>
              </div>
            </template>
          </Card>

          <!-- Details Card -->
          <Card>
            <template #title>
              <div class="flex items-center gap-2">
                <i class="pi pi-info-circle" />
                <span>Détails du litige</span>
              </div>
            </template>
            <template #content>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Reason -->
                <div>
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Raison</p>
                  <div class="flex items-center gap-2">
                    <i :class="getReasonIcon(dispute.dispute_reason)" class="text-gray-600" />
                    <p class="font-medium text-gray-900 dark:text-white">
                      {{ getReasonLabel(dispute.dispute_reason) }}
                    </p>
                  </div>
                </div>

                <!-- Buyer -->
                <div>
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Acheteur</p>
                  <p class="font-medium text-gray-900 dark:text-white">
                    {{ dispute.buyer_username || '-' }}
                  </p>
                </div>

                <!-- Buyer claim -->
                <div v-if="dispute.buyer_claimed" class="md:col-span-2">
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Réclamation de l'acheteur</p>
                  <p class="text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
                    {{ dispute.buyer_claimed }}
                  </p>
                </div>

                <!-- Seller Response -->
                <div v-if="dispute.seller_response">
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Votre réponse</p>
                  <Tag
                    :severity="getSellerResponseSeverity(dispute.seller_response)"
                  >
                    {{ getSellerResponseLabel(dispute.seller_response) }}
                  </Tag>
                </div>

                <!-- Seller Comment -->
                <div v-if="dispute.seller_comment" class="md:col-span-2">
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Votre commentaire</p>
                  <p class="text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
                    {{ dispute.seller_comment }}
                  </p>
                </div>

                <!-- Seller Evidence -->
                <div v-if="dispute.seller_evidence" class="md:col-span-2">
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Preuves fournies</p>
                  <p class="text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
                    {{ dispute.seller_evidence }}
                  </p>
                </div>
              </div>
            </template>
          </Card>

          <!-- Resolution Card -->
          <Card v-if="dispute.resolution_status || dispute.dispute_state === 'CLOSED'">
            <template #title>
              <div class="flex items-center gap-2">
                <i class="pi pi-check-square" />
                <span>Résolution</span>
              </div>
            </template>
            <template #content>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Resolution Status -->
                <div v-if="dispute.resolution_status">
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Statut</p>
                  <p class="font-medium text-gray-900 dark:text-white">
                    {{ dispute.resolution_status }}
                  </p>
                </div>

                <!-- Resolution Method -->
                <div v-if="dispute.resolution_method">
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Méthode</p>
                  <p class="font-medium text-gray-900 dark:text-white">
                    {{ dispute.resolution_method }}
                  </p>
                </div>

                <!-- Resolution Amount -->
                <div v-if="dispute.resolution_amount">
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Montant résolu</p>
                  <p class="font-medium text-gray-900 dark:text-white">
                    {{ new Intl.NumberFormat('fr-FR', { style: 'currency', currency: dispute.dispute_currency || 'EUR' }).format(dispute.resolution_amount) }}
                  </p>
                </div>

                <!-- Resolution Date -->
                <div v-if="dispute.resolution_date">
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Date de résolution</p>
                  <p class="font-medium text-gray-900 dark:text-white">
                    {{ formatDate(dispute.resolution_date) }}
                  </p>
                </div>
              </div>
            </template>
          </Card>

          <!-- Reference Card -->
          <Card>
            <template #title>
              <div class="flex items-center gap-2">
                <i class="pi pi-link" />
                <span>Références</span>
              </div>
            </template>
            <template #content>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Order ID -->
                <div>
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">N° Commande</p>
                  <div class="flex items-center gap-2">
                    <p class="font-mono text-sm text-gray-900 dark:text-white">
                      {{ dispute.order_id || '-' }}
                    </p>
                    <Button
                      v-if="dispute.order_id"
                      icon="pi pi-external-link"
                      text
                      rounded
                      size="small"
                      @click="goToOrder"
                    />
                  </div>
                </div>

                <!-- Dispute ID -->
                <div>
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">ID Litige eBay</p>
                  <p class="font-mono text-sm text-gray-900 dark:text-white">
                    {{ dispute.dispute_id }}
                  </p>
                </div>

                <!-- Dispute Status -->
                <div v-if="dispute.dispute_status">
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Statut détaillé</p>
                  <p class="font-mono text-sm text-gray-900 dark:text-white">
                    {{ dispute.dispute_status }}
                  </p>
                </div>

                <!-- Reason Code -->
                <div v-if="dispute.reason_code">
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Code raison</p>
                  <p class="font-mono text-sm text-gray-900 dark:text-white">
                    {{ dispute.reason_code }}
                  </p>
                </div>
              </div>
            </template>
          </Card>
        </div>

        <!-- Right Column: Actions & Timeline -->
        <div class="space-y-6">
          <!-- Actions Card -->
          <Card v-if="canTakeAction || canAddEvidence">
            <template #title>
              <div class="flex items-center gap-2">
                <i class="pi pi-bolt" />
                <span>Actions</span>
              </div>
            </template>
            <template #content>
              <div class="space-y-3">
                <!-- Contest Button -->
                <Button
                  v-if="canTakeAction"
                  label="Contester le litige"
                  icon="pi pi-shield"
                  severity="warn"
                  class="w-full"
                  @click="showContestDialog = true"
                />

                <!-- Accept Button -->
                <Button
                  v-if="canTakeAction"
                  label="Accepter le litige"
                  icon="pi pi-check"
                  severity="secondary"
                  outlined
                  class="w-full"
                  @click="showAcceptDialog = true"
                />

                <!-- Add Evidence Button -->
                <Button
                  v-if="canAddEvidence"
                  label="Ajouter une preuve"
                  icon="pi pi-paperclip"
                  severity="info"
                  class="w-full"
                  @click="showEvidenceDialog = true"
                />
              </div>
            </template>
          </Card>

          <!-- Deadline Card -->
          <Card v-if="dispute.response_due_date">
            <template #title>
              <div class="flex items-center gap-2">
                <i class="pi pi-clock" />
                <span>Deadline</span>
              </div>
            </template>
            <template #content>
              <div class="text-center py-2">
                <p :class="['text-2xl font-bold', deadlineStatus.class]">
                  {{ deadlineStatus.text }}
                </p>
                <p class="text-sm text-gray-500 mt-2">
                  {{ formatDate(dispute.response_due_date) }}
                </p>
              </div>
            </template>
          </Card>

          <!-- Status Card -->
          <Card>
            <template #title>
              <div class="flex items-center gap-2">
                <i class="pi pi-chart-bar" />
                <span>Statut</span>
              </div>
            </template>
            <template #content>
              <div class="space-y-4">
                <div class="flex items-center justify-between">
                  <span class="text-gray-600 dark:text-gray-400">État</span>
                  <Tag
                    :severity="getStateSeverity(dispute.dispute_state)"
                  >
                    <template #default>
                      <i :class="getStateIcon(dispute.dispute_state)" class="mr-1" />
                      {{ getStateLabel(dispute.dispute_state) }}
                    </template>
                  </Tag>
                </div>

                <div v-if="dispute.seller_response" class="flex items-center justify-between">
                  <span class="text-gray-600 dark:text-gray-400">Réponse</span>
                  <Tag
                    :severity="getSellerResponseSeverity(dispute.seller_response)"
                  >
                    {{ getSellerResponseLabel(dispute.seller_response) }}
                  </Tag>
                </div>

                <!-- Status indicators -->
                <div class="pt-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
                  <div class="flex items-center gap-2 text-sm">
                    <i
                      :class="[
                        'pi',
                        dispute.is_open
                          ? 'pi-exclamation-circle text-blue-500'
                          : 'pi-circle text-gray-300'
                      ]"
                    />
                    <span :class="dispute.is_open ? 'text-blue-600' : 'text-gray-400'">
                      Litige ouvert
                    </span>
                  </div>

                  <div class="flex items-center gap-2 text-sm">
                    <i
                      :class="[
                        'pi',
                        dispute.needs_action
                          ? 'pi-exclamation-triangle text-orange-500'
                          : 'pi-circle text-gray-300'
                      ]"
                    />
                    <span :class="dispute.needs_action ? 'text-orange-600' : 'text-gray-400'">
                      Action requise
                    </span>
                  </div>

                  <div class="flex items-center gap-2 text-sm">
                    <i
                      :class="[
                        'pi',
                        dispute.was_contested
                          ? 'pi-shield text-yellow-500'
                          : 'pi-circle text-gray-300'
                      ]"
                    />
                    <span :class="dispute.was_contested ? 'text-yellow-600' : 'text-gray-400'">
                      Contesté par vous
                    </span>
                  </div>

                  <div class="flex items-center gap-2 text-sm">
                    <i
                      :class="[
                        'pi',
                        dispute.was_accepted
                          ? 'pi-check text-green-500'
                          : 'pi-circle text-gray-300'
                      ]"
                    />
                    <span :class="dispute.was_accepted ? 'text-green-600' : 'text-gray-400'">
                      Accepté par vous
                    </span>
                  </div>
                </div>
              </div>
            </template>
          </Card>

          <!-- Timeline Card -->
          <Card>
            <template #title>
              <div class="flex items-center gap-2">
                <i class="pi pi-history" />
                <span>Chronologie</span>
              </div>
            </template>
            <template #content>
              <div class="space-y-4">
                <!-- Creation Date -->
                <div class="flex items-start gap-3">
                  <div class="p-2 bg-red-100 dark:bg-red-900/40 rounded-full">
                    <i class="pi pi-exclamation-circle text-red-600 dark:text-red-400 text-sm" />
                  </div>
                  <div>
                    <p class="text-sm font-medium text-gray-900 dark:text-white">
                      Litige ouvert
                    </p>
                    <p class="text-xs text-gray-500">
                      {{ formatDate(dispute.creation_date) }}
                    </p>
                  </div>
                </div>

                <!-- Response Due Date -->
                <div v-if="dispute.response_due_date" class="flex items-start gap-3">
                  <div
                    class="p-2 rounded-full"
                    :class="
                      dispute.is_past_due
                        ? 'bg-red-100 dark:bg-red-900/40'
                        : 'bg-yellow-100 dark:bg-yellow-900/40'
                    "
                  >
                    <i
                      :class="[
                        'pi text-sm',
                        dispute.is_past_due
                          ? 'pi-times text-red-600 dark:text-red-400'
                          : 'pi-clock text-yellow-600 dark:text-yellow-400'
                      ]"
                    />
                  </div>
                  <div>
                    <p class="text-sm font-medium text-gray-900 dark:text-white">
                      {{ dispute.is_past_due ? 'Deadline dépassée' : 'Deadline réponse' }}
                    </p>
                    <p class="text-xs text-gray-500">
                      {{ formatDate(dispute.response_due_date) }}
                    </p>
                  </div>
                </div>

                <!-- Resolution Date -->
                <div v-if="dispute.resolution_date" class="flex items-start gap-3">
                  <div class="p-2 bg-blue-100 dark:bg-blue-900/40 rounded-full">
                    <i class="pi pi-check-square text-blue-600 dark:text-blue-400 text-sm" />
                  </div>
                  <div>
                    <p class="text-sm font-medium text-gray-900 dark:text-white">
                      Résolution
                    </p>
                    <p class="text-xs text-gray-500">
                      {{ formatDate(dispute.resolution_date) }}
                    </p>
                  </div>
                </div>

                <!-- Closed Date -->
                <div v-if="dispute.closed_date" class="flex items-start gap-3">
                  <div class="p-2 bg-green-100 dark:bg-green-900/40 rounded-full">
                    <i class="pi pi-check-circle text-green-600 dark:text-green-400 text-sm" />
                  </div>
                  <div>
                    <p class="text-sm font-medium text-gray-900 dark:text-white">
                      Litige fermé
                    </p>
                    <p class="text-xs text-gray-500">
                      {{ formatDate(dispute.closed_date) }}
                    </p>
                  </div>
                </div>

                <!-- Last Update -->
                <div class="flex items-start gap-3">
                  <div class="p-2 bg-gray-100 dark:bg-gray-700 rounded-full">
                    <i class="pi pi-refresh text-gray-600 dark:text-gray-400 text-sm" />
                  </div>
                  <div>
                    <p class="text-sm font-medium text-gray-900 dark:text-white">
                      Dernière mise à jour
                    </p>
                    <p class="text-xs text-gray-500">
                      {{ formatDate(dispute.updated_at) }}
                    </p>
                  </div>
                </div>
              </div>
            </template>
          </Card>
        </div>
      </div>
    </div>

    <!-- Accept Dialog -->
    <Dialog
      v-model:visible="showAcceptDialog"
      header="Accepter le litige"
      :modal="true"
      :closable="!actionLoading"
      class="w-full max-w-md"
    >
      <div class="space-y-4">
        <p class="text-gray-600 dark:text-gray-400">
          En acceptant ce litige, vous reconnaissez la réclamation de l'acheteur.
          Le montant contesté sera remboursé.
        </p>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Commentaire (optionnel)
          </label>
          <Textarea
            v-model="acceptComment"
            rows="3"
            placeholder="Ajouter un commentaire..."
            class="w-full"
          />
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-2">
          <Button
            label="Annuler"
            severity="secondary"
            :disabled="actionLoading"
            @click="showAcceptDialog = false"
          />
          <Button
            label="Accepter"
            icon="pi pi-check"
            :loading="actionLoading"
            @click="handleAccept"
          />
        </div>
      </template>
    </Dialog>

    <!-- Contest Dialog -->
    <Dialog
      v-model:visible="showContestDialog"
      header="Contester le litige"
      :modal="true"
      :closable="!actionLoading"
      class="w-full max-w-lg"
    >
      <div class="space-y-4">
        <p class="text-gray-600 dark:text-gray-400">
          Fournissez des preuves pour contester ce litige.
        </p>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Type de preuve *
          </label>
          <Dropdown
            v-model="contestForm.evidenceType"
            :options="getEvidenceTypeOptions()"
            option-label="label"
            option-value="value"
            placeholder="Sélectionner un type de preuve"
            class="w-full"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Information de preuve
          </label>
          <Textarea
            v-model="contestForm.evidenceInfo"
            rows="3"
            placeholder="Numéro de suivi, URL, description..."
            class="w-full"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Commentaire
          </label>
          <Textarea
            v-model="contestForm.comment"
            rows="3"
            placeholder="Expliquer votre contestation..."
            class="w-full"
          />
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-2">
          <Button
            label="Annuler"
            severity="secondary"
            :disabled="actionLoading"
            @click="showContestDialog = false"
          />
          <Button
            label="Contester"
            icon="pi pi-shield"
            severity="warn"
            :loading="actionLoading"
            :disabled="!contestForm.evidenceType"
            @click="handleContest"
          />
        </div>
      </template>
    </Dialog>

    <!-- Add Evidence Dialog -->
    <Dialog
      v-model:visible="showEvidenceDialog"
      header="Ajouter une preuve"
      :modal="true"
      :closable="!actionLoading"
      class="w-full max-w-lg"
    >
      <div class="space-y-4">
        <p class="text-gray-600 dark:text-gray-400">
          Ajoutez une preuve supplémentaire pour renforcer votre contestation.
        </p>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Type de preuve *
          </label>
          <Dropdown
            v-model="evidenceForm.evidenceType"
            :options="getEvidenceTypeOptions()"
            option-label="label"
            option-value="value"
            placeholder="Sélectionner un type de preuve"
            class="w-full"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Information de preuve *
          </label>
          <Textarea
            v-model="evidenceForm.evidenceInfo"
            rows="3"
            placeholder="Numéro de suivi, URL, référence..."
            class="w-full"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Description
          </label>
          <Textarea
            v-model="evidenceForm.description"
            rows="2"
            placeholder="Description de la preuve..."
            class="w-full"
          />
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-2">
          <Button
            label="Annuler"
            severity="secondary"
            :disabled="actionLoading"
            @click="showEvidenceDialog = false"
          />
          <Button
            label="Ajouter"
            icon="pi pi-paperclip"
            :loading="actionLoading"
            :disabled="!evidenceForm.evidenceType || !evidenceForm.evidenceInfo"
            @click="handleAddEvidence"
          />
        </div>
      </template>
    </Dialog>
  </div>
</template>
