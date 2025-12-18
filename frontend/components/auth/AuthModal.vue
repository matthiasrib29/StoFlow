<template>
  <Dialog
    v-model:visible="isVisible"
    modal
    :closable="true"
    :dismissable-mask="true"
    :style="{ width: '450px' }"
    :draggable="false"
  >
    <template #header>
      <div class="flex items-center gap-3">
        <div class="w-12 h-12 rounded-xl bg-primary-100 flex items-center justify-center">
          <i class="pi pi-user text-primary-600 text-xl"/>
        </div>
        <div>
          <h3 class="text-2xl font-bold text-secondary-900">
            {{ isLoginMode ? 'Connexion' : 'Inscription' }}
          </h3>
          <p class="text-sm text-gray-600">
            {{ isLoginMode ? 'Connectez-vous à votre compte' : 'Créez votre compte Stoflow' }}
          </p>
        </div>
      </div>
    </template>

    <div class="space-y-6 py-4">
      <!-- Message d'erreur -->
      <Message v-if="errorMessage" severity="error" :closable="true" @close="errorMessage = null">
        {{ errorMessage }}
      </Message>

      <!-- Formulaire de connexion -->
      <div v-if="isLoginMode" class="space-y-4">
        <div>
          <label for="login-email" class="block text-sm font-semibold text-secondary-900 mb-2">
            Email
          </label>
          <InputText
            id="login-email"
            v-model="loginForm.email"
            type="email"
            placeholder="votre@email.com"
            class="w-full"
            :invalid="!!loginErrors.email"
            @keyup.enter="handleLogin"
          />
          <small v-if="loginErrors.email" class="text-red-500">{{ loginErrors.email }}</small>
        </div>

        <div>
          <label for="login-password" class="block text-sm font-semibold text-secondary-900 mb-2">
            Mot de passe
          </label>
          <Password
            id="login-password"
            v-model="loginForm.password"
            :feedback="false"
            toggle-mask
            placeholder="••••••••"
            class="w-full"
            :invalid="!!loginErrors.password"
            @keyup.enter="handleLogin"
          />
          <small v-if="loginErrors.password" class="text-red-500">{{ loginErrors.password }}</small>
        </div>
      </div>

      <!-- Formulaire d'inscription -->
      <div v-else class="space-y-4">
        <div>
          <label for="register-name" class="block text-sm font-semibold text-secondary-900 mb-2">
            Nom complet
          </label>
          <InputText
            id="register-name"
            v-model="registerForm.fullName"
            type="text"
            placeholder="John Doe"
            class="w-full"
            :invalid="!!registerErrors.fullName"
          />
          <small v-if="registerErrors.fullName" class="text-red-500">{{ registerErrors.fullName }}</small>
        </div>

        <div>
          <label for="register-email" class="block text-sm font-semibold text-secondary-900 mb-2">
            Email
          </label>
          <InputText
            id="register-email"
            v-model="registerForm.email"
            type="email"
            placeholder="votre@email.com"
            class="w-full"
            :invalid="!!registerErrors.email"
          />
          <small v-if="registerErrors.email" class="text-red-500">{{ registerErrors.email }}</small>
        </div>

        <div>
          <label for="register-password" class="block text-sm font-semibold text-secondary-900 mb-2">
            Mot de passe
          </label>
          <Password
            id="register-password"
            v-model="registerForm.password"
            :feedback="true"
            toggle-mask
            placeholder="••••••••"
            class="w-full"
            :invalid="!!registerErrors.password"
            prompt-label="Entrez un mot de passe"
            weak-label="Faible"
            medium-label="Moyen"
            strong-label="Fort"
          >
            <template #footer>
              <Divider />
              <p class="text-xs text-gray-600 mt-2">Suggestions:</p>
              <ul class="text-xs text-gray-600 ml-4 mt-1">
                <li>Au moins 12 caractères</li>
                <li>1 majuscule, 1 minuscule</li>
                <li>1 chiffre, 1 caractère spécial (!@#$%^&*)</li>
              </ul>
            </template>
          </Password>
          <small v-if="registerErrors.password" class="text-red-500">{{ registerErrors.password }}</small>
        </div>
      </div>

      <!-- Lien pour basculer entre connexion et inscription -->
      <div class="text-center">
        <Button
          :label="isLoginMode ? 'Pas encore de compte ? Inscrivez-vous' : 'Déjà un compte ? Connectez-vous'"
          link
          class="text-primary-600 hover:text-primary-700 text-sm"
          @click="toggleMode"
        />
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end gap-3">
        <Button
          label="Annuler"
          icon="pi pi-times"
          class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
          :disabled="isLoading"
          @click="close"
        />
        <Button
          :label="isLoginMode ? 'Se connecter' : 'S\'inscrire'"
          :icon="isLoading ? 'pi pi-spin pi-spinner' : 'pi pi-check'"
          class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
          :disabled="isLoading"
          @click="isLoginMode ? handleLogin() : handleRegister()"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
const props = defineProps<{
  visible: boolean
  mode?: 'login' | 'register'
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'success': []
}>()

const { showSuccess, showError } = useAppToast()
const authStore = useAuthStore()

// State
const isLoginMode = ref(props.mode === 'login' || props.mode !== 'register')
const isLoading = ref(false)
const errorMessage = ref<string | null>(null)

// Forms
const loginForm = reactive({
  email: '',
  password: ''
})

const registerForm = reactive({
  fullName: '',
  email: '',
  password: ''
})

// Errors
const loginErrors = reactive({
  email: '',
  password: ''
})

const registerErrors = reactive({
  fullName: '',
  email: '',
  password: ''
})

// Computed
const isVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

// Methods
const toggleMode = () => {
  isLoginMode.value = !isLoginMode.value
  errorMessage.value = null
  resetForms()
}

const resetForms = () => {
  loginForm.email = ''
  loginForm.password = ''
  registerForm.fullName = ''
  registerForm.email = ''
  registerForm.password = ''

  loginErrors.email = ''
  loginErrors.password = ''
  registerErrors.fullName = ''
  registerErrors.email = ''
  registerErrors.password = ''
}

const validateLogin = (): boolean => {
  let isValid = true

  loginErrors.email = ''
  loginErrors.password = ''

  if (!loginForm.email) {
    loginErrors.email = 'Email requis'
    isValid = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(loginForm.email)) {
    loginErrors.email = 'Email invalide'
    isValid = false
  }

  if (!loginForm.password) {
    loginErrors.password = 'Mot de passe requis'
    isValid = false
  } else if (loginForm.password.length < 8) {
    loginErrors.password = 'Minimum 8 caractères'
    isValid = false
  }

  return isValid
}

const validateRegister = (): boolean => {
  let isValid = true

  registerErrors.fullName = ''
  registerErrors.email = ''
  registerErrors.password = ''

  if (!registerForm.fullName || registerForm.fullName.trim().length === 0) {
    registerErrors.fullName = 'Nom complet requis'
    isValid = false
  } else if (registerForm.fullName.length > 255) {
    registerErrors.fullName = 'Maximum 255 caractères'
    isValid = false
  }

  if (!registerForm.email) {
    registerErrors.email = 'Email requis'
    isValid = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registerForm.email)) {
    registerErrors.email = 'Email invalide'
    isValid = false
  }

  if (!registerForm.password) {
    registerErrors.password = 'Mot de passe requis'
    isValid = false
  } else if (registerForm.password.length < 12) {
    registerErrors.password = 'Minimum 12 caractères'
    isValid = false
  } else {
    // Validation complexité (backend requirement)
    const hasUppercase = /[A-Z]/.test(registerForm.password)
    const hasLowercase = /[a-z]/.test(registerForm.password)
    const hasNumber = /[0-9]/.test(registerForm.password)
    const hasSpecial = /[!@#$%^&*]/.test(registerForm.password)

    if (!hasUppercase || !hasLowercase || !hasNumber || !hasSpecial) {
      registerErrors.password = 'Doit contenir: 1 majuscule, 1 minuscule, 1 chiffre, 1 caractère spécial (!@#$%^&*)'
      isValid = false
    }
  }

  return isValid
}

const handleLogin = async () => {
  if (!validateLogin()) return

  isLoading.value = true
  errorMessage.value = null

  try {
    await authStore.login(loginForm.email, loginForm.password)

    showSuccess('Connexion réussie', `Bienvenue ${authStore.user?.email || ''}`)

    emit('success')
    close()
  } catch (error: any) {
    errorMessage.value = error.message || 'Erreur lors de la connexion'
    showError('Erreur de connexion', error.message || 'Impossible de se connecter', 5000)
  } finally {
    isLoading.value = false
  }
}

const handleRegister = async () => {
  if (!validateRegister()) return

  isLoading.value = true
  errorMessage.value = null

  try {
    await authStore.register(
      registerForm.email,
      registerForm.password,
      registerForm.fullName
    )

    showSuccess('Inscription réussie', `Bienvenue sur Stoflow, ${registerForm.fullName} !`)

    emit('success')
    close()
  } catch (error: any) {
    errorMessage.value = error.message || 'Erreur lors de l\'inscription'
    showError('Erreur d\'inscription', error.message || 'Impossible de créer le compte', 5000)
  } finally {
    isLoading.value = false
  }
}

const close = () => {
  emit('update:visible', false)
  resetForms()
  errorMessage.value = null
}

// Watch mode changes
watch(() => props.mode, (newMode) => {
  if (newMode) {
    isLoginMode.value = newMode === 'login'
  }
})
</script>

<style scoped>
:deep(.p-password input) {
  width: 100%;
}

:deep(.p-inputtext) {
  width: 100%;
}
</style>
