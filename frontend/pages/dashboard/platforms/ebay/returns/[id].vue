<template>
  <div class="page-container">
    <!-- Back Button & Header -->
    <div class="flex items-center gap-4 mb-6">
      <Button
        icon="pi pi-arrow-left"
        text
        rounded
        severity="secondary"
        @click="navigateTo('/dashboard/platforms/ebay/returns')"
      />
      <div class="flex-1">
        <h1 class="text-2xl font-bold text-secondary-900">Détails du retour</h1>
        <p v-if="returnItem" class="text-sm text-gray-500 mt-1">{{ returnItem.return_id }}</p>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-20">
      <ProgressSpinner />
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-error-50 border border-error-200 rounded-lg p-6">
      <div class="flex items-center gap-3">
        <i class="pi pi-exclamation-circle text-2xl text-error-600" />
        <div>
          <h3 class="font-semibold text-error-900">Erreur</h3>
          <p class="text-sm text-error-700 mt-1">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- Return Details -->
    <div v-else-if="returnItem" class="space-y-6">
      <!-- Alert for Past Deadline -->
      <div
        v-if="returnItem.is_past_deadline"
        class="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3"
      >
        <i class="pi pi-exclamation-triangle text-xl text-red-600" />
        <div>
          <p class="font-semibold text-red-900">Ce retour est en retard !</p>
          <p class="text-sm text-red-700">
            La date limite était le {{ formatDate(returnItem.deadline_date) }}. Veuillez traiter ce retour immédiatement.
          </p>
        </div>
      </div>

      <!-- Alert for Needs Action -->
      <div
        v-else-if="returnItem.needs_action"
        class="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-center gap-3"
      >
        <i class="pi pi-exclamation-circle text-xl text-amber-600" />
        <div>
          <p class="font-semibold text-amber-900">Action requise</p>
          <p class="text-sm text-amber-700">
            Ce retour nécessite votre attention. Deadline : {{ formatDate(returnItem.deadline_date) }}
          </p>
        </div>
      </div>

      <!-- Status Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- State -->
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <div class="text-center">
              <p class="text-sm text-gray-500 mb-2">État</p>
              <Tag
                :value="getStateLabel(returnItem.state)"
                :severity="getStateSeverity(returnItem.state)"
                class="text-base px-4 py-2"
              />
            </div>
          </template>
        </Card>

        <!-- Status -->
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <div class="text-center">
              <p class="text-sm text-gray-500 mb-2">Statut</p>
              <Tag
                :value="getStatusLabel(returnItem.status)"
                :severity="getStatusSeverity(returnItem.status)"
                class="text-base px-4 py-2"
              />
            </div>
          </template>
        </Card>

        <!-- Refund Amount -->
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <div class="text-center">
              <p class="text-sm text-gray-500 mb-2">Montant remboursement</p>
              <p v-if="returnItem.refund_amount" class="text-2xl font-bold text-success-600">
                {{ formatAmount(returnItem.refund_amount, returnItem.refund_currency) }}
              </p>
              <p v-else class="text-xl text-gray-400">-</p>
            </div>
          </template>
        </Card>
      </div>

      <!-- Action Buttons -->
      <Card
        v-if="returnItem.is_open"
        class="shadow-sm modern-rounded border border-gray-100"
      >
        <template #header>
          <div class="p-4 border-b border-gray-100">
            <h2 class="text-lg font-semibold text-secondary-900 flex items-center gap-2">
              <i class="pi pi-bolt text-platform-ebay" />
              Actions
            </h2>
          </div>
        </template>
        <template #content>
          <div class="flex flex-wrap gap-3">
            <Button
              v-if="canAccept"
              label="Accepter le retour"
              icon="pi pi-check"
              class="bg-success-600 hover:bg-success-700 text-white border-0"
              :loading="actionLoading === 'accept'"
              @click="showAcceptDialog = true"
            />
            <Button
              v-if="canDecline"
              label="Refuser le retour"
              icon="pi pi-times"
              class="bg-error-600 hover:bg-error-700 text-white border-0"
              :loading="actionLoading === 'decline'"
              @click="showDeclineDialog = true"
            />
            <Button
              v-if="canRefund"
              label="Rembourser"
              icon="pi pi-dollar"
              class="bg-platform-ebay hover:bg-blue-700 text-white border-0"
              :loading="actionLoading === 'refund'"
              @click="showRefundDialog = true"
            />
            <Button
              v-if="canMarkReceived"
              label="Marquer comme reçu"
              icon="pi pi-box"
              class="bg-info-600 hover:bg-info-700 text-white border-0"
              :loading="actionLoading === 'received'"
              @click="handleMarkReceived"
            />
            <Button
              label="Envoyer un message"
              icon="pi pi-envelope"
              class="bg-gray-600 hover:bg-gray-700 text-white border-0"
              :loading="actionLoading === 'message'"
              @click="showMessageDialog = true"
            />
          </div>
        </template>
      </Card>

      <!-- Main Content Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Return Information -->
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #header>
            <div class="p-4 border-b border-gray-100">
              <h2 class="text-lg font-semibold text-secondary-900 flex items-center gap-2">
                <i class="pi pi-undo text-platform-ebay" />
                Informations Retour
              </h2>
            </div>
          </template>
          <template #content>
            <div class="space-y-3">
              <div>
                <p class="text-xs text-gray-500 mb-1">ID Retour</p>
                <p class="font-mono font-medium">{{ returnItem.return_id }}</p>
              </div>
              <div v-if="returnItem.order_id">
                <p class="text-xs text-gray-500 mb-1">ID Commande</p>
                <p class="font-mono font-medium">{{ returnItem.order_id }}</p>
              </div>
              <div v-if="returnItem.return_type">
                <p class="text-xs text-gray-500 mb-1">Type</p>
                <p class="font-medium">{{ returnItem.return_type }}</p>
              </div>
              <div v-if="returnItem.rma_number">
                <p class="text-xs text-gray-500 mb-1">Numéro RMA</p>
                <p class="font-mono font-medium">{{ returnItem.rma_number }}</p>
              </div>
            </div>
          </template>
        </Card>

        <!-- Buyer Information -->
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #header>
            <div class="p-4 border-b border-gray-100">
              <h2 class="text-lg font-semibold text-secondary-900 flex items-center gap-2">
                <i class="pi pi-user text-platform-ebay" />
                Acheteur
              </h2>
            </div>
          </template>
          <template #content>
            <div class="space-y-3">
              <div>
                <p class="text-xs text-gray-500 mb-1">Nom d'utilisateur</p>
                <p class="font-medium">{{ returnItem.buyer_username || '-' }}</p>
              </div>
            </div>
          </template>
        </Card>

        <!-- Reason -->
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #header>
            <div class="p-4 border-b border-gray-100">
              <h2 class="text-lg font-semibold text-secondary-900 flex items-center gap-2">
                <i class="pi pi-question-circle text-platform-ebay" />
                Motif du retour
              </h2>
            </div>
          </template>
          <template #content>
            <div class="space-y-3">
              <div>
                <p class="text-xs text-gray-500 mb-1">Motif principal</p>
                <p class="font-medium">{{ getReasonLabel(returnItem.reason) }}</p>
              </div>
              <div v-if="returnItem.reason_detail">
                <p class="text-xs text-gray-500 mb-1">Détails</p>
                <p class="font-medium text-gray-700">{{ returnItem.reason_detail }}</p>
              </div>
              <div v-if="returnItem.buyer_comments">
                <p class="text-xs text-gray-500 mb-1">Commentaires acheteur</p>
                <p class="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">{{ returnItem.buyer_comments }}</p>
              </div>
            </div>
          </template>
        </Card>

        <!-- Shipping / Tracking -->
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #header>
            <div class="p-4 border-b border-gray-100">
              <h2 class="text-lg font-semibold text-secondary-900 flex items-center gap-2">
                <i class="pi pi-send text-platform-ebay" />
                Suivi Retour
              </h2>
            </div>
          </template>
          <template #content>
            <div class="space-y-3">
              <div v-if="returnItem.return_tracking_number">
                <p class="text-xs text-gray-500 mb-1">Numéro de suivi</p>
                <p class="font-mono font-medium">{{ returnItem.return_tracking_number }}</p>
              </div>
              <div v-if="returnItem.return_carrier">
                <p class="text-xs text-gray-500 mb-1">Transporteur</p>
                <p class="font-medium">{{ returnItem.return_carrier }}</p>
              </div>
              <div v-if="!returnItem.return_tracking_number && !returnItem.return_carrier">
                <p class="text-gray-400 text-sm">Aucune information de suivi disponible</p>
              </div>
            </div>
          </template>
        </Card>

        <!-- Dates -->
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #header>
            <div class="p-4 border-b border-gray-100">
              <h2 class="text-lg font-semibold text-secondary-900 flex items-center gap-2">
                <i class="pi pi-calendar text-platform-ebay" />
                Dates
              </h2>
            </div>
          </template>
          <template #content>
            <div class="space-y-3">
              <div v-if="returnItem.creation_date">
                <p class="text-xs text-gray-500 mb-1">Création</p>
                <p class="font-medium">{{ formatDate(returnItem.creation_date) }}</p>
              </div>
              <div v-if="returnItem.deadline_date">
                <p class="text-xs text-gray-500 mb-1">Échéance</p>
                <p
                  class="font-medium"
                  :class="returnItem.is_past_deadline ? 'text-red-600' : ''"
                >
                  {{ formatDate(returnItem.deadline_date) }}
                </p>
              </div>
              <div v-if="returnItem.received_date">
                <p class="text-xs text-gray-500 mb-1">Reçu le</p>
                <p class="font-medium">{{ formatDate(returnItem.received_date) }}</p>
              </div>
              <div v-if="returnItem.closed_date">
                <p class="text-xs text-gray-500 mb-1">Fermé le</p>
                <p class="font-medium">{{ formatDate(returnItem.closed_date) }}</p>
              </div>
            </div>
          </template>
        </Card>

        <!-- Refund Details -->
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #header>
            <div class="p-4 border-b border-gray-100">
              <h2 class="text-lg font-semibold text-secondary-900 flex items-center gap-2">
                <i class="pi pi-dollar text-platform-ebay" />
                Remboursement
              </h2>
            </div>
          </template>
          <template #content>
            <div class="space-y-3">
              <div>
                <p class="text-xs text-gray-500 mb-1">Montant</p>
                <p v-if="returnItem.refund_amount" class="font-semibold text-lg text-success-600">
                  {{ formatAmount(returnItem.refund_amount, returnItem.refund_currency) }}
                </p>
                <p v-else class="text-gray-400">Non défini</p>
              </div>
              <div v-if="returnItem.refund_status">
                <p class="text-xs text-gray-500 mb-1">Statut</p>
                <p class="font-medium">{{ returnItem.refund_status }}</p>
              </div>
              <div v-if="returnItem.seller_comments">
                <p class="text-xs text-gray-500 mb-1">Commentaires vendeur</p>
                <p class="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">{{ returnItem.seller_comments }}</p>
              </div>
            </div>
          </template>
        </Card>
      </div>
    </div>

    <!-- Accept Dialog -->
    <Dialog
      v-model:visible="showAcceptDialog"
      header="Accepter le retour"
      :modal="true"
      :style="{ width: '450px' }"
    >
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Commentaires (optionnel)</label>
          <Textarea
            v-model="acceptForm.comments"
            rows="3"
            class="w-full"
            placeholder="Commentaires pour l'acheteur..."
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Numéro RMA (optionnel)</label>
          <InputText
            v-model="acceptForm.rma_number"
            class="w-full"
            placeholder="Numéro RMA"
          />
        </div>
      </div>
      <template #footer>
        <Button label="Annuler" text @click="showAcceptDialog = false" />
        <Button
          label="Accepter"
          icon="pi pi-check"
          class="bg-success-600 hover:bg-success-700 text-white border-0"
          :loading="actionLoading === 'accept'"
          @click="handleAccept"
        />
      </template>
    </Dialog>

    <!-- Decline Dialog -->
    <Dialog
      v-model:visible="showDeclineDialog"
      header="Refuser le retour"
      :modal="true"
      :style="{ width: '450px' }"
    >
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Raison du refus (requis)</label>
          <Textarea
            v-model="declineForm.comments"
            rows="3"
            class="w-full"
            placeholder="Expliquez pourquoi vous refusez ce retour..."
          />
        </div>
      </div>
      <template #footer>
        <Button label="Annuler" text @click="showDeclineDialog = false" />
        <Button
          label="Refuser"
          icon="pi pi-times"
          class="bg-error-600 hover:bg-error-700 text-white border-0"
          :loading="actionLoading === 'decline'"
          :disabled="!declineForm.comments"
          @click="handleDecline"
        />
      </template>
    </Dialog>

    <!-- Refund Dialog -->
    <Dialog
      v-model:visible="showRefundDialog"
      header="Émettre un remboursement"
      :modal="true"
      :style="{ width: '450px' }"
    >
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Montant (laisser vide pour remboursement total)</label>
          <InputNumber
            v-model="refundForm.amount"
            mode="currency"
            :currency="returnItem?.refund_currency || 'EUR'"
            class="w-full"
            placeholder="Montant partiel..."
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Commentaires (optionnel)</label>
          <Textarea
            v-model="refundForm.comments"
            rows="3"
            class="w-full"
            placeholder="Commentaires sur le remboursement..."
          />
        </div>
      </div>
      <template #footer>
        <Button label="Annuler" text @click="showRefundDialog = false" />
        <Button
          label="Rembourser"
          icon="pi pi-dollar"
          class="bg-platform-ebay hover:bg-blue-700 text-white border-0"
          :loading="actionLoading === 'refund'"
          @click="handleRefund"
        />
      </template>
    </Dialog>

    <!-- Message Dialog -->
    <Dialog
      v-model:visible="showMessageDialog"
      header="Envoyer un message"
      :modal="true"
      :style="{ width: '450px' }"
    >
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Message (requis)</label>
          <Textarea
            v-model="messageForm.message"
            rows="4"
            class="w-full"
            placeholder="Votre message à l'acheteur..."
          />
        </div>
      </div>
      <template #footer>
        <Button label="Annuler" text @click="showMessageDialog = false" />
        <Button
          label="Envoyer"
          icon="pi pi-send"
          class="bg-gray-600 hover:bg-gray-700 text-white border-0"
          :loading="actionLoading === 'message'"
          :disabled="!messageForm.message"
          @click="handleSendMessage"
        />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import type { EbayReturn } from '~/types/ebay'

