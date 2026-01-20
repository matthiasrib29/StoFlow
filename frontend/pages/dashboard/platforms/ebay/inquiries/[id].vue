<script setup lang="ts">
import { ebayLogger } from '~/utils/logger'
/**
 * eBay INR Inquiry Detail Page
 *
 * Displays detailed information about a specific INR inquiry
 * with actions to provide shipment info, refund, message, or escalate.
 */

import type { EbayInquiry } from '~/types/ebay'

definePageMeta({
  layout: 'dashboard',
})

const route = useRoute()
const router = useRouter()
const toast = useAppToast()

const {
  fetchInquiry,
  provideShipmentInfo,
  provideRefund,
  sendMessage,
  escalateInquiry,
  getStateLabel,
  getStateSeverity,
  getStatusLabel,
  getStatusSeverity,
  getStateIcon,
  getStatusIcon,
  formatAmount,
  formatDate,
  getCarrierOptions,
  isUrgent,
  getDaysUntilDeadline
} = useEbayInquiries()

// =========================================================================
// STATE
// =========================================================================

const inquiry = ref<EbayInquiry | null>(null)
const loading = ref(false)
const actionLoading = ref(false)

// Dialogs
const showShipmentDialog = ref(false)
const showRefundDialog = ref(false)
const showMessageDialog = ref(false)
const showEscalateDialog = ref(false)

// Form data
const shipmentForm = ref({
  trackingNumber: '',
  carrier: null as string | null,
  shippedDate: null as Date | null,
  comments: ''
})

const refundForm = ref({
  refundAmount: null as number | null,
  currency: 'EUR',
  comments: ''
})

const messageForm = ref({
  message: ''
})

const escalateForm = ref({
  comments: ''
})

// =========================================================================
// COMPUTED
// =========================================================================

const inquiryId = computed(() => {
  const id = route.params.id
  return Array.isArray(id) ? parseInt(id[0]) : parseInt(id)
})

const canTakeAction = computed(() => {
  if (!inquiry.value) return false
  return (
    inquiry.value.inquiry_state === 'OPEN' &&
    inquiry.value.inquiry_status === 'INR_WAITING_FOR_SELLER'
  )
})

const canEscalate = computed(() => {
  if (!inquiry.value) return false
  return (
    inquiry.value.inquiry_state === 'OPEN' &&
    !inquiry.value.is_escalated
  )
})

