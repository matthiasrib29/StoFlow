<script setup lang="ts">
import { ebayLogger } from '~/utils/logger'
/**
 * eBay Cancellation Detail Page
 *
 * Displays detailed information about a specific cancellation
 * and provides actions (approve, reject) for buyer-initiated cancellations.
 */

import type {
  EbayCancellation,
  EbayCancellationRejectReason
} from '~/types/ebay'

definePageMeta({
  layout: 'dashboard',
})

const route = useRoute()
const router = useRouter()
const toast = useAppToast()

const {
  fetchCancellation,
  approveCancellation,
  rejectCancellation,
  getStatusLabel,
  getStatusSeverity,
  getReasonLabel,
  getRequestorLabel,
  getRequestorSeverity,
  getStateLabel,
  getStateSeverity,
  formatRefundAmount
} = useEbayCancellations()

// =========================================================================
// STATE
// =========================================================================

const cancellation = ref<EbayCancellation | null>(null)
const loading = ref(false)
const actionLoading = ref(false)

// Dialogs
const showApproveDialog = ref(false)
const showRejectDialog = ref(false)

// Form data
const approveComments = ref('')
const rejectReason = ref<EbayCancellationRejectReason>('ALREADY_SHIPPED')
const rejectTrackingNumber = ref('')
const rejectCarrier = ref('')
const rejectComments = ref('')

// Reject reason options
const rejectReasonOptions = [
  {
    label: 'Déjà expédié',
    value: 'ALREADY_SHIPPED' as const,
    description: 'L\'article a déjà été expédié'
  },
  {
    label: 'Autre raison',
    value: 'OTHER_SELLER_REJECT_REASON' as const,
    description: 'Autre raison de refus'
  }
]

// Carrier options
const carrierOptions = [
  { label: 'Colissimo', value: 'colissimo' },
  { label: 'Mondial Relay', value: 'mondial_relay' },
  { label: 'Chronopost', value: 'chronopost' },
  { label: 'La Poste', value: 'la_poste' },
  { label: 'UPS', value: 'ups' },
  { label: 'FedEx', value: 'fedex' },
  { label: 'DHL', value: 'dhl' },
  { label: 'DPD', value: 'dpd' },
  { label: 'GLS', value: 'gls' },
  { label: 'Autre', value: 'other' }
]

// =========================================================================
// COMPUTED
// =========================================================================

const cancellationId = computed(() => {
  const id = route.params.id
  return Array.isArray(id) ? parseInt(id[0]) : parseInt(id)
})

const canTakeAction = computed(() => {
  if (!cancellation.value) return false
  return (
    cancellation.value.needs_action &&
    cancellation.value.requestor_role === 'BUYER' &&
    !cancellation.value.is_closed
  )
})

const isBuyerInitiated = computed(() => {
  return cancellation.value?.requestor_role === 'BUYER'
})

const isOverdue = computed(() => {
  return cancellation.value?.is_past_response_due ?? false
})

// =========================================================================
// DATA FETCHING
// =========================================================================

const loadCancellation = async () => {
  loading.value = true
  try {
    cancellation.value = await fetchCancellation(cancellationId.value)
  } catch (error) {
    ebayLogger.error('Failed to load cancellation:', error)
    toast.add({
      severity: 'error',
      summary: 'Erreur',
      detail: 'Impossible de charger l\'annulation',
      life: 5000
    })
    router.push('/dashboard/platforms/ebay/cancellations')
  } finally {
    loading.value = false
  }
}

// =========================================================================
// ACTIONS
// =========================================================================

const handleApprove = async () => {
  if (!cancellation.value) return

  actionLoading.value = true
  try {
    const result = await approveCancellation(
      cancellation.value.id,
      approveComments.value || undefined
    )

    if (result.success) {
      toast.add({
        severity: 'success',
        summary: 'Annulation approuvée',
        detail: 'L\'annulation a été approuvée avec succès',
        life: 5000
      })
      showApproveDialog.value = false
      approveComments.value = ''
      await loadCancellation()
    } else {
      toast.add({
        severity: 'error',
        summary: 'Erreur',
        detail: result.message || 'Échec de l\'approbation',
        life: 5000
      })
    }
  } catch (error) {
    ebayLogger.error('Failed to approve cancellation:', error)
    toast.add({
      severity: 'error',
      summary: 'Erreur',
      detail: 'Impossible d\'approuver l\'annulation',
      life: 5000
    })
  } finally {
    actionLoading.value = false
  }
}