definePageMeta({
  layout: 'dashboard'
})

// Get return ID from route
const route = useRoute()
const returnId = computed(() => Number(route.params.id))

// Toast notifications
const { showSuccess, showError } = useAppToast()

// Composable
const {
  fetchReturn,
  acceptReturn,
  declineReturn,
  issueRefund,
  markAsReceived,
  sendMessage,
  getStatusLabel,
  getStatusSeverity,
  getStateLabel,
  getStateSeverity,
  getReasonLabel
} = useEbayReturns()

// State
const loading = ref(true)
const error = ref<string | null>(null)
const returnItem = ref<EbayReturn | null>(null)
const actionLoading = ref<string | null>(null)

// Dialog visibility
const showAcceptDialog = ref(false)
const showDeclineDialog = ref(false)
const showRefundDialog = ref(false)
const showMessageDialog = ref(false)

// Form data
const acceptForm = ref({
  comments: '',
  rma_number: ''
})

const declineForm = ref({
  comments: ''
})

const refundForm = ref({
  amount: null as number | null,
  comments: ''
})

const messageForm = ref({
  message: ''
})

// Computed - Action availability
const canAccept = computed(() => {
  const status = returnItem.value?.status
  return status === 'RETURN_REQUESTED' || status === 'RETURN_WAITING_FOR_RMA'
})

