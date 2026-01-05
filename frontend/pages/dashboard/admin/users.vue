<template>
  <div class="p-4 lg:p-8">
    <!-- Page Header -->
    <div class="mb-6 lg:mb-8">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-2">
        <div>
          <h1 class="text-2xl lg:text-3xl font-bold text-secondary-900 mb-1">Gestion des utilisateurs</h1>
          <p class="text-gray-600 text-sm lg:text-base">Administrez les comptes utilisateurs de la plateforme</p>
        </div>
        <Button
          label="Nouvel utilisateur"
          icon="pi pi-plus"
          class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-bold w-full sm:w-auto"
          @click="openCreateDialog"
        />
      </div>
    </div>

    <!-- Filters -->
    <AdminUsersFilters
      v-model:search-query="searchQuery"
      v-model:selected-role="selectedRole"
      v-model:selected-status="selectedStatus"
      @search="debouncedSearch"
      @filter="fetchUsers"
    />

    <!-- Loading State -->
    <div v-if="isLoading" class="flex items-center justify-center py-20">
      <ProgressSpinner style="width: 50px; height: 50px" />
    </div>

    <!-- Users Table -->
    <AdminUsersTable
      v-else
      :users="users"
      :total-records="total"
      :current-user-id="currentUserId"
      @create="openCreateDialog"
      @edit="openEditDialog"
      @toggle-active="handleToggleActive"
      @unlock="handleUnlock"
      @delete="confirmDelete"
    />

    <!-- Create/Edit Dialog -->
    <AdminUserDialog
      v-model:visible="showUserDialog"
      :is-editing="isEditing"
      :is-current-user="isCurrentUserEditing"
      :loading="isLoading"
      :form="userForm"
      @save="saveUser"
    />

    <!-- Delete Confirmation Dialog -->
    <ConfirmDialog />
  </div>
</template>

<script setup lang="ts">
import { useAdminUsersPage } from '~/composables/useAdminUsersPage'

definePageMeta({
  layout: 'dashboard',
  middleware: ['admin'],
})

const {
  // State
  searchQuery,
  selectedRole,
  selectedStatus,
  showUserDialog,
  isEditing,
  isCurrentUserEditing,
  userForm,
  currentUserId,

  // From useAdminUsers
  users,
  total,
  isLoading,

  // Methods
  fetchUsers,
  debouncedSearch,
  openCreateDialog,
  openEditDialog,
  saveUser,
  handleToggleActive,
  handleUnlock,
  confirmDelete,
} = useAdminUsersPage()

// Fetch users on mount
onMounted(async () => {
  await fetchUsers()
})
</script>
