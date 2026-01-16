<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-8 px-4">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-display font-bold text-gray-900 mb-2">
          📧 Preview Email Beta Confirmation
        </h1>
        <p class="text-gray-600">
          Visualisez le rendu de l'email de confirmation d'inscription beta avec différentes données
        </p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Controls Panel -->
        <div class="lg:col-span-1">
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sticky top-8">
            <h2 class="text-xl font-display font-semibold text-gray-900 mb-4">
              🎛️ Paramètres
            </h2>

            <!-- Name Input -->
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Nom complet
              </label>
              <InputText
                v-model="previewData.name"
                class="w-full"
                placeholder="Jean Dupont"
              />
            </div>

            <!-- Vendor Type -->
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Type de vendeur
              </label>
              <Dropdown
                v-model="previewData.vendorType"
                :options="vendorTypes"
                option-label="label"
                option-value="value"
                class="w-full"
              />
            </div>

            <!-- Monthly Volume -->
            <div class="mb-6">
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Volume mensuel
              </label>
              <Dropdown
                v-model="previewData.monthlyVolume"
                :options="monthlyVolumes"
                option-label="label"
                option-value="value"
                class="w-full"
              />
            </div>

            <!-- Refresh Button -->
            <Button
              label="Actualiser le preview"
              icon="pi pi-refresh"
              @click="refreshPreview"
              :loading="isLoading"
              class="w-full"
              severity="secondary"
            />

            <!-- Preset Examples -->
            <div class="mt-6 pt-6 border-t border-gray-200">
              <p class="text-sm font-medium text-gray-700 mb-3">
                💡 Exemples rapides
              </p>
              <div class="space-y-2">
                <button
                  @click="loadPreset('particulier-petit')"
                  class="w-full text-left px-3 py-2 text-sm bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  Particulier - Petit volume
                </button>
                <button
                  @click="loadPreset('professionnel-moyen')"
                  class="w-full text-left px-3 py-2 text-sm bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  Professionnel - Moyen volume
                </button>
                <button
                  @click="loadPreset('professionnel-gros')"
                  class="w-full text-left px-3 py-2 text-sm bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  Professionnel - Gros volume
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Email Preview -->
        <div class="lg:col-span-2">
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <!-- Preview Header -->
            <div class="bg-gray-50 border-b border-gray-200 px-6 py-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm font-medium text-gray-900">
                    De: {{ emailMeta.from }}
                  </p>
                  <p class="text-sm text-gray-600 mt-1">
                    Objet: {{ emailMeta.subject }}
                  </p>
                </div>
                <div class="flex items-center gap-2">
                  <Button
                    icon="pi pi-external-link"
                    text
                    rounded
                    severity="secondary"
                    @click="openInNewTab"
                    v-tooltip.top="'Ouvrir dans un nouvel onglet'"
                  />
                </div>
              </div>
            </div>

            <!-- Email Content -->
            <div class="relative">
              <!-- Loading Overlay -->
              <div
                v-if="isLoading"
                class="absolute inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center z-10"
              >
                <ProgressSpinner
                  style="width: 50px; height: 50px"
                  stroke-width="4"
                />
              </div>

              <!-- Email HTML -->
              <div class="p-6 bg-gray-50">
                <div class="max-w-2xl mx-auto bg-white shadow-lg rounded-lg overflow-hidden">
                  <iframe
                    ref="emailFrame"
                    :srcdoc="emailHtml"
                    class="w-full border-0"
                    style="min-height: 800px"
                    @load="adjustIframeHeight"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const config = useRuntimeConfig()

const previewData = reactive({
  name: 'Sophie Martin',
  vendorType: 'professionnel',
  monthlyVolume: '10-50'
})

const vendorTypes = [
  { label: 'Particulier', value: 'particulier' },
  { label: 'Professionnel', value: 'professionnel' }
]

const monthlyVolumes = [
  { label: '0-10 articles/mois', value: '0-10' },
  { label: '10-50 articles/mois', value: '10-50' },
  { label: '50+ articles/mois', value: '50+' }
]

const emailMeta = {
  from: 'StoFlow <noreply@stoflow.io>',
  subject: '🚀 Bienvenue dans la beta StoFlow !'
}

const emailHtml = ref('')
const isLoading = ref(false)
const emailFrame = ref<HTMLIFrameElement>()

// Load preview on mount
onMounted(() => {
  refreshPreview()
})

// Watch for changes and auto-refresh
watch(() => previewData, () => {
  refreshPreview()
}, { deep: true })

async function refreshPreview() {
  isLoading.value = true
  try {
    const response = await $fetch(`${config.public.apiBaseUrl}/preview/beta-confirmation`, {
      params: {
        name: previewData.name,
        vendor_type: previewData.vendorType,
        monthly_volume: previewData.monthlyVolume
      }
    })
    emailHtml.value = response as string
  } catch (error) {
    console.error('Failed to load email preview:', error)
  } finally {
    isLoading.value = false
  }
}

function adjustIframeHeight() {
  if (emailFrame.value?.contentWindow?.document.body) {
    const height = emailFrame.value.contentWindow.document.body.scrollHeight
    emailFrame.value.style.height = `${height + 40}px`
  }
}

function loadPreset(preset: string) {
  const presets = {
    'particulier-petit': {
      name: 'Marie Dubois',
      vendorType: 'particulier',
      monthlyVolume: '0-10'
    },
    'professionnel-moyen': {
      name: 'Alexandre Laurent',
      vendorType: 'professionnel',
      monthlyVolume: '10-50'
    },
    'professionnel-gros': {
      name: 'Emma Rousseau',
      vendorType: 'professionnel',
      monthlyVolume: '50+'
    }
  }

  Object.assign(previewData, presets[preset])
}

function openInNewTab() {
  const url = `${config.public.apiBaseUrl}/preview/beta-confirmation?name=${encodeURIComponent(previewData.name)}&vendor_type=${previewData.vendorType}&monthly_volume=${previewData.monthlyVolume}`
  window.open(url, '_blank')
}
</script>

<style scoped>
/* Smooth transitions */
.transition-colors {
  transition: background-color 0.2s ease;
}
</style>
