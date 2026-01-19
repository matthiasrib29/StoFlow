<template>
  <div class="filter-bar mb-6">
    <div class="flex flex-col md:flex-row gap-4 items-stretch">
      <!-- Search -->
      <div class="flex-1 min-w-0">
        <div class="relative h-[42px]">
          <i class="pi pi-search absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 z-10"/>
          <InputText
            :model-value="search"
            placeholder="Rechercher..."
            class="search-input w-full h-full"
            @update:model-value="onSearchUpdate($event as string)"
          />
        </div>
      </div>

      <!-- Category Filter (Hierarchical) -->
      <div class="w-full md:w-48">
        <ProductsFilterCategorySelect
          :model-value="category"
          @update:model-value="onCategoryUpdate($event)"
        />
      </div>

      <!-- Status Filter -->
      <div class="w-full md:w-36">
        <Select
          :model-value="status ?? 'all'"
          :options="statusOptions"
          option-label="label"
          option-value="value"
          class="w-full h-[42px]"
          @update:model-value="onStatusUpdate($event === 'all' ? null : $event)"
        />
      </div>

      <!-- View Toggle -->
      <div v-if="showViewToggle" class="view-toggle flex items-center gap-1 shrink-0">
        <button
          type="button"
          :class="['view-btn', view === 'table' ? 'active' : '']"
          @click="onViewUpdate('table')"
        >
          <i class="pi pi-list"/>
        </button>
        <button
          type="button"
          :class="['view-btn', view === 'grid' ? 'active' : '']"
          @click="onViewUpdate('grid')"
        >
          <i class="pi pi-th-large"/>
        </button>
      </div>
    </div>

    <!-- Selection Actions -->
    <div v-if="selectedCount > 0" class="mt-4 pt-4 border-t border-gray-200">
      <div class="flex items-center gap-3 flex-wrap">
        <span class="text-sm font-semibold text-secondary-900 bg-primary-100 px-3 py-1.5 rounded-full">
          {{ selectedCount }} sélectionné{{ selectedCount > 1 ? 's' : '' }}
        </span>
        <div class="flex gap-2 items-center">
          <span class="text-sm text-gray-500">Changer en :</span>
          <Button
            label="Brouillon"
            icon="pi pi-file"
            class="bg-gray-100 hover:bg-gray-200 text-gray-700 border-0 font-medium rounded-lg"
            size="small"
            @click="onBulkStatusChange('draft')"
          />
          <Button
            label="Publié"
            icon="pi pi-check-circle"
            class="btn-success-solid"
            size="small"
            @click="onBulkStatusChange('published')"
          />
          <Button
            label="Vendu"
            icon="pi pi-tag"
            class="bg-primary-500 hover:bg-primary-600 text-white border-0 font-medium rounded-lg"
            size="small"
            @click="onBulkStatusChange('sold')"
          />
          <Button
            label="Archiver"
            icon="pi pi-inbox"
            class="bg-gray-500 hover:bg-gray-600 text-white border-0 font-medium rounded-lg"
            size="small"
            @click="onBulkStatusChange('archived')"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  search?: string
  category?: string | null
  status?: string | null
  view?: 'table' | 'grid'
  selectedCount?: number
  showViewToggle?: boolean
}

withDefaults(defineProps<Props>(), {
  search: '',
  category: null,
  status: null,
  view: 'table',
  selectedCount: 0,
  showViewToggle: true
})

const emit = defineEmits<{
  'update:search': [value: string]
  'update:category': [value: string | null]
  'update:status': [value: string | null]
  'update:view': [value: 'table' | 'grid']
  'bulk-status-change': [status: 'draft' | 'published' | 'sold' | 'archived']
}>()

// Handlers for template
const onSearchUpdate = (value: string) => emit('update:search', value)
const onCategoryUpdate = (value: string | null) => emit('update:category', value)
const onStatusUpdate = (value: string | null) => emit('update:status', value)
const onViewUpdate = (value: 'table' | 'grid') => emit('update:view', value)
const onBulkStatusChange = (status: 'draft' | 'published' | 'sold' | 'archived') => emit('bulk-status-change', status)

const statusOptions = [
  { label: 'Tous les statuts', value: 'all' },
  { label: 'Brouillon', value: 'draft' },
  { label: 'Publié', value: 'published' },
  { label: 'Vendu', value: 'sold' },
  { label: 'Archivé', value: 'archived' }
]
</script>

<style scoped>
/* Search input with icon */
.search-input {
  padding-left: 2.75rem !important;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  font-size: 0.875rem;
}

.search-input:focus {
  border-color: #facc15;
  outline: none;
  box-shadow: 0 0 0 2px rgba(250, 204, 21, 0.2);
}

/* View toggle buttons - no background */
.view-toggle {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 4px;
  background: white;
}

.view-btn {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.375rem;
  border: none;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  transition: all 0.15s ease;
}

.view-btn:hover {
  color: #1f2937;
  background: #f3f4f6;
}

.view-btn.active {
  background: #facc15;
  color: #1f2937;
}

/* Fix Select component height */
:deep(.p-select) {
  height: 42px;
  border-radius: 0.5rem;
  border-color: #e5e7eb;
}

:deep(.p-select:hover) {
  border-color: #d1d5db;
}

:deep(.p-select.p-focus) {
  border-color: #facc15;
  box-shadow: 0 0 0 2px rgba(250, 204, 21, 0.2);
}

:deep(.p-select .p-select-label) {
  padding: 0.625rem 0.75rem;
  font-size: 0.875rem;
}
</style>
