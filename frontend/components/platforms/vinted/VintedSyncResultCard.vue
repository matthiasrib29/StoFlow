<template>
  <Card v-if="syncResult" class="shadow-sm modern-rounded border border-gray-100 mb-6">
    <template #content>
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-bold text-secondary-900">
          <i class="pi pi-code mr-2"/>
          Résultat brut de la synchronisation
        </h3>
        <div class="flex gap-2">
          <Button
            label="Copier"
            icon="pi pi-copy"
            class="bg-gray-100 hover:bg-gray-200 text-secondary-900 border-0"
            size="small"
            @click="$emit('copy')"
          />
          <Button
            label="Fermer"
            icon="pi pi-times"
            class="btn-danger"
            size="small"
            @click="$emit('close')"
          />
        </div>
      </div>

      <!-- Stats Grid -->
      <div v-if="syncResult.stats" class="grid grid-cols-5 gap-3 mb-4">
        <div class="bg-info-50 rounded-lg p-3 text-center">
          <div class="text-2xl font-bold text-info-600">{{ syncResult.stats.created || 0 }}</div>
          <div class="text-xs text-info-700">Créés</div>
        </div>
        <div class="bg-success-50 rounded-lg p-3 text-center">
          <div class="text-2xl font-bold text-success-600">{{ syncResult.stats.updated || syncResult.stats.synced || 0 }}</div>
          <div class="text-xs text-success-700">Mis à jour</div>
        </div>
        <div class="bg-primary-50 rounded-lg p-3 text-center">
          <div class="text-2xl font-bold text-primary-600">{{ syncResult.stats.enriched || 0 }}</div>
          <div class="text-xs text-primary-700">Enrichis</div>
        </div>
        <div class="bg-error-50 rounded-lg p-3 text-center">
          <div class="text-2xl font-bold text-error-600">{{ syncResult.stats.deleted || 0 }}</div>
          <div class="text-xs text-error-700">Supprimés</div>
        </div>
        <div class="bg-warning-50 rounded-lg p-3 text-center">
          <div class="text-2xl font-bold text-warning-600">{{ (syncResult.stats.errors || 0) + (syncResult.stats.enrichment_errors || 0) }}</div>
          <div class="text-xs text-warning-700">Erreurs</div>
        </div>
      </div>

      <!-- Raw JSON -->
      <div class="bg-gray-900 rounded-lg p-4 max-h-[500px] overflow-auto">
        <pre class="text-xs text-green-400 whitespace-pre-wrap break-words font-mono">{{ JSON.stringify(syncResult, null, 2) }}</pre>
      </div>
    </template>
  </Card>
</template>

<script setup lang="ts">
interface SyncStats {
  created?: number
  updated?: number
  synced?: number
  enriched?: number
  deleted?: number
  errors?: number
  enrichment_errors?: number
}

interface SyncResult {
  timestamp?: string
  stats?: SyncStats
  [key: string]: any
}

defineProps<{
  syncResult: SyncResult | null
}>()

defineEmits<{
  copy: []
  close: []
}>()
</script>
