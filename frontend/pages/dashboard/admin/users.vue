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
    <div class="bg-white rounded-xl border border-gray-200 p-4 mb-6">
      <div class="flex flex-col md:flex-row gap-4">
        <!-- Search -->
        <div class="flex-1">
          <InputText
            v-model="searchQuery"
            placeholder="Rechercher par email, nom..."
            class="w-full"
            @input="debouncedSearch"
          />
        </div>

        <!-- Role Filter -->
        <div class="w-full md:w-48">
          <Dropdown
            v-model="selectedRole"
            :options="roleOptions"
            option-label="label"
            option-value="value"
            placeholder="Tous les rôles"
            class="w-full"
            show-clear
            @change="fetchUsers"
          />
        </div>

        <!-- Status Filter -->
        <div class="w-full md:w-48">
          <Dropdown
            v-model="selectedStatus"
            :options="statusOptions"
            option-label="label"
            option-value="value"
            placeholder="Tous les statuts"
            class="w-full"
            show-clear
            @change="fetchUsers"
          />
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="adminUsers.isLoading.value" class="flex items-center justify-center py-20">
      <ProgressSpinner style="width: 50px; height: 50px" />
    </div>

    <!-- Users Table -->
    <div v-else class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <DataTable
        :value="adminUsers.users.value"
        :paginator="true"
        :rows="10"
        :rows-per-page-options="[5, 10, 20, 50]"
        :total-records="adminUsers.total.value"
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
              @click="openCreateDialog"
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
              {{ data.last_login ? formatDate(data.last_login) : 'Jamais' }}
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
                @click="openEditDialog(data)"
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
                @click="handleToggleActive(data)"
              >
                <i :class="data.is_active ? 'pi pi-ban' : 'pi pi-check'" class="text-sm"/>
              </button>

              <!-- Unlock -->
              <button
                v-if="data.locked_until"
                class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-blue-500 hover:bg-blue-50 transition-colors"
                title="Déverrouiller"
                @click="handleUnlock(data)"
              >
                <i class="pi pi-unlock text-sm"/>
              </button>

              <!-- Delete -->
              <button
                v-if="!isCurrentUser(data.id)"
                class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
                title="Supprimer"
                @click="confirmDelete(data)"
              >
                <i class="pi pi-trash text-sm"/>
              </button>
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Create/Edit Dialog -->
    <Dialog
      v-model:visible="showUserDialog"
      :header="isEditing ? 'Modifier l\'utilisateur' : 'Nouvel utilisateur'"
      :style="{ width: '500px' }"
      :modal="true"
      class="p-fluid"
    >
      <div class="space-y-4 py-4">
        <!-- Email -->
        <div class="field">
          <label for="email" class="font-medium text-sm text-gray-700 mb-1 block">Email *</label>
          <InputText
            id="email"
            v-model="userForm.email"
            type="email"
            :class="{ 'p-invalid': submitted && !userForm.email }"
            placeholder="utilisateur@exemple.com"
          />
          <small v-if="submitted && !userForm.email" class="p-error">L'email est requis</small>
        </div>

        <!-- Full Name -->
        <div class="field">
          <label for="fullName" class="font-medium text-sm text-gray-700 mb-1 block">Nom complet *</label>
          <InputText
            id="fullName"
            v-model="userForm.full_name"
            :class="{ 'p-invalid': submitted && !userForm.full_name }"
            placeholder="Jean Dupont"
          />
          <small v-if="submitted && !userForm.full_name" class="p-error">Le nom est requis</small>
        </div>

        <!-- Password (only for create or if changing) -->
        <div class="field">
          <label for="password" class="font-medium text-sm text-gray-700 mb-1 block">
            {{ isEditing ? 'Nouveau mot de passe (laisser vide pour ne pas changer)' : 'Mot de passe *' }}
          </label>
          <Password
            id="password"
            v-model="userForm.password"
            :class="{ 'p-invalid': submitted && !isEditing && !userForm.password }"
            :feedback="false"
            toggle-mask
            placeholder="********"
          />
          <small v-if="submitted && !isEditing && !userForm.password" class="p-error">Le mot de passe est requis</small>
        </div>

        <!-- Role -->
        <div class="field">
          <label for="role" class="font-medium text-sm text-gray-700 mb-1 block">Rôle *</label>
          <Dropdown
            id="role"
            v-model="userForm.role"
            :options="roleOptionsForm"
            option-label="label"
            option-value="value"
            placeholder="Sélectionner un rôle"
            :disabled="isEditing && isCurrentUser(editingUserId)"
          />
        </div>

        <!-- Subscription Tier -->
        <div class="field">
          <label for="tier" class="font-medium text-sm text-gray-700 mb-1 block">Abonnement</label>
          <Dropdown
            id="tier"
            v-model="userForm.subscription_tier"
            :options="tierOptions"
            option-label="label"
            option-value="value"
            placeholder="Sélectionner un abonnement"
          />
        </div>

        <!-- Business Name -->
        <div class="field">
          <label for="businessName" class="font-medium text-sm text-gray-700 mb-1 block">Nom de l'entreprise</label>
          <InputText
            id="businessName"
            v-model="userForm.business_name"
            placeholder="Ma Boutique"
          />
        </div>

        <!-- Is Active -->
        <div class="field flex items-center gap-3">
          <Checkbox
            id="isActive"
            v-model="userForm.is_active"
            :binary="true"
            :disabled="isEditing && isCurrentUser(editingUserId)"
          />
          <label for="isActive" class="font-medium text-sm text-gray-700">Compte actif</label>
        </div>
      </div>

      <template #footer>
        <Button
          label="Annuler"
          icon="pi pi-times"
          class="p-button-text"
          @click="showUserDialog = false"
        />
        <Button
          :label="isEditing ? 'Enregistrer' : 'Créer'"
          icon="pi pi-check"
          class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0"
          :loading="adminUsers.isLoading.value"
          @click="saveUser"
        />
      </template>
    </Dialog>

    <!-- Delete Confirmation Dialog -->
    <ConfirmDialog />
  </div>
