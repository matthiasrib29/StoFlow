<template>
  <!-- Connected state -->
  <Card v-if="isConnected" class="shadow-sm modern-rounded border border-gray-100 mb-6">
    <template #content>
      <h3 class="text-lg font-bold text-secondary-900 mb-4">Informations de connexion</h3>
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <span class="text-gray-600">User ID</span>
          <span class="font-semibold text-secondary-900">{{ connectionInfo.userId || '-' }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-gray-600">Username</span>
          <span class="font-semibold text-secondary-900">{{ connectionInfo.username || '-' }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-gray-600">Dernière synchronisation</span>
          <span class="font-semibold text-secondary-900">{{ connectionInfo.lastSync || '-' }}</span>
        </div>
      </div>

      <!-- Sync Button -->
      <div class="mt-6 pt-4 border-t border-gray-200">
        <Button
          label="Synchroniser les produits Vinted"
          icon="pi pi-sync"
          class="w-full btn-primary"
          :loading="syncLoading"
          :disabled="syncLoading"
          @click="$emit('sync')"
        />
        <p class="text-xs text-gray-500 mt-2 text-center">
          Récupère tous vos produits depuis votre garde-robe Vinted
        </p>
      </div>
    </template>
  </Card>

  <!-- Not connected state -->
  <Card v-else class="shadow-sm modern-rounded border border-gray-100">
    <template #content>
      <div class="text-center py-8">
        <i class="pi pi-link text-gray-300 text-6xl mb-4"/>
        <h3 class="text-xl font-bold text-secondary-900 mb-2">Connectez votre compte Vinted</h3>
        <p class="text-gray-600 mb-6">Commencez à publier vos produits sur Vinted en un clic</p>
        <Button
          label="Connecter maintenant"
          icon="pi pi-link"
          class="btn-primary"
          :loading="loading"
          @click="$emit('connect')"
        />
      </div>
    </template>
  </Card>
</template>

<script setup lang="ts">
interface ConnectionInfo {
  userId: number | null
  username: string | null
  lastSync: string | null
}

defineProps<{
  isConnected: boolean
  connectionInfo: ConnectionInfo
  syncLoading: boolean
  loading: boolean
}>()

defineEmits<{
  sync: []
  connect: []
}>()
</script>