const canDecline = computed(() => {
  const status = returnItem.value?.status
  return status === 'RETURN_REQUESTED'
})

const canRefund = computed(() => {
  const status = returnItem.value?.status
  return status === 'RETURN_ITEM_DELIVERED' || status === 'RETURN_ACCEPTED'
})

const canMarkReceived = computed(() => {
  const status = returnItem.value?.status
  return status === 'RETURN_ITEM_SHIPPED'
})

// Methods
const fetchReturnDetails = async () => {
  loading.value = true
  error.value = null

  try {
    returnItem.value = await fetchReturn(returnId.value)
  } catch (e: unknown) {
    const err = e as Error
    error.value = err.message || 'Erreur lors du chargement du retour'
    showError('Erreur', error.value, 5000)
  } finally {
    loading.value = false
  }
}

const handleAccept = async () => {
  if (!returnItem.value) return

  actionLoading.value = 'accept'
  try {
    await acceptReturn(returnItem.value.id, {
      comments: acceptForm.value.comments || undefined,
      rma_number: acceptForm.value.rma_number || undefined
    })
    showSuccess('Succès', 'Le retour a été accepté', 4000)
    showAcceptDialog.value = false
    acceptForm.value = { comments: '', rma_number: '' }
    await fetchReturnDetails()
  } catch (e: unknown) {
    const err = e as Error
    showError('Erreur', err.message || 'Impossible d\'accepter le retour', 5000)
  } finally {
    actionLoading.value = null
  }
}