</template>

<script setup lang="ts">
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { useAdminUsers, type AdminUser } from '~/composables/useAdminUsers'

// Page meta
definePageMeta({
  layout: 'dashboard',
  middleware: ['admin'],
})

// Composables
const authStore = useAuthStore()
const adminUsers = useAdminUsers()
// SSR-safe: useConfirm and useToast require client-side services
const confirm = import.meta.client ? useConfirm() : null
const toast = import.meta.client ? useToast() : null

// State
const searchQuery = ref('')
const selectedRole = ref<string | null>(null)
const selectedStatus = ref<boolean | null>(null)
const showUserDialog = ref(false)
const isEditing = ref(false)
const editingUserId = ref<number | null>(null)
const submitted = ref(false)

// Form
const userForm = ref({
  email: '',
  full_name: '',
  password: '',
  role: 'user',
  subscription_tier: 'free',
  business_name: '',
  is_active: true,
})

// Options
const roleOptions = [
  { label: 'Admin', value: 'admin' },
  { label: 'Utilisateur', value: 'user' },
  { label: 'Support', value: 'support' },
]

const roleOptionsForm = roleOptions

const statusOptions = [
  { label: 'Actif', value: true },
  { label: 'Inactif', value: false },
]

const tierOptions = [
  { label: 'Free', value: 'free' },
  { label: 'Starter', value: 'starter' },
  { label: 'Pro', value: 'pro' },
  { label: 'Enterprise', value: 'enterprise' },
]

// Fetch users once on page load (client-side only, requires auth token)
if (import.meta.client) {
  await callOnce(async () => {
    await adminUsers.fetchUsers()
  })
}

// Methods
const fetchUsers = async () => {
  try {
    await adminUsers.fetchUsers({
      search: searchQuery.value || undefined,
      role: selectedRole.value || undefined,
      is_active: selectedStatus.value ?? undefined,
    })
  } catch (e: any) {
    toast?.add({
      severity: 'error',
      summary: 'Erreur',
      detail: e.message || 'Impossible de charger les utilisateurs',
      life: 5000,
    })
  }
}

// Debounced search
let searchTimeout: ReturnType<typeof setTimeout> | null = null
const debouncedSearch = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    fetchUsers()
  }, 300)
}

