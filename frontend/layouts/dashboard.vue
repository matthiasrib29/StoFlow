<template>
  <div class="min-h-screen bg-white">
    <!-- Mobile Menu Overlay -->
    <Transition
      enter-active-class="transition-opacity duration-300"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-200"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="nav.mobileMenuOpen.value"
        class="fixed inset-0 bg-black/50 z-40 lg:hidden"
        @click="nav.closeMobileMenu"
      />
    </Transition>

    <!-- Sidebar -->
    <LayoutDashboardSidebar
      :mobile-menu-open="nav.mobileMenuOpen.value"
      :nav="nav"
      @logout="handleLogout"
    />

    <!-- Main content -->
    <div class="lg:ml-64 bg-white min-h-screen">
      <!-- Top Bar -->
      <div class="bg-white sticky top-0 z-30 border-b border-gray-100 lg:border-0">
        <div class="flex items-center justify-between px-3 lg:px-6 py-2">
          <div class="flex items-center gap-4">
            <!-- Mobile Menu Button -->
            <button
              class="lg:hidden p-2 -ml-2 rounded-lg hover:bg-gray-100 transition-colors"
              @click="nav.openMobileMenu"
            >
              <i class="pi pi-bars text-xl text-gray-600" />
            </button>

            <!-- Breadcrumb -->
            <nav class="flex items-center gap-2 text-sm">
              <NuxtLink
                to="/dashboard"
                class="text-gray-500 hover:text-secondary-900 transition-colors duration-200"
              >
                <i class="pi pi-home text-xs"/>
              </NuxtLink>
              <template v-for="crumb in breadcrumbs" :key="crumb.path || crumb.label">
                <i class="pi pi-chevron-right text-gray-400 text-xs"/>
                <NuxtLink
                  v-if="crumb.path"
                  :to="crumb.path"
                  class="text-gray-500 hover:text-secondary-900 transition-colors duration-200 capitalize"
                >
                  {{ crumb.label }}
                </NuxtLink>
                <span v-else class="text-secondary-900 font-semibold capitalize">
                  {{ crumb.label }}
                </span>
              </template>
            </nav>
          </div>

          <!-- Platform Header Actions -->
          <PlatformHeaderActions
            v-if="nav.isVintedRoute.value"
            platform-name="Vinted"
            platform-code="vinted"
            logo-src="/images/platforms/vinted-logo.png"
            :active-jobs-count="vintedJobsCount"
            :is-connected="vintedConnected"
            @show-jobs="showVintedJobsPopup = true"
            @connect="connectPlatform('vinted')"
            @disconnect="disconnectPlatform('vinted')"
          />
          <PlatformHeaderActions
            v-else-if="nav.isEbayRoute.value"
            platform-name="eBay"
            platform-code="ebay"
            logo-src="/images/platforms/ebay-logo.png"
            :active-jobs-count="ebayJobsCount"
            :is-connected="ebayConnected"
            @show-jobs="showEbayJobsPopup = true"
            @connect="connectPlatform('ebay')"
            @disconnect="disconnectPlatform('ebay')"
          />
          <PlatformHeaderActions
            v-else-if="nav.isEtsyRoute.value"
            platform-name="Etsy"
            platform-code="etsy"
            logo-src="/images/platforms/etsy-logo.png"
            :active-jobs-count="etsyJobsCount"
            :is-connected="etsyConnected"
            @show-jobs="showEtsyJobsPopup = true"
            @connect="connectPlatform('etsy')"
            @disconnect="disconnectPlatform('etsy')"
          />
        </div>
      </div>

      <!-- Page Content -->
      <slot />

      <!-- Platform Jobs Popups -->
      <PlatformJobsPopup v-model="showVintedJobsPopup" platform-code="vinted" />
      <PlatformJobsPopup v-model="showEbayJobsPopup" platform-code="ebay" />
      <PlatformJobsPopup v-model="showEtsyJobsPopup" platform-code="etsy" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useToast } from 'primevue/usetoast'
import { usePlatformJobs, type PlatformCode } from '~/composables/usePlatformJobs'
import { usePlatformConnection } from '~/composables/usePlatformConnection'

// SEO: Prevent search engines from indexing private dashboard pages
useHead({
  meta: [
    { name: 'robots', content: 'noindex, nofollow' }
  ]
})

const authStore = useAuthStore()
const router = useRouter()
const toast = import.meta.client ? useToast() : null

// Navigation composable
const nav = useDashboardNavigation()

// Breadcrumbs composable
const { breadcrumbs } = useBreadcrumbs()

// Platform Jobs composables
const vintedJobs = usePlatformJobs('vinted')
const ebayJobs = usePlatformJobs('ebay')
const etsyJobs = usePlatformJobs('etsy')

// Platform Connection composables
const vintedConnection = usePlatformConnection('vinted')
const ebayConnection = usePlatformConnection('ebay')
const etsyConnection = usePlatformConnection('etsy')

// Jobs counts
const vintedJobsCount = computed(() => vintedJobs.activeJobsCount.value)
const ebayJobsCount = computed(() => ebayJobs.activeJobsCount.value)
const etsyJobsCount = computed(() => etsyJobs.activeJobsCount.value)

// Connection status
const vintedConnected = computed(() => vintedConnection.isConnected.value)
const ebayConnected = computed(() => ebayConnection.isConnected.value)
const etsyConnected = computed(() => etsyConnection.isConnected.value)

// Jobs popups visibility
const showVintedJobsPopup = ref(false)
const showEbayJobsPopup = ref(false)
const showEtsyJobsPopup = ref(false)

// Platform connect/disconnect handlers
const connectPlatform = (platform: PlatformCode) => {
  const connections: Record<PlatformCode, ReturnType<typeof usePlatformConnection>> = {
    vinted: vintedConnection,
    ebay: ebayConnection,
    etsy: etsyConnection,
  }
  connections[platform].connect()
}

const disconnectPlatform = async (platform: PlatformCode) => {
  const connections: Record<PlatformCode, ReturnType<typeof usePlatformConnection>> = {
    vinted: vintedConnection,
    ebay: ebayConnection,
    etsy: etsyConnection,
  }
  const connection = connections[platform]
  const success = await connection.disconnect()

  if (success) {
    toast?.add({
      severity: 'info',
      summary: `${connection.platformName} déconnecté`,
      detail: `Votre compte ${connection.platformName} a été déconnecté`,
      life: 3000,
    })
  } else {
    toast?.add({
      severity: 'error',
      summary: 'Erreur',
      detail: connection.error.value || `Impossible de déconnecter ${connection.platformName}`,
      life: 5000,
    })
  }
}

// Platform watchers: Fetch status when on platform route
watch(nav.isVintedRoute, (isActive) => {
  if (!import.meta.client) return
  if (isActive) vintedConnection.fetchStatus()
}, { immediate: true })

watch(nav.isEbayRoute, (isActive) => {
  if (!import.meta.client) return
  if (isActive) ebayConnection.fetchStatus()
}, { immediate: true })

watch(nav.isEtsyRoute, (isActive) => {
  if (!import.meta.client) return
  if (isActive) etsyConnection.fetchStatus()
}, { immediate: true })

// Logout handler
const handleLogout = () => {
  authStore.logout()
  toast?.add({
    severity: 'info',
    summary: 'Déconnexion',
    detail: 'À bientôt !',
    life: 3000
  })
  router.push('/login')
}
</script>
