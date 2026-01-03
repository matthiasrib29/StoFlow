<template>
  <Card class="w-full max-w-md border-2 border-secondary-900 shadow-xl">
      <template #title>
        <div class="flex items-center gap-2 bg-primary-400 -mx-6 -mt-6 px-6 py-4 mb-4">
          <i class="pi pi-sign-in text-secondary-900 text-2xl"/>
          <span class="text-secondary-900 font-bold text-2xl">Se connecter</span>
        </div>
      </template>
      <template #content>
        <form class="space-y-4" @submit.prevent="handleLogin">
          <div>
            <label for="email" class="block text-sm font-medium mb-2">
              Email
            </label>
            <InputText
              id="email"
              v-model="email"
              type="email"
              placeholder="votre@email.com"
              class="w-full"
              required
              :disabled="authStore.isLoading"
            />
          </div>

          <div>
            <label for="password" class="block text-sm font-medium mb-2">
              Mot de passe
            </label>
            <Password
              id="password"
              v-model="password"
              placeholder="••••••••"
              class="w-full"
              :feedback="false"
              toggle-mask
              required
              :disabled="authStore.isLoading"
            />
          </div>

          <div v-if="authStore.error" class="p-3 bg-secondary-50 border border-primary-200 rounded-lg">
            <p class="text-secondary-600 text-sm">
              <i class="pi pi-exclamation-triangle mr-2"/>
              {{ authStore.error }}
            </p>
          </div>

          <Button
            type="submit"
            label="Se connecter"
            icon="pi pi-sign-in"
            class="w-full bg-secondary-900 hover:bg-secondary-800 border-0 font-bold"
            :loading="authStore.isLoading"
          />
        </form>
      </template>
      <template #footer>
        <div class="text-center text-sm text-secondary-900 border-t-2 border-primary-400 pt-4">
          Pas encore de compte ?
          <NuxtLink to="/register" class="text-primary-600 hover:text-primary-700 underline font-bold">
            S'inscrire
          </NuxtLink>
        </div>
      </template>
  </Card>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'auth'
})

const authStore = useAuthStore()
const router = useRouter()
const { showSuccess, showError } = useAppToast()

const email = ref('')
const password = ref('')

const handleLogin = async () => {
  try {
    await authStore.login(email.value, password.value)
    showSuccess('Connexion réussie', `Bienvenue ${authStore.user?.full_name} !`)
    router.push('/dashboard')
  } catch (error: any) {
    showError('Erreur de connexion', error.message || 'Une erreur est survenue')
  }
}
</script>
