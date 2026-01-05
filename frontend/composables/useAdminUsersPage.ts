import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { useAdminUsers, type AdminUser } from '~/composables/useAdminUsers'

export interface UserForm {
  email: string
  full_name: string
  password: string
  role: string
  subscription_tier: string
  business_name: string
  is_active: boolean
}

const defaultForm = (): UserForm => ({
  email: '',
  full_name: '',
  password: '',
  role: 'user',
  subscription_tier: 'free',
  business_name: '',
  is_active: true,
})

export function useAdminUsersPage() {
  const authStore = useAuthStore()
  const adminUsers = useAdminUsers()
  const confirm = import.meta.client ? useConfirm() : null
  const toast = import.meta.client ? useToast() : null

  // State
  const searchQuery = ref('')
  const selectedRole = ref<string | null>(null)
  const selectedStatus = ref<boolean | null>(null)
  const showUserDialog = ref(false)
  const isEditing = ref(false)
  const editingUserId = ref<number | null>(null)
  const userForm = ref<UserForm>(defaultForm())

  // Computed
  const currentUserId = computed(() => authStore.user?.id ?? null)
  const isCurrentUserEditing = computed(() => {
    return isEditing.value && editingUserId.value === currentUserId.value
  })

  // Fetch users with filters
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

  // Dialog methods
  const openCreateDialog = () => {
    isEditing.value = false
    editingUserId.value = null
    userForm.value = defaultForm()
    showUserDialog.value = true
  }

  const openEditDialog = (user: AdminUser) => {
    isEditing.value = true
    editingUserId.value = user.id
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

  const closeDialog = () => {
    showUserDialog.value = false
  }

  // Save user (create or update)
  const saveUser = async (form: UserForm) => {
    try {
      if (isEditing.value && editingUserId.value) {
        const updateData: any = {
          email: form.email,
          full_name: form.full_name,
          role: form.role,
          subscription_tier: form.subscription_tier,
          business_name: form.business_name || null,
          is_active: form.is_active,
        }

        if (form.password) {
          updateData.password = form.password
        }

        await adminUsers.updateUser(editingUserId.value, updateData)

        toast?.add({
          severity: 'success',
          summary: 'Succès',
          detail: 'Utilisateur modifié avec succès',
          life: 3000,
        })
      } else {
        await adminUsers.createUser({
          email: form.email,
          full_name: form.full_name,
          password: form.password,
          role: form.role,
          subscription_tier: form.subscription_tier,
          business_name: form.business_name || undefined,
          is_active: form.is_active,
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

  // Toggle user active status
  const handleToggleActive = async (user: AdminUser) => {
    try {
      await adminUsers.toggleUserActive(user.id, user.is_active)

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

  // Unlock user
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

  // Confirm and delete user
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

  return {
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
    users: adminUsers.users,
    total: adminUsers.total,
    isLoading: adminUsers.isLoading,

    // Methods
    fetchUsers,
    debouncedSearch,
    openCreateDialog,
    openEditDialog,
    closeDialog,
    saveUser,
    handleToggleActive,
    handleUnlock,
    confirmDelete,
  }
}