const daysUntilDeadline = computed(() => {
  if (!inquiry.value) return null
  return getDaysUntilDeadline(inquiry.value)
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

const loadInquiry = async () => {
  loading.value = true
  try {
    inquiry.value = await fetchInquiry(inquiryId.value)
  } catch (error) {
    ebayLogger.error('Failed to load inquiry:', error)
    toast.add({
      severity: 'error',
      summary: 'Erreur',
      detail: 'Impossible de charger la réclamation',
      life: 5000
    })
    router.push('/dashboard/platforms/ebay/inquiries')
  } finally {
    loading.value = false
  }
}

// =========================================================================
// ACTIONS
// =========================================================================

const handleProvideShipment = async () => {
  if (!inquiry.value || !shipmentForm.value.trackingNumber || !shipmentForm.value.carrier) return
  actionLoading.value = true
  try {
    const result = await provideShipmentInfo(inquiry.value.id, {
      tracking_number: shipmentForm.value.trackingNumber,
      carrier: shipmentForm.value.carrier,
      shipped_date: shipmentForm.value.shippedDate?.toISOString() || null,
      comments: shipmentForm.value.comments || null
    })
    if (result.success) {
      toast.add({
        severity: 'success',
        summary: 'Information envoyée',
        detail: 'Les informations de suivi ont été fournies',
        life: 5000
      })
      showShipmentDialog.value = false
      shipmentForm.value = { trackingNumber: '', carrier: null, shippedDate: null, comments: '' }
      await loadInquiry()
    } else {
      throw new Error(result.message || 'Action failed')
    }
  } catch (error) {
    ebayLogger.error('Shipment info failed:', error)
    toast.add({
      severity: 'error',
      summary: 'Erreur',
      detail: "Impossible d'envoyer les informations de suivi",
      life: 5000
    })
  } finally {
    actionLoading.value = false
  }
}

const handleProvideRefund = async () => {
  if (!inquiry.value) return
  actionLoading.value = true
  try {
    const result = await provideRefund(inquiry.value.id, {
      refund_amount: refundForm.value.refundAmount,
      currency: refundForm.value.currency || null,
      comments: refundForm.value.comments || null
    })
    if (result.success) {
      toast.add({
        severity: 'success',
        summary: 'Remboursement initié',
        detail: 'Le remboursement a été initié',
        life: 5000
      })
      showRefundDialog.value = false
      refundForm.value = { refundAmount: null, currency: 'EUR', comments: '' }
      await loadInquiry()
    } else {
      throw new Error(result.message || 'Action failed')
    }
  } catch (error) {
    ebayLogger.error('Refund failed:', error)
    toast.add({
      severity: 'error',
      summary: 'Erreur',
      detail: "Impossible d'initier le remboursement",
      life: 5000
    })
  } finally {
    actionLoading.value = false
  }
}

const handleSendMessage = async () => {
  if (!inquiry.value || !messageForm.value.message) return
  actionLoading.value = true
  try {
    const result = await sendMessage(inquiry.value.id, messageForm.value.message)
    if (result.success) {
      toast.add({
        severity: 'success',
        summary: 'Message envoyé',
        detail: "Le message a été envoyé à l'acheteur",
        life: 5000
      })
      showMessageDialog.value = false
      messageForm.value = { message: '' }
      await loadInquiry()
    } else {
      throw new Error(result.message || 'Action failed')
    }
  } catch (error) {
    ebayLogger.error('Send message failed:', error)
    toast.add({
      severity: 'error',
      summary: 'Erreur',
      detail: "Impossible d'envoyer le message",
      life: 5000
    })
  } finally {
    actionLoading.value = false
  }
}

const handleEscalate = async () => {
  if (!inquiry.value) return
  actionLoading.value = true
  try {
    const result = await escalateInquiry(
      inquiry.value.id,
      escalateForm.value.comments || null
    )
    if (result.success) {
      toast.add({
        severity: 'warn',
        summary: 'Réclamation escaladée',
        detail: 'La réclamation a été escaladée vers eBay',
        life: 5000
      })
      showEscalateDialog.value = false
      escalateForm.value = { comments: '' }
      await loadInquiry()
    } else {
      throw new Error(result.message || 'Action failed')
    }
  } catch (error) {
    ebayLogger.error('Escalate failed:', error)
    toast.add({
      severity: 'error',
      summary: 'Erreur',
      detail: "Impossible d'escalader la réclamation",
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
  router.push('/dashboard/platforms/ebay/inquiries')
}

const goToOrder = () => {
  if (inquiry.value?.order_id) {
    router.push(`/dashboard/platforms/ebay/orders?search=${inquiry.value.order_id}`)
  }
}

// =========================================================================
// LIFECYCLE
// =========================================================================

onMounted(async () => {
  await loadInquiry()
})
</script>

<template>
  <div class="p-6">
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <ProgressSpinner />
    </div>

    <!-- Content -->
    <div v-else-if="inquiry">
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
              Réclamation #{{ inquiry.inquiry_id }}
            </h1>
            <p class="text-gray-600 dark:text-gray-400 mt-1">
              {{ formatDate(inquiry.creation_date || inquiry.created_at) }}
            </p>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <Tag
            :severity="getStateSeverity(inquiry.inquiry_state)"
            class="text-base px-4 py-2"
          >
            <template #default>
              <i :class="getStateIcon(inquiry.inquiry_state)" class="mr-2" />
              {{ getStateLabel(inquiry.inquiry_state) }}
            </template>
          </Tag>
        </div>
      </div>

      <!-- Urgent Alert -->
      <div
        v-if="isUrgent(inquiry)"
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
              <span v-else-if="inquiry.is_escalated">
                Cette réclamation a été escaladée.
              </span>
              <span v-else>
                Cette réclamation nécessite votre attention.
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
                <span>Montant réclamé</span>
              </div>
            </template>
            <template #content>
              <div class="text-center py-4">
                <p class="text-4xl font-bold text-red-600 dark:text-red-400">
                  {{ formatAmount(inquiry) }}
                </p>
              </div>
            </template>
          </Card>

          <!-- Details Card -->
          <Card>
            <template #title>
              <div class="flex items-center gap-2">
                <i class="pi pi-info-circle" />
                <span>Détails de la réclamation</span>
              </div>
            </template>
            <template #content>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Status -->
                <div>
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Statut</p>
                  <Tag
                    :severity="getStatusSeverity(inquiry.inquiry_status)"
                  >
                    <template #default>
                      <i :class="getStatusIcon(inquiry.inquiry_status)" class="mr-1" />
                      {{ getStatusLabel(inquiry.inquiry_status) }}
                    </template>
                  </Tag>
                </div>

                <!-- Buyer -->
                <div>
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Acheteur</p>
                  <p class="font-medium text-gray-900 dark:text-white">
                    {{ inquiry.buyer_username || '-' }}
                  </p>
                </div>

                <!-- Item -->
                <div class="md:col-span-2">
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Article</p>
                  <p class="font-medium text-gray-900 dark:text-white">
                    {{ inquiry.item_title || '-' }}
                  </p>
                  <p v-if="inquiry.item_id" class="text-sm text-gray-500 mt-1">
                    ID: {{ inquiry.item_id }}
                  </p>
                </div>

                <!-- Buyer comments -->
                <div v-if="inquiry.buyer_comments" class="md:col-span-2">
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Commentaires de l'acheteur</p>
                  <p class="text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
                    {{ inquiry.buyer_comments }}
                  </p>
                </div>

                <!-- Seller Response -->
                <div v-if="inquiry.seller_response">
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Votre réponse</p>
                  <p class="font-medium text-gray-900 dark:text-white">
                    {{ inquiry.seller_response }}
                  </p>
                </div>
              </div>
            </template>
          </Card>

          <!-- Shipment Info Card (if provided) -->
          <Card v-if="inquiry.shipment_tracking_number">
            <template #title>
              <div class="flex items-center gap-2">
                <i class="pi pi-truck" />
                <span>Informations de suivi</span>
              </div>
            </template>
            <template #content>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Numéro de suivi</p>
                  <p class="font-mono text-gray-900 dark:text-white">
                    {{ inquiry.shipment_tracking_number }}
                  </p>
                </div>
                <div v-if="inquiry.shipment_carrier">
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Transporteur</p>
                  <p class="font-medium text-gray-900 dark:text-white">
                    {{ inquiry.shipment_carrier }}
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
                      {{ inquiry.order_id || '-' }}
                    </p>
                    <Button
                      v-if="inquiry.order_id"
                      icon="pi pi-external-link"
                      text
                      rounded
                      size="small"
                      @click="goToOrder"
                    />
                  </div>
                </div>

                <!-- Inquiry ID -->
                <div>
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">ID Réclamation eBay</p>
                  <p class="font-mono text-sm text-gray-900 dark:text-white">
                    {{ inquiry.inquiry_id }}
                  </p>
                </div>

                <!-- Inquiry Type -->
                <div>
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Type</p>
                  <p class="font-medium text-gray-900 dark:text-white">
                    {{ inquiry.inquiry_type || 'INR' }}
                  </p>
                </div>
              </div>
            </template>
          </Card>
        </div>

        <!-- Right Column: Actions & Timeline -->
        <div class="space-y-6">
          <!-- Actions Card -->
          <Card v-if="canTakeAction || canEscalate">
            <template #title>
              <div class="flex items-center gap-2">
                <i class="pi pi-bolt" />
                <span>Actions</span>
              </div>
            </template>
            <template #content>
              <div class="space-y-3">
                <!-- Provide Shipment Info -->
                <Button
                  v-if="canTakeAction"
                  label="Fournir suivi"
                  icon="pi pi-truck"
                  severity="info"
                  class="w-full"
                  @click="showShipmentDialog = true"
                />

                <!-- Provide Refund -->
                <Button
                  v-if="canTakeAction"
                  label="Rembourser"
                  icon="pi pi-money-bill"
                  severity="success"
                  class="w-full"
                  @click="showRefundDialog = true"
                />

                <!-- Send Message -->
                <Button
                  v-if="canTakeAction"
                  label="Envoyer message"
                  icon="pi pi-envelope"
                  severity="secondary"
                  outlined
                  class="w-full"
                  @click="showMessageDialog = true"
                />

                <!-- Escalate -->
                <Button
                  v-if="canEscalate"
                  label="Escalader"
                  icon="pi pi-arrow-up"
                  severity="warn"
                  outlined
                  class="w-full"
                  @click="showEscalateDialog = true"
                />
              </div>
            </template>
          </Card>

          <!-- Deadline Card -->
          <Card v-if="inquiry.respond_by_date">
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
                  {{ formatDate(inquiry.respond_by_date) }}
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
                    :severity="getStateSeverity(inquiry.inquiry_state)"
                  >
                    <template #default>
                      <i :class="getStateIcon(inquiry.inquiry_state)" class="mr-1" />
                      {{ getStateLabel(inquiry.inquiry_state) }}
                    </template>
                  </Tag>
                </div>

                <!-- Status indicators -->
                <div class="pt-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
                  <div class="flex items-center gap-2 text-sm">
                    <i
                      :class="[
                        'pi',
                        inquiry.is_open
                          ? 'pi-exclamation-circle text-yellow-500'
                          : 'pi-circle text-gray-300'
                      ]"
                    />
                    <span :class="inquiry.is_open ? 'text-yellow-600' : 'text-gray-400'">
                      Réclamation ouverte
                    </span>
                  </div>

                  <div class="flex items-center gap-2 text-sm">
                    <i
                      :class="[
                        'pi',
                        inquiry.needs_action
                          ? 'pi-clock text-orange-500'
                          : 'pi-circle text-gray-300'
                      ]"
                    />
                    <span :class="inquiry.needs_action ? 'text-orange-600' : 'text-gray-400'">
                      Action requise
                    </span>
                  </div>

                  <div class="flex items-center gap-2 text-sm">
                    <i
                      :class="[
                        'pi',
                        inquiry.is_past_due
                          ? 'pi-times text-red-500'
                          : 'pi-circle text-gray-300'
                      ]"
                    />
                    <span :class="inquiry.is_past_due ? 'text-red-600' : 'text-gray-400'">
                      En retard
                    </span>
                  </div>

                  <div class="flex items-center gap-2 text-sm">
                    <i
                      :class="[
                        'pi',
                        inquiry.is_escalated
                          ? 'pi-arrow-up text-purple-500'
                          : 'pi-circle text-gray-300'
                      ]"
                    />
                    <span :class="inquiry.is_escalated ? 'text-purple-600' : 'text-gray-400'">
                      Escaladé
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
                  <div class="p-2 bg-yellow-100 dark:bg-yellow-900/40 rounded-full">
                    <i class="pi pi-inbox text-yellow-600 dark:text-yellow-400 text-sm" />
                  </div>
                  <div>
                    <p class="text-sm font-medium text-gray-900 dark:text-white">
                      Réclamation ouverte
                    </p>
                    <p class="text-xs text-gray-500">
                      {{ formatDate(inquiry.creation_date) }}
                    </p>
                  </div>
                </div>

                <!-- Response Due Date -->
                <div v-if="inquiry.respond_by_date" class="flex items-start gap-3">
                  <div
                    class="p-2 rounded-full"
                    :class="
                      inquiry.is_past_due
                        ? 'bg-red-100 dark:bg-red-900/40'
                        : 'bg-orange-100 dark:bg-orange-900/40'
                    "
                  >
                    <i
                      :class="[
                        'pi text-sm',
                        inquiry.is_past_due
                          ? 'pi-times text-red-600 dark:text-red-400'
                          : 'pi-clock text-orange-600 dark:text-orange-400'
                      ]"
                    />
                  </div>
                  <div>
                    <p class="text-sm font-medium text-gray-900 dark:text-white">
                      {{ inquiry.is_past_due ? 'Deadline dépassée' : 'Deadline réponse' }}
                    </p>
                    <p class="text-xs text-gray-500">
                      {{ formatDate(inquiry.respond_by_date) }}
                    </p>
                  </div>
                </div>

                <!-- Escalation Date -->
                <div v-if="inquiry.escalation_date" class="flex items-start gap-3">
                  <div class="p-2 bg-purple-100 dark:bg-purple-900/40 rounded-full">
                    <i class="pi pi-arrow-up text-purple-600 dark:text-purple-400 text-sm" />
                  </div>
                  <div>
                    <p class="text-sm font-medium text-gray-900 dark:text-white">
                      Escaladé
                    </p>
                    <p class="text-xs text-gray-500">
                      {{ formatDate(inquiry.escalation_date) }}
                    </p>
                  </div>
                </div>

                <!-- Closed Date -->
                <div v-if="inquiry.closed_date" class="flex items-start gap-3">
                  <div class="p-2 bg-green-100 dark:bg-green-900/40 rounded-full">
                    <i class="pi pi-check-circle text-green-600 dark:text-green-400 text-sm" />
                  </div>
                  <div>
                    <p class="text-sm font-medium text-gray-900 dark:text-white">
                      Réclamation fermée
                    </p>
                    <p class="text-xs text-gray-500">
                      {{ formatDate(inquiry.closed_date) }}
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
                      {{ formatDate(inquiry.updated_at) }}
                    </p>
                  </div>
                </div>
              </div>
            </template>
          </Card>
        </div>
      </div>
    </div>

    <!-- Provide Shipment Dialog -->
    <Dialog
      v-model:visible="showShipmentDialog"
      header="Fournir informations de suivi"
      :modal="true"
      :closable="!actionLoading"
      class="w-full max-w-lg"
    >
      <div class="space-y-4">
        <p class="text-gray-600 dark:text-gray-400">
          Fournissez les informations de suivi pour prouver que l'article a été expédié.
        </p>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Numéro de suivi *
          </label>
          <InputText
            v-model="shipmentForm.trackingNumber"
            placeholder="Ex: 1Z999AA10123456784"
            class="w-full"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Transporteur *
          </label>
          <Dropdown
            v-model="shipmentForm.carrier"
            :options="getCarrierOptions()"
            option-label="label"
            option-value="value"
            placeholder="Sélectionner un transporteur"
            class="w-full"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Date d'expédition
          </label>
          <Calendar
            v-model="shipmentForm.shippedDate"
            date-format="dd/mm/yy"
            placeholder="Sélectionner une date"
            class="w-full"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Commentaire
          </label>
          <Textarea
            v-model="shipmentForm.comments"
            rows="3"
            placeholder="Message pour l'acheteur..."
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
            @click="showShipmentDialog = false"
          />
          <Button
            label="Envoyer"
            icon="pi pi-truck"
            :loading="actionLoading"
            :disabled="!shipmentForm.trackingNumber || !shipmentForm.carrier"
            @click="handleProvideShipment"
          />
        </div>
      </template>
    </Dialog>

    <!-- Provide Refund Dialog -->
    <Dialog
      v-model:visible="showRefundDialog"
      header="Rembourser l'acheteur"
      :modal="true"
      :closable="!actionLoading"
      class="w-full max-w-md"
    >
      <div class="space-y-4">
        <p class="text-gray-600 dark:text-gray-400">
          Initiez un remboursement pour résoudre cette réclamation.
          Laissez le montant vide pour un remboursement complet.
        </p>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Montant (optionnel pour remboursement partiel)
          </label>
          <div class="flex gap-2">
            <InputNumber
              v-model="refundForm.refundAmount"
              mode="currency"
              :currency="refundForm.currency"
              locale="fr-FR"
              placeholder="Montant complet si vide"
              class="flex-1"
            />
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Commentaire
          </label>
          <Textarea
            v-model="refundForm.comments"
            rows="3"
            placeholder="Raison du remboursement..."
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
            @click="showRefundDialog = false"
          />
          <Button
            label="Rembourser"
            icon="pi pi-money-bill"
            severity="success"
            :loading="actionLoading"
            @click="handleProvideRefund"
          />
        </div>
      </template>
    </Dialog>

    <!-- Send Message Dialog -->
    <Dialog
      v-model:visible="showMessageDialog"
      header="Envoyer un message"
      :modal="true"
      :closable="!actionLoading"
      class="w-full max-w-md"
    >
      <div class="space-y-4">
        <p class="text-gray-600 dark:text-gray-400">
          Envoyez un message à l'acheteur concernant cette réclamation.
        </p>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Message *
          </label>
          <Textarea
            v-model="messageForm.message"
            rows="5"
            placeholder="Votre message à l'acheteur..."
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
            @click="showMessageDialog = false"
          />
          <Button
            label="Envoyer"
            icon="pi pi-envelope"
            :loading="actionLoading"
            :disabled="!messageForm.message"
            @click="handleSendMessage"
          />
        </div>
      </template>
    </Dialog>

    <!-- Escalate Dialog -->
    <Dialog
      v-model:visible="showEscalateDialog"
      header="Escalader la réclamation"
      :modal="true"
      :closable="!actionLoading"
      class="w-full max-w-md"
    >
      <div class="space-y-4">
        <div class="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
          <div class="flex items-center gap-2">
            <i class="pi pi-exclamation-triangle text-yellow-600 dark:text-yellow-400" />
            <p class="font-medium text-yellow-700 dark:text-yellow-300">
              Attention
            </p>
          </div>
          <p class="text-sm text-yellow-600 dark:text-yellow-400 mt-2">
            L'escalade transmet la réclamation à eBay pour arbitrage.
            Cette action est irréversible.
          </p>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Commentaire (optionnel)
          </label>
          <Textarea
            v-model="escalateForm.comments"
            rows="3"
            placeholder="Raison de l'escalade..."
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
            @click="showEscalateDialog = false"
          />
          <Button
            label="Escalader"
            icon="pi pi-arrow-up"
            severity="warn"
            :loading="actionLoading"
            @click="handleEscalate"
          />
        </div>
      </template>
    </Dialog>
  </div>
</template>
