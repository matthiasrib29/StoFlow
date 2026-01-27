<template>
  <div v-if="pendingCount > 0" class="bg-white rounded-xl shadow-md border border-orange-200 overflow-hidden">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-2 px-4 py-3 border-b border-orange-100 bg-orange-50/50">
      <div class="flex items-center gap-2">
        <i class="pi pi-shopping-bag text-orange-500"/>
        <span class="text-secondary-900 font-bold text-sm">Actions en attente</span>
        <Badge :value="pendingCount" severity="warn" />
      </div>
      <div class="flex gap-2" v-if="pendingCount > 1">
        <Button
          :label="`Tout confirmer (${pendingCount})`"
          icon="pi pi-check-circle"
          size="small"
          severity="success"
          text
          @click="handleConfirmAll"
        />
        <Button
          label="Tout ignorer"
          icon="pi pi-times"
          size="small"
          severity="secondary"
          text
          @click="handleBulkReject"
        />
      </div>
    </div>

    <!-- Content -->
    <div class="p-4 space-y-3">
      <div
        v-for="action in pendingActions"
        :key="action.id"
        class="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:border-orange-300 transition"
      >
        <!-- Product image -->
        <div class="w-12 h-12 rounded-lg overflow-hidden bg-gray-100 shrink-0">
          <NuxtImg
            v-if="action.product?.image_url"
            :src="action.product.image_url"
            :alt="action.product?.title"
            class="w-full h-full object-cover"
          />
          <div v-else class="w-full h-full flex items-center justify-center">
            <i class="pi pi-image text-gray-400"/>
          </div>
        </div>

        <!-- Product info -->
        <div class="min-w-0 flex-1">
          <p class="text-sm font-medium text-secondary-900 truncate">
            {{ action.product?.title || `Produit #${action.product_id}` }}
          </p>
          <span class="text-xs text-gray-500">
            {{ getActionDescription(action) }}
          </span>
        </div>

        <!-- Action buttons -->
        <div class="flex items-center gap-2 shrink-0">
          <Button
            :label="getConfirmLabel(action)"
            icon="pi pi-check"
            size="small"
            severity="success"
            outlined
            @click="handleConfirm(action.id)"
          />
          <Button
            icon="pi pi-times"
            size="small"
            severity="secondary"
            text
            rounded
            @click="handleReject(action.id)"
            v-tooltip.top="'Ignorer'"
          />
        </div>
      </div>

      <div v-if="isLoading" class="flex justify-center py-4">
        <i class="pi pi-spin pi-spinner text-2xl text-gray-400"/>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex items-center justify-between px-4 py-3 border-t border-gray-100 bg-gray-50/50">
      <span class="text-xs text-gray-500">
        Page {{ currentPage }} / {{ totalPages }}
      </span>
      <div class="flex gap-1">
        <Button
          icon="pi pi-chevron-left"
          size="small"
          severity="secondary"
          text
          rounded
          :disabled="currentPage <= 1"
          @click="prevPage"
        />
        <Button
          icon="pi pi-chevron-right"
          size="small"
          severity="secondary"
          text
          rounded
          :disabled="currentPage >= totalPages"
          @click="nextPage"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const {
  pendingActions,
  pendingCount,
  currentPage,
  totalPages,
  isLoading,
  fetchPendingActions,
  nextPage,
  prevPage,
  confirmAction,
  rejectAction,
  confirmAllPending,
  bulkRejectAll,
  getActionDescription,
  getConfirmLabel,
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

async function handleConfirmAll() {
  await confirmAllPending()
}

async function handleBulkReject() {
  await bulkRejectAll()
}
</script>
