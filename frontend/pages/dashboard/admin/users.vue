<template>
  <div class="p-4 lg:p-8">
    <PageHeader
      title="Gestion des utilisateurs"
      subtitle="Administrez les comptes utilisateurs de la plateforme"
    >
      <template #actions>
        <Button
          label="Nouvel utilisateur"
          icon="pi pi-plus"
          class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-bold"
          @click="openCreateDialog"
        />
      </template>
    </PageHeader>

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