const handleReject = async () => {
  if (!cancellation.value) return

  actionLoading.value = true
  try {
    const result = await rejectCancellation(
      cancellation.value.id,
      rejectReason.value,
      {
        tracking_number: rejectTrackingNumber.value || undefined,
        carrier: rejectCarrier.value || undefined,
        comments: rejectComments.value || undefined
      }
    )

    if (result.success) {
      toast.add({
        severity: 'success',
        summary: 'Annulation rejetée',
        detail: 'L\'annulation a été rejetée avec succès',
        life: 5000
      })
      showRejectDialog.value = false
      resetRejectForm()
      await loadCancellation()
    } else {
      toast.add({
        severity: 'error',
        summary: 'Erreur',
        detail: result.message || 'Échec du rejet',
        life: 5000
      })
    }
  } catch (error) {
    ebayLogger.error('Failed to reject cancellation:', error)
    toast.add({
      severity: 'error',
      summary: 'Erreur',
      detail: 'Impossible de rejeter l\'annulation',
      life: 5000
    })
  } finally {
    actionLoading.value = false
  }
}

const resetRejectForm = () => {
  rejectReason.value = 'ALREADY_SHIPPED'
  rejectTrackingNumber.value = ''
  rejectCarrier.value = ''
  rejectComments.value = ''
}

// =========================================================================
// HELPERS
// =========================================================================

const formatDate = (dateString: string | null): string => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const goBack = () => {
  router.push('/dashboard/platforms/ebay/cancellations')
}

// =========================================================================
// LIFECYCLE
// =========================================================================

onMounted(() => {
  loadCancellation()
})
</script>

