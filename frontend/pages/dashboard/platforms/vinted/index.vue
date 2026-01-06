<template>
  <div class="page-container">
    <!-- Stats Cards -->
    <VintedStatsCards :stats="stats" />

    <!-- Connection Card -->
    <VintedConnectionCard
      :is-connected="isConnected"
      :connection-info="connectionInfo"
      :sync-loading="syncLoading"
      :loading="loading"
      @sync="handleSyncProducts"
      @connect="handleConnect"
    />

    <!-- Sync Result Card -->
    <VintedSyncResultCard
      :sync-result="rawSyncResult"
      @copy="copyRawResult"
      @close="clearSyncResult"
    />

    <!-- Synced Products JSON Card -->
    <Card v-if="isConnected && syncedProducts.length > 0" class="shadow-sm modern-rounded border border-gray-100">
      <template #content>
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-bold text-secondary-900">Produits Synchronisés (JSON Brut)</h3>
          <div class="flex gap-2">
            <Button
              label="Copier JSON"
              icon="pi pi-copy"
              class="bg-gray-100 hover:bg-gray-200 text-secondary-900 border-0"
              size="small"
              @click="copySyncedProducts"
            />
            <Button
              label="Effacer"
              icon="pi pi-times"
              class="btn-danger"
              size="small"
              @click="clearSyncedProducts"
            />
          </div>
        </div>
        <div class="bg-gray-50 rounded-lg p-4 max-h-96 overflow-auto">
          <pre class="text-xs text-gray-800 whitespace-pre-wrap break-words">{{ JSON.stringify(syncedProducts, null, 2) }}</pre>
        </div>
        <div class="mt-3 text-sm text-gray-600">
          <i class="pi pi-info-circle mr-2"/>
          {{ syncedProducts.length }} produit(s) récupéré(s) depuis Vinted
        </div>
      </template>
    </Card>

    <!-- Price Edit Modal -->
    <Dialog
      v-model:visible="priceModalVisible"
      modal
      header="Modifier le prix"
      class="w-[400px]"
    >
      <div v-if="selectedPublication" class="space-y-4">
        <div>
          <p class="font-semibold text-secondary-900 mb-2">{{ selectedPublication.product.title }}</p>
          <p class="text-sm text-gray-600 mb-4">Prix actuel: {{ formatCurrency(selectedPublication.price) }}</p>
        </div>
        <div>
          <label class="block text-sm font-semibold text-secondary-900 mb-2">Nouveau prix</label>
          <InputNumber
            v-model="newPrice"
            mode="currency"
            currency="EUR"
            locale="fr-FR"
            class="w-full"
            :min="0"
            :max-fraction-digits="2"
          />
        </div>
      </div>
      <template #footer>
        <Button
          label="Annuler"
          icon="pi pi-times"
          class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
          @click="priceModalVisible = false"
        />
        <Button
          label="Sauvegarder"
          icon="pi pi-check"
          class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
          @click="updatePrice"
        />
      </template>
    </Dialog>

    <!-- Synced Products Modal -->
    <Dialog
      v-model:visible="syncModalVisible"
      modal
      header="Produits synchronisés depuis Vinted"
      class="w-[900px]"
      :maximizable="true"
    >
      <div v-if="syncedProducts.length > 0">
        <p class="text-gray-600 mb-4">
          {{ syncedProducts.length }} produit(s) trouvé(s) sur votre compte Vinted
        </p>
        <DataTable
          :value="syncedProducts"
          :paginator="true"
          :rows="5"
          class="modern-table"
          striped-rows
        >
          <Column field="title" header="Titre" sortable>
            <template #body="{ data }">
              <div class="flex items-center gap-3">
                <img
                  v-if="data.photo?.url"
                  :src="data.photo.url"
                  :alt="data.title"
                  class="w-12 h-12 rounded-lg object-cover"
                >
                <div v-else class="w-12 h-12 rounded-lg bg-gray-100 flex items-center justify-center">
                  <i class="pi pi-image text-gray-400"/>
                </div>
                <div>
                  <p class="font-semibold text-secondary-900">{{ data.title }}</p>
                  <p class="text-xs text-gray-500">ID: {{ data.id }}</p>
                </div>
              </div>
            </template>
          </Column>
          <Column field="price" header="Prix" sortable>
            <template #body="{ data }">
              <span class="font-bold text-secondary-900">{{ formatCurrency(data.price || 0) }}</span>
            </template>
          </Column>
          <Column field="brand" header="Marque" sortable>
            <template #body="{ data }">
              <span class="text-sm">{{ data.brand || '-' }}</span>
            </template>
          </Column>
          <Column field="size" header="Taille" sortable>
            <template #body="{ data }">
              <span class="text-sm">{{ data.size || '-' }}</span>
            </template>
          </Column>
          <Column field="view_count" header="Vues" sortable>
            <template #body="{ data }">
              <div class="flex items-center gap-2">
                <i class="pi pi-eye text-gray-400 text-sm"/>
                <span>{{ data.view_count || 0 }}</span>
              </div>
            </template>
          </Column>
          <Column field="favourite_count" header="Favoris" sortable>
            <template #body="{ data }">
              <div class="flex items-center gap-2">
                <i class="pi pi-heart text-gray-400 text-sm"/>
                <span>{{ data.favourite_count || 0 }}</span>
              </div>
            </template>
          </Column>
        </DataTable>
      </div>
      <div v-else class="text-center py-8">
        <i class="pi pi-inbox text-gray-300 text-5xl mb-3"/>
        <p class="text-gray-600">Aucun produit trouvé</p>
      </div>
      <template #footer>
        <Button
          label="Fermer"
          icon="pi pi-times"
          class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
          @click="syncModalVisible = false"
        />
      </template>
    </Dialog>

    <!-- Confirm Dialog -->
    <ConfirmDialog />
  </div>