const handleDecline = async () => {
  if (!returnItem.value || !declineForm.value.comments) return

  actionLoading.value = 'decline'
  try {
    await declineReturn(returnItem.value.id, declineForm.value.comments)
    showSuccess('Succès', 'Le retour a été refusé', 4000)
    showDeclineDialog.value = false
    declineForm.value = { comments: '' }
    await fetchReturnDetails()
  } catch (e: unknown) {
    const err = e as Error
    showError('Erreur', err.message || 'Impossible de refuser le retour', 5000)
  } finally {
    actionLoading.value = null
  }
}

const handleRefund = async () => {
  if (!returnItem.value) return

  actionLoading.value = 'refund'
  try {
    await issueRefund(returnItem.value.id, {
      refund_amount: refundForm.value.amount || undefined,
      currency: returnItem.value.refund_currency || undefined,
      comments: refundForm.value.comments || undefined
    })
    showSuccess('Succès', 'Le remboursement a été émis', 4000)
    showRefundDialog.value = false
    refundForm.value = { amount: null, comments: '' }
    await fetchReturnDetails()
  } catch (e: unknown) {
    const err = e as Error
    showError('Erreur', err.message || 'Impossible d\'émettre le remboursement', 5000)
  } finally {
    actionLoading.value = null
  }
}

