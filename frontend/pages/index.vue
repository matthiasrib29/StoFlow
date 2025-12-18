<template>
  <div class="min-h-screen flex items-center justify-center bg-white">
    <Card class="w-full max-w-md shadow-2xl border-2 border-secondary-900">
      <template #header>
        <div class="text-center py-6 bg-primary-400">
          <h1 class="text-4xl font-bold text-secondary-900">Stoflow</h1>
          <p class="text-secondary-900 mt-2 font-medium">Flow your products everywhere</p>
        </div>
      </template>
      <template #content>
        <div class="space-y-4">
          <p class="text-secondary-900 text-center font-medium">
            Plateforme SaaS pour publication automatisée de vos produits sur
            plusieurs marketplaces avec génération de descriptions par IA.
          </p>

          <div class="flex flex-col gap-3 mt-6">
            <Button
              label="Se connecter"
              icon="pi pi-sign-in"
              class="w-full bg-secondary-900 hover:bg-secondary-800 border-0"
              @click="navigateTo('/login')"
            />
            <Button
              label="Créer un compte"
              icon="pi pi-user-plus"
              class="w-full bg-primary-400 hover:bg-primary-500 text-secondary-900 border-2 border-secondary-900"
              @click="navigateTo('/register')"
            />
          </div>
        </div>
      </template>
      <template #footer>
        <div class="text-center text-sm text-secondary-700 border-t-2 border-primary-400 pt-4">
          <p>Version MVP 1.0 - Frontend Demo</p>
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
// Rediriger si déjà connecté
const authStore = useAuthStore()

onMounted(() => {
  if (authStore.isAuthenticated) {
    navigateTo('/dashboard')
  }
})
</script>