</template>

<script setup lang="ts">
import { useConfirm } from 'primevue/useconfirm'
import { formatCurrency } from '~/utils/formatters'
import type { Publication } from '~/stores/publications'

definePageMeta({
  layout: 'dashboard'
})

// SSR-safe initialization
const confirm = import.meta.client ? useConfirm() : null
const publicationsStore = usePublicationsStore()
const { put } = useApi()
const { showSuccess, showError, showInfo } = useAppToast()

// Use extracted composables
const {
  isConnected,
  loading,
  connectionInfo,
  stats,
  connect,
  disconnect,
  fetchConnectionStatus,
  fetchStats,
  updateLastSync
} = useVintedConnection()

const {
  syncLoading,
  syncedProducts,
  rawSyncResult,
  syncModalVisible,
  syncProducts,
  copyRawResult,
  copySyncedProducts,
  clearSyncResult,
  clearSyncedProducts
} = useVintedSync()

// Local state for price editing
const priceModalVisible = ref(false)
const selectedPublication = ref<Publication | null>(null)
const newPrice = ref(0)

// Methods
const handleConnect = async () => {
  const success = await connect()
  if (success) {
    await fetchVintedProducts()
    await fetchStats()
  }
}

const handleSyncProducts = async () => {
  const result = await syncProducts()
  if (result) {
    updateLastSync()
  }
}

const handleDisconnect = () => {
  confirm?.require({
    message: 'Voulez-vous vraiment déconnecter votre compte Vinted ?',
    header: 'Confirmation',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Oui, déconnecter',
    rejectLabel: 'Annuler',
    accept: () => disconnect()
  })
}

const fetchVintedProducts = async () => {
  // Products are fetched as part of sync
}

const editPrice = (publication: any) => {
  selectedPublication.value = publication
  newPrice.value = publication.price
  priceModalVisible.value = true
}

const updatePrice = async () => {
  if (!selectedPublication.value) return

  try {
    const productId = selectedPublication.value.product_id || selectedPublication.value.id

    showInfo('Modification du prix', 'Mise à jour du prix sur Vinted...', 3000)

    const response = await put<{ success: boolean; product_id: number }>(
      `/api/vinted/products/${productId}`
    )

    if (!response.success) {
      throw new Error('Échec de la mise à jour')
    }

    selectedPublication.value.price = newPrice.value

    showSuccess('Prix modifié', 'Le prix a été mis à jour sur Vinted', 3000)

    priceModalVisible.value = false
    await publicationsStore.fetchPublications()

  } catch (error: any) {
    showError('Erreur', error.message || 'Impossible de modifier le prix', 5000)
  }
}

// Initialize on mount
onMounted(async () => {
  await fetchConnectionStatus()
  if (isConnected.value) {
    await fetchStats()
  }
})
</script>
