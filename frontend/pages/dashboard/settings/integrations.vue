<template>
  <div class="page-container">
    <PageHeader
      title="Intégrations"
      subtitle="Gérez vos connexions aux services externes"
    />

    <!-- Contenu -->
    <div class="space-y-6">
      <!-- Marketplaces connectées -->
      <Card class="shadow-sm modern-rounded border border-gray-100">
        <template #content>
          <div class="space-y-6">
            <div>
              <h3 class="text-lg font-bold text-secondary-900 mb-1">Marketplaces</h3>
              <p class="text-sm text-gray-600">État de vos connexions aux plateformes de vente</p>
            </div>

            <div class="space-y-4">
              <!-- Vinted -->
              <div class="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                <div class="flex items-center gap-4">
                  <div class="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                    <img src="/images/platforms/vinted-logo.png" alt="Vinted" class="w-8 h-8 object-contain">
                  </div>
                  <div>
                    <p class="font-semibold text-secondary-900">Vinted</p>
                    <p class="text-sm text-gray-600">Synchronisation via extension navigateur</p>
                  </div>
                </div>
                <div class="flex items-center gap-3">
                  <span class="badge badge-success">Connecté</span>
                  <Button
                    icon="pi pi-cog"
                    class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
                    size="small"
                    @click="navigateTo('/dashboard/platforms/vinted/settings')"
                  />
                </div>
              </div>

              <!-- eBay -->
              <div class="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                <div class="flex items-center gap-4">
                  <div class="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                    <img src="/images/platforms/ebay-logo.png" alt="eBay" class="w-8 h-8 object-contain">
                  </div>
                  <div>
                    <p class="font-semibold text-secondary-900">eBay</p>
                    <p class="text-sm text-gray-600">Intégration API directe</p>
                  </div>
                </div>
                <div class="flex items-center gap-3">
                  <span class="badge badge-neutral">Non connecté</span>
                  <Button
                    label="Connecter"
                    icon="pi pi-link"
                    class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0"
                    size="small"
                    @click="navigateTo('/dashboard/platforms/ebay')"
                  />
                </div>
              </div>

              <!-- Etsy -->
              <div class="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                <div class="flex items-center gap-4">
                  <div class="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                    <img src="/images/platforms/etsy-logo.png" alt="Etsy" class="w-8 h-8 object-contain">
                  </div>
                  <div>
                    <p class="font-semibold text-secondary-900">Etsy</p>
                    <p class="text-sm text-gray-600">Intégration API directe</p>
                  </div>
                </div>
                <div class="flex items-center gap-3">
                  <span class="badge badge-neutral">Non connecté</span>
                  <Button
                    label="Connecter"
                    icon="pi pi-link"
                    class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0"
                    size="small"
                    @click="navigateTo('/dashboard/platforms/etsy')"
                  />
                </div>
              </div>
            </div>
          </div>
        </template>
      </Card>

      <!-- MVP1: Clé API et Webhooks désactivés - voir commentaire en bas -->
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'dashboard'
})
</script>

<!--
MVP1: Sections Clé API et Webhooks désactivées - Code original commenté

<Card class="shadow-sm modern-rounded border border-gray-100">
  <template #content>
    <div class="space-y-4">
      <div>
        <h3 class="text-lg font-bold text-secondary-900 mb-1">Clé API</h3>
        <p class="text-sm text-gray-600">Utilisez cette clé pour intégrer StoFlow à vos propres outils</p>
      </div>

      <div class="flex items-center gap-3">
        <InputText
          :model-value="apiKeyVisible ? apiKey : '••••••••••••••••••••••••'"
          readonly
          class="w-full font-mono text-sm"
        />
        <Button
          :icon="apiKeyVisible ? 'pi pi-eye-slash' : 'pi pi-eye'"
          class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
          @click="apiKeyVisible = !apiKeyVisible"
        />
        <Button
          icon="pi pi-copy"
          class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
          @click="copyApiKey"
        />
      </div>

      <div class="flex justify-end">
        <Button
          label="Régénérer la clé"
          icon="pi pi-refresh"
          class="bg-red-100 hover:bg-red-200 text-red-700 border-0"
          size="small"
          @click="regenerateApiKey"
        />
      </div>
    </div>
  </template>
</Card>

<Card class="shadow-sm modern-rounded border border-gray-100">
  <template #content>
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-lg font-bold text-secondary-900 mb-1">Webhooks</h3>
          <p class="text-sm text-gray-600">Recevez des notifications en temps réel</p>
        </div>
        <Button
          label="Ajouter un webhook"
          icon="pi pi-plus"
          class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0"
          size="small"
        />
      </div>

      <div class="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
        <i class="pi pi-link text-gray-400 text-3xl mb-2" />
        <p class="text-gray-600">Aucun webhook configuré</p>
        <p class="text-sm text-gray-500">Les webhooks vous permettent de recevoir des événements en temps réel</p>
      </div>
    </div>
  </template>
</Card>

Script pour ces fonctionnalités:

const { showSuccess, showInfo } = useAppToast()

const apiKey = ref('sk_live_stoflow_abc123def456ghi789')
const apiKeyVisible = ref(false)

const copyApiKey = () => {
  navigator.clipboard.writeText(apiKey.value)
  showSuccess('Copié', 'Clé API copiée dans le presse-papier', 2000)
}

const regenerateApiKey = () => {
  showInfo('Info', 'Fonctionnalité bientôt disponible', 3000)
}
-->
