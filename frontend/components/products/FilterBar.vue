<template>
  <Card class="filter-bar shadow-sm mb-6 border border-gray-100">
    <template #content>
      <div class="flex flex-col md:flex-row gap-4 items-stretch">
        <!-- Search -->
        <div class="flex-1 min-w-0">
          <div class="relative h-[42px]">
            <i class="pi pi-search absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 z-10"></i>
            <InputText
              :model-value="search"
              @update:model-value="$emit('update:search', $event)"
              placeholder="Rechercher..."
              class="search-input w-full h-full"
            />
          </div>
        </div>

        <!-- Category Filter -->
        <div class="w-full md:w-40">
          <Select
            :model-value="category"
            @update:model-value="$emit('update:category', $event)"
            :options="categoryOptions"
            placeholder="Catégorie"
            class="w-full h-[42px]"
            showClear
          />
        </div>

        <!-- Status Filter -->
        <div class="w-full md:w-32">
          <Select
            :model-value="status"
            @update:model-value="$emit('update:status', $event)"
            :options="statusOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Statut"
            class="w-full h-[42px]"
            showClear
          />
        </div>

        <!-- View Toggle -->
        <div v-if="showViewToggle" class="view-toggle flex items-center gap-1 shrink-0">
          <button
            type="button"
            :class="['view-btn', view === 'table' ? 'active' : '']"
            @click="$emit('update:view', 'table')"
          >
            <i class="pi pi-list"></i>
          </button>
          <button
            type="button"
            :class="['view-btn', view === 'grid' ? 'active' : '']"
            @click="$emit('update:view', 'grid')"
          >
            <i class="pi pi-th-large"></i>
          </button>
        </div>
      </div>

      <!-- Selection Actions -->
      <div v-if="selectedCount > 0" class="mt-4 pt-4 border-t border-gray-100">
        <div class="flex items-center gap-3 flex-wrap">
          <span class="text-sm font-semibold text-secondary-900 bg-primary-100 px-3 py-1.5 rounded-full">
            {{ selectedCount }} sélectionné{{ selectedCount > 1 ? 's' : '' }}
          </span>
          <div class="flex gap-2">
            <Button
              label="Activer"
              icon="pi pi-check"
              class="bg-green-500 hover:bg-green-600 text-white border-0 font-medium"
              size="small"
              @click="$emit('bulk-activate')"
            />
            <Button
              label="Désactiver"
              icon="pi pi-ban"
              class="bg-orange-500 hover:bg-orange-600 text-white border-0 font-medium"
              size="small"
              @click="$emit('bulk-deactivate')"
            />
            <Button
              label="Supprimer"
              icon="pi pi-trash"
              class="bg-red-500 hover:bg-red-600 text-white border-0 font-medium"
              size="small"
              @click="$emit('bulk-delete')"
            />
          </div>
        </div>
      </div>
    </template>
  </Card>
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

defineEmits<{
  'update:search': [value: string]
  'update:category': [value: string | null]
  'update:status': [value: string | null]
  'update:view': [value: 'table' | 'grid']
  'bulk-activate': []
  'bulk-deactivate': []
  'bulk-delete': []
}>()

const categoryOptions = [
  'Vêtements',
  'Chaussures',
  'Accessoires',
  'Maroquinerie',
  'Bijoux',
  'Autre'
]

const statusOptions = [
  { label: 'Actif', value: 'active' },
  { label: 'Inactif', value: 'inactive' }
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

/* Fix Card padding */
:deep(.filter-bar .p-card-body) {
  padding: 1rem;
}

:deep(.filter-bar .p-card-content) {
  padding: 0;
}
</style>
