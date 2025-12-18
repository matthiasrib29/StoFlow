<template>
  <div class="min-h-screen bg-white">
    <!-- Modern Sidebar -->
    <aside class="fixed left-0 top-0 h-full w-64 bg-white shadow-sm border-r border-gray-200 z-10">
      <!-- Logo & Tenant -->
      <div class="p-6 border-b border-gray-100">
        <h1 class="text-2xl font-bold text-secondary-900 mb-1">Stoflow</h1>
        <p class="text-xs text-gray-500 font-medium">{{ authStore?.user?.tenant_name }}</p>
      </div>

      <!-- Navigation -->
      <nav class="px-3 py-6 space-y-1">
        <!-- Accueil -->
        <NuxtLink
          to="/dashboard"
          class="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-gray-50 transition-all text-gray-600 font-medium"
          active-class="bg-primary-50 text-secondary-900 font-semibold shadow-sm border border-primary-100"
        >
          <i class="pi pi-home text-lg"></i>
          <span>Accueil</span>
        </NuxtLink>

        <!-- Produits avec sous-menu -->
        <div>
          <button
            @click="toggleProductsMenu"
            class="w-full flex items-center justify-between px-4 py-3 rounded-xl hover:bg-gray-50 transition-all text-gray-600 font-medium"
            :class="{ 'bg-primary-50 text-secondary-900 font-semibold shadow-sm border border-primary-100': isProductsRoute }"
          >
            <div class="flex items-center gap-3">
              <i class="pi pi-box text-lg"></i>
              <span>Produits</span>
            </div>
            <i :class="['pi pi-chevron-down text-sm transition-transform duration-300', productsMenuOpen ? 'rotate-180' : 'rotate-0']"></i>
          </button>

          <!-- Sous-menu avec animation slide -->
          <Transition
            enter-active-class="transition-all duration-300 ease-out"
            enter-from-class="opacity-0 max-h-0 -translate-y-2"
            enter-to-class="opacity-100 max-h-40 translate-y-0"
            leave-active-class="transition-all duration-200 ease-in"
            leave-from-class="opacity-100 max-h-40 translate-y-0"
            leave-to-class="opacity-0 max-h-0 -translate-y-2"
          >
            <div
              v-if="productsMenuOpen"
              class="mt-1 ml-4 space-y-1 overflow-hidden"
            >
              <NuxtLink
                to="/dashboard/products"
                class="flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                active-class="bg-primary-50 text-secondary-900 font-semibold"
              >
                <i class="pi pi-list text-sm"></i>
                <span>Liste des produits</span>
              </NuxtLink>

              <NuxtLink
                to="/dashboard/products/create"
                class="flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                active-class="bg-primary-50 text-secondary-900 font-semibold"
              >
                <i class="pi pi-plus text-sm"></i>
                <span>Créer un produit</span>
              </NuxtLink>
            </div>
          </Transition>
        </div>

        <!-- Plateformes avec sous-menu -->
        <div>
          <div class="flex items-center gap-1">
            <NuxtLink
              to="/dashboard/platforms"
              class="flex-1 flex items-center gap-3 px-4 py-3 rounded-l-xl hover:bg-gray-50 transition-all text-gray-600 font-medium"
              active-class="bg-primary-50 text-secondary-900 font-semibold shadow-sm border border-primary-100"
            >
              <i class="pi pi-shopping-bag text-lg"></i>
              <span>Plateformes</span>
            </NuxtLink>
            <button
              @click="togglePlatformsMenu"
              class="px-3 py-3 rounded-r-xl hover:bg-gray-50 transition-all text-gray-600"
              :class="{ 'bg-primary-50 text-secondary-900': platformsMenuOpen }"
            >
              <i :class="['pi pi-chevron-down text-sm transition-transform duration-300', platformsMenuOpen ? 'rotate-180' : 'rotate-0']"></i>
            </button>
          </div>

          <!-- Sous-menu Plateformes avec animation -->
          <Transition
            enter-active-class="transition-all duration-300 ease-out"
            enter-from-class="opacity-0 max-h-0 -translate-y-2"
            enter-to-class="opacity-100 max-h-60 translate-y-0"
            leave-active-class="transition-all duration-200 ease-in"
            leave-from-class="opacity-100 max-h-60 translate-y-0"
            leave-to-class="opacity-0 max-h-0 -translate-y-2"
          >
            <div
              v-if="platformsMenuOpen"
              class="mt-1 ml-4 space-y-1 overflow-hidden"
            >
              <NuxtLink
                to="/dashboard/platforms/vinted"
                class="flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                active-class="bg-primary-50 text-secondary-900 font-semibold"
              >
                <img src="/images/platforms/vinted-logo.png" alt="Vinted" class="w-4 h-4 object-contain" />
                <span>Vinted</span>
              </NuxtLink>

              <NuxtLink
                to="/dashboard/platforms/ebay"
                class="flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                active-class="bg-primary-50 text-secondary-900 font-semibold"
              >
                <img src="/images/platforms/ebay-logo.png" alt="eBay" class="w-4 h-4 object-contain" />
                <span>eBay</span>
              </NuxtLink>

              <NuxtLink
                to="/dashboard/platforms/etsy"
                class="flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                active-class="bg-primary-50 text-secondary-900 font-semibold"
              >
                <img src="/images/platforms/etsy-logo.png" alt="Etsy" class="w-4 h-4 object-contain" />
                <span>Etsy</span>
              </NuxtLink>

              <NuxtLink
                to="/dashboard/platforms/facebook"
                class="flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                active-class="bg-primary-50 text-secondary-900 font-semibold"
              >
                <img src="/images/platforms/facebook-logo.png" alt="Facebook" class="w-4 h-4 object-contain" />
                <span>Facebook Marketplace</span>
              </NuxtLink>
            </div>
          </Transition>
        </div>

        <!-- Publications -->
        <NuxtLink
          to="/dashboard/publications"
          class="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-gray-50 transition-all text-gray-600 font-medium"
          active-class="bg-primary-50 text-secondary-900 font-semibold shadow-sm border border-primary-100"
        >
          <i class="pi pi-send text-lg"></i>
          <span>Publications</span>
        </NuxtLink>

        <!-- Statistiques -->
        <NuxtLink
          to="/dashboard/stats"
          class="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-gray-50 transition-all text-gray-600 font-medium"
          active-class="bg-primary-50 text-secondary-900 font-semibold shadow-sm border border-primary-100"
        >
          <i class="pi pi-chart-bar text-lg"></i>
          <span>Statistiques</span>
        </NuxtLink>

        <!-- Abonnement -->
        <NuxtLink
          to="/dashboard/subscription"
          class="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-gray-50 transition-all text-gray-600 font-medium"
          active-class="bg-primary-50 text-secondary-900 font-semibold shadow-sm border border-primary-100"
        >
          <i class="pi pi-star text-lg"></i>
          <span>Abonnement</span>
        </NuxtLink>

        <!-- Paramètres -->
        <NuxtLink
          to="/dashboard/settings"
          class="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-gray-50 transition-all text-gray-600 font-medium"
          active-class="bg-primary-50 text-secondary-900 font-semibold shadow-sm border border-primary-100"
        >
          <i class="pi pi-cog text-lg"></i>
          <span>Paramètres</span>
        </NuxtLink>
      </nav>

      <!-- User Section -->
      <div class="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-100 bg-gray-50">
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
            <i class="pi pi-user text-primary-600"></i>
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-semibold truncate text-secondary-900">{{ authStore?.user?.full_name }}</p>
            <ClientOnly>
              <p class="text-xs text-gray-500 truncate">{{ authStore?.user?.email }}</p>
              <template #fallback>
                <p class="text-xs text-gray-500 truncate">&nbsp;</p>
              </template>
            </ClientOnly>
          </div>
        </div>
        <Button
          label="Déconnexion"
          icon="pi pi-sign-out"
          class="w-full bg-secondary-900 hover:bg-secondary-800 text-primary-400 border-0 font-semibold"
          size="small"
          @click="handleLogout"
        />
      </div>
    </aside>

    <!-- Main content -->
    <div class="ml-64 bg-white">
      <!-- Top Bar with Locale Selector -->
      <div class="bg-white">
        <div class="flex items-center justify-between px-8 py-3">
          <div class="flex items-center gap-4">
            <!-- Breadcrumb -->
            <nav class="flex items-center gap-2 text-sm">
              <NuxtLink
                to="/dashboard"
                class="text-gray-500 hover:text-secondary-900 transition-colors duration-200"
              >
                <i class="pi pi-home text-xs"></i>
              </NuxtLink>
              <template v-for="(crumb, index) in breadcrumbs" :key="crumb.path || crumb.label">
                <i class="pi pi-chevron-right text-gray-400 text-xs"></i>
                <NuxtLink
                  v-if="crumb.path"
                  :to="crumb.path"
                  class="text-gray-500 hover:text-secondary-900 transition-colors duration-200 capitalize"
                >
                  {{ crumb.label }}
                </NuxtLink>
                <span
                  v-else
                  class="text-secondary-900 font-semibold capitalize"
                >
                  {{ crumb.label }}
                </span>
              </template>
            </nav>
          </div>

          <!-- Locale Selector -->
          <div class="flex items-center gap-4">
            <div class="flex items-center gap-2 text-sm text-gray-600">
              <i class="pi pi-globe"></i>
              <span class="font-medium">Langue :</span>
            </div>
            <LocaleSelector />
          </div>
        </div>
      </div>

      <!-- Page Content -->
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useToast } from 'primevue/usetoast'
import { useLocaleStore } from '~/stores/locale'

