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
        v-if="mobileMenuOpen"
        class="fixed inset-0 bg-black/50 z-40 lg:hidden"
        @click="mobileMenuOpen = false"
      />
    </Transition>

    <!-- Modern Sidebar -->
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
        <p class="text-xs text-gray-500 font-medium">{{ authStore?.user?.tenant_name }}</p>
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
        <div>
          <button
            class="w-full flex items-center justify-between px-4 py-3 rounded-xl hover:bg-gray-50 transition-all text-gray-600 font-medium"
            :class="{ 'bg-primary-50 text-secondary-900 font-semibold shadow-sm border border-primary-100': isProductsRoute }"
            @click="toggleProductsMenu"
          >
            <div class="flex items-center gap-3">
              <i class="pi pi-box text-lg"/>
              <span>Produits StoFlow</span>
            </div>
            <i :class="['pi pi-chevron-down text-sm transition-transform duration-300', productsMenuOpen ? 'rotate-180' : 'rotate-0']"/>
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
              class="mt-1 ml-3 space-y-1 overflow-hidden border-l-2 border-gray-100 pl-3"
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
              <i class="pi pi-shopping-bag text-lg"/>
              <span>Plateformes</span>
            </NuxtLink>
            <button
              class="px-3 py-3 rounded-r-xl hover:bg-gray-50 transition-all text-gray-600"
              :class="{ 'bg-primary-50 text-secondary-900': platformsMenuOpen }"
              @click="togglePlatformsMenu"
            >
              <i :class="['pi pi-chevron-down text-sm transition-transform duration-300', platformsMenuOpen ? 'rotate-180' : 'rotate-0']"/>
            </button>
          </div>

          <!-- Sous-menu Plateformes avec animation -->
          <Transition
            enter-active-class="transition-all duration-300 ease-out"
            enter-from-class="opacity-0 max-h-0 -translate-y-2"
            enter-to-class="opacity-100 max-h-screen translate-y-0"
            leave-active-class="transition-all duration-200 ease-in"
            leave-from-class="opacity-100 max-h-screen translate-y-0"
            leave-to-class="opacity-0 max-h-0 -translate-y-2"
          >
            <div
              v-if="platformsMenuOpen"
              class="mt-1 ml-3 space-y-1 overflow-hidden border-l-2 border-gray-100 pl-3"
            >
              <!-- Vinted avec sous-menu -->
              <div>
                <button
                  class="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                  :class="{ 'bg-primary-50 text-secondary-900 font-semibold': isVintedRoute }"
                  @click="toggleVintedMenu"
                >
                  <div class="flex items-center gap-3">
                    <img src="/images/platforms/vinted-logo.png" alt="Vinted" class="w-5 h-5 object-contain">
                    <span>Vinted</span>
                  </div>
                  <i :class="['pi pi-chevron-down text-sm transition-transform duration-300', vintedMenuOpen ? 'rotate-180' : 'rotate-0']"/>
                </button>
                <Transition
                  enter-active-class="transition-all duration-200 ease-out"
                  enter-from-class="opacity-0 max-h-0"
                  enter-to-class="opacity-100 max-h-96"
                  leave-active-class="transition-all duration-150 ease-in"
                  leave-from-class="opacity-100 max-h-96"
                  leave-to-class="opacity-0 max-h-0"
                >
                  <div v-if="vintedMenuOpen" class="ml-3 mt-1 space-y-1 overflow-hidden border-l-2 border-gray-100 pl-3">
                    <NuxtLink
                      to="/dashboard/platforms/vinted"
                      class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                      :class="{ 'bg-primary-50 text-secondary-900 font-semibold': route.path === '/dashboard/platforms/vinted' }"
                    >
                      <i class="pi pi-chart-line text-sm"/>
                      <span>Vue d'ensemble</span>
                    </NuxtLink>
                    <NuxtLink
                      to="/dashboard/platforms/vinted/products"
                      class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                      active-class="bg-primary-50 text-secondary-900 font-semibold"
                    >
                      <i class="pi pi-box text-sm"/>
                      <span>Annonces Vinted</span>
                    </NuxtLink>
                    <!-- MVP1: Ventes désactivé
                    <NuxtLink
                      to="/dashboard/platforms/vinted/sales"
                      class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                      active-class="bg-primary-50 text-secondary-900 font-semibold"
                    >
                      <i class="pi pi-shopping-cart text-sm"/>
                      <span>Ventes</span>
                    </NuxtLink>
                    -->
                    <!-- MVP1: Expéditions désactivé
                    <NuxtLink
                      to="/dashboard/platforms/vinted/shipments"
                      class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                      active-class="bg-primary-50 text-secondary-900 font-semibold"
                    >
                      <i class="pi pi-truck text-sm"/>
                      <span>Expéditions</span>
                    </NuxtLink>
                    -->
                    <NuxtLink
                      to="/dashboard/platforms/vinted/analytics"
                      class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                      active-class="bg-primary-50 text-secondary-900 font-semibold"
                    >
                      <i class="pi pi-chart-bar text-sm"/>
                      <span>Analytiques</span>
                    </NuxtLink>
                    <!-- MVP1: Messages désactivé
                    <NuxtLink
                      to="/dashboard/platforms/vinted/messages"
                      class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                      active-class="bg-primary-50 text-secondary-900 font-semibold"
                    >
                      <i class="pi pi-envelope text-sm"/>
                      <span>Messages</span>
                      <Badge v-if="vintedUnreadMessages > 0" :value="vintedUnreadMessages" severity="danger" class="text-sm ml-auto"/>
                    </NuxtLink>
                    -->
                    <NuxtLink
                      to="/dashboard/platforms/vinted/settings"
                      class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                      active-class="bg-primary-50 text-secondary-900 font-semibold"
                    >
                      <i class="pi pi-cog text-sm"/>
                      <span>Paramètres</span>
                    </NuxtLink>
                  </div>
                </Transition>
              </div>

              <!-- eBay avec sous-menu -->
              <div>
                <button
                  class="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                  :class="{ 'bg-primary-50 text-secondary-900 font-semibold': isEbayRoute }"
                  @click="toggleEbayMenu"
                >
                  <div class="flex items-center gap-3">
                    <img src="/images/platforms/ebay-logo.png" alt="eBay" class="w-5 h-5 object-contain">
                    <span>eBay</span>
                  </div>
                  <i :class="['pi pi-chevron-down text-sm transition-transform duration-300', ebayMenuOpen ? 'rotate-180' : 'rotate-0']"/>
                </button>
                <Transition
                  enter-active-class="transition-all duration-200 ease-out"
                  enter-from-class="opacity-0 max-h-0"
                  enter-to-class="opacity-100 max-h-40"
                  leave-active-class="transition-all duration-150 ease-in"
                  leave-from-class="opacity-100 max-h-40"
                  leave-to-class="opacity-0 max-h-0"
                >
                  <div v-if="ebayMenuOpen" class="ml-3 mt-1 space-y-1 overflow-hidden border-l-2 border-gray-100 pl-3">
                    <NuxtLink
                      to="/dashboard/platforms/ebay"
                      class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                      :class="{ 'bg-primary-50 text-secondary-900 font-semibold': route.path === '/dashboard/platforms/ebay' }"
                    >
                      <i class="pi pi-chart-line text-sm"/>
                      <span>Vue d'ensemble</span>
                    </NuxtLink>
                    <NuxtLink
                      to="/dashboard/platforms/ebay/products"
                      class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                      active-class="bg-primary-50 text-secondary-900 font-semibold"
                    >
                      <i class="pi pi-box text-sm"/>
                      <span>Annonces eBay</span>
                    </NuxtLink>
                    <NuxtLink
                      to="/dashboard/platforms/ebay/settings"
                      class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                      active-class="bg-primary-50 text-secondary-900 font-semibold"
                    >
                      <i class="pi pi-cog text-sm"/>
                      <span>Paramètres</span>
                    </NuxtLink>
                  </div>
                </Transition>
              </div>

              <!-- Etsy avec sous-menu -->
              <div>
                <button
                  class="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                  :class="{ 'bg-primary-50 text-secondary-900 font-semibold': isEtsyRoute }"
                  @click="toggleEtsyMenu"
                >
                  <div class="flex items-center gap-3">
                    <img src="/images/platforms/etsy-logo.png" alt="Etsy" class="w-5 h-5 object-contain">
                    <span>Etsy</span>
                  </div>
                  <i :class="['pi pi-chevron-down text-sm transition-transform duration-300', etsyMenuOpen ? 'rotate-180' : 'rotate-0']"/>
                </button>
                <Transition
                  enter-active-class="transition-all duration-200 ease-out"
                  enter-from-class="opacity-0 max-h-0"
                  enter-to-class="opacity-100 max-h-40"
                  leave-active-class="transition-all duration-150 ease-in"
                  leave-from-class="opacity-100 max-h-40"
                  leave-to-class="opacity-0 max-h-0"
                >
                  <div v-if="etsyMenuOpen" class="ml-3 mt-1 space-y-1 overflow-hidden border-l-2 border-gray-100 pl-3">
                    <NuxtLink
                      to="/dashboard/platforms/etsy"
                      class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                      :class="{ 'bg-primary-50 text-secondary-900 font-semibold': route.path === '/dashboard/platforms/etsy' }"
                    >
                      <i class="pi pi-chart-line text-sm"/>
                      <span>Vue d'ensemble</span>
                    </NuxtLink>
                    <NuxtLink
                      to="/dashboard/platforms/etsy/products"
                      class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                      active-class="bg-primary-50 text-secondary-900 font-semibold"
                    >
                      <i class="pi pi-box text-sm"/>
                      <span>Annonces Etsy</span>
                    </NuxtLink>
                    <NuxtLink
                      to="/dashboard/platforms/etsy/settings"
                      class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                      active-class="bg-primary-50 text-secondary-900 font-semibold"
                    >
                      <i class="pi pi-cog text-sm"/>
                      <span>Paramètres</span>
                    </NuxtLink>
                  </div>
                </Transition>
              </div>
            </div>
          </Transition>
        </div>

        <!-- MVP1: Publications désactivé
        <NuxtLink
          to="/dashboard/publications"
          class="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-gray-50 transition-all text-gray-600 font-medium"
          active-class="bg-primary-50 text-secondary-900 font-semibold shadow-sm border border-primary-100"
        >
          <i class="pi pi-send text-lg"/>
          <span>Publications</span>
        </NuxtLink>
        -->

        <!-- MVP1: Statistiques désactivé
        <NuxtLink
          to="/dashboard/stats"
          class="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-gray-50 transition-all text-gray-600 font-medium"
          active-class="bg-primary-50 text-secondary-900 font-semibold shadow-sm border border-primary-100"
        >
          <i class="pi pi-chart-bar text-lg"/>
          <span>Statistiques</span>
        </NuxtLink>
        -->

        <!-- Abonnement -->
        <NuxtLink
          to="/dashboard/subscription"
          class="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-gray-50 transition-all text-gray-600 font-medium"
          active-class="bg-primary-50 text-secondary-900 font-semibold shadow-sm border border-primary-100"
        >
          <i class="pi pi-star text-lg"/>
          <span>Abonnement</span>
        </NuxtLink>

        <!-- Administration (Admin only) -->
        <div v-if="isAdmin">
          <button
            class="w-full flex items-center justify-between px-4 py-3 rounded-xl hover:bg-gray-50 transition-all text-gray-600 font-medium"
            :class="{ 'bg-primary-50 text-secondary-900 font-semibold shadow-sm border border-primary-100': isAdminRoute }"
            @click="toggleAdminMenu"
          >
            <div class="flex items-center gap-3">
              <i class="pi pi-shield text-lg"/>
              <span>Administration</span>
            </div>
            <i :class="['pi pi-chevron-down text-sm transition-transform duration-300', adminMenuOpen ? 'rotate-180' : 'rotate-0']"/>
          </button>

          <!-- Sous-menu Administration -->
          <Transition
            enter-active-class="transition-all duration-300 ease-out"
            enter-from-class="opacity-0 max-h-0 -translate-y-2"
            enter-to-class="opacity-100 max-h-40 translate-y-0"
            leave-active-class="transition-all duration-200 ease-in"
            leave-from-class="opacity-100 max-h-40 translate-y-0"
            leave-to-class="opacity-0 max-h-0 -translate-y-2"
          >
            <div
              v-if="adminMenuOpen"
              class="mt-1 ml-3 space-y-1 overflow-hidden border-l-2 border-gray-100 pl-3"
            >
              <NuxtLink
                to="/dashboard/admin/users"
                class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                active-class="bg-primary-50 text-secondary-900 font-semibold"
              >
                <i class="pi pi-users text-sm"/>
                <span>Gestion des utilisateurs</span>
              </NuxtLink>
            </div>
          </Transition>
        </div>

        <!-- Paramètres avec sous-menu -->
        <div>
          <div class="flex items-center gap-1">
            <NuxtLink
              to="/dashboard/settings"
              class="flex-1 flex items-center gap-3 px-4 py-3 rounded-l-xl hover:bg-gray-50 transition-all text-gray-600 font-medium"
              active-class="bg-primary-50 text-secondary-900 font-semibold shadow-sm border border-primary-100"
            >
              <i class="pi pi-cog text-lg"/>
              <span>Paramètres</span>
            </NuxtLink>
            <button
              class="px-3 py-3 rounded-r-xl hover:bg-gray-50 transition-all text-gray-600"
              :class="{ 'bg-primary-50 text-secondary-900': settingsMenuOpen }"
              @click="toggleSettingsMenu"
            >
              <i :class="['pi pi-chevron-down text-sm transition-transform duration-300', settingsMenuOpen ? 'rotate-180' : 'rotate-0']"/>
            </button>
          </div>

          <!-- Sous-menu Paramètres -->
          <Transition
            enter-active-class="transition-all duration-200 ease-out"
            enter-from-class="opacity-0 max-h-0"
            enter-to-class="opacity-100 max-h-96"
            leave-active-class="transition-all duration-150 ease-in"
            leave-from-class="opacity-100 max-h-96"
            leave-to-class="opacity-0 max-h-0"
          >
            <div v-if="settingsMenuOpen" class="mt-1 ml-3 space-y-1 overflow-hidden border-l-2 border-gray-100 pl-3">
              <NuxtLink
                to="/dashboard/settings"
                class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                :class="{ 'bg-primary-50 text-secondary-900 font-semibold': route.path === '/dashboard/settings' }"
              >
                <i class="pi pi-user text-sm"/>
                <span>Profil</span>
              </NuxtLink>
              <!-- MVP1: Notifications désactivé
              <NuxtLink
                to="/dashboard/settings/notifications"
                class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
                active-class="bg-primary-50 text-secondary-900 font-semibold"
              >
                <i class="pi pi-bell text-sm"/>
                <span>Notifications</span>
              </NuxtLink>
              -->
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
            </div>
          </Transition>
        </div>

        <!-- Documentation (ouvre dans un nouvel onglet) -->
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
    <div class="lg:ml-64 bg-white min-h-screen">
      <!-- Top Bar with Locale Selector -->
      <div class="bg-white sticky top-0 z-30 border-b border-gray-100 lg:border-0">
        <div class="flex items-center justify-between px-4 lg:px-8 py-3">
          <div class="flex items-center gap-4">
            <!-- Mobile Menu Button -->
            <button
              class="lg:hidden p-2 -ml-2 rounded-lg hover:bg-gray-100 transition-colors"
              @click="mobileMenuOpen = true"
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
                <span
                  v-else
                  class="text-secondary-900 font-semibold capitalize"
                >
                  {{ crumb.label }}
                </span>
              </template>
            </nav>
          </div>

          <!-- Platform Header Actions (Vinted, eBay, Etsy) -->
          <PlatformHeaderActions
            v-if="isVintedRoute"
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
            v-else-if="isEbayRoute"
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
            v-else-if="isEtsyRoute"
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

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()
// SSR-safe initialization
const toast = import.meta.client ? useToast() : null

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

