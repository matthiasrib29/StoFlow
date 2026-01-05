<template>
  <div class="bg-white rounded-xl border border-gray-200 p-4 mb-6">
    <div class="flex flex-col md:flex-row gap-4">
      <!-- Search -->
      <div class="flex-1">
        <InputText
          :model-value="searchQuery"
          placeholder="Rechercher par email, nom..."
          class="w-full"
          @update:model-value="$emit('update:searchQuery', $event)"
          @input="$emit('search')"
        />
      </div>

      <!-- Role Filter -->
      <div class="w-full md:w-48">
        <Dropdown
          :model-value="selectedRole"
          :options="roleOptions"
          option-label="label"
          option-value="value"
          placeholder="Tous les rôles"
          class="w-full"
          show-clear
          @update:model-value="val => { $emit('update:selectedRole', val); $emit('filter') }"
        />
      </div>

      <!-- Status Filter -->
      <div class="w-full md:w-48">
        <Dropdown
          :model-value="selectedStatus"
          :options="statusOptions"
          option-label="label"
          option-value="value"
          placeholder="Tous les statuts"
          class="w-full"
          show-clear
          @update:model-value="val => { $emit('update:selectedStatus', val); $emit('filter') }"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  searchQuery: string
  selectedRole: string | null
  selectedStatus: boolean | null
}>()

defineEmits<{
  'update:searchQuery': [value: string]
  'update:selectedRole': [value: string | null]
  'update:selectedStatus': [value: boolean | null]
  'search': []
  'filter': []
}>()

const roleOptions = [
  { label: 'Admin', value: 'admin' },
  { label: 'Utilisateur', value: 'user' },
  { label: 'Support', value: 'support' },
]

const statusOptions = [
  { label: 'Actif', value: true },
  { label: 'Inactif', value: false },
]
</script>