const isCurrentUser = (userId: number | null) => {
  if (userId === null) return false
  return authStore.user?.id === userId
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

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// Dialog methods
const openCreateDialog = () => {
  isEditing.value = false
  editingUserId.value = null
  submitted.value = false
  userForm.value = {
    email: '',
    full_name: '',
    password: '',
    role: 'user',
    subscription_tier: 'free',
    business_name: '',
    is_active: true,
  }
  showUserDialog.value = true
}

const openEditDialog = (user: AdminUser) => {
  isEditing.value = true
  editingUserId.value = user.id
  submitted.value = false
  userForm.value = {
    email: user.email,
    full_name: user.full_name,
    password: '',
    role: user.role,
    subscription_tier: user.subscription_tier,
    business_name: user.business_name || '',
    is_active: user.is_active,
  }
  showUserDialog.value = true
}

const saveUser = async () => {
  submitted.value = true

  // Validation
  if (!userForm.value.email || !userForm.value.full_name) {
    return
  }

  if (!isEditing.value && !userForm.value.password) {
    return
  }

  try {
    if (isEditing.value && editingUserId.value) {
      // Update
      const updateData: any = {
        email: userForm.value.email,
        full_name: userForm.value.full_name,
        role: userForm.value.role,
        subscription_tier: userForm.value.subscription_tier,
        business_name: userForm.value.business_name || null,
        is_active: userForm.value.is_active,
      }

      if (userForm.value.password) {
        updateData.password = userForm.value.password
      }

      await adminUsers.updateUser(editingUserId.value, updateData)

      toast?.add({
        severity: 'success',
        summary: 'Succès',
        detail: 'Utilisateur modifié avec succès',
        life: 3000,
      })
    } else {
      // Create
      await adminUsers.createUser({
        email: userForm.value.email,
        full_name: userForm.value.full_name,
        password: userForm.value.password,
        role: userForm.value.role,
        subscription_tier: userForm.value.subscription_tier,
        business_name: userForm.value.business_name || undefined,
        is_active: userForm.value.is_active,
      })

      toast?.add({
        severity: 'success',
        summary: 'Succès',
        detail: 'Utilisateur créé avec succès',
        life: 3000,
      })
    }

    showUserDialog.value = false
  } catch (e: any) {
    toast?.add({
      severity: 'error',
      summary: 'Erreur',
      detail: e.message || 'Impossible de sauvegarder l\'utilisateur',
      life: 5000,
    })
  }
}

const handleToggleActive = async (user: AdminUser) => {
  try {
    await adminUsers.toggleUserActive(user.id)

    const action = user.is_active ? 'désactivé' : 'activé'
    toast?.add({
      severity: 'success',
      summary: 'Succès',
      detail: `Utilisateur ${action} avec succès`,
      life: 3000,
    })
  } catch (e: any) {
    toast?.add({
      severity: 'error',
      summary: 'Erreur',
      detail: e.message || 'Impossible de modifier le statut',
      life: 5000,
    })
  }
}

const handleUnlock = async (user: AdminUser) => {
  try {
    await adminUsers.unlockUser(user.id)

    toast?.add({
      severity: 'success',
      summary: 'Succès',
      detail: 'Compte déverrouillé avec succès',
      life: 3000,
    })
  } catch (e: any) {
    toast?.add({
      severity: 'error',
      summary: 'Erreur',
      detail: e.message || 'Impossible de déverrouiller le compte',
      life: 5000,
    })
  }
}

const confirmDelete = (user: AdminUser) => {
  confirm?.require({
    message: `Êtes-vous sûr de vouloir supprimer l'utilisateur "${user.full_name}" (${user.email}) ? Cette action est irréversible.`,
    header: 'Confirmation de suppression',
    icon: 'pi pi-exclamation-triangle',
    acceptClass: 'p-button-danger',
    acceptLabel: 'Supprimer',
    rejectLabel: 'Annuler',
    accept: async () => {
      try {
        await adminUsers.deleteUser(user.id)

        toast?.add({
          severity: 'success',
          summary: 'Succès',
          detail: 'Utilisateur supprimé avec succès',
          life: 3000,
        })
      } catch (e: any) {
        toast?.add({
          severity: 'error',
          summary: 'Erreur',
          detail: e.message || 'Impossible de supprimer l\'utilisateur',
          life: 5000,
        })
      }
    },
  })
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