// État du menu mobile
const mobileMenuOpen = ref(false)

// État des sous-menus
const productsMenuOpen = ref(false)
const platformsMenuOpen = ref(false)
const settingsMenuOpen = ref(false)
const adminMenuOpen = ref(false)

// État des sous-menus plateformes
const vintedMenuOpen = ref(false)
const ebayMenuOpen = ref(false)
const etsyMenuOpen = ref(false)

// Badge messages non lus Vinted (à connecter au store plus tard)
const vintedUnreadMessages = ref(0)

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

    // Sous-sections des plateformes
    const subSectionLabels: Record<string, string> = {
      'publications': 'Publications',
      'sales': 'Ventes',
      'shipments': 'Expéditions',
      'analytics': 'Analytiques',
      'settings': 'Paramètres',
      'messages': 'Messages'
    }

    if (path.includes('/vinted')) {
      crumbs.push({ label: 'Vinted', path: '/dashboard/platforms/vinted' })
      // Ajouter la sous-section si présente
      const subSection = path.split('/vinted/')[1]
      if (subSection && subSectionLabels[subSection]) {
        crumbs.push({ label: subSectionLabels[subSection] })
      }
    } else if (path.includes('/ebay')) {
      crumbs.push({ label: 'eBay', path: '/dashboard/platforms/ebay' })
      const subSection = path.split('/ebay/')[1]
      if (subSection && subSectionLabels[subSection]) {
        crumbs.push({ label: subSectionLabels[subSection] })
      }
    } else if (path.includes('/etsy')) {
      crumbs.push({ label: 'Etsy', path: '/dashboard/platforms/etsy' })
      const subSection = path.split('/etsy/')[1]
      if (subSection && subSectionLabels[subSection]) {
        crumbs.push({ label: subSectionLabels[subSection] })
      }
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

// Vérifier les routes de chaque plateforme
const isVintedRoute = computed(() => route.path.startsWith('/dashboard/platforms/vinted'))
const isEbayRoute = computed(() => route.path.startsWith('/dashboard/platforms/ebay'))
const isEtsyRoute = computed(() => route.path.startsWith('/dashboard/platforms/etsy'))

// Vérifier si on est sur une route paramètres
const isSettingsRoute = computed(() => route.path.startsWith('/dashboard/settings'))

// Vérifier si on est sur une route admin
const isAdminRoute = computed(() => route.path.startsWith('/dashboard/admin'))

// Vérifier si l'utilisateur est admin
const isAdmin = computed(() => authStore.user?.role === 'admin')

// Platform watchers: Fetch status and start polling when on platform route
// Only run client-side to avoid SSR auth issues
watch(isVintedRoute, (isActive) => {
  if (!import.meta.client) return
  if (isActive) {
    vintedConnection.fetchStatus()
    vintedJobs.fetchActiveJobs()
    vintedJobs.startPolling(10000)
  } else {
    vintedJobs.stopPolling()
  }
}, { immediate: true })

watch(isEbayRoute, (isActive) => {
  if (!import.meta.client) return
  if (isActive) {
    ebayConnection.fetchStatus()
    ebayJobs.fetchActiveJobs()
    ebayJobs.startPolling(10000)
  } else {
    ebayJobs.stopPolling()
  }
}, { immediate: true })

watch(isEtsyRoute, (isActive) => {
  if (!import.meta.client) return
  if (isActive) {
    etsyConnection.fetchStatus()
    etsyJobs.fetchActiveJobs()
    etsyJobs.startPolling(10000)
  } else {
    etsyJobs.stopPolling()
  }
}, { immediate: true })

// Cleanup jobs polling on unmount
onUnmounted(() => {
  vintedJobs.stopPolling()
  ebayJobs.stopPolling()
  etsyJobs.stopPolling()
})

// Ouvrir automatiquement les menus si on est sur leurs routes
// Et fermer le menu mobile à chaque navigation
watch(() => route.path, (newPath) => {
  // Fermer le menu mobile à chaque changement de route
  mobileMenuOpen.value = false

  if (newPath.startsWith('/dashboard/products')) {
    productsMenuOpen.value = true
  }
  if (newPath.startsWith('/dashboard/platforms')) {
    platformsMenuOpen.value = true
    // Ouvrir le sous-menu de la plateforme concernée
    if (newPath.startsWith('/dashboard/platforms/vinted')) {
      vintedMenuOpen.value = true
    }
    if (newPath.startsWith('/dashboard/platforms/ebay')) {
      ebayMenuOpen.value = true
    }
    if (newPath.startsWith('/dashboard/platforms/etsy')) {
      etsyMenuOpen.value = true
    }
  }
  if (newPath.startsWith('/dashboard/settings')) {
    settingsMenuOpen.value = true
  }
  if (newPath.startsWith('/dashboard/admin')) {
    adminMenuOpen.value = true
  }
}, { immediate: true })

// Toggle des menus
const toggleProductsMenu = () => {
  productsMenuOpen.value = !productsMenuOpen.value
}

const togglePlatformsMenu = () => {
  platformsMenuOpen.value = !platformsMenuOpen.value
}

const toggleSettingsMenu = () => {
  settingsMenuOpen.value = !settingsMenuOpen.value
}

const toggleAdminMenu = () => {
  adminMenuOpen.value = !adminMenuOpen.value
}

// Toggle des sous-menus plateformes
const toggleVintedMenu = () => {
  vintedMenuOpen.value = !vintedMenuOpen.value
}

const toggleEbayMenu = () => {
  ebayMenuOpen.value = !ebayMenuOpen.value
}

const toggleEtsyMenu = () => {
  etsyMenuOpen.value = !etsyMenuOpen.value
}

// Note: Authentication is now handled by middleware/auth.global.ts

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

