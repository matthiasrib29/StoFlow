<template>
  <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
    <DataTable
      :value="users"
      :paginator="true"
      :rows="10"
      :rows-per-page-options="[5, 10, 20, 50]"
      :total-records="totalRecords"
      paginator-template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
      current-page-report-template="{first}-{last} sur {totalRecords}"
      class="users-table"
      responsive-layout="scroll"
    >
      <template #empty>
        <div class="text-center py-16">
          <div class="w-20 h-20 rounded-full bg-gray-50 flex items-center justify-center mx-auto mb-4">
            <i class="pi pi-users text-4xl text-gray-300"/>
          </div>
          <p class="text-secondary-900 font-semibold text-lg mb-1">Aucun utilisateur</p>
          <p class="text-gray-400 text-sm mb-6">Commencez par créer un utilisateur</p>
          <Button
            label="Nouvel utilisateur"
            icon="pi pi-plus"
            class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
            @click="$emit('create')"
          />
        </div>
      </template>

      <!-- Email & Name -->
      <Column field="email" header="Utilisateur" sortable style="min-width: 280px">
        <template #body="{ data }">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
              <i class="pi pi-user text-primary-600"/>
            </div>
            <div>
              <p class="font-semibold text-secondary-900">{{ data.full_name }}</p>
              <p class="text-xs text-gray-500">{{ data.email }}</p>
            </div>
          </div>
        </template>
      </Column>

      <!-- Role -->
      <Column field="role" header="Rôle" sortable style="width: 120px">
        <template #body="{ data }">
          <Tag
            :value="getRoleLabel(data.role)"
            :severity="getRoleSeverity(data.role)"
          />
        </template>
      </Column>

      <!-- Status -->
      <Column field="is_active" header="Statut" sortable style="width: 100px">
        <template #body="{ data }">
          <span
            class="inline-flex items-center gap-1.5 text-xs font-medium"
            :class="data.is_active ? 'text-green-600' : 'text-red-500'"
          >
            <span
              class="w-2 h-2 rounded-full"
              :class="data.is_active ? 'bg-green-500' : 'bg-red-500'"
            />
            {{ data.is_active ? 'Actif' : 'Inactif' }}
          </span>
        </template>
      </Column>

      <!-- Subscription -->
      <Column field="subscription_tier" header="Abonnement" sortable style="width: 120px">
        <template #body="{ data }">
          <span class="text-sm text-gray-600 capitalize">{{ data.subscription_tier }}</span>
        </template>
      </Column>

      <!-- Products Count -->
      <Column field="current_products_count" header="Produits" sortable style="width: 90px">
        <template #body="{ data }">
          <span class="text-sm font-medium text-gray-700">{{ data.current_products_count }}</span>
        </template>
      </Column>

      <!-- Last Login -->
      <Column field="last_login" header="Dernière connexion" sortable style="width: 150px">
        <template #body="{ data }">
          <span class="text-sm text-gray-500">
            {{ data.last_login ? formatDateTime(data.last_login) : 'Jamais' }}
          </span>
        </template>
      </Column>

      <!-- Locked -->
      <Column header="" style="width: 40px">
        <template #body="{ data }">
          <i
            v-if="data.locked_until"
            class="pi pi-lock text-red-500"
            title="Compte verrouillé"
          />
        </template>
      </Column>

      <!-- Actions -->
      <Column header="" style="width: 120px">
        <template #body="{ data }">
          <div class="flex gap-1 justify-end">
            <!-- Edit -->
            <button
              class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-primary-600 hover:bg-primary-50 transition-colors"
              title="Modifier"
              @click="$emit('edit', data)"
            >
              <i class="pi pi-pencil text-sm"/>
            </button>

            <!-- Toggle Active -->
            <button
              v-if="!isCurrentUser(data.id)"
              class="w-8 h-8 rounded-lg flex items-center justify-center transition-colors"
              :class="data.is_active
                ? 'text-gray-400 hover:text-orange-500 hover:bg-orange-50'
                : 'text-gray-400 hover:text-green-500 hover:bg-green-50'"
              :title="data.is_active ? 'Désactiver' : 'Activer'"
              @click="$emit('toggle-active', data)"
            >
              <i :class="data.is_active ? 'pi pi-ban' : 'pi pi-check'" class="text-sm"/>
            </button>

            <!-- Unlock -->
            <button
              v-if="data.locked_until"
              class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-blue-500 hover:bg-blue-50 transition-colors"
              title="Déverrouiller"
              @click="$emit('unlock', data)"
            >
              <i class="pi pi-unlock text-sm"/>
            </button>

            <!-- Delete -->
            <button
              v-if="!isCurrentUser(data.id)"
              class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
              title="Supprimer"
              @click="$emit('delete', data)"
            >
              <i class="pi pi-trash text-sm"/>
            </button>
          </div>
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import type { AdminUser } from '~/composables/useAdminUsers'
import { formatDateTime } from '~/utils/formatters'

const props = defineProps<{
  users: AdminUser[]
  totalRecords: number
  currentUserId: number | null
}>()

defineEmits<{
  create: []
  edit: [user: AdminUser]
  'toggle-active': [user: AdminUser]
  unlock: [user: AdminUser]
  delete: [user: AdminUser]
}>()

const isCurrentUser = (userId: number) => {
  return props.currentUserId === userId
}

const getRoleLabel = (role: string) => {
  const labels: Record<string, string> = {
    admin: 'Admin',
    user: 'Utilisateur',
    support: 'Support',
  }
  return labels[role] || role
}

const getRoleSeverity = (role: string) => {
  const severities: Record<string, string> = {
    admin: 'danger',
    user: 'info',
    support: 'warning',
  }
  return severities[role] || 'info'
}
</script>

<style scoped>
.users-table :deep(.p-datatable-header) {
  background: transparent;
  border: none;
}

.users-table :deep(.p-datatable-thead > tr > th) {
  background: #f9fafb;
  color: #6b7280;
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #e5e7eb;
}

.users-table :deep(.p-datatable-tbody > tr > td) {
  border-bottom: 1px solid #f3f4f6;
}

.users-table :deep(.p-datatable-tbody > tr:hover) {
  background: #fafafa;
}
</style>
