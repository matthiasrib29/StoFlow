<template>
  <PlatformOrdersPage
    platform="etsy"
    :is-connected="isConnected"
    :loading="false"
    :error="null"
    :is-empty="true"
    empty-message="Fonctionnalité à venir"
    back-to="/dashboard/platforms"
  >
    <!-- Header Actions -->
    <template #header-actions>
      <Button
        label="Synchroniser"
        icon="pi pi-refresh"
        disabled
        class="bg-platform-etsy hover:bg-orange-600 text-white border-0 opacity-50"
        title="Fonctionnalité à venir"
      />
    </template>

    <!-- Stats Cards -->
    <template #stats>
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-500 mb-1">Total commandes</p>
                <p class="text-2xl font-bold text-gray-400">0</p>
              </div>
              <i class="pi pi-shopping-bag text-3xl text-gray-300"/>
            </div>
          </template>
        </Card>

        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-500 mb-1">Revenus</p>
                <p class="text-2xl font-bold text-gray-400">0,00 €</p>
              </div>
              <i class="pi pi-dollar text-3xl text-gray-300"/>
            </div>
          </template>
        </Card>

        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-500 mb-1">À expédier</p>
                <p class="text-2xl font-bold text-gray-400">0</p>
              </div>
              <i class="pi pi-box text-3xl text-gray-300"/>
            </div>
          </template>
        </Card>

        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-500 mb-1">Expédiées</p>
                <p class="text-2xl font-bold text-gray-400">0</p>
              </div>
              <i class="pi pi-send text-3xl text-gray-300"/>
            </div>
          </template>
        </Card>
      </div>
    </template>

    <!-- Toolbar (disabled) -->
    <template #toolbar>
      <div class="flex flex-col md:flex-row gap-4 opacity-50">
        <div class="flex-1">
          <IconField>
            <InputIcon class="pi pi-search" />
            <InputText
              placeholder="Rechercher..."
              class="w-full"
              disabled
            />
          </IconField>
        </div>
        <Dropdown
          placeholder="Tous les statuts"
          class="w-full md:w-48"
          disabled
        />
      </div>
    </template>

    <!-- Empty State Content -->
    <template #content>
      <div class="text-center py-12">
        <i class="pi pi-clock text-6xl text-gray-300 mb-6"/>
        <h3 class="text-2xl font-bold text-secondary-900 mb-3">Fonctionnalité à venir</h3>
        <p class="text-gray-500 mb-2">La gestion des commandes Etsy sera disponible prochainement.</p>
        <p class="text-sm text-gray-400">Le backend pour Etsy est en cours de développement.</p>
      </div>
    </template>

    <!-- Empty Actions -->
    <template #empty-actions>
      <div class="mt-6">
        <Button
          label="Retour aux plateformes"
          icon="pi pi-arrow-left"
          text
          class="text-gray-500"
          @click="$router.push('/dashboard/platforms')"
        />
      </div>
    </template>
  </PlatformOrdersPage>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'dashboard'
})

// Platform connection
const { isConnected, fetchStatus } = usePlatformConnection('etsy')

// Lifecycle
onMounted(async () => {
  await fetchStatus()
})
</script>
