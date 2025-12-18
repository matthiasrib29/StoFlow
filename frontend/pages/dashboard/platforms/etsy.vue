<template>
  <div class="p-8">
    <!-- Page Header -->
    <div class="mb-8">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-4">
          <div class="w-16 h-16 rounded-2xl bg-white flex items-center justify-center shadow-lg border border-gray-100 p-2">
            <img src="/images/platforms/etsy-logo.png" alt="Etsy" class="w-full h-full object-contain" >
          </div>
          <div>
            <h1 class="text-3xl font-bold text-secondary-900 mb-1">Etsy</h1>
            <Badge
              :value="isConnected ? 'Connecté' : 'Déconnecté'"
              :severity="isConnected ? 'success' : 'secondary'"
            />
          </div>
        </div>
        <div class="flex gap-3">
          <Button
            label="Retour"
            icon="pi pi-arrow-left"
            class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
            @click="$router.push('/dashboard/platforms')"
          />
          <Button
            v-if="!isConnected"
            label="Connecter Etsy"
            icon="pi pi-link"
            class="bg-orange-500 hover:bg-orange-600 text-white border-0 font-semibold"
            @click="handleConnect"
          />
          <Button
            v-else
            label="Déconnecter"
            icon="pi pi-sign-out"
            class="bg-red-500 hover:bg-red-600 text-white border-0 font-semibold"
            severity="danger"
            @click="handleDisconnect"
          />
        </div>
      </div>
    </div>

    <!-- Tabs - PrimeVue v4 -->
    <Tabs v-model:value="activeTab">
      <TabList>
        <Tab value="0">Vue d'ensemble</Tab>
        <Tab value="1">Publications</Tab>
        <Tab value="2">Paramètres</Tab>
      </TabList>
      <TabPanels>
        <!-- Onglet: Vue d'ensemble -->
        <TabPanel value="0">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <!-- Stat Cards -->
          <div class="stat-card bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
            <div class="flex items-center justify-between mb-4">
              <div class="w-12 h-12 rounded-xl bg-orange-100 flex items-center justify-center">
                <i class="pi pi-send text-orange-600 text-xl"/>
              </div>
            </div>
            <h3 class="text-3xl font-bold text-secondary-900 mb-1">{{ stats.activePublications }}</h3>
            <p class="text-sm text-gray-600">Publications actives</p>
          </div>

          <div class="stat-card bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
            <div class="flex items-center justify-between mb-4">
              <div class="w-12 h-12 rounded-xl bg-primary-100 flex items-center justify-center">
                <i class="pi pi-eye text-primary-600 text-xl"/>
              </div>
            </div>
            <h3 class="text-3xl font-bold text-secondary-900 mb-1">{{ stats.totalViews }}</h3>
            <p class="text-sm text-gray-600">Vues totales</p>
          </div>

          <div class="stat-card bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
            <div class="flex items-center justify-between mb-4">
              <div class="w-12 h-12 rounded-xl bg-secondary-100 flex items-center justify-center">
                <i class="pi pi-check-circle text-secondary-700 text-xl"/>
              </div>
            </div>
            <h3 class="text-3xl font-bold text-secondary-900 mb-1">{{ stats.totalSales }}</h3>
            <p class="text-sm text-gray-600">Ventes</p>
          </div>

          <div class="stat-card bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
            <div class="flex items-center justify-between mb-4">
              <div class="w-12 h-12 rounded-xl bg-primary-100 flex items-center justify-center">
                <i class="pi pi-euro text-primary-600 text-xl"/>
              </div>
            </div>
            <h3 class="text-3xl font-bold text-secondary-900 mb-1">{{ formatCurrency(stats.totalRevenue) }}</h3>
            <p class="text-sm text-gray-600">Chiffre d'affaires</p>
          </div>
        </div>

        <!-- Infos Connexion -->
        <Card v-if="isConnected" class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <h3 class="text-lg font-bold text-secondary-900 mb-4">Informations de connexion</h3>
            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <span class="text-gray-600">Boutique connectée</span>
                <span class="font-semibold text-secondary-900">{{ connectionInfo.shopName }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-600">Date de connexion</span>
                <span class="font-semibold text-secondary-900">{{ connectionInfo.connectedAt }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-600">Dernière synchronisation</span>
                <div class="flex items-center gap-2">
                  <span class="font-semibold text-secondary-900">{{ connectionInfo.lastSync }}</span>
                  <Button
                    icon="pi pi-refresh"
                    class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0"
                    size="small"
                    rounded
                    text
                    @click="handleSync"
                  />
                </div>
              </div>
            </div>
          </template>
        </Card>

        <!-- Message si non connecté -->
        <Card v-else class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <div class="text-center py-8">
              <i class="pi pi-link text-gray-300 text-6xl mb-4"/>
              <h3 class="text-xl font-bold text-secondary-900 mb-2">Connectez votre boutique Etsy</h3>
              <p class="text-gray-600 mb-6">Commencez à vendre vos créations sur Etsy en un clic</p>
              <Button
                label="Connecter maintenant"
                icon="pi pi-link"
                class="bg-orange-500 hover:bg-orange-600 text-white border-0 font-semibold"
                @click="handleConnect"
              />
            </div>
          </template>
        </Card>
        </TabPanel>

        <!-- Onglet: Publications -->
        <TabPanel value="1">
        <DataTable
          :value="publications"
          :paginator="true"
          :rows="10"
          :loading="loading"
          class="modern-table"
          striped-rows
        >
          <template #empty>
            <div class="text-center py-8">
              <i class="pi pi-inbox text-gray-300 text-5xl mb-3"/>
              <p class="text-gray-600">Aucune publication sur Etsy pour le moment</p>
            </div>
          </template>

          <Column field="product.title" header="Produit" sortable>
            <template #body="{ data }">
              <div class="flex items-center gap-3">
                <img
                  v-if="data.product.image_url"
                  :src="data.product.image_url"
                  :alt="data.product.title"
                  class="w-12 h-12 rounded-lg object-cover"
                >
                <div v-else class="w-12 h-12 rounded-lg bg-gray-100 flex items-center justify-center">
                  <i class="pi pi-image text-gray-400"/>
                </div>
                <div>
                  <p class="font-semibold text-secondary-900">{{ data.product.title }}</p>
                  <p class="text-xs text-gray-500">ID: {{ data.product.id }}</p>
                </div>
              </div>
            </template>
          </Column>

          <Column field="price" header="Prix" sortable>
            <template #body="{ data }">
              <span class="font-bold text-secondary-900">{{ formatCurrency(data.price) }}</span>
            </template>
          </Column>

          <Column field="views" header="Vues" sortable>
            <template #body="{ data }">
              <div class="flex items-center gap-2">
                <i class="pi pi-eye text-gray-400 text-sm"/>
                <span>{{ data.views || 0 }}</span>
              </div>
            </template>
          </Column>

          <Column field="status" header="Statut" sortable>
            <template #body="{ data }">
              <Badge
                :value="getStatusLabel(data.status)"
                :severity="getStatusSeverity(data.status)"
              />
            </template>
          </Column>

          <Column field="published_at" header="Publié le" sortable>
            <template #body="{ data }">
              <span class="text-sm text-gray-600">{{ formatDate(data.published_at) }}</span>
            </template>
          </Column>

          <Column header="Actions">
            <template #body="{ data }">
              <div class="flex gap-2">
                <Button
                  v-tooltip.top="'Voir sur Etsy'"
                  icon="pi pi-external-link"
                  class="bg-gray-100 hover:bg-gray-200 text-secondary-900 border-0"
                  size="small"
                  rounded
                  text
                  @click="openPublication(data)"
                />
                <Button
                  v-tooltip.top="'Modifier le prix'"
                  icon="pi pi-euro"
                  class="bg-primary-100 hover:bg-primary-200 text-primary-700 border-0"
                  size="small"
                  rounded
                  text
                  @click="editPrice(data)"
                />
                <Button
                  v-tooltip.top="'Supprimer'"
                  icon="pi pi-trash"
                  class="bg-red-100 hover:bg-red-200 text-red-700 border-0"
                  size="small"
                  rounded
                  text
                  @click="confirmDelete(data)"
                />
              </div>
            </template>
          </Column>
        </DataTable>
        </TabPanel>

        <!-- Onglet: Paramètres -->
        <TabPanel value="2">
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <h3 class="text-lg font-bold text-secondary-900 mb-4">Paramètres Etsy</h3>

            <div class="space-y-6">
              <!-- Synchronisation automatique -->
              <div class="flex items-center justify-between">
                <div>
                  <p class="font-semibold text-secondary-900 mb-1">Synchronisation automatique</p>
                  <p class="text-sm text-gray-600">Synchroniser automatiquement les ventes et le stock</p>
                </div>
                <ToggleSwitch v-model="settings.autoSync" />
              </div>

              <!-- Notifications -->
              <div class="flex items-center justify-between">
                <div>
                  <p class="font-semibold text-secondary-900 mb-1">Notifications de vente</p>
                  <p class="text-sm text-gray-600">Recevoir un email quand un produit est vendu</p>
                </div>
                <ToggleSwitch v-model="settings.saleNotifications" />
              </div>

              <!-- Auto-renouvellement -->
              <div class="flex items-center justify-between">
                <div>
                  <p class="font-semibold text-secondary-900 mb-1">Auto-renouvellement</p>
                  <p class="text-sm text-gray-600">Renouveler automatiquement les listings qui expirent</p>
                </div>
                <ToggleSwitch v-model="settings.autoRenew" />
              </div>

              <!-- Catégorie par défaut -->
              <div>
                <label class="block font-semibold text-secondary-900 mb-2">Section par défaut</label>
                <InputText
                  v-model="settings.defaultSection"
                  placeholder="Nom de la section (optionnel)"
                  class="w-full"
                />
                <small class="text-gray-500">Les produits seront ajoutés dans cette section de votre boutique</small>
              </div>

              <Divider />

              <!-- Bouton sauvegarder -->
              <div class="flex justify-end">
                <Button
                  label="Sauvegarder les paramètres"
                  icon="pi pi-save"
                  class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
                  @click="saveSettings"
                />
              </div>
            </div>
          </template>
        </Card>
        </TabPanel>
      </TabPanels>
    </Tabs>

    <!-- Modal: Modifier le prix -->
    <Dialog
      v-model:visible="priceModalVisible"
      modal
      header="Modifier le prix"
      :style="{ width: '400px' }"
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

    <!-- Confirm Dialog -->
    <ConfirmDialog />
  </div>
</template>

<script setup lang="ts">
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'

definePageMeta({
  layout: 'dashboard'
})

// SSR-safe initialization: Only call PrimeVue hooks on client-side
const confirm = import.meta.client ? useConfirm() : null
const toast = import.meta.client ? useToast() : null
const publicationsStore = usePublicationsStore()

// State
const activeTab = ref('0')
const isConnected = ref(false)
const loading = ref(false)
const priceModalVisible = ref(false)
const selectedPublication = ref<any>(null)
const newPrice = ref(0)

// Stats (mock data)
const stats = ref({
  activePublications: 0,
  totalViews: 0,
  totalSales: 0,
  totalRevenue: 0
})

// Connection info (mock)
const connectionInfo = ref({
  shopName: 'MaBoutique',
  connectedAt: '5 déc. 2024',
  lastSync: 'Il y a 2 heures'
})

// Settings
const settings = ref({
  autoSync: true,
  saleNotifications: true,
  autoRenew: false,
  defaultSection: ''
})

// Publications (mock data)
const publications = computed(() => {
  return publicationsStore.publications
    .filter((p: any) => p.platform === 'etsy')
    .map((p: any) => ({
      ...p,
      views: Math.floor(Math.random() * 80),
      published_at: new Date().toISOString()
    }))
})

// Computed
const platformData = computed(() => {
  return publicationsStore.integrations.find((i: any) => i.platform === 'etsy')
})

// Watch platform data
watch(() => platformData.value?.is_connected, (connected) => {
  if (connected !== undefined) {
    isConnected.value = connected
  }
}, { immediate: true })

// Watch publications for stats
watch(publications, (pubs) => {
  stats.value.activePublications = pubs.filter((p: any) => p.status === 'active').length
  stats.value.totalViews = pubs.reduce((sum: number, p: any) => sum + (p.views || 0), 0)
  stats.value.totalSales = pubs.filter((p: any) => p.status === 'sold').length
  stats.value.totalRevenue = pubs
    .filter((p: any) => p.status === 'sold')
    .reduce((sum: number, p: any) => sum + p.price, 0)
}, { immediate: true })

// Methods
const handleConnect = async () => {
  try {
    loading.value = true
    await new Promise(resolve => setTimeout(resolve, 1000))
    await publicationsStore.connectIntegration('etsy')

    toast?.add({
      severity: 'success',
      summary: 'Connexion réussie',
      detail: 'Votre boutique Etsy a été connectée avec succès',
      life: 3000
    })
  } catch (error: any) {
    toast?.add({
      severity: 'error',
      summary: 'Erreur de connexion',
      detail: error.message || 'Impossible de connecter à Etsy',
      life: 5000
    })
  } finally {
    loading.value = false
  }
}

const handleDisconnect = () => {
  confirm?.require({
    message: 'Voulez-vous vraiment déconnecter votre boutique Etsy ?',
    header: 'Confirmation',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Oui, déconnecter',
    rejectLabel: 'Annuler',
    accept: async () => {
      try {
        await publicationsStore.disconnectIntegration('etsy')
        toast?.add({
          severity: 'info',
          summary: 'Déconnecté',
          detail: 'Votre boutique Etsy a été déconnectée',
          life: 3000
        })
      } catch (error) {
        toast?.add({
          severity: 'error',
          summary: 'Erreur',
          detail: 'Impossible de déconnecter la boutique',
          life: 5000
        })
      }
    }
  })
}

const handleSync = async () => {
  try {
    toast?.add({
      severity: 'info',
      summary: 'Synchronisation',
      detail: 'Synchronisation en cours...',
      life: 2000
    })

    await new Promise(resolve => setTimeout(resolve, 1500))
    connectionInfo.value.lastSync = 'À l\'instant'

    toast?.add({
      severity: 'success',
      summary: 'Synchronisé',
      detail: 'Vos données Etsy sont à jour',
      life: 3000
    })
  } catch (error) {
    toast?.add({
      severity: 'error',
      summary: 'Erreur',
      detail: 'Échec de la synchronisation',
      life: 5000
    })
  }
}

const openPublication = (publication: any) => {
  const url = `https://www.etsy.com/listing/${publication.id}`
  window.open(url, '_blank')

  toast?.add({
    severity: 'info',
    summary: 'Ouverture',
    detail: 'Ouverture de la publication sur Etsy',
    life: 2000
  })
}

const editPrice = (publication: any) => {
  selectedPublication.value = publication
  newPrice.value = publication.price
  priceModalVisible.value = true
}

const updatePrice = async () => {
  if (!selectedPublication.value) return

  try {
    selectedPublication.value.price = newPrice.value

    toast?.add({
      severity: 'success',
      summary: 'Prix modifié',
      detail: `Le prix a été mis à jour sur Etsy`,
      life: 3000
    })

    priceModalVisible.value = false
  } catch (error) {
    toast?.add({
      severity: 'error',
      summary: 'Erreur',
      detail: 'Impossible de modifier le prix',
      life: 5000
    })
  }
}

const confirmDelete = (publication: any) => {
  confirm?.require({
    message: `Voulez-vous vraiment supprimer "${publication.product.title}" de Etsy ?`,
    header: 'Confirmation de suppression',
    icon: 'pi pi-exclamation-triangle',
    acceptClass: 'p-button-danger',
    acceptLabel: 'Supprimer',
    rejectLabel: 'Annuler',
    accept: async () => {
      try {
        await new Promise(resolve => setTimeout(resolve, 500))

        toast?.add({
          severity: 'success',
          summary: 'Publication supprimée',
          detail: 'La publication a été retirée de Etsy',
          life: 3000
        })
      } catch (error) {
        toast?.add({
          severity: 'error',
          summary: 'Erreur',
          detail: 'Impossible de supprimer la publication',
          life: 5000
        })
      }
    }
  })
}

const saveSettings = () => {
  toast?.add({
    severity: 'success',
    summary: 'Paramètres sauvegardés',
    detail: 'Vos préférences ont été enregistrées',
    life: 3000
  })
}

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    active: 'Actif',
    sold: 'Vendu',
    paused: 'En pause',
    expired: 'Expiré'
  }
  return labels[status] || status
}

const getStatusSeverity = (status: string): string => {
  const severities: Record<string, string> = {
    active: 'success',
    sold: 'info',
    paused: 'warning',
    expired: 'danger'
  }
  return severities[status] || 'secondary'
}

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR'
  }).format(value)
}

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  })
}

// Load data on mount
onMounted(async () => {
  try {
    loading.value = true
    await publicationsStore.fetchPublications()
  } catch (error) {
    console.error('Erreur chargement publications:', error)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.stat-card {
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #f97316, #ea580c);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.stat-card:hover::before {
  opacity: 1;
}

.modern-table {
  border-radius: 16px;
  overflow: hidden;
}
</style>