const authStore = useAuthStore()
const localeStore = useLocaleStore()
const router = useRouter()
const route = useRoute()
// SSR-safe initialization
const toast = import.meta.client ? useToast() : null

// État des sous-menus
const productsMenuOpen = ref(false)
const platformsMenuOpen = ref(false)

// Client-side mount state for hydration safety
const mounted = ref(false)
onMounted(() => {
  mounted.value = true
})

// Breadcrumb intelligent
const breadcrumbs = computed(() => {
  const path = route.path
  const crumbs: Array<{ label: string; path?: string }> = []

  // Cas spéciaux pour les pages d'abonnement
  if (path.startsWith('/dashboard/subscription')) {
    crumbs.push({ label: 'Abonnement', path: '/dashboard/subscription' })

    // Page de détails crédits IA
    if (path.match(/\/subscription\/credits\/(\d+)/)) {
      const credits = route.params.credits
      crumbs.push({ label: `Pack ${credits} crédits` })
    }
    // Page de détails upgrade
    else if (path.match(/\/subscription\/upgrade\/([^/]+)/)) {
      const tier = route.params.tier as string
      crumbs.push({ label: `Abonnement ${tier.toUpperCase()}` })
    }
    // Page de paiement
    else if (path.includes('/payment')) {
      // Déterminer le label basé sur les query params
      const type = route.query.type as string
      if (type === 'credits') {
        const credits = route.query.credits
        crumbs.push({ label: `Pack ${credits} crédits`, path: `/dashboard/subscription/credits/${credits}` })
      } else if (type === 'upgrade') {
        const tier = route.query.tier as string
        crumbs.push({ label: `Abonnement ${tier?.toUpperCase()}`, path: `/dashboard/subscription/upgrade/${tier}` })
      }
      crumbs.push({ label: 'Paiement' })
    }
  }
  // Cas spéciaux pour les produits
  else if (path.startsWith('/dashboard/products')) {
    crumbs.push({ label: 'Produits', path: '/dashboard/products' })

    if (path.includes('/create')) {
      crumbs.push({ label: 'Créer un produit' })
    } else if (route.params.sku) {
      crumbs.push({ label: `Produit ${route.params.sku}` })
    }
  }
  // Cas spéciaux pour les plateformes
  else if (path.startsWith('/dashboard/platforms')) {
    crumbs.push({ label: 'Plateformes', path: '/dashboard/platforms' })

    if (path.includes('/vinted')) {
      crumbs.push({ label: 'Vinted' })
    } else if (path.includes('/ebay')) {
      crumbs.push({ label: 'eBay' })
    } else if (path.includes('/etsy')) {
      crumbs.push({ label: 'Etsy' })
    } else if (path.includes('/facebook')) {
      crumbs.push({ label: 'Facebook Marketplace' })
    }
  }
  // Autres pages simples
  else if (path.startsWith('/dashboard/')) {
    const segments = path.split('/').filter(Boolean)
    if (segments.length > 1) {
      const pageName = segments[segments.length - 1]
      const labels: Record<string, string> = {
        'publications': 'Publications',
        'stats': 'Statistiques',
        'settings': 'Paramètres'
      }
      crumbs.push({ label: labels[pageName] || pageName })
    }
  }

  return crumbs
})

// Vérifier si on est sur une route produits
const isProductsRoute = computed(() => {
  return route.path.startsWith('/dashboard/products')
})

// Vérifier si on est sur une route plateformes
const isPlatformsRoute = computed(() => {
  return route.path.startsWith('/dashboard/platforms')
})

// Ouvrir automatiquement les menus si on est sur leurs routes
watch(() => route.path, (newPath) => {
  if (newPath.startsWith('/dashboard/products')) {
    productsMenuOpen.value = true
  }
  if (newPath.startsWith('/dashboard/platforms')) {
    platformsMenuOpen.value = true
  }
}, { immediate: true })

// Toggle des menus
const toggleProductsMenu = () => {
  productsMenuOpen.value = !productsMenuOpen.value
}

const togglePlatformsMenu = () => {
  platformsMenuOpen.value = !platformsMenuOpen.value
}

// Vérifier l'authentification
onMounted(() => {
  if (!authStore.isAuthenticated) {
    router.push('/login')
  }
})

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
