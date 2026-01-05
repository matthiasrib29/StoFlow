<template>
  <!-- Single Delete Dialog -->
  <Dialog
    :visible="deleteDialogVisible"
    :style="{ width: '450px' }"
    header="Confirmer la suppression"
    :modal="true"
    @update:visible="$emit('update:deleteDialogVisible', $event)"
  >
    <div class="flex items-center gap-4">
      <i class="pi pi-exclamation-triangle text-5xl text-secondary-500"/>
      <div>
        <p class="text-secondary-900">
          Êtes-vous sûr de vouloir supprimer
          <strong>{{ productToDelete?.title }}</strong> ?
        </p>
        <p class="text-sm text-secondary-600 mt-2">Cette action est irréversible.</p>
      </div>
    </div>
    <template #footer>
      <Button
        label="Annuler"
        icon="pi pi-times"
        class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
        @click="$emit('update:deleteDialogVisible', false)"
      />
      <Button
        label="Supprimer"
        icon="pi pi-trash"
        class="bg-secondary-500 hover:bg-secondary-600 text-white border-0"
        :loading="loading"
        @click="$emit('delete')"
      />
    </template>
  </Dialog>

  <!-- Bulk Delete Dialog -->
  <Dialog
    :visible="bulkDeleteDialogVisible"
    :style="{ width: '450px' }"
    header="Confirmer la suppression multiple"
    :modal="true"
    @update:visible="$emit('update:bulkDeleteDialogVisible', $event)"
  >
    <div class="flex items-center gap-4">
      <i class="pi pi-exclamation-triangle text-5xl text-secondary-500"/>
      <div>
        <p class="text-secondary-900">
          Êtes-vous sûr de vouloir supprimer
          <strong>{{ selectedCount }} produit(s)</strong> ?
        </p>
        <p class="text-sm text-secondary-600 mt-2">Cette action est irréversible.</p>
      </div>
    </div>
    <template #footer>
      <Button
        label="Annuler"
        icon="pi pi-times"
        class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
        @click="$emit('update:bulkDeleteDialogVisible', false)"
      />
      <Button
        label="Supprimer tout"
        icon="pi pi-trash"
        class="bg-secondary-500 hover:bg-secondary-600 text-white border-0"
        :loading="loading"
        @click="$emit('bulk-delete')"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import type { Product } from '~/stores/products'

defineProps<{
  deleteDialogVisible: boolean
  bulkDeleteDialogVisible: boolean
  productToDelete: Product | null
  selectedCount: number
  loading: boolean
}>()

defineEmits<{
  'update:deleteDialogVisible': [value: boolean]
  'update:bulkDeleteDialogVisible': [value: boolean]
  delete: []
  'bulk-delete': []
}>()
</script>
