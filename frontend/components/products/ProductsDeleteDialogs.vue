<template>
  <!-- Single Archive Dialog -->
  <Dialog
    :visible="deleteDialogVisible"
    :style="{ width: '450px' }"
    header="Archiver le produit"
    :modal="true"
    @update:visible="$emit('update:deleteDialogVisible', $event)"
  >
    <div class="flex items-center gap-4">
      <div class="w-14 h-14 rounded-full bg-gray-100 flex items-center justify-center shrink-0">
        <i class="pi pi-inbox text-2xl text-gray-500"/>
      </div>
      <div>
        <p class="text-secondary-900">
          Archiver <strong>{{ productToDelete?.title }}</strong> ?
        </p>
        <p class="text-sm text-gray-500 mt-2">
          Le produit sera déplacé dans les archives et retiré de la vente.
        </p>
        <p class="text-sm text-primary-600 mt-1 flex items-center gap-1">
          <i class="pi pi-replay text-xs"/>
          Vous pourrez le restaurer à tout moment.
        </p>
      </div>
    </div>
    <template #footer>
      <Button
        label="Annuler"
        icon="pi pi-times"
        class="bg-gray-100 hover:bg-gray-200 text-secondary-900 border-0"
        @click="$emit('update:deleteDialogVisible', false)"
      />
      <Button
        label="Archiver"
        icon="pi pi-inbox"
        class="bg-gray-600 hover:bg-gray-700 text-white border-0"
        :loading="loading"
        @click="$emit('delete')"
      />
    </template>
  </Dialog>

  <!-- Bulk Archive Dialog -->
  <Dialog
    :visible="bulkDeleteDialogVisible"
    :style="{ width: '450px' }"
    header="Archiver les produits"
    :modal="true"
    @update:visible="$emit('update:bulkDeleteDialogVisible', $event)"
  >
    <div class="flex items-center gap-4">
      <div class="w-14 h-14 rounded-full bg-gray-100 flex items-center justify-center shrink-0">
        <i class="pi pi-inbox text-2xl text-gray-500"/>
      </div>
      <div>
        <p class="text-secondary-900">
          Archiver <strong>{{ selectedCount }} produit(s)</strong> ?
        </p>
        <p class="text-sm text-gray-500 mt-2">
          Les produits seront déplacés dans les archives et retirés de la vente.
        </p>
        <p class="text-sm text-primary-600 mt-1 flex items-center gap-1">
          <i class="pi pi-replay text-xs"/>
          Vous pourrez les restaurer à tout moment.
        </p>
      </div>
    </div>
    <template #footer>
      <Button
        label="Annuler"
        icon="pi pi-times"
        class="bg-gray-100 hover:bg-gray-200 text-secondary-900 border-0"
        @click="$emit('update:bulkDeleteDialogVisible', false)"
      />
      <Button
        label="Archiver tout"
        icon="pi pi-inbox"
        class="bg-gray-600 hover:bg-gray-700 text-white border-0"
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
