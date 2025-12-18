<template>
  <Card class="shadow-md">
    <template #title>
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <i class="pi pi-link text-primary-500"/>
          <span class="text-secondary-900 font-bold">Intégrations</span>
        </div>
        <NuxtLink
          to="/dashboard/settings"
          class="text-sm font-bold text-primary-600 hover:text-primary-700"
        >
          Gérer
          <i class="pi pi-arrow-right ml-1"/>
        </NuxtLink>
      </div>
    </template>
    <template #content>
      <div class="space-y-3">
        <div
          v-for="integration in integrations"
          :key="integration.platform"
          class="flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:border-primary-400 transition"
        >
          <div class="flex items-center gap-3">
            <div
:class="[
              'w-10 h-10 rounded-full flex items-center justify-center',
              getPlatformColor(integration.platform).bg
            ]">
              <i :class="[getPlatformIcon(integration.platform), 'text-lg', getPlatformColor(integration.platform).text]"/>
            </div>

            <div>
              <p class="text-sm font-bold text-secondary-900">{{ integration.name }}</p>
              <p class="text-xs text-gray-500">
                {{ integration.is_connected ? `${integration.active_publications || 0} publications actives` : 'Non connecté' }}
              </p>
            </div>
          </div>

          <div class="flex items-center gap-2">
            <Badge
              :value="integration.is_connected ? 'Connecté' : 'Déconnecté'"
              :severity="integration.is_connected ? 'success' : 'secondary'"
            />
          </div>
        </div>
      </div>

      <UiInfoBox v-if="connectedCount === 0" class="mt-4" type="info" icon="pi pi-info-circle">
        Connectez vos comptes pour publier vos produits automatiquement sur plusieurs plateformes.
      </UiInfoBox>
    </template>
  </Card>
</template>

<script setup lang="ts">
const publicationsStore = usePublicationsStore()
const { getPlatformIcon, getPlatformColor } = usePlatform()

const integrations = computed(() => publicationsStore.integrations)
const connectedCount = computed(() => publicationsStore.connectedIntegrations.length)
</script>
