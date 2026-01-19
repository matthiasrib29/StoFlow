<template>
  <aside
    :class="[
      'fixed left-0 top-0 h-full w-64 bg-white shadow-sm border-r border-gray-200 z-50',
      'transition-transform duration-300 ease-in-out',
      'lg:translate-x-0 lg:z-10',
      'flex flex-col',
      mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
    ]"
  >
    <!-- Logo & Tenant -->
    <div class="p-6 border-b border-gray-100 flex-shrink-0">
      <h1 class="text-2xl font-bold text-secondary-900 mb-1">Stoflow</h1>
      <ClientOnly>
        <p class="text-xs text-gray-500 font-medium">{{ authStore?.user?.tenant_name }}</p>
        <template #fallback>
          <p class="text-xs text-gray-500 font-medium">&nbsp;</p>
        </template>
      </ClientOnly>
    </div>

    <!-- Navigation (scrollable) -->
    <nav class="px-3 py-6 space-y-1 flex-1 overflow-y-auto">
      <!-- Accueil -->
      <NuxtLink
        to="/dashboard"
        class="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-gray-50 transition-all text-gray-600 font-medium"
        active-class="bg-primary-50 text-secondary-900 font-semibold shadow-sm border border-primary-100"
      >
        <i class="pi pi-home text-lg"/>
        <span>Accueil</span>
      </NuxtLink>

      <!-- Produits avec sous-menu -->
      <SidebarMenuItem
        icon="pi-box"
        label="Produits StoFlow"
        :is-active="nav.isProductsRoute.value"
        :is-open="nav.productsMenuOpen.value"
        @toggle="nav.toggleProductsMenu"
      >
        <NuxtLink
          to="/dashboard/products"
          class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
          active-class="bg-primary-50 text-secondary-900 font-semibold"
        >
          <i class="pi pi-list text-sm"/>
          <span>Liste des produits</span>
        </NuxtLink>
        <NuxtLink
          to="/dashboard/products/create"
          class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
          active-class="bg-primary-50 text-secondary-900 font-semibold"
        >
          <i class="pi pi-plus text-sm"/>
          <span>Créer un produit</span>
        </NuxtLink>
      </SidebarMenuItem>

      <!-- Plateformes avec sous-menu -->
      <div>
        <div class="flex items-center gap-1">
          <NuxtLink
            to="/dashboard/platforms"
            class="flex-1 flex items-center gap-3 px-4 py-3 rounded-l-xl hover:bg-gray-50 transition-all text-gray-600 font-medium"
            active-class="bg-primary-50 text-secondary-900 font-semibold shadow-sm border border-primary-100"
          >
            <i class="pi pi-shopping-bag text-lg"/>
            <span>Plateformes</span>
          </NuxtLink>
          <button
            class="px-3 py-3 rounded-r-xl hover:bg-gray-50 transition-all text-gray-600"
            :class="{ 'bg-primary-50 text-secondary-900': nav.platformsMenuOpen.value }"
            @click="nav.togglePlatformsMenu"
          >
            <i :class="['pi pi-chevron-down text-sm transition-transform duration-300', nav.platformsMenuOpen.value ? 'rotate-180' : 'rotate-0']"/>
          </button>
        </div>

        <!-- Sous-menu Plateformes -->
        <Transition
          enter-active-class="transition-all duration-300 ease-out"
          enter-from-class="opacity-0 max-h-0 -translate-y-2"
          enter-to-class="opacity-100 max-h-screen translate-y-0"
          leave-active-class="transition-all duration-200 ease-in"
          leave-from-class="opacity-100 max-h-screen translate-y-0"
          leave-to-class="opacity-0 max-h-0 -translate-y-2"
        >
          <div
            v-if="nav.platformsMenuOpen.value"
            class="mt-1 ml-3 space-y-1 overflow-hidden border-l-2 border-gray-100 pl-3"
          >
            <!-- Vinted -->
            <SidebarPlatformMenu
              platform="vinted"
              label="Vinted"
              logo="/images/platforms/vinted-logo.png"
              :is-active="nav.isVintedRoute.value"
              :is-open="nav.vintedMenuOpen.value"
              @toggle="nav.toggleVintedMenu"
            />

            <!-- eBay -->
            <SidebarPlatformMenu
              platform="ebay"
              label="eBay"
              logo="/images/platforms/ebay-logo.png"
              :is-active="nav.isEbayRoute.value"
              :is-open="nav.ebayMenuOpen.value"
              @toggle="nav.toggleEbayMenu"
            />

            <!-- Etsy -->
            <SidebarPlatformMenu
              platform="etsy"
              label="Etsy"
              logo="/images/platforms/etsy-logo.png"
              :is-active="nav.isEtsyRoute.value"
              :is-open="nav.etsyMenuOpen.value"
              @toggle="nav.toggleEtsyMenu"
            />
          </div>
        </Transition>
      </div>

      <!-- Abonnement -->
      <SidebarMenuItemWithLink
        to="/dashboard/subscription"
        icon="pi-star"
        label="Abonnement"
        :is-open="nav.subscriptionMenuOpen.value"
        @toggle="nav.toggleSubscriptionMenu"
      >
        <NuxtLink
          to="/dashboard/subscription/plans"
          class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
          active-class="bg-primary-50 text-secondary-900 font-semibold"
        >
          <i class="pi pi-sync text-sm"/>
          <span>Changer d'abonnement</span>
        </NuxtLink>
        <NuxtLink
          to="/dashboard/subscription/credits"
          class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
          active-class="bg-primary-50 text-secondary-900 font-semibold"
        >
          <i class="pi pi-bolt text-sm"/>
          <span>Crédits IA</span>
        </NuxtLink>
      </SidebarMenuItemWithLink>

      <!-- Administration (Admin only) - ClientOnly to prevent hydration mismatch -->
      <ClientOnly>
        <SidebarMenuItem
          v-if="isAdmin"
          icon="pi-shield"
          label="Administration"
          :is-active="nav.isAdminRoute.value"
          :is-open="nav.adminMenuOpen.value"
          @toggle="nav.toggleAdminMenu"
        >
          <NuxtLink
            to="/dashboard/admin"
            class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
            :class="{ 'bg-primary-50 text-secondary-900 font-semibold': route.path === '/dashboard/admin' }"
          >
            <i class="pi pi-chart-bar text-sm"/>
            <span>Tableau de bord</span>
          </NuxtLink>
          <NuxtLink
            to="/dashboard/admin/users"
            class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
            active-class="bg-primary-50 text-secondary-900 font-semibold"
          >
            <i class="pi pi-users text-sm"/>
            <span>Gestion des utilisateurs</span>
          </NuxtLink>
          <NuxtLink
            to="/dashboard/admin/attributes"
            class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
            active-class="bg-primary-50 text-secondary-900 font-semibold"
          >
            <i class="pi pi-database text-sm"/>
            <span>Donnees de reference</span>
          </NuxtLink>
          <NuxtLink
            to="/dashboard/admin/audit-logs"
            class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
            active-class="bg-primary-50 text-secondary-900 font-semibold"
          >
            <i class="pi pi-history text-sm"/>
            <span>Logs d'audit</span>
          </NuxtLink>
        </SidebarMenuItem>
      </ClientOnly>

      <!-- Paramètres -->
      <SidebarMenuItemWithLink
        to="/dashboard/settings"
        icon="pi-cog"
        label="Paramètres"
        :is-open="nav.settingsMenuOpen.value"
        @toggle="nav.toggleSettingsMenu"
      >
        <NuxtLink
          to="/dashboard/settings"
          class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
          :class="{ 'bg-primary-50 text-secondary-900 font-semibold': route.path === '/dashboard/settings' }"
        >
          <i class="pi pi-user text-sm"/>
          <span>Profil</span>
        </NuxtLink>
        <NuxtLink
          to="/dashboard/settings/security"
          class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
          active-class="bg-primary-50 text-secondary-900 font-semibold"
        >
          <i class="pi pi-lock text-sm"/>
          <span>Sécurité</span>
        </NuxtLink>
        <NuxtLink
          to="/dashboard/settings/integrations"
          class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
          active-class="bg-primary-50 text-secondary-900 font-semibold"
        >
          <i class="pi pi-link text-sm"/>
          <span>Intégrations</span>
        </NuxtLink>
      </SidebarMenuItemWithLink>

      <!-- Documentation -->
      <a
        href="/docs"
        target="_blank"
        class="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-gray-50 transition-all text-gray-600 font-medium"
      >
        <i class="pi pi-book text-lg"/>
        <span>Documentation</span>
        <i class="pi pi-external-link text-xs text-gray-400 ml-auto"/>
      </a>
    </nav>

    <!-- User Section -->
    <div class="flex-shrink-0 p-4 border-t border-gray-100 bg-gray-50">
      <div class="flex items-center gap-3 mb-3">
        <div class="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
          <i class="pi pi-user text-primary-600"/>
        </div>
        <div class="flex-1 min-w-0">
          <ClientOnly>
            <p class="text-sm font-semibold truncate text-secondary-900">{{ authStore?.user?.full_name }}</p>
            <template #fallback>
              <p class="text-sm font-semibold truncate text-secondary-900">&nbsp;</p>
            </template>
          </ClientOnly>
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
        @click="$emit('logout')"
      />
    </div>
  </aside>
</template>

<script setup lang="ts">
const props = defineProps<{
  mobileMenuOpen: boolean
  nav: ReturnType<typeof useDashboardNavigation>
}>()

defineEmits<{
  logout: []
}>()

const route = useRoute()
const authStore = useAuthStore()

const isAdmin = computed(() => authStore.user?.role === 'admin')
</script>
