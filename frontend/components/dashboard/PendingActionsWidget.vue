<template>
  <Card v-if="pendingCount > 0" class="shadow-md border-orange-200">
    <template #title>
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <i class="pi pi-exclamation-triangle text-orange-500"/>
          <span class="text-secondary-900 font-bold">Actions en attente</span>
          <Badge :value="pendingCount" severity="warn" />
        </div>
        <div class="flex gap-2" v-if="pendingActions.length > 1">
          <Button
            label="Tout confirmer"
            icon="pi pi-check-circle"
            size="small"
            severity="success"
            text
            @click="handleBulkConfirm"
          />
          <Button
            label="Tout restaurer"
            icon="pi pi-undo"
            size="small"
            severity="secondary"
            text
            @click="handleBulkReject"
          />
        </div>
      </div>
    </template>
    <template #content>
      <p class="text-sm text-gray-500 mb-4">
        Ces produits ont été détectés comme vendus/supprimés sur les marketplaces.
        Confirmez ou restaurez-les.
      </p>

      <div class="space-y-2">
        <div
          v-for="action in pendingActions"
          :key="action.id"
          class="flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:border-orange-300 transition"
        >
          <div class="flex items-center gap-3 flex-1 min-w-0">
            <div class="w-8 h-8 rounded-lg flex items-center justify-center"
                 :class="getMarketplaceBgClass(action.marketplace)">
              <img
                :src="getMarketplaceLogo(action.marketplace)"
                :alt="getMarketplaceLabel(action.marketplace)"
                class="w-5 h-5 object-contain"
              >
            </div>

            <div class="min-w-0 flex-1">
              <p class="text-sm font-medium text-secondary-900 truncate">
                {{ action.product?.title || `Produit #${action.product_id}` }}
              </p>
              <p class="text-xs text-gray-500 truncate">
                {{ action.reason }}
              </p>
            </div>

            <Badge
              :value="getActionTypeLabel(action.action_type)"
              :severity="action.action_type === 'mark_sold' ? 'info' : 'warn'"
              class="shrink-0"
            />
          </div>

          <div class="flex items-center gap-1 ml-3 shrink-0">
            <Button
              icon="pi pi-check"
              size="small"
              severity="success"
              rounded
              text
              @click="handleConfirm(action.id)"
              v-tooltip.top="'Confirmer (vendu)'"
            />
            <Button
              icon="pi pi-undo"
              size="small"
              severity="secondary"
              rounded
              text
              @click="handleReject(action.id)"
              v-tooltip.top="'Restaurer'"
            />
          </div>
        </div>
      </div>

      <div v-if="isLoading" class="flex justify-center py-4">
        <i class="pi pi-spin pi-spinner text-2xl text-gray-400"/>
      </div>
    </template>
  </Card>
</template>

<script setup lang="ts">
const {
  pendingActions,
  pendingCount,
  isLoading,
  fetchPendingActions,
  confirmAction,
  rejectAction,
  bulkConfirmAll,
  bulkRejectAll,
  getActionTypeLabel,
  getMarketplaceLabel,
} = usePendingActions()

// Fetch on mount
onMounted(async () => {
  await fetchPendingActions()
})

async function handleConfirm(actionId: number) {
  await confirmAction(actionId)
}

async function handleReject(actionId: number) {
  await rejectAction(actionId)
}

async function handleBulkConfirm() {
  await bulkConfirmAll()
}

async function handleBulkReject() {
  await bulkRejectAll()
}

function getMarketplaceBgClass(marketplace: string): string {
  const classes: Record<string, string> = {
    vinted: 'bg-teal-100',
    ebay: 'bg-blue-100',
    etsy: 'bg-orange-100',
  }
  return classes[marketplace] || 'bg-gray-100'
}

function getMarketplaceLogo(marketplace: string): string {
  const logos: Record<string, string> = {
    vinted: '/images/vinted-logo.svg',
    ebay: '/images/ebay-logo.svg',
    etsy: '/images/etsy-logo.svg',
  }
  return logos[marketplace] || ''
}
</script>
