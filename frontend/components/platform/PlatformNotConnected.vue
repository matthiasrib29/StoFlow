<template>
  <Card class="shadow-sm modern-rounded border border-gray-100">
    <template #content>
      <div class="text-center py-12">
        <i class="pi pi-link text-4xl text-gray-300 mb-4"/>
        <h3 class="text-xl font-bold text-secondary-900 mb-2">
          Connectez votre compte {{ platformLabel }}
        </h3>
        <p class="text-gray-500 mb-4">{{ message }}</p>
        <Button
          :label="buttonLabel"
          icon="pi pi-link"
          class="btn-primary"
          @click="handleConnect"
        />
      </div>
    </template>
  </Card>
</template>

<script setup lang="ts">
type Platform = 'vinted' | 'ebay' | 'etsy'

const props = withDefaults(defineProps<{
  platform: Platform
  message?: string
  buttonLabel?: string
  redirectTo?: string
}>(), {
  message: 'Accédez à vos produits après connexion',
  buttonLabel: 'Connecter maintenant'
})

const platformLabels: Record<Platform, string> = {
  vinted: 'Vinted',
  ebay: 'eBay',
  etsy: 'Etsy'
}

const platformLabel = computed(() => platformLabels[props.platform])

const handleConnect = () => {
  // Si une redirection custom est fournie, l'utiliser
  if (props.redirectTo) {
    navigateTo(props.redirectTo)
    return
  }

  // Sinon, redirection automatique vers la page products de la plateforme
  const defaultRoutes: Record<Platform, string> = {
    vinted: '/dashboard/platforms/vinted/products',
    ebay: '/dashboard/platforms/ebay/products',
    etsy: '/dashboard/platforms/etsy/products'
  }

  navigateTo(defaultRoutes[props.platform])
}
</script>