const handleMarkReceived = async () => {
  if (!returnItem.value) return

  actionLoading.value = 'received'
  try {
    await markAsReceived(returnItem.value.id)
    showSuccess('Succès', 'L\'article a été marqué comme reçu', 4000)
    await fetchReturnDetails()
  } catch (e: unknown) {
    const err = e as Error
    showError('Erreur', err.message || 'Impossible de marquer comme reçu', 5000)
  } finally {
    actionLoading.value = null
  }
}

const handleSendMessage = async () => {
  if (!returnItem.value || !messageForm.value.message) return

  actionLoading.value = 'message'
  try {
    await sendMessage(returnItem.value.id, messageForm.value.message)
    showSuccess('Succès', 'Le message a été envoyé', 4000)
    showMessageDialog.value = false
    messageForm.value = { message: '' }
  } catch (e: unknown) {
    const err = e as Error
    showError('Erreur', err.message || 'Impossible d\'envoyer le message', 5000)
  } finally {
    actionLoading.value = null
  }
}

const formatAmount = (amount: number | null | undefined, currency: string | null | undefined = 'EUR') => {
  if (amount === null || amount === undefined) return '-'
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: currency || 'EUR'
  }).format(amount)
}

const formatDate = (date: string | null | undefined) => {
  if (!date) return '-'
  return new Intl.DateTimeFormat('fr-FR', {
    dateStyle: 'medium',
    timeStyle: 'short'
  }).format(new Date(date))
}

// Lifecycle
onMounted(() => {
  fetchReturnDetails()
})
</script>