<template>
  <div class="p-6">
    <!-- Header -->
    <div class="flex items-center gap-4 mb-6">
      <Button
        icon="pi pi-arrow-left"
        severity="secondary"
        text
        rounded
        @click="goBack"
      />
      <div class="flex-1">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Détails de l'annulation
        </h1>
        <p
          v-if="cancellation"
          class="text-gray-600 dark:text-gray-400 mt-1 font-mono"
        >
          {{ cancellation.cancel_id }}
        </p>
      </div>

      <!-- Action Buttons -->
      <div v-if="canTakeAction" class="flex gap-2">
        <Button
          label="Approuver"
          icon="pi pi-check"
          severity="success"
          @click="showApproveDialog = true"
        />
        <Button
          label="Rejeter"
          icon="pi pi-times"
          severity="danger"
          @click="showRejectDialog = true"
        />
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center py-12">
      <ProgressSpinner />
    </div>

    <!-- Content -->
    <div v-else-if="cancellation" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Main Info -->
      <div class="lg:col-span-2 space-y-6">
        <!-- Alert Banner for Action Required -->
        <Message
          v-if="cancellation.needs_action"
          :severity="isOverdue ? 'error' : 'warn'"
          :closable="false"
        >
          <template #container>
            <div class="flex items-center gap-3 p-3">
              <i
                :class="[
                  'text-xl',
                  isOverdue ? 'pi pi-exclamation-triangle' : 'pi pi-bell'
                ]"
              />
              <div>
                <p class="font-medium">
                  {{ isOverdue ? 'Réponse en retard !' : 'Action requise' }}
                </p>
                <p class="text-sm">
                  {{
                    isOverdue
                      ? 'La date limite de réponse est dépassée. Répondez au plus vite.'
                      : 'Cette demande d\'annulation nécessite votre réponse.'
                  }}
                </p>
              </div>
            </div>
          </template>
        </Message>

        <!-- Status Card -->
        <Card>
          <template #title>
            <div class="flex items-center gap-2">
              <i class="pi pi-info-circle text-blue-500" />
              <span>Statut</span>
            </div>
          </template>
          <template #content>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">
                  État
                </p>
                <Tag
                  :value="getStateLabel(cancellation.cancel_state)"
                  :severity="getStateSeverity(cancellation.cancel_state)"
                />
              </div>
              <div>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">
                  Statut
                </p>
                <Tag
                  :value="getStatusLabel(cancellation.cancel_status)"
                  :severity="getStatusSeverity(cancellation.cancel_status)"
                />
              </div>
              <div>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">
                  Demandeur
                </p>
                <Tag
                  :value="getRequestorLabel(cancellation.requestor_role)"
                  :severity="getRequestorSeverity(cancellation.requestor_role)"
                />
              </div>
              <div>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">
                  Raison
                </p>
                <span class="text-gray-900 dark:text-white">
                  {{ getReasonLabel(cancellation.cancel_reason) }}
                </span>
              </div>
            </div>
          </template>
        </Card>

        <!-- Order Info -->
        <Card>
          <template #title>
            <div class="flex items-center gap-2">
              <i class="pi pi-shopping-cart text-green-500" />
              <span>Commande</span>
            </div>
          </template>
          <template #content>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">
                  N° Commande eBay
                </p>
                <p class="font-mono text-gray-900 dark:text-white">
                  {{ cancellation.order_id || '-' }}
                </p>
              </div>
              <div>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">
                  Acheteur
                </p>
                <p class="text-gray-900 dark:text-white">
                  {{ cancellation.buyer_username || '-' }}
                </p>
              </div>
            </div>
          </template>
        </Card>

        <!-- Refund Info -->
        <Card v-if="cancellation.refund_amount">
          <template #title>
            <div class="flex items-center gap-2">
              <i class="pi pi-dollar text-yellow-500" />
              <span>Remboursement</span>
            </div>
          </template>
          <template #content>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">
                  Montant
                </p>
                <p class="text-xl font-bold text-gray-900 dark:text-white">
                  {{ formatRefundAmount(cancellation) }}
                </p>
              </div>
              <div>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">
                  Statut remboursement
                </p>
                <p class="text-gray-900 dark:text-white">
                  {{ cancellation.refund_status || '-' }}
                </p>
              </div>
            </div>
          </template>
        </Card>

        <!-- Shipping Info (if rejected with tracking) -->
        <Card v-if="cancellation.tracking_number || cancellation.shipped_date">
          <template #title>
            <div class="flex items-center gap-2">
              <i class="pi pi-truck text-purple-500" />
              <span>Expédition</span>
            </div>
          </template>
          <template #content>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">
                  N° Suivi
                </p>
                <p class="font-mono text-gray-900 dark:text-white">
                  {{ cancellation.tracking_number || '-' }}
                </p>
              </div>
              <div>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">
                  Transporteur
                </p>
                <p class="text-gray-900 dark:text-white">
                  {{ cancellation.carrier || '-' }}
                </p>
              </div>
              <div>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">
                  Date d'expédition
                </p>
                <p class="text-gray-900 dark:text-white">
                  {{ formatDate(cancellation.shipped_date) }}
                </p>
              </div>
            </div>
          </template>
        </Card>

        <!-- Comments -->
        <Card
          v-if="cancellation.buyer_comments || cancellation.seller_comments"
        >
          <template #title>
            <div class="flex items-center gap-2">
              <i class="pi pi-comments text-indigo-500" />
              <span>Commentaires</span>
            </div>
          </template>
          <template #content>
            <div class="space-y-4">
              <div v-if="cancellation.buyer_comments">
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">
                  Commentaire acheteur
                </p>
                <div
                  class="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-gray-900 dark:text-white"
                >
                  {{ cancellation.buyer_comments }}
                </div>
              </div>
              <div v-if="cancellation.seller_comments">
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">
                  Commentaire vendeur
                </p>
                <div
                  class="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-gray-900 dark:text-white"
                >
                  {{ cancellation.seller_comments }}
                </div>
              </div>
            </div>
          </template>
        </Card>

        <!-- Rejection Info -->
        <Card v-if="cancellation.was_rejected && cancellation.reject_reason">
          <template #title>
            <div class="flex items-center gap-2">
              <i class="pi pi-ban text-red-500" />
              <span>Raison du rejet</span>
            </div>
          </template>
          <template #content>
            <p class="text-gray-900 dark:text-white">
              {{ getReasonLabel(cancellation.reject_reason) }}
            </p>
          </template>
        </Card>
      </div>

      <!-- Sidebar -->
      <div class="space-y-6">
        <!-- Timeline -->
        <Card>
          <template #title>
            <div class="flex items-center gap-2">
              <i class="pi pi-calendar text-blue-500" />
              <span>Chronologie</span>
            </div>
          </template>
          <template #content>
            <div class="space-y-4">
              <div>
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  Date de demande
                </p>
                <p class="font-medium text-gray-900 dark:text-white">
                  {{ formatDate(cancellation.request_date) }}
                </p>
              </div>
              <div>
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  Date limite de réponse
                </p>
                <p
                  class="font-medium"
                  :class="[
                    isOverdue
                      ? 'text-red-600 dark:text-red-400'
                      : 'text-gray-900 dark:text-white'
                  ]"
                >
                  {{ formatDate(cancellation.response_due_date) }}
                  <i
                    v-if="isOverdue"
                    class="pi pi-exclamation-circle ml-1"
                  />
                </p>
              </div>
              <div v-if="cancellation.closed_date">
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  Date de clôture
                </p>
                <p class="font-medium text-gray-900 dark:text-white">
                  {{ formatDate(cancellation.closed_date) }}
                </p>
              </div>
              <Divider />
              <div>
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  Création en base
                </p>
                <p class="text-sm text-gray-900 dark:text-white">
                  {{ formatDate(cancellation.created_at) }}
                </p>
              </div>
              <div>
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  Dernière mise à jour
                </p>
                <p class="text-sm text-gray-900 dark:text-white">
                  {{ formatDate(cancellation.updated_at) }}
                </p>
              </div>
            </div>
          </template>
        </Card>

        <!-- Quick Actions -->
        <Card v-if="canTakeAction">
          <template #title>
            <div class="flex items-center gap-2">
              <i class="pi pi-bolt text-yellow-500" />
              <span>Actions rapides</span>
            </div>
          </template>
          <template #content>
            <div class="space-y-2">
              <Button
                label="Approuver l'annulation"
                icon="pi pi-check"
                severity="success"
                class="w-full"
                @click="showApproveDialog = true"
              />
              <Button
                label="Rejeter l'annulation"
                icon="pi pi-times"
                severity="danger"
                class="w-full"
                @click="showRejectDialog = true"
              />
            </div>
          </template>
        </Card>

        <!-- Info Box -->
        <Card v-if="isBuyerInitiated && !cancellation.is_closed">
          <template #content>
            <div class="flex gap-3">
              <i class="pi pi-info-circle text-blue-500 text-xl flex-shrink-0" />
              <div class="text-sm text-gray-600 dark:text-gray-400">
                <p class="font-medium text-gray-900 dark:text-white mb-1">
                  Demande acheteur
                </p>
                <p>
                  L'acheteur a demandé l'annulation de cette commande.
                  Vous pouvez approuver ou rejeter cette demande.
                </p>
                <p class="mt-2">
                  <strong>Approuver</strong> : L'acheteur sera remboursé.<br />
                  <strong>Rejeter</strong> : La commande reste active.
                </p>
              </div>
            </div>
          </template>
        </Card>
      </div>
    </div>

    <!-- Approve Dialog -->
    <Dialog
      v-model:visible="showApproveDialog"
      header="Approuver l'annulation"
      :modal="true"
      :style="{ width: '450px' }"
    >
      <div class="space-y-4">
        <Message severity="info" :closable="false">
          En approuvant cette annulation, l'acheteur sera automatiquement
          remboursé.
        </Message>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Commentaire (optionnel)
          </label>
          <Textarea
            v-model="approveComments"
            rows="3"
            class="w-full"
            placeholder="Ajouter un commentaire..."
          />
        </div>
      </div>

      <template #footer>
        <Button
          label="Annuler"
          severity="secondary"
          text
          @click="showApproveDialog = false"
        />
        <Button
          label="Approuver"
          icon="pi pi-check"
          severity="success"
          :loading="actionLoading"
          @click="handleApprove"
        />
      </template>
    </Dialog>

    <!-- Reject Dialog -->
    <Dialog
      v-model:visible="showRejectDialog"
      header="Rejeter l'annulation"
      :modal="true"
      :style="{ width: '500px' }"
    >
      <div class="space-y-4">
        <Message severity="warn" :closable="false">
          En rejetant cette annulation, la commande restera active et devra
          être livrée.
        </Message>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Raison du rejet *
          </label>
          <div class="space-y-2">
            <div
              v-for="option in rejectReasonOptions"
              :key="option.value"
              class="flex items-start gap-3"
            >
              <RadioButton
                v-model="rejectReason"
                :input-id="option.value"
                :value="option.value"
              />
              <label :for="option.value" class="cursor-pointer">
                <p class="font-medium text-gray-900 dark:text-white">
                  {{ option.label }}
                </p>
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  {{ option.description }}
                </p>
              </label>
            </div>
          </div>
        </div>

        <div v-if="rejectReason === 'ALREADY_SHIPPED'" class="space-y-4">
          <Divider />
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Pour rejeter avec la raison "Déjà expédié", vous pouvez fournir les
            informations de suivi.
          </p>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Transporteur
              </label>
              <Dropdown
                v-model="rejectCarrier"
                :options="carrierOptions"
                option-label="label"
                option-value="value"
                placeholder="Sélectionner"
                class="w-full"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                N° de suivi
              </label>
              <InputText
                v-model="rejectTrackingNumber"
                class="w-full"
                placeholder="Ex: 1Z999AA10123456784"
              />
            </div>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Commentaire (optionnel)
          </label>
          <Textarea
            v-model="rejectComments"
            rows="3"
            class="w-full"
            placeholder="Ajouter un commentaire..."
          />
        </div>
      </div>

      <template #footer>
        <Button
          label="Annuler"
          severity="secondary"
          text
          @click="showRejectDialog = false"
        />
        <Button
          label="Rejeter"
          icon="pi pi-times"
          severity="danger"
          :loading="actionLoading"
          @click="handleReject"
        />
      </template>
    </Dialog>
  </div>
</template>
